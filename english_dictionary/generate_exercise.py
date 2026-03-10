import json
import os
import re
from pathlib import Path
from glob import glob
from collections import defaultdict

try:
from config import CHAPTER_MAP, CHAPTER_WORD_COUNT
except ImportError:
CHAPTER_MAP = {1: “【Basic】第1章”, 500: “【Advanced】第2章”}
CHAPTER_WORD_COUNT = {}

def get_json_file_list(base_path):
json_pattern = str(base_path / “vocabulary_data*.json”)
files = glob(json_pattern)
json_filenames = [os.path.basename(f) for f in files]
def sort_key(name):
if name == ‘vocabulary_data.json’: return 0
match = re.search(r’_(\d+).json’, name)
return int(match.group(1)) if match else 999
return sorted(json_filenames, key=sort_key)

def generate_html():
base_dir = Path(“english_dictionary”)
output_file = base_dir / “exercise.html”

```
grouped = defaultdict(list)
for s_num, title in sorted(CHAPTER_MAP.items()):
    group_name = re.search(r'【(.*?)】', title).group(1) if '【' in title else "その他"
    display_label = title.split('】')[-1] if '】' in title else title
    grouped[group_name].append({"id": s_num, "label": display_label})

chapters_js = json.dumps(dict(grouped), ensure_ascii=False)

all_thresholds_js = json.dumps(
    sorted([ch["id"] for chs in grouped.values() for ch in chs])
)

# CHAPTER_WORD_COUNT を JS に埋め込む（語数バッジのリアルタイム表示用）
word_count_js = json.dumps(CHAPTER_WORD_COUNT)

# JSONファイル名リストのみ埋め込む（build_file_index は不要）
json_files_js = json.dumps(get_json_file_list(base_dir))

html_template = f"""<!DOCTYPE html>
```

<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英単語演習</title>
    <link rel="icon" href="../image/logo.png">
    <style>
        :root {{ --primary: #007bff; --success: #28a745; --danger: #dc3545; --bg: #f4f7f9; --text: #333; }}
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: var(--bg); margin: 0; padding: 20px; color: var(--text); display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; }}

```
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
    h1 {{ margin: 0; font-size: 1.5rem; color: var(--primary); }}

    .setup-section, .quiz-section {{ display: none; }}
    .active {{ display: block; }}
    
    .chapter-container {{ max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 12px; border-radius: 8px; background: #fafafa; margin-bottom: 10px; }}
    .chapter-group-title {{ font-size: 0.85rem; font-weight: bold; color: #555; background: #e9ecef; padding: 6px 12px; margin: 12px 0 6px 0; border-radius: 4px; border-left: 4px solid var(--primary); }}
    .chapter-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 6px; padding: 0 5px; }}
    .chapter-item {{ font-size: 0.85rem; display: flex; align-items: center; cursor: pointer; }}
    .chapter-item input {{ margin-right: 10px; }}
    
    .option-group {{ margin-bottom: 25px; }}
    label.group-label {{ display: block; font-weight: bold; margin-bottom: 10px; font-size: 1rem; color: #444; }}
    
    .word-count-badge {{
        display: inline-block; margin-left: 10px; padding: 3px 10px;
        background: #e9ecef; border-radius: 20px; font-size: 0.85rem; color: #555;
        font-weight: bold; transition: 0.2s;
    }}
    .word-count-badge.over {{ background: #f8d7da; color: var(--danger); }}
    .word-count-badge.ok {{ background: #d4edda; color: var(--success); }}

    .error-msg {{
        display: none; background: #f8d7da; color: var(--danger);
        border: 1px solid #f5c6cb; border-radius: 8px;
        padding: 12px 16px; margin-bottom: 12px; font-weight: bold; font-size: 0.95rem;
    }}

    .btn {{ background: var(--primary); color: white; border: none; padding: 14px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-size: 1rem; font-weight: bold; transition: 0.3s; margin-top: 10px; }}
    .btn:hover:not(:disabled) {{ opacity: 0.9; transform: translateY(-1px); }}
    .btn:disabled {{ background: #ccc; cursor: not-allowed; transform: none; }}
    
    .progress {{ font-size: 0.9rem; color: #777; margin-bottom: 15px; text-align: center; background: #eee; padding: 5px; border-radius: 20px; }}
    .card {{ border: 2px solid var(--primary); padding: 50px 20px; border-radius: 15px; text-align: center; min-height: 140px; display: flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: bold; background: white; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 12px rgba(0,123,255,0.1); }}
    .card.flipped {{ border-color: var(--success); color: var(--success); box-shadow: 0 4px 12px rgba(40,167,69,0.1); }}
    
    .nav-controls {{ display: flex; justify-content: space-between; gap: 12px; margin-top: 20px; }}
    .nav-btn {{ flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 8px; cursor: pointer; background: #fff; font-weight: bold; transition: 0.2s; }}
    .nav-btn:hover:not(:disabled) {{ background: #f0f0f0; }}
    .nav-btn:disabled {{ opacity: 0.3; cursor: not-allowed; }}

    .options-grid {{ display: grid; grid-template-columns: 1fr; gap: 10px; margin-top: 20px; }}
    .option-btn {{ background: white; border: 2px solid #eee; padding: 16px; border-radius: 10px; cursor: pointer; font-size: 1.1rem; text-align: left; transition: 0.2s; }}
    .option-btn:hover {{ border-color: var(--primary); background: #f8fbff; }}

    .fill-blank-area {{ text-align: left; background: #fff; padding: 25px; border-radius: 12px; margin: 20px 0; border: 2px solid #eee; }}
    .sentence-ja {{ font-size: 0.95rem; color: #666; margin-bottom: 15px; border-left: 3px solid #ccc; padding-left: 10px; }}
    .sentence-en {{ font-size: 1.3rem; font-weight: 500; line-height: 1.8; }}
    .blank-input {{ border: none; border-bottom: 2px solid var(--primary); outline: none; background: transparent; font-size: 1.3rem; text-align: center; color: var(--primary); width: 160px; padding: 0 5px; font-family: inherit; }}
    .blank-input.correct {{ color: var(--success); border-color: var(--success); }}
    .blank-input.wrong {{ color: var(--danger); border-color: var(--danger); }}
    .feedback {{ margin-top: 15px; font-weight: bold; font-size: 1.1rem; min-height: 1.5em; text-align: center; }}
    .btn-home {{ display: inline-block; margin-bottom: 20px; padding: 8px 18px; background-color: #6c757d; color: white !important; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 0.85rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.3s; }}
    .btn-home:hover {{ background-color: #5a6268; transform: translateY(-1px); }}

    .loading-overlay {{
        display: none; position: fixed; inset: 0;
        background: rgba(255,255,255,0.85); z-index: 999;
        flex-direction: column; align-items: center; justify-content: center;
        font-size: 1.1rem; color: var(--primary); font-weight: bold; gap: 16px;
    }}
    .loading-overlay.active {{ display: flex; }}
    .spinner {{
        width: 40px; height: 40px; border: 4px solid #cce5ff;
        border-top-color: var(--primary); border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>
```

</head>
<body>

<div class="loading-overlay" id="loadingOverlay">
    <div class="spinner"></div>
    <div id="loadingMsg">データを読み込んでいます...</div>
</div>

<div class="container">
    <a href="index.html" class="btn-home">英単語帳に戻る</a>
    <div class="header">
        <h1>単語演習</h1>
    </div>

```
<div id="setup" class="setup-section active">
    <div class="option-group">
        <label class="group-label">
            1. 出題範囲を選択
            <span class="word-count-badge" id="wordCountBadge">0語選択中</span>
        </label>
        <div class="chapter-container" id="chapterList"></div>
    </div>

    <div class="option-group">
        <label class="group-label">2. 出題順序</label>
        <label style="margin-right:20px; cursor:pointer;"><input type="radio" name="orderType" value="random" checked> ランダム</label>
        <label style="cursor:pointer;"><input type="radio" name="orderType" value="sequential"> 番号順</label>
        <label style="cursor:pointer; color: var(--danger); font-weight: bold; margin-left:20px;">
            <input type="checkbox" id="basicOnly"> 基本語のみ出題
        </label>
    </div>

    <div class="option-group">
        <label class="group-label">3. 演習モード</label>
        <select id="mode" style="width:100%; padding:12px; border-radius:8px; border:1px solid #ccc; font-size:1rem;">
            <option value="card-en-ja">暗記カード (英 → 日)</option>
            <option value="card-ja-en">暗記カード (日 → 英)</option>
            <option value="quiz-en-ja">4択問題 (英 → 日)</option>
            <option value="quiz-ja-en">4択問題 (日 → 英)</option>
            <option value="fill-blank">例文穴埋め (スペリング入力)</option>
        </select>
    </div>

    <div class="error-msg" id="errorMsg"></div>
    <button id="startBtn" class="btn" onclick="startExercise()">演習開始！</button>
</div>

<div id="quiz" class="quiz-section">
    <div class="progress" id="progressText">STEP: 0 / 0</div>
    <div id="quizContainer"></div>
    <button id="mainActionBtn" class="btn" style="display:none;"></button>
    <div style="display:flex; gap:10px; margin-top:20px;">
        <button class="btn" style="background:#6c757d; flex:1;" onclick="location.reload()">演習をやり直す</button>
    </div>
</div>
```

</div>

<script>
const GROUPED_CHAPTERS   = {chapters_js};
const ALL_THRESHOLDS     = {all_thresholds_js};
// CHAPTER_WORD_COUNT: {{ "chapterId": 語数 }}  ※JSONキーは文字列
const CHAPTER_WORD_COUNT = {word_count_js};
const JSON_FILES         = {json_files_js};
const WORD_LIMIT         = 1000;

let ALL_WORDS    = [];
let quizWords    = [];
let currentIndex = 0;
let isFlipped    = false;

// チャプターIDから単語番号の範囲を返す
function getChapterRange(chapterId) {{
    const idx = ALL_THRESHOLDS.indexOf(chapterId);
    const min = chapterId;
    const max = (idx + 1 < ALL_THRESHOLDS.length) ? ALL_THRESHOLDS[idx + 1] - 1 : Infinity;
    return {{ min, max }};
}}

// 選択チャプターの合計語数を CHAPTER_WORD_COUNT から即座に計算
function calcSelectedCount(selectedIds) {{
    return selectedIds.reduce((sum, id) => sum + (CHAPTER_WORD_COUNT[String(id)] || 0), 0);
}}

// 語数バッジをリアルタイム更新
function updateWordCountBadge() {{
    const selected = Array.from(document.querySelectorAll('input[name="chapters"]:checked'))
                         .map(cb => parseInt(cb.value));
    const badge    = document.getElementById('wordCountBadge');
    const errorMsg = document.getElementById('errorMsg');

    if (selected.length === 0) {{
        badge.textContent = '0語選択中';
        badge.className   = 'word-count-badge';
        errorMsg.style.display = 'none';
        document.getElementById('startBtn').disabled = false;
        return;
    }}

    const count = calcSelectedCount(selected);
    badge.textContent = `${{count}}語選択中`;

    if (count > WORD_LIMIT) {{
        badge.className = 'word-count-badge over';
        errorMsg.textContent = `⚠️ 選択範囲が ${{count}} 語あります。1000語以下になるようチャプター数を減らしてください。`;
        errorMsg.style.display = 'block';
        document.getElementById('startBtn').disabled = true;
    }} else {{
        badge.className = 'word-count-badge ok';
        errorMsg.style.display = 'none';
        document.getElementById('startBtn').disabled = false;
    }}
}}

// チャプター選択UIの構築
const chapterListDiv = document.getElementById('chapterList');
for (const [group, chapters] of Object.entries(GROUPED_CHAPTERS)) {{
    const groupTitle = document.createElement('div');
    groupTitle.className = 'chapter-group-title';
    groupTitle.innerText = group;
    chapterListDiv.appendChild(groupTitle);

    const grid = document.createElement('div');
    grid.className = 'chapter-grid';
    chapters.forEach(ch => {{
        const wordCount = CHAPTER_WORD_COUNT[String(ch.id)] || 0;
        const div = document.createElement('div');
        div.className = 'chapter-item';
        div.innerHTML = `<label><input type="checkbox" name="chapters" value="${{ch.id}}" onchange="updateWordCountBadge()"> ${{ch.label}} <span style="color:#999;font-size:0.8em;">(${{wordCount}}語)</span></label>`;
        grid.appendChild(div);
    }});
    chapterListDiv.appendChild(grid);
}}
document.getElementById('basicOnly').addEventListener('change', updateWordCountBadge);

// 開始ボタン押下時にのみ必要なJSONを読み込む
async function startExercise() {{
    const selected = Array.from(document.querySelectorAll('input[name="chapters"]:checked'))
                         .map(cb => parseInt(cb.value));
    if (selected.length === 0) {{ alert("チャプターを選択してください"); return; }}

    // 事前チェック（CHAPTER_WORD_COUNTベース、fetch前に弾く）
    const preCount = calcSelectedCount(selected);
    if (preCount > WORD_LIMIT) {{
        document.getElementById('errorMsg').textContent =
            `⚠️ 選択範囲が ${{preCount}} 語あります。1000語以下になるようチャプター数を減らしてください。`;
        document.getElementById('errorMsg').style.display = 'block';
        return;
    }}

    const basicOnly = document.getElementById('basicOnly').checked;
    const ranges    = selected.map(id => getChapterRange(id));

    const overlay    = document.getElementById('loadingOverlay');
    const loadingMsg = document.getElementById('loadingMsg');
    overlay.classList.add('active');
    document.getElementById('startBtn').disabled = true;

    ALL_WORDS = [];
    try {{
        for (let i = 0; i < JSON_FILES.length; i++) {{
            loadingMsg.textContent = `読み込み中... (${{i + 1}} / ${{JSON_FILES.length}})`;
            const response = await fetch(JSON_FILES[i]);
            const data     = await response.json();
            if (data.words) {{
                data.words.forEach(w => {{
                    const nStr  = String(w.number);
                    const baseN = parseInt(nStr.split('-')[0]);
                    // 選択範囲外はスキップ（メモリ節約）
                    if (!ranges.some(r => baseN >= r.min && baseN <= r.max)) return;
                    ALL_WORDS.push({{
                        n: nStr,
                        w: w.word,
                        m: w.meaning,
                        examples: w.example_sections || []
                    }});
                }});
            }}
        }}
    }} catch (e) {{
        overlay.classList.remove('active');
        document.getElementById('startBtn').disabled = false;
        alert("データの読み込みに失敗しました。\n" + e.message);
        return;
    }}

    overlay.classList.remove('active');

    // basicOnly フィルタ後の最終語数チェック
    quizWords = ALL_WORDS.filter(w => !(basicOnly && w.n.includes('-')));

    if (quizWords.length > WORD_LIMIT) {{
        document.getElementById('errorMsg').textContent =
            `⚠️ 出題語数が ${{quizWords.length}} 語になります。1000語以下になるようチャプター数を減らしてください。`;
        document.getElementById('errorMsg').style.display = 'block';
        document.getElementById('startBtn').disabled = false;
        return;
    }}

    const mode = document.getElementById('mode').value;
    if (mode === 'fill-blank') {{
        quizWords = quizWords.filter(w => w.examples.length > 0);
        if (quizWords.length === 0) {{ alert("選択した範囲に例文つきの単語がありません。"); return; }}
    }}

    if (document.querySelector('input[name="orderType"]:checked').value === 'random') {{
        quizWords.sort(() => Math.random() - 0.5);
    }}

    currentIndex = 0;
    document.getElementById('setup').classList.remove('active');
    document.getElementById('quiz').classList.add('active');
    showQuestion();
}}

function showQuestion() {{
    const word      = quizWords[currentIndex];
    const mode      = document.getElementById('mode').value;
    const container = document.getElementById('quizContainer');
    const mainBtn   = document.getElementById('mainActionBtn');

    document.getElementById('progressText').innerText =
        `STEP: ${{currentIndex + 1}} / ${{quizWords.length}} (No. ${{word.n}})`;
    container.innerHTML = '';
    mainBtn.style.display = 'none';

    if (mode === 'fill-blank')        showFillBlank(word);
    else if (mode.startsWith('card')) showCard(word, mode);
    else                              showQuiz(word, mode);
}}

function showFillBlank(word) {{
    const container = document.getElementById('quizContainer');
    const section   = word.examples[Math.floor(Math.random() * word.examples.length)];
    const ex        = section.examples[Math.floor(Math.random() * section.examples.length)];
    const target    = ex.highlight;
    const parts     = ex.en.split(new RegExp(`(${{target}})`, 'i'));

    container.innerHTML = `
        <div class="fill-blank-area">
            <div class="sentence-ja">${{ex.ja}}</div>
            <div class="sentence-en" id="sentenceEn"></div>
            <div class="feedback" id="feedback"></div>
        </div>`;

    const sentenceEn = document.getElementById('sentenceEn');
    parts.forEach(p => {{
        if (p.toLowerCase() === target.toLowerCase()) {{
            const input = document.createElement('input');
            input.type = 'text'; input.className = 'blank-input'; input.id = 'answerInput';
            input.autocomplete = 'off';
            input.onkeypress = (e) => {{ if (e.key === 'Enter') checkFillBlank(target); }};
            sentenceEn.appendChild(input);
            setTimeout(() => input.focus(), 150);
        }} else {{
            sentenceEn.appendChild(document.createTextNode(p));
        }}
    }});

    const mainBtn = document.getElementById('mainActionBtn');
    mainBtn.innerText = '判定する'; mainBtn.style.display = 'block';
    mainBtn.style.background = 'var(--primary)';
    mainBtn.onclick = () => checkFillBlank(target);
}}

function checkFillBlank(correctAnswer) {{
    const input    = document.getElementById('answerInput');
    const feedback = document.getElementById('feedback');
    const mainBtn  = document.getElementById('mainActionBtn');
    input.disabled = true;
    if (input.value.trim().toLowerCase() === correctAnswer.toLowerCase()) {{
        input.className = 'blank-input correct';
        feedback.innerText = '✨ 正解です！';
        feedback.style.color = 'var(--success)';
    }} else {{
        input.className = 'blank-input wrong';
        feedback.innerHTML = `❌ 正解は <span style="color:var(--danger)">${{correctAnswer}}</span> でした`;
        feedback.style.color = '#555';
    }}
    mainBtn.innerText = '次の問題へ';
    mainBtn.onclick = () => {{ currentIndex++; checkEnd(); }};
}}

function showCard(word, mode) {{
    const container = document.getElementById('quizContainer');
    isFlipped = false;
    container.innerHTML = `
        <div id="card" class="card" onclick="flipCard()">
            ${{mode === 'card-en-ja' ? word.w : word.m}}
        </div>
        <div class="nav-controls">
            <button id="prevBtn" class="nav-btn" onclick="goBack()" ${{currentIndex === 0 ? 'disabled' : ''}}>← 前へ戻る</button>
            <button id="nextBtn" class="nav-btn" onclick="flipCard()" style="background:var(--primary); color:white; border:none;">答えを見る / 次へ →</button>
        </div>`;
}}

function flipCard() {{
    const word = quizWords[currentIndex];
    const mode = document.getElementById('mode').value;
    const card = document.getElementById('card');
    if (!isFlipped) {{
        card.innerText = mode === 'card-en-ja' ? word.m : word.w;
        card.classList.add('flipped');
        isFlipped = true;
    }} else {{
        currentIndex++; checkEnd();
    }}
}}

function showQuiz(word, mode) {{
    const container = document.getElementById('quizContainer');
    const isEnJa    = mode === 'quiz-en-ja';
    container.innerHTML = `
        <div class="card" style="cursor:default; font-size:1.8rem; margin-bottom:15px; min-height:100px;">
            ${{isEnJa ? word.w : word.m}}
        </div>
        <div class="options-grid" id="options"></div>`;

    let choices = [word];
    while (choices.length < 4 && ALL_WORDS.length > 4) {{
        const r = ALL_WORDS[Math.floor(Math.random() * ALL_WORDS.length)];
        if (!choices.find(o => o.n === r.n)) choices.push(r);
    }}
    choices.sort(() => Math.random() - 0.5);

    const optionsDiv = document.getElementById('options');
    choices.forEach(opt => {{
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.innerText = isEnJa ? opt.m : opt.w;
        btn.onclick = () => {{
            if (opt.n === word.n) {{
                btn.style.background = '#d4edda'; btn.style.borderColor = 'var(--success)';
                setTimeout(() => {{ currentIndex++; checkEnd(); }}, 500);
            }} else {{
                btn.style.background = '#f8d7da'; btn.style.borderColor = 'var(--danger)';
                btn.disabled = true;
            }}
        }};
        optionsDiv.appendChild(btn);
    }});
}}

function goBack()   {{ if (currentIndex > 0) {{ currentIndex--; showQuestion(); }} }}
function checkEnd() {{
    if (currentIndex < quizWords.length) showQuestion();
    else {{ alert("全問終了しました！お疲れ様でした。"); location.reload(); }}
}}
</script>

</body>
</html>"""

```
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_template)
print(f"✓ {output_file} has been generated.")
```

if **name** == “**main**”:
generate_html()
