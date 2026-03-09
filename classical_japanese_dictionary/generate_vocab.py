import json
import os
import re
from pathlib import Path
from glob import glob

# ==========================================
# 1. 古文単語用 HTMLテンプレート
# ==========================================
HTML_TEMPLATE_KOBUN = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{number} {word}</title>
    <link rel="icon" href="/image/logo.png">
    <style>
        :root {{ 
            --primary-color: #a33c3a; /* 茜色 */
            --bg-color: #f8f4e6;      /* 生成り色 */
            --card-bg: #ffffff;
            --text-main: #2c2c2c;
            --text-sub: #555;
            --accent-soft: #e9e4d1;
        }}
        /* 前者の body スタイルを継承 */
        body {{ 
            font-family: "Sawarabi Mincho", "Hiragino Mincho ProN", serif; 
            background-color: var(--bg-color); 
            margin: 0; 
            padding: 20px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            color: var(--text-main); 
        }}
        
        /* 前者の container スタイルを適用 */
        .container {{ 
            width: 100%; 
            max-width: 800px; 
        }}

        /* 「戻る」ボタン：前者の .btn-home と完全に一致 */
        .btn-home {{ 
            display: inline-block; 
            padding: 8px 20px; 
            background-color: var(--primary-color); 
            color: white; 
            text-decoration: none; 
            border-radius: 20px; 
            font-weight: bold; 
            font-size: 0.9rem; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            transition: 0.3s; 
            margin-bottom: 20px;
        }}
        .btn-home:hover {{ 
            background-color: #c78a88; 
            transform: translateY(-1px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.15); 
        }}

        .card {{ 
            background: var(--card-bg); 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 2px 15px rgba(0,0,0,0.05); 
            border: 1px solid #e0d9c1; 
        }}
        .nav-buttons {{ 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 20px; 
            gap: 10px; 
        }}
        .nav-button {{ 
            flex: 1; 
            padding: 10px; 
            border: 1px solid var(--primary-color); 
            background: white; 
            color: var(--primary-color); 
            text-decoration: none; 
            border-radius: 4px; 
            font-weight: bold; 
            text-align: center; 
            font-size: 0.9rem; 
            transition: 0.3s; 
        }}
        .nav-button:hover:not(.disabled) {{ 
            background: var(--primary-color); 
            color: white; 
        }}
        .nav-button.disabled {{ 
            opacity: 0.3; 
            cursor: not-allowed; 
        }}
        
        .word-header {{ 
            border-bottom: 2px solid var(--primary-color); 
            padding-bottom: 10px; 
            margin-bottom: 25px; 
        }}
        .word-number {{ 
            font-size: 0.9rem; 
            color: var(--primary-color); 
            font-weight: bold; 
        }}
        .word-title {{ 
            font-size: 2.8rem; 
            margin: 5px 0; 
            font-weight: bold; 
            display: flex; 
            align-items: baseline; 
        }}
        .pos-tag {{ 
            font-size: 0.9rem; 
            background: var(--primary-color); 
            color: white; 
            padding: 2px 10px; 
            border-radius: 3px; 
            margin-left: 15px; 
        }}
        .conj-tag {{ 
            font-size: 0.9rem; 
            border: 1px solid var(--primary-color); 
            color: var(--primary-color); 
            padding: 1px 8px; 
            border-radius: 3px; 
            margin-left: 8px; 
        }}
        .section-title {{ 
            font-size: 1.1rem; 
            font-weight: bold; 
            color: var(--primary-color); 
            margin-top: 30px; 
            border-left: 4px solid var(--primary-color); 
            padding-left: 10px; 
        }}
        .meaning-jp {{ 
            font-size: 1.4rem; 
            font-weight: bold; 
            margin: 15px 0; 
            color: #000; 
        }}
        .nuance-box {{ 
            background: var(--accent-soft); 
            padding: 15px; 
            border-radius: 5px; 
            font-size: 0.95rem; 
            line-height: 1.6; 
            border-left: 4px solid #ccc; 
        }}
        .example-item {{ 
            margin-bottom: 20px; 
            padding: 10px 15px; 
            background: #fafafa; 
            border-radius: 4px; 
        }}
        .ex-text {{ 
            display: block; 
            font-weight: bold; 
            font-size: 1.1rem; 
            color: #333; 
        }}
        .ex-trans {{ 
            display: block; 
            color: var(--text-sub); 
            font-size: 0.95rem; 
            margin-top: 5px; 
        }}
        .ex-source {{ 
            display: block; 
            text-align: right; 
            font-size: 0.8rem; 
            color: #999; 
            font-style: italic; 
        }}
        .info-grid {{ 
            display: block; 
            margin-top: 30px; 
        }}
        .info-item {{ 
            background: #fdfdfd; 
            padding: 20px; 
            border: 1px solid #eee; 
            border-radius: 8px; 
            line-height: 1.7; 
        }}
        .info-label {{ 
            display: block; 
            font-weight: bold; 
            color: var(--primary-color); 
            font-size: 1rem; 
            margin-bottom: 12px; 
            border-bottom: 1px dashed var(--primary-color); 
            padding-bottom: 5px; 
        }}
        .related-entry {{ 
            margin-bottom: 8px; 
        }}
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
                <span class="word-number">第 {number} 番</span>
                <h1 class="word-title">{word} 
                    <span class="pos-tag">{pos}</span>
                    {conj_html}
                </h1>
            </div>

            <div class="section-title">現代語訳</div>
            <div class="meaning-jp">{meaning}</div>
            
            <div class="nuance-box">
                <strong>【解釈のポイント】</strong><br>{nuance}
            </div>

            <div class="section-title">例文</div>
            {examples_html}

            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">関連知識・類義語など</span>
                    {related}
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

# （以下の関数群は変更なし）

def load_all_vocabulary_files():
    all_words = []
    base_path = 'classical_japanese_dictionary'
    json_files = sorted(glob(os.path.join(base_path, 'vocabulary_data*.json')))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_words.extend(data.get('words', []))
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    return all_words

def generate_html(data, current_index, sorted_words):
    def get_btn(idx, label_prefix):
        if 0 <= idx < len(sorted_words):
            target = sorted_words[idx]
            fname = f"{target['number']}-{target['word']}.html"
            return f'<a href="{fname}" class="nav-button">{label_prefix}</a>'
        return f'<span class="nav-button disabled">{label_prefix}</span>'

    prev_button = get_btn(current_index - 1, "← 前の単語")
    next_button = get_btn(current_index + 1, "次の単語 →")

    examples_html = ""
    for ex in data.get('examples', []):
        examples_html += f"""
        <div class="example-item">
            <span class="ex-text">{ex['text']}</span>
            <span class="ex-trans">{ex['translation']}</span>
            <span class="ex-source">― {ex.get('source', '出典不明')}</span>
        </div>"""

    conj_html = f'<span class="conj-tag">{data["conjugation"]}</span>' if 'conjugation' in data else ""

    def list_to_text(items):
        if not items:
            return "なし"
        html_list = []
        for i in items:
            html_list.append(f'<div class="related-entry">・<strong>{i["word"]}</strong>（{i["trans"]}）</div>')
        return "".join(html_list)

    return HTML_TEMPLATE_KOBUN.format(
        number=data['number'],
        word=data['word'],
        pos=data['pos'],
        conj_html=conj_html,
        meaning=data['meaning'],
        nuance=data['nuance'],
        examples_html=examples_html,
        related=list_to_text(data.get('related', [])),
        prev_button=prev_button,
        next_button=next_button
    )

def main():
    all_words = load_all_vocabulary_files()
    if not all_words: 
        return

    sorted_words = sorted(all_words, key=lambda w: float(str(w['number']).replace('-', '.')))
    
    output_dir = Path('classical_japanese_dictionary/data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for index, word_data in enumerate(sorted_words):
        html_content = generate_html(word_data, index, sorted_words)
        filename = f"{word_data['number']}-{word_data['word']}.html"
        with open(output_dir / filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ {filename} を生成しました。")

if __name__ == '__main__':
    main()
