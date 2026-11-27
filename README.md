# GOSAT TRACKER — いまGOSATはどこ？

温室効果ガス観測技術衛星「いぶき」シリーズ（GOSAT、GOSAT-2、GOSAT-GW）の現在位置、地上軌跡、近傍通過時刻をブラウザで確認できる静的Webアプリです。

アプリは [GitHub Pages](https://ishida-works.github.io/gosat-tracker/) で閲覧できます（Pages の公開設定が完了している場合）。

## できること

- GOSAT、GOSAT-2、GOSAT-GW の現在位置・高度・昼夜の状態を表示
- 過去 50 分と今後 100 分の地上軌跡を 2D 地図／3D 地球儀で表示
- 指定地点の半径 100 / 300 / 500 km 内を通過する時刻を、72 時間先まで検索
- 地図をクリックして観測地点を変更、またはブラウザの現在地を使用
- 3D 表示で地球、月、太陽、恒星、星座線を確認

## 使い方

このアプリはビルド不要です。Python 3 で最新の軌道要素（TLE）を取得してから、ローカル Web サーバーで開きます。

```powershell
git clone https://github.com/ishida-works/gosat-tracker.git
cd gosat-tracker
python fetch_tle.py --source celestrak
python -m http.server 8000
```

ブラウザで <http://localhost:8000> を開いてください。

`data/tle.json` がない場合もデモ用の埋め込み TLE で起動しますが、位置は大きくずれるため、利用前に取得してください。

## 軌道データの更新

TLE は数日で精度が落ちます。1 日に 1〜数回を目安に更新してください。短時間で何度も取得しないでください。

```powershell
# CelesTrak から取得（推奨）
python fetch_tle.py --source celestrak

# 既定の N2YO から取得
python fetch_tle.py

# 手元の TLE テキストから作成
python fetch_tle.py --manual path\\to\\tle.txt
```

生成される `data/tle.json` は更新データのため Git には登録しません。

## GitHub Pages での公開

`main` ブランチへの push と約 12 時間ごとに、GitHub Actions が CelesTrak から軌道データを取得し、静的サイトを GitHub Pages へデプロイします。Actions タブから手動実行することもできます。

初回だけ、リポジトリの **Settings → Pages → Build and deployment → Source** で **GitHub Actions** を選択してください。公開後の URL は次のとおりです。

<https://ishida-works.github.io/gosat-tracker/>

軌道データの取得に失敗した場合、デプロイは失敗し、最後に公開されたサイトが残ります。Actions タブで実行結果を確認してください。

## 技術とデータ

- 軌道計算: [satellite.js](https://github.com/shashwatak/satellite-js)
- 3D 描画: [three.js](https://threejs.org/)
- 地図データ: [world-atlas](https://github.com/topojson/world-atlas)
- 地球画像: NASA Blue Marble / Black Marble（`three-globe` 同梱データ）
- TLE 取得元: [CelesTrak](https://celestrak.org/)、[N2YO](https://www.n2yo.com/)

位置・通過時刻は公開されている TLE に基づく計算値であり、実際の観測地点や運用情報を示すものではありません。

## ライセンス

ライセンスは未設定です。利用条件を定める場合は `LICENSE` を追加してください。
