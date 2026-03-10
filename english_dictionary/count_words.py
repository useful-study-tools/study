“””
update_chapter_word_count.py
実行すると english_dictionary/ 内の全JSONを走査し、
config.py の末尾に CHAPTER_WORD_COUNT = {…} を追記または上書きする。
“””

import json
import re
from pathlib import Path
from glob import glob
from collections import defaultdict

# ── パス設定 ──────────────────────────────────────────

BASE_DIR = Path(“english_dictionary”)   # JSONが入っているフォルダ
CONFIG_PATH = Path(“config.py”)         # 編集対象

# ──────────────────────────────────────────────────────

def main():
# 1. config.py から CHAPTER_MAP を読み込む
try:
import importlib.util, sys
spec = importlib.util.spec_from_file_location(“config”, CONFIG_PATH)
cfg  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)
CHAPTER_MAP = cfg.CHAPTER_MAP
except Exception as e:
print(f”[ERROR] config.py の読み込みに失敗しました: {e}”)
return

```
thresholds = sorted(CHAPTER_MAP.keys())

# 2. 全JSONを走査して各チャプターの語数をカウント
counts = defaultdict(int)
json_files = glob(str(BASE_DIR / "vocabulary_data*.json"))

if not json_files:
    print(f"[ERROR] {BASE_DIR}/ に vocabulary_data*.json が見つかりません")
    return

for filepath in sorted(json_files):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for w in data.get("words", []):
        n_str = str(w["number"])
        base_n = int(n_str.split("-")[0])
        chapter_id = None
        for t in reversed(thresholds):
            if base_n >= t:
                chapter_id = t
                break
        if chapter_id is not None:
            counts[chapter_id] += 1

total = sum(counts.values())
print(f"[INFO] 総単語数: {total} 語 / {len(json_files)} ファイル")

# 3. 新しい CHAPTER_WORD_COUNT ブロックを生成
lines = ["CHAPTER_WORD_COUNT = {\n"]
for ch_id in thresholds:
    label = CHAPTER_MAP[ch_id]
    c = counts.get(ch_id, 0)
    lines.append(f"    {ch_id}: {c},  # {label}\n")
lines.append("}\n")
new_block = "".join(lines)

# 4. config.py を読み込み、既存ブロックがあれば置換、なければ末尾に追記
original = CONFIG_PATH.read_text(encoding="utf-8")

pattern = re.compile(
    r"^CHAPTER_WORD_COUNT\s*=\s*\{.*?^\}\s*$",
    re.MULTILINE | re.DOTALL
)

if pattern.search(original):
    updated = pattern.sub(new_block.rstrip("\n"), original)
    action = "上書き"
else:
    sep = "\n" if original.endswith("\n") else "\n\n"
    updated = original + sep + new_block
    action = "追記"

CONFIG_PATH.write_text(updated, encoding="utf-8")
print(f"[OK] config.py に CHAPTER_WORD_COUNT を{action}しました。")
print(f"     チャプター数: {len(thresholds)}")
```

if **name** == “**main**”:
main()
