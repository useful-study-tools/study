import json
import os
import re
from pathlib import Path
from glob import glob
from collections import defaultdict

try:
    from config import CHAPTER_MAP, CHAPTER_WORD_COUNT
except ImportError:
    CHAPTER_MAP = {1: "【Basic】第1章", 500: "【Advanced】第2章"}
    CHAPTER_WORD_COUNT = {}


def get_json_file_list(base_path):
    json_pattern = str(base_path / "vocabulary_data*.json")
    files = glob(json_pattern)
    json_filenames = [os.path.basename(f) for f in files]

    def sort_key(name):
        if name == "vocabulary_data.json":
            return 0
        match = re.search(r"_(\d+)\.json", name)
        return int(match.group(1)) if match else 999

    return sorted(json_filenames, key=sort_key)


def generate_html():
    base_dir = Path("english_dictionary")
    output_file = base_dir / "exercise.html"

    grouped = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group_name = re.search(r"【(.*?)】", title).group(1) if "【" in title else "その他"
        display_label = title.split("】")[-1] if "】" in title else title
        grouped[group_name].append({"id": s_num, "label": display_label})

    chapters_js = json.dumps(dict(grouped), ensure_ascii=False)

    all_thresholds_js = json.dumps(
        sorted([ch["id"] for chs in grouped.values() for ch in chs])
    )

    word_count_js = json.dumps(CHAPTER_WORD_COUNT)
    json_files_js = json.dumps(get_json_file_list(base_dir))

    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>英単語演習</title>
<link rel="icon" href="../image/logo.png">

<style>
:root {{
--primary:#007bff;
--success:#28a745;
--danger:#dc3545;
--bg:#f4f7f9;
--text:#333;
}}

body {{
font-family:'Helvetica Neue',Arial,sans-serif;
background:var(--bg);
margin:0;
padding:20px;
color:var(--text);
display:flex;
flex-direction:column;
align-items:center;
}}

.container {{
width:100%;
max-width:800px;
}}

.header {{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:20px;
border-bottom:2px solid #eee;
padding-bottom:15px;
}}

h1 {{
margin:0;
font-size:1.5rem;
color:var(--primary);
}}

.setup-section,.quiz-section {{
display:none;
}}

.active {{
display:block;
}}
</style>
</head>

<body>

<div class="container">
<a href="index.html">英単語帳に戻る</a>

<div class="header">
<h1>単語演習</h1>
</div>

<div id="setup" class="setup-section active">
<button onclick="startExercise()">演習開始</button>
</div>

<div id="quiz" class="quiz-section">
<div id="quizContainer"></div>
</div>

</div>

<script>
const GROUPED_CHAPTERS={chapters_js};
const ALL_THRESHOLDS={all_thresholds_js};
const CHAPTER_WORD_COUNT={word_count_js};
const JSON_FILES={json_files_js};
const WORD_LIMIT=1000;

let ALL_WORDS=[];
let quizWords=[];
let currentIndex=0;

function startExercise(){{
alert("読み込み開始");
}}
</script>

</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"✓ {output_file} has been generated.")


if __name__ == "__main__":
    generate_html()
