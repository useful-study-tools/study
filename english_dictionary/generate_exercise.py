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
    """
    JSONファイル名から番号を読み取り
    その番号を開始番号としてマッピングする
    vocabulary_data_51.json → 51
    """
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

        # 中略（上のインポートや関数はそのまま）

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>英単語演習</title>

<style>
body {{
font-family: sans-serif;
background:#f4f7f9;
margin:0;
padding:20px;
}}

.container {{
max-width:800px;
margin:auto;
}}

.chapter-container {{
max-height:300px;
overflow:auto;
border:1px solid #ccc;
padding:10px;
border-radius:8px;
background:white;
}}

.chapter-group-title {{
font-weight:bold;
margin-top:10px;
}}

.chapter-grid {{
display:grid;
grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
gap:4px;
}}

.card {{
border:2px solid #007bff;
padding:40px;
border-radius:10px;
text-align:center;
font-size:2rem;
background:white;
}}

.option-btn {{
display:block;
width:100%;
padding:12px;
margin:6px 0;
border:1px solid #ccc;
border-radius:6px;
background:white;
cursor:pointer;
}}
</style>

</head>
<body>

<div class="container">
    <h2>単語演習</h2>
    <div id="setup">
        <p>出題範囲</p>
        <div class="chapter-container" id="chapterList"></div>
        <p>順序</p>
        <label><input type="radio" name="orderType" value="random" checked>ランダム</label>
        <label><input type="radio" name="orderType" value="sequential">番号順</label>
        <br><br>
        <label><input type="checkbox" id="basicOnly">基本語のみ</label>
        <br><br>
        <select id="mode">
            <option value="card-en-ja">暗記カード 英→日</option>
            <option value="card-ja-en">暗記カード 日→英</option>
            <option value="quiz-en-ja">4択 英→日</option>
            <option value="quiz-ja-en">4択 日→英</option>
            <option value="fill-blank">例文穴埋め</option>
        </select>
        <br><br>
        <button onclick="startExercise()">開始</button>
    </div>

    <div id="quiz" style="display:none">
        <p id="progress"></p>
        <div id="quizContainer"></div>
        <br>
        <button onclick="location.reload()">最初に戻る</button>
    </div>
</div>

<script>
// ここはPythonの変数を流し込むので単一の { }
const GROUPED_CHAPTERS = {chapters_js};
const NUMBER_TO_FILE = {number_to_file_js};

// ここからはJavaScriptのコードなので、波括弧を {{ }} にエスケープする
const FILE_THRESHOLDS = Object.keys(NUMBER_TO_FILE)
    .map(Number)
    .sort((a,b)=>a-b);

let quizWords=[];
let currentIndex=0;
let loadedWords=[];

const chapterList=document.getElementById("chapterList");

for(const [group,chapters] of Object.entries(GROUPED_CHAPTERS)){{
    const title=document.createElement("div");
    title.className="chapter-group-title";
    title.innerText=group;
    chapterList.appendChild(title);

    const grid=document.createElement("div");
    grid.className="chapter-grid";

    chapters.forEach(ch=>{{
        const div=document.createElement("div");
        // JavaScriptのテンプレートリテラル `${{...}}` は Python f-string内では `{{ ... }}` 
        div.innerHTML=`<label>
            <input type="checkbox" value="${{ch.id}}">
            ${{ch.label}}
        </label>`;
        grid.appendChild(div);
    }});
    chapterList.appendChild(grid);
}}

function getFileForNumber(n){{
    for(let i=FILE_THRESHOLDS.length-1;i>=0;i--){{
        if(n>=FILE_THRESHOLDS[i]){{
            return NUMBER_TO_FILE[FILE_THRESHOLDS[i]];
        }}
    }}
    return null;
}}

async function startExercise(){{
    const selectedIds=[...document.querySelectorAll("#chapterList input:checked")]
        .map(e=>parseInt(e.value));

    if(selectedIds.length==0){{
        alert("チャプター選択してください");
        return;
    }}

    const files=new Set();
    selectedIds.forEach(id=>{{
        const f=getFileForNumber(id);
        if(f)files.add(f);
    }});

    try{{
        loadedWords=[];
        for(const file of files){{
            const res=await fetch(file);
            const data=await res.json();
            data.words.forEach(w=>{{
                loadedWords.push({{
                    n:String(w.number),
                    w:w.word,
                    m:w.meaning,
                    examples:w.example_sections||[]
                }});
            }});
        }}
        buildQuiz(selectedIds);
    }}catch(e){{
        alert("JSON読み込み失敗");
        console.error(e);
    }}
}}

function buildQuiz(selectedIds){{
    const thresholds=Object.values(GROUPED_CHAPTERS)
        .flat()
        .map(c=>c.id)
        .sort((a,b)=>a-b);

    const basicOnly=document.getElementById("basicOnly").checked;

    quizWords=loadedWords.filter(w=>{{
        if(basicOnly && w.n.includes("-")) return false;
        const n=parseInt(w.n.split("-")[0]);
        let chapter=null;
        for(let i=thresholds.length-1;i>=0;i--){{
            if(n>=thresholds[i]){{
                chapter=thresholds[i];
                break;
            }}
        }}
        return selectedIds.includes(chapter);
    }});

    if(quizWords.length==0){{
        alert("単語が見つかりませんでした");
        return;
    }}

    if(document.querySelector('input[name="orderType"]:checked').value=="random"){{
        quizWords.sort(()=>Math.random()-0.5);
    }}else{{
        quizWords.sort((a,b)=>parseInt(a.n)-parseInt(b.n));
    }}

    document.getElementById("setup").style.display="none";
    document.getElementById("quiz").style.display="block";
    currentIndex=0;
    showQuestion();
}}

function showQuestion(){{
    const word=quizWords[currentIndex];
    document.getElementById("progress").innerText=
        (currentIndex+1)+" / "+quizWords.length+"  No."+word.n;
    const mode=document.getElementById("mode").value;

    if(mode.startsWith("card")){{
        showCard(word,mode);
    }} else if(mode.startsWith("quiz")){{
        showQuiz(word,mode);
    }} else {{
        showFillBlank(word);
    }}
}}

function showCard(word,mode){{
    const front=mode=="card-en-ja"?word.w:word.m;
    const back=mode=="card-en-ja"?word.m:word.w;
    const container=document.getElementById("quizContainer");
    // ここもJavaScriptのリテラルなので ${{...}} に修正
    container.innerHTML=`<div class="card" onclick="nextCard('${{back}}')">${{front}}</div>`;
}}

function nextCard(ans){{
    const c=document.querySelector(".card");
    if(c.innerText!=ans){{
        c.innerText=ans;
        return;
    }}
    currentIndex++;
    if(currentIndex>=quizWords.length){{
        finish();
        return;
    }}
    showQuestion();
}}

function showQuiz(word,mode){{
    const container=document.getElementById("quizContainer");
    const isEnJa=mode=="quiz-en-ja";
    container.innerHTML=`<div class="card">${{isEnJa?word.w:word.m}}</div><div id="opts"></div>`;

    const opts=[word];
    while(opts.length<4 && quizWords.length>opts.length){{
        const r=quizWords[Math.floor(Math.random()*quizWords.length)];
        if(!opts.find(o=>o.n==r.n))opts.push(r);
    }}
    opts.sort(()=>Math.random()-0.5);

    const div=document.getElementById("opts");
    opts.forEach(o=>{{
        const b=document.createElement("button");
        b.className="option-btn";
        b.innerText=isEnJa?o.m:o.w;
        b.onclick=()=>{{
            if(o.n==word.n){{
                currentIndex++;
                if(currentIndex>=quizWords.length)finish();
                else showQuestion();
            }}else{{
                b.style.background="#f8d7da";
            }}
        }};
        div.appendChild(b);
    }});
}}

function showFillBlank(word){{
    const container=document.getElementById("quizContainer");
    if(!word.examples.length){{
        currentIndex++;
        showQuestion();
        return;
    }}
    const sec=word.examples[Math.floor(Math.random()*word.examples.length)];
    const ex=sec.examples[Math.floor(Math.random()*sec.examples.length)];

    container.innerHTML=`<p>${{ex.ja}}</p><p>${{ex.en}}</p><input id="ans"><button onclick="check('${{ex.highlight}}')">判定</button>`;
}}

function check(ans){{
    const v=document.getElementById("ans").value.trim().toLowerCase();
    if(v==ans.toLowerCase())alert("正解");
    else alert("正解: "+ans);
    currentIndex++;
    if(currentIndex>=quizWords.length)finish();
    else showQuestion();
}}

function finish(){{
    alert("終了");
    location.reload();
}}
</script>

</body>
</html>
"""


    with open(output_file,"w",encoding="utf-8") as f:
        f.write(html)

    print("exercise.html generated")


if __name__=="__main__":
    generate_html()
