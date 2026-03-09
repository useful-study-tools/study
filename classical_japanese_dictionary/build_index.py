import os
import re
from collections import defaultdict
from pathlib import Path

# ==========================================
# 0. 設定（config.pyの内容を古文用に想定）
# ==========================================
try:
    from config import CHAPTER_MAP
except ImportError:
    CHAPTER_MAP = {1: "最重要語", 164: "重要語"}

# ==========================================
# 1. 補助関数（古文用に最適化）
# ==========================================
def natural_sort_key(filename):
    parts = re.split(r'(\d+)', filename)
    return [int(p) if p.isdigit() else p.lower() for p in parts if p]

def get_base_number(filename):
    match = re.match(r'^(\d+)', filename)
    return int(match.group(1)) if match else 0

def get_word_details(filepath):
    """HTMLから単語名、活用、意味を抽出する"""
    details = {"meaning": "", "conjugation": ""}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 意味(JP)の抽出
        m_match = re.search(r'<div class="meaning-jp">\s*(.*?)\s*</div>', content, re.DOTALL)
        if m_match:
            details["meaning"] = re.sub(r'<[^>]+>', '', m_match.group(1)).strip()
        
        # 活用(conjugation)の抽出（HTML側に <div class="conjugation">マ行上一段</div> 等がある想定）
        c_match = re.search(r'<div class="conjugation">\s*(.*?)\s*</div>', content, re.DOTALL)
        if c_match:
            details["conjugation"] = c_match.group(1).strip()
            
    except:
        pass
    return details

# ==========================================
# 2. メイン処理
# ==========================================
def generate_index():
    # パス設定を classical_japanese_dictionary/ 基準に変更
    base_dir = Path("classical_japanese_dictionary")
    word_dir = base_dir / "data"
    output_file = base_dir / "index.html"

    if not word_dir.exists():
        print(f"エラー: ディレクトリ {word_dir} が見つかりません。")
        return

    files = [f for f in os.listdir(word_dir) if f.endswith(".html")]
    files.sort(key=natural_sort_key)

    grouped_chapters = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group_match = re.search(r'【(.*?)】', title)
        group_name = group_match.group(1) if group_match else "その他"
        display_label = title.split('】')[-1] if '】' in title else title
        grouped_chapters[group_name].append((s_num, display_label))

    # HTMLヘッダー（和風のデザインに調整）
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>古文単語 データベース</title>
    <link rel="icon" href="/image/logo.png">
    <style>
        :root {{ 
            --primary-color: #a33c3a; /* 茜色 - 古文らしい赤 */
            --chapter-color: #555243; /* 焦茶 */
            --bg-color: #f8f4e6;      /* 生成り色 */
            --accent-color: #6a994e;  /* 抹茶色 */
        }}
        body {{ font-family: "Sawarabi Mincho", "Hiragino Mincho ProN", serif; background-color: var(--bg-color); margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; color: #333; }}
        .container {{ width: 100%; max-width: 800px; }}
        h1 {{ margin-top: 10px; color: var(--primary-color); text-align: center; border-bottom: 2px solid var(--primary-color); padding-bottom: 10px; font-weight: bold; }}
        
        .btn-home {{ display: inline-block; padding: 8px 20px; background-color: var(--primary-color); color: white; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.3s; }}
        .btn-home:hover {{ background-color: #c78a88; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        
        .exercise-link {{ display: block; width: fit-content; margin: 0 auto 30px; padding: 12px 40px; background-color: var(--primary-color); color: white; text-decoration: none; border-radius: 20px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.3s; }}

        .toc {{ background: white; padding: 20px; border-radius: 5px; margin-bottom: 25px; border: 1px solid #ddd; }}
        .toc-group-title {{ font-weight: bold; color: var(--primary-color); border-left: 4px solid var(--primary-color); padding-left: 10px; margin-bottom: 10px; }}
        .toc-links {{ display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; margin-bottom: 15px; }}
        .toc-links a {{ text-decoration: none; color: #444; background: #eee; padding: 5px 12px; border-radius: 3px; font-size: 0.85rem; }}

        .search-box {{ width: 100%; padding: 15px; font-size: 18px; border: 2px solid #ccc; border-radius: 5px; margin-bottom: 20px; box-sizing: border-box; }}
        
        .word-list {{ list-style: none; padding: 0; }}
        .chapter-header {{ background: var(--chapter-color); color: white; padding: 10px 15px; margin: 30px 0 10px 0; border-radius: 3px; }}
        .word-item {{ background: white; margin-bottom: 5px; border-bottom: 1px solid #eee; }}
        .word-item a {{ display: flex; padding: 12px; text-decoration: none; color: #333; align-items: center; }}
        
        .word-id {{ font-weight: bold; color: var(--primary-color); min-width: 60px; }}
        .word-name {{ font-size: 1.2em; font-weight: bold; }}
        .word-conj {{ font-size: 0.7em; background: #f0f0f0; color: #666; padding: 2px 6px; margin-left: 10px; border-radius: 3px; }}
        .word-meaning {{ font-size: 0.85em; color: #666; margin-left: auto; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 300px; }}
        
        .word-item.hidden {{ display: none; }}
        #backToTop {{ position: fixed; bottom: 30px; right: 30px; width: 50px; height: 50px; background: var(--primary-color); color: white; border: none; border-radius: 50%; cursor: pointer; display: none; align-items: center; justify-content: center; }}
    </style>
</head>
<body>
<div class="container">
    <a href="../index.html" class="btn-home">ホームに戻る</a>
    <h1>古文単語 辞書目次</h1>
    <a href="exercise.html" class="exercise-link">単語演習</a>
    <nav class="toc">
"""

    # 目次生成
    for group_name, chapters in grouped_chapters.items():
        html_content += f'        <div class="toc-group"><div class="toc-group-title">{group_name}</div><ul class="toc-links">\n'
        for s_num, label in chapters:
            html_content += f'            <li><a href="#chapter-{s_num}">{label}</a></li>\n'
        html_content += f'        </ul></div>\n'

    html_content += """    </nav>
    <input type="text" id="searchInput" class="search-box" placeholder="単語・現代語訳で検索..." onkeyup="filterList()">
    <ul class="word-list" id="wordList">
"""

    current_chapter_start = -1
    sorted_thresholds = sorted(CHAPTER_MAP.keys(), reverse=True)

    for filename in files:
        base_num = get_base_number(filename)
        for t in sorted_thresholds:
            if base_num >= t:
                if t != current_chapter_start:
                    html_content += f'        <li class="chapter-header" id="chapter-{t}">{CHAPTER_MAP[t]}</li>\n'
                    current_chapter_start = t
                break

        word_id_full = filename.replace(".html", "")
        # 数字を除去して単語名にする（例: 001-miru -> miru）
        display_name = re.sub(r'^[0-9-]+', '', word_id_full).strip()
        
        # 活用と意味を取得
        details = get_word_details(word_dir / filename)

        html_content += f'        <li class="word-item"><a href="data/{filename}">'
        html_content += f'<span class="word-id">{base_num:03}</span>'
        html_content += f'<span class="word-name">{display_name}</span>'
        if details["conjugation"]:
            html_content += f'<span class="word-conj">{details["conjugation"]}</span>'
        if details["meaning"]:
            html_content += f'<span class="word-meaning">{details["meaning"]}</span>'
        html_content += f'</a></li>\n'

    # JS部分は英単語版のロジックをそのまま継承（省略なしで結合）
    html_content += """    </ul>
    <div id="loadingIndicator" style="text-align:center; padding:20px;">スクロールして読み込み...</div>
</div>
<button id="backToTop">↑</button>
<script>
    const wordList = document.getElementById('wordList');
    const allItems = Array.from(wordList.children).filter(item => item.classList.contains('word-item'));
    const backToTopBtn = document.getElementById('backToTop');
    const margin = 1200;

    function checkVisibleItems() {
        const triggerLimit = window.innerHeight + window.scrollY + margin;
        let hasHidden = false;
        for (let item of allItems) {
            if (item.classList.contains('hidden')) {
                if (item.offsetTop < triggerLimit) {
                    item.classList.remove('hidden');
                } else {
                    hasHidden = true;
                    break;
                }
            }
        }
        document.getElementById('loadingIndicator').style.display = hasHidden ? 'block' : 'none';
        backToTopBtn.style.display = window.scrollY > 300 ? 'flex' : 'none';
    }

    function initializeLazyLoad() {
        allItems.forEach(item => item.classList.add('hidden'));
        checkVisibleItems();
    }

    function loadChapterAndScroll(event, chapterId) {
        event.preventDefault();
        const chapterHeader = document.getElementById(chapterId);
        if (!chapterHeader) return;
        let nextEl = chapterHeader.nextElementSibling;
        for (let i = 0; i < 40 && nextEl; i++) {
            if (nextEl.classList.contains('word-item')) nextEl.classList.remove('hidden');
            nextEl = nextEl.nextElementSibling;
        }
        chapterHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setTimeout(checkVisibleItems, 100);
    }

    window.addEventListener('scroll', () => window.requestAnimationFrame(checkVisibleItems));
    backToTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.toc-links a').forEach(link => {
            link.addEventListener('click', (e) => loadChapterAndScroll(e, link.getAttribute('href').substring(1)));
        });
        initializeLazyLoad();
    });

    function filterList() {
        const filter = document.getElementById('searchInput').value.toLowerCase();
        for (let item of wordList.getElementsByTagName('li')) {
            if (item.classList.contains('chapter-header')) {
                item.style.display = filter === "" ? "" : "none";
                continue;
            }
            if (filter === "") {
                item.classList.add('hidden');
                item.style.display = "";
            } else {
                const text = item.textContent || item.innerText;
                item.classList.remove('hidden');
                item.style.display = text.toLowerCase().includes(filter) ? "" : "none";
            }
        }
        if (filter === "") checkVisibleItems();
    }
</script>
</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"古文辞書の更新完了: {output_file}")

if __name__ == "__main__":
    generate_index()
