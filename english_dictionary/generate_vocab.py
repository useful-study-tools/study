import json
import os
import re
from pathlib import Path
from glob import glob
from config import CHAPTER_MAP 

# ==========================================
# 1. HTMLテンプレート (メイン単語用)
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
        :root {{ --primary-color: #2c3e50; --accent-color: #f4f7f6; --text-main: #333; --text-sub: #666; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.7; color: var(--text-main); margin: 0; padding: 20px; background-color: #f0f2f5; display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; }}
        .card {{ background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
        .nav-buttons {{ display: flex; justify-content: space-between; margin-bottom: 20px; gap: 10px; }}
        .nav-button {{ flex: 1; padding: 12px 20px; border: 2px solid var(--primary-color); background: white; color: var(--primary-color); text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; transition: 0.3s; cursor: pointer; }}
        .nav-button:hover:not(.disabled) {{ background: var(--primary-color); color: white; }}
        .nav-button.disabled {{ opacity: 0.3; cursor: not-allowed; border-color: #ccc; color: #ccc; }}
        .btn-home {{ display: inline-block; margin-bottom: 20px; padding: 8px 18px; background-color: #6c757d; color: white !important; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 0.85rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.3s; }}
        .btn-home:hover {{ background-color: #5a6268; transform: translateY(-1px); }}
        .word-header {{ border-bottom: 3px solid var(--primary-color); padding-bottom: 15px; margin-bottom: 25px; }}
        .word-number {{ font-size: 1rem; color: var(--text-sub); font-weight: bold; }}
        .word-title {{ font-size: 3rem; margin: 5px 0; letter-spacing: 1px; }}
        .pos-tag {{ display: inline-block; background: var(--primary-color); color: white; padding: 2px 12px; border-radius: 20px; font-size: 0.85rem; vertical-align: middle; margin-left: 10px; }}
        .section-title {{ font-size: 1.1rem; font-weight: bold; color: var(--primary-color); margin-top: 25px; margin-bottom: 10px; display: flex; align-items: center; }}
        .section-title::before {{ content: ""; display: inline-block; width: 4px; height: 18px; background: var(--primary-color); margin-right: 10px; border-radius: 2px; }}
        .meaning-jp {{ font-size: 1.5rem; font-weight: bold; display: block; margin-bottom: 15px; padding: 10px 0; color: var(--text-main); }}
        .nuance-box {{ background: var(--accent-color); padding: 15px; border-radius: 8px; font-size: 0.95rem; border: 1px dashed var(--primary-color); }}
        .example-item {{ margin-bottom: 15px; padding-left: 15px; border-left: 3px solid #ddd; }}
        .en {{ display: block; font-weight: 500; color: #444; }}
        .ja {{ display: block; color: var(--text-sub); font-size: 0.9rem; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
        .info-item {{ background: #f8f9fa; padding: 12px; border-radius: 8px; font-size: 0.9rem; }}
        .info-label {{ display: block; font-weight: bold; color: var(--text-sub); font-size: 0.8rem; text-transform: uppercase; margin-bottom: 5px; }}
        .list-unit {{ margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
        .list-unit:last-child {{ border-bottom: none; }}
        .word-small {{ font-weight: bold; color: #444; }}
        .trans-small {{ color: var(--text-sub); font-size: 0.85em; margin-left: 5px; }}
        .source-tag {{ font-size: 0.75rem; color: #888; margin-left: 4px; border: 1px solid #ccc; border-radius: 4px; padding: 0 4px; }}
        .list-unit a {{ text-decoration: none; color: #4169e1; }}
        .list-unit a:hover {{ text-decoration: underline; opacity: 0.8; }}
        .list-unit a .word-small {{ color: inherit !important; }}

        @media (max-width: 600px) {{ .info-grid {{ grid-template-columns: 1fr; }} .word-title {{ font-size: 2.2rem; }} }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="btn-home">辞書へ戻る</a>
        <div class="nav-buttons">
            {prev_button}
            {next_button}
        </div>
        <div class="card">
            <div class="word-header">
                <span class="word-number"># {number}</span>
                <h1 class="word-title">{word} <span class="pos-tag">{pos}</span></h1>
            </div>
            <div class="section-title">主な意味</div>
            <div class="meaning-jp">{meaning}</div>
            <div class="nuance-box">
                <strong>ニュアンス:</strong> {nuance}
            </div>
            {examples_sections}
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">語源</span>
                    {etymology}
                </div>
                <div class="info-item">
                    <span class="info-label">類義語 (Synonyms)</span>
                    {synonyms}
                </div>
                <div class="info-item">
                    <span class="info-label">対義語 (Antonyms)</span>
                    {antonyms}
                </div>
                <div class="info-item">
                    <span class="info-label">関連語</span>
                    {related}
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

# サブ単語テンプレート（メイン単語と同じだがスタイル色が異なる。リンク色は継承）
HTML_TEMPLATE_SUB = HTML_TEMPLATE_MAIN.replace("--primary-color: #2c3e50", "--primary-color: #28a745").replace("--accent-color: #f4f7f6", "--accent-color: #f4faf6")

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

def load_all_vocabulary_files():
    all_words = []
    base_path = 'english_dictionary'
    json_files = []
    
    main_json = os.path.join(base_path, 'vocabulary_data.json')
    if os.path.exists(main_json):
        json_files.append(main_json)
    
    numbered_pattern = os.path.join(base_path, 'vocabulary_data_*.json')
    numbered_files = sorted(glob(numbered_pattern), 
                           key=lambda x: int(re.search(r'_(\d+)\.json', x).group(1)))
    json_files.extend(numbered_files)
    
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

def generate_word_list(target_words, all_words_data, is_sub_word=False):
    word_to_links = {}
    for w in all_words_data:
        name_lower = w['word'].lower()
        if name_lower not in word_to_links:
            word_to_links[name_lower] = []
        word_to_links[name_lower].append({
            'filename': get_filename(w),
            'label': get_source_label(w['number'])
        })

    html = ""
    for w in target_words:
        word_name = w["word"]
        word_name_lower = word_name.lower()
        trans = w["trans"]
        found_links = word_to_links.get(word_name_lower, [])
        manual_link = w.get('link')
        
        html += '<div class="list-unit">'
        
        if manual_link:
            # リンク色をCSSで制御するためインライン色は排除
            html += f'<a href="{manual_link}"><span class="word-small">{word_name}</span></a>'
        elif found_links:
            for i, link_info in enumerate(found_links):
                label = link_info['label']
                suffix = f'<span class="source-tag">{label}</span>' if len(found_links) > 1 else ""
                html += f'<a href="{link_info["filename"]}">'
                html += f'<span class="word-small">{word_name}</span>{suffix}</a> '
        else:
            html += f'<span class="word-small">{word_name}</span>'
            
        html += f'<span class="trans-small">({trans})</span></div>\n'
    return html

def generate_example_section(section_title, examples):
    html = f'        <div class="section-title">{section_title}</div>\n'
    for ex in examples:
        highlight = ex.get('highlight', '')
        en_text = ex['en']
        if highlight:
            en_text = en_text.replace(highlight, f"<strong>{highlight}</strong>")
        html += f'''        <div class="example-item">
            <span class="en">{en_text}</span>
            <span class="ja">{ex['ja']}</span>
        </div>\n'''
    return html

def generate_html(data, current_index, sorted_words):
    is_sub_word = '-' in str(data['number'])
    template = HTML_TEMPLATE_SUB if is_sub_word else HTML_TEMPLATE_MAIN
    
    prev_b = f'<a href="{get_filename(sorted_words[current_index-1])}" class="nav-button">← 前の単語</a>' if current_index > 0 else '<span class="nav-button disabled">← 前の単語</span>'
    next_b = f'<a href="{get_filename(sorted_words[current_index+1])}" class="nav-button">次の単語 →</a>' if current_index < len(sorted_words)-1 else '<span class="nav-button disabled">次の単語 →</span>'
    
    ex_secs = ""
    if 'example_sections' in data:
        for s in data['example_sections']:
            ex_secs += generate_example_section(s['title'], s['examples'])
    else:
        ex_secs = generate_example_section('例文', data.get('examples', []))
    
    return template.format(
        number=data['number'], word=data['word'], pos=data['pos'],
        meaning=data['meaning'], nuance=data['nuance'],
        examples_sections=ex_secs,
        etymology=data.get('etymology', '不明または未記載'),
        synonyms=generate_word_list(data.get('synonyms', []), sorted_words, is_sub_word),
        antonyms=generate_word_list(data.get('antonyms', []), sorted_words, is_sub_word),
        related=generate_word_list(data.get('related', []), sorted_words, is_sub_word),
        prev_button=prev_b, next_button=next_b
    )

def main():
    all_words = load_all_vocabulary_files()
    if not all_words: return
    
    sorted_words = sorted(all_words, key=lambda w: parse_number(w['number']))
    output_dir = Path('english_dictionary/data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"HTML生成中... (全 {len(sorted_words)} 件)")
    for index, word_data in enumerate(sorted_words):
        html_content = generate_html(word_data, index, sorted_words)
        filepath = output_dir / get_filename(word_data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print("✅ すべてのHTMLファイルが english_dictionary/data/ に生成されました。")

if __name__ == '__main__':
    main()
