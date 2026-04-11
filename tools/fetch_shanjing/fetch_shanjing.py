#!/usr/bin/env python3
"""
Fetch and parse Shan Hai Jing (山海经) from ctext.org
Outputs bilingual markdown files organized by chapter.
"""

import os
import re
import time
import sys
from html.parser import HTMLParser

# Try to use uv if available, otherwise use system python
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing dependencies with uv...")
    os.system("uv pip install requests beautifulsoup4 lxml")
    import requests
    from bs4 import BeautifulSoup

BASE_URL = "https://ctext.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

CHAPTERS = [
    ("nan-shan-jing", "南山经", "Nan Shan Jing - Classic of the Southern Mountains"),
    ("xi-shan-jing", "西山经", "Xi Shan Jing - Classic of the Western Mountains"),
    ("bei-shan-jing", "北山经", "Bei Shan Jing - Classic of the Northern Mountains"),
    ("dong-shan-jing", "东山经", "Dong Shan Jing - Classic of the Eastern Mountains"),
    ("zhong-shan-jing", "中山经", "Zhong Shan Jing - Classic of the Central Mountains"),
    ("hai-wai-nan-jing", "海外南经", "Hai Wai Nan Jing - Classic of Regions Beyond the Seas: South"),
    ("hai-wai-xi-jing", "海外西经", "Hai Wai Xi Jing - Classic of Regions Beyond the Seas: West"),
    ("hai-wai-dong-jing", "海外东经", "Hai Wai Dong Jing - Classic of Regions Beyond the Seas: East"),
    ("hai-wai-bei-jing", "海外北经", "Hai Wai Bei Jing - Classic of Regions Beyond the Seas: North"),
    ("hai-nei-nan-jing", "海内南经", "Hai Nei Nan Jing - Classic of Regions Within the Seas: South"),
    ("hai-nei-xi-jing", "海内西经", "Hai Nei Xi Jing - Classic of Regions Within the Seas: West"),
    ("hai-nei-dong-jing", "海内东经", "Hai Nei Dong Jing - Classic of Regions Within the Seas: East"),
    ("hai-nei-bei-jing", "海内北经", "Hai Nei Bei Jing - Classic of Regions Within the Seas: North"),
    ("da-huang-dong-jing", "大荒东经", "Da Huang Dong Jing - Classic of the Great Wilderness: East"),
    ("da-huang-nan-jing", "大荒南经", "Da Huang Nan Jing - Classic of the Great Wilderness: South"),
    ("da-huang-xi-jing", "大荒西经", "Da Huang Xi Jing - Classic of the Great Wilderness: West"),
    ("da-huang-bei-jing", "大荒北经", "Da Huang Bei Jing - Classic of the Great Wilderness: North"),
    ("hai-nei-jing", "海内经", "Hai Nei Jing - Classic of Regions Within the Seas"),
]


def extract_text_from_page(html: str, lang: str) -> str:
    """Extract main text content from ctext.org page."""
    soup = BeautifulSoup(html, "lxml")

    # Remove scripts, styles, nav elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Find the main content area
    # ctext.org uses class "etext" for main text content
    content = soup.find("td", class_="etext")
    if not content:
        content = soup.find("div", class_="etext")
    if not content:
        content = soup.find("div", id="content")
    if not content:
        # Fallback: try to find the main body
        content = soup.find("body")

    if not content:
        print("  WARNING: Could not find content area")
        return ""

    # Remove navigation and decorative elements within content
    for tag in content.find_all(["a", "span", "div"], class_=["stopPunct", "infobox"]):
        tag.decompose()

    # Extract text, preserving paragraph structure
    paragraphs = []
    for child in content.children:
        if isinstance(child, str):
            text = child.strip()
            if text:
                paragraphs.append(text)
        elif child.name in ("p", "div", "blockquote"):
            # Check if this is a paragraph with a section number
            text = child.get_text(separator=" ", strip=True)
            if text:
                paragraphs.append(text)
        elif child.name == "br":
            pass  # Skip standalone br tags
        elif child.name and child.name not in ("script", "style"):
            text = child.get_text(separator=" ", strip=True)
            if text:
                paragraphs.append(text)

    return "\n\n".join(p for p in paragraphs if len(p.strip()) > 2)


def clean_text(text: str) -> str:
    """Clean up extracted text."""
    # Remove multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove trailing whitespace on lines
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


def fetch_chapter(slug: str, lang: str, retries: int = 3) -> str:
    """Fetch a single chapter."""
    url = f"{BASE_URL}/shan-hai-jing/{slug}/{lang}"
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            text = extract_text_from_page(resp.text, lang)
            return clean_text(text)
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    return ""


def create_bilingual_markdown(chapter_data: list, output_dir: str):
    """Create combined bilingual markdown files."""
    os.makedirs(output_dir, exist_ok=True)

    # Create combined bilingual files
    combined_zh_path = os.path.join(output_dir, "山海经_中文版.md")
    combined_en_path = os.path.join(output_dir, "shan_hai_jing_english.md")

    with open(combined_zh_path, "w", encoding="utf-8") as zh_f, \
         open(combined_en_path, "w", encoding="utf-8") as en_f:

        # Chinese version header
        zh_f.write("""# 山海经

> 《山海经》是中国古代的一部地理和神话著作，记录了远古时期的山川地理、
> 奇禽异兽、神话传说和民俗信仰。全书共十八卷，分为五大部分：
> 五藏山经（南山经、西山经、北山经、东山经、中山经）、
> 海外经（海外南经、海外西经、海外东经、海外北经）、
> 海内经（海内南经、海内西经、海内东经、海内北经）、
> 大荒经（大荒东经、大荒南经、大荒西经、大荒北经）、
> 海内经（独立一卷）。

---

""")

        # English version header
        en_f.write("""# Shan Hai Jing (Classic of Mountains and Seas)

> The *Shan Hai Jing* (Classic of Mountains and Seas) is an ancient Chinese text
> recording geography, mythology, strange creatures, and folklore from antiquity.
> It contains 18 chapters organized into five major sections:
> the Five Classics of Mountains (Nan Shan, Xi Shan, Bei Shan, Dong Shan, Zhong Shan),
> the Classic of Regions Beyond the Seas (South, West, East, North),
> the Classic of Regions Within the Seas (South, West, East, North),
> the Classic of the Great Wilderness (East, South, West, North),
> and an independent Classic of Regions Within the Seas.

---

""")

        for slug, name_cn, name_en, zh_text, en_text in chapter_data:
            # Write Chinese chapter
            zh_f.write(f"## {name_cn}\n\n")
            zh_f.write(zh_text)
            zh_f.write("\n\n---\n\n")

            # Write English chapter
            en_f.write(f"## {name_en}\n\n")
            en_f.write(en_text)
            en_f.write("\n\n---\n\n")

    # Also create individual chapter files
    for slug, name_cn, name_en, zh_text, en_text in chapter_data:
        safe_slug = slug.replace("-", "_")

        # Individual Chinese chapter
        with open(os.path.join(output_dir, f"{safe_slug}_zh.md"), "w", encoding="utf-8") as f:
            f.write(f"# {name_cn}\n\n")
            f.write(zh_text)
            f.write("\n")

        # Individual English chapter
        with open(os.path.join(output_dir, f"{safe_slug}_en.md"), "w", encoding="utf-8") as f:
            f.write(f"# {name_en}\n\n")
            f.write(en_text)
            f.write("\n")

        # Bilingual side-by-side
        with open(os.path.join(output_dir, f"{safe_slug}_bilingual.md"), "w", encoding="utf-8") as f:
            f.write(f"# {name_cn} / {name_en}\n\n")
            f.write("## 中文\n\n")
            f.write(zh_text)
            f.write("\n\n---\n\n")
            f.write("## English\n\n")
            f.write(en_text)
            f.write("\n")

    print(f"\nFiles created in: {output_dir}")
    for f in sorted(os.listdir(output_dir)):
        size = os.path.getsize(os.path.join(output_dir, f))
        print(f"  {f}: {size:,} bytes")


def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "03_01_REFERENCE", "shan_hai_jing")

    print(f"Output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    chapter_data = []

    for i, (slug, name_cn, name_en) in enumerate(CHAPTERS):
        print(f"\n[{i+1}/{len(CHAPTERS)}] {name_cn} / {name_en}")

        print("  Fetching Chinese...")
        zh_text = fetch_chapter(slug, "zhs")
        if zh_text:
            print(f"  Got {len(zh_text)} chars (Chinese)")
        else:
            print("  WARNING: No Chinese content fetched")

        time.sleep(2)

        print("  Fetching English...")
        en_text = fetch_chapter(slug, "ens")
        if en_text:
            print(f"  Got {len(en_text)} chars (English)")
        else:
            print("  WARNING: No English content fetched")

        time.sleep(2)

        chapter_data.append((slug, name_cn, name_en, zh_text, en_text))

    # Create markdown files
    create_bilingual_markdown(chapter_data, output_dir)

    # Summary
    total_zh = sum(len(zh) for _, _, _, zh, _ in chapter_data)
    total_en = sum(len(en) for _, _, _, _, en in chapter_data)
    print(f"\n{'='*50}")
    print(f"Total Chinese characters: {total_zh:,}")
    print(f"Total English characters: {total_en:,}")
    print(f"Chapters fetched: {len(chapter_data)}/{len(CHAPTERS)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
