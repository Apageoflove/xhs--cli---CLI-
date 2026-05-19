"""数据可视化插件 - 终端图表和分析"""

import plotext as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def plot_engagement_chart(notes):
    """绘制笔记互动数据柱状图"""
    if not notes:
        console.print("[yellow]没有数据可绘制[/yellow]")
        return

    titles = []
    likes = []
    comments_list = []
    collects = []

    for i, note in enumerate(notes[:15]):
        card = note.get("note_card", note)
        title = card.get("display_title", "") or card.get("title", "") or f"笔记{i+1}"
        titles.append(title[:12])

        interact = card.get("interact_info", {})
        if isinstance(interact, dict):
            liked = interact.get("liked_count", "0")
            try:
                likes.append(int(str(liked).replace("万","0000").replace("+","")))
            except (ValueError, TypeError):
                likes.append(0)

            collected = interact.get("collected_count", "0")
            try:
                collects.append(int(str(collected).replace("万","0000").replace("+","")))
            except (ValueError, TypeError):
                collects.append(0)
        else:
            likes.append(0)
            collects.append(0)

        comment_count = card.get("comment_count", 0)
        try:
            comments_list.append(int(comment_count))
        except (ValueError, TypeError):
            comments_list.append(0)

    plt.clear_figure()
    plt.title("📊 笔记互动分析")
    plt.xlabel("笔记")
    plt.ylabel("数量")

    x = list(range(1, len(titles) + 1))

    plt.bar(x, likes, label="点赞", color="red")
    plt.bar(x, collects, label="收藏", color="yellow")
    plt.bar(x, comments_list, label="评论", color="cyan")

    plt.xticks(x, titles)
    plt.show()
    print()


def plot_engagement_pie(notes):
    """绘制互动分布饼图"""
    if not notes:
        console.print("[yellow]没有数据[/yellow]")
        return

    total_likes = 0
    total_collects = 0
    total_comments = 0

    for note in notes[:15]:
        card = note.get("note_card", note)
        interact = card.get("interact_info", {})
        if isinstance(interact, dict):
            try:
                total_likes += int(str(interact.get("liked_count", "0")).replace("万","0000").replace("+",""))
            except (ValueError, TypeError):
                pass
            try:
                total_collects += int(str(interact.get("collected_count", "0")).replace("万","0000").replace("+",""))
            except (ValueError, TypeError):
                pass
        try:
            total_comments += int(card.get("comment_count", 0))
        except (ValueError, TypeError):
            pass

    if total_likes + total_collects + total_comments == 0:
        console.print("[yellow]无互动数据[/yellow]")
        return

    plt.clear_figure()
    plt.title("📊 互动分布")
    plt.pie(
        [total_likes, total_collects, total_comments],
        labels=["点赞", "收藏", "评论"],
        colors=["red", "yellow", "cyan"],
    )
    plt.show()
    print()


def show_stats_table(notes):
    """显示统计信息表格"""
    if not notes:
        console.print("[yellow]没有数据[/yellow]")
        return

    total = len(notes)
    video_count = 0
    image_count = 0
    total_likes = 0
    total_collects = 0
    total_comments = 0

    for note in notes:
        card = note.get("note_card", note)
        ntype = card.get("type", "")
        if "video" in str(ntype).lower():
            video_count += 1
        else:
            image_count += 1

        interact = card.get("interact_info", {})
        if isinstance(interact, dict):
            try:
                total_likes += int(str(interact.get("liked_count", "0")).replace("万","0000").replace("+",""))
            except (ValueError, TypeError):
                pass
            try:
                total_collects += int(str(interact.get("collected_count", "0")).replace("万","0000").replace("+",""))
            except (ValueError, TypeError):
                pass
        try:
            total_comments += int(card.get("comment_count", 0))
        except (ValueError, TypeError):
            pass

    table = Table(title="📊 数据统计", box=box.ROUNDED)
    table.add_column("指标", style="bold yellow")
    table.add_column("数值", style="cyan", justify="right")

    table.add_row("总笔记数", str(total))
    table.add_row("图文笔记", str(image_count))
    table.add_row("视频笔记", str(video_count))
    table.add_row("总点赞", f"{total_likes:,}")
    table.add_row("总收藏", f"{total_collects:,}")
    table.add_row("总评论", f"{total_comments:,}")
    if total > 0:
        table.add_row("平均点赞", f"{total_likes // total:,}")
        table.add_row("平均收藏", f"{total_collects // total:,}")
        table.add_row("平均评论", f"{total_comments // total:,}")

    console.print(table)
    print()
