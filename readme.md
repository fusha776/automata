### 参考ページ

[Androidテスト自動化のためにappiumを導入(windows+python)](https://qiita.com/exp/items/bdf06a388f30a1726984)

### 商用フリーの写真サイト
https://www.pakutaso.com/animal/cat/
https://pixabay.com/ja/
https://www.photock.jp/

### Tips

DOM (webElement) の使いまわしは基本的に控えた方が良い
描画が一回走りなおすと、前のODMをもう一度使える可能性はだいぶ低い

node でインストールするものは全て、`npm install -g` で実行する必要がある  
外部から実行されるようで、ローカルインストールだとうまく参照できない

opencv のインストールで cmake が必要になり、たぶん Python2 が必要になる
[Windows Global Install for opencv4nodejs](https://gist.github.com/adwellj/61e7f202bcfe5b96f312293e9c812ca6)

uiautomatorviewer の格納先
`<%AppData%>\Local\Android\Sdk\tools`

appium の実装が描いてある
[【Android】AppiumでAndroidのテストを自動化する](https://qiita.com/takumi0620/items/c08f81d5cbed7872e137)

[android端末上でテストを行う](https://www.htmlhifive.com/conts/web/view/library/android-test-appium-command)

sqlite3について
https://stackoverflow.com/questions/19522505/using-sqlite3-in-python-with-with-keyword