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
    CHAPTER_MAP = {1: "【Basic】第1章", 500: "【Advanced】第2章"}

def get_json_file_mapping(base_path):
    """
    各JSONファイルがどのチャプターIDをカバーしているかのマッピングを作成。
    例: {1: "vocabulary_data.json", 17: "vocabulary_data_17.json", ...}
    """
    json_pattern = str(base_path / "vocabulary_data*.json")
    files = glob(json_pattern)
    
    mapping = {}
    for f in files:
        name = os.path.basename(f)
        if name == 'vocabulary_data.json':
            mapping[1] = name
        else:
            match = re.search(r'_(\d+)\.json', name)
            if match:
                mapping[int(match.group(1))] = name
    return mapping

def generate_html():
    # パス設定
    base_dir = Path("english_dictionary")
    output_file = base_dir / "exercise.html"

    # チャプターをグループ化
    grouped = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group_name = re.search(r'【(.*?)】', title).group(1) if '【' in title else "その他"
        display_label = title.split('】')[-1] if '】' in title else title
        grouped[group_name].append({"id": s_num, "label": display_label})
    
    chapters_js = json.dumps(dict(grouped), ensure_ascii=False)
    # {チャプターID: ファイル名} のマッピングをJSに渡す
    file_mapping_js = json.dumps(get_json_file_mapping(base_dir))
    
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英単語演習</title>
    <link rel="icon" href="/favicon.png" type="image/png">
    <link rel="apple-touch-icon" href="/favicon.png">
    <style>
        :root {{ --primary: #007bff; --success: #28a745; --danger: #dc3545; --bg: #f4f7f9; --text: #333; }}
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: var(--bg); margin: 0; padding: 20px; color: var(--text); display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; }}
        
        /* パンくずリストの統一スタイル */
        .breadcrumb {{ margin-bottom: 25px; font-size: 0.9em; padding: 12px 15px; background: #e9ecef; border-radius: 6px; color: #6c757d; box-sizing: border-box; width: 100%; text-align: left; }}
        .breadcrumb a {{ color: var(--primary); text-decoration: none; font-weight: bold; }}
        .breadcrumb a:hover {{ text-decoration: underline; }}

        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
        h1 {{ margin: 0; font-size: 1.5rem; color: var(--primary); }}

        .setup-section, .quiz-section {{ display: none; }}
        .active {{ display: block; }}
        
        .chapter-container {{ max-height: 350px; overflow-y: auto; border: 1px solid #ddd; padding: 12px; border-radius: 8px; background: #fafafa; margin-bottom: 10px; }}
        
        /* 変更点：グループヘッダーをクリッカブルに変更 */
        .chapter-group-header {{ font-size: 0.9rem; font-weight: bold; color: #555; background: #e9ecef; padding: 8px 12px; margin: 8px 0 0 0; border-radius: 4px; border-left: 4px solid var(--primary); display: flex; justify-content: space-between; cursor: pointer; user-select: none; transition: background 0.2s; }}
        .chapter-group-header:hover {{ background: #dde2e6; }}
        
        /* 変更点：デフォルトは非表示にし、.activeが付与されたらグリッド表示 */
        .chapter-grid {{ display: none; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 6px; padding: 10px; background: #fff; border: 1px solid #eee; border-top: none; border-radius: 0 0 4px 4px; margin-bottom: 8px; }}
        .chapter-grid.active {{ display: grid; }}
        
        .chapter-item {{ font-size: 0.85rem; display: flex; align-items: center; cursor: pointer; }}
        .chapter-item input {{ margin-right: 10px; }}
        
        .option-group {{ margin-bottom: 25px; }}
        label.group-label {{ display: block; font-weight: bold; margin-bottom: 10px; font-size: 1rem; color: #444; }}
        
        .btn {{ background: var(--primary); color: white; border: none; padding: 14px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-size: 1rem; font-weight: bold; transition: 0.3s; margin-top: 10px; }}
        .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
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
    </style>
</head>
<body>

<div class="container">
    <div class="breadcrumb">
        <a href="../index.html">ホーム</a> > <a href="index.html">英単語帳</a> > 単語演習
    </div>

    <div class="header">
        <h1>単語演習</h1>
    </div>

    <div id="setup" class="setup-section active">
        <div class="option-group">
            <label class="group-label">1. 出題範囲を選択 (最大20チャプター)</label>
            <div class="chapter-container" id="chapterList"></div>
        </div>

        <div class="option-group">
            <label class="group-label">2. 出題順序</label>
            <label style="margin-right:20px; cursor:pointer;"><input type="radio" name="orderType" value="random" checked> ランダム</label>
            <label style="cursor:pointer;"><input type="radio" name="orderType" value="sequential"> 番号順</label>
            <label style="cursor:pointer; color: var(--danger); font-weight: bold; margin-left: 20px;">
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

        <button id="startBtn" class="btn" onclick="startExercise()">演習開始！</button>
    </div>

    <div id="quiz" class="quiz-section">
        <div id="loadingMessage" style="display:none; text-align:center; padding: 20px; color: var(--primary); font-weight: bold;">
            選択したチャプターのデータを読み込んでいます...
        </div>
        <div id="quizContent">
            <div class="progress" id="progressText">STEP: 0 / 0</div>
            <div id="quizContainer"></div>
            <button id="mainActionBtn" class="btn" style="display:none;"></button>
            
            <div style="display:flex; gap:10px; margin-top:20px;">
                <button class="btn" style="background:#6c757d; flex:1;" onclick="location.reload()">演習をやり直す</button>
            </div>
        </div>
    </div>
</div>

<script>
const GROUPED_CHAPTERS = {chapters_js}; 
const FILE_MAPPING = {file_mapping_js};
let ALL_WORDS_BUFFER = []; // 読み込んだ全単語

// 変更点：チャプター選択画面の構築（アコーディオン化）
const chapterListDiv = document.getElementById('chapterList');
for (const [group, chapters] of Object.entries(GROUPED_CHAPTERS)) {{
    const groupHeader = document.createElement('div');
    groupHeader.className = 'chapter-group-header';
    groupHeader.innerHTML = `<span>${{group}}</span><span class="toggle-icon">▽</span>`;
    chapterListDiv.appendChild(groupHeader);
    
    const grid = document.createElement('div');
    grid.className = 'chapter-grid';
    chapters.forEach(ch => {{
        const div = document.createElement('div');
        div.className = 'chapter-item';
        div.innerHTML = `<label><input type="checkbox" name="chapters" value="${{ch.id}}"> ${{ch.label}}</label>`;
        grid.appendChild(div);
    }});
    chapterListDiv.appendChild(grid);

    // クリックイベントで展開・折りたたみを切り替え
    groupHeader.addEventListener('click', () => {{
        const isActive = grid.classList.toggle('active');
        groupHeader.querySelector('.toggle-icon').innerText = isActive ? '△' : '▽';
    }});
}}

let quizWords = [];
let currentIndex = 0;
let isFlipped = false;

async function startExercise() {{
    const selectedIds = Array.from(document.querySelectorAll('input[name="chapters"]:checked')).map(cb => parseInt(cb.value));
    
    if(selectedIds.length === 0) {{ alert("チャプターを選択してください"); return; }}
    if(selectedIds.length > 20) {{ alert("一度に選択できるのは20チャプターまでです（現在: " + selectedIds.length + "）"); return; }}

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    startBtn.innerText = "データ読み込み中...";

    // 必要なJSONファイルを特定
    const filesToFetch = new Set();
    const allThresholds = Object.values(GROUPED_CHAPTERS).flat().map(ch => ch.id).sort((a,b)=>a-b);
    
    selectedIds.forEach(id => {{
        if (FILE_MAPPING[id]) {{
            filesToFetch.add(FILE_MAPPING[id]);
        }}
    }});

    try {{
        // 動的フェッチ
        const results = await Promise.all(Array.from(filesToFetch).map(file => fetch(file).then(r => r.json())));
        
        let loadedWords = [];
        results.forEach(data => {{
            if (data.words) {{
                data.words.forEach(w => {{
                    loadedWords.push({{ 
                        n: String(w.number), 
                        w: w.word, 
                        m: w.meaning,
                        examples: w.example_sections || []
                    }});
                }});
            }}
        }});

        // フィルタリング（選択されたチャプターの範囲内か）
        const basicOnly = document.getElementById('basicOnly').checked;
        quizWords = loadedWords.filter(w => {{
            if (basicOnly && w.n.includes('-')) return false;
            const n = parseInt(w.n.split('-')[0]);
            const chapterId = allThresholds.slice().reverse().find(t => n >= t);
            return selectedIds.includes(chapterId);
        }});

        const mode = document.getElementById('mode').value;
        if(mode === 'fill-blank') {{
            quizWords = quizWords.filter(w => w.examples.length > 0);
            if(quizWords.length === 0) {{ alert("選択した範囲に例文つきの単語がありません。"); location.reload(); return; }}
        }}

        if(document.querySelector('input[name="orderType"]:checked').value === 'random') {{
            quizWords.sort(() => Math.random() - 0.5);
        }} else {{
            quizWords.sort((a,b) => parseInt(a.n) - parseInt(b.n));
        }}

        if(quizWords.length === 0) {{ alert("単語が見つかりませんでした。"); location.reload(); return; }}

        currentIndex = 0;
        document.getElementById('setup').classList.remove('active');
        document.getElementById('quiz').classList.add('active');
        showQuestion();

    }} catch (e) {{
        alert("データの取得に失敗しました。");
        console.error(e);
        location.reload();
    }}
}}

function showQuestion() {{
    const word = quizWords[currentIndex];
    const mode = document.getElementById('mode').value;
    const container = document.getElementById('quizContainer');
    const mainBtn = document.getElementById('mainActionBtn');
    
    document.getElementById('progressText').innerText = `STEP: ${{currentIndex + 1}} / ${{quizWords.length}} (No. ${{word.n}})`;
    container.innerHTML = '';
    mainBtn.style.display = 'none';

    if(mode === 'fill-blank') {{
        showFillBlank(word);
    }} else if(mode.startsWith('card')) {{
        showCard(word, mode);
    }} else {{
        showQuiz(word, mode);
    }}
}}

function showFillBlank(word) {{
    const container = document.getElementById('quizContainer');
    const section = word.examples[Math.floor(Math.random() * word.examples.length)];
    const ex = section.examples[Math.floor(Math.random() * section.examples.length)];
    const target = ex.highlight;
    const parts = ex.en.split(new RegExp(`(${{target}})`, 'i'));

    container.innerHTML = `
        <div class="fill-blank-area">
            <div class="sentence-ja">${{ex.ja}}</div>
            <div class="sentence-en" id="sentenceEn"></div>
            <div class="feedback" id="feedback"></div>
        </div>
    `;

    const sentenceEn = document.getElementById('sentenceEn');
    parts.forEach(p => {{
        if(p.toLowerCase() === target.toLowerCase()) {{
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'blank-input';
            input.id = 'answerInput';
            input.autocomplete = 'off';
            input.onkeypress = (e) => {{ if(e.key === 'Enter') checkFillBlank(target); }};
            sentenceEn.appendChild(input);
            setTimeout(() => input.focus(), 150);
        }} else {{
            sentenceEn.appendChild(document.createTextNode(p));
        }}
    }});

    const mainBtn = document.getElementById('mainActionBtn');
    mainBtn.innerText = '判定する';
    mainBtn.style.display = 'block';
    mainBtn.style.background = 'var(--primary)';
    mainBtn.onclick = () => checkFillBlank(target);
}}

function checkFillBlank(correctAnswer) {{
    const input = document.getElementById('answerInput');
    const feedback = document.getElementById('feedback');
    const mainBtn = document.getElementById('mainActionBtn');
    const userAns = input.value.trim().toLowerCase();
    
    input.disabled = true;
    if(userAns === correctAnswer.toLowerCase()) {{
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
        </div>
    `;
}}

function flipCard() {{
    const word = quizWords[currentIndex];
    const mode = document.getElementById('mode').value;
    const card = document.getElementById('card');
    if(!isFlipped) {{
        card.innerText = mode === 'card-en-ja' ? word.m : word.w;
        card.classList.add('flipped');
        isFlipped = true;
    }} else {{
        currentIndex++; checkEnd();
    }}
}}

function showQuiz(word, mode) {{
    const container = document.getElementById('quizContainer');
    const isEnJa = mode === 'quiz-en-ja';
    container.innerHTML = `
        <div class="card" style="cursor:default; font-size:1.8rem; margin-bottom:15px; min-height:100px;">
            ${{isEnJa ? word.w : word.m}}
        </div>
        <div class="options-grid" id="options"></div>
    `;
    
    // 誤選択肢用のダミー単語
    let choices = [word];
    // quizWords（現在読み込まれている中）からランダムに選ぶ
    let pool = quizWords.length > 10 ? quizWords : loadedWords_Global_Fallback; 
    // ※今回は簡略化のため、今回のquizWordsから。足りなければ他から。
    
    while(choices.length < 4) {{
        const r = quizWords[Math.floor(Math.random() * quizWords.length)];
        if(!choices.find(o => o.n === r.n)) choices.push(r);
        // 万が一選択肢が足りない場合の無限ループ防止
        if(quizWords.length < 4) break;
    }}
    choices.sort(() => Math.random() - 0.5);
    
    const optionsDiv = document.getElementById('options');
    choices.forEach(opt => {{
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.innerText = isEnJa ? opt.m : opt.w;
        btn.onclick = () => {{
            if(opt.n === word.n) {{
                btn.style.background = '#d4edda';
                btn.style.borderColor = 'var(--success)';
                setTimeout(() => {{ currentIndex++; checkEnd(); }}, 500);
            }} else {{
                btn.style.background = '#f8d7da';
                btn.style.borderColor = 'var(--danger)';
                btn.disabled = true;
            }}
        }};
        optionsDiv.appendChild(btn);
    }});
}}

function goBack() {{ if(currentIndex > 0) {{ currentIndex--; showQuestion(); }} }}
function checkEnd() {{ if(currentIndex < quizWords.length) showQuestion(); else {{ alert("全問終了しました！お疲れ様でした。"); location.reload(); }} }}
</script>
</body>
</html>"""

    # 保存
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"✓ {output_file} has been generated (Dynamic Loading Mode).")

if __name__ == "__main__":
    generate_html()
