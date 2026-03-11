import json
from pathlib import Path

def generate_lightweight_html():
    from config import CHAPTER_MAP, CHAPTER_WORD_COUNT
    base_dir = Path("english_dictionary")
    output_file = base_dir / "exercise.html"

    # JavaScriptに渡すためのデータ
    chapters_data = []
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group = title.split('】')[0].replace('【', '') if '【' in title else "その他"
        label = title.split('】')[-1] if '】' in title else title
        chapters_data.append({
            "id": s_num,
            "group": group,
            "label": label,
            "count": CHAPTER_WORD_COUNT.get(s_num, 0)
        })

    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>英単語演習 (軽量版)</title>
    <style>
        /* スタイルは以前のものを継承しつつ、カウント表示用に追加 */
        :root {{ --primary: #007bff; --success: #28a745; --danger: #dc3545; --bg: #f4f7f9; }}
        body {{ font-family: sans-serif; background: var(--bg); padding: 20px; display: flex; flex-direction: column; align-items: center; }}
        .container {{ width: 100%; max-width: 800px; background: white; padding: 20px; border-radius: 12px; shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .chapter-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; border-radius: 8px; }}
        .chapter-item {{ display: flex; justify-content: space-between; padding: 5px; border-bottom: 1px solid #eee; font-size: 0.9rem; }}
        .word-count-badge {{ background: #eee; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; color: #666; }}
        .summary-bar {{ margin: 15px 0; padding: 10px; background: #e9ecef; border-radius: 8px; text-align: center; font-weight: bold; }}
        .limit-over {{ color: var(--danger); }}
        .btn {{ width: 100%; padding: 15px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; }}
        .btn-primary {{ background: var(--primary); color: white; }}
        .btn-primary:disabled {{ background: #ccc; cursor: not-allowed; }}
        /* 演習画面などのスタイルは適宜含める */
        .setup-section, .quiz-section {{ display: none; }}
        .active {{ display: block; }}
        /* (中略: 以前のスタイルを適用) */
    </style>
</head>
<body>
<div class="container">
    <div id="setup" class="setup-section active">
        <h2>出題設定</h2>
        <div class="summary-bar" id="summaryBar">選択中の単語数: 0 / 2000</div>
        
        <div class="chapter-container" id="chapterList"></div>

        <div style="margin-top:20px;">
            <label>演習モード: 
                <select id="mode" style="padding:8px;">
                    <option value="card-en-ja">暗記カード (英→日)</option>
                    <option value="quiz-en-ja">4択問題 (英→日)</option>
                    <option value="fill-blank">例文穴埋め</option>
                </select>
            </label>
        </div>
        
        <button id="startBtn" class="btn btn-primary" onclick="startExercise()" disabled style="margin-top:20px;">チャプターを選択してください</button>
    </div>

    <div id="quiz" class="quiz-section">
        <div id="progressText"></div>
        <div id="quizContainer"></div>
        <button id="mainActionBtn" class="btn btn-primary" style="display:none; margin-top:10px;"></button>
        <button class="btn" onclick="location.reload()" style="margin-top:10px; background:#6c757d; color:white;">設定に戻る</button>
    </div>
</div>

<script>
const CHAPTERS = {json.dumps(chapters_data, ensure_ascii=False)};
let selectedCount = 0;

// 画面構築
const listDiv = document.getElementById('chapterList');
let currentGroup = "";
CHAPTERS.forEach(ch => {{
    if(ch.group !== currentGroup) {{
        const gDiv = document.createElement('div');
        gDiv.style = "background:#f0f0f0; padding:5px; font-weight:bold; margin-top:10px;";
        gDiv.innerText = ch.group;
        listDiv.appendChild(gDiv);
        currentGroup = ch.group;
    }}
    const item = document.createElement('div');
    item.className = 'chapter-item';
    item.innerHTML = `
        <label><input type="checkbox" class="ch-cb" value="${{ch.id}}" data-count="${{ch.count}}" onchange="updateSummary()"> ${{ch.label}}</label>
        <span class="word-count-badge">${{ch.count}} 語</span>
    `;
    listDiv.appendChild(item);
}});

function updateSummary() {{
    const cbs = document.querySelectorAll('.ch-cb:checked');
    selectedCount = Array.from(cbs).reduce((sum, cb) => sum + parseInt(cb.dataset.count), 0);
    
    const bar = document.getElementById('summaryBar');
    const btn = document.getElementById('startBtn');
    bar.innerText = `選択中の単語数: ${{selectedCount}} / 2000`;
    
    if(selectedCount > 0 && selectedCount <= 2000) {{
        bar.classList.remove('limit-over');
        btn.disabled = false;
        btn.innerText = "演習開始！";
    }} else {{
        if(selectedCount > 2000) bar.classList.add('limit-over');
        btn.disabled = true;
        btn.innerText = selectedCount > 2000 ? "単語数が多すぎます(2000語以内)" : "チャプターを選択してください";
    }}
}}

async function startExercise() {{
    const selectedIds = Array.from(document.querySelectorAll('.ch-cb:checked')).map(cb => parseInt(cb.value));
    const btn = document.getElementById('startBtn');
    btn.disabled = true;
    btn.innerText = "データを読み込み中...";

    try {{
        // ここで初めてJSONを読み込む (必要なファイルだけ推測してfetch)
        // 実際には全てのvocabulary_data*.jsonを読み込み、中身をフィルタリング
        const files = ["vocabulary_data.json", "vocabulary_data_1.json", "vocabulary_data_2.json"]; // 適切なファイルリストを生成
        
        let allWords = [];
        // ※実際にはサーバー上のファイルリストを取得するか、
        // もしくは vocabulary_data_1...10.json までを順番にfetchしてエラーなら止める等の処理
        const results = await Promise.all([
            fetch('vocabulary_data.json').then(r => r.ok ? r.json() : {{words:[]}}),
            fetch('vocabulary_data_1.json').then(r => r.ok ? r.json() : {{words:[]}}),
            fetch('vocabulary_data_2.json').then(r => r.ok ? r.json() : {{words:[]}})
        ]);

        results.forEach(data => {{
            data.words.forEach(w => {{
                const n = parseInt(String(w.number).split('-')[0]);
                const chId = CHAPTERS.slice().reverse().find(c => n >= c.id)?.id;
                if(selectedIds.includes(chId)) {{
                    allWords.push(w);
                }}
            }});
        }});

        // 演習開始ロジックへ (quizWords = allWords ...)
        console.log("Loaded words:", allWords.length);
        // ... (以下、以前の演習ロジック)
        alert(allWords.length + "語読み込みました。演習を開始します。");
        // ※実際にはここにshowQuestion()などの処理を続けます
    }} catch(e) {{
        alert("読み込みエラーが発生しました。");
        console.error(e);
    }}
}}
</script>
</body>
</html>"""
    
    output_file.write_text(html_template, encoding="utf-8")
    print(f"✓ {output_file} generated.")
