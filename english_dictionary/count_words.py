import json
import os
from pathlib import Path
from glob import glob
from collections import defaultdict

# パス設定
BASE_DIR = Path("english_dictionary")
CONFIG_PATH = Path("config.py")

def update_config():
    # 1. CHAPTER_MAPの読み込み
    import config
    import importlib
    importlib.reload(config)
    chapter_map = config.CHAPTER_MAP
    thresholds = sorted(chapter_map.keys())

    # 2. カウント処理
    counts = defaultdict(int)
    json_files = glob(str(BASE_DIR / "vocabulary_data*.json"))
    
    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for w in data.get("words", []):
            base_n = int(str(w["number"]).split("-")[0])
            chapter_id = next((t for t in reversed(thresholds) if base_n >= t), None)
            if chapter_id is not None:
                counts[chapter_id] += 1

    # 3. ファイルの書き出し
    # CHAPTER_MAPの部分はそのまま残し、WORD_COUNTだけ新しく作る
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # CHAPTER_WORD_COUNT より前の行だけ抽出
    new_lines = []
    for line in lines:
        if "CHAPTER_WORD_COUNT =" in line:
            break
        new_lines.append(line)

    # 末尾に新しいデータを追記
    if not new_lines[-1].strip() == "": new_lines.append("\n")
    new_lines.append("CHAPTER_WORD_COUNT = {\n")
    for ch_id in thresholds:
        c = counts.get(ch_id, 0)
        label = chapter_map[ch_id]
        new_lines.append(f"    {ch_id}: {c},  # {label}\n")
    new_lines.append("}\n")

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("✓ config.py has been updated with word counts.")

if __name__ == "__main__":
    update_config()
