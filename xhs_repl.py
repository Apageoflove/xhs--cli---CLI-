#!/usr/bin/env python3
"""
xhs 交互式终端 — 类似 Claude Code 的 REPL 界面
支持所有 30 条命令，带彩色输出、自动补全、背景自定义
"""

import os
import sys
import json
import time
import shutil
import readline
import threading
from pathlib import Path

# 确保在项目虚拟环境中运行
PROJECT_DIR = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_DIR / ".venv"
sys.path.insert(0, str(PROJECT_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import box

console = Console()

# ─── 配置 ──────────────────────────────────────────────────────────

CONFIG_DIR = Path.home() / ".xiaohongshu-cli"
CONFIG_FILE = CONFIG_DIR / "xhs_repl_config.json"

DEFAULT_CONFIG = {
    "theme": "default",
    "background_image": "",
    "show_tips": True,
}

THEMES = {
    "default": {"prompt": "bold magenta", "accent": "cyan", "success": "green", "error": "red", "title": "bold yellow"},
    "ocean": {"prompt": "bold blue", "accent": "cyan", "success": "green", "error": "red", "title": "bold cyan"},
    "forest": {"prompt": "bold green", "accent": "yellow", "success": "bright_green", "error": "red", "title": "bold green"},
    "sunset": {"prompt": "bold red", "accent": "yellow", "success": "green", "error": "bright_red", "title": "bold yellow"},
    "purple": {"prompt": "bold magenta", "accent": "bright_magenta", "success": "green", "error": "red", "title": "bold magenta"},
}

TIPS = [
    "输入 search \"关键词\" 搜索笔记",
    "输入 read 1 读取上一条搜索结果的第1条",
    "输入 like 1 给第1条搜索结果点赞",
    "输入 hot -c travel 查看旅行热门",
    "输入 theme ocean 切换主题",
    "输入 help 查看所有命令",
    "输入 feed 查看推荐首页",
    "输入 notifications 查看通知",
    "输入 whoami 查看当前登录用户",
]

def load_config():
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


# ─── 命令列表 ───────────────────────────────────────────────────────

ALL_COMMANDS = [
    "search", "read", "comments", "sub-comments", "user", "user-posts",
    "feed", "hot", "topics", "search-user", "my-notes",
    "like", "favorite", "unfavorite", "comment", "reply", "delete-comment",
    "follow", "unfollow", "favorites", "likes",
    "notifications", "unread",
    "post", "delete",
    "login", "status", "whoami", "logout", "import-cookies",
    # REPL 专属命令
    "help", "exit", "quit", "clear", "theme", "config", "history", "tips", "open",
    "analyze", "chart", "wordcloud", "stats", "covers",
]


# ─── readline 自动补全 ──────────────────────────────────────────────

class XhsCompleter:
    def __init__(self):
        self.commands = ALL_COMMANDS
        self.matches = []

    def complete(self, text, state):
        if state == 0:
            line = readline.get_line_buffer().lstrip()
            if ' ' not in line:
                self.matches = [c for c in self.commands if c.startswith(text)]
            else:
                self.matches = []
        if state < len(self.matches):
            return self.matches[state]
        return None


# ─── 背景图处理 ──────────────────────────────────────────────────────

def draw_background_image(image_path):
    """在终端绘制背景图（使用 Unicode 块字符）"""
    if not image_path or not Path(image_path).exists():
        return

    try:
        from PIL import Image
        img = Image.open(image_path)
        term_w = min(shutil.get_terminal_size().columns, 120)
        term_h = min(20, shutil.get_terminal_size().lines // 3)
        img = img.resize((term_w // 2, term_h))
        img = img.convert("RGB")

        for y in range(term_h):
            line = ""
            for x in range(term_w // 2):
                r, g, b = img.getpixel((x, y))
                line += f"\033[48;2;{r};{g};{b}m \033[0m"
            console.print(line)
    except Exception:
        pass


# ─── 欢迎界面 ────────────────────────────────────────────────────────

def show_banner(cfg):
    theme_name = cfg.get("theme", "default")
    theme = THEMES.get(theme_name, THEMES["default"])

    banner = Text()
    banner.append("╔══════════════════════════════════════════╗\n", style=theme["title"])
    banner.append("║    📕  xhs 交互式终端  —  小红书 CLI     ║\n", style=theme["title"])
    banner.append("╚══════════════════════════════════════════╝\n", style=theme["title"])
    banner.append("\n  输入 help 查看命令  |  输入 exit 退出", style=theme["accent"])
    banner.append("\n  输入 search \"关键词\" 开始搜索", style="dim")
    console.print(banner)
    console.print()


# ─── 帮助界面 ────────────────────────────────────────────────────────

def show_help():
    table = Table(title="xhs 命令列表", box=box.ROUNDED, show_lines=False)
    table.add_column("分类", style="bold yellow")
    table.add_column("命令", style="cyan")
    table.add_column("说明", style="white")
    table.add_column("示例", style="dim")

    rows = [
        ("认证", "login", "登录（自动提取浏览器cookie）", "login / login --qrcode"),
        ("认证", "status", "检查登录状态", "status"),
        ("认证", "whoami", "查看当前用户详情", "whoami"),
        ("认证", "logout", "退出登录", "logout"),
        ("搜索", "search \"关键词\"", "搜索笔记", "search \"美食\" --sort popular"),
        ("搜索", "search-user \"名字\"", "搜索用户", "search-user \"摄影师\""),
        ("搜索", "topics \"话题\"", "搜索话题", "topics \"美食探店\""),
        ("阅读", "read <ID或序号>", "读取笔记详情", "read 1 / read abc123"),
        ("阅读", "comments <ID或序号>", "查看评论", "comments 1 / comments abc --all"),
        ("阅读", "sub-comments <笔记> <评论>", "查看评论回复", "sub-comments abc cmt123"),
        ("阅读", "user <用户ID>", "查看用户资料", "user 5f2e123"),
        ("阅读", "user-posts <用户ID>", "用户发布的笔记", "user-posts 5f2e123"),
        ("阅读", "feed", "推荐首页", "feed"),
        ("阅读", "hot -c <分类>", "热门笔记", "hot / hot -c travel"),
        ("阅读", "my-notes", "我的笔记", "my-notes --page 1"),
        ("互动", "like <ID或序号>", "点赞/取消点赞", "like 1 / like abc --undo"),
        ("互动", "favorite <ID或序号>", "收藏", "favorite 1"),
        ("互动", "unfavorite <ID或序号>", "取消收藏", "unfavorite 1"),
        ("互动", "comment <ID> -c \"内容\"", "发表评论", "comment 1 -c \"好看！\""),
        ("互动", "reply <ID> --comment-id X -c \"内容\"", "回复评论", "reply 1 --comment-id 123 -c \"谢谢\""),
        ("互动", "delete-comment <笔记> <评论>", "删除评论", "delete-comment abc cmt123 -y"),
        ("社交", "follow <用户ID>", "关注", "follow 5f2e123"),
        ("社交", "unfollow <用户ID>", "取消关注", "unfollow 5f2e123"),
        ("社交", "favorites", "收藏列表", "favorites / favorites <用户ID>"),
        ("社交", "likes", "点赞列表", "likes / likes <用户ID>"),
        ("创作", "post --title \"标题\"", "发布笔记", "post --title \"标题\" --body \"正文\""),
        ("创作", "delete <笔记ID>", "删除笔记", "delete abc123 -y"),
        ("通知", "unread", "未读通知数", "unread"),
        ("通知", "notifications", "查看通知", "notifications / notifications --type likes"),
        ("终端", "theme <主题名>", "切换主题", "theme ocean"),
        ("终端", "open <序号/ID/URL>", "在浏览器打开笔记", "open 1 / open abc123"),
        ("可视化", "analyze", "关键词分析 + 趋势分析", "analyze"),
        ("可视化", "chart [pie]", "终端柱状图/饼图", "chart / chart pie"),
        ("可视化", "wordcloud", "生成并打开词云图", "wordcloud"),
        ("可视化", "stats", "统计信息表格", "stats"),
        ("可视化", "covers", "显示封面图网格", "covers"),
        ("终端", "clear", "清屏", "clear"),
        ("终端", "exit / quit", "退出", "exit"),
    ]

    for row in rows:
        table.add_row(*row)

    console.print(table)
    console.print("\n[dim]快捷方式：数字序号（如 read 1）可复用上次搜索结果[/dim]")
    console.print("[dim]主题列表：default / ocean / forest / sunset / purple[/dim]\n")


# ─── 执行命令 ────────────────────────────────────────────────────────

# 保存最近一次搜索的原始 items，供可视化/分析用
_LAST_ITEMS = []

def _load_last_items():
    """返回上次搜索结果的 items 列表。"""
    return _LAST_ITEMS


def _save_last_items(data):
    """从 API 响应中提取并缓存 items。"""
    global _LAST_ITEMS
    if isinstance(data, dict) and data.get("ok"):
        payload = data.get("data", {})
        if isinstance(payload, dict) and "items" in payload:
            _LAST_ITEMS = payload["items"]
        elif isinstance(payload, list):
            _LAST_ITEMS = payload


def run_xhs_command(args_str, cfg):
    """调用 xhs CLI 执行命令"""
    theme_name = cfg.get("theme", "default")
    theme = THEMES.get(theme_name, THEMES["default"])

    parts = args_str.strip().split()
    if not parts:
        return

    cmd = parts[0]
    rest_args = parts[1:]

    # REPL 内置命令
    if cmd in ("exit", "quit"):
        console.print("[bold]👋 再见！[/bold]")
        sys.exit(0)

    elif cmd == "help":
        show_help()
        return

    elif cmd == "clear":
        os.system("clear")
        return

    elif cmd == "theme":
        if not rest_args:
            current = cfg.get("theme", "default")
            console.print(f"当前主题: [bold]{current}[/bold]")
            console.print(f"可用主题: {', '.join(THEMES.keys())}")
            console.print("用法: theme <主题名>")
            return
        t = rest_args[0]
        if t in THEMES:
            cfg["theme"] = t
            save_config(cfg)
            console.print(f"[green]✓ 主题已切换为 {t}[/green]")
        else:
            console.print(f"[red]未知主题: {t}[/red]")
            console.print(f"可用: {', '.join(THEMES.keys())}")
        return

    elif cmd == "tips":
        import random
        tip = random.choice(TIPS)
        console.print(Panel(tip, title="💡 小提示", border_style="cyan"))
        return

    elif cmd == "config":
        console.print(Panel(json.dumps(cfg, indent=2, ensure_ascii=False), title="⚙️ 配置", border_style="cyan"))
        return

    elif cmd == "background":
        if not rest_args:
            console.print(f"当前背景: {cfg.get('background_image', '未设置')}")
            console.print("用法: background <图片路径>  或  background clear")
            return
        if rest_args[0] == "clear":
            cfg["background_image"] = ""
            save_config(cfg)
            console.print("[green]✓ 背景已清除[/green]")
        else:
            path = " ".join(rest_args)
            if Path(path).exists():
                cfg["background_image"] = str(Path(path).resolve())
                save_config(cfg)
                console.print(f"[green]✓ 背景已设置: {path}[/green]")
            else:
                console.print(f"[red]文件不存在: {path}[/red]")
        return

    elif cmd == "history":
        hist_len = readline.get_current_history_length()
        console.print(f"[cyan]命令历史（共 {hist_len} 条）:[/cyan]")
        for i in range(max(1, hist_len - 20), hist_len + 1):
            line = readline.get_history_item(i)
            if line:
                console.print(f"  {i:3d}  {line}")
        return

    elif cmd == "open":
        import webbrowser
        from xhs_cli.cookies import get_note_by_index, load_token_cache

        if not rest_args:
            console.print("[yellow]用法: open <序号或笔记ID或URL>[/yellow]")
            console.print("[dim]示例: open 1  — 在浏览器打开上次搜索的第1条[/dim]")
            return

        ref = rest_args[0]

        # 尝试从索引缓存解析
        note_id = ""
        xsec_token = ""
        if ref.isdigit():
            entry = get_note_by_index(int(ref))
            if entry:
                note_id = entry.get("note_id", "")
                xsec_token = entry.get("xsec_token", "")
            else:
                console.print(f"[red]序号 {ref} 不存在，请先运行搜索[/red]")
                return
        elif "xiaohongshu.com" in ref:
            from xhs_cli.formatter import parse_note_reference
            note_id, xsec_token, _ = parse_note_reference(ref)
        else:
            note_id = ref
            cache = load_token_cache()
            cached = cache.get(note_id, {})
            xsec_token = cached.get("token", "")

        if not note_id:
            console.print("[red]无法解析笔记引用[/red]")
            return

        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if xsec_token:
            url += f"?xsec_token={xsec_token}&xsec_source=pc_feed"

        console.print(f"[cyan]正在打开: {url}[/cyan]")
        webbrowser.open(url)
        return

    elif cmd == "analyze":
        # 关键词分析
        items = _load_last_items()
        if not items:
            console.print("[yellow]没有搜索数据，请先 search[/yellow]")
            return
        from plugins.analyzer import analyze_search_results, show_keyword_analysis, show_trend_analysis
        analysis = analyze_search_results(items)
        show_keyword_analysis(analysis)
        show_trend_analysis(items)
        console.print("[dim]输入 wordcloud 生成词云图[/dim]")
        return

    elif cmd == "chart":
        # 终端图表
        items = _load_last_items()
        if not items:
            console.print("[yellow]没有搜索数据，请先 search[/yellow]")
            return
        from plugins.charts import plot_engagement_chart, plot_engagement_pie
        if rest_args and rest_args[0] == "pie":
            plot_engagement_pie(items)
        else:
            plot_engagement_chart(items)
        return

    elif cmd == "wordcloud":
        # 生成词云
        items = _load_last_items()
        if not items:
            console.print("[yellow]没有搜索数据，请先 search[/yellow]")
            return
        from plugins.analyzer import analyze_search_results, generate_wordcloud
        analysis = analyze_search_results(items)
        kw = rest_args[0] if rest_args else "xhs"
        path = generate_wordcloud(analysis, keyword=kw)
        if path:
            import webbrowser
            webbrowser.open(path)
        return

    elif cmd == "stats":
        # 统计表
        items = _load_last_items()
        if not items:
            console.print("[yellow]没有搜索数据，请先 search[/yellow]")
            return
        from plugins.charts import show_stats_table
        show_stats_table(items)
        return

    elif cmd == "covers":
        # 封面图网格
        items = _load_last_items()
        if not items:
            console.print("[yellow]没有搜索数据，请先 search[/yellow]")
            return
        urls = []
        for item in items[:20]:
            card = item.get("note_card", item) if isinstance(item, dict) else {}
            img_list = card.get("image_list", []) if isinstance(card, dict) else []
            if img_list and isinstance(img_list, list):
                url = img_list[0].get("url_default", img_list[0].get("url", ""))
                if url:
                    urls.append(url)
        if urls:
            from plugins.image_preview import render_cover_grid
            render_cover_grid(urls)
        else:
            console.print("[yellow]没有封面图数据[/yellow]")
        return

    # 调用真正的 xhs 命令
    import subprocess
    venv_python = str(VENV_DIR / "bin" / "python")

    # 先用 JSON 模式拿到数据供插件用
    json_cmd = [venv_python, "-m", "xhs_cli"] + parts
    try:
        json_result = subprocess.run(
            json_cmd,
            capture_output=True, text=True, timeout=120,
            cwd=str(PROJECT_DIR),
            env={**os.environ, "OUTPUT": "json"},
        )
        if json_result.stdout.strip():
            try:
                data = json.loads(json_result.stdout.strip())
                _save_last_items(data)
            except (json.JSONDecodeError, ValueError):
                pass
    except Exception:
        pass

    # 再用 Rich 模式输出到终端（用户看到漂亮的表格）
    rich_cmd = [venv_python, "-m", "xhs_cli"] + parts
    try:
        subprocess.run(
            rich_cmd,
            timeout=120,
            cwd=str(PROJECT_DIR),
            env={**os.environ, "OUTPUT": "rich"},
        )
    except subprocess.TimeoutExpired:
        console.print(f"[{theme['error']}]⏱ 请求超时，请重试[/{theme['error']}]")
    except KeyboardInterrupt:
        console.print(f"\n[{theme['error']}]已取消[/{theme['error']}]")
    except Exception as e:
        console.print(f"[{theme['error']}]错误: {e}[/{theme['error']}]")


def pretty_output(data, theme):
    """美化显示 JSON 输出"""
    if data.get("ok"):
        # 成功输出
        payload = data.get("data", {})
        if isinstance(payload, dict):
            # 搜索结果
            if "items" in payload:
                items = payload["items"]
                console.print(Panel(
                    f"[bold]搜索结果（{len(items)} 条）[/bold]",
                    border_style=theme["success"],
                ))
                table = Table(box=box.SIMPLE, show_lines=False)
                table.add_column("#", style="bold", width=4)
                table.add_column("标题", style="cyan", max_width=40)
                table.add_column("用户", style="yellow", max_width=12)
                table.add_column("点赞", style="red", width=8)
                table.add_column("链接", style="cyan", no_wrap=True, max_width=50)
                for i, item in enumerate(items[:20], 1):
                    note_card = item.get("note_card", {}) if isinstance(item, dict) else {}
                    title = note_card.get("display_title", "") or note_card.get("title", "") or "(无标题)"
                    user = note_card.get("user", {}) if isinstance(note_card, dict) else {}
                    nickname = user.get("nickname", "") if isinstance(user, dict) else ""
                    interact = note_card.get("interact_info", {}) if isinstance(note_card, dict) else {}
                    liked = interact.get("liked_count", "") if isinstance(interact, dict) else ""
                    nid = item.get("id", note_card.get("note_id", "")) if isinstance(item, dict) else ""
                    xsec = item.get("xsec_token", "") if isinstance(item, dict) else ""
                    url = f"https://www.xiaohongshu.com/explore/{nid}"
                    if xsec:
                        url += f"?xsec_token={xsec}&xsec_source=pc_search"
                    table.add_row(str(i), title[:40], nickname[:12], str(liked), url)
                console.print(table)

            # 评论
            elif "comments" in payload:
                comments = payload["comments"]
                total = payload.get("total_fetched", len(comments))
                console.print(Panel(
                    f"[bold]评论（{total} 条）[/bold]",
                    border_style=theme["success"],
                ))
                for i, c in enumerate(comments[:20], 1):
                    if not isinstance(c, dict):
                        continue
                    user_info = c.get("user_info", {})
                    nickname = user_info.get("nickname", "?") if isinstance(user_info, dict) else "?"
                    content = c.get("content", "")
                    like_count = c.get("like_count", 0) or 0
                    sub_count = c.get("sub_comment_count", 0) or 0
                    extra = ""
                    if like_count:
                        extra += f" ❤{like_count}"
                    if sub_count:
                        extra += f" 💬{sub_count}"
                    console.print(f"  [{theme['accent']}]{i}.[/{theme['accent']}] [bold]{nickname}[/bold]: {content}[dim]{extra}[/dim]")

            # 用户信息
            elif "user" in payload and isinstance(payload.get("user"), dict):
                user = payload["user"]
                console.print(Panel(
                    f"[bold]{user.get('nickname', '?')}[/bold]",
                    border_style=theme["success"],
                ))
                for k, v in user.items():
                    if v and k not in ("guest",):
                        console.print(f"  {k}: [{theme['accent']}]{v}[/{theme['accent']}]")

            # 笔记详情
            elif "note_detail_map" in payload or "title" in str(payload):
                # 尝试提取笔记内容
                detail = payload
                if "note_detail_map" in detail:
                    for v in detail["note_detail_map"].values():
                        if isinstance(v, dict) and "note" in v:
                            detail = v["note"]
                            break
                title = detail.get("title", "") or detail.get("display_title", "")
                desc = detail.get("desc", "")
                user = detail.get("user", {})
                nickname = user.get("nickname", "?") if isinstance(user, dict) else "?"
                interact = detail.get("interact_info", {})
                console.print(Panel(
                    f"[bold]{title}[/bold]\n[dim]by {nickname}[/dim]",
                    border_style=theme["success"],
                ))
                if desc:
                    console.print(f"\n  {desc}\n")
                if isinstance(interact, dict):
                    parts = []
                    for k, v in interact.items():
                        if v and "count" in k:
                            parts.append(f"{k.replace('_count','')}: {v}")
                    if parts:
                        console.print(f"  [{' | '.join(parts)}]")

            else:
                console.print_json(json.dumps(data, indent=2, ensure_ascii=False))

        elif isinstance(payload, list):
            for i, item in enumerate(payload[:20], 1):
                console.print(f"  [{theme['accent']}]{i}.[/{theme['accent']}] {item}")
        else:
            console.print_json(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        # 错误输出
        error_msg = data.get("error", "") or data.get("message", "未知错误")
        console.print(Panel(
            f"[bold red]{error_msg}[/bold red]",
            title="错误",
            border_style="red",
        ))


# ─── 主循环 ──────────────────────────────────────────────────────────

def main():
    cfg = load_config()
    theme_name = cfg.get("theme", "default")
    theme = THEMES.get(theme_name, THEMES["default"])

    # 设置自动补全
    completer = XhsCompleter()
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")

    # 清屏 + 显示欢迎界面
    os.system("clear")

    bg = cfg.get("background_image", "")
    if bg and Path(bg).exists():
        draw_background_image(bg)

    show_banner(cfg)

    # 检查登录状态
    import subprocess
    venv_python = str(VENV_DIR / "bin" / "python")
    try:
        result = subprocess.run(
            [venv_python, "-m", "xhs_cli", "status", "--json"],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_DIR),
        )
        if result.returncode == 0:
            console.print("[green]✓ 已登录[/green]\n")
        else:
            console.print("[yellow]⚠ 未登录，请先输入 login 登录[/yellow]\n")
    except Exception:
        pass

    # 主循环
    while True:
        try:
            theme_name = cfg.get("theme", "default")
            theme = THEMES.get(theme_name, THEMES["default"])

            user_input = Prompt.ask(
                f"[{theme['prompt']}]xhs >[/{theme['prompt']}]",
                console=console,
            )

            user_input = user_input.strip()
            if not user_input:
                continue

            # 保存到 readline 历史
            readline.add_history(user_input)

            run_xhs_command(user_input, cfg)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]输入 exit 退出[/dim]")
            continue
        except EOFError:
            console.print("\n[bold]👋 再见！[/bold]")
            break


if __name__ == "__main__":
    main()
