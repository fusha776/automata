# AUTOMATA

自動でInstagramを操作する的なやつ


# どちゃくそ参考になるページ

---

[SeleniumでChromeのユーザープロファイルを指定しつつ同時に自分もChromeを使う方法](https://qiita.com/Hidenatsu/items/e43ba04b4b5f710784e6)

[Python + Selenium + Chrome で自動ログインいくつか](https://qiita.com/memakura/items/dbe7f6edadd456da1c5d)

[【完全版】PythonとSeleniumでブラウザを自動操作(クローリング／スクレイピング)するチートシート](https://tanuhack.com/selenium/)

[Selenium webdriverよく使う操作メソッドまとめ](https://qiita.com/mochio/items/dc9935ee607895420186)
[Chromeのコンソール上でXPathのテストをする](https://dangerous-animal141.hatenablog.com/entry/2015/02/07/101251)

### XPath 関連

[XPathのまとめ、要素の参照方法いろいろ](https://webbibouroku.com/Blog/Article/xpath)
[クローラ作成に必須！XPATHの記法まとめ](https://qiita.com/rllllho/items/cb1187cec0fb17fc650a)


### 待機時間 関連

[Seleniumで待機処理するお話](https://qiita.com/uguisuheiankyo/items/cec03891a86dfda12c9a)
[Selenium WebDriver と Chrome で StaleElementReferenceError が頻発するようになったので対処した](https://blog.fkoji.com/2015/07281859.html)
[【完全版】PythonとSeleniumでブラウザを自動操作(クローリング／スクレイピング)するチートシート](https://tanuhack.com/selenium/#i-19)

### ajax 関連
[Python selenium webdriver - stop a repeating AJAX request](https://stackoverflow.com/questions/40956676/python-selenium-webdriver-stop-a-repeating-ajax-request)


# コマンド集

---

### プロファイルのディレクトリを指定してChromeを起動

"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\Users\bell\python\project\insta\chrome_profiles" --disk-cache-size="104857600" 


### ajaxを一時停止

```
window.oSend=XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(){console.log('stopped ajax request', arguments)};
```

### 復旧

```
window.jQuery=window.oldjQuery;window.$=window.jQuery;XMLHttpRequest.prototype.send=window.oSend
```

# メモ

### アクションブロック

かなりすぐポップしてページ移動で消える  
アクション後に確認させるか、ページ移動のタイミングで確認させるかだけど、
アクション後の方が出入り口が絞られて良さそう
