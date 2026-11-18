from base64 import urlsafe_b64decode
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
import imaplib
import json
import os
import re
import ssl
import tempfile
from pathlib import Path
from threading import RLock


MAIL_HOST = "mail.neirmail.com"
SUBJECT = "Blog-Comment-"
COMMENT_ID = re.compile(r"[a-f0-9]{32}\Z")
PACKET = re.compile(r"ACHMLI-COMMENT-V1\s+([A-Za-z0-9_-]{1,16384})(?![A-Za-z0-9_-])")


def write_atomic(path, content):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix="comments-", suffix=".tmp", delete=False) as output:
        scratch = Path(output.name)
        try:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        except BaseException:
            output.close()
            scratch.unlink(missing_ok=True)
            raise
    try:
        os.replace(scratch, path)
    finally:
        scratch.unlink(missing_ok=True)


class MailText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def parse_comment(raw):
    mail = BytesParser(policy=policy.default).parsebytes(raw)
    subject = str(mail.get("Subject", ""))
    if SUBJECT not in subject:
        return None
    for part in mail.walk():
        if part.get_content_type() not in {"text/plain", "text/html"} or part.get_filename():
            continue
        try:
            body = part.get_content()
        except (LookupError, ValueError):
            continue
        if part.get_content_type() == "text/html":
            parser = MailText()
            parser.feed(body)
            body = " ".join(parser.parts)
        for match in PACKET.finditer(body):
            encoded = match[1]
            try:
                packet = json.loads(urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            except (ValueError, UnicodeError):
                continue
            if isinstance(packet, dict):
                identifier = packet.get("id")
                if isinstance(identifier, str) and COMMENT_ID.fullmatch(identifier) and SUBJECT + identifier in subject:
                    return packet
    return None


class CommentStore:
    def __init__(self, path, posts):
        self.path = path
        self.posts = posts
        self.lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record = json.loads(line)
                    self.records[record["id"]] = record

    def _save(self, records):
        write_atomic(self.path, "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records.values()))
        self.records = records

    def import_comment(self, packet):
        fields = ("id", "article", "reply_to", "nickname", "body")
        if any(not isinstance(packet.get(field), str) for field in fields):
            return False
        identifier, article, reply_to, nickname, body = (packet[field] for field in fields)
        nickname, body = nickname.strip(), body.strip()
        if (not COMMENT_ID.fullmatch(identifier) or article not in self.posts
                or len(nickname) > 40 or not 0 < len(body) <= 2000):
            return False
        with self.lock:
            if identifier in self.records:
                return False
            root_id = ""
            if reply_to:
                target = self.records.get(reply_to)
                if not target or target.get("article") != article or not target.get("published"):
                    return False
                root_id = target["root_id"] or target["id"]
            record = {
                "id": identifier, "article": article, "reply_to": reply_to, "root_id": root_id,
                "nickname": nickname, "body": body, "state": "pending", "published": False,
                "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            self._save({**self.records, identifier: record})
            return True

    def visible_to_owner(self, state):
        with self.lock:
            items = []
            for record in reversed(self.records.values()):
                if record["state"] != state:
                    continue
                item = record.copy()
                if record["reply_to"]:
                    target = self.records.get(record["reply_to"], {})
                    item["reply_context"] = (
                        (target["nickname"] or "匿名", target["body"])
                        if target.get("state") == "public" else ("已删除的留言", "")
                    )
                items.append(item)
            return items

    def moderate(self, identifier, action):
        with self.lock:
            record = self.records.get(identifier)
            if not record or record["state"] == "deleted":
                return
            if action == "publish":
                updated = {**record, "state": "public", "published": True}
            elif action == "delete":
                # Keep the identifier to prevent a retry or a later inbox scan from restoring the text.
                updated = {key: record[key] for key in ("id", "article", "root_id", "published")}
                updated["state"] = "deleted"
            else:
                raise ValueError("Unknown moderation action")
            self._save({**self.records, identifier: updated})

    def public_threads(self, article):
        with self.lock:
            public = [record for record in self.records.values()
                      if record["state"] == "public" and record["article"] == article]
            threads = {}
            for record in public:
                item = {key: record[key] for key in ("id", "nickname", "body", "received_at")}
                root_id = record["root_id"]
                if root_id:
                    thread = threads.setdefault(root_id, {
                        "root": {"id": root_id, "deleted": True}, "replies": [],
                    })
                    if record["reply_to"] != root_id:
                        target = self.records.get(record["reply_to"], {})
                        item["reply_name"] = (
                            target["nickname"] or "匿名" if target.get("state") == "public" else "已删除的留言"
                        )
                    thread["replies"].append(item)
                else:
                    threads.setdefault(record["id"], {"replies": []})["root"] = item
            return list(threads.values())

    def export_public(self, destination):
        with self.lock:
            articles = {record["article"] for record in self.records.values()
                        if record["state"] == "public" and record["article"] in self.posts}
            data = {article: self.public_threads(article) for article in sorted(articles)}
            content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            if not destination.exists() or destination.read_text(encoding="utf-8") != content:
                write_atomic(destination, content)


def receive_comments(address, password, store, stop, updates):
    while not stop.is_set():
        try:
            with imaplib.IMAP4_SSL(MAIL_HOST, ssl_context=ssl.create_default_context(), timeout=14) as inbox:
                try:
                    inbox.login(address, password)
                except imaplib.IMAP4.abort:
                    raise
                except imaplib.IMAP4.error:
                    updates.put(("error", "Neir 登录失败。请检查邮箱地址和应用密码。"))
                    return
                if inbox.select("INBOX", readonly=True)[0] != "OK":
                    raise imaplib.IMAP4.abort("Could not open the inbox")
                updates.put(("status", "已连接 Neir，正在检查收件箱。"))
                checked = set()
                while not stop.is_set():
                    status, matches = inbox.uid("search", None, "HEADER", "SUBJECT", f'"{SUBJECT}"')
                    if status != "OK":
                        raise imaplib.IMAP4.abort("Search failed")
                    for uid in (matches[0] or b"").split():
                        if stop.is_set():
                            return
                        if uid in checked:
                            continue
                        status, parts = inbox.uid("fetch", uid, "(BODY.PEEK[])")
                        if status != "OK":
                            raise imaplib.IMAP4.abort("Fetch failed")
                        for part in parts:
                            if isinstance(part, tuple):
                                packet = parse_comment(part[1])
                                if packet and store.import_comment(packet):
                                    updates.put(("new", "收到新留言，等待审核。"))
                        checked.add(uid)
                    stop.wait(8)
        except (OSError, imaplib.IMAP4.error):
            if not stop.is_set():
                updates.put(("status", "收信连接暂时中断，正在等待重连。"))
                stop.wait(8)
