import os
import re
import json
from collections import defaultdict
from pathlib import Path

try:
    from config import CHAPTER_MAP
except ImportError:
    print("エラー: config.py が見つかりません。")
    exit()

# ==========================================
# 1. 補助関数と設定
# ==========================================
BOOK_SLUGS = {
    "速読英単語": "sokutan",
    "FINAL DRAFT": "final_draft",
    "Change the World": "change_the_world",
    "東進上級英単語1000": "toshin",
    "鉄壁": "teppeki",
    "LEAP": "leap"
}

def get_slug(book_name):
    return BOOK_SLUGS.get(book_name, "others")

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
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'<div class="meaning-jp">\s*(.*?)\s*</div>', content, re.DOTALL)
        if match:
            return re.sub(r'<[^>]+>', '', match.group(1)).strip()
    except:
        pass
    return ""

def parse_chapter_title(title):
    match = re.search(r'【(.*?)】(.*)', title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "その他", title

# ==========================================
# 2. メイン処理
# ==========================================
def generate_index():
    base_dir = Path("english_dictionary")
    word_dir = base_dir / "data"
    
    if not word_dir.exists():
        print(f"エラー: ディレクトリ {word_dir} が見つかりません。")
        return

    files = [f for f in os.listdir(word_dir) if f.endswith(".html")]
    files.sort(key=natural_sort_key)

    books = defaultdict(lambda: {"slug": "", "chapters": {}})
    sorted_thresholds = sorted(CHAPTER_MAP.keys(), reverse=True)

    # 章の枠組みをセットアップ
    for t_id in sorted(CHAPTER_MAP.keys()):
        book_name, chapter_title = parse_chapter_title(CHAPTER_MAP[t_id])
        slug = get_slug(book_name)
        books[book_name]["slug"] = slug
        books[book_name]["chapters"][t_id] = {"title": chapter_title, "words": []}

    search_json_data = defaultdict(list)

    for filename in files:
        base_num = get_base_number(filename)
        for t in sorted_thresholds:
            if base_num >= t:
                book_name, _ = parse_chapter_title(CHAPTER_MAP[t])
                slug = get_slug(book_name)
                
                word_id_full = filename.replace(".html", "")
                display_name = re.sub(r'^[0-9-]+', '', word_id_full).replace("-", " ").strip()
                parts = word_id_full.split("-")
                is_sub = len(parts) > 1 and parts[1].isdigit()
                display_id = parts[0] + ("-" + parts[1] if is_sub else "")
                meaning = get_japanese_meaning(word_dir / filename)

                word_data = {
                    "id": display_id,
                    "name": display_name,
                    "meaning": meaning,
                    "filename": filename,
                    "is_sub": is_sub
                }
                
                books[book_name]["chapters"][t]["words"].append(word_data)
                
                search_json_data[slug].append({
                    "id": display_id,
                    "name": display_name,
                    "meaning": meaning,
                    "link": f"data/{filename}",
                    "chapter_page": f"{slug}_{t}.html"
                })
                break

    # ==========================================
    # 3. 検索用JSONファイルの生成
    # ==========================================
    for slug, words in search_json_data.items():
        json_path = base_dir / f"search_{slug}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False, separators=(',', ':'))

    # 共通CSSの定義 (パンくずリスト, ナビゲーションボタンなど)
    common_css = """
        body { font-family: sans-serif; background: #f4f7f9; padding: 20px; max-width: 800px; margin: 0 auto; color: #333; }
        h1 { color: #007bff; text-align: center; margin-bottom: 20px; }
        h2.section-title { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 8px; margin-top: 35px; margin-bottom: 15px; font-size: 1.3em; }
        
        .breadcrumb { margin-bottom: 25px; font-size: 0.9em; padding: 12px 15px; background: #e9ecef; border-radius: 6px; color: #6c757d; }
        .breadcrumb a { color: #007bff; text-decoration: none; font-weight: bold; }
        .breadcrumb a:hover { text-decoration: underline; }
        
        .btn { display: inline-block; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; text-align: center; border: none; cursor: pointer; transition: 0.2s; }
        .btn:hover { opacity: 0.8; transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .btn-exercise { background: #28a745; color: white; padding: 12px 30px; font-size: 1.1rem; border-radius: 30px; display: block; width: fit-content; margin: 0 auto 30px; }
        
        /* 前後章ナビゲーションボタンのスタイル */
        .nav-buttons { display: flex; justify-content: space-between; margin: 20px 0; }
        .nav-btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; transition: 0.2s; }
        .nav-btn:hover { background: #0056b3; transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .nav-btn.disabled { background: #ccc; color: #666; cursor: not-allowed; pointer-events: none; transform: none; box-shadow: none; }
    """

    # ==========================================
    # 4. メインページ (index.html) の生成
    # ==========================================
    main_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英単語帳トップ</title>
    <link rel="icon" href="../favicon.png" type="image/png">
    <style>
        {common_css}
        .search-controls {{ display: flex; gap: 10px; margin-bottom: 15px; }}
        select, input[type="text"] {{ padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box; }}
        input[type="text"] {{ flex-grow: 1; }}
        .result-item {{ padding: 12px; border-bottom: 1px solid #eee; display: flex; flex-direction: column; background: white; margin-bottom: 5px; border-radius: 6px; }}
        .result-item a {{ text-decoration: none; color: #007bff; font-weight: bold; font-size: 1.1em; }}
        .result-meaning {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
        
        .book-list {{ display: flex; flex-direction: column; gap: 10px; }}
        .book-link {{ display: block; padding: 15px 20px; background: white; border: 1px solid #ddd; border-radius: 8px; text-decoration: none; color: #333; font-weight: bold; font-size: 1.1rem; transition: 0.2s; }}
        .book-link:hover {{ border-color: #007bff; color: #007bff; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="breadcrumb">
        <a href="../index.html">ホーム</a> > 英単語帳
    </div>

    <h1>英単語辞書 データベース</h1>
    
    <a href="exercise.html" class="btn btn-exercise">📝 演習を始める</a>

    <h2 class="section-title">🔍 単語検索</h2>
    <div class="search-controls">
        <select id="bookSelect" onchange="loadSearchData()">
            <option value="">-- 単語帳を選択 --</option>
"""
    for book_name, data in books.items():
        main_html += f'            <option value="{data["slug"]}">{book_name}</option>\n'
        
    main_html += """        </select>
        <input type="text" id="globalSearchInput" placeholder="単語・番号・意味を入力..." onkeyup="executeSearch()" disabled>
    </div>
    <div id="searchResults"></div>

    <h2 class="section-title">📚 単語帳一覧</h2>
    <div class="book-list">
"""
    for book_name, data in books.items():
        main_html += f'        <a href="{data["slug"]}.html" class="book-link">{book_name}</a>\n'

    main_html += """    </div>

<script>
    let currentSearchData = [];
    const bookSelect = document.getElementById('bookSelect');
    const searchInput = document.getElementById('globalSearchInput');
    const searchResults = document.getElementById('searchResults');

    async function loadSearchData() {
        const slug = bookSelect.value;
        if (!slug) {
            searchInput.disabled = true;
            searchInput.value = '';
            searchResults.innerHTML = '';
            currentSearchData = [];
            return;
        }
        
        searchInput.disabled = true;
        searchInput.placeholder = "JSONを読み込み中...";
        
        try {
            const response = await fetch(`search_${slug}.json`);
            currentSearchData = await response.json();
            searchInput.disabled = false;
            searchInput.placeholder = "単語・番号・意味を入力...";
            executeSearch();
        } catch (error) {
            console.error("JSONの読み込みに失敗しました:", error);
            searchInput.placeholder = "読み込みエラー";
        }
    }

    function executeSearch() {
        const query = searchInput.value.toLowerCase().trim();
        if (!query) {
            searchResults.innerHTML = '';
            return;
        }

        const filtered = currentSearchData.filter(word => 
            word.id.toLowerCase().includes(query) || 
            word.name.toLowerCase().includes(query) || 
            word.meaning.includes(query)
        );

        if (filtered.length === 0) {
            searchResults.innerHTML = '<p style="color:#666; padding: 10px;">見つかりませんでした。</p>';
            return;
        }

        const html = filtered.slice(0, 50).map(word => `
            <div class="result-item">
                <a href="${word.link}">[${word.id}] ${word.name}</a>
                <span class="result-meaning">${word.meaning} <span style="font-size:0.8em; color:#999; margin-left:10px;">(収録: <a href="${word.chapter_page}" style="color:#007bff; text-decoration:none;">章ページへ</a>)</span></span>
            </div>
        `).join('');
        
        searchResults.innerHTML = html;
    }
</script>
</body>
</html>"""

    with open(base_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(main_html)

    # ==========================================
    # 5. 各単語帳トップページ ＆ 章別ページの生成
    # ==========================================
    for book_name, book_data in books.items():
        slug = book_data["slug"]
        
        # --- 5-1. 単語帳トップページ (例: sokutan.html) ---
        book_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{book_name} | 目次</title>
    <link rel="icon" href="../favicon.png" type="image/png">
    <style>
        {common_css}
        .chapter-list {{ display: flex; flex-direction: column; gap: 8px; }}
        .chapter-link {{ display: block; padding: 12px 15px; background: white; border: 1px solid #ddd; border-radius: 6px; text-decoration: none; color: #333; transition: 0.2s; font-weight: 500; }}
        .chapter-link:hover {{ background: #007bff; color: white; border-color: #007bff; }}
    </style>
</head>
<body>
    <div class="breadcrumb">
        <a href="../index.html">ホーム</a> > <a href="index.html">英単語帳</a> > {book_name}
    </div>

    <h1>{book_name}</h1>
    <h2 class="section-title">📖 章を選択</h2>
    <div class="chapter-list">
"""
        for ch_id, ch_data in book_data["chapters"].items():
            if ch_data["words"]:
                book_html += f'        <a href="{slug}_{ch_id}.html" class="chapter-link">{ch_data["title"]}</a>\n'

        book_html += """    </div>
</body>
</html>"""
        with open(base_dir / f"{slug}.html", "w", encoding="utf-8") as f:
            f.write(book_html)


        # --- 5-2. 章別ページ (例: sokutan_1.html) ---
        # 単語が1つ以上含まれる章のIDだけを抽出し、ソートする
        valid_ch_ids = sorted([ch_id for ch_id, ch_data in book_data["chapters"].items() if ch_data["words"]])
        
        for i, ch_id in enumerate(valid_ch_ids):
            ch_data = book_data["chapters"][ch_id]
            
            # ナビゲーションボタンの生成
            if i > 0:
                prev_btn = f'<a href="{slug}_{valid_ch_ids[i-1]}.html" class="nav-btn">← 前の章</a>'
            else:
                prev_btn = f'<span class="nav-btn disabled">← 前の章</span>'
                
            if i < len(valid_ch_ids) - 1:
                next_btn = f'<a href="{slug}_{valid_ch_ids[i+1]}.html" class="nav-btn">次の章 →</a>'
            else:
                next_btn = f'<span class="nav-btn disabled">次の章 →</span>'
                
            nav_html = f'<div class="nav-buttons">\n        {prev_btn}\n        {next_btn}\n    </div>'
                
            chapter_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ch_data["title"]} | {book_name}</title>
    <link rel="icon" href="../favicon.png" type="image/png">
    <style>
        {common_css}
        .local-search {{ width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; margin-bottom: 20px; box-sizing: border-box; }}
        
        .word-list {{ list-style: none; padding: 0; margin: 0; }}
        .word-item {{ background: white; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: 0.2s; }}
        .word-item:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
        .word-item a {{ display: flex; padding: 15px 20px; text-decoration: none; color: #333; align-items: center; gap: 15px; }}
        .word-id {{ font-weight: bold; color: #007bff; font-family: monospace; min-width: 60px; }}
        .word-name {{ font-size: 1.1em; font-weight: 500; min-width: 120px; }}
        .word-meaning {{ font-size: 0.9em; color: #666; }}
        
        .sub-word {{ margin-left: 20px; border-left: 4px solid #ccd5ae; background-color: #fafafa; }}
    </style>
</head>
<body>
    <div class="breadcrumb">
        <a href="../index.html">ホーム</a> > <a href="index.html">英単語帳</a> > <a href="{slug}.html">{book_name}</a> > {ch_data["title"]}
    </div>
    
    <h2 class="section-title">{ch_data["title"]}</h2>
    
    {nav_html}
    
    <input type="text" id="localSearch" class="local-search" placeholder="この章の中で検索..." onkeyup="filterLocal()">

    <ul class="word-list" id="wordList">
"""
            for word in ch_data["words"]:
                item_class = "word-item sub-word" if word["is_sub"] else "word-item"
                chapter_html += f'        <li class="{item_class}"><a href="data/{word["filename"]}">'
                chapter_html += f'<span class="word-id">{word["id"]}</span>'
                chapter_html += f'<span class="word-name">{word["name"]}</span>'
                chapter_html += f'<span class="word-meaning">{word["meaning"]}</span>'
                chapter_html += f'</a></li>\n'

            chapter_html += f"""    </ul>

    {nav_html}

<script>
    function filterLocal() {{
        const filter = document.getElementById('localSearch').value.toLowerCase();
        const items = document.getElementById('wordList').getElementsByTagName('li');
        
        for (let i = 0; i < items.length; i++) {{
            const text = items[i].textContent || items[i].innerText;
            if (text.toLowerCase().indexOf(filter) > -1) {{
                items[i].style.display = "";
            }} else {{
                items[i].style.display = "none";
            }}
        }}
    }}
</script>
</body>
</html>"""
            
            with open(base_dir / f"{slug}_{ch_id}.html", "w", encoding="utf-8") as f:
                f.write(chapter_html)
                
    print("Update Complete: All index, book, and chapter pages have been generated successfully.")

if __name__ == "__main__":
    generate_index()
