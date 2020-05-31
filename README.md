# mo-code-4koma
道草屋バックヤード漫画の配信用

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
