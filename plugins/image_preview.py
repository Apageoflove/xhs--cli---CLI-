"""图片预览插件 - 在终端中显示图片（Sixel/Unicode 块字符）"""

import os
import sys
import shutil
import urllib.request
import tempfile
from pathlib import Path

from PIL import Image
from rich.console import Console

console = Console()

# 项目目录
PROJECT_DIR = Path(__file__).parent.parent
FONT_DIR = PROJECT_DIR / "assets" / "fonts"


def download_image(url, timeout=10):
    """下载图片到临时文件"""
    if not url:
        return None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(tmp.name, "wb") as f:
                f.write(resp.read())
        return tmp.name
    except Exception:
        return None


def render_terminal_image(image_path, max_width=60, max_height=20):
    """用 Unicode 半块字符在终端渲染图片（兼容性最好）"""
    if not image_path or not Path(image_path).exists():
        return

    try:
        img = Image.open(image_path)
        img = img.convert("RGB")

        w = min(max_width, shutil.get_terminal_size().columns)
        h = min(max_height, shutil.get_terminal_size().lines // 3)

        img = img.resize((w, h // 2))

        for y in range(0, img.height):
            line = ""
            for x in range(img.width):
                r, g, b = img.getpixel((x, y))
                line += f"\033[48;2;{r};{g};{b}m \033[0m"
            print(line)
    except Exception:
        pass


def render_cover_grid(image_urls, cols=5, max_width=30):
    """在终端以网格形式显示多张封面图"""
    if not image_urls:
        return

    valid_images = []
    for url in image_urls[:20]:
        path = download_image(url)
        if path:
            valid_images.append(path)

    if not valid_images:
        console.print("[dim]无法加载封面图[/dim]")
        return

    try:
        thumb_h = 6
        thumb_w = max_width // cols

        row_images = []
        for path in valid_images:
            img = Image.open(path).convert("RGB")
            img = img.resize((thumb_w, thumb_h))
            row_images.append(img)

        for row_start in range(0, len(row_images), cols):
            batch = row_images[row_start:row_start + cols]
            for y in range(thumb_h):
                line = ""
                for img in batch:
                    for x in range(img.width):
                        r, g, b = img.getpixel((x, y))
                        line += f"\033[48;2;{r};{g};{b}m \033[0m"
                    line += "  "
                print(line)
            print()
    finally:
        for path in valid_images:
            try:
                os.unlink(path)
            except OSError:
                pass


def generate_word_cloud_image(words_freq, output_path, width=800, height=400):
    """生成词云图片"""
    from wordcloud import WordCloud

    font_path = str(FONT_DIR / "DroidSansFallback.ttf")
    if not Path(font_path).exists():
        font_path = None

    wc = WordCloud(
        width=width,
        height=height,
        font_path=font_path,
        background_color="white",
        max_words=100,
        max_font_size=80,
        colormap="viridis",
    )
    wc.generate_from_frequencies(words_freq)
    wc.to_file(output_path)
    return output_path
