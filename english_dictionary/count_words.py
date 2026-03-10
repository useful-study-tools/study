# count_words.py
# これを一度だけ実行して、CHAPTER_WORD_COUNT の内容を出力する

import json
from pathlib import Path
from glob import glob
from collections import defaultdict
import re

try:
    from config import CHAPTER_MAP
except ImportError:
    print("config.pyが見つかりません")
    exit()

base_dir = Path("english_dictionary")
thresholds = sorted(CHAPTER_MAP.keys())

counts = defaultdict(int)

for filepath in glob(str(base_dir / "vocabulary_data*.json")):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    for w in data.get("words", []):
        n_str = str(w["number"])
        base_n = int(n_str.split("-")[0])
        # どのチャプターに属するか判定
        chapter_id = None
        for t in reversed(thresholds):
            if base_n >= t:
                chapter_id = t
                break
        if chapter_id is not None:
            counts[chapter_id] += 1

# CHAPTER_WORD_COUNT として出力
print("CHAPTER_WORD_COUNT = {")
for ch_id in thresholds:
    print(f"    {ch_id}: {counts.get(ch_id, 0)},")
print("}")
