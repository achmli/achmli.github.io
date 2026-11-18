import calendar
import tkinter as tk
from datetime import date
from tkinter import ttk

from posts import blog_today


def picker_window(parent, title):
    popup = tk.Toplevel(parent)
    popup.title(title)
    popup.transient(parent)
    popup.resizable(False, False)
    popup.bind("<Escape>", lambda _: popup.destroy())
    content = ttk.Frame(popup, padding=14)
    content.pack(fill="both", expand=True)
    return popup, content


def pick_date(parent, selected, on_pick):
    popup, content = picker_window(parent, "选择日期")
    year, month = selected.year, selected.month
    heading = tk.StringVar(popup)

    def choose(day):
        on_pick(day.isoformat())
        popup.destroy()

    def show_month():
        heading.set(f"{year} 年 {month} 月")
        previous.state(["disabled"] if (year, month) == (1, 1) else ["!disabled"])
        following.state(["disabled"] if (year, month) == (9999, 12) else ["!disabled"])
        for widget in days.winfo_children():
            widget.destroy()
        weeks = calendar.Calendar().monthdayscalendar(year, month)
        for row, week in enumerate(weeks):
            for column, number in enumerate(week):
                if not number:
                    continue
                day = date(year, month, number)
                style = "Save.TButton" if day == selected else "TButton"
                ttk.Button(days, text=str(number), width=3, style=style,
                           command=lambda value=day: choose(value)).grid(row=row, column=column, padx=2, pady=2)

    def move(delta):
        nonlocal year, month
        year, offset = divmod(year * 12 + month - 1 + delta, 12)
        month = offset + 1
        show_month()

    navigation = ttk.Frame(content)
    navigation.pack(fill="x", pady=(0, 8))
    previous = ttk.Button(navigation, text="‹", width=3, command=lambda: move(-1))
    previous.pack(side="left")
    following = ttk.Button(navigation, text="›", width=3, command=lambda: move(1))
    following.pack(side="right")
    ttk.Label(navigation, textvariable=heading, anchor="center").pack(fill="x", expand=True)

    weekdays = ttk.Frame(content)
    weekdays.pack(fill="x")
    for day_name in "一二三四五六日":
        ttk.Label(weekdays, text=day_name, anchor="center", style="Muted.TLabel").pack(side="left", fill="x", expand=True)
    days = ttk.Frame(content, height=204)
    days.pack(fill="x")
    for column in range(7):
        days.columnconfigure(column, weight=1, uniform="dates")
    for row in range(6):
        days.rowconfigure(row, minsize=34)
    ttk.Button(content, text="今天", command=lambda: choose(blog_today())).pack(anchor="e", pady=(8, 0))
    show_month()
    popup.grab_set()
    return popup


def pick_tags(parent, choices, selected, on_pick):
    popup, content = picker_window(parent, "选择标签")
    choices = sorted(set(choices).union(selected), key=lambda tag: (tag.casefold(), tag))

    ttk.Label(content, text="点击切换选择，可选多个标签。", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
    list_frame = ttk.Frame(content)
    list_frame.pack(fill="both", expand=True)
    style = ttk.Style(parent)
    tags = tk.Listbox(list_frame, height=10, width=36, selectmode="multiple", exportselection=False,
                      font=style.lookup("TLabel", "font"), background=style.lookup("Treeview", "background"),
                      foreground=style.lookup("TLabel", "foreground"), selectbackground="#16685e",
                      selectforeground="#ffffff", highlightthickness=1)
    tags.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tags.yview)
    scrollbar.pack(side="right", fill="y")
    tags.configure(yscrollcommand=scrollbar.set)
    for index, tag in enumerate(choices):
        tags.insert("end", tag)
        if tag in selected:
            tags.selection_set(index)

    custom = ttk.Frame(content)
    custom.pack(fill="x", pady=(10, 0))
    ttk.Label(custom, text="新标签").pack(side="left", padx=(0, 8))
    entry = ttk.Entry(custom)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def add_tag(_=None):
        tag = entry.get().strip()
        if tag:
            if tag not in choices:
                choices.append(tag)
                tags.insert("end", tag)
            index = choices.index(tag)
            tags.selection_set(index)
            tags.see(index)
            entry.delete(0, "end")
        return "break"

    def apply():
        add_tag()
        active = [choices[index] for index in tags.curselection()]
        ordered = tuple(dict.fromkeys(tag for tag in (*selected, *active) if tag in active))
        on_pick(ordered)
        popup.destroy()

    ttk.Button(custom, text="添加", command=add_tag).pack(side="right")
    entry.bind("<Return>", add_tag)
    actions = ttk.Frame(content)
    actions.pack(fill="x", pady=(12, 0))
    ttk.Button(actions, text="确定", command=apply, style="Save.TButton").pack(side="right")
    ttk.Button(actions, text="取消", command=popup.destroy).pack(side="right", padx=(0, 8))
    tags.focus_set()
    popup.grab_set()
    return popup
