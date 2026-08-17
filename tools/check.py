#!/usr/bin/env python3
"""Guesthouse Gamarjoba — 公開前ゲート。コミット前に必ず走らせる。
   通常:      python3 tools/check.py
   公開直前:  python3 tools/check.py --publish   ← 下書きの痕跡が残っていたら落ちる
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLISH = "--publish" in sys.argv
errors, warnings = [], []

pages = sorted(ROOT.glob("*.html"))
if not pages: errors.append("HTMLが1枚も無い")

assets = set()
for p in pages:
    s = p.read_text(encoding="utf-8")
    name = p.name

    # h1 は1ページに1つ
    n_h1 = len(re.findall(r"<h1\b", s))
    if name != "ui-catalog.html" and n_h1 != 1:
        errors.append(f"{name}: h1 が {n_h1} 個（1個であること）")

    # img には必ず alt
    for img in re.findall(r"<img\b[^>]*>", s):
        if 'alt="' not in img:
            errors.append(f"{name}: alt の無い img → {img[:70]}")
        elif re.search(r'alt=""', img):
            warnings.append(f"{name}: alt が空の img（装飾画像なら可）")

    # 参照アセットの実在
    for m in re.findall(r'(?:src|href)="(/assets/[^"]+)"', s):
        assets.add((name, m))
    for m in re.findall(r'srcset="([^"]+)"', s):
        for part in m.split(","):
            u = part.strip().split(" ")[0]
            if u.startswith("/assets/"): assets.add((name, u))

    # 内部アンカーの実在
    ids = set(re.findall(r'id="([^"]+)"', s))
    for a in re.findall(r'href="#([^"]+)"', s):
        if a and a not in ids:
            errors.append(f"{name}: 存在しないアンカー #{a}")

    # ---- 公開モードでのみ落とすもの ----
    if PUBLISH:
        if "draft-note" in s:
            errors.append(f"{name}: ⛔ 下書きの印 .draft-note が残っている（オーナー確認前の記述）")
        if "要確認" in s or "TODO" in s:
            errors.append(f"{name}: ⛔ 社内メモ（要確認 / TODO）が残っている")
        if 'content="noindex' in s and name != "404.html":
            errors.append(f"{name}: ⛔ noindex が残っている。公開版から外すこと")
        if 'plate--empty' in s:
            errors.append(f"{name}: ⛔ 空の額 .plate--empty が残っている（写真が未着の場所）")
        if 'href="#"' in s:
            errors.append(f"{name}: ⛔ 空リンク href=\"#\" が残っている")

if PUBLISH:
    r = ROOT / "robots.txt"
    if r.exists() and "Disallow: /" in r.read_text():
        errors.append("robots.txt: ⛔ 下書き用の Disallow: / が残っている。公開版では Allow: / にする")
    if (ROOT / "ui-catalog.html").exists():
        errors.append("ui-catalog.html: ⛔ 社内用。公開版に含めない")

for name, a in sorted(assets):
    if not (ROOT / a.lstrip("/")).exists():
        errors.append(f"{name}: 参照先が無い {a}")

print(f"checked {len(pages)} pages, {len(assets)} asset references"
      + ("  [PUBLISH MODE]" if PUBLISH else ""))
for w in warnings: print("  warn:", w)
if errors:
    print("\nFAILED:")
    for e in errors: print("  -", e)
    sys.exit(1)
print("\nall checks passed")
