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
    CHAPTER_MAP = {1: "【一段】動詞の基本", 100: "【二段】形容詞・形容動詞"}

def get_json_file_list(base_path):
    json_pattern = str(base_path / "vocabulary_data*.json")
    files = glob(json_pattern)
    json_filenames = [os.path.basename(f) for f in files]
    
    def sort_key(name):
        if name == 'vocabulary_data.json': return 0
        match = re.search(r'_(\d+)\.json', name)
        return int(match.group(1)) if match else 999
    
    return sorted(json_filenames, key=sort_key)

def generate_html():
    # パス設定: classical_japanese_dictionary フォルダを基準とする
    base_dir = Path("classical_japanese_dictionary")
    output_file = base_dir / "exercise.html"

    # チャプターをグループ化
    grouped = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group_match = re.search(r'【(.*?)】', title)
        group_name = group_match.group(1) if group_match else "その他"
        display_label = title.split('】')[-1] if '】' in title else title
        grouped[group_name].append({"id": s_num, "label": display_label})
    
    chapters_js = json.dumps(dict(grouped), ensure_ascii=False)
    json_files_js = json.dumps(get_json_file_list(base_dir))
    
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>古文単語演習</title>
    <style>
        :root {{ 
            --primary: #a33c3a; /* 茜色 */
            --success: #6a994e; /* 抹茶色 */
            --danger: #c94b4b; 
            --bg: #f8f4e6;      /* 生成り色 */
            --text: #333; 
        }}
        body {{ font-family: "Sawarabi Mincho", serif; background: var(--bg); margin: 0; padding: 20px; color: var(--text); display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; }}
        
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid var(--primary); padding-bottom: 10px; }}
        h1 {{ margin: 0; font-size: 1.5rem; color: var(--primary); }}
        
        .btn-home {{ text-decoration: none; color: white; background: #6c757d; padding: 8px 15px; border-radius: 5px; font-size: 0.85rem; }}

        .setup-section, .quiz-section {{ display: none; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        .active {{ display: block; }}
        
        .chapter-container {{ max-height: 250px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: #fff; margin-bottom: 15px; }}
        .chapter-group-title {{ font-weight: bold; color: var(--primary); border-left: 4px solid var(--primary); padding-left: 10px; margin: 15px 0 5px 0; }}
        
        .btn {{ background: var(--primary); color: white; border: none; padding: 15px; border-radius: 5px; cursor: pointer; width: 100%; font-size: 1.1rem; font-weight: bold; margin-top: 10px; }}
        
        .card {{ border: 2px solid var(--primary); padding: 40px 20px; border-radius: 10px; text-align: center; font-size: 2.2rem; font-weight: bold; background: white; margin-bottom: 20px; cursor: pointer; }}
        .card.flipped {{ border-color: var(--success); color: var(--success); }}
        
        .option-btn {{ background: white; border: 1px solid #ddd; padding: 15px; border-radius: 5px; cursor: pointer; font-size: 1rem; text-align: left; transition: 0.2s; margin-bottom: 10px; width: 100%; }}
        .option-btn:hover {{ border-color: var(--primary); background: #fffcfc; }}

        .nav-buttons {{ display: flex; gap: 10px; margin-top: 10px; }}
        .btn-prev {{ background: #6c757d; flex: 1; }}
        .btn-next {{ background: var(--primary); flex: 2; }}
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>古文単語演習</h1>
        <a href="index.html" class="btn-home">辞書に戻る</a>
    </div>

    <div id="loadingStatus" style="text-align:center; padding: 40px;">データを読み込んでいます...</div>

    <div id="setup" class="setup-section">
        <label style="font-weight:bold;">1. 出題範囲を選択</label>
        <div class="chapter-container" id="chapterList"></div>

        <div style="margin: 20px 0;">
            <label style="font-weight:bold;">2. 出題設定</label><br>
            <label><input type="radio" name="orderType" value="random" checked> ランダム</label>
            <label style="margin-left:15px;"><input type="radio" name="orderType" value="sequential"> 番号順</label>
            <label style="margin-left:15px; color: var(--primary);"><input type="checkbox" id="basicOnly"> 基本語のみ</label>
        </div>

        <div style="margin-bottom: 20px;">
            <label style="font-weight:bold;">3. 演習モード</label>
            <select id="mode" style="width:100%; padding:10px; margin-top:5px;">
                <option value="card-ko-ja">暗記カード (古文 → 現代語)</option>
                <option value="card-ja-ko">暗記カード (現代語 → 古文)</option>
                <option value="quiz-ko-ja">4択問題 (古文 → 現代語)</option>
                <option value="quiz-ja-ko">4択問題 (現代語 → 古文)</option>
            </select>
        </div>

        <button id="startBtn" class="btn" onclick="startExercise()" disabled>準備中...</button>
    </div>

    <div id="quiz" class="quiz-section">
        <div id="progressText" style="text-align:center; color:#888; margin-bottom:10px;"></div>
        <div id="quizContainer"></div>
        <div id="cardControls" class="nav-buttons" style="display:none;">
            <button id="prevBtn" class="btn btn-prev">← 前へ</button>
            <button id="mainActionBtn" class="btn btn-next"></button>
        </div>
        <button id="quizNextBtn" class="btn" style="display:none;"></button>
        <button class="btn" style="background:#6c757d; margin-top:20px;" onclick="location.reload()">設定に戻る</button>
    </div>
</div>

<script>
const GROUPED_CHAPTERS = {chapters_js}; 
const JSON_FILES = {json_files_js};
let ALL_WORDS = [];

async function loadAllData() {{
    try {{
        const results = await Promise.all(JSON_FILES.map(file => fetch(file).then(r => r.json())));
        results.forEach(data => {{
            if (data.words) {{
                data.words.forEach(w => {{
                    ALL_WORDS.push({{ 
                        n: String(w.number), 
                        w: w.word, 
                        m: w.meaning,
                        examples: w.examples || []
                    }});
                }});
            }}
        }});
        document.getElementById('loadingStatus').style.display = 'none';
        document.getElementById('setup').classList.add('active');
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').innerText = '演習開始！';
    }} catch (e) {{ 
        document.getElementById('loadingStatus').innerText = "エラー：読み込み失敗";
    }}
}}

// チャプターリスト構築
const chapterListDiv = document.getElementById('chapterList');
for (const [group, chapters] of Object.entries(GROUPED_CHAPTERS)) {{
    const title = document.createElement('div');
    title.className = 'chapter-group-title';
    title.innerText = group;
    chapterListDiv.appendChild(title);
    chapters.forEach(ch => {{
        const label = document.createElement('label');
        label.style.display = 'block';
        label.innerHTML = `<input type="checkbox" name="chapters" value="${{ch.id}}"> ${{ch.label}}`;
        chapterListDiv.appendChild(label);
    }});
}}

let quizWords = [];
let currentIndex = 0;

function startExercise() {{
    const selected = Array.from(document.querySelectorAll('input[name="chapters"]:checked')).map(cb => parseInt(cb.value));
    if(selected.length === 0) {{ alert("範囲を選択してください"); return; }}

    const basicOnly = document.getElementById('basicOnly').checked;
    let thresholds = Object.values(GROUPED_CHAPTERS).flat().map(ch => parseInt(ch.id)).sort((a,b)=>a-b);

    quizWords = ALL_WORDS.filter(w => {{
        if (basicOnly && w.n.includes('-')) return false;
        const n = parseInt(w.n.split('-')[0]);
        const chapterId = thresholds.slice().reverse().find(t => n >= t);
        return selected.includes(chapterId);
    }});

    if(document.querySelector('input[name="orderType"]:checked').value === 'random') {{
        quizWords.sort(() => Math.random() - 0.5);
    }}

    currentIndex = 0;
    document.getElementById('setup').classList.remove('active');
    document.getElementById('quiz').classList.add('active');
    showQuestion();
}}

function showQuestion() {{
    const word = quizWords[currentIndex];
    const mode = document.getElementById('mode').value;
    const container = document.getElementById('quizContainer');
    const cardControls = document.getElementById('cardControls');
    const quizNextBtn = document.getElementById('quizNextBtn');
    
    document.getElementById('progressText').innerText = `第 ${{currentIndex + 1}} 問 / ${{quizWords.length}} (No.${{word.n}})`;
    container.innerHTML = '';
    cardControls.style.display = 'none';
    quizNextBtn.style.display = 'none';

    if(mode.startsWith('card')) {{
        showCard(word, mode);
    }} else {{
        showQuiz(word, mode);
    }}
}}

function showCard(word, mode) {{
    const container = document.getElementById('quizContainer');
    const cardControls = document.getElementById('cardControls');
    const mainBtn = document.getElementById('mainActionBtn');
    const prevBtn = document.getElementById('prevBtn');
    
    let isFlipped = false;
    container.innerHTML = `<div id="card" class="card">${{mode === 'card-ko-ja' ? word.w : word.m}}</div>`;
    
    cardControls.style.display = 'flex';
    mainBtn.innerText = '答えを見る';
    prevBtn.style.visibility = currentIndex > 0 ? 'visible' : 'hidden';

    const card = document.getElementById('card');
    
    const flipAction = () => {{
        if(!isFlipped) {{
            card.innerText = mode === 'card-ko-ja' ? word.m : word.w;
            card.classList.add('flipped');
            isFlipped = true;
            mainBtn.innerText = '次の単語へ';
        }} else {{
            currentIndex++; checkEnd();
        }}
    }};

    card.onclick = flipAction;
    mainBtn.onclick = flipAction;
    prevBtn.onclick = () => {{ if(currentIndex > 0) {{ currentIndex--; showQuestion(); }} }};
}}

function showQuiz(word, mode) {{
    const container = document.getElementById('quizContainer');
    const questionText = mode === 'quiz-ko-ja' ? word.w : word.m;
    container.innerHTML = `<div class="card" style="font-size:1.8rem;">${{questionText}}</div><div id="options"></div>`;
    
    let choices = [word];
    while(choices.length < 4) {{
        const r = ALL_WORDS[Math.floor(Math.random() * ALL_WORDS.length)];
        if(!choices.find(o => o.n === r.n)) choices.push(r);
    }}
    choices.sort(() => Math.random() - 0.5);
    
    choices.forEach(opt => {{
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.innerText = mode === 'quiz-ko-ja' ? opt.m : opt.w;
        btn.onclick = () => {{
            if(opt.n === word.n) {{
                btn.style.background = '#e8f5e9';
                btn.style.borderColor = 'var(--success)';
                setTimeout(() => {{ currentIndex++; checkEnd(); }}, 400);
            }} else {{
                btn.style.background = '#ffebee';
                btn.style.borderColor = 'var(--danger)';
                btn.disabled = true;
            }}
        }};
        document.getElementById('options').appendChild(btn);
    }});
}}

function checkEnd() {{ if(currentIndex < quizWords.length) showQuestion(); else {{ alert("終了しました！"); location.reload(); }} }}

loadAllData();
</script>
</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✓ 古文単語演習を生成: {output_file}")

if __name__ == "__main__":
    generate_html()
