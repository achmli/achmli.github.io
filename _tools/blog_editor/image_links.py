import re
from bisect import bisect_right
from dataclasses import dataclass, replace
from html import unescape
from html.parser import HTMLParser
from itertools import accumulate

from markdown_it import MarkdownIt
from markdown_it.rules_inline import html_inline, image


@dataclass(frozen=True)
class ImageLink:
    url: str
    start: int
    end: int


def line_starts(lines):
    return list(accumulate((len(line) + 1 for line in lines), initial=0))


def markdown_destination(parser, source, start):
    destination = parser.helpers.parseLinkDestination(source, start, len(source))
    if not destination.ok:
        return None
    end = destination.pos
    if source[start] == "<":
        start += 1
        end -= 1
    return ImageLink(destination.str, start, end)


BARE_DESTINATION_STOP = re.compile(r"[()]|[ \t](?=['\"])")
QUOTED_TITLE = re.compile(r"\s*(['\"])(.*?)\1\s*\)")


def kramdown_image(state, silent, start):
    # Kramdown also accepts spaces in bare destinations, including local paths
    # emitted by some Markdown editors. The ordinary parser handles <> links.
    if not state.src.startswith("![", start):
        return False
    label_end = state.md.helpers.parseLinkLabel(state, start + 1, False)
    opening = label_end + 1
    if label_end < 0 or state.src[opening:opening + 1] != "(":
        return False

    left = opening + 1
    while left < state.posMax and state.src[left] in " \t":
        left += 1
    if state.src[left:left + 1] == "<":
        return False
    newline = state.src.find("\n", left, state.posMax)
    limit = newline if newline >= 0 else state.posMax
    depth = 0
    for stop in BARE_DESTINATION_STOP.finditer(state.src, left, limit):
        char = stop.group()
        if char == "(":
            depth += 1
            continue
        if char == ")" and depth:
            depth -= 1
            continue
        end = stop.end()
        if char != ")":
            title = QUOTED_TITLE.match(state.src, stop.start(), limit)
            if not title:
                return False
            end = title.end()
        destination = state.src[left:stop.start()].rstrip()
        if not destination:
            return False
        if not silent:
            token = state.push("image", "img", 0)
            token.meta["destination"] = ImageLink(destination, left, left + len(destination))
        state.pos = end
        return True
    return False


def record_image(state, silent):
    start = state.pos
    if not image(state, silent):
        return kramdown_image(state, silent, start)
    if not silent:
        token = state.tokens[-1]
        if "label" not in token.meta:
            label_end = state.md.helpers.parseLinkLabel(state, start + 1, False)
            dest_start = label_end + 2
            while state.src[dest_start] in " \t\n":
                dest_start += 1
            token.meta["destination"] = markdown_destination(state.md, state.src, dest_start)
    return True


def record_html(state, silent):
    start = state.pos
    if not html_inline(state, silent):
        return False
    if not silent:
        state.tokens[-1].meta["offset"] = start
    return True


# Read source positions from the parser so fenced code, inline code, and escaped
# image syntax never get edited. Local file URLs are valid inputs to this tool.
MARKDOWN = MarkdownIt("commonmark", {"store_labels": True}).enable("table")
MARKDOWN.validateLink = lambda url: True
MARKDOWN.inline.ruler.at("image", record_image)
MARKDOWN.inline.ruler.at("html_inline", record_html)


ATTRIBUTE = re.compile(r'''([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?''')


class HTMLImages(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.starts = line_starts(source.split("\n"))
        self.links = []
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        markup = self.get_starttag_text()
        line, column = self.getpos()
        offset = self.starts[line - 1] + column
        for attribute in ATTRIBUTE.finditer(markup, 4):
            if attribute.group(1).lower() != "src":
                continue
            for group in (2, 3, 4):
                if attribute.group(group) is not None:
                    start, end = attribute.span(group)
                    self.links.append(ImageLink(unescape(attribute.group(group)), offset + start, offset + end))
                    return


REFERENCE = re.compile(r"(?:[ \t]*>[ \t]?)*[ \t]*\[(?:\\.|[^\]\\\n])+\]:[ \t]*(?:\n(?:[ \t]*>[ \t]?)*[ \t]*)?")


def image_links(body):
    """Return the source ranges of image URLs without reformatting the Markdown."""
    lines = body.split("\n")
    starts = line_starts(lines)
    env = {}
    links = []
    references = set()
    columns = {}

    for token in MARKDOWN.parse(body, env):
        if not token.map or token.type not in ("inline", "html_block"):
            continue
        found = []
        if token.type == "html_block":
            found = HTMLImages(token.content).links
        else:
            for child in token.children or ():
                if child.type == "image":
                    if "label" in child.meta:
                        references.add(child.meta["label"])
                    elif child.meta.get("destination"):
                        found.append(child.meta["destination"])
                elif child.type == "html_inline":
                    offset = child.meta["offset"]
                    found.extend(replace(link, start=link.start + offset, end=link.end + offset)
                                 for link in HTMLImages(child.content).links)

        # Block quote and list prefixes are trimmed from the parser's inline
        # text. Locate its lines in the original source before editing URLs.
        inline_lines = token.content.split("\n")
        inline_starts = line_starts(inline_lines)
        placements = {}
        for line, value in enumerate(inline_lines):
            original = token.map[0] + line
            if original >= token.map[1]:
                break
            column = lines[original].find(value, columns.get(original, 0))
            if column >= 0:
                placements[line] = starts[original] + column - inline_starts[line]
                columns[original] = column + len(value)
        for link in found:
            line = bisect_right(inline_starts, link.start) - 1
            if line in placements and link.end < inline_starts[line + 1]:
                offset = placements[line]
                links.append(replace(link, start=link.start + offset, end=link.end + offset))

    for label in references:
        first, last = env["references"][label]["map"]
        source = body[starts[first]:starts[last]]
        definition = REFERENCE.match(source)
        if definition:
            link = markdown_destination(MARKDOWN, source, definition.end())
            if link:
                links.append(replace(link, start=link.start + starts[first], end=link.end + starts[first]))
    return sorted(links, key=lambda link: link.start)
