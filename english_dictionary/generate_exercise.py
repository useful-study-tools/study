import json
import os
import re
from pathlib import Path
from glob import glob
from collections import defaultdict

try:
    from config import CHAPTER_MAP
except ImportError:
    CHAPTER_MAP = {1: "第1章"}

def get_number_to_file_mapping(base_path):
    files = glob(str(base_path / "vocabulary_data*.json"))
    mapping = {}
    for f in files:
        name = os.path.basename(f)
        if name == "vocabulary_data.json":
            mapping[1] = name
        else:
            m = re.search(r'_(\d+)\.json', name)
            if m:
                mapping[int(m.group(1))] = name
    return dict(sorted(mapping.items()))

def generate_html():
    base_dir = Path("english_dictionary")
    output_file = base_dir / "exercise.html"

    grouped = defaultdict(list)
    for s_num, title in sorted(CHAPTER_MAP.items()):
        group_name = re.search(r'【(.*?)】', title).group(1) if '【' in title else "その他"
        display_label = title.split('】')[-1] if '】' in title else title
        grouped[group_name].append({
            "id": s_num,
            "label": display_label
        })

    chapters_js = json.dumps(dict(grouped), ensure_ascii=False)
    number_to_file_js = json.dumps(
        get_number_to_file_mapping(base_dir),
        ensure_ascii=False
    )

    # 修正ポイント: f-string(f""")を止め、普通の文字列にする
    # Pythonで埋め込みたい箇所だけ __PLACEHOLDER__ に書き換え
    html_template = """<!DOCTYPE html>
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
        
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
        h1 {{ margin: 0; font-size: 1.5rem; color: var(--primary); }}
        .home-link {{ text-decoration: none; color: #666; font-size: 0.9rem; font-weight: bold; padding: 8px 12px; border-radius: 6px; background: #eee; transition: 0.2s; }}
        .home-link:hover {{ background: #ddd; color: #333; }}

        .setup-section, .quiz-section {{ display: none; }}
        .active {{ display: block; }}
        
        .chapter-container {{ max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 12px; border-radius: 8px; background: #fafafa; margin-bottom: 10px; }}
        .chapter-group-title {{ font-size: 0.85rem; font-weight: bold; color: #555; background: #e9ecef; padding: 6px 12px; margin: 12px 0 6px 0; border-radius: 4px; border-left: 4px solid var(--primary); }}
        .chapter-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 6px; padding: 0 5px; }}
        .chapter-item {{ font-size: 0.85rem; display: flex; align-items: center; cursor: pointer; }}
        .chapter-item input {{ margin-right: 10px; }}
        
        .option-group {{ margin-bottom: 25px; }}
        label.group-label {{ display: block; font-weight: bold; margin-bottom: 10px; font-size: 1rem; color: #444; }}
        
        .btn {{ background: var(--primary); color: white; border: none; padding: 14px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-size: 1rem; font-weight: bold; transition: 0.3s; margin-top: 10px; }}
        .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
        .btn:disabled {{ background: #ccc; cursor: wait; transform: none; }}
        
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
        .header-top {{ width: 100%; display: flex; justify-content: flex-start; margin-bottom: 15px; }}
        .btn-home {{ display: inline-block; margin-bottom: 20px; padding: 8px 18px; background-color: #6c757d; color: white !important; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 0.85rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: 0.3s; }}
        .btn-home:hover {{ background-color: #5a6268; transform: translateY(-1px); }}
    </style>
</head>
<body>

<div class="container">
        <a href="index.html" class="btn-home">英単語帳に戻る</a>
    <div class="header">
        <h1>単語演習</h1>
    </div>

    <div id="loadingStatus" style="text-align:center; padding: 40px; color: var(--primary);">
        データを読み込んでいます...
    </div>

    <div id="setup" class="setup-section">
        <div class="option-group">
            <label class="group-label">1. 出題範囲を選択</label>
            <div class="chapter-container" id="chapterList"></div>
        </div>

        <div class="option-group">
            <label class="group-label">2. 出題順序</label>
            <label style="margin-right:20px; cursor:pointer;"><input type="radio" name="orderType" value="random" checked> ランダム</label>
            <label style="cursor:pointer;"><input type="radio" name="orderType" value="sequential"> 番号順</label>
            <label style="cursor:pointer; color: var(--danger); font-weight: bold;">
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

        <button id="startBtn" class="btn" onclick="startExercise()" disabled>準備中...</button>
    </div>

    <div id="quiz" class="quiz-section">
        <div class="progress" id="progressText">STEP: 0 / 0</div>
        <div id="quizContainer"></div>
        <button id="mainActionBtn" class="btn" style="display:none;"></button>
        
        <div style="display:flex; gap:10px; margin-top:20px;">
            <button class="btn" style="background:#6c757d; flex:1;" onclick="location.reload()">演習をやり直す</button>
        </div>
    </div>
</div>

<script>
// Pythonからデータを注入
const GROUPED_CHAPTERS = __GROUPED_CHAPTERS__;
const NUMBER_TO_FILE = __NUMBER_TO_FILE__;

const FILE_THRESHOLDS = Object.keys(NUMBER_TO_FILE).map(Number).sort((a,b)=>a-b);
let quizWords=[];
let currentIndex=0;
let loadedWords=[];

const chapterList=document.getElementById("chapterList");
for(const [group, chapters] of Object.entries(GROUPED_CHAPTERS)){
    const title=document.createElement("div");
    title.className="chapter-group-title";
    title.innerText=group;
    chapterList.appendChild(title);
    const grid=document.createElement("div");
    grid.className="chapter-grid";
    chapters.forEach(ch=>{
        const div=document.createElement("div");
        div.innerHTML=`<label><input type="checkbox" value="${ch.id}">${ch.label}</label>`;
        grid.appendChild(div);
    });
    chapterList.appendChild(grid);
}

function getFileForNumber(n){
    for(let i=FILE_THRESHOLDS.length-1; i>=0; i--){
        if(n>=FILE_THRESHOLDS[i]) return NUMBER_TO_FILE[FILE_THRESHOLDS[i]];
    }
    return null;
}

async function startExercise(){
    const selectedIds=[...document.querySelectorAll("#chapterList input:checked")].map(e=>parseInt(e.value));
    if(selectedIds.length==0){ alert("チャプター選択してください"); return; }
    const files=new Set();
    selectedIds.forEach(id=>{ const f=getFileForNumber(id); if(f) files.add(f); });

    try{
        loadedWords=[];
        for(const file of files){
            const res=await fetch(file);
            const data=await res.json();
            data.words.forEach(w=>{
                loadedWords.push({
                    n:String(w.number), w:w.word, m:w.meaning, examples:w.example_sections||[]
                });
            });
        }
        buildQuiz(selectedIds);
    }catch(e){ alert("JSON読み込み失敗"); console.error(e); }
}

function buildQuiz(selectedIds){
    const thresholds=Object.values(GROUPED_CHAPTERS).flat().map(c=>c.id).sort((a,b)=>a-b);
    const basicOnly=document.getElementById("basicOnly").checked;
    quizWords=loadedWords.filter(w=>{
        if(basicOnly && w.n.includes("-")) return false;
        const n=parseInt(w.n.split("-")[0]);
        let chapter=null;
        for(let i=thresholds.length-1; i>=0; i--){
            if(n>=thresholds[i]){ chapter=thresholds[i]; break; }
        }
        return selectedIds.includes(chapter);
    });
    if(quizWords.length==0){ alert("単語が見つかりませんでした"); return; }
    if(document.querySelector('input[name="orderType"]:checked').value=="random"){
        quizWords.sort(()=>Math.random()-0.5);
    }else{
        quizWords.sort((a,b)=>parseInt(a.n)-parseInt(b.n));
    }
    document.getElementById("setup").style.display="none";
    document.getElementById("quiz").style.display="block";
    currentIndex=0;
    showQuestion();
}

function showQuestion(){
    const word=quizWords[currentIndex];
    document.getElementById("progress").innerText=`${currentIndex+1} / ${quizWords.length}  No.${word.n}`;
    const mode=document.getElementById("mode").value;
    if(mode.startsWith("card")) showCard(word,mode);
    else if(mode.startsWith("quiz")) showQuiz(word,mode);
    else showFillBlank(word);
}

function showCard(word,mode){
    const front=mode=="card-en-ja"?word.w:word.m;
    const back=mode=="card-en-ja"?word.m:word.w;
    const container=document.getElementById("quizContainer");
    container.innerHTML=`<div class="card" onclick="nextCard('${back}')">${front}</div>`;
}

function nextCard(ans){
    const c=document.querySelector(".card");
    if(c.innerText!=ans){ c.innerText=ans; return; }
    currentIndex++;
    if(currentIndex>=quizWords.length) finish();
    else showQuestion();
}

function showQuiz(word,mode){
    const container=document.getElementById("quizContainer");
    const isEnJa=mode=="quiz-en-ja";
    container.innerHTML=`<div class="card">${isEnJa?word.w:word.m}</div><div id="opts"></div>`;
    const opts=[word];
    while(opts.length<4 && quizWords.length>opts.length){
        const r=quizWords[Math.floor(Math.random()*quizWords.length)];
        if(!opts.find(o=>o.n==r.n)) opts.push(r);
    }
    opts.sort(()=>Math.random()-0.5);
    const div=document.getElementById("opts");
    opts.forEach(o=>{
        const b=document.createElement("button");
        b.className="option-btn";
        b.innerText=isEnJa?o.m:o.w;
        b.onclick=()=>{
            if(o.n==word.n){ currentIndex++; if(currentIndex>=quizWords.length) finish(); else showQuestion(); }
            else{ b.style.background="#f8d7da"; }
        };
        div.appendChild(b);
    });
}

function showFillBlank(word){
    const container=document.getElementById("quizContainer");
    if(!word.examples.length){ currentIndex++; showQuestion(); return; }
    const sec=word.examples[Math.floor(Math.random()*word.examples.length)];
    const ex=sec.examples[Math.floor(Math.random()*sec.examples.length)];
    container.innerHTML=`<p>${ex.ja}</p><p>${ex.en.replace(new RegExp(ex.highlight, 'gi'), '____')}</p>
    <input id="ans" placeholder="答えを入力">
    <button onclick="checkAnswer('${ex.highlight}')">判定</button>`;
}

function checkAnswer(ans){
    const v=document.getElementById("ans").value.trim().toLowerCase();
    if(v==ans.toLowerCase()) alert("正解！");
    else alert("正解は: "+ans);
    currentIndex++;
    if(currentIndex>=quizWords.length) finish();
    else showQuestion();
}

function finish(){ alert("終了！お疲れ様でした。"); location.reload(); }
</script>
</body>
</html>
"""

    # 最後にPython変数を流し込む
    final_html = html_template.replace("__GROUPED_CHAPTERS__", chapters_js)
    final_html = final_html.replace("__NUMBER_TO_FILE__", number_to_file_js)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"✅ {output_file} generated successfully.")

if __name__=="__main__":
    generate_html()
