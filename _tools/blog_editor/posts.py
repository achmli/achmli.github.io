import copy
import hashlib
import io
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from urllib.request import url2pathname

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

from image_links import MARKDOWN, image_links


FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*(?:\n|$)", re.MULTILINE | re.DOTALL)
POST_NAME = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})-(.+)\.(?:md|markdown)", re.IGNORECASE)
DATE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})(?=$|[ T])")
RAW_BLOG_IMAGE = re.compile(
    r"https?://raw\.githubusercontent\.com/achmli/achmli\.github\.io/"
    r"(?:refs/heads/)?(?:master|main)/(img/[^?#]+)",
    re.IGNORECASE,
)
IMAGE_EXTENSIONS = {".apng", ".avif", ".bmp", ".gif", ".ico", ".jpeg", ".jpg",
                    ".png", ".svg", ".tif", ".tiff", ".webp"}
BLOG_TIMEZONE = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class Fields:
    title: str
    subtitle: str
    author: str
    day: str
    slug: str
    tags: tuple[str, ...]
    series: str = ""
    series_order: str = ""
    topic: str = ""


@dataclass
class Draft:
    source: Path | None
    original: bytes | None
    header: str
    metadata: CommentedMap
    fields: Fields
    body: str


@dataclass(frozen=True)
class ImageLocation:
    kind: str
    path: Path | None = None
    url: str | None = None


def yaml_editor():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def slugify(value):
    value = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"[^\w-]+", "-", value).strip("-_")


def read_day(value):
    match = DATE.match(str(value))
    if match:
        return date(*map(int, match.groups()))
    raise ValueError("日期请填写为 YYYY-MM-DD。")


def read_series_order(fields):
    if not fields.series or not fields.series_order:
        return None
    if fields.series_order.isdecimal():
        order = int(fields.series_order)
        if order > 0:
            return order
    raise ValueError("系列顺序请填写正整数，或留空。")


def blog_today():
    return datetime.now(BLOG_TIMEZONE).date()


def load_draft(source=None, text=""):
    original = None
    if source is not None:
        source = Path(source).resolve()
        original = source.read_bytes()
        text = original.decode("utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    header = FRONT_MATTER.match(text)
    metadata = yaml_editor().load(header.group(1)) if header else None
    if metadata is None:
        metadata = CommentedMap()
    if not isinstance(metadata, CommentedMap):
        raise ValueError("文章页头需要是 YAML 字段列表。")
    body = text[header.end():] if header else text

    title = str(metadata.get("title") or "")
    if not title:
        tokens = MARKDOWN.parse(body)
        for index, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag == "h1":
                title = tokens[index + 1].content
                break
        if not title and source:
            title = source.stem

    day = blog_today()
    slug = slugify(source.stem) if source else ""
    named_post = POST_NAME.fullmatch(source.name) if source else None
    if named_post:
        day = read_day(named_post[1])
        slug = named_post[2]
    elif metadata.get("date"):
        day = read_day(metadata["date"])

    tags = metadata.get("tags") or []
    if isinstance(tags, list):
        tags = tuple(map(str, tags))
    else:
        tags = tuple(str(tags).split())
    order = metadata.get("series_order")
    fields = Fields(
        title=title,
        subtitle=str(metadata.get("subtitle") or ""),
        author=str(metadata.get("author") or ""),
        day=day.isoformat(),
        slug=slug,
        tags=tags,
        series=str(metadata.get("series") or ""),
        series_order=str(order) if order is not None else "",
        topic=str(metadata.get("topic") or ""),
    )
    return Draft(source, original, header.group(0) if header else "", metadata, fields, body)


def render_post(draft, fields, day, body):
    metadata = copy.deepcopy(draft.metadata)
    metadata.setdefault("layout", "post")
    metadata["title"] = fields.title
    for key in ("subtitle", "author", "series", "topic"):
        value = getattr(fields, key)
        if value != getattr(draft.fields, key):
            if value:
                metadata[key] = value
            else:
                metadata.pop(key, None)
    order = read_series_order(fields)
    if order is None:
        metadata.pop("series_order", None)
    else:
        metadata["series_order"] = order
    if fields.tags != draft.fields.tags:
        metadata["tags"] = list(fields.tags)
    if not draft.header:
        metadata["header-style"] = "text"
        metadata["catalog"] = True
    if not draft.header or "date" in metadata and day != read_day(draft.fields.day):
        metadata["date"] = day

    header = draft.header
    if metadata != draft.metadata or not header:
        output = io.StringIO()
        yaml_editor().dump(metadata, output)
        header = f"---\n{output.getvalue()}---\n"
    if body and not body.endswith("\n"):
        body += "\n"
    return f"{header}{body}".encode("utf-8")


def write_file(path, content, expected=None):
    """Finish writing alongside the target before putting the file in place."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".blog-", delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
        if expected is not None:
            if path.read_bytes() != expected:
                raise ValueError("这篇文章在别处被修改了。请重新打开后再保存。")
            os.replace(temporary, path)
        elif os.name == "nt":
            os.rename(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class Blog:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.posts = (self.root / "_posts").resolve()
        self.images = (self.root / "img").resolve()
        if not all(folder.is_dir() and folder.is_relative_to(self.root) for folder in (self.posts, self.images)):
            raise ValueError("博客目录需要包含 _posts 和 img 文件夹。")
        config = YAML(typ="safe").load((self.root / "_config.yml").read_text(encoding="utf-8-sig"))
        baseurl = str(config.get("baseurl") or "").strip("/")
        self.baseurl = f"/{baseurl}" if baseurl else ""

    def available_choices(self, field):
        choices = set()
        for path in self.posts.rglob("*"):
            if not POST_NAME.fullmatch(path.name) or not path.is_file():
                continue
            if any(part.startswith(("_", ".")) for part in path.relative_to(self.posts).parts[:-1]):
                continue
            try:
                value = getattr(load_draft(path).fields, field)
            except (OSError, ValueError, YAMLError):
                continue
            if isinstance(value, tuple):
                choices.update(value)
            elif value:
                choices.add(value)
        return sorted(choices, key=lambda value: (value.casefold(), value))

    def destination(self, draft, fields):
        if not fields.title:
            raise ValueError("请填写文章标题。")
        if not re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", fields.day):
            raise ValueError("日期请填写为 YYYY-MM-DD。")
        day = read_day(fields.day)
        read_series_order(fields)
        slug = fields.slug or slugify(fields.title)
        if draft.source and draft.source.is_relative_to(self.posts):
            original = POST_NAME.fullmatch(draft.source.name)
            if original and original[2] == slug and read_day(original[1]) == day:
                return draft.source, day
        if not re.fullmatch(r"[\w-]+", slug) or not slug.strip("-_"):
            raise ValueError("文件名可用中文、字母、数字、连字符和下划线。")
        return self.posts / f"{day.isoformat()}-{slug}.md", day

    def image_url(self, path):
        relative = path.relative_to(self.images).as_posix()
        return f"{self.baseurl}/img/{quote(relative, safe='/')}"

    def find_image(self, value, source):
        value = value.strip()
        raw = RAW_BLOG_IMAGE.fullmatch(value.split("?", 1)[0].split("#", 1)[0])
        if raw:
            path = (self.root / unquote(raw[1])).resolve()
            if path.is_relative_to(self.images) and path.is_file():
                return ImageLocation("site", path, self.image_url(path))
            return ImageLocation("remote")

        value = re.sub(r"^\{\{\s*site\.baseurl\s*\}\}", self.baseurl, value)
        if not value or value.startswith(("//", "\\\\", "{{", "{%", "#")):
            return ImageLocation("remote")
        try:
            parsed = urlsplit(value)
        except ValueError:
            return ImageLocation("remote")
        windows_path = re.match(r"^[a-zA-Z]:[\\/]", value)
        if parsed.scheme and parsed.scheme != "file" and not windows_path:
            return ImageLocation("remote")

        site_prefix = self.baseurl + "/img/"
        if not parsed.scheme and parsed.path.startswith((site_prefix, "/img/")):
            prefix = site_prefix if parsed.path.startswith(site_prefix) else "/img/"
            image_part = unquote(parsed.path.removeprefix(prefix))
            path = (self.images / image_part).resolve()
            if path.is_relative_to(self.images) and path.is_file():
                tail = value[len(parsed.path):]
                return ImageLocation("site", path, self.image_url(path) + tail)
            return ImageLocation("missing")

        if parsed.scheme == "file":
            if parsed.netloc.lower() not in ("", "localhost"):
                return ImageLocation("remote")
            paths = [Path(url2pathname(parsed.path))]
        else:
            decoded = parsed.path if not windows_path else value.split("?", 1)[0].split("#", 1)[0]
            paths = [Path(candidate) for candidate in dict.fromkeys((value, unquote(decoded)))]

        parent = source.parent if source else self.root
        for candidate in paths:
            for folder in dict.fromkeys((parent, self.root)):
                try:
                    path = (folder / candidate).resolve()
                    if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                        continue
                except (OSError, ValueError):
                    continue
                if path.is_relative_to(self.images):
                    return ImageLocation("site", path, self.image_url(path))
                return ImageLocation("local", path)
        return ImageLocation("missing")

    def scan(self, draft, body):
        return [(link, self.find_image(link.url, draft.source)) for link in image_links(body)]

    def save(self, draft, fields, body, images):
        target, day = self.destination(draft, fields)
        expected = draft.original if target == draft.source else None
        if expected is None and target.exists():
            raise ValueError("已有同名文章。可以打开那篇文章编辑，或换一个文件名。")
        if expected is not None and target.read_bytes() != expected:
            raise ValueError("这篇文章在别处被修改了。请重新打开后再保存。")

        replacements = []
        copied = 0
        imported = {}
        asset_folder = (self.images / "in-post" / target.stem).resolve()
        if not asset_folder.is_relative_to(self.images):
            raise ValueError("图片目录需要位于博客的 img 目录内。")
        for link, location in images:
            url = location.url
            if location.kind == "local":
                if location.path not in imported:
                    asset_folder.mkdir(parents=True, exist_ok=True)
                    asset = location.path.read_bytes()
                    digest = hashlib.sha256(asset).hexdigest()[:12]
                    name = slugify(location.path.stem)[:72] or "image"
                    destination = asset_folder / f"{name}-{digest}{location.path.suffix.lower()}"
                    try:
                        write_file(destination, asset)
                        copied += 1
                    except FileExistsError:
                        if destination.read_bytes() != asset:
                            raise ValueError(f"已有不同内容的图片：{destination.name}") from None
                    imported[location.path] = self.image_url(destination)
                url = imported[location.path]
            if url is not None:
                replacements.append((link, url))

        for link, url in reversed(replacements):
            body = body[:link.start] + url + body[link.end:]
        write_file(target, render_post(draft, fields, day, body), expected=expected)
        return target, copied
