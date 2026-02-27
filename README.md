# 📚 勉強ツールまとめ

学習効率を上げるためのツール・サービスを厳選してまとめたサイトです。

## 🌐 サイトURL

https://useful-study-tools.github.io/study/

---

## 📖 サイト概要

このサイトでは、勉強ツールをカテゴリ別に作成しています。
高校生に向けて、実際に使ってみて役立ったものだけを掲載しています。

---

## 📂 ページ構成

### 📖 英単語帳ページ

英単語を単語番号で引けるページです。複数の単語帳データをJSONファイルで管理しています。`/exercise.html` では単語の演習も行えます。

| 単語番号 | JSONファイル番号 | 対応単語帳 |
|---|---|---|
| 1 〜 2000 | `english-dictionary/vocabulary_data_01.json` 〜 `_48.json` | 速読英単語 |
| 3974 〜 4973 | `english-dictionary/vocabulary_data_51.json` 〜 `_60.json` | 東進上級英単語 |
| 10001 〜 11935 | `english-dictionary/vocabulary_data_100.json` 〜 `_119.json` | LEAP |

> JSONファイル名の番号は単語帳の通し番号ではなく、ファイル管理用の番号です（例：`vocabulary_data_01.json`）。

---

### 🛠️ 便利ツールまとめページ

日常の学習・作業で役立つWebツールをまとめたページです。

- **PDF編集ツール** — PDFの結合・分割・圧縮・変換などができるツールを紹介
- **音楽再生ツール** — 作業BGMや集中用ミュージックを手軽に流せるツールを紹介

---

## 🗂️ ファイル構成

```
study-tools/
├── index.html                        # トップページ
├── english-dictionary/               # 英単語帳ページ
│   ├── index.html
│   ├── exercise.html                 # 演習ページ
│   ├── vocabulary_data_01.json       # 速読英単語（単語番号 1〜）
│   ├── vocabulary_data_02.json
│   ├── ...
│   ├── vocabulary_data_48.json       # 速読英単語（〜単語番号 2000）
│   ├── vocabulary_data_51.json       # 東進上級英単語（単語番号 3974〜）
│   ├── ...
│   ├── vocabulary_data_60.json       # 東進上級英単語（〜単語番号 4973）
│   ├── vocabulary_data_100.json      # LEAP（単語番号 10001〜）
│   ├── ...
│   └── vocabulary_data_119.json      # LEAP（〜単語番号 11935）
├── tools/                            # 便利ツールまとめページ
│   ├── index.html                    # ツール一覧
│   ├── pdf.html                      # PDF編集ツール
│   └── music.html                    # 音楽再生ツール
└── README.md
```

---

## 🛠️ 使用技術

```
HTML / CSS / JavaScript / Python
```

---

## 🚀 ローカルで動かす方法

```bash
# リポジトリをクローン
git clone https://github.com/useful-study-tools/study.git

# ディレクトリに移動
cd study

# ブラウザで開く（静的サイトの場合）
open index.html
```

---

## 📝 掲載ツールの追加・修正について

掲載希望のツールや情報の誤りがある場合は、以下の方法でご連絡ください。

- **Issue** を立てる（GitHub をお使いの場合）
- **Pull Request** を送る

---

## 📌 注意事項

- 掲載しているツールの情報は執筆時点のものです。最新情報は各サービスの公式サイトをご確認ください。

---

## 👤 作者

- **名前**：secret🥰

---

## 🕒 最終更新

2026年2月27日
