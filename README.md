# mo-code-4koma
道草屋バックヤード漫画の配信用

### VRChat向けの simple 版

Python 3.10以降で、原本と既存の `4komaData.json` を変更せず、
原本と同じ画像構成のコピーと、対応する `4komaDataSimple.json` を生成できます。
1話1画像への結合は行いません。

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-simple.txt
python generate-simple.py
```

- 出力画像: `4koma/ja/simple/<元画像の相対パス>`
- 公開パス例: `/4koma/ja/simple/404-1.jpg`
- 公開JSON: `/4komaDataSimple.json`
- `Title`・`BaseUrl`・`Index`・話順と、`ImagesUrl` の件数・順序を保持します。
- 画像パスだけを `./simple/` 配下のコピー先に置き換えます。

`ImagesUrl` は既存JSONと同じく、日本語画像ディレクトリ `/4koma/ja/` を基準にします
（JSON自身からの相対パスではありません）。たとえば第404話は次のようになります。

```json
{
  "Title": "同じ穴",
  "BaseUrl": "http://momoirocode.web.fc2.com/4koma/404.html",
  "ImagesUrl": [
    "./simple/404-1.jpg",
    "./simple/404-2.jpg",
    "./simple/404-3.jpg",
    "./simple/404-4.jpg",
    "./simple/sp.jpg"
  ],
  "Index": 404
}
```

各画像は縦横とも2048px以下ならバイト列を変えずにコピーします。
どちらかが上限を超える場合だけ、縦横比を保ち、長辺が2048px以内になるよう
Lanczosフィルターで縮小します。拡大・切り抜き・分割・余白調整は行いません。
縮小するJPEGは品質95・色差サブサンプリングなし（4:4:4）で保存します。
空白画像（`sp.jpg` など）も除外せず、共有画像は1ファイルだけコピーして各参照を保ちます。
元画像がサブディレクトリにある場合も、その相対パスを保持します。

```sh
python generate-simple.py --max-dimension 2048 --quality 95
# さらに小さい上限も指定可能（2048を超える指定は不可）
python generate-simple.py --max-dimension 1024
```

同じ入力・設定・Pillow版なら出力は同じになり、変更のないファイルは書き換えません。
元画像の欠落・破損・危険なパスがあれば、既存のJSON・画像を更新する前に停止します。
生成完了後、参照されなくなった画像や旧結合画像は `simple/` 内から削除します。
同じファイル名が原本にもある場合は、結合画像を原本のコピーで置き換えます。
旧版の `--no-trim`・`--threshold`・`--max-width`・`--gap`・`--padding` は廃止しました。

`NewUpdate`・`SkipFeed`・`GenerateWebP` でも原本の更新後に自動生成・コミットします。
手動再生成は GitHub Actions の **Generate simple episodes** → **Run workflow** でも実行できます。
スクリプトや設定を変更した場合は、生成結果も再生成してコミットしてください。

開発時の検証:

```sh
python -m pip install -r requirements-dev.txt
ruff check generate-simple.py test_generate_simple.py
ruff format --check generate-simple.py test_generate_simple.py
mypy generate-simple.py --check-untyped-defs
python -m unittest -v
```

### 透過画像を重ねる

[みちくさびゅあー](https://iranika.github.io/mo-code/)は多言語対応を目的として、画像の重ね表示(overlay)に対応しました。  
これにより、ビュアーで元画像の上に翻訳版の透過画像(gif)を重ねて表示することできるようになりました。  
次の画像は元画像に白吹き出しを重ねて表示した例です。  

![](./overlay.gif)

現在は英語および中文繁体字の翻訳を対象にしていますが、他にも面白い利用ができるかもしれません。  
(関西弁やおもしろ吹き出し等)
もし何かをビュアーで表示させたい場合は、issueもしくはいらにか([@happy_packet](https://twitter.com/happy_packet))までご連絡ください。

### 翻訳作業への参加

翻訳作業に協力していただけるボランティアを募集しています。  
興味がある人はiranika[@happy_packet](https://twitter.com/happy_packet)までご連絡ください。  
Discordもありますので、ぜひJoinしてみてください。  
https://discord.gg/nfg3nZv

大まかに漫画の翻訳からリリースまでの流れを説明します。

1. 画像のダウンロード  
このリポジトリの[ここ](https://github.com/iranika/mo-code-4koma/tree/master/4koma/ja)から翻訳する画像を選んで、ダウンロードします。  
すべてのファイルをダウンロードしたい場合は、[このリンクをクリック](https://github.com/iranika/mo-code-4koma/archive/master.zip)してリポジトリ全てをダウンロードしてください。

1. 画像の加工（翻訳）  
翻訳する画像をGIMPやPhotoshop等のお好みの画像編集ソフトで加工します。  
翻訳にあたっての制約事項は下記の通りです。  
    - 保存時の名前は元画像と同じにしてください。
    - 可能な限り画像サイズ(縦横比率）は元画像と同じにしてください。
    - 画像はGIF形式で保存してください。  
    もしGIF形式で保存ができない人は、iranika[@happy_packet](https://twitter.com/happy_packet)までご連絡ください。  

1. 動作チェック  
翻訳データを元画像に重ねて表示したときの動作を確認します。  
https://github.com/iranika/mo-code-local/archive/master.zip  
上記のツールをダウンロードして、翻訳画像をビュアーで表示したときにどうなるか動作チェックができます。  
例えば中文繁体字で1.jpgを翻訳する場合は下記のように確認できます。
    1. 'mo-code-local/mo-code/mo-code-4koma/4koma/zh-tw/'に翻訳データ（1.gif)を保存します。
    2. 'mo-code-local/index.html'をChrome等のWEBブラウザで開きます。
    3. ビュアー右上のメニューから、言語「中文繁体字」を選ぶと翻訳データが元画像の上に表示されます。
    4. 翻訳データが正しく表示されているかチェックします。  
    もし、この工程が難しい場合はiranika[@happy_packet](https://twitter.com/happy_packet)までご連絡ください。  

1. 画像のアップロード  
Google DriveやNextCloudに共有フォルダがあります。  
共有フォルダのURLが知りたい人はiranika[@happy_packet](https://twitter.com/happy_packet)までご連絡ください。  
それ以外にも、Twitterで翻訳画像をDMで送ってもOKです。

#### 翻訳時の推奨ルール

- 貴方が何かしらの理由でこの推奨ルールを破るとき、私はそれを非難しません。  
このルールはクオリティマネジメントのために存在し、貴方の生み出すクオリティがルールを守ることで下がるのであれば、ルールを破って構いません。  
ただ、特に理由がなければ貴方は推奨ルールを守るべきです。  
統一されたルールは安定したクオリティを生み出すために効果的です。

何か問題があれば都度、ルールを定めて共有します。 
