/* TechMind prototype state — localStorage */
(function (global) {
  var KEYS = {
    users: "tm_users",
    user: "tm_user",
    session: "tm_session",
    articles: "tm_articles",
    favorites: "tm_favorites",
    draft: "tm_draft",
    drafts: "tm_drafts",
    draftActive: "tm_draft_active",
    follows: "tm_follows",
    adminQueue: "tm_admin_queue",
    jobs: "tm_jobs"
  };

  var ROLE_LABEL = {
    reader: "读者",
    author: "作者",
    both: "读者 & 作者"
  };

  var DEFAULT_TAGS = ["Java", "Redis", "云原生", "前端", "AI", "JVM", "源码"];

  var DEMO_USER = {
    username: "demo",
    email: "demo@techmind.app",
    password: "demo1234",
    role: "both",
    tags: ["Java", "Redis", "JVM"],
    bio: "后端 / 源码爱好者",
    followers: 128,
    following: 36,
    createdAt: Date.now(),
    updatedAt: Date.now()
  };

  var SEED_ARTICLES = [
    {
      id: "a_seed_1",
      title: "Redisson 分布式锁源码分析：可重入与 WatchDog",
      subtitle: "从 Lua 到续期机制",
      content: "## 背景\n\n分布式锁实践。\n\n## WatchDog\n\n默认 30s 续期。",
      author: "demo",
      status: "published",
      createdAt: "2026-03-12",
      updatedAt: "2026-03-12",
      likes: 1200,
      favs: 430,
      score: 92,
      depth: 94,
      readability: 90,
      codeQuality: 93,
      tags: ["Redis", "分布式锁", "源码"],
      column: "Spring 源码深度解析",
      review: "approved",
      versions: [
        { v: 1, at: "2026-03-10 14:20", note: "初稿", title: "Redisson 锁浅析" },
        { v: 2, at: "2026-03-11 09:10", note: "补充 WatchDog", title: "Redisson 分布式锁源码分析" },
        { v: 3, at: "2026-03-12 18:00", note: "发布版", title: "Redisson 分布式锁源码分析：可重入与 WatchDog" }
      ]
    },
    {
      id: "a_seed_2",
      title: "GraalVM 在微服务中的落地实践",
      subtitle: "",
      content: "## 大纲\n\n- 背景\n- 落地步骤",
      author: "demo",
      status: "draft",
      createdAt: "2026-03-18",
      updatedAt: "2026-03-19",
      likes: 0,
      favs: 0,
      score: null,
      tags: ["GraalVM", "JVM"],
      column: "",
      review: "draft",
      versions: [
        { v: 1, at: "2026-03-18 21:00", note: "草稿创建", title: "GraalVM 在微服务中的落地实践" }
      ]
    }
  ];

  var SEED_ADMIN = [
    {
      id: "a_review_1",
      title: "缓存穿透问题排查手册",
      author: "钱七",
      score: 76,
      depth: 72,
      readability: 80,
      codeQuality: 74,
      status: "pending",
      reason: "待人工复核质量分"
    },
    {
      id: "a_review_2",
      title: "K8s 上的 JVM 内存配置踩坑实录",
      author: "李四",
      score: 84,
      depth: 85,
      readability: 82,
      codeQuality: 86,
      status: "pending",
      reason: "候选进入推荐池"
    },
    {
      id: "a_review_3",
      title: "聊聊缓存穿透那点事",
      author: "赵六",
      score: 61,
      depth: 55,
      readability: 70,
      codeQuality: 50,
      status: "pending",
      reason: "质量分偏低"
    }
  ];

  function read(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      if (!raw) return fallback;
      return JSON.parse(raw);
    } catch (e) {
      return fallback;
    }
  }

  function write(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function avatarLetter(name) {
    if (!name) return "?";
    return String(name).trim().charAt(0).toUpperCase();
  }

  function nowLabel() {
    var d = new Date();
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + m + "-" + day;
  }

  function nowDateTime() {
    var d = new Date();
    var pad = function (n) { return String(n).padStart(2, "0"); };
    return (
      d.getFullYear() +
      "-" +
      pad(d.getMonth() + 1) +
      "-" +
      pad(d.getDate()) +
      " " +
      pad(d.getHours()) +
      ":" +
      pad(d.getMinutes())
    );
  }

  function getUsers() {
    var users = read(KEYS.users, null);
    if (!users) {
      users = {};
      var legacy = read(KEYS.user, null);
      if (legacy && legacy.username) users[legacy.username] = legacy;
    }
    if (!users.demo) users.demo = Object.assign({}, DEMO_USER);
    write(KEYS.users, users);
    return users;
  }

  function findUser(account) {
    var users = getUsers();
    if (users[account]) return users[account];
    var keys = Object.keys(users);
    for (var i = 0; i < keys.length; i++) {
      if (users[keys[i]].email === account) return users[keys[i]];
    }
    return null;
  }

  function ensureArticles() {
    var list = read(KEYS.articles, null);
    if (!list) list = [];
    SEED_ARTICLES.forEach(function (seed) {
      if (!list.some(function (a) { return a.id === seed.id; })) {
        list.push(Object.assign({}, seed));
      }
    });
    write(KEYS.articles, list);
    return list;
  }

  function ensureAdmin() {
    var list = read(KEYS.adminQueue, null);
    if (!list) {
      list = SEED_ADMIN.slice();
      write(KEYS.adminQueue, list);
    }
    return list;
  }

  var Store = {
    ROLE_LABEL: ROLE_LABEL,
    DEFAULT_TAGS: DEFAULT_TAGS,
    DEMO: {
      username: DEMO_USER.username,
      email: DEMO_USER.email,
      password: DEMO_USER.password
    },

    getUser: function () {
      var session = read(KEYS.session, null);
      if (!session || !session.username) return null;
      return getUsers()[session.username] || null;
    },

    saveUser: function (user) {
      var users = getUsers();
      users[user.username] = user;
      write(KEYS.users, users);
      write(KEYS.user, user);
      return user;
    },

    updateUser: function (patch) {
      var user = Store.getUser();
      if (!user) return null;
      var users = getUsers();
      var oldName = user.username;
      var next = Object.assign({}, user, patch, { updatedAt: Date.now() });
      if (patch.username && patch.username !== oldName) {
        delete users[oldName];
        var session = read(KEYS.session, null);
        if (session) {
          session.username = next.username;
          write(KEYS.session, session);
        }
      }
      users[next.username] = next;
      write(KEYS.users, users);
      write(KEYS.user, next);
      return next;
    },

    isLoggedIn: function () {
      return !!Store.getUser();
    },

    login: function (account, password) {
      getUsers();
      var user = findUser(account);
      if (!user) return { ok: false, msg: "账号不存在，请先注册" };
      if (user.password !== password) return { ok: false, msg: "密码错误" };
      write(KEYS.session, { at: Date.now(), username: user.username });
      write(KEYS.user, user);
      return { ok: true, user: user };
    },

    logout: function () {
      localStorage.removeItem(KEYS.session);
    },

    register: function (payload) {
      var users = getUsers();
      if (findUser(payload.username) || findUser(payload.email)) {
        return { ok: false, msg: "用户名或邮箱已被注册" };
      }
      var user = {
        username: payload.username,
        email: payload.email,
        password: payload.password,
        role: payload.role || "reader",
        tags: payload.tags || [],
        bio: payload.bio || "这位用户还没有填写简介",
        followers: 0,
        following: 0,
        createdAt: Date.now(),
        updatedAt: Date.now()
      };
      users[user.username] = user;
      write(KEYS.users, users);
      write(KEYS.user, user);
      write(KEYS.session, { at: Date.now(), username: user.username });
      ensureArticles();
      if (!read(KEYS.favorites, null)) write(KEYS.favorites, []);
      return { ok: true, user: user };
    },

    getArticles: function () {
      return ensureArticles();
    },

    getMyArticles: function () {
      var user = Store.getUser();
      if (!user) return [];
      return ensureArticles().filter(function (a) {
        return a.author === user.username;
      });
    },

    getArticleById: function (id) {
      return ensureArticles().find(function (a) {
        return a.id === id;
      }) || null;
    },

    addArticle: function (article) {
      var user = Store.getUser();
      var list = ensureArticles();
      var title = article.title || "未命名文章";
      var item = Object.assign(
        {
          id: "a_" + Date.now(),
          author: user ? user.username : "匿名",
          status: "published",
          createdAt: nowLabel(),
          updatedAt: nowLabel(),
          likes: 0,
          favs: 0,
          score: Math.floor(80 + Math.random() * 15),
          depth: Math.floor(78 + Math.random() * 18),
          readability: Math.floor(78 + Math.random() * 18),
          codeQuality: Math.floor(78 + Math.random() * 18),
          tags: [],
          column: "",
          review: "pending",
          versions: []
        },
        article
      );
      item.versions = [
        {
          v: 1,
          at: nowDateTime(),
          note: item.status === "draft" ? "草稿创建" : "发布版",
          title: title
        }
      ];
      list.unshift(item);
      write(KEYS.articles, list);
      return item;
    },

    updateArticle: function (id, patch) {
      var list = ensureArticles();
      var idx = list.findIndex(function (a) { return a.id === id; });
      if (idx < 0) return null;
      var prev = list[idx];
      var next = Object.assign({}, prev, patch, { updatedAt: nowLabel() });
      if (patch.title && patch.title !== prev.title) {
        var versions = (prev.versions || []).slice();
        versions.push({
          v: versions.length + 1,
          at: nowDateTime(),
          note: patch.versionNote || "内容更新",
          title: patch.title
        });
        next.versions = versions;
      }
      list[idx] = next;
      write(KEYS.articles, list);
      return next;
    },

    deleteArticle: function (id) {
      var list = ensureArticles().filter(function (a) { return a.id !== id; });
      write(KEYS.articles, list);
      return list;
    },

    getDraft: function () {
      // 兼容旧单草稿；优先返回当前 active 多草稿
      var active = localStorage.getItem(KEYS.draftActive);
      if (active) {
        var map = read(KEYS.drafts, {});
        if (map[active]) return map[active];
      }
      return read(KEYS.draft, null);
    },

    listDrafts: function () {
      var map = read(KEYS.drafts, {});
      return Object.keys(map)
        .map(function (id) { return map[id]; })
        .filter(Boolean)
        .sort(function (a, b) { return (b.updatedAt || 0) - (a.updatedAt || 0); });
    },

    getDraftById: function (id) {
      var map = read(KEYS.drafts, {});
      return map[id] || null;
    },

    getActiveDraftId: function () {
      return localStorage.getItem(KEYS.draftActive);
    },

    setActiveDraftId: function (id) {
      if (id) localStorage.setItem(KEYS.draftActive, id);
      else localStorage.removeItem(KEYS.draftActive);
    },

    createDraftId: function () {
      return "d_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
    },

    saveDraft: function (draft) {
      var id = draft.id || Store.createDraftId();
      var next = Object.assign({}, draft, { id: id, updatedAt: Date.now() });
      var map = read(KEYS.drafts, {});
      map[id] = next;
      write(KEYS.drafts, map);
      Store.setActiveDraftId(id);
      // 兼容旧 key（单草稿镜像）
      write(KEYS.draft, next);
      return next;
    },

    createNewDraft: function () {
      return Store.saveDraft({
        id: Store.createDraftId(),
        title: "",
        subtitle: "",
        content: "",
        tags: [],
        summary: "",
        column: "",
        category: "后端"
      });
    },

    clearDraft: function (id) {
      var active = id || localStorage.getItem(KEYS.draftActive);
      if (active) {
        var map = read(KEYS.drafts, {});
        delete map[active];
        write(KEYS.drafts, map);
        if (localStorage.getItem(KEYS.draftActive) === active) {
          localStorage.removeItem(KEYS.draftActive);
        }
      }
      localStorage.removeItem(KEYS.draft);
    },

    getFavorites: function () {
      return read(KEYS.favorites, []);
    },

    toggleFavorite: function (item) {
      var list = Store.getFavorites();
      var idx = list.findIndex(function (f) { return f.id === item.id; });
      if (idx >= 0) {
        list.splice(idx, 1);
        write(KEYS.favorites, list);
        return { added: false, list: list };
      }
      list.unshift(
        Object.assign({}, item, {
          favoritedAt: nowLabel(),
          folder: item.folder || "distributed",
          unread: true
        })
      );
      write(KEYS.favorites, list);
      return { added: true, list: list };
    },

    isFavorited: function (id) {
      return Store.getFavorites().some(function (f) { return f.id === id; });
    },

    getFollows: function () {
      return read(KEYS.follows, []);
    },

    isFollowing: function (authorId) {
      var user = Store.getUser();
      if (!user) return false;
      return Store.getFollows().some(function (f) {
        return f.from === user.username && f.to === authorId;
      });
    },

    toggleFollow: function (authorId) {
      var user = Store.getUser();
      if (!user) return { ok: false, msg: "请先登录" };
      if (authorId === user.username) return { ok: false, msg: "不能关注自己" };
      var list = Store.getFollows();
      var idx = list.findIndex(function (f) {
        return f.from === user.username && f.to === authorId;
      });
      if (idx >= 0) {
        list.splice(idx, 1);
        write(KEYS.follows, list);
        return { ok: true, following: false };
      }
      list.push({ from: user.username, to: authorId, at: nowLabel() });
      write(KEYS.follows, list);
      return { ok: true, following: true };
    },

    getAdminQueue: function () {
      return ensureAdmin();
    },

    setAdminStatus: function (id, status) {
      var list = ensureAdmin();
      var item = list.find(function (a) { return a.id === id; });
      if (!item) return null;
      item.status = status;
      write(KEYS.adminQueue, list);
      return item;
    },

    setAdminScore: function (id, score) {
      var list = ensureAdmin();
      var item = list.find(function (a) { return a.id === id; });
      if (!item) return null;
      item.score = score;
      write(KEYS.adminQueue, list);
      return item;
    },

    createPublishJob: function (article) {
      var job = {
        id: "job_" + Date.now(),
        articleId: article.id,
        title: article.title,
        createdAt: nowDateTime(),
        steps: [
          { key: "embed", name: "Embedding 向量化", status: "pending" },
          { key: "summary", name: "生成智能导读", status: "pending" },
          { key: "tags", name: "推荐标签", status: "pending" },
          { key: "score", name: "内容质量评分", status: "pending" },
          { key: "related", name: "关联文章发现", status: "pending" },
          { key: "queue", name: "进入推荐队列", status: "pending" }
        ]
      };
      write(KEYS.jobs, job);
      return job;
    },

    getJob: function () {
      return read(KEYS.jobs, null);
    },

    updateJobStep: function (index, status) {
      var job = Store.getJob();
      if (!job || !job.steps[index]) return null;
      job.steps[index].status = status;
      write(KEYS.jobs, job);
      return job;
    },

    avatarLetter: avatarLetter,
    roleLabel: function (role) {
      return ROLE_LABEL[role] || role || "读者";
    },
    nowDateTime: nowDateTime
  };

  getUsers();
  ensureArticles();
  ensureAdmin();
  global.TM = Store;
})(window);
