"""关键词分析和趋势插件 - 中文分词、词云、趋势分析"""

import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import jieba
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

PROJECT_DIR = Path(__file__).parent.parent
EXPORT_DIR = PROJECT_DIR / "exports"

# 中文停用词
STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么", "如何", "可以",
    "这个", "那个", "所以", "因为", "但是", "而且", "或者", "如果", "虽然", "已经",
    "被", "把", "从", "向", "对", "为", "与", "以", "及", "等", "之", "其", "中",
    "能", "让", "给", "还", "比", "更", "最", "再", "又", "吗", "吧", "呢", "啊",
    "嗯", "哦", "哈", "呀", "啦", "嘛", "么", "不是", "没", "过", "做", "来",
    "下", "出", "得", "地", "着", "过", "用", "个", "只", "才", "已", "于",
    "笔记", "全文", "查看", "图片", "视频", "来自", "小红书",
}


def extract_keywords(texts, top_n=30):
    """从文本列表中提取关键词"""
    words = []
    for text in texts:
        if not text or not isinstance(text, str):
            continue
        segs = jieba.cut(text)
        for w in segs:
            w = w.strip()
            if len(w) >= 2 and w not in STOP_WORDS and not w.isdigit():
                if not re.match(r'^[\W_]+$', w):
                    words.append(w)
    return Counter(words).most_common(top_n)


def analyze_search_results(items):
    """分析搜索结果，提取关键词和统计"""
    titles = []
    descs = []
    all_text = []

    for item in items:
        card = item.get("note_card", item) if isinstance(item, dict) else {}
        title = card.get("display_title", "") or card.get("title", "") or ""
        desc = card.get("desc", "") or ""
        titles.append(title)
        descs.append(desc)
        all_text.append(f"{title} {desc}")

    # 标题关键词
    title_keywords = extract_keywords(titles, 20)

    # 全文关键词
    all_keywords = extract_keywords(all_text, 30)

    # 用户分布
    users = Counter()
    for item in items:
        card = item.get("note_card", item) if isinstance(item, dict) else {}
        user = card.get("user", {}) if isinstance(card, dict) else {}
        if isinstance(user, dict):
            nick = user.get("nickname", "")
            if nick:
                users[nick] += 1

    # 类型分布
    type_count = Counter()
    for item in items:
        card = item.get("note_card", item) if isinstance(item, dict) else {}
        ntype = card.get("type", "unknown")
        type_count[str(ntype)] += 1

    return {
        "title_keywords": title_keywords,
        "all_keywords": all_keywords,
        "user_distribution": users.most_common(10),
        "type_distribution": dict(type_count),
        "total": len(items),
    }


def show_keyword_analysis(analysis):
    """显示关键词分析结果"""
    # 标题关键词表格
    kw = analysis["title_keywords"]
    if kw:
        table = Table(title="🔑 标题关键词 Top 20", box=box.ROUNDED, show_lines=False)
        table.add_column("排名", style="bold", width=6)
        table.add_column("关键词", style="cyan")
        table.add_column("出现次数", style="yellow", justify="right")
        table.add_column("热度条", style="red")

        max_count = kw[0][1] if kw else 1
        for i, (word, count) in enumerate(kw, 1):
            bar_len = int(count / max_count * 20)
            bar = "█" * bar_len
            table.add_row(str(i), word, str(count), bar)

        console.print(table)
        print()

    # 用户分布
    users = analysis["user_distribution"]
    if users:
        table = Table(title="👤 作者分布", box=box.ROUNDED)
        table.add_column("作者", style="cyan")
        table.add_column("笔记数", style="yellow", justify="right")
        for nick, count in users[:10]:
            table.add_row(nick, str(count))
        console.print(table)
        print()


def generate_wordcloud(analysis, keyword="xhs"):
    """生成并显示词云"""
    all_keywords = analysis.get("all_keywords", {})
    if not all_keywords:
        console.print("[yellow]没有关键词数据[/yellow]")
        return None

    freq_dict = dict(all_keywords)
    from plugins.image_preview import generate_word_cloud_image

    EXPORT_DIR.mkdir(exist_ok=True)
    output = EXPORT_DIR / f"wordcloud_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    generate_word_cloud_image(freq_dict, str(output))

    console.print(f"[green]✓ 词云已生成: {output}[/green]")
    return str(output)


def show_trend_analysis(items):
    """显示趋势分析"""
    console.print(Panel("[bold]📈 趋势分析[/bold]", border_style="cyan"))

    if not items:
        console.print("[yellow]没有数据[/yellow]")
        return

    # 互动分布分析
    engagement_levels = {"低互动": 0, "中互动": 0, "高互动": 0, "爆款": 0}
    for item in items:
        card = item.get("note_card", item) if isinstance(item, dict) else {}
        interact = card.get("interact_info", {})
        if not isinstance(interact, dict):
            continue
        try:
            likes = int(str(interact.get("liked_count", "0")).replace("万", "0000").replace("+", ""))
        except (ValueError, TypeError):
            likes = 0

        if likes >= 10000:
            engagement_levels["爆款"] += 1
        elif likes >= 1000:
            engagement_levels["高互动"] += 1
        elif likes >= 100:
            engagement_levels["中互动"] += 1
        else:
            engagement_levels["低互动"] += 1

    table = Table(box=box.ROUNDED)
    table.add_column("互动级别", style="bold")
    table.add_column("数量", justify="right")
    table.add_column("占比", justify="right")
    table.add_column("分布", style="cyan")

    total = len(items)
    for level, count in engagement_levels.items():
        pct = f"{count / total * 100:.1f}%" if total else "0%"
        bar = "█" * int(count / max(total, 1) * 30)
        color = {"爆款": "red", "高互动": "yellow", "中互动": "green", "低互动": "dim"}.get(level, "white")
        table.add_row(f"[{color}]{level}[/{color}]", str(count), pct, bar)

    console.print(table)
    print()
