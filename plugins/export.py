"""导出插件 - PDF / HTML / Markdown 导出"""

import json
import os
from pathlib import Path
from datetime import datetime

from rich.console import Console

console = Console()

PROJECT_DIR = Path(__file__).parent.parent
FONT_DIR = PROJECT_DIR / "assets" / "fonts"
EXPORT_DIR = PROJECT_DIR / "exports"


def _ensure_export_dir():
    EXPORT_DIR.mkdir(exist_ok=True)
    return EXPORT_DIR


def export_note_html(note_data, filename=None):
    """导出笔记为 HTML"""
    _ensure_export_dir()

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_{ts}.html"

    filepath = EXPORT_DIR / filename

    title = note_data.get("title", "无标题")
    desc = note_data.get("desc", "")
    nickname = "?"
    user = note_data.get("user", {})
    if isinstance(user, dict):
        nickname = user.get("nickname", "?")

    interact = note_data.get("interact_info", {})
    interact_html = ""
    if isinstance(interact, dict):
        parts = []
        for k, v in interact.items():
            if v and "count" in k:
                parts.append(f"<span>{k}: {v}</span>")
        interact_html = " | ".join(parts)

    # 提取图片
    images_html = ""
    image_list = note_data.get("image_list", [])
    if isinstance(image_list, list):
        for img in image_list:
            if isinstance(img, dict):
                url_default = img.get("url_default", img.get("url", ""))
                if url_default:
                    images_html += f'<img src="{url_default}" style="max-width:600px;margin:8px 0;border-radius:8px;">\n'

    comments_html = ""
    comments = note_data.get("comments", [])
    if isinstance(comments, list):
        for c in comments[:50]:
            if not isinstance(c, dict):
                continue
            c_user = c.get("user_info", {})
            c_nick = c_user.get("nickname", "?") if isinstance(c_user, dict) else "?"
            c_content = c.get("content", "")
            c_likes = c.get("like_count", 0)
            comments_html += f"""
            <div class="comment">
                <strong>{c_nick}</strong>
                <p>{c_content}</p>
                <small>❤ {c_likes}</small>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 小红书笔记</title>
    <style>
        body {{ font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
               max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px;
                 box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #ff2442; margin-bottom: 8px; }}
        .meta {{ color: #999; font-size: 14px; margin-bottom: 16px; }}
        .images {{ text-align: center; }}
        .images img {{ max-width: 100%; }}
        .comment {{ border-bottom: 1px solid #eee; padding: 12px 0; }}
        .comment p {{ margin: 4px 0; }}
        .comment small {{ color: #999; }}
        .interact {{ color: #666; font-size: 13px; margin: 12px 0; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{title}</h1>
        <div class="meta">by {nickname} · {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
        <div class="interact">{interact_html}</div>
        <div class="images">{images_html}</div>
        <div style="white-space:pre-wrap;line-height:1.8;margin-top:16px;">{desc}</div>
    </div>
    {"<div class='card'><h2>评论</h2>" + comments_html + "</div>" if comments_html else ""}
</body>
</html>"""

    filepath.write_text(html, encoding="utf-8")
    console.print(f"[green]✓ HTML 已导出: {filepath}[/green]")
    return str(filepath)


def export_note_pdf(note_data, filename=None):
    """导出笔记为 PDF"""
    _ensure_export_dir()

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_{ts}.pdf"

    filepath = EXPORT_DIR / filename

    from fpdf import FPDF

    font_path = str(FONT_DIR / "DroidSansFallback.ttf")
    has_font = Path(font_path).exists()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    if has_font:
        pdf.add_font("zh", "", font_path, uni=True)
        pdf.set_font("zh", size=16)
    else:
        pdf.set_font("Helvetica", size=16)

    title = note_data.get("title", "无标题")
    pdf.cell(0, 12, title, ln=True, align="C")
    pdf.ln(5)

    if has_font:
        pdf.set_font("zh", size=10)
    else:
        pdf.set_font("Helvetica", size=10)

    nickname = "?"
    user = note_data.get("user", {})
    if isinstance(user, dict):
        nickname = user.get("nickname", "?")
    pdf.cell(0, 8, f"作者: {nickname}    导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    desc = note_data.get("desc", "")
    if desc:
        if has_font:
            pdf.set_font("zh", size=12)
        else:
            pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 8, desc)
        pdf.ln(5)

    comments = note_data.get("comments", [])
    if isinstance(comments, list) and comments:
        if has_font:
            pdf.set_font("zh", size=14)
        else:
            pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, f"评论 ({len(comments)} 条)", ln=True)
        pdf.ln(3)

        if has_font:
            pdf.set_font("zh", size=10)
        else:
            pdf.set_font("Helvetica", size=10)

        for c in comments[:50]:
            if not isinstance(c, dict):
                continue
            c_user = c.get("user_info", {})
            c_nick = c_user.get("nickname", "?") if isinstance(c_user, dict) else "?"
            c_content = c.get("content", "")
            pdf.cell(0, 7, f"  {c_nick}: {c_content}", ln=True)

    pdf.output(str(filepath))
    console.print(f"[green]✓ PDF 已导出: {filepath}[/green]")
    return str(filepath)


def export_search_results_html(items, keyword, filename=None):
    """导出搜索结果为 HTML"""
    _ensure_export_dir()

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_{keyword}_{ts}.html"

    filepath = EXPORT_DIR / filename

    rows_html = ""
    for i, item in enumerate(items, 1):
        card = item.get("note_card", item) if isinstance(item, dict) else {}
        title = card.get("display_title", "") or card.get("title", "") or "(无标题)"
        user = card.get("user", {}) if isinstance(card, dict) else {}
        nickname = user.get("nickname", "") if isinstance(user, dict) else ""
        interact = card.get("interact_info", {}) if isinstance(card, dict) else {}
        liked = interact.get("liked_count", "-") if isinstance(interact, dict) else "-"
        desc = card.get("desc", "") if isinstance(card, dict) else ""
        cover = ""
        if isinstance(card, dict):
            cover_url = card.get("cover", {})
            if isinstance(cover_url, dict):
                cover = cover_url.get("url_default", cover_url.get("url", ""))

        cover_html = f'<img src="{cover}" width="120" style="border-radius:6px;">' if cover else ""

        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td>{cover_html}</td>
            <td><strong>{title}</strong><br><small style="color:#999">{desc[:60]}</small></td>
            <td>{nickname}</td>
            <td>{liked}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>搜索 "{keyword}" 的结果</title>
    <style>
        body {{ font-family: -apple-system, "PingFang SC", sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #ff2442; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; vertical-align: top; }}
        th {{ background: #f8f8f8; color: #666; }}
    </style>
</head>
<body>
    <h1>搜索 "{keyword}" 的结果</h1>
    <p>共 {len(items)} 条 · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    <table>
        <tr><th>#</th><th>封面</th><th>标题</th><th>作者</th><th>点赞</th></tr>
        {rows_html}
    </table>
</body>
</html>"""

    filepath.write_text(html, encoding="utf-8")
    console.print(f"[green]✓ 搜索结果 HTML 已导出: {filepath}[/green]")
    return str(filepath)
