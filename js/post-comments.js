(() => {
    "use strict";

    const section = document.querySelector("#post-comments");
    const article = section.dataset.commentPost;
    const previewFeed = section.dataset.commentsUrl;
    const threads = section.querySelector(".comment-threads");
    const empty = section.querySelector(".comment-empty");
    const form = section.querySelector(".comment-form");
    const nickname = form.elements.nickname;
    const message = form.elements.message;
    const button = form.querySelector(".comment-submit");
    const status = form.querySelector(".comment-status");
    const replyContext = form.querySelector(".comment-reply-context");
    const replyLabel = replyContext.querySelector("span");
    const cancelReply = replyContext.querySelector("button");
    const draftKey = "comment-draft:" + article;
    const dateFormat = new Intl.DateTimeFormat("zh-CN", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Asia/Shanghai",
    });
    let endpoint = "";
    let lastThreads = "";
    let sent = null;
    let replyTo = "";
    let active = false;

    function setReply(id, name) {
        replyTo = id;
        replyLabel.textContent = name;
        replyContext.hidden = !id;
    }

    function remember(attempt) {
        sent = attempt;
        try {
            if (attempt) sessionStorage.setItem(draftKey, JSON.stringify(attempt));
            else sessionStorage.removeItem(draftKey);
        } catch {
            // The current page can still reuse the submission ID.
        }
    }

    try {
        sent = JSON.parse(sessionStorage.getItem(draftKey));
        if (sent?.article === article) {
            nickname.value = sent.nickname;
            message.value = sent.body;
            setReply(sent.reply_to, sent.reply_name);
            status.textContent = "上次送达待确认。留言已保留，重试会沿用原编号。";
        }
    } catch {
        sent = null;
    }

    cancelReply.addEventListener("click", () => setReply("", ""));

    function element(tag, className, text) {
        const node = document.createElement(tag);
        node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function renderComment(comment) {
        const item = element("li", "comment-item");
        item.id = "comment-" + comment.id;
        if (comment.deleted) {
            item.append(element("p", "comment-reply-target", "原留言已删除"));
            return item;
        }

        const header = element("div", "comment-meta");
        const name = comment.nickname || "匿名";
        const time = element("time", "", dateFormat.format(new Date(comment.received_at)));
        time.dateTime = comment.received_at;
        header.append(element("strong", "", name), time);
        if (comment.reply_name) {
            header.append(element("span", "comment-reply-target", "回复 " + comment.reply_name));
        }
        const reply = element("button", "comment-action", "回复");
        reply.type = "button";
        reply.setAttribute("aria-label", "回复 " + name);
        reply.addEventListener("click", () => {
            if (!active) {
                setReply(comment.id, name);
                message.focus();
            }
        });
        item.append(header, element("p", "comment-message", comment.body), reply);
        return item;
    }

    function showComments(data) {
        endpoint = data.endpoint || "";
        button.disabled = active || !endpoint;
        const snapshot = JSON.stringify(data.threads);
        if (snapshot !== lastThreads) {
            lastThreads = snapshot;
            const items = data.threads.map(({ root, replies }) => {
                const thread = renderComment(root);
                if (replies.length) {
                    const branch = element("ul", "comment-replies");
                    branch.append(...replies.map(renderComment));
                    thread.append(branch);
                }
                return thread;
            });
            threads.replaceChildren(...items);
        }
        empty.textContent = "还没有留言";
        empty.hidden = data.threads.length > 0;
        if (!endpoint && !sent) status.textContent = "留言入口尚未设置。";
        else if (endpoint && status.textContent === "留言入口尚未设置。") status.textContent = "审核后显示";
    }

    async function refresh() {
        try {
            const response = await fetch(previewFeed + "?" + new URLSearchParams({ post: article }), { cache: "no-store" });
            if (!response.ok) throw new Error("Could not load comments");
            showComments(await response.json());
        } catch {
            if (!lastThreads) empty.textContent = "暂时无法读取留言。";
        }
    }

    function packetFor(attempt) {
        const { id, article, body, nickname, reply_to } = attempt;
        const bytes = new TextEncoder().encode(JSON.stringify({ id, article, body, nickname, reply_to }));
        const packet = btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
        return "ACHMLI-COMMENT-V1 " + packet;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (active || !endpoint) return;
        const body = message.value.trim();
        const name = nickname.value.trim();
        if (!body) {
            status.textContent = "请填写留言。";
            message.focus();
            return;
        }

        if (!sent || sent.article !== article || sent.body !== body || sent.nickname !== name || sent.reply_to !== replyTo) {
            const random = crypto.getRandomValues(new Uint8Array(16));
            const id = Array.from(random, (byte) => byte.toString(16).padStart(2, "0")).join("");
            remember({ id, article, body, nickname: name, reply_to: replyTo, reply_name: replyLabel.textContent });
        }

        active = true;
        button.disabled = true;
        nickname.readOnly = message.readOnly = cancelReply.disabled = true;
        status.textContent = "正在发送，等待回执…";
        const abort = new AbortController();
        const timeout = setTimeout(() => abort.abort(), 50000);
        const uncertain = "送达待确认。留言已保留，重试会沿用原编号。";
        try {
            const response = await fetch(endpoint, {
                method: "POST",
                credentials: "omit",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify({
                    _subject: "Blog-Comment-" + sent.id,
                    _captcha: "false",
                    message: sent.body,
                    comment_packet: packetFor(sent),
                }),
                signal: abort.signal,
            });
            // FormSubmit sometimes sends JSON with a text/html content type.
            const result = await response.json();
            if (response.ok && (result.success === true || result.success === "true")) {
                remember(null);
                message.value = "";
                setReply("", "");
                status.textContent = "已提交，审核后会显示。";
            } else if (/needs activation|activate form/i.test(String(result.message))) {
                status.textContent = "留言入口需要站长确认。留言已保留。";
            } else {
                status.textContent = uncertain;
            }
        } catch {
            status.textContent = uncertain;
        } finally {
            clearTimeout(timeout);
            active = false;
            button.disabled = !endpoint;
            nickname.readOnly = message.readOnly = cancelReply.disabled = false;
        }
    });

    if (previewFeed) {
        refresh();
        window.addEventListener("focus", refresh);
        setInterval(() => { if (!document.hidden) refresh(); }, 10000);
    } else {
        showComments({
            endpoint: section.dataset.commentEndpoint,
            threads: JSON.parse(section.dataset.commentThreads || "null") ?? [],
        });
    }
})();
