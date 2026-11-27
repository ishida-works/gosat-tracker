# GOSAT TRACKER — いまGOSATはどこ？

温室効果ガス観測技術衛星「いぶき」シリーズ（GOSAT、GOSAT-2、GOSAT-GW）の現在位置、地上軌跡、近傍通過時刻をブラウザで確認できる静的Webアプリです。

公開先（設定完了後）: [いまGOSATはどこ？](https://ishida-works.github.io/gosat-tracker/)

## できること

- GOSAT、GOSAT-2、GOSAT-GW の現在位置・高度・昼夜の状態を表示
- 過去 50 分と今後 100 分の地上軌跡を 2D 地図／3D 地球儀で表示
- 指定地点の半径 100 / 300 / 500 km 内を通過する時刻を、72 時間先まで検索
- 地図をクリックして観測地点を変更、またはブラウザの現在地を使用
- 3D 表示で地球、月、太陽、恒星、星座線を確認

## TLE から位置を計算するしくみ

TLE（Two-Line Element set）は、ある基準時刻の衛星の軌道を表す2行のデータです。基準時刻、軌道傾斜角、昇交点赤経、離心率、近地点引数、平均近点角、平均運動、抗力項などが含まれます。アプリは、このデータを使って指定した時刻の衛星位置を計算します。

### 1. SGP4 で軌道を伝播する

TLE の基準時刻を $t_0$、計算したい時刻を $t$ とすると、基準時刻からの経過時間 $\Delta t$ は次のとおりです。

$$
\Delta t = \frac{t-t_0}{60} \quad [\mathrm{min}]
$$

ここで $t$ と $t_0$ は秒単位で表した時刻です。アプリでは [satellite.js 4.1.3](https://github.com/shashwatak/satellite-js/tree/v4.1.3) の `twoline2satrec` で TLE を読み込み、`propagate` で SGP4 軌道モデルを計算します。出力される位置 $\boldsymbol{r}$ と速度 $\boldsymbol{v}$ は、地球中心の TEME 座標系で表されます。

$$
\left(\boldsymbol{r}_{\mathrm{TEME}}(t),\ \boldsymbol{v}_{\mathrm{TEME}}(t)\right)
= \mathrm{SGP4}(\mathrm{TLE},\Delta t)
$$

$t$ に現在時刻を入れれば現在位置、未来の時刻を入れれば予測位置になります。過去の軌跡も同じ方法で計算します。SGP4 は地球の形状による摂動や大気抵抗などを考慮するモデルで、上式はその**計算処理全体を表す記法**です。単純なケプラー運動の式だけで TLE を伝播しているわけではありません。詳細なモデルと実装は [Revisiting Spacetrack Report #3](https://celestrak.org/publications/AIAA/2006-6753/) を参照してください。

### 2. 地球の自転を考慮して緯度・経度・高度に変換する

SGP4 の出力を $(x,y,z)$、計算時刻のグリニッジ平均恒星時を $\theta$ とすると、地球とともに回転する座標 $(x_f,y_f,z_f)$ は次の回転で表せます。

$$
\begin{aligned}
x_f &= x\cos\theta+y\sin\theta,\\
y_f &= -x\sin\theta+y\cos\theta,\\
z_f &= z.
\end{aligned}
$$

東経を正とする経度 $\lambda$ は、次のように求められます。`atan2` は象限を考慮した逆正接です。

$$
\lambda = \mathrm{atan2}(y_f,x_f)
$$

地球を球ではなく楕円体として扱い、測地緯度 $\phi$ と楕円体からの高度 $h$ を求めます。赤道半径を $a$、楕円体の離心率を $e$ とし、 $p=\sqrt{x_f^2+y_f^2}$ とおくと、次の関係を満たす $\phi$ を反復計算します。

$$
\begin{aligned}
N(\phi) &= \frac{a}{\sqrt{1-e^2\sin^2\phi}},\\
\phi &= \mathrm{atan2}\left(z_f+e^2N(\phi)\sin\phi,\ p\right),\\
h &= \frac{p}{\cos\phi}-N(\phi).
\end{aligned}
$$

実装では `gstime` と `eciToGeodetic` を使用します。位置と高度は km、内部の角度はラジアンで扱い、画面には緯度・経度を度単位で表示します。地図上の衛星位置は、この緯度・経度を地上に投影したものです。

### 3. 近くを通る時刻を探す

観測地点の緯度・経度を $(\phi_o,\lambda_o)$、衛星の直下点を $(\phi_s,\lambda_s)$ とし、地球を半径 $R=6371\ \mathrm{km}$ の球として、両地点の地表距離 $d$ を求めます。

$$
d=R\arccos\left(\sin\phi_o\sin\phi_s+\cos\phi_o\cos\phi_s\cos(\lambda_s-\lambda_o)\right)
$$

現在から72時間先まで時刻を進めて距離を調べ、指定半径内に入る区間ごとに、最も距離が小さい時刻を最大2件表示します。遠いときは1分刻み、近くでは5秒刻みの探索です。これは**衛星の直下点と指定地点の地表距離**であり、衛星を地上から目視できることや、実際に観測が行われることを保証するものではありません。

TLE は観測や軌道修正によって更新されるため、基準時刻から離れるほど予測誤差が大きくなる傾向があります。画面の軌道データの経過日数と警告もあわせて確認してください。

## 自分のパソコンで動かす場合（開発者向け）

このアプリはビルド不要です。Python 3 で最新の軌道要素（TLE）を取得してから、ローカル Web サーバーで開きます。

```powershell
git clone https://github.com/ishida-works/gosat-tracker.git
cd gosat-tracker
python fetch_tle.py --source celestrak
python -m http.server 8000
```

上記のサーバーを起動したパソコンのブラウザで `http://localhost:8000` を開いてください。これはローカル開発用で、他の人に共有できるアドレスではありません。

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
