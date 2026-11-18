import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from PIL import Image, ImageOps, ImageTk
from ruamel.yaml.error import YAMLError

from pickers import pick_date, pick_tags
from posts import IMAGE_EXTENSIONS, Blog, Fields, blog_today, load_draft, read_day


WINDOW_BG = "#f1f5f4"
SURFACE = "#ffffff"
TEXT = "#1c302e"
SECONDARY = "#49615e"
ACCENT = "#16685e"
IMAGE_TYPES = [("图片", " ".join(f"*{suffix}" for suffix in sorted(IMAGE_EXTENSIONS))), ("所有文件", "*")]
IMAGE_LABEL = {"site": "站内", "local": "待复制", "remote": "链接保留", "missing": "找不到"}


class Editor(ttk.Frame):
    def __init__(self, root, blog_root):
        super().__init__(root, padding=16)
        self.root = root
        self.blog = Blog(blog_root)
        self.draft = load_draft()
        self.variables = {key: tk.StringVar() for key in Fields.__dataclass_fields__ if key != "tags"}
        self.tags = self.draft.fields.tags
        self.tag_summary = tk.StringVar()
        self.destination = tk.StringVar()
        self.source_name = tk.StringVar()
        self.status = tk.StringVar()
        self.image_detail = tk.StringVar()
        self.image_rows = []
        self.scanned_body = ""
        self.refresh_job = None
        self.thumbnail = None

        families = set(font.families(root))
        ui_font = ("Inter" if "Inter" in families else "Microsoft YaHei UI", 10)
        body_font = ("IBM Plex Mono" if "IBM Plex Mono" in families else "Consolas", 11)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background=WINDOW_BG)
        style.configure("TLabel", background=WINDOW_BG, foreground=TEXT, font=ui_font)
        style.configure("Muted.TLabel", foreground=SECONDARY)
        style.configure("TButton", font=ui_font, padding=(9, 5))
        style.configure("Save.TButton", background=ACCENT, foreground=SURFACE)
        style.map("Save.TButton", background=[("active", "#12584f")])
        style.configure("TEntry", padding=(5, 4))
        style.configure("Treeview", font=ui_font, rowheight=28, background=SURFACE,
                        fieldbackground=SURFACE, foreground=TEXT)
        style.configure("Treeview.Heading", font=ui_font)
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", SURFACE)])

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for label, command in (("打开 Markdown…", self.open_file), ("粘贴稿件", self.paste_document),
                               ("插入图片…", self.insert_images)):
            ttk.Button(toolbar, text=label, command=command).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="保存到博客", style="Save.TButton", command=self.save).pack(side="right")
        ttk.Label(toolbar, textvariable=self.source_name, style="Muted.TLabel").pack(side="left", padx=5)

        metadata = ttk.Frame(self)
        metadata.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        metadata.columnconfigure(1, weight=3)
        metadata.columnconfigure(3, weight=2)
        field_rows = (
            (("标题", "title"), ("日期", "day")),
            (("副标题", "subtitle"), ("文件名", "slug")),
            (("标签", "tags"), ("作者", "author")),
            (("系列", "series"), ("系列顺序", "series_order")),
            (("专题", "topic"),),
        )
        selectors = {"day": ("选日期…", self.choose_date), "tags": ("选标签…", self.choose_tags)}
        for row, fields in enumerate(field_rows):
            for position, (label, key) in enumerate(fields):
                column = position * 2
                ttk.Label(metadata, text=label).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=4)
                control = ttk.Frame(metadata)
                control.grid(row=row, column=column + 1, sticky="ew", padx=(0, 16 if column == 0 else 0), pady=4)
                if key in selectors:
                    button_text, command = selectors[key]
                    ttk.Button(control, text=button_text, command=command).pack(side="right", padx=(8, 0))
                variable = self.tag_summary if key == "tags" else self.variables[key]
                if key in ("series", "topic"):
                    entry = ttk.Combobox(control, textvariable=variable, font=ui_font)
                    entry.configure(postcommand=lambda widget=entry, field=key: widget.configure(
                        values=("", *self.blog.available_choices(field))
                    ))
                else:
                    entry = ttk.Entry(control, textvariable=variable, font=ui_font)
                if key == "tags":
                    entry.state(["readonly"])
                if key == "series_order":
                    self.series_order_entry = entry
                entry.pack(side="left", fill="x", expand=True)

        ttk.Label(self, textvariable=self.destination, style="Muted.TLabel").grid(
            row=2, column=0, sticky="w", pady=(0, 12))
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.grid(row=3, column=0, sticky="nsew")
        markdown = ttk.Frame(panes, padding=(0, 0, 9, 0))
        pictures = ttk.Frame(panes, padding=(9, 0, 0, 0))
        panes.add(markdown, weight=3)
        panes.add(pictures, weight=2)

        ttk.Label(markdown, text="Markdown 正文").pack(anchor="w", pady=(0, 6))
        self.body = ScrolledText(markdown, undo=True, wrap="word", font=body_font, width=60, height=18,
                                 padx=10, pady=8, background=SURFACE, foreground=TEXT, insertbackground=TEXT,
                                 relief="solid", borderwidth=1)
        self.body.pack(fill="both", expand=True)

        picture_toolbar = ttk.Frame(pictures)
        picture_toolbar.pack(fill="x", pady=(0, 6))
        ttk.Label(picture_toolbar, text="图片链接").pack(side="left")
        self.replace_button = ttk.Button(picture_toolbar, text="替换所选图片…", command=self.replace_image)
        self.replace_button.pack(side="right")
        table_frame = ttk.Frame(pictures)
        table_frame.pack(fill="both", expand=True)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(table_frame, columns=("state", "link"), show="headings", selectmode="browse", height=8)
        self.table.heading("state", text="状态")
        self.table.heading("link", text="原链接")
        self.table.column("state", width=84, stretch=False)
        self.table.column("link", width=252, minwidth=100)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.thumbnail_label = ttk.Label(pictures)
        self.thumbnail_label.pack(anchor="w", pady=(8, 0))
        ttk.Label(pictures, textvariable=self.image_detail, wraplength=340, style="Muted.TLabel").pack(
            fill="x", pady=(4, 0))

        ttk.Label(self, textvariable=self.status, style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.body.bind("<<Modified>>", self.body_changed)
        self.table.bind("<<TreeviewSelect>>", self.show_image)
        self.table.bind("<Double-1>", self.jump_to_image)
        self.root.bind("<Control-o>", lambda _: self.open_file())
        self.root.bind("<Control-s>", lambda _: self.save())
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        for variable in self.variables.values():
            variable.trace_add("write", self.update_destination)
        self.variables["series"].trace_add("write", self.update_series_order_state)
        self.set_draft(self.draft)

    def fields(self):
        return Fields(tags=self.tags, **{key: variable.get().strip() for key, variable in self.variables.items()})

    def update_series_order_state(self, *_):
        self.series_order_entry.state(["!disabled"] if self.variables["series"].get().strip() else ["disabled"])

    def choose_date(self):
        variable = self.variables["day"]
        try:
            day = read_day(variable.get().strip())
        except ValueError:
            day = blog_today()
        return pick_date(self.root, day, variable.set)

    def choose_tags(self):
        return pick_tags(self.root, self.blog.available_choices("tags"), self.tags, self.set_tags)

    def set_tags(self, tags):
        self.tags = tags
        self.tag_summary.set("，".join(tags))

    def text(self):
        return self.body.get("1.0", "end-1c")

    def index(self, text, offset):
        previous_text = text[:offset]
        line = previous_text.count("\n") + 1
        column = self.tk.call("string", "length", previous_text.rsplit("\n", 1)[-1])
        return f"{line}.{column}"

    def set_draft(self, draft):
        self.draft = draft
        self.set_tags(draft.fields.tags)
        for key, variable in self.variables.items():
            variable.set(getattr(draft.fields, key))
        self.body.delete("1.0", "end")
        self.body.insert("1.0", draft.body)
        self.body.edit_reset()
        self.body.edit_modified(False)
        self.source_name.set(draft.source.name if draft.source else "")
        self.status.set("")
        self.baseline = (self.fields(), self.text())
        self.refresh_images()

    def update_destination(self, *_):
        try:
            target, _ = self.blog.destination(self.draft, self.fields())
        except ValueError as error:
            self.destination.set(str(error))
        else:
            source = self.draft.source
            label = "另存到" if source and source.is_relative_to(self.blog.posts) and target != source else "保存位置"
            self.destination.set(f"{label}  {target.relative_to(self.blog.root).as_posix()}")

    def discard_changes(self):
        return (self.fields(), self.text()) == self.baseline or messagebox.askyesno(
            "还有未保存的修改", "放弃当前修改？", parent=self.root)

    def close(self):
        if self.discard_changes():
            self.root.destroy()

    def open_file(self):
        path = filedialog.askopenfilename(title="打开 Markdown", parent=self.root,
                                          filetypes=[("Markdown", "*.md *.markdown"), ("所有文件", "*")])
        if path and self.discard_changes():
            self.import_document(path=path)

    def paste_document(self):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("粘贴稿件", "剪贴板里没有文字。", parent=self.root)
            return
        if self.discard_changes():
            self.import_document(text=text)

    def import_document(self, path=None, text=""):
        try:
            draft = load_draft(path, text)
        except (OSError, ValueError, YAMLError) as error:
            messagebox.showerror("无法打开稿件", str(error), parent=self.root)
            return
        self.set_draft(draft)
        self.body.focus_set()

    def body_changed(self, _):
        if self.body.edit_modified():
            self.body.edit_modified(False)
            if self.refresh_job is not None:
                self.after_cancel(self.refresh_job)
            self.refresh_job = self.after(350, self.refresh_images)

    def refresh_images(self):
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.scanned_body = self.text()
        self.image_rows = self.blog.scan(self.draft, self.scanned_body)
        self.table.delete(*self.table.get_children())
        for row, (link, location) in enumerate(self.image_rows):
            self.table.insert("", "end", iid=str(row), values=(IMAGE_LABEL[location.kind], link.url))
        self.show_image()

    def show_image(self, _=None):
        selected = self.table.selection()
        self.thumbnail = None
        self.thumbnail_label.configure(image="")
        self.replace_button.state(["!disabled"] if selected else ["disabled"])
        if not selected:
            self.image_detail.set("双击图片链接可定位到正文。" if self.image_rows else "正文中尚无图片链接。")
            return
        link, location = self.image_rows[int(selected[0])]
        self.image_detail.set(location.url or str(location.path or link.url))
        if location.path:
            try:
                with Image.open(location.path) as original:
                    preview = ImageOps.exif_transpose(original)
                    preview.thumbnail((280, 135))
                    self.thumbnail = ImageTk.PhotoImage(preview)
                    self.thumbnail_label.configure(image=self.thumbnail)
            except (OSError, ValueError, Image.DecompressionBombError):
                pass

    def jump_to_image(self, _):
        selected = self.table.selection()
        if selected and self.scanned_body == self.text():
            link, _ = self.image_rows[int(selected[0])]
            start = self.index(self.scanned_body, link.start)
            end = self.index(self.scanned_body, link.end)
            self.body.focus_set()
            self.body.mark_set("insert", end)
            self.body.tag_remove("sel", "1.0", "end")
            self.body.tag_add("sel", start, end)
            self.body.see(start)

    def insert_images(self):
        paths = filedialog.askopenfilenames(title="插入图片", filetypes=IMAGE_TYPES, parent=self.root)
        if paths:
            links = []
            for name in paths:
                path = Path(name).resolve()
                alt = path.stem.replace("[", "\\[").replace("]", "\\]")
                links.append(f"![{alt}](<{path.as_uri()}>)")
            self.body.insert("insert", "\n".join(links))
            self.refresh_images()

    def replace_image(self):
        selected = self.table.selection()
        if not selected or self.text() != self.scanned_body:
            self.refresh_images()
            return
        link, _ = self.image_rows[int(selected[0])]
        path = filedialog.askopenfilename(title="选择替换图片", filetypes=IMAGE_TYPES, parent=self.root)
        if path:
            self.body.replace(self.index(self.scanned_body, link.start), self.index(self.scanned_body, link.end),
                              Path(path).resolve().as_uri())
            self.refresh_images()

    def save(self):
        self.refresh_images()
        fields = self.fields()
        try:
            self.blog.destination(self.draft, fields)
            missing = list(dict.fromkeys(link.url for link, image in self.image_rows if image.kind == "missing"))
            if missing:
                display = "\n".join(missing[:5])
                if len(missing) > 5:
                    display += f"\n另有 {len(missing) - 5} 个链接"
                if not messagebox.askyesno("有图片找不到", f"{display}\n\n保留这些链接并保存？", parent=self.root):
                    return
            target, copied = self.blog.save(self.draft, fields, self.scanned_body, self.image_rows)
            self.set_draft(load_draft(target))
        except (OSError, ValueError, YAMLError) as error:
            messagebox.showerror("无法保存文章", str(error), parent=self.root)
            return
        relative = target.relative_to(self.blog.root).as_posix()
        suffix = f"，已复制 {copied} 张图片" if copied else ""
        self.status.set(f"已保存 {relative}{suffix}")


def main():
    root = tk.Tk()
    root.title("博客发文工具")
    root.geometry("1120x740")
    root.minsize(860, 560)
    try:
        editor = Editor(root, Path(__file__).resolve().parents[2])
    except (OSError, ValueError, YAMLError) as error:
        root.withdraw()
        messagebox.showerror("无法打开博客", str(error), parent=root)
        root.destroy()
        return 1
    editor.pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
