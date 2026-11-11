"""Whole Maths questions take every mark-scheme section for that number; Business gets its source extracts."""
import json, re, sys
sys.path.insert(0, "/Users/khaledalseiari/foq/ial-quiz"); sys.path.insert(0, ".")
import extract as E

items = json.load(open("data/questions.json"))
manifest = {(p["subject"], p["unit"], p["session"]): p for p in json.load(open("pdfs/manifest.json"))}
changed = lost = ctx = 0
by_paper = {}
for q in items:
    by_paper.setdefault((q["subject"], q["unit"], q["session"]), []).append(q)
for key, qs in by_paper.items():
    paper = manifest[key]
    if key[0] == "Maths":
        ms = E.parse_ms(paper["ms"])
        for q in qs:
            n = int(re.match(r"Q(\d+)", q["label"]).group(1))
            crops = sorted({tuple(c) for (mq, _), cs in ms.items() if mq == n for c in cs}, key=lambda c: (c[0], c[2]))
            if not crops:
                lost += 1
                continue
            crops = [list(c) for c in crops]
            if crops != q["a"]:
                q["a"] = crops
                changed += 1
    if key[0] == "Business":
        inserts = E.insert_pages(paper["qp"])
        for q in qs:
            if inserts and re.search(r"\bExtract\b|\bFigure\b", E.crop_text(paper["qp"], q["stem"] + q["q"])):
                q["ctx"] = inserts
                ctx += 1
json.dump(items, open("data/questions.json", "w"), separators=(",", ":"))
print("maths mark schemes corrected", changed, "| no sections found (left as they were)", lost, "| business cards given extracts", ctx)
q = next(x for x in items if x["id"] == "Mat-P3-June2026A-5"); print(q["a"])
