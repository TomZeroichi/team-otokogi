# TEAM狭気 — GitHub導入とLINE共有の手順

## 1. GitHubリポジトリ（作成済み）

リポジトリ：`TomZeroichi/team-otokogi`（Private）。
URL： https://github.com/TomZeroichi/team-otokogi
表示名は **TEAM狭気** のままです。

## 2. GitHubで管理するもの

- `app.py`：Python FastAPI / SQLite の共有バックエンド
- `static/index.html`, `static/style.css`, `static/app.js`：和風スマホ用UI
- `tests/`：男気・通常ルール、ルール決定権、集計元データ、権限のテスト
- `.github/workflows/ci.yml`：Push / PR時の自動テスト
- `Dockerfile`：ホスティング用のビルド定義

`data/` 内の認証・戦績データベースはGitHubへアップロードしてはいけません。

## 3. GitHubだけでオンライン共有できる？

いいえ。`GitHub Pages` は静的ファイル配信なので、FastAPI+SQLiteを動かせません。
オンライン共有にはアプリサーバーと永続ディスクが必要です。

## 4. Railwayでオンライン公開（次の段階）

1. Railwayで **Deploy from GitHub repo** に `TomZeroichi/team-otokogi` を指定します。
2. Dockerfileでビルドされることを確認します。
3. **Volumeを作成し、Mount Pathを `/data` に設定**（必須）。
4. Environment Variablesで `DATA_DIR=/data`, `COOKIE_SECURE=1` を指定します。
5. RailwayのHTTPS公開ドメインを発行します。
6. `/health` が `{"ok":true}` と返すことを確認します。
7. 初回アクセスで管理者がグループを作成し、アプリ内招待URLをLINEグループに貼ります。

**重要**：ボリュームを作らず公開すると、サービス更新などの際に戦績が消える可能性があります。

## 5. 既存の仕様

- 男気：じゃんけん勝者が全額支払い
- 通常：じゃんけん敗者が全額支払い
- 次回ルールは最終敗者だけが選択
- 収支・勝率・敗戦・支払金額などの集計
- 管理者による過去データ入力と削除
- 招待URL+名前+6桁暗証番号で参加
- ブラウザ約20秒間隔の更新

## 6. セキュリティと運用

- 招待URLの漏えいに注意してください。
- 6桁PINによる簡易認証のため機密情報や決済情報は登録しないでください。
- DBはVolume上に配置し定期バックアップを取ってください。
- Railwayの無料枠・料金・ボリューム利用可能条件はデプロイ前に確認してください。
