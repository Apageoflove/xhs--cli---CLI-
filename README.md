# xiaohongshu-cli

Xiaohongshu (RED) CLI — search, read, interact, post, and visualize data, all from the terminal 📕

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)]()

[English](#features) | [中文](#功能特性)

Two editions available: **Python interactive REPL** (recommended) and **Go CLI tool**, sharing the same login session.

For detailed walkthrough with screenshots, see [小红书CLI使用指南.md](./小红书CLI使用指南.md)

---

## Features

- 🔐 **Auth** — auto-extract Firefox cookies, status check, whoami
- 🔍 **Search** — notes by keyword, user search, topic search
- 📖 **Reading** — note detail, comments, sub-comments, user profiles
- 📰 **Feed** — recommendation feed, hot/trending by category
- 👥 **Social** — follow/unfollow, favorites, likes
- 👍 **Interactions** — like, favorite, comment, reply, delete
- ✍️ **Creator** — post image notes, my-notes list, delete
- 🔔 **Notifications** — unread count, mentions, likes, new followers
- 📊 **Data Visualization** — statistics, keyword analysis, terminal charts, word cloud, cover preview (Python edition)
- 🌈 **Themes** — ocean blue, forest green, sunset red, purple
- 🛡️ **Anti-detection** — consistent Chrome fingerprint, Gaussian jitter, captcha cooldown, exponential backoff
- 📊 **Structured output** — `--yaml` / `--json`; non-TTY defaults to YAML

---

## Quick Start

### Python Edition (Recommended)

```python
# Option 1: Double-click the desktop icon "小红书 CLI"

# Option 2: Run the launcher script
./启动小红书CLI.sh

# Option 3: Run directly
.venv/bin/python xhs_repl.py
```

Auto-extracts login credentials from Firefox on first launch.

### Go Edition

```python
# Single-shot execution, exits after completion
./xhs-cli-go/bin/xhs search "美食"
./xhs-cli-go/bin/xhs status
./xhs-cli-go/bin/xhs read abc123
```

### Build from Source

```python
# Python edition
git clone https://github.com/Apageoflove/xhs--cli---CLI-.git
cd xhs--cli---CLI-
uv sync

# Go edition (requires Go)
cd xhs-cli-go
go build -o bin/xhs ./cmd/xhs
```

---

## Edition Comparison

| Feature | Python (Interactive REPL) | Go (CLI Tool) |
|---------|---------------------------|---------------|
| Launch | `./启动小红书CLI.sh` or desktop icon | `./xhs-cli-go/bin/xhs <cmd>` |
| Mode | Persistent session, autocomplete | Single-shot, pipe-friendly |
| UI | Rich tables, panels, progress bars | Plain text |
| Visualization | stats / analyze / chart / wordcloud / covers | None |
| Browser open | `open 1` | None |
| Themes | Yes | None |
| Dependencies | Python 3.10+, .venv | Single static binary |
| Best for | Daily browsing, data analysis | Scripts, batch ops, cron |

---

## Usage

Commands below are used in the Python interactive REPL. Search results are numbered (1, 2, 3...); use the number in place of note IDs.

### Auth

```python
xhs >: login                    # Extract cookies from browser
xhs >: status                   # Check login status
xhs >: whoami                   # View profile
xhs >: logout                   # Clear cookies
```

### Search & Reading

```python
xhs >: search "美食"             # Search notes
xhs >: search "旅行" --sort popular   # Sort: general, popular, latest
xhs >: search-user "用户名"      # Search users
xhs >: topics "美食"             # Search topics
xhs >: feed                      # Recommendation feed
xhs >: hot                       # Hot notes
xhs >: read 1                    # Read the 1st result
xhs >: comments 1                # View comments for the 1st result
xhs >: user <user_id>            # View user profile
xhs >: user-posts <user_id>      # View user's notes
```

### Interactions

```python
xhs >: like 1                    # Like
xhs >: like 1 --undo             # Unlike
xhs >: favorite 1                # Favorite
xhs >: unfavorite 1              # Unfavorite
xhs >: comment 1 -c "好看！"     # Post comment
xhs >: reply 1 --comment-id X -c "谢谢"  # Reply to comment
```

### Social & Creator

```python
xhs >: follow <user_id>          # Follow
xhs >: unfollow <user_id>        # Unfollow
xhs >: favorites                 # My favorites
xhs >: likes                     # My likes
xhs >: my-notes                  # My notes
xhs >: post --title "Title" --body "Body"  # Post note
xhs >: delete <note_id>          # Delete note
```

### Notifications

```python
xhs >: unread                    # Unread count
xhs >: notifications             # View notifications
xhs >: notifications --type likes       # Like/favorite notifications
xhs >: notifications --type connections  # New follower notifications
```

### Open in Browser

```python
xhs >: open 1       # Open the 1st search result
xhs >: open 3       # Open the 3rd
xhs >: open abc123  # Open by note ID
```

Full URLs are shown below search results — **Ctrl+Click** in terminal also works.

---

## Data Visualization

After searching, analyze and visualize results:

| Command | Description |
|---------|-------------|
| `stats` | Statistics table (total/avg likes, favorites, comments) |
| `analyze` | Keyword analysis + engagement trends |
| `chart` | Terminal bar chart (likes/favorites/comments) |
| `chart pie` | Terminal pie chart |
| `wordcloud` | Generate word cloud image (opens in browser) |
| `covers` | Cover image grid preview |

All visualization commands work on the **most recent search results**. Data refreshes automatically after each new search.

> For full examples with screenshots, see [小红书CLI使用指南.md](./小红书CLI使用指南.md#数据可视化)

---

## Themes

| Command | Theme |
|---------|-------|
| `theme ocean` | Ocean Blue |
| `theme forest` | Forest Green |
| `theme sunset` | Sunset Red |
| `theme purple` | Purple |
| `theme default` | Default |

---

## Authentication

1. **Browser cookies** — auto-extracted from Firefox (including Snap installs)
2. **Saved cookies** — loaded from `cookies.json`
3. **QR code login** — browser-assisted login with terminal QR code (`xhs login --qrcode`)

Saved cookies are valid for **7 days**. Auto-refresh from browser on expiry.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT` | `auto` | Output format: `json`, `yaml`, `rich`, `auto` (→ YAML when non-TTY) |

---

## Project Structure

```python
reds/
├── 启动小红书CLI.sh          # Launcher script
├── xhs_repl.py               # Interactive REPL (Python)
├── xhs_cli/                  # Python core library
│   ├── cli.py                # CLI entry point
│   ├── client.py             # API client
│   ├── client_mixins.py      # API endpoints
│   ├── cookies.py            # Cookie management
│   ├── signing.py            # Request signing
│   └── commands/             # Command implementations
├── xhs-cli-go/               # Go edition
│   └── bin/xhs               # Compiled binary
├── plugins/                  # Visualization plugins
│   ├── analyzer.py           # Keyword analysis
│   ├── charts.py             # Terminal charts
│   └── image_preview.py      # Word cloud / cover images
├── assets/
│   ├── icon.png              # Official icon
│   └── fonts/                # Chinese fonts
├── tests/                    # Test suite (166 tests)
└── .venv/                    # Python virtual environment
```

---

## Development

```python
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Unit tests only (no network)
uv run pytest tests/ -v --ignore=tests/test_integration.py

# Lint
uv run ruff check .
```

---

## Troubleshooting

- **`NoCookieError`** — Log in at xiaohongshu.com in your browser, then run `xhs >: login`
- **`NeedVerifyError`** — Captcha triggered. Complete it in browser, then retry.
- **`IpBlockedError`** — IP restricted. Switch networks (mobile hotspot or VPN).
- **`SessionExpiredError`** — Cookies expired. Run `xhs >: login` to refresh.
- **Slow requests** — Built-in Gaussian jitter (~1-1.5s) mimics human browsing to avoid detection.

---

## 功能特性

- 🔐 **认证** — 自动从 Firefox 浏览器提取 Cookie，状态检查，用户信息
- 🔍 **搜索** — 按关键词搜索笔记、用户、话题
- 📖 **阅读** — 笔记详情、评论、子评论、用户主页
- 📰 **发现** — 推荐 Feed、热门笔记
- 👥 **社交** — 关注/取关、收藏夹、点赞列表
- 👍 **互动** — 点赞、收藏、评论、回复、删除
- ✍️ **创作者** — 发布图文笔记、我的笔记列表、删除
- 🔔 **通知** — 未读数、@、点赞、新关注
- 📊 **数据可视化** — 统计分析、关键词热度、终端图表、词云、封面预览（Python 版）
- 🌈 **主题切换** — 海洋蓝、森林绿、日落红、紫色
- 🛡️ **反风控** — Chrome 指纹一致性、高斯抖动延迟、验证码冷却、指数退避
- 📊 **结构化输出** — `--yaml` / `--json`，非 TTY 默认输出 YAML

详细图文指南见 [小红书CLI使用指南.md](./小红书CLI使用指南.md)

---

## License

Apache-2.0
