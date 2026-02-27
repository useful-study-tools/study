import os
import re
from collections import defaultdict
from pathlib import Path

# ※ CHAPTER_MAPは同じディレクトリのconfig.pyにある想定です
try:
    from config import CHAPTER_MAP
except ImportError:
    # configがない場合のフォールバック（動作確認用）
    CHAPTER_MAP = {1: "【Basic】第1章", 500: "【Advanced】第2章"}

# ==========================================
# 1. 補助関数
# ==========================================
def natural_sort_key(filename):
    parts = re.split(r'(\d+)', filename)
    converted_parts = [int(p) if p.isdigit() else p.lower() for p in parts if p]
    if len(converted_parts) > 1:
        if converted_parts[1] == '.html':
            return [converted_parts[0], 0] + converted_parts[2:]
        else:
            return [converted_parts[0], 1] + converted_parts[2:]
    return converted_parts

def get_base_number(filename):
    match = re.match(r'^(\d+)', filename)
    return int(match.group(1)) if match else 0

def get_japanese_meaning(filepath):
    """HTMLファイルからmeaning-jpクラスの日本語訳を抽出する"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'<div class="meaning-jp">\s*(.*?)\s*</div>', content, re.DOTALL)
        if match:
            # HTMLタグを除去して返す
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            return text
    except:
        pass
    return ""

# ==========================================
# 2. メイン処理
# ==========================================
def generate_index():
    # パス設定を english_dictionary/ 基準に変更
    base_dir = Path("english_dictionary")
    word_dir = base_dir / "data"
    output_file = base_dir / "index.html"

    if not word_dir.exists():
        print(f"エラー: ディレクトリ {word_dir} が見つかりません。")
        return

    # ファイルリストの取得とソート
    files = [f for f in os.listdir(word_dir) if f.endswith(".html")]
    files.sort(key=natural_sort_key)

    # 目次グループ化用
    grouped_chapters = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        # 【】の中身を抽出。なければ「Others」
        group_match = re.search(r'【(.*?)】', title)
        group_name = group_match.group(1) if group_match else "Others"
        # ボタンには【】以降のテキストを表示
        display_label = title.split('】')[-1] if '】' in title else title
        grouped_chapters[group_name].append((s_num, display_label))

    html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>English Dictionary</title>
    <style>
        :root { --primary-color: #007bff; --chapter-color: #6c757d; --bg-color: #f4f7f9; }
        body { font-family: sans-serif; background-color: var(--bg-color); margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 800px; }
        h1 { color: var(--primary-color); text-align: center; border-bottom: 3px solid var(--primary-color); padding-bottom: 10px; margin-bottom: 15px; }
        .header-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        
        /* 演習ページへのボタンリンク */
        .exercise-link {
            display: block;
            width: fit-content;
            margin: 0 auto 30px;
            padding: 12px 40px;
            background-color: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            font-size: 1.1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: 0.3s;
            border: none;
        }
        .exercise-link:hover {
            background-color: #218838;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }

        /* 目次 (TOC) 改良 */
        .toc { background: white; padding: 20px; border-radius: 10px; margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .toc-group { margin-bottom: 15px; }
        .toc-group-title { font-size: 0.9rem; font-weight: bold; color: #333; margin-bottom: 8px; border-left: 4px solid var(--primary-color); padding-left: 10px; }
        .toc-links { display: flex; flex-wrap: wrap; gap: 6px; list-style: none; padding: 0; margin: 0; }
        .toc-links a { text-decoration: none; color: var(--primary-color); font-size: 0.8rem; background: #f0f4f8; padding: 5px 10px; border-radius: 4px; transition: 0.2s; border: 1px solid #dce3e9; }
        .toc-links a:hover { background: var(--primary-color); color: white; border-color: var(--primary-color); }

        .search-box { width: 100%; padding: 15px; font-size: 18px; border: 2px solid #ddd; border-radius: 10px; margin-bottom: 20px; box-sizing: border-box; outline: none; }
        .search-box:focus { border-color: var(--primary-color); }
        
        .word-list { list-style: none; padding: 0; }
        .chapter-header { background: var(--chapter-color); color: white; padding: 10px 15px; margin: 40px 0 12px 0; border-radius: 5px; font-weight: bold; scroll-margin-top: 20px; }
        .word-item { background: white; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: 0.2s; }
        .word-item:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .word-item a { display: flex; padding: 12px 20px; text-decoration: none; color: #333; align-items: center; }
        .word-id { font-weight: bold; color: var(--primary-color); min-width: 75px; font-family: monospace; }
        .word-name { font-size: 1.1em; font-weight: 500; }
        .word-meaning { font-size: 0.78em; color: #888; margin-left: 12px; font-weight: normal; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px; }
        
        .sub-word { margin-left: 30px; border-left: 4px solid #ccd5ae; background-color: #fafafa; }
        .sub-word .word-id { color: #6a994e; }
        
        .word-item.hidden { display: none; }
        .loading-indicator { text-align: center; padding: 20px; color: var(--chapter-color); }

        /* Back to Top Button */
        #backToTop {
            position: fixed; bottom: 30px; right: 30px; width: 50px; height: 50px;
            background-color: var(--primary-color); color: white; border: none; border-radius: 50%;
            cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: none;
            align-items: center; justify-content: center; font-size: 24px; z-index: 1000;
        }

        /* ホームに戻るボタン（special-linkをベースに調整） */
        .btn-home {
            display: inline-block;
            padding: 8px 20px;
            background-color: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: 0.3s;
        }
        
        .btn-home:hover {
            background-color: #5a6268;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
    </style>
</head>
<body>

<div class="header-nav">
    <a href="index.html" class="btn btn-home">ホームに戻る</a>
</div>
    
<div class="container">
    <h1>英単語辞書 データベース</h1>

    <a href="exercise.html" class="exercise-link">演習を始める</a>

    <nav class="toc">
"""

    # --- グループ化された目次の生成 ---
    for group_name, chapters in grouped_chapters.items():
        html_content += f'        <div class="toc-group">\n'
        html_content += f'            <div class="toc-group-title">{group_name}</div>\n'
        html_content += f'            <ul class="toc-links">\n'
        for s_num, label in chapters:
            html_content += f'                <li><a href="#chapter-{s_num}">{label}</a></li>\n'
        html_content += f'            </ul>\n'
        html_content += f'        </div>\n'

    html_content += """    </nav>
    <input type="text" id="searchInput" class="search-box" placeholder="単語・番号で検索..." onkeyup="filterList()">
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
        display_name = re.sub(r'^[0-9-]+', '', word_id_full).replace("-", " ").strip()
        parts = word_id_full.split("-")
        # 枝番チェック (例: 422-2)
        is_sub = len(parts) > 1 and parts[1].isdigit()
        item_class = "word-item sub-word" if is_sub else "word-item"
        display_id = parts[0] + ("-" + parts[1] if is_sub else "")

        # 日本語訳を取得 (正しいパスを指定)
        meaning = get_japanese_meaning(word_dir / filename)

        # リンク先は data/filename (index.htmlからの相対パス)
        html_content += f'        <li class="{item_class}"><a href="data/{filename}">'
        html_content += f'<span class="word-id">{display_id}</span>'
        html_content += f'<span class="word-name">{display_name}</span>'
        if meaning:
            html_content += f'<span class="word-meaning">{meaning}</span>'
        html_content += f'</a></li>\n'

    html_content += """    </ul>
    <div class="loading-indicator" id="loadingIndicator">スクロールして読み込み...</div>
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

    # english_dictionary/index.html として保存
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Update Complete: {output_file} has been rebuilt.")

if __name__ == "__main__":
    generate_index()
