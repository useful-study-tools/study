import json
import re
from pathlib import Path
from glob import glob
from config import CHAPTER_MAP

# ==========================================
# データ読み込み
# ==========================================
def load_all_history_files():
    base_dir = Path("japanese-history")  # ★ここ変更
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
# 補助関数
# ==========================================
def parse_number(number_str):
    parts = str(number_str).split("-")
    main = int(parts[0])
    sub = int(parts[1]) if len(parts) > 1 else 0
    return (main, sub)


def get_filename(word_data):
    safe_word = re.sub(r"[\\/:*?\"<>|]", "", word_data["word"])
    return f"{word_data['number']}-{safe_word}.html"


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
# HTML生成
# ==========================================
def generate_html(data, index, words):
    prev_btn = (
        f'<a href="{get_filename(words[index-1])}">←前</a>'
        if index > 0 else "←前"
    )

    next_btn = (
        f'<a href="{get_filename(words[index+1])}">次→</a>'
        if index < len(words) - 1 else "次→"
    )

    return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{data['word']}</title>
</head>
<body>

<a href="../index.html">一覧へ戻る</a>

<div>
{prev_btn} | {next_btn}
</div>

<h1>{data['word']}</h1>
<p>{data.get('description','')}</p>

</body>
</html>
"""


# ==========================================
# メイン処理
# ==========================================
def main():
    words = load_all_history_files()

    if not words:
        print("❌ JSONが見つからない")
        return

    words = sorted(words, key=lambda w: parse_number(w["number"]))

    output_dir = Path("japanese-history/data")  # ★ここ変更
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📚 {len(words)} 件生成")

    for i, word in enumerate(words):
        html = generate_html(word, i, words)
        filepath = output_dir / get_filename(word)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    print("✅ 完了: japanese-history/data に生成")


if __name__ == "__main__":
    main()
