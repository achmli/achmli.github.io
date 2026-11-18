from argparse import ArgumentParser
from html import unescape
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from urllib.parse import parse_qs, quote, urlsplit
import json
import os
import re
import subprocess
import sys
import tempfile
import tkinter as tk
import webbrowser

from comments import CommentStore, receive_comments


REPO = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "AchmliBlog" / "comments"
PUBLIC_THREADS = REPO / "_data" / "comment_threads.json"
PORT = 18765
MAILBOX = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*@(?:neirmail\.com|neir\.io)\Z", re.I)
ARTICLE = re.compile(r'data-comment-post="([^"]+)"\s+data-comment-title="([^"]*)"')


def build_site(work):
    output = work / "site"
    settings = work / "preview.yml"
    settings.write_text("comments_preview: true\n", encoding="utf-8")
    build = subprocess.run(
        ["ruby", "-S", "bundle", "exec", "jekyll", "build", "--destination", str(output),
         "--config", f"{REPO / '_config.yml'},{settings}", "--disable-disk-cache", "--strict_front_matter"],
        cwd=REPO, capture_output=True, encoding="utf-8", errors="replace", timeout=90,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if build.returncode:
        raise RuntimeError((build.stderr or build.stdout).strip())
    return output


def find_posts(output):
    posts = {}
    for page in output.rglob("*.html"):
        article = ARTICLE.search(page.read_text(encoding="utf-8"))
        if article:
            posts[unescape(article[1])] = unescape(article[2])
    if not posts:
        raise RuntimeError("预览构建中没有找到博文。")
    return posts


def preview_server(output, store, settings, port=PORT):
    class PreviewRequest(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=output, **kwargs)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, *_args):
            pass

        def list_directory(self, _path):
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_GET(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            url = urlsplit(self.path)
            if url.path != "/__comments":
                super().do_GET()
                return
            path = parse_qs(url.query).get("post", [""])[0]
            if path not in store.posts:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            address = settings["mailbox"]
            endpoint = "https://formsubmit.co/ajax/" + quote(address, safe="") if address else ""
            data = json.dumps({"endpoint": endpoint, "threads": store.public_threads(path)}, ensure_ascii=False)
            body = data.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer(("127.0.0.1", port), PreviewRequest)


class Moderator(ttk.Frame):
    def __init__(self, window, store, settings, base_url, public_threads_path):
        super().__init__(window, padding=16)
        self.store = store
        self.settings = settings
        self.base_url = base_url
        self.public_threads_path = public_threads_path
        self.inbox = Queue()
        self.stop_mail = None
        self.worker = None
        self.rows = {}
        self.mailbox = tk.StringVar(value=settings["mailbox"])
        self.password = tk.StringVar()
        self.mail_status = tk.StringVar(value="连接 Neir 后，待审核留言会自动出现。")
        self.review_status = tk.StringVar(value="")
        self.filter = tk.StringVar()
        self.state = tk.StringVar(value="pending")

        window.title("博客留言审核")
        window.geometry("845x615")
        window.minsize(640, 480)
        window.configure(background="#f1f5f4")
        style = ttk.Style(window)
        style.theme_use("clam")
        style.configure("TFrame", background="#f1f5f4")
        style.configure("TLabel", background="#f1f5f4", foreground="#1c302e")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("TButton", padding=(8, 5))
        style.configure("TRadiobutton", background="#f1f5f4", foreground="#1c302e")
        style.configure("Treeview", rowheight=28)
        style.configure("Publish.TButton", background="#16685e", foreground="#ffffff")
        style.map("Publish.TButton", background=[("active", "#12584f"), ("disabled", "#c4d1ce")])

        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=3)
        self.rowconfigure(5, weight=2)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 11))
        ttk.Label(toolbar, text="博客留言审核", style="Title.TLabel").pack(side="left")
        ttk.Button(toolbar, text="打开留言文件夹", command=lambda: os.startfile(self.store.path.parent)).pack(side="right")
        ttk.Button(toolbar, text="打开本地博客", command=lambda: webbrowser.open(self.base_url)).pack(
            side="right", padx=(0, 8),
        )

        account = ttk.Frame(self)
        account.grid(row=1, column=0, sticky="ew")
        account.columnconfigure((0, 1), weight=1)
        ttk.Label(account, text="Neir 邮箱地址").grid(row=0, column=0, sticky="w")
        ttk.Label(account, text="应用密码").grid(row=0, column=1, sticky="w")
        self.address_entry = ttk.Entry(account, textvariable=self.mailbox, width=34)
        self.address_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.password_entry = ttk.Entry(account, textvariable=self.password, show="•", width=22)
        self.password_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))
        self.password_entry.bind("<Return>", lambda _event: self.toggle_connection())
        self.connection = ttk.Button(account, text="连接 Neir", command=self.toggle_connection)
        self.connection.grid(row=1, column=2)
        ttk.Label(self, textvariable=self.mail_status).grid(row=2, column=0, sticky="w", pady=(4, 12))

        tabs = ttk.Frame(self)
        tabs.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        ttk.Radiobutton(tabs, text="待审核", value="pending", variable=self.state, command=self.refresh).pack(side="left")
        ttk.Radiobutton(tabs, text="预览已公开", value="public", variable=self.state, command=self.refresh).pack(
            side="left", padx=(12, 0),
        )
        ttk.Entry(tabs, textvariable=self.filter, width=25).pack(side="right")
        ttk.Label(tabs, text="搜索").pack(side="right", padx=6)
        self.filter.trace_add("write", lambda *_args: self.refresh())

        content = ttk.Frame(self)
        content.grid(row=4, column=0, sticky="nsew")
        self.tree = ttk.Treeview(content, show="headings", columns=("post", "name", "text"), selectmode="browse", height=8)
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        for key, label, width, stretch in (("post", "文章", 245, True), ("name", "昵称", 80, False),
                                            ("text", "留言", 300, True)):
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=65, stretch=stretch)
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected())

        self.detail = ScrolledText(self, height=5, wrap="word", font=("Microsoft YaHei UI", 10), padx=8, pady=6)
        self.detail.grid(row=5, column=0, sticky="nsew", pady=(8, 8))
        actions = ttk.Frame(self)
        actions.grid(row=6, column=0, sticky="ew")
        ttk.Label(actions, textvariable=self.review_status).pack(side="left")
        self.approve = ttk.Button(actions, text="公开到预览", style="Publish.TButton",
                                  command=lambda: self.moderate("publish"))
        self.approve.pack(side="right")
        self.delete = ttk.Button(actions, text="删除留言", command=lambda: self.moderate("delete"))
        self.delete.pack(side="right", padx=(0, 8))
        ttk.Button(actions, text="重新生成公开内容", command=self.export_public).pack(side="right", padx=(0, 8))
        self.refresh()
        self.after(200, self.process_mail_events)

    def toggle_connection(self):
        if self.worker is not None:
            self.stop_mail.set()
            self.connection.configure(text="正在断开…", state="disabled")
            return
        address, password = self.mailbox.get().strip(), self.password.get().strip()
        if not MAILBOX.fullmatch(address) or not password:
            self.mail_status.set("请填写 Neir 邮箱地址和应用密码。")
            return
        try:
            (self.store.path.parent / "mailbox.txt").write_text(address + "\n", encoding="utf-8")
        except OSError:
            self.mail_status.set("无法保存本地邮箱设置。")
            return
        self.settings["mailbox"] = address
        self.password.set("")
        self.address_entry.configure(state="readonly")
        self.password_entry.configure(state="disabled")
        self.mail_status.set("正在连接 Neir…")
        self.connection.configure(text="断开 Neir")
        self.stop_mail = Event()
        self.worker = Thread(
            target=receive_comments, args=(address, password, self.store, self.stop_mail, self.inbox), daemon=True,
        )
        self.worker.start()

    def process_mail_events(self):
        changed = False
        while True:
            try:
                kind, label = self.inbox.get_nowait()
            except Empty:
                break
            self.mail_status.set(label)
            changed |= kind == "new"
        if self.worker and not self.worker.is_alive():
            if self.stop_mail.is_set():
                self.mail_status.set("Neir 已断开。")
            self.worker = None
            self.connection.configure(text="连接 Neir", state="normal")
            self.address_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
        if changed:
            self.refresh()
        self.after(200, self.process_mail_events)

    def selected(self):
        selection = self.tree.selection()
        return self.rows.get(selection[0]) if selection else None

    def refresh(self):
        current = self.tree.selection()
        state, filter_text = self.state.get(), self.filter.get().strip().casefold()
        self.rows = {}
        self.tree.delete(*self.tree.get_children())
        for item in self.store.visible_to_owner(state):
            title = self.store.posts.get(item["article"], item["article"])
            name = item["nickname"] or "匿名"
            sample = " ".join(item["body"].split())
            if filter_text in f"{title} {item['article']} {name} {item['body']}".casefold():
                self.rows[item["id"]] = item
                self.tree.insert("", "end", iid=item["id"], values=(title, name, sample[:100]))
        if current and current[0] in self.rows:
            self.tree.selection_set(*current)
        self.review_status.set(f"{len(self.rows)} 条留言")
        self.show_selected()

    def show_selected(self):
        selected = self.selected()
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        if selected:
            if "reply_context" in selected:
                name, body = selected["reply_context"]
                self.detail.insert("end", f"回复 {name}\n{body}\n\n")
            self.detail.insert("end", selected["body"])
        else:
            self.detail.insert("end", "选中留言查看正文。")
        self.detail.configure(state="disabled")
        self.approve.configure(state="normal" if selected and self.state.get() == "pending" else "disabled")
        self.delete.configure(state="normal" if selected else "disabled")

    def moderate(self, action):
        selected = self.selected()
        if selected:
            if action == "delete" and not messagebox.askyesno("删除留言", "删除这条留言和本地正文？"):
                return
            try:
                self.store.moderate(selected["id"], action)
            except OSError:
                messagebox.showerror("无法保存", "留言文件暂时无法写入。")
                return
            self.refresh()
            self.export_public()

    def export_public(self):
        try:
            self.store.export_public(self.public_threads_path)
        except OSError:
            messagebox.showerror("生成失败", "本地留言已保存。请重试「重新生成公开内容」。")
        else:
            self.review_status.set("公开内容已生成，可随博客发布。")


def main():
    args = ArgumentParser()
    args.add_argument("--mailbox", default="")
    args.add_argument("--no-browser", action="store_true")
    options = args.parse_args()
    window = tk.Tk()
    window.withdraw()
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        mailbox_file = DATA / "mailbox.txt"
        address = options.mailbox or (mailbox_file.read_text(encoding="utf-8").strip() if mailbox_file.exists() else "")
        if address and not MAILBOX.fullmatch(address):
            raise ValueError("请输入有效的 Neir 邮箱地址。")
        if options.mailbox:
            mailbox_file.write_text(address + "\n", encoding="utf-8")
        settings = {"mailbox": address}
        parent = Path(tempfile.gettempdir()).resolve()
        with tempfile.TemporaryDirectory(prefix="achmli-comments-", dir=parent, ignore_cleanup_errors=True) as directory:
            work = Path(directory).resolve()
            if work.parent != parent:
                raise RuntimeError("无法建立预览目录。")
            output = build_site(work)
            store = CommentStore(DATA / "comments.jsonl", find_posts(output))
            with preview_server(output, store, settings) as server:
                url = f"http://127.0.0.1:{server.server_port}/"
                moderator = Moderator(window, store, settings, url, PUBLIC_THREADS)
                Thread(target=server.serve_forever, daemon=True).start()
                window.deiconify()
                if not options.no_browser:
                    window.after(200, lambda: webbrowser.open(url))
                if sys.stdout is not None:
                    print("PREVIEW_URL=" + url, flush=True)
                try:
                    window.mainloop()
                finally:
                    if moderator.stop_mail:
                        moderator.stop_mail.set()
                    server.shutdown()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        messagebox.showerror("无法启动留言预览", str(error))
        window.destroy()


if __name__ == "__main__":
    main()
