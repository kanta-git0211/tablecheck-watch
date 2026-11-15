# tablecheck-watch

eman・静龍苑（2名）の空き状況を GitHub Actions で **5分おき・24時間** 確認する。
空きが出たら、スマホの ntfy アプリにプッシュ通知が届く。通知を押すと予約ページが開く。

## セットアップ（1回だけ・約10分）

### 1. スマホに ntfy を入れる
- App Store で「ntfy」を入れる（無料・登録不要）
- 「+」→ Topic name に **`kanta-tc-db5c694c906e`** を入れて Subscribe

### 2. GitHub にリポジトリを作る
- github.com →「New repository」→ 名前 `tablecheck-watch`
- **Public（公開）を選ぶ**
  - Private だと無料枠（月2000分）を5日ほどで使い切り、監視が止まる。Public なら無制限
  - 公開されるのはこのスクリプトだけ。通知先の名前は手順3で非公開の設定に入れる
- 「uploading an existing file」から、このフォルダの `watch.py`・`README.md`・`.github` フォルダをアップロード
  - `.github` は隠しフォルダ。Finder で表示されない場合は ⌘+Shift+. を押す

### 3. 通知先を非公開の設定に入れる
- リポジトリの Settings → Secrets and variables → Actions → New repository secret
- Name: `NTFY_TOPIC`　Secret: `kanta-tc-db5c694c906e`

### 4. 動作確認
- Actions タブ → tablecheck-watch →「Run workflow」
- 1〜2分後にスマホへ「テスト通知です」が届けばOK
- 実行結果に「eman: 確認した週 …／空き なし」と出ていれば、監視も正常

以降は5分おきに自動で動く。

## 注意
- GitHub の混雑で、実行が数分遅れることがある
- 公開リポジトリは、60日間更新がないとスケジュール実行が自動で止まる。止まったら Actions タブから再開する
- 赤い×（失敗）が続くときは、ページの作りが変わったか、GitHub からのアクセスが弾かれている
