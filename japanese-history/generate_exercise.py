import json
import os
import re
from pathlib import Path
from glob import glob
from collections import defaultdict

# CHAPTER_MAPのインポート
try:
    from config import CHAPTER_MAP
except ImportError:
    CHAPTER_MAP = {1: "【原始】第1章", 1000: "【中世】第2章"}

def get_json_file_mapping(base_path):
    """各JSONファイルがどのチャプターIDをカバーしているかのマッピングを作成"""
    json_pattern = str(base_path / "history_data*.json")
    files = glob(json_pattern)
    
    mapping = {}
    for f in files:
        name = os.path.basename(f)
        if name == 'history_data.json':
            mapping[1] = name
        else:
            match = re.search(r'_(\d+)\.json', name)
            if match:
                mapping[int(match.group(1))] = name
    return mapping

def generate_html():
    base_dir = Path("japanese-history")
    output_file = base_dir / "exercise.html"

    # チャプターをグループ化
    grouped = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group_name = re.search(r'【(.*?)】', title).group(1) if '【' in title else "その他"
        display_label = title.split('】')[-1] if '】' in title else title
        grouped[group_name].append({"id": s_num, "label": display_label})
    
    chapters_js = json.dumps(dict(grouped), ensure_ascii=False)
    file_mapping_js = json.dumps(get_json_file_mapping(base_dir))
    
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日本史用語演習</title>
    <style>
        :root {{ --primary: #8b0000; --success: #28a745; --danger: #dc3545; --bg: #fdfaf5; --text: #2c2c2c; }}
        body {{ font-family: "Hiragino Mincho ProN", serif; background: var(--bg); margin: 0; padding: 20px; color: var(--text); display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; }}
        
        .header {{ border-bottom: 2px solid var(--primary); padding-bottom: 10px; margin-bottom: 20px; }}
        h1 {{ margin: 0; font-size: 1.8rem; color: var(--primary); }}

        .setup-section, .quiz-section {{ display: none; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .active {{ display: block; }}
        
        .chapter-container {{ max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 12px; border-radius: 4px; background: #fff; margin-bottom: 15px; }}
        .chapter-group-title {{ font-size: 0.9rem; font-weight: bold; background: #f0f0f0; padding: 5px 10px; margin: 10px 0; border-left: 5px solid var(--primary); }}
        .chapter-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 8px; }}
        
        .btn {{ background: var(--primary); color: white; border: none; padding: 15px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 1.1rem; font-weight: bold; transition: 0.2s; }}
        .btn:hover {{ opacity: 0.8; }}
        
        /* 演習カード */
        .card {{ border: 3px double var(--primary); padding: 40px 20px; border-radius: 8px; text-align: center; min-height: 120px; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: bold; background: #fff; cursor: pointer; }}
        .card.flipped {{ border-color: #d4a373; color: #b22222; }}
        
        .fill-blank-area {{ background: #fff9f0; padding: 30px; border: 1px solid #e0d5c1; border-radius: 4px; line-height: 2; font-size: 1.2rem; }}
        .blank-input {{ border: none; border-bottom: 2px solid var(--primary); outline: none; background: transparent; font-size: 1.2rem; text-align: center; color: var(--primary); width: 180px; font-family: inherit; }}
        
        .btn-home {{ text-decoration: none; color: #666; font-size: 0.9rem; margin-bottom: 20px; display: inline-block; }}
    </style>
</head>
<body>

<div class="container">
    <a href="index.html" class="btn-home">← 用語帳に戻る</a>
    <div class="header"><h1>日本史 知識定着演習</h1></div>

    <div id="setup" class="setup-section active">
        <label><b>1. 時代・範囲を選択</b></label>
        <div class="chapter-container" id="chapterList"></div>

        <label><b>2. 演習モード</b></label>
        <select id="mode" style="width:100%; padding:12px; margin: 15px 0; font-size:1rem;">
            <option value="card-term-desc">一問一答 (用語 → 解説)</option>
            <option value="card-desc-term">一問一答 (解説 → 用語)</option>
            <option value="quiz-desc-term">4択問題 (解説から用語を選ぶ)</option>
            <option value="fill-blank">背景・史料 穴埋め入力</option>
        </select>

        <button id="startBtn" class="btn" onclick="startExercise()">演習開始</button>
    </div>

    <div id="quiz" class="quiz-section">
        <div class="progress" id="progressText" style="text-align:right; color:#888; margin-bottom:10px;"></div>
        <div id="quizContainer"></div>
        <button id="mainActionBtn" class="btn" style="display:none; margin-top:20px;"></button>
        <button class="btn" style="background:#6c757d; margin-top:10px;" onclick="location.reload()">終了・戻る</button>
    </div>
</div>

<script>
const GROUPED_CHAPTERS = {chapters_js}; 
const FILE_MAPPING = {file_mapping_js};
let quizWords = [];
let currentIndex = 0;
let isFlipped = false;

// 初期化（チャプターリスト作成）
const listDiv = document.getElementById('chapterList');
for (const [group, chapters] of Object.entries(GROUPED_CHAPTERS)) {{
    const title = document.createElement('div');
    title.className = 'chapter-group-title';
    title.innerText = group;
    listDiv.appendChild(title);
    
    const grid = document.createElement('div');
    grid.className = 'chapter-grid';
    chapters.forEach(ch => {{
        grid.innerHTML += `<label class="chapter-item"><input type="checkbox" name="chapters" value="${{ch.id}}"> ${{ch.label}}</label>`;
    }});
    listDiv.appendChild(grid);
}}

async function startExercise() {{
    const selectedIds = Array.from(document.querySelectorAll('input[name="chapters"]:checked')).map(cb => parseInt(cb.value));
    if(selectedIds.length === 0) return alert("範囲を選択してください");

    const filesToFetch = new Set();
    selectedIds.forEach(id => {{ if(FILE_MAPPING[id]) filesToFetch.add(FILE_MAPPING[id]); }});

    try {{
        const results = await Promise.all(Array.from(filesToFetch).map(file => fetch(file).then(r => r.json())));
        let loaded = [];
        results.forEach(data => {{
            data.words.forEach(w => {{
                loaded.push({{ n: w.number, w: w.word, d: w.description, bg: w.background }});
            }});
        }});

        // 範囲フィルタリング
        const allT = Object.values(GROUPED_CHAPTERS).flat().map(c => c.id).sort((a,b)=>a-b);
        quizWords = loaded.filter(w => {{
            const num = parseInt(w.n.split('-')[0]);
            const cId = allT.slice().reverse().find(t => num >= t);
            return selectedIds.includes(cId);
        }}).sort(() => Math.random() - 0.5);

        document.getElementById('setup').classList.remove('active');
        document.getElementById('quiz').classList.add('active');
        showQuestion();
    }} catch(e) {{ alert("読込失敗"); }}
}}

function showQuestion() {{
    const item = quizWords[currentIndex];
    const mode = document.getElementById('mode').value;
    const container = document.getElementById('quizContainer');
    const mainBtn = document.getElementById('mainActionBtn');
    
    document.getElementById('progressText').innerText = `${{currentIndex + 1}} / ${{quizWords.length}}`;
    container.innerHTML = '';
    mainBtn.style.display = 'none';

    if(mode === 'fill-blank') {{
        // 背景文から用語（w）を隠す
        const text = item.bg || item.d;
        const parts = text.split(new RegExp(`(${{item.w}})`, 'g'));
        container.innerHTML = '<div class="fill-blank-area" id="fillArea"></div><div id="feedback" style="margin-top:15px; font-weight:bold;"></div>';
        const area = document.getElementById('fillArea');
        parts.forEach(p => {{
            if(p === item.w) {{
                area.innerHTML += `<input type="text" class="blank-input" id="ansInp" autocomplete="off">`;
            }} else {{
                area.appendChild(document.createTextNode(p));
            }}
        }});
        mainBtn.innerText = "判定";
        mainBtn.style.display = "block";
        mainBtn.onclick = () => {{
            const user = document.getElementById('ansInp').value;
            const f = document.getElementById('feedback');
            if(user === item.w) {{ f.innerText = "◎ 正解！"; f.style.color="green"; }}
            else {{ f.innerText = "× 正解は: " + item.w; f.style.color="red"; }}
            mainBtn.innerText = "次へ";
            mainBtn.onclick = () => {{ currentIndex++; checkEnd(); }};
        }};
    }} else if(mode.startsWith('card')) {{
        isFlipped = false;
        const front = mode === 'card-term-desc' ? item.w : item.d;
        container.innerHTML = `<div class="card" id="card" onclick="flip()">${{front}}</div>`;
    }} else {{
        // 4択
        container.innerHTML = `<div class="card" style="font-size:1.2rem; cursor:default; margin-bottom:15px;">${{item.d}}</div><div id="opts" style="display:grid; gap:10px;"></div>`;
        let choices = [item];
        while(choices.length < 4 && quizWords.length >= 4) {{
            const r = quizWords[Math.floor(Math.random()*quizWords.length)];
            if(!choices.find(c => c.n === r.n)) choices.push(r);
        }}
        choices.sort(()=>Math.random()-0.5).forEach(c => {{
            const b = document.createElement('button');
            b.className = 'btn'; b.style.background="white"; b.style.color="var(--primary)"; b.style.border="1px solid var(--primary)";
            b.innerText = c.w;
            b.onclick = () => {{
                if(c.n === item.n) {{ b.style.background="#d4edda"; setTimeout(()=>{{currentIndex++; checkEnd();}}, 600); }}
                else b.style.background="#f8d7da";
            }};
            document.getElementById('opts').appendChild(b);
        }});
    }}
}}

function flip() {{
    const item = quizWords[currentIndex];
    const mode = document.getElementById('mode').value;
    const card = document.getElementById('card');
    if(!isFlipped) {{
        card.innerText = mode === 'card-term-desc' ? item.d : item.w;
        card.classList.add('flipped');
        isFlipped = true;
    }} else {{ currentIndex++; checkEnd(); }}
}}

function checkEnd() {{ if(currentIndex < quizWords.length) showQuestion(); else {{ alert("終了！"); location.reload(); }} }}
</script>
</body>
</html>"""

    # 修正ポイント：ディレクトリ名を除去して、カレントディレクトリに保存するようにする
    output_file = "exercise.html"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✓ {output_file} (Japanese History Edition) generated.")

if __name__ == "__main__":
    generate_html()

