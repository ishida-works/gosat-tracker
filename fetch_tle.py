#!/usr/bin/env python3
"""最新のTLEを data/tle.json に保存する。

使い方:
  python3 fetch_tle.py                      # n2yo.com の衛星ページから取得(既定)
  python3 fetch_tle.py --source celestrak   # CelesTrakから取得
  python3 fetch_tle.py --manual FILE        # コピーしたTLEのテキストから作成

TLEは数日で古くなるが、取得は1日に1〜数回で十分。短時間に繰り返し実行しないこと。
プロキシが必要な環境では、先に export https_proxy=http://ホスト:ポート を設定する。
"""
import argparse
import datetime
import html
import json
import pathlib
import re
import time
import urllib.request

IDS = {"33492": "GOSAT (IBUKI)", "43672": "GOSAT-2 (IBUKI-2)", "64694": "GOSAT-GW"}
URLS = {
    "n2yo": "https://www.n2yo.com/satellite/?s={}",
    "celestrak": "https://celestrak.org/NORAD/elements/gp.php?CATNR={}&FORMAT=tle",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (gosat-tracker; personal use)"}


def checksum(s):
    """先頭68文字の数字の和(「-」は1)を10で割った余り。"""
    return sum(int(c) if c.isdigit() else 1 if c == "-" else 0 for c in s[:68]) % 10


def fix(line):
    """TLE 1行を検証して返す。空白が詰まっていれば固定桁に直す。不正ならNone。"""
    line = line.strip()
    if len(line) == 69 and line[68].isdigit() and checksum(line) == int(line[68]):
        return line
    t = line.split()
    try:
        if t[0] == "1":
            elem, cks = t[8][:-1], t[8][-1]
            out = (f"1 {t[1]:<6} {t[2]:<8} {t[3]:>14} {t[4]:>10} {t[5]:>8} "
                   f"{t[6]:>8} {t[7]} {elem:>4}{cks}")
        else:
            mm, rest = (t[7][:11], t[7][11:]) if len(t) == 8 else (t[7], t[8])
            out = (f"2 {t[1]} {t[2]:>8} {t[3]:>8} {t[4]:>7} {t[5]:>8} "
                   f"{t[6]:>8} {mm:>11}{rest[:-1]:>5}{rest[-1]}")
        if len(out) == 69 and checksum(out) == int(out[68]):
            return out
    except (IndexError, ValueError):
        pass
    return None


def parse(text):
    """テキストから {カタログ番号: (1行目, 2行目)} を取り出す(衛星名の行などは無視)。"""
    out = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for a, b in zip(lines, lines[1:]):
        if a.startswith("1 ") and b.startswith("2 "):
            fa, fb = fix(a), fix(b)
            if fa and fb and fa[2:7] == fb[2:7]:
                out[fa[2:7].strip()] = (fa, fb)
            else:
                print("警告: 形式またはチェックサムが不正なため読み飛ばしました:\n  ", a)
    return out


def page_text(page):
    """HTMLのタグを改行に置き換えてテキスト化する。"""
    return html.unescape(re.sub(r"<[^>]+>", "\n", page)).replace("\xa0", " ")


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


ap = argparse.ArgumentParser()
ap.add_argument("--source", choices=["n2yo", "celestrak"], default="n2yo")
ap.add_argument("--manual", metavar="FILE", help="TLEを貼り付けたテキストファイル")
args = ap.parse_args()

sats = {}
if args.manual:
    sources = {cat: parse(pathlib.Path(args.manual).read_text(encoding="utf-8")) for cat in IDS}
else:
    sources = {}
    for i, cat in enumerate(IDS):
        if i:
            time.sleep(2)  # 相手サーバーに負担をかけない
        try:
            page = get(URLS[args.source].format(cat))
            sources[cat] = parse(page_text(page))
        except Exception as e:
            sources[cat] = {}
            print("FAIL", cat, IDS[cat], repr(e))

for cat, name in IDS.items():
    if cat in sources.get(cat, {}):
        l1, l2 = sources[cat][cat]
        sats[cat] = {"name": name, "l1": l1, "l2": l2}
        print("OK  ", cat, name, " epoch:", l1[18:32])
    else:
        print("なし", cat, name)

if not sats:
    print("\nTLEを1件も取得できませんでした。既存の data/tle.json は変更していません。")
    print("・WSL側のpython3で実行しているか、プロキシ設定が必要かを確認")
    print("・--source を切り替えるか、--manual でコピーしたTLEを渡すこともできます")
    raise SystemExit(1)

out = pathlib.Path(__file__).parent / "data" / "tle.json"
out.parent.mkdir(exist_ok=True)
out.write_text(
    json.dumps(
        {"fetched": datetime.datetime.now(datetime.timezone.utc).isoformat(), "sats": sats},
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)
print("saved:", out)
