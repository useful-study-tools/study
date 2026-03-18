import json
import re
from pathlib import Path
from glob import glob
from config import CHAPTER_MAP

# ==========================================
# 1. HTMLテンプレート
# ==========================================
HTML_TEMPLATE_MAIN = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{number} {word}</title>
    <link rel="icon" href="/study/favicon.png" type="image/png">
    <link rel="apple-touch-icon" href="/study/favicon.png">
</head>
<body>
    <a href="../index.html">一覧へ戻る</a>
    <div>
        {prev_button} | {next_button}
    </div>

    <h1>{word}（{era}）</h1>
    <p><strong>番号:</strong> {number}</p>

    <h2>用語解説</h2>
    <p class="description">{description}</p>

    <h2>背景</h2>
    <p>{background}</p>

    <h2>関連</h2>
    {related_events}

    <h2>場所</h2>
    <p>{location}</p>

    <h2>比較</h2>
    {comparisons}

    <h2>重要度</h2>
    <p>{importance}</p>

</body>
</html>"""

HTML_TEMPLATE_SUB = HTML_TEMPLATE_MAIN

# ==========================================
# 2. データ読み込み
# ==========================================
def load_all_history_files():
    base_dir = Path("japanese_history")
    json_files = glob(str(base_dir / "history_data*.json"))

    all_words = []

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_words.extend(data.get("words", []))
        except Exception as e:
            print(f"⚠ エラー: {json_file} → {e}")

    return all_words


# ==========================================
# 3. 補助関数
# ==========================================
def parse_number(number_str):
    parts = str(number_str).split("-")
    main = int(parts[0])
    sub = int(parts[1]) if len(parts) > 1 else 0
    return (main, sub)


def get_filename(word_data):
    safe_word = re.sub(r"[\\/:*?\"<>|]", "", word_data["word"])
    return f"{word_data['number']}-{safe_word}.html"


def get_source_label(number_str):
    try:
        main_val = int(str(number_str).split("-")[0])
        for key in sorted(CHAPTER_MAP.keys(), reverse=True):
            if main_val >= key:
                label = CHAPTER_MAP[key]
                match = re.search(r"【(.*?)】", label)
                return match.group(1) if match else label
        return "その他"
    except:
        return "不明"


def generate_history_link_list(target_items, all_words_data):
    word_map = {}
    for w in all_words_data:
        name = w["word"]
        word_map.setdefault(name, []).append(get_filename(w))

    html = ""
    for item in target_items:
        name = item["word"]
        note = item.get("note", "")

        if name in word_map:
            links = " ".join([f'<a href="{fn}">{name}</a>' for fn in word_map[name]])
        else:
            links = f"<strong>{name}</strong>"

        if note:
            links += f"（{note}）"

        html += f"<div>{links}</div>\n"

    return html or "なし"


# ==========================================
# 4. HTML生成
# ==========================================
def generate_html(data, index, words):
    template = HTML_TEMPLATE_SUB if "-" in str(data["number"]) else HTML_TEMPLATE_MAIN

    prev_btn = (
        f'<a href="{get_filename(words[index-1])}">←前</a>'
        if index > 0 else "←前"
    )

    next_btn = (
        f'<a href="{get_filename(words[index+1])}">次→</a>'
        if index < len(words) - 1 else "次→"
    )

    return template.format(
        number=data["number"],
        word=data["word"],
        era=data.get("era", ""),
        description=data.get("description", ""),
        background=data.get("background", ""),
        related_events=generate_history_link_list(data.get("related", []), words),
        location=data.get("location", ""),
        comparisons=generate_history_link_list(data.get("comparisons", []), words),
        importance=data.get("importance", ""),
        prev_button=prev_btn,
        next_button=next_btn
    )


# ==========================================
# 5. メイン処理
# ==========================================
def main():
    words = load_all_history_files()

    if not words:
        print("❌ JSONデータが見つかりません")
        return

    words = sorted(words, key=lambda w: parse_number(w["number"]))

    output_dir = Path("japanese_history/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📚 生成開始: {len(words)} 件")

    for i, word in enumerate(words):
        html = generate_html(word, i, words)
        filepath = output_dir / get_filename(word)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    print("✅ 完了: japanese_history/data に生成されました")


# ==========================================
if __name__ == "__main__":
    main()
