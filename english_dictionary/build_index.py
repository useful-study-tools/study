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

    # books[book_name] = { 
    #   "slug": "sokutan",
    #   "chapters": { chapter_id: {"title": "第1章...", "words": []} } 
    # }
    books = defaultdict(lambda: {"slug": "", "chapters": {}})
    sorted_thresholds = sorted(CHAPTER_MAP.keys(), reverse=True)

    # 章の枠組みをセットアップ
    for t_id in sorted(CHAPTER_MAP.keys()):
        book_name, chapter_title = parse_chapter_title(CHAPTER_MAP[t_id])
        slug = get_slug(book_name)
        books[book_name]["slug"] = slug
        books[book_name]["chapters"][t_id] = {"title": chapter_title, "words": []}

    # 各単語ファイルを適切な章に振り分け、同時にJSON用データを構築
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
                
                # 検索用JSONデータにも追加
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
        print(f"Created JSON: {json_path}")

    # ==========================================
    # 4. メインページ (index.html) の生成
    # ==========================================
    main_html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英単語帳トップ</title>
    <style>
        body { font-family: sans-serif; background: #f4f7f9; padding: 20px; max-width: 800px; margin: 0 auto; }
        h1 { color: #007bff; text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .btn { display: inline-block; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; text-align: center; color: white; background: #007bff; border: none; cursor: pointer; margin: 5px; }
        .btn:hover { opacity: 0.8; }
        .book-list { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
        .book-link { display: block; padding: 15px; background: white; border: 1px solid #ddd; border-radius: 8px; text-decoration: none; color: #333; font-weight: bold; font-size: 1.2rem; transition: 0.2s; }
        .book-link:hover { border-color: #007bff; color: #007bff; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        
        .search-container { background: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .search-controls { display: flex; gap: 10px; margin-bottom: 15px; }
        select, input[type="text"] { padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; }
        input[type="text"] { flex-grow: 1; }
        .result-item { padding: 10px; border-bottom: 1px solid #eee; display: flex; flex-direction: column; }
        .result-item a { text-decoration: none; color: #007bff; font-weight: bold; }
        .result-meaning { font-size: 0.85em; color: #666; margin-top: 4px; }
    </style>
</head>
<body>
    <a href="../index.html" class="btn" style="background:#6c757d;">← サイトトップへ</a>
    <h1>英単語辞書 データベース</h1>

    <div class="search-container">
        <h3>🔍 単語検索</h3>
        <div class="search-controls">
            <select id="bookSelect" onchange="loadSearchData()">
                <option value="">-- 単語帳を選択 --</option>
"""
    for book_name, data in books.items():
        main_html += f'                <option value="{data["slug"]}">{book_name}</option>\n'
        
    main_html += """            </select>
            <input type="text" id="globalSearchInput" placeholder="単語・番号・意味を入力..." onkeyup="executeSearch()" disabled>
        </div>
        <div id="searchResults"></div>
    </div>

    <h3>📚 単語帳一覧</h3>
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
            executeSearch(); // 既存の入力があれば即時検索
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
            searchResults.innerHTML = '<p style="color:#666;">見つかりませんでした。</p>';
            return;
        }

        // 最大50件まで表示
        const html = filtered.slice(0, 50).map(word => `
            <div class="result-item">
                <a href="${word.link}">[${word.id}] ${word.name}</a>
                <span class="result-meaning">${word.meaning} <span style="font-size:0.8em; color:#999;">(収録: <a href="${word.chapter_page}" style="color:#999; text-decoration:underline;">章ページへ</a>)</span></span>
            </div>
        `).join('');
        
        searchResults.innerHTML = html;
    }
</script>
</body>
</html>"""

    with open(base_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(main_html)
    print("Created Main Index: index.html")

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
    <style>
        body {{ font-family: sans-serif; background: #f4f7f9; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #007bff; text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .btn {{ display: inline-block; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; background: #6c757d; color: white; margin-bottom: 20px; }}
        .chapter-list {{ display: flex; flex-direction: column; gap: 8px; }}
        .chapter-link {{ display: block; padding: 12px 15px; background: white; border: 1px solid #ddd; border-radius: 6px; text-decoration: none; color: #333; transition: 0.2s; }}
        .chapter-link:hover {{ background: #007bff; color: white; border-color: #007bff; }}
    </style>
</head>
<body>
    <a href="index.html" class="btn">← 単語帳一覧へ</a>
    <h1>{book_name}</h1>
    <div class="chapter-list">
"""
        for ch_id, ch_data in book_data["chapters"].items():
            if ch_data["words"]: # 単語が1つ以上ある章だけリンクを作成
                book_html += f'        <a href="{slug}_{ch_id}.html" class="chapter-link">{ch_data["title"]}</a>\n'

        book_html += """    </div>
</body>
</html>"""
        with open(base_dir / f"{slug}.html", "w", encoding="utf-8") as f:
            f.write(book_html)


        # --- 5-2. 章別ページ (例: sokutan_1.html) ---
        for ch_id, ch_data in book_data["chapters"].items():
            if not ch_data["words"]:
                continue
                
            chapter_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ch_data["title"]} | {book_name}</title>
    <style>
        body {{ font-family: sans-serif; background: #f4f7f9; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h2 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .breadcrumb {{ margin-bottom: 20px; font-size: 0.9em; }}
        .breadcrumb a {{ color: #007bff; text-decoration: none; }}
        
        .local-search {{ width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; margin-bottom: 20px; box-sizing: border-box; }}
        
        .word-list {{ list-style: none; padding: 0; margin: 0; }}
        .word-item {{ background: white; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: 0.2s; }}
        .word-item:hover {{ transform: translateY(-2px); }}
        .word-item a {{ display: flex; padding: 15px 20px; text-decoration: none; color: #333; align-items: center; gap: 15px; }}
        .word-id {{ font-weight: bold; color: #007bff; font-family: monospace; min-width: 60px; }}
        .word-name {{ font-size: 1.1em; font-weight: 500; min-width: 120px; }}
        .word-meaning {{ font-size: 0.9em; color: #666; }}
        
        .sub-word {{ margin-left: 20px; border-left: 4px solid #ccd5ae; background-color: #fafafa; }}
    </style>
</head>
<body>
    <div class="breadcrumb">
        <a href="index.html">ホーム</a> > <a href="{slug}.html">{book_name}</a> > {ch_data["title"]}
    </div>
    
    <h2>{ch_data["title"]}</h2>
    
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

            chapter_html += """    </ul>

<script>
    function filterLocal() {
        const filter = document.getElementById('localSearch').value.toLowerCase();
        const items = document.getElementById('wordList').getElementsByTagName('li');
        
        for (let i = 0; i < items.length; i++) {
            const text = items[i].textContent || items[i].innerText;
            if (text.toLowerCase().indexOf(filter) > -1) {
                items[i].style.display = "";
            } else {
                items[i].style.display = "none";
            }
        }
    }
</script>
</body>
</html>"""
            
            chapter_file = base_dir / f"{slug}_{ch_id}.html"
            with open(chapter_file, "w", encoding="utf-8") as f:
                f.write(chapter_html)
                
        print(f"Created Book & Chapter pages for: {book_name}")

if __name__ == "__main__":
    generate_index()
