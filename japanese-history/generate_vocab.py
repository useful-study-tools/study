import json
import os
import re
from pathlib import Path
from glob import glob
from config import CHAPTER_MAP 

# ==========================================
# 1. HTMLテンプレート (メイン用語用)
# ==========================================
HTML_TEMPLATE_MAIN = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{number} {word}</title>
    <link rel="icon" href="/study/favicon.png" type="image/png">
    <link rel="apple-touch-icon" href="/study/favicon.png">
    <style>
        :root {{ --primary-color: #8b0000; --accent-color: #f9f7f2; --text-main: #2c2c2c; --text-sub: #555; }}
        body {{ font-family: "Hiragino Mincho ProN", "MS Mincho", serif; line-height: 1.8; color: var(--text-main); margin: 0; padding: 20px; background-color: #f2f0eb; display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; }}
        .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 15px rgba(0,0,0,0.1); border-top: 5px solid var(--primary-color); }}
        .nav-buttons {{ display: flex; justify-content: space-between; margin-bottom: 20px; gap: 10px; }}
        .nav-button {{ flex: 1; padding: 12px 20px; border: 1px solid var(--primary-color); background: white; color: var(--primary-color); text-decoration: none; border-radius: 4px; font-weight: bold; text-align: center; transition: 0.3s; cursor: pointer; }}
        .nav-button:hover:not(.disabled) {{ background: var(--primary-color); color: white; }}
        .nav-button.disabled {{ opacity: 0.3; cursor: not-allowed; border-color: #ccc; color: #ccc; }}
        .btn-home {{ display: inline-block; margin-bottom: 20px; padding: 8px 18px; background-color: #6c757d; color: white !important; text-decoration: none; border-radius: 4px; font-size: 0.85rem; transition: 0.3s; }}
        
        .word-header {{ border-bottom: 1px solid #ddd; padding-bottom: 15px; margin-bottom: 25px; }}
        .word-number {{ font-size: 1rem; color: var(--text-sub); font-family: monospace; }}
        .word-title {{ font-size: 2.5rem; margin: 5px 0; color: var(--primary-color); }}
        .era-tag {{ display: inline-block; background: #5d5d5d; color: white; padding: 2px 12px; border-radius: 4px; font-size: 0.9rem; vertical-align: middle; margin-left: 10px; }}
        
        .section-title {{ font-size: 1.1rem; font-weight: bold; color: white; background: var(--primary-color); padding: 5px 15px; margin-top: 30px; margin-bottom: 15px; border-radius: 2px; }}
        .description {{ font-size: 1.2rem; line-height: 1.9; margin-bottom: 20px; padding: 10px 0; }}
        .background-box {{ background: var(--accent-color); padding: 20px; border-radius: 4px; font-size: 0.95rem; border-left: 5px solid #d4a373; }}
        
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }}
        .info-item {{ background: #fff; border: 1px solid #eee; padding: 15px; border-radius: 4px; }}
        .info-label {{ display: block; font-weight: bold; color: var(--primary-color); font-size: 0.85rem; margin-bottom: 8px; border-bottom: 1px dotted #ccc; }}
        
        .list-unit {{ margin-bottom: 8px; font-size: 0.95rem; }}
        .list-unit a {{ text-decoration: none; color: #b22222; font-weight: bold; }}
        .list-unit a:hover {{ text-decoration: underline; }}
        .source-tag {{ font-size: 0.7rem; color: #888; margin-left: 5px; border: 1px solid #ddd; padding: 0 3px; }}

        @media (max-width: 600px) {{ .info-grid {{ grid-template-columns: 1fr; }} .word-title {{ font-size: 2rem; }} }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="btn-home">一覧へ戻る</a>
        <div class="nav-buttons">
            {prev_button}
            {next_button}
        </div>
        <div class="card">
            <div class="word-header">
                <span class="word-number">項目番号: {number}</span>
                <h1 class="word-title">{word} <span class="era-tag">{era}</span></h1>
            </div>
            
            <div class="section-title">用語解説</div>
            <div class="description">{description}</div>
            
            <div class="background-box">
                <strong>歴史的背景・詳細:</strong><br>
                {background}
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">関連人物・出来事</span>
                    {related_events}
                </div>
                <div class="info-item">
                    <span class="info-label">場所・地域</span>
                    {location}
                </div>
                <div class="info-item">
                    <span class="info-label">類義・対比語</span>
                    {comparisons}
                </div>
                <div class="info-item">
                    <span class="info-label">重要度 / 試験頻出度</span>
                    {importance}
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

# サブ単語（派生用語）用：テーマカラーを少し変えるなどの調整が可能
HTML_TEMPLATE_SUB = HTML_TEMPLATE_MAIN.replace("--primary-color: #8b0000", "--primary-color: #2f4f4f")

# ==========================================
# 2. ロジック関数
# ==========================================

def get_source_label(number_str):
    try:
        main_val = int(str(number_str).split('-')[0])
        sorted_keys = sorted(CHAPTER_MAP.keys(), reverse=True)
        for key in sorted_keys:
            if main_val >= key:
                full_label = CHAPTER_MAP[key]
                match = re.search(r'【(.*?)】', full_label)
                return match.group(1) if match else full_label
        return "その他"
    except:
        return "不明"

def load_all_history_files():
    all_words = []
    base_path = 'japanese_history'
    
    # 修正：history_dataで始まるすべてのJSONを取得し、柔軟にソートする
    pattern = os.path.join(base_path, 'history_data*.json')
    json_files = glob(pattern)
    
    # 数字が含まれる場合は数字順、そうでない場合は名前順にソート
    def sort_key(x):
        nums = re.findall(r'\d+', x)
        return int(nums[-1]) if nums else 0

    json_files.sort(key=sort_key)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_words.extend(data.get('words', []))
        except Exception as e:
            print(f"⚠ エラー ({json_file}): {e}")
    return all_words

def parse_number(number_str):
    parts = str(number_str).split('-')
    main_num = int(parts[0])
    sub_num = int(parts[1]) if len(parts) > 1 else 0
    return (main_num, sub_num)

def get_filename(word_data):
    return f"{word_data['number']}-{word_data['word']}.html"

def generate_history_link_list(target_items, all_words_data):
    """用語のリストに対して自動リンクを生成する"""
    word_to_links = {}
    for w in all_words_data:
        name = w['word']
        if name not in word_to_links:
            word_to_links[name] = []
        word_to_links[name].append({
            'filename': get_filename(w),
            'label': get_source_label(w['number'])
        })

    html = ""
    for item in target_items:
        name = item["word"]
        note = item.get("note", "") # 補足情報
        found_links = word_to_links.get(name, [])
        
        html += '<div class="list-unit">'
        if found_links:
            for link_info in found_links:
                label = link_info['label']
                suffix = f'<span class="source-tag">{label}</span>' if len(found_links) > 1 else ""
                html += f'<a href="{link_info["filename"]}">{name}{suffix}</a> '
        else:
            html += f'<strong>{name}</strong>'
        
        if note:
            html += f' <span style="color:#666; font-size:0.8em;">({note})</span>'
        html += '</div>\n'
    return html or "なし"

def generate_html(data, current_index, sorted_words):
    is_sub_word = '-' in str(data['number'])
    template = HTML_TEMPLATE_SUB if is_sub_word else HTML_TEMPLATE_MAIN
    
    prev_b = f'<a href="{get_filename(sorted_words[current_index-1])}" class="nav-button">← 前の用語</a>' if current_index > 0 else '<span class="nav-button disabled">← 前の用語</span>'
    next_b = f'<a href="{get_filename(sorted_words[current_index+1])}" class="nav-button">次の用語 →</a>' if current_index < len(sorted_words)-1 else '<span class="nav-button disabled">次の用語 →</span>'
    
    # JSONのフィールド名を日本史用にマッピング
    return template.format(
        number=data['number'], 
        word=data['word'], 
        era=data.get('era', '時代不明'), # 時代
        description=data.get('description', '解説未記入'), # 用語解説
        background=data.get('background', '背景情報なし'), # 歴史的背景
        related_events=generate_history_link_list(data.get('related', []), sorted_words), # 関連人物・出来事
        location=data.get('location', '不明'), # 場所
        comparisons=generate_history_link_list(data.get('comparisons', []), sorted_words), # 類義・対比
        importance=data.get('importance', '★★★'), # 重要度
        prev_button=prev_b, 
        next_button=next_b
    )

def main():
    all_words = load_all_history_files()
    if not all_words: 
        print("表示するデータが見つかりませんでした。")
        return
    
    sorted_words = sorted(all_words, key=lambda w: parse_number(w['number']))
    output_dir = Path('japanese_history/data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"日本史HTML生成中... (全 {len(sorted_words)} 件)")
    for index, word_data in enumerate(sorted_words):
        html_content = generate_html(word_data, index, sorted_words)
        filepath = output_dir / get_filename(word_data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print("✅ すべての日本史用語HTMLが japanese_history/data/ に生成されました。")

if __name__ == '__main__':
    main()
