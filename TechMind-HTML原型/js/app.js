(function () {
  var TM = window.TM;

  function toast(msg) {
    var el = document.getElementById("toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast";
      el.className = "toast";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(el._t);
    el._t = setTimeout(function () {
      el.classList.remove("show");
    }, 1800);
  }
  window.tmToast = toast;

  document.querySelectorAll("[data-toast]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      toast(btn.getAttribute("data-toast"));
      if (btn.dataset.toggleText) {
        var next = btn.dataset.toggleText;
        btn.dataset.toggleText = btn.textContent;
        btn.textContent = next;
      }
    });
  });

  /* —— Unified global nav —— */
  var TAB_PAGES = {
    "home.html": true,
    "search.html": true,
    "editor.html": true,
    "favorites.html": true,
    "profile.html": true
  };

  var BACK_FALLBACK = {
    "article.html": "home.html",
    "author.html": "home.html",
    "column.html": "home.html",
    "topic.html": "home.html",
    "graph.html": "profile.html",
    "settings.html": "profile.html",
    "manage.html": "profile.html",
    "admin.html": "profile.html",
    "pipeline.html": "editor.html"
  };

  function currentPageFile() {
    var path = (location.pathname || "").replace(/\\/g, "/");
    return path.split("/").pop() || "";
  }

  function renderGlobalNav() {
    var nav = document.querySelector("nav.nav");
    if (!nav) return;
    var file = currentPageFile();
    var items = [
      { href: "home.html", label: "首页", keys: ["home.html", ""] },
      { href: "search.html", label: "语义搜索", keys: ["search.html"] },
      { href: "editor.html", label: "写文章", keys: ["editor.html", "pipeline.html"] },
      { href: "favorites.html", label: "收藏", keys: ["favorites.html"] },
      {
        href: "profile.html",
        label: "我的",
        keys: ["profile.html", "settings.html", "manage.html", "admin.html", "graph.html"]
      }
    ];
    nav.innerHTML = items
      .map(function (item) {
        var active = item.keys.indexOf(file) !== -1;
        return (
          '<a href="' +
          item.href +
          '"' +
          (active ? ' class="active"' : "") +
          ">" +
          item.label +
          "</a>"
        );
      })
      .join("");
  }

  function renderBackButton() {
    var file = currentPageFile();
    if (!file || TAB_PAGES[file] || file === "login.html" || file === "register.html" || file === "index.html") {
      return;
    }
    if (!BACK_FALLBACK[file]) return;

    var top = document.querySelector(".app-top-inner");
    if (!top || top.querySelector(".nav-back")) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "nav-back";
    btn.setAttribute("aria-label", "返回");
    btn.innerHTML = "<span aria-hidden=\"true\">←</span><em>返回</em>";
    btn.addEventListener("click", function () {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        location.href = BACK_FALLBACK[file] || "home.html";
      }
    });
    top.insertBefore(btn, top.firstChild);
    document.body.classList.add("has-page-back");
  }

  /* —— Nav auth actions —— */
  function renderAuthActions() {
    var slots = document.querySelectorAll("[data-auth-actions]");
    if (!slots.length || !TM) return;
    var loggedIn = TM.isLoggedIn();
    var user = TM.getUser();
    slots.forEach(function (slot) {
      var compact = slot.getAttribute("data-auth-actions") === "compact";
      if (loggedIn && user) {
        slot.innerHTML = compact
          ? '<a class="btn" href="settings.html">设置</a><a class="avatar" href="profile.html" title="' +
            user.username +
            '">' +
            TM.avatarLetter(user.username) +
            "</a>"
          : '<a class="btn" href="settings.html">设置</a>' +
            '<a class="btn btn-primary" href="editor.html">写文章</a>' +
            '<a class="avatar" href="profile.html" title="' +
            user.username +
            '">' +
            TM.avatarLetter(user.username) +
            "</a>";
      } else {
        slot.innerHTML = compact
          ? '<a class="btn" href="login.html">登录</a>'
          : '<a class="btn" href="login.html">登录</a>' +
            '<a class="btn btn-primary" href="register.html">注册</a>';
      }
    });
  }

  function requireLogin(actionLabel) {
    if (TM && TM.isLoggedIn()) return true;
    toast("请先登录后再" + (actionLabel || "继续"));
    setTimeout(function () {
      location.href = "login.html";
    }, 700);
    return false;
  }

  /* —— Tag picker —— */
  function mountTagPicker(container, selected) {
    if (!container || !TM) return;
    var selectedSet = {};
    (selected || []).forEach(function (t) { selectedSet[t] = true; });
    container.innerHTML = "";
    TM.DEFAULT_TAGS.forEach(function (tag) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tag-pick-item" + (selectedSet[tag] ? " on" : "");
      btn.textContent = tag;
      btn.dataset.tag = tag;
      btn.addEventListener("click", function () {
        btn.classList.toggle("on");
      });
      container.appendChild(btn);
    });
  }

  function readTagPicker(container) {
    if (!container) return [];
    return Array.prototype.map
      .call(container.querySelectorAll(".tag-pick-item.on"), function (el) {
        return el.dataset.tag;
      });
  }

  /* —— Password —— */
  document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = document.getElementById(btn.getAttribute("data-toggle-password"));
      if (!input) return;
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "隐藏" : "显示";
    });
  });

  var regPwd = document.getElementById("regPassword");
  var meter = document.querySelector(".pwd-meter");
  if (regPwd && meter) {
    regPwd.addEventListener("input", function () {
      var v = regPwd.value;
      var level = 0;
      if (v.length >= 6) level++;
      if (v.length >= 8) level++;
      if (/[A-Za-z]/.test(v) && /\d/.test(v)) level++;
      if (/[^A-Za-z0-9]/.test(v)) level++;
      meter.setAttribute("data-level", String(Math.min(level, 4)));
    });
  }

  /* —— Register —— */
  var registerTags = document.getElementById("registerTags");
  if (registerTags) mountTagPicker(registerTags, ["Java", "Redis"]);

  var registerForm = document.getElementById("registerForm");
  if (registerForm && TM) {
    registerForm.addEventListener("submit", function (e) {
      e.preventDefault();
      if (registerForm.password.value !== registerForm.confirm.value) {
        toast("两次密码不一致");
        return;
      }
      if (registerForm.password.value.length < 8) {
        toast("密码至少 8 位");
        return;
      }
      if (!registerForm.querySelector(".auth-agree input").checked) {
        toast("请先同意用户协议");
        return;
      }
      var tags = readTagPicker(registerTags);
      if (!tags.length) {
        toast("请至少选择 1 个兴趣标签");
        return;
      }
      var roleEl = registerForm.querySelector('input[name="role"]:checked');
      var result = TM.register({
        username: registerForm.username.value.trim(),
        email: registerForm.email.value.trim(),
        password: registerForm.password.value,
        role: roleEl ? roleEl.value : "reader",
        tags: tags,
        bio: (registerForm.bio && registerForm.bio.value.trim()) || "这位用户还没有填写简介"
      });
      if (!result.ok) {
        toast(result.msg);
        return;
      }
      toast("注册成功");
      setTimeout(function () {
        location.href = "profile.html";
      }, 700);
    });
  }

  /* —— Login —— */
  var fillDemoHint = document.getElementById("fillDemoHint");
  if (fillDemoHint && TM) {
    fillDemoHint.addEventListener("click", function () {
      var form = document.getElementById("loginForm");
      var demo = TM.DEMO;
      if (form && demo) {
        form.account.value = demo.username;
        form.password.value = demo.password;
      }
      toast("已填充演示账号");
    });
  }

  var loginForm = document.getElementById("loginForm");
  if (loginForm && TM) {
    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var result = TM.login(loginForm.account.value.trim(), loginForm.password.value);
      if (!result.ok) {
        toast(result.msg);
        return;
      }
      toast("登录成功");
      setTimeout(function () {
        location.href = "home.html";
      }, 600);
    });
  }

  /* —— Settings —— */
  var settingsForm = document.getElementById("settingsForm");
  var settingsGuest = document.getElementById("settingsGuest");
  if (settingsForm && TM) {
    if (!TM.isLoggedIn()) {
      if (settingsGuest) settingsGuest.classList.remove("hidden");
      settingsForm.classList.add("hidden");
    } else {
      if (settingsGuest) settingsGuest.classList.add("hidden");
      settingsForm.classList.remove("hidden");
      var user = TM.getUser();
      settingsForm.username.value = user.username;
      settingsForm.email.value = user.email;
      settingsForm.bio.value = user.bio || "";
      var roleInput = settingsForm.querySelector('input[name="role"][value="' + user.role + '"]');
      if (roleInput) roleInput.checked = true;
      mountTagPicker(document.getElementById("settingsTags"), user.tags || []);

      settingsForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var tags = readTagPicker(document.getElementById("settingsTags"));
        if (!tags.length) {
          toast("请至少保留 1 个兴趣标签");
          return;
        }
        var roleEl = settingsForm.querySelector('input[name="role"]:checked');
        var patch = {
          username: settingsForm.username.value.trim(),
          email: settingsForm.email.value.trim(),
          bio: settingsForm.bio.value.trim() || "这位用户还没有填写简介",
          role: roleEl ? roleEl.value : "reader",
          tags: tags
        };
        if (settingsForm.password.value) {
          if (settingsForm.password.value.length < 8) {
            toast("新密码至少 8 位");
            return;
          }
          patch.password = settingsForm.password.value;
        }
        TM.updateUser(patch);
        toast("保存成功");
        setTimeout(function () {
          location.href = "profile.html";
        }, 700);
      });

      var logoutBtn = document.getElementById("logoutBtn");
      if (logoutBtn) {
        logoutBtn.addEventListener("click", function () {
          TM.logout();
          toast("已退出登录");
          setTimeout(function () {
            location.href = "login.html";
          }, 500);
        });
      }
    }
  }

  /* —— Profile —— */
  function renderProfile() {
    var guest = document.getElementById("profileGuest");
    var authed = document.getElementById("profileAuthed");
    if (!guest || !authed || !TM) return;

    if (!TM.isLoggedIn()) {
      guest.classList.remove("hidden");
      authed.classList.add("hidden");
      return;
    }

    guest.classList.add("hidden");
    authed.classList.remove("hidden");
    var user = TM.getUser();
    var articles = TM.getArticles();
    var favs = TM.getFavorites();

    document.getElementById("profileAvatar").textContent = TM.avatarLetter(user.username);
    document.getElementById("profileName").textContent = user.username;
    document.getElementById("profileRole").textContent = TM.roleLabel(user.role);
    document.getElementById("profileBio").textContent = user.bio || "这位用户还没有填写简介";
    document.getElementById("statArticles").textContent = String(articles.length);
    document.getElementById("statFollowers").textContent = String(user.followers || 0);
    document.getElementById("statFollowing").textContent = String(user.following || 0);
    document.getElementById("statFavs").textContent = String(favs.length);

    var tagsEl = document.getElementById("profileTags");
    tagsEl.innerHTML = "";
    (user.tags || []).forEach(function (tag) {
      var span = document.createElement("span");
      span.className = "profile-tag";
      span.textContent = tag;
      tagsEl.appendChild(span);
    });
    if (!(user.tags || []).length) {
      tagsEl.innerHTML = '<span class="profile-tag muted">暂无兴趣标签</span>';
    }

    var feed = document.getElementById("myArticleFeed");
    feed.innerHTML = "";
    if (!articles.length) {
      feed.innerHTML =
        '<div class="empty-feed">还没有发布文章。<a href="editor.html">开始写作</a></div>';
    } else {
      articles.forEach(function (a) {
        var link = document.createElement("a");
        link.className = "article-card";
        link.href = "article.html";
        link.innerHTML =
          "<div><div class=\"meta\"><span>" +
          (a.status === "published" ? "已发布" : "草稿") +
          "</span><span>" +
          a.createdAt +
          "</span><span>" +
          (a.likes || 0) +
          " 赞 · " +
          (a.favs || 0) +
          " 藏</span></div><h3></h3>" +
          (a.tags && a.tags.length
            ? '<div style="margin-top:10px">' +
              a.tags.map(function (t) { return '<span class="tag">#' + t + "</span>"; }).join("") +
              "</div>"
            : "") +
          '</div><div class="score"><b>' +
          (a.score || "—") +
          "</b></div>";
        link.querySelector("h3").textContent = a.title;
        feed.appendChild(link);
      });
    }
  }

  /* —— Home personalization —— */
  function renderHomePersonal() {
    var slot = document.getElementById("homePersonal");
    if (!slot || !TM) return;
    if (TM.isLoggedIn()) {
      var user = TM.getUser();
      var tags = (user.tags || []).join(" / ") || "未设置";
      slot.innerHTML =
        "<strong>Hi, " +
        user.username +
        "</strong><span>为你推荐：" +
        tags +
        "</span>";
    } else {
      slot.innerHTML =
        '<strong>访客模式</strong><span>登录后获得更精准的个性化推荐</span>';
    }
  }

  /* —— Favorites page —— */
  function renderFavoritesPage() {
    var feed = document.getElementById("favFeed");
    var empty = document.getElementById("favEmpty");
    var guest = document.getElementById("favGuest");
    var layout = document.getElementById("favLayout");
    if (!feed || !TM) return;

    if (!TM.isLoggedIn()) {
      if (guest) guest.classList.remove("hidden");
      if (layout) layout.classList.add("hidden");
      feed.classList.add("hidden");
      if (empty) empty.classList.add("hidden");
      return;
    }
    if (guest) guest.classList.add("hidden");
    if (layout) layout.classList.remove("hidden");

    var list = TM.getFavorites();
    feed.innerHTML = "";
    if (!list.length) {
      feed.classList.add("hidden");
      if (empty) empty.classList.remove("hidden");
      return;
    }
    feed.classList.remove("hidden");
    if (empty) empty.classList.add("hidden");

    list.forEach(function (item) {
      var a = document.createElement("a");
      a.className = "article-card";
      a.href = "article.html";
      a.setAttribute("data-in-folder", item.folder || "distributed");
      a.innerHTML =
        "<div><div class=\"meta\"><span>" +
        (item.folderLabel || item.folder || "默认") +
        "</span><span>" +
        (item.favoritedAt || "") +
        "</span><span>" +
        (item.unread ? "未读" : "已读") +
        '</span></div><h3></h3><p class="lede" style="margin:0"></p></div><div class="score"><b>' +
        (item.score || "—") +
        "</b></div>";
      a.querySelector("h3").textContent = item.title;
      a.querySelector(".lede").textContent = item.summary || "已加入智能收藏";
      feed.appendChild(a);
    });
  }

  /* —— Article favorite + composer identity —— */
  function bindArticleLoop() {
    var favBtn = document.getElementById("favArticleBtn");
    if (favBtn && TM) {
      var articleMeta = {
        id: favBtn.getAttribute("data-article-id") || "demo-redisson",
        title: favBtn.getAttribute("data-article-title") || "Redisson 分布式锁源码分析",
        score: 92,
        folder: "distributed",
        folderLabel: "分布式系统",
        summary: "与你最近的阅读兴趣相关"
      };
      if (TM.isFavorited(articleMeta.id)) {
        favBtn.textContent = "已收藏";
      }
      favBtn.addEventListener("click", function () {
        if (!requireLogin("收藏")) return;
        var result = TM.toggleFavorite(articleMeta);
        favBtn.textContent = result.added ? "已收藏" : "收藏";
        toast(result.added ? "已加入智能收藏" : "已取消收藏");
      });
    }

    var composerName = document.getElementById("composerName");
    if (composerName && TM) {
      if (TM.isLoggedIn()) {
        var u = TM.getUser();
        composerName.textContent = TM.avatarLetter(u.username);
        composerName.title = u.username;
      } else {
        composerName.textContent = "?";
        composerName.title = "未登录";
      }
    }
  }

  /* —— Search —— */
  var modeBtns = document.querySelectorAll("[data-search-mode]");
  if (modeBtns.length) {
    modeBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        modeBtns.forEach(function (b) { b.classList.remove("on"); });
        btn.classList.add("on");
        var mode = btn.getAttribute("data-search-mode");
        document.querySelectorAll("[data-mode-panel]").forEach(function (panel) {
          panel.classList.toggle("hidden", panel.getAttribute("data-mode-panel") !== mode);
        });
      });
    });
  }

  function showSearchResults(q) {
    var idle = document.getElementById("searchIdle");
    var results = document.getElementById("searchResults");
    var label = document.getElementById("searchQueryText");
    var input = document.getElementById("searchInput");
    if (!results) return;
    if (input) input.value = q;
    if (label) label.textContent = q;
    if (idle) idle.classList.add("hidden");
    results.classList.remove("hidden");
  }

  var searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var q = ((document.getElementById("searchInput") || {}).value || "").trim();
      if (!q) {
        toast("请输入搜索内容");
        return;
      }
      sessionStorage.setItem("tm_q", q);
      if (location.pathname.indexOf("search") !== -1) {
        showSearchResults(q);
      } else {
        location.href = "search.html";
      }
    });
  }

  if (location.pathname.indexOf("search") !== -1) {
    var saved = sessionStorage.getItem("tm_q");
    if (saved) showSearchResults(saved);
  }

  document.querySelectorAll("[data-chip-q]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var q = chip.getAttribute("data-chip-q");
      sessionStorage.setItem("tm_q", q);
      if (location.pathname.indexOf("search") !== -1) {
        showSearchResults(q);
      } else {
        location.href = "search.html";
      }
    });
  });

  /* Home feed tabs */
  var homeTabs = document.querySelectorAll("[data-home-tab]");
  if (homeTabs.length) {
    homeTabs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tab = btn.getAttribute("data-home-tab");
        homeTabs.forEach(function (b) { b.classList.remove("on"); });
        btn.classList.add("on");
        document.querySelectorAll("[data-home-panel]").forEach(function (panel) {
          panel.classList.toggle("hidden", panel.getAttribute("data-home-panel") !== tab);
        });
      });
    });
  }

  /* —— Favorites folders —— */
  var folderBtns = document.querySelectorAll("[data-folder]");
  if (folderBtns.length) {
    folderBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        folderBtns.forEach(function (b) { b.classList.remove("on"); });
        btn.classList.add("on");
        var folder = btn.getAttribute("data-folder");
        if (folder === "unread") {
          document.querySelectorAll("[data-in-folder]").forEach(function (item) {
            var unread = (item.textContent || "").indexOf("未读") !== -1;
            item.classList.toggle("hidden", !unread);
          });
          return;
        }
        document.querySelectorAll("[data-in-folder]").forEach(function (item) {
          var f = item.getAttribute("data-in-folder");
          item.classList.toggle("hidden", folder !== "all" && f !== folder);
        });
      });
    });
  }

  /* —— Guide —— */
  var guideToggle = document.getElementById("guideToggle");
  var guideBody = document.getElementById("guideBody");
  if (guideToggle && guideBody) {
    guideToggle.addEventListener("click", function () {
      var open = !guideBody.classList.contains("hidden");
      guideBody.classList.toggle("hidden", open);
      guideToggle.textContent = open ? "展开" : "收起";
    });
  }

  /* —— Editor —— */
  var mdSource = document.getElementById("mdSource");
  var mdPreview = document.getElementById("mdPreview");
  var wordCount = document.getElementById("wordCount");
  var saveStatus = document.getElementById("saveStatus");
  var canvas = document.querySelector(".editor-canvas");
  var currentDraftId = null;
  var previousDraftId = null;
  var aiSnapshot = null;
  var pendingTopic = "";
  var pendingTopicOutline = "";
  var pendingTopicAngle = "";
  var confirmMode = "topic"; /* topic | summary */
  var pendingSummary = "";
  var pendingOpening = "";
  var pendingExpand = "";
  var aiSideCollapsed = false;

  function simpleMarkdown(src) {
    var html = src
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    html = html.replace(/```([\s\S]*?)```/g, function (_, code) {
      return "<pre>" + code.trim() + "</pre>";
    });
    html = html.replace(/^### (.*)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.*)$/gm, "<h2>$1</h2>");
    html = html.replace(/^> (.*)$/gm, "<blockquote>$1</blockquote>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/^\- (.*)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, function (m) {
      return "<ul>" + m + "</ul>";
    });
    html = html.replace(/^(?!<[hupblo]|<pre|<li|<ul|<blockquote)(.+)$/gm, "<p>$1</p>");
    return html;
  }

  function refreshPreview() {
    if (!mdSource || !mdPreview) return;
    mdPreview.innerHTML = simpleMarkdown(mdSource.value || "");
  }

  function refreshCount() {
    if (!mdSource || !wordCount) return;
    var text = mdSource.value.replace(/\s/g, "");
    wordCount.textContent = text.length + " 字";
  }

  function getSummaryEl() {
    return document.getElementById("articleSummary") || document.getElementById("pubSummary");
  }

  function syncSummaryFields(fromId) {
    var main = document.getElementById("articleSummary");
    var pub = document.getElementById("pubSummary");
    if (!main || !pub) return;
    if (fromId === "pubSummary") main.value = pub.value;
    else pub.value = main.value;
  }

  function collectEditorPayload() {
    var titleEl = document.getElementById("articleTitle");
    var subEl = document.getElementById("articleSubtitle");
    var summaryEl = getSummaryEl();
    var colEl = document.getElementById("pubColumn");
    var catEl = document.getElementById("pubCategory");
    var tags = Array.prototype.map.call(
      document.querySelectorAll("#tagPreview .tag-pill"),
      function (el) {
        return el.textContent.replace("×", "").replace("#", "").trim();
      }
    );
    return {
      id: currentDraftId || undefined,
      title: (titleEl && titleEl.value.trim()) || "",
      subtitle: (subEl && subEl.value.trim()) || "",
      content: mdSource ? mdSource.value : "",
      tags: tags,
      summary: summaryEl ? summaryEl.value.trim() : "",
      column: colEl ? colEl.value : "",
      category: catEl ? catEl.value : "后端"
    };
  }

  function applyDraftToForm(draft) {
    if (!draft) return;
    currentDraftId = draft.id || null;
    var titleEl = document.getElementById("articleTitle");
    var subEl = document.getElementById("articleSubtitle");
    var summaryEl = document.getElementById("articleSummary");
    var pubSummaryEl = document.getElementById("pubSummary");
    if (titleEl) titleEl.value = draft.title || "";
    if (subEl) subEl.value = draft.subtitle || "";
    if (mdSource) mdSource.value = draft.content || "";
    if (summaryEl) summaryEl.value = draft.summary || "";
    if (pubSummaryEl) pubSummaryEl.value = draft.summary || "";
    if (draft.tags && draft.tags.length) {
      renderTags(draft.tags);
    }
    refreshCount();
    refreshPreview();
    refreshDraftSelect();
    setBackPrevVisible();
  }

  function persistDraft(manual) {
    if (!TM || !mdSource) return;
    var saved = TM.saveDraft(collectEditorPayload());
    currentDraftId = saved.id;
    if (saveStatus) {
      saveStatus.textContent = manual ? "已手动保存" : "已自动保存 刚刚";
    }
    refreshDraftSelect();
  }

  function setUndoVisible(on) {
    var btn = document.getElementById("undoAiBtn");
    var bar = document.getElementById("aiUndoBar");
    if (btn) btn.classList.toggle("hidden", !on);
    if (bar) bar.classList.toggle("hidden", !on);
  }

  function pushAiSnapshot(label) {
    if (!mdSource) return;
    var titleEl = document.getElementById("articleTitle");
    aiSnapshot = {
      title: titleEl ? titleEl.value : "",
      content: mdSource.value,
      label: label || "上次 AI 操作"
    };
    var undoLabel = document.getElementById("aiUndoLabel");
    if (undoLabel) undoLabel.textContent = "可撤销：" + aiSnapshot.label;
    setUndoVisible(true);
  }

  function undoAi() {
    if (!aiSnapshot || !mdSource) return;
    var titleEl = document.getElementById("articleTitle");
    if (titleEl) titleEl.value = aiSnapshot.title;
    mdSource.value = aiSnapshot.content;
    aiSnapshot = null;
    setUndoVisible(false);
    mdSource.dispatchEvent(new Event("input"));
    persistDraft(false);
    toast("已恢复 AI 改动前的内容");
  }

  function draftLabel(d) {
    var t = (d.title || "").trim();
    return t || "未命名草稿";
  }

  function refreshDraftSelect() {
    var sel = document.getElementById("draftSelect");
    if (!sel || !TM) return;
    var list = TM.listDrafts();
    sel.innerHTML = list
      .map(function (d) {
        var mark = d.id === currentDraftId ? " ✓" : "";
        return (
          '<option value="' +
          d.id +
          '"' +
          (d.id === currentDraftId ? " selected" : "") +
          ">" +
          draftLabel(d) +
          mark +
          "</option>"
        );
      })
      .join("");
    if (!list.length) {
      sel.innerHTML = '<option value="">暂无草稿</option>';
    }
  }

  function setBackPrevVisible() {
    var btn = document.getElementById("backPrevDraft");
    if (!btn) return;
    var show = Boolean(previousDraftId && previousDraftId !== currentDraftId);
    btn.classList.toggle("hidden", !show);
  }

  function switchToDraft(id, opts) {
    opts = opts || {};
    if (!TM || !id) return;
    if (id === currentDraftId && !opts.force) return;
    if (!opts.skipSave && currentDraftId) persistDraft(true);
    var draft = TM.getDraftById(id);
    if (!draft) {
      toast("草稿不存在");
      return;
    }
    if (opts.rememberPrev && currentDraftId && currentDraftId !== id) {
      previousDraftId = currentDraftId;
    }
    TM.setActiveDraftId(id);
    applyDraftToForm(draft);
    aiSnapshot = null;
    setUndoVisible(false);
    refreshDraftSelect();
    setBackPrevVisible();
    if (saveStatus) saveStatus.textContent = "已切换草稿";
  }

  function bindTagRemove(root) {
    (root || document).querySelectorAll(".tag-pill button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.parentElement.remove();
        toast("已移除标签");
      });
    });
  }

  function renderTags(tags) {
    var box = document.getElementById("tagPreview");
    if (!box) return;
    box.innerHTML =
      tags
        .map(function (t) {
          return '<span class="tag-pill">#' + t + ' <button type="button" aria-label="移除">×</button></span>';
        })
        .join("") +
      '<button class="tag-add" type="button" id="addTagBtn">+ 添加</button>';
    bindTagRemove(box);
    var addBtn = document.getElementById("addTagBtn");
    if (addBtn) {
      addBtn.addEventListener("click", function () {
        var name = window.prompt("自定义标签");
        if (!name || !name.trim()) return;
        var current = Array.prototype.map.call(
          document.querySelectorAll("#tagPreview .tag-pill"),
          function (el) {
            return el.textContent.replace("×", "").replace("#", "").trim();
          }
        );
        if (current.indexOf(name.trim()) >= 0) {
          toast("标签已存在");
          return;
        }
        renderTags(current.concat([name.trim()]));
      });
    }
  }

  if (document.getElementById("tagPreview")) {
    bindTagRemove(document.getElementById("tagPreview"));
    var addTagInit = document.getElementById("addTagBtn");
    if (addTagInit) {
      addTagInit.addEventListener("click", function () {
        var name = window.prompt("自定义标签");
        if (!name || !name.trim()) return;
        var current = Array.prototype.map.call(
          document.querySelectorAll("#tagPreview .tag-pill"),
          function (el) {
            return el.textContent.replace("×", "").replace("#", "").trim();
          }
        );
        renderTags(current.concat([name.trim()]));
      });
    }
  }

  var tagBtn = document.getElementById("genTags");
  if (tagBtn) {
    tagBtn.addEventListener("click", function () {
      var userTags = TM && TM.isLoggedIn() ? TM.getUser().tags || [] : [];
      var auto = userTags.length ? userTags.slice(0, 3) : ["JVM", "性能优化", "GC"];
      renderTags(auto);
      toast("已生成智能标签");
    });
  }

  /* AI 阶段切换 */
  document.querySelectorAll("[data-ai-stage]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var stage = btn.getAttribute("data-ai-stage");
      document.querySelectorAll("[data-ai-stage]").forEach(function (b) {
        b.classList.toggle("on", b === btn);
      });
      document.querySelectorAll("[data-stage-panel]").forEach(function (panel) {
        panel.classList.toggle("hidden", panel.getAttribute("data-stage-panel") !== stage);
        panel.classList.toggle("on", panel.getAttribute("data-stage-panel") === stage);
      });
    });
  });

  /* 侧栏折叠（桌面） */
  var toggleAiSide = document.getElementById("toggleAiSide");
  var editorWorkspace = document.getElementById("editorWorkspace");
  if (toggleAiSide && editorWorkspace) {
    toggleAiSide.addEventListener("click", function () {
      aiSideCollapsed = !aiSideCollapsed;
      editorWorkspace.classList.toggle("ai-collapsed", aiSideCollapsed);
      toggleAiSide.textContent = aiSideCollapsed ? "显示助手" : "收起助手";
    });
  }

  /* 移动端助手抽屉：克隆侧栏内容 */
  var aiDrawer = document.getElementById("aiDrawer");
  var aiMask = document.getElementById("aiMask");
  var aiDrawerBody = document.getElementById("aiDrawerBody");
  var editorSide = document.getElementById("editorSide");
  function openAiMobile() {
    if (!aiDrawer || !aiMask || !aiDrawerBody || !editorSide) return;
    aiDrawerBody.innerHTML = "";
    aiDrawerBody.appendChild(editorSide);
    aiDrawer.classList.remove("hidden");
    aiMask.classList.remove("hidden");
  }
  function closeAiMobile() {
    if (!aiDrawer || !aiMask || !editorWorkspace || !editorSide) return;
    editorWorkspace.appendChild(editorSide);
    aiDrawer.classList.add("hidden");
    aiMask.classList.add("hidden");
  }
  var openAiMobileBtn = document.getElementById("openAiMobile");
  var closeAiMobileBtn = document.getElementById("closeAiMobile");
  if (openAiMobileBtn) openAiMobileBtn.addEventListener("click", openAiMobile);
  if (closeAiMobileBtn) closeAiMobileBtn.addEventListener("click", closeAiMobile);
  if (aiMask) aiMask.addEventListener("click", closeAiMobile);

  /* 选题：预览确认 */
  var topicConfirm = document.getElementById("topicConfirm");
  var topicMask = document.getElementById("topicMask");
  function openTopicConfirm(btn) {
    confirmMode = "topic";
    pendingTopic = btn.getAttribute("data-preview-topic") || "";
    pendingTopicOutline = (btn.getAttribute("data-topic-outline") || "").replace(/&#10;/g, "\n");
    pendingTopicAngle = btn.getAttribute("data-topic-angle") || "";
    pendingSummary = "";
    var text = document.getElementById("topicConfirmText");
    var angle = document.getElementById("topicConfirmAngle");
    var dialogTitle = document.getElementById("confirmDialogTitle");
    var hint = document.getElementById("confirmDialogHint");
    if (dialogTitle) dialogTitle.textContent = "采用选题？";
    if (hint) {
      hint.textContent = "写入工作标题；正文为空时填入大纲骨架。导读可之后在「润色」里生成。";
    }
    if (angle) {
      angle.textContent = pendingTopicAngle ? "切口：" + pendingTopicAngle : "";
      angle.classList.toggle("hidden", !pendingTopicAngle);
    }
    if (text) text.textContent = pendingTopic;
    if (topicConfirm) topicConfirm.classList.remove("hidden");
    if (topicMask) topicMask.classList.remove("hidden");
  }
  function openSummaryConfirm(summary) {
    confirmMode = "summary";
    pendingSummary = summary;
    pendingTopic = "";
    pendingTopicOutline = "";
    pendingTopicAngle = "";
    var text = document.getElementById("topicConfirmText");
    var angle = document.getElementById("topicConfirmAngle");
    var dialogTitle = document.getElementById("confirmDialogTitle");
    var hint = document.getElementById("confirmDialogHint");
    if (dialogTitle) dialogTitle.textContent = "采用导读摘要？";
    if (hint) hint.textContent = "写入编辑区「导读摘要」，发布前仍可修改。";
    if (angle) angle.classList.add("hidden");
    if (text) text.textContent = summary;
    if (topicConfirm) topicConfirm.classList.remove("hidden");
    if (topicMask) topicMask.classList.remove("hidden");
  }
  function closeTopicConfirm() {
    if (topicConfirm) topicConfirm.classList.add("hidden");
    if (topicMask) topicMask.classList.add("hidden");
    pendingTopic = "";
    pendingTopicOutline = "";
    pendingTopicAngle = "";
    pendingSummary = "";
  }
  document.querySelectorAll("[data-preview-topic]").forEach(function (el) {
    el.addEventListener("click", function () {
      openTopicConfirm(el);
    });
  });
  var applyTopicConfirm = document.getElementById("applyTopicConfirm");
  if (applyTopicConfirm) {
    applyTopicConfirm.addEventListener("click", function () {
      if (confirmMode === "summary") {
        if (!pendingSummary) return;
        pushAiSnapshot("导读摘要");
        var summaryEl = document.getElementById("articleSummary");
        var pubSummaryEl = document.getElementById("pubSummary");
        if (summaryEl) summaryEl.value = pendingSummary;
        if (pubSummaryEl) pubSummaryEl.value = pendingSummary;
        persistDraft(false);
        closeTopicConfirm();
        toast("已写入导读摘要，可在标题下方继续修改");
        return;
      }
      if (!pendingTopic) return;
      pushAiSnapshot("选题");
      var kw = document.getElementById("topicKeyword");
      var title = document.getElementById("articleTitle");
      if (kw && pendingTopicAngle) kw.value = pendingTopicAngle;
      if (title) title.value = pendingTopic;
      if (mdSource && pendingTopicOutline && !mdSource.value.trim()) {
        mdSource.value = pendingTopicOutline;
        mdSource.dispatchEvent(new Event("input"));
      } else {
        persistDraft(false);
      }
      closeTopicConfirm();
      toast("已采用选题（可恢复）");
    });
  }
  ["closeTopicConfirm", "cancelTopicConfirm"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("click", closeTopicConfirm);
  });
  if (topicMask) topicMask.addEventListener("click", closeTopicConfirm);

  function buildSummaryVariants(title, content) {
    var t = (title || "").trim() || "本文";
    var hasOutline = /##\s/.test(content || "");
    return [
      {
        label: "问题导向",
        value: t + "：讲清常见误区与可落地做法，帮你少踩一遍坑。"
      },
      {
        label: "读者收益",
        value: "读完可以带着清单去实践：" + t.replace(/[：:].*$/, "") + "相关决策与排查路径。"
      },
      {
        label: "结论先行",
        value:
          (hasOutline ? "先给结论再展开细节。" : "结论先行。") +
          "围绕「" +
          t +
          "」给出边界条件与取舍。"
      }
    ];
  }

  var polishSummaryBtn = document.getElementById("polishSummary");
  if (polishSummaryBtn) {
    polishSummaryBtn.addEventListener("click", function () {
      var titleEl = document.getElementById("articleTitle");
      var base = titleEl ? titleEl.value.trim() : "";
      if (!base && !(mdSource && mdSource.value.trim())) {
        toast("请先选题或写一点正文，再生成导读");
        return;
      }
      var box = document.getElementById("summaryOpts");
      if (!box) return;
      var variants = buildSummaryVariants(base, mdSource ? mdSource.value : "");
      box.innerHTML = variants
        .map(function (v, i) {
          return (
            '<button type="button" data-preview-summary="' +
            v.value.replace(/"/g, "&quot;") +
            '">' +
            (i + 1) +
            ". [" +
            v.label +
            "] " +
            v.value +
            "</button>"
          );
        })
        .join("");
      box.classList.remove("hidden");
      box.querySelectorAll("[data-preview-summary]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          openSummaryConfirm(btn.getAttribute("data-preview-summary"));
        });
      });
      toast("已生成 3 条导读摘要候选");
    });
  }

  var polishOpenings = document.getElementById("polishOpenings");
  if (polishOpenings) {
    polishOpenings.addEventListener("click", function () {
      var box = document.getElementById("openingOpts");
      if (box) box.classList.remove("hidden");
      toast("已生成 3 种开头改写");
    });
  }

  document.querySelectorAll("[data-preview-opening]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      pendingOpening = btn.getAttribute("data-preview-opening") || "";
      var box = document.getElementById("openingPreview");
      var text = document.getElementById("openingPreviewText");
      if (text) text.textContent = pendingOpening;
      if (box) box.classList.remove("hidden");
    });
  });
  var applyOpening = document.getElementById("applyOpening");
  if (applyOpening) {
    applyOpening.addEventListener("click", function () {
      if (!mdSource || !pendingOpening) return;
      pushAiSnapshot("改写开头");
      mdSource.value = pendingOpening + "\n\n" + mdSource.value;
      mdSource.dispatchEvent(new Event("input"));
      var box = document.getElementById("openingPreview");
      if (box) box.classList.add("hidden");
      toast("已插入开头（可点「恢复原文」撤销）");
    });
  }
  var dismissOpening = document.getElementById("dismissOpening");
  if (dismissOpening) {
    dismissOpening.addEventListener("click", function () {
      var box = document.getElementById("openingPreview");
      if (box) box.classList.add("hidden");
      pendingOpening = "";
    });
  }

  var analyzeTopic = document.getElementById("analyzeTopic");
  if (analyzeTopic) {
    analyzeTopic.addEventListener("click", function () {
      var kw = document.getElementById("topicKeyword");
      var insight = document.getElementById("topicInsight");
      var key = (kw && kw.value.trim()) || "JVM";
      if (insight) {
        insight.textContent =
          "近 30 天「" + key + "」相关内容偏多，高质量占比偏低。建议选对比 / 实战 / 踩坑类切口，而不是再写通识入门。";
      }
      toast("已刷新选题分析");
    });
  }

  var undoAiBtn = document.getElementById("undoAiBtn");
  if (undoAiBtn) undoAiBtn.addEventListener("click", undoAi);
  var undoAiSideBtn = document.getElementById("undoAiSideBtn");
  if (undoAiSideBtn) undoAiSideBtn.addEventListener("click", undoAi);

  var draftSelect = document.getElementById("draftSelect");
  if (draftSelect) {
    draftSelect.addEventListener("change", function () {
      var id = draftSelect.value;
      if (!id) return;
      switchToDraft(id, { rememberPrev: true });
      toast("已切换到：「" + draftLabel(TM.getDraftById(id) || {}) + "」");
    });
  }

  var backPrevDraft = document.getElementById("backPrevDraft");
  if (backPrevDraft) {
    backPrevDraft.addEventListener("click", function () {
      if (!previousDraftId) return;
      var target = previousDraftId;
      previousDraftId = currentDraftId;
      switchToDraft(target, { rememberPrev: false });
      toast("已返回上一篇草稿");
    });
  }

  // 进入：恢复 active 草稿；空标题空正文则提示可新开
  if (mdSource && TM) {
    var params = new URLSearchParams(location.search);
    var preferId = params.get("draft");
    var draft = preferId ? TM.getDraftById(preferId) : TM.getDraft();
    if (!draft) {
      draft = TM.createNewDraft();
      if (saveStatus) saveStatus.textContent = "新草稿";
    } else {
      TM.setActiveDraftId(draft.id);
      if (saveStatus) saveStatus.textContent = "已恢复草稿";
    }
    applyDraftToForm(draft);

    var banner = document.getElementById("draftBanner");
    var hasContent =
      (draft.title && draft.title.trim()) ||
      (draft.content && draft.content.trim());
    if (banner && hasContent && !preferId) {
      var others = TM.listDrafts().filter(function (d) {
        return d.id !== draft.id;
      });
      if (others.length) {
        banner.classList.remove("hidden");
        var bannerText = document.getElementById("draftBannerText");
        if (bannerText) {
          bannerText.textContent =
            "当前草稿「" +
            (draft.title || "未命名") +
            "」。另有 " +
            others.length +
            " 篇本地草稿。";
        }
      }
    }
  }

  var draftBannerKeep = document.getElementById("draftBannerKeep");
  if (draftBannerKeep) {
    draftBannerKeep.addEventListener("click", function () {
      var banner = document.getElementById("draftBanner");
      if (banner) banner.classList.add("hidden");
    });
  }
  var draftBannerNew = document.getElementById("draftBannerNew");
  if (draftBannerNew) {
    draftBannerNew.addEventListener("click", function () {
      if (!TM) return;
      previousDraftId = currentDraftId;
      persistDraft(true);
      var created = TM.createNewDraft();
      applyDraftToForm(created);
      var banner = document.getElementById("draftBanner");
      if (banner) banner.classList.add("hidden");
      setBackPrevVisible();
      refreshDraftSelect();
      toast("已新开一篇，可随时切回旧草稿");
    });
  }

  var newDraftBtn = document.getElementById("newDraftBtn");
  if (newDraftBtn) {
    newDraftBtn.addEventListener("click", function () {
      if (!TM) return;
      previousDraftId = currentDraftId;
      persistDraft(true);
      var created = TM.createNewDraft();
      applyDraftToForm(created);
      aiSnapshot = null;
      setUndoVisible(false);
      setBackPrevVisible();
      refreshDraftSelect();
      toast("已新开一篇，可点「返回上一篇」或下拉切换");
    });
  }

  if (mdSource) {
    refreshCount();
    refreshPreview();
    var saveTimer;
    mdSource.addEventListener("input", function () {
      refreshCount();
      if (mdPreview && !mdPreview.classList.contains("hidden")) refreshPreview();
      if (saveStatus) {
        saveStatus.textContent = "保存中…";
        clearTimeout(saveTimer);
        saveTimer = setTimeout(function () {
          persistDraft(false);
        }, 600);
      }
    });
    ["articleTitle", "articleSubtitle", "articleSummary", "pubSummary"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.addEventListener("input", function () {
          if (id === "articleSummary" || id === "pubSummary") {
            syncSummaryFields(id);
          }
          clearTimeout(saveTimer);
          saveTimer = setTimeout(function () {
            persistDraft(false);
          }, 600);
        });
      }
    });
  }

  document.querySelectorAll("[data-editor-mode]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("[data-editor-mode]").forEach(function (b) {
        b.classList.remove("on");
      });
      btn.classList.add("on");
      var mode = btn.getAttribute("data-editor-mode");
      if (!mdSource || !mdPreview || !canvas) return;
      canvas.classList.toggle("is-split", mode === "split");
      if (mode === "write") {
        mdSource.classList.remove("hidden");
        mdPreview.classList.add("hidden");
      } else if (mode === "preview") {
        refreshPreview();
        mdSource.classList.add("hidden");
        mdPreview.classList.remove("hidden");
      } else {
        refreshPreview();
        mdSource.classList.remove("hidden");
        mdPreview.classList.remove("hidden");
      }
    });
  });

  function wrapSelection(before, after, placeholder) {
    if (!mdSource) return;
    var start = mdSource.selectionStart;
    var end = mdSource.selectionEnd;
    var value = mdSource.value;
    var selected = value.slice(start, end) || placeholder || "";
    mdSource.value = value.slice(0, start) + before + selected + after + value.slice(end);
    mdSource.focus();
    mdSource.selectionStart = start + before.length;
    mdSource.selectionEnd = start + before.length + selected.length;
    mdSource.dispatchEvent(new Event("input"));
  }

  document.querySelectorAll("#mdToolbar [data-md]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var t = btn.getAttribute("data-md");
      var map = {
        h2: ["## ", "", "二级标题"],
        h3: ["### ", "", "三级标题"],
        bold: ["**", "**", "粗体"],
        italic: ["*", "*", "斜体"],
        code: ["`", "`", "code"],
        codeblock: ["```java\n", "\n```", "// code"],
        quote: ["> ", "", "引用内容"],
        ul: ["- ", "", "列表项"],
        ol: ["1. ", "", "列表项"],
        link: ["[", "](https://)", "链接文字"],
        image: ["![", "](https://)", "图片说明"]
      };
      var conf = map[t];
      if (conf) wrapSelection(conf[0], conf[1], conf[2]);
    });
  });

  var imgUpload = document.getElementById("imgUpload");
  if (imgUpload) {
    imgUpload.addEventListener("change", function () {
      var file = imgUpload.files && imgUpload.files[0];
      if (!file) return;
      var name = file.name || "image.png";
      wrapSelection("![", "](https://cdn.techmind.app/" + name + ")", "图片说明");
      toast("已插入图片 Markdown");
      imgUpload.value = "";
    });
  }

  var expandDraftBtn = document.getElementById("expandDraft");
  if (expandDraftBtn) {
    expandDraftBtn.addEventListener("click", function () {
      pendingExpand =
        "\n\n## AI 扩写初稿\n\n" +
        "本节由大纲扩写生成，请作者润色后发布。\n\n" +
        "Redisson 通过 Lua 保证加解锁原子性；WatchDog 负责锁续期。" +
        "生产中应明确锁粒度，避免长时间持锁阻塞业务。\n";
      var box = document.getElementById("expandPreview");
      var text = document.getElementById("expandPreviewText");
      if (text) text.textContent = pendingExpand.trim();
      if (box) box.classList.remove("hidden");
      toast("已生成初稿预览");
    });
  }
  var applyExpand = document.getElementById("applyExpand");
  if (applyExpand) {
    applyExpand.addEventListener("click", function () {
      if (!mdSource || !pendingExpand) return;
      pushAiSnapshot("扩写初稿");
      mdSource.value += pendingExpand;
      mdSource.dispatchEvent(new Event("input"));
      var box = document.getElementById("expandPreview");
      if (box) box.classList.add("hidden");
      toast("已应用初稿（可点「恢复原文」撤销）");
    });
  }
  var dismissExpand = document.getElementById("dismissExpand");
  if (dismissExpand) {
    dismissExpand.addEventListener("click", function () {
      var box = document.getElementById("expandPreview");
      if (box) box.classList.add("hidden");
      pendingExpand = "";
    });
  }

  function ensureSummaryOnPublish(payload) {
    if (payload.summary) return payload;
    var variants = buildSummaryVariants(payload.title, payload.content);
    var auto = variants[0] ? variants[0].value : (payload.title || "本文") + "：技术实践与要点梳理。";
    var summaryEl = document.getElementById("articleSummary");
    var pubSummaryEl = document.getElementById("pubSummary");
    if (summaryEl) summaryEl.value = auto;
    if (pubSummaryEl) pubSummaryEl.value = auto;
    payload.summary = auto;
    toast("未填写导读，已自动生成摘要");
    return payload;
  }

  function publishArticle() {
    if (!requireLogin("发布文章")) return;
    var user = TM.getUser();
    var payload = ensureSummaryOnPublish(collectEditorPayload());
    if (!payload.title) {
      toast("请先填写标题");
      return;
    }
    var article = TM.addArticle({
      title: payload.title,
      subtitle: payload.subtitle,
      content: payload.content,
      summary: payload.summary,
      tags: payload.tags.length ? payload.tags : user.tags || [],
      column: payload.column,
      status: "published",
      review: "pending"
    });
    TM.createPublishJob(article);
    TM.clearDraft(currentDraftId);
    currentDraftId = null;
    toast("已提交发布");
    setTimeout(function () {
      location.href = "pipeline.html";
    }, 500);
  }

  document.querySelectorAll("[data-save-draft]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (!TM) return;
      persistDraft(true);
      toast("草稿已保存到本地");
    });
  });

  var drawer = document.getElementById("publishDrawer");
  var mask = document.getElementById("publishMask");
  function openDrawer() {
    if (!drawer || !mask) return;
    drawer.classList.remove("hidden");
    mask.classList.remove("hidden");
  }
  function closeDrawer() {
    if (!drawer || !mask) return;
    drawer.classList.add("hidden");
    mask.classList.add("hidden");
  }
  var openPublish = document.getElementById("openPublish");
  var closePublish = document.getElementById("closePublish");
  if (openPublish) openPublish.addEventListener("click", openDrawer);
  if (closePublish) closePublish.addEventListener("click", closeDrawer);
  if (mask) mask.addEventListener("click", closeDrawer);

  var confirmPublish = document.getElementById("confirmPublish");
  if (confirmPublish) {
    confirmPublish.addEventListener("click", function () {
      closeDrawer();
      publishArticle();
    });
  }

  var scheduleToggle = document.getElementById("scheduleToggle");
  var scheduleField = document.getElementById("scheduleField");
  if (scheduleToggle && scheduleField) {
    scheduleToggle.addEventListener("change", function () {
      scheduleField.classList.toggle("hidden", !scheduleToggle.checked);
    });
  }

  var editorGate = document.getElementById("editorGate");
  if (editorGate && TM && !TM.isLoggedIn()) {
    editorGate.classList.remove("hidden");
  }

  var editorBack = document.getElementById("editorBack");
  if (editorBack) {
    editorBack.addEventListener("click", function () {
      persistDraft(true);
      if (document.referrer) {
        window.history.back();
        return;
      }
      location.href = "home.html";
    });
  }

  /* —— Comments —— */
  var commentInput = document.getElementById("commentInput");
  var cCount = document.getElementById("cCount");
  if (commentInput && cCount) {
    commentInput.addEventListener("input", function () {
      var n = commentInput.value.length;
      cCount.textContent = String(n);
      cCount.style.color = n > 500 ? "var(--theme)" : "";
    });
  }

  var cancelComment = document.getElementById("cancelComment");
  if (cancelComment && commentInput) {
    cancelComment.addEventListener("click", function () {
      commentInput.value = "";
      commentInput.dispatchEvent(new Event("input"));
    });
  }

  var postComment = document.getElementById("postComment");
  var commentList = document.getElementById("commentList");
  if (postComment && commentInput && commentList) {
    postComment.addEventListener("click", function () {
      if (!requireLogin("评论")) return;
      var text = commentInput.value.trim();
      if (!text) {
        toast("请先输入评论内容");
        return;
      }
      if (text.length > 500) {
        toast("评论不能超过 500 字");
        return;
      }
      var user = TM.getUser();
      var article = document.createElement("article");
      article.className = "c-item";
      article.setAttribute("data-sort-hot", "0");
      article.setAttribute("data-sort-new", "99");
      article.innerHTML =
        '<div class="c-avatar"></div>' +
        '<div class="c-main">' +
        '<div class="c-meta"><strong></strong><span class="badge">我</span><time>刚刚</time></div>' +
        '<p class="c-text"></p>' +
        '<div class="c-actions">' +
        '<button type="button" data-c-like>赞 0</button>' +
        '<button type="button" data-c-reply>回复</button>' +
        "</div>" +
        '<div class="reply-box hidden">' +
        '<textarea rows="2" placeholder="回复…"></textarea>' +
        '<div class="reply-actions">' +
        '<button class="btn btn-ghost" type="button" data-c-cancel>取消</button>' +
        '<button class="btn btn-primary" type="button" data-c-send>回复</button>' +
        "</div></div></div>";
      article.querySelector(".c-avatar").textContent = TM.avatarLetter(user.username);
      article.querySelector(".c-meta strong").textContent = user.username;
      article.querySelector(".c-text").textContent = text;
      commentList.insertBefore(article, commentList.firstChild);
      bindCommentItem(article);
      commentInput.value = "";
      commentInput.dispatchEvent(new Event("input"));
      toast("评论已发布");
    });
  }

  function bindCommentItem(root) {
    root.querySelectorAll("[data-c-like]").forEach(function (btn) {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", function () {
        var m = (btn.textContent || "").match(/(\d+)/);
        var n = m ? parseInt(m[1], 10) : 0;
        if (btn.classList.contains("on")) {
          btn.classList.remove("on");
          btn.textContent = "赞 " + Math.max(0, n - 1);
        } else {
          btn.classList.add("on");
          btn.textContent = "赞 " + (n + 1);
        }
      });
    });
    root.querySelectorAll("[data-c-reply]").forEach(function (btn) {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", function () {
        if (!requireLogin("回复")) return;
        var box = btn.closest(".c-main").querySelector(".reply-box");
        if (box) box.classList.toggle("hidden");
      });
    });
    root.querySelectorAll("[data-c-cancel]").forEach(function (btn) {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", function () {
        var box = btn.closest(".reply-box");
        if (box) {
          box.classList.add("hidden");
          var ta = box.querySelector("textarea");
          if (ta) ta.value = "";
        }
      });
    });
    root.querySelectorAll("[data-c-send]").forEach(function (btn) {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", function () {
        if (!requireLogin("回复")) return;
        var box = btn.closest(".reply-box");
        var ta = box && box.querySelector("textarea");
        if (!ta || !ta.value.trim()) {
          toast("请输入回复内容");
          return;
        }
        toast("回复已发布");
        ta.value = "";
        box.classList.add("hidden");
      });
    });
  }
  bindCommentItem(document);

  document.querySelectorAll("[data-comment-sort]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("[data-comment-sort]").forEach(function (b) {
        b.classList.remove("on");
      });
      btn.classList.add("on");
      var sort = btn.getAttribute("data-comment-sort");
      var list = document.getElementById("commentList");
      if (!list) return;
      var items = Array.prototype.slice.call(list.querySelectorAll(":scope > .c-item"));
      items.sort(function (a, b) {
        var ka = parseInt(a.getAttribute("data-sort-" + sort) || "0", 10);
        var kb = parseInt(b.getAttribute("data-sort-" + sort) || "0", 10);
        return kb - ka;
      });
      items.forEach(function (item) {
        list.appendChild(item);
      });
    });
  });

  /* —— Manage articles —— */
  function renderManage() {
    var guest = document.getElementById("manageGuest");
    var authed = document.getElementById("manageAuthed");
    var listEl = document.getElementById("manageList");
    if (!listEl || !TM) return;

    if (!TM.isLoggedIn()) {
      if (guest) guest.classList.remove("hidden");
      if (authed) authed.classList.add("hidden");
      return;
    }
    if (guest) guest.classList.add("hidden");
    if (authed) authed.classList.remove("hidden");

    var tab = document.querySelector("[data-manage-tab].on");
    var filter = tab ? tab.getAttribute("data-manage-tab") : "all";
    var articles = TM.getMyArticles().filter(function (a) {
      if (filter === "all") return true;
      return a.status === filter;
    });

    listEl.innerHTML = "";
    if (!articles.length) {
      listEl.innerHTML = '<div class="empty-feed">暂无文章。<a href="editor.html">去写作</a></div>';
      return;
    }

    articles.forEach(function (a) {
      var row = document.createElement("div");
      row.className = "manage-row";
      row.innerHTML =
        "<div><div class=\"meta\"><span>" +
        (a.status === "published" ? "已发布" : "草稿") +
        "</span><span>" +
        (a.updatedAt || a.createdAt) +
        "</span><span>v" +
        ((a.versions && a.versions.length) || 1) +
        '</span></div><h3></h3></div><div class="manage-actions"></div>';
      row.querySelector("h3").textContent = a.title;
      var actions = row.querySelector(".manage-actions");

      var editBtn = document.createElement("a");
      editBtn.className = "btn";
      editBtn.href = "editor.html";
      editBtn.textContent = "编辑";
      editBtn.addEventListener("click", function () {
        TM.saveDraft({
          title: a.title,
          subtitle: a.subtitle || "",
          content: a.content || "",
          tags: a.tags || []
        });
      });

      var verBtn = document.createElement("button");
      verBtn.className = "btn";
      verBtn.type = "button";
      verBtn.textContent = "版本历史";
      verBtn.addEventListener("click", function () {
        openVersions(a);
      });

      var delBtn = document.createElement("button");
      delBtn.className = "btn";
      delBtn.type = "button";
      delBtn.textContent = "删除";
      delBtn.addEventListener("click", function () {
        if (!window.confirm("确认删除《" + a.title + "》？")) return;
        TM.deleteArticle(a.id);
        toast("已删除");
        renderManage();
      });

      if (a.status === "published") {
        var view = document.createElement("a");
        view.className = "btn";
        view.href = "article.html";
        view.textContent = "查看";
        actions.appendChild(view);
      }
      actions.appendChild(editBtn);
      actions.appendChild(verBtn);
      actions.appendChild(delBtn);
      listEl.appendChild(row);
    });
  }

  function openVersions(article) {
    var drawer = document.getElementById("versionDrawer");
    var mask = document.getElementById("versionMask");
    var body = document.getElementById("versionBody");
    if (!drawer || !body) return;
    var versions = article.versions || [];
    body.innerHTML = versions.length
      ? versions
          .slice()
          .reverse()
          .map(function (v) {
            return (
              '<div class="version-item"><strong>v' +
              v.v +
              "</strong><span>" +
              v.at +
              "</span><p>" +
              (v.note || "") +
              " · " +
              (v.title || "") +
              "</p></div>"
            );
          })
          .join("")
      : "<p class=\"side-hint\">暂无版本记录</p>";
    drawer.classList.remove("hidden");
    if (mask) mask.classList.remove("hidden");
  }

  var closeVersion = document.getElementById("closeVersion");
  var versionMask = document.getElementById("versionMask");
  if (closeVersion) {
    closeVersion.addEventListener("click", function () {
      document.getElementById("versionDrawer").classList.add("hidden");
      if (versionMask) versionMask.classList.add("hidden");
    });
  }
  if (versionMask) {
    versionMask.addEventListener("click", function () {
      document.getElementById("versionDrawer").classList.add("hidden");
      versionMask.classList.add("hidden");
    });
  }

  document.querySelectorAll("[data-manage-tab]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("[data-manage-tab]").forEach(function (b) {
        b.classList.remove("on");
      });
      btn.classList.add("on");
      renderManage();
    });
  });

  /* —— Admin —— */
  function renderAdmin() {
    var box = document.getElementById("adminQueue");
    if (!box || !TM) return;
    var list = TM.getAdminQueue();
    var pending = list.filter(function (i) { return i.status === "pending"; }).length;
    var pendingEl = document.getElementById("adminPending");
    if (pendingEl) pendingEl.textContent = String(pending);

    box.innerHTML = list
      .map(function (item) {
        return (
          '<div class="admin-row" data-admin-id="' +
          item.id +
          '"><div><div class="meta"><span>' +
          item.author +
          "</span><span>深度 " +
          item.depth +
          " · 可读 " +
          item.readability +
          " · 代码 " +
          item.codeQuality +
          '</span></div><h3>' +
          item.title +
          '</h3><p class="side-hint">' +
          item.reason +
          ' · 状态：' +
          item.status +
          '</p></div><div class="manage-actions">' +
          '<label class="score-edit">评分 <input type="number" min="0" max="100" value="' +
          item.score +
          '" data-score-input /></label>' +
          '<button class="btn" type="button" data-admin-act="approve">通过推荐</button>' +
          '<button class="btn" type="button" data-admin-act="reject">下架</button>' +
          "</div></div>"
        );
      })
      .join("");

    box.querySelectorAll(".admin-row").forEach(function (row) {
      var id = row.getAttribute("data-admin-id");
      var scoreInput = row.querySelector("[data-score-input]");
      if (scoreInput) {
        scoreInput.addEventListener("change", function () {
          TM.setAdminScore(id, Number(scoreInput.value) || 0);
          toast("质量分已更新");
        });
      }
      row.querySelectorAll("[data-admin-act]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var act = btn.getAttribute("data-admin-act");
          TM.setAdminStatus(id, act === "approve" ? "approved" : "rejected");
          toast(act === "approve" ? "已进入推荐池" : "已下架");
          renderAdmin();
        });
      });
    });
  }

  /* —— Follow author —— */
  var followBtn = document.getElementById("followAuthor");
  if (followBtn && TM) {
    var authorId = followBtn.getAttribute("data-author");
    function syncFollow() {
      var on = TM.isFollowing(authorId);
      followBtn.textContent = on ? "已关注" : "关注";
      followBtn.classList.toggle("btn-primary", !on);
    }
    syncFollow();
    followBtn.addEventListener("click", function () {
      if (!requireLogin("关注")) return;
      var res = TM.toggleFollow(authorId);
      if (!res.ok) {
        toast(res.msg);
        return;
      }
      syncFollow();
      toast(res.following ? "关注成功" : "已取消关注");
    });
  }

  /* —— Topic switch —— */
  var topicMap = {
    jvm: {
      title: "JVM 调优",
      desc: "AI 发现本周该话题讨论升温：近 30 天 12 篇新文章，高质量仅 3 篇，竞争中等，细分切口仍有空间。"
    },
    cache: {
      title: "缓存异常治理",
      desc: "穿透 / 击穿 / 雪崩相关讨论集中，语义搜索「怎么解决缓存穿透」命中量上升明显。"
    },
    k8s: {
      title: "容器化 JVM",
      desc: "K8s 场景下的内存配置成为高频踩坑点，热度近 7 日上升 98%。"
    }
  };
  document.querySelectorAll("[data-topic]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.getAttribute("data-topic");
      var data = topicMap[key];
      if (!data) return;
      var t = document.getElementById("topicTitle");
      var d = document.getElementById("topicDesc");
      if (t) t.textContent = data.title;
      if (d) d.textContent = data.desc;
      toast("已切换专题：" + data.title);
    });
  });

  /* —— Publish pipeline —— */
  function runPipeline() {
    var stepsEl = document.getElementById("pipelineSteps");
    var titleEl = document.getElementById("jobTitle");
    if (!stepsEl || !TM) return;
    var job = TM.getJob();
    if (!job) {
      stepsEl.innerHTML = '<li class="side-hint">暂无发布任务。请先在编辑器发布一篇文章。</li>';
      return;
    }
    if (titleEl) titleEl.textContent = job.title;
    function paint() {
      job = TM.getJob();
      stepsEl.innerHTML = job.steps
        .map(function (s, i) {
          return (
            '<li class="pipe-step ' +
            s.status +
            '"><span class="pipe-idx">' +
            (i + 1) +
            "</span><div><strong>" +
            s.name +
            "</strong><em>" +
            (s.status === "done" ? "完成" : s.status === "running" ? "处理中…" : "等待中") +
            "</em></div></li>"
          );
        })
        .join("");
    }
    paint();
    var i = 0;
    function next() {
      if (i >= job.steps.length) {
        toast("全部处理完成，已进入推荐队列");
        return;
      }
      TM.updateJobStep(i, "running");
      paint();
      setTimeout(function () {
        TM.updateJobStep(i, "done");
        paint();
        i += 1;
        setTimeout(next, 350);
      }, 700);
    }
    setTimeout(next, 400);
  }

  /* —— Article TOC (Feishu-like outline) —— */
  function bindArticleToc() {
    var links = document.querySelectorAll("[data-toc]");
    if (!links.length) return;

    var targets = [];
    links.forEach(function (link) {
      var id = (link.getAttribute("href") || "").replace("#", "");
      var el = document.getElementById(id);
      if (el) targets.push({ link: link, el: el });

      link.addEventListener("click", function (e) {
        e.preventDefault();
        var node = document.getElementById(id);
        if (!node) return;
        var top = node.getBoundingClientRect().top + window.pageYOffset - 88;
        window.scrollTo({ top: top, behavior: "smooth" });
        links.forEach(function (l) { l.classList.remove("on"); });
        link.classList.add("on");
        history.replaceState(null, "", "#" + id);
      });
    });

    if (!targets.length || !("IntersectionObserver" in window)) return;

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var id = entry.target.id;
          links.forEach(function (l) {
            var href = (l.getAttribute("href") || "").replace("#", "");
            l.classList.toggle("on", href === id);
          });
        });
      },
      { rootMargin: "-20% 0px -65% 0px", threshold: 0 }
    );
    targets.forEach(function (t) { io.observe(t.el); });
  }

  /* boot */
  renderGlobalNav();
  renderBackButton();
  renderAuthActions();
  renderProfile();
  renderHomePersonal();
  renderFavoritesPage();
  bindArticleLoop();
  bindArticleToc();
  renderManage();
  renderAdmin();
  runPipeline();
})();
