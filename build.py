"""Private build: public papers + the school-provided 2026 papers. Never publish this folder."""
import collections, glob, json, os, re, shutil, sys

PUBLIC = "/Users/khaledalseiari/foq/ial-quiz"
sys.path.insert(0, PUBLIC)
MONTHS = {"Jan": "January", "June": "June", "Jun": "June", "Oct": "October", "May": "June"}
NAME = re.compile(r"^(\w+) (Jan|June|Jun|Oct|May) (\d{4}) ([A-Z]+\d*?)([AR]?) (QP|MS)\.pdf$")


def school_papers():
    found, skipped = collections.defaultdict(dict), []
    for f in glob.glob("src/**/*.pdf", recursive=True):
        if "__MACOSX" in f:
            continue
        m = NAME.match(os.path.basename(f))
        if not m:
            skipped.append(f)
            continue
        subject, mon, year, unit, variant, kind = m.groups()
        session = f"{MONTHS[mon]} {year}" + (f" {variant}" if variant else "")
        found[(subject, unit, session)][kind] = f
    papers = []
    for (subject, unit, session), files in sorted(found.items()):
        if len(files) < 2:
            skipped.append(str(files))
            continue
        row = {"subject": subject, "unit": unit, "session": session}
        for kind, f in files.items():
            k = kind.lower()
            dest = f"pdfs/{subject}/{unit}/{session.replace(' ', '_')}_{k}.pdf"
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(f, dest)
            row[k], row[k + "_url"] = dest, dest
        papers.append(row)
    return papers, skipped


def clean(words):
    return ", ".join(w.strip() for w in words.split(",") if len(w.strip()) >= 2 and not w.strip().isdigit())


def main():
    papers, skipped = school_papers()
    print(len(papers), "school papers; skipped:", skipped)
    public = json.load(open(f"{PUBLIC}/pdfs/manifest.json"))
    for p in public:
        p["qp"], p["ms"] = f"{PUBLIC}/{p['qp']}", f"{PUBLIC}/{p['ms']}"
    os.makedirs("data", exist_ok=True)
    json.dump(public + papers, open("pdfs/manifest.json", "w"), indent=1)

    import extract, predict, topics
    if "--skip-extract" in sys.argv:  # reuse the last extraction when only the analysis changed
        shutil.copyfile("data/raw_questions.json", "data/questions.json")
    else:
        extract.main()
        shutil.copyfile("data/questions.json", "data/raw_questions.json")

    items = json.load(open("data/questions.json"))
    # a paper and its "A" variant sit in the same exam series for the Predicted analysis
    series = [{**q, "session": re.sub(r" [AR]$", "", q["session"])} for q in items]
    index = []
    # units without a hand-written spec-point list are analysed at topic level
    specs = dict(predict.SPECS)
    broad = {**topics.TOPICS, **{("Business", u): v for u, v in BUSINESS.items()}}
    for key, spec in broad.items():
        specs.setdefault(key, {t: ("Broad topic", clean(w)) for t, w in spec.items()})
    order = ["Maths", "Physics", "Chemistry", "Biology", "Economics", "Business", "Psychology"]
    for (subject, unit), spec in sorted(specs.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1])):
        if not any(q["subject"] == subject and q["unit"] == unit for q in series):
            continue
        out = predict.analyse(series, subject, unit, spec)
        key = f"{subject.lower()}_{unit.lower()}"
        json.dump(out, open(f"data/predict_{key}.json", "w"), separators=(",", ":"))
        index.append({"key": key, "subject": subject, "unit": unit, "papers": len(out["sessions"]),
                      "from": out["sessions"][0], "to": out["sessions"][-1]})
    json.dump(index, open("data/predict_index.json", "w"), indent=1)

    known = topics.COMPILED
    topics.COMPILED = collections.defaultdict(dict, known)  # units without a topic list become "Other"
    topics.COMPILED.update({("Business", u): topics.compile_topics(s) for u, s in BUSINESS.items()})
    topics.main()

    for f in ("index.html", "predicted.html"):
        shutil.copyfile(f"{PUBLIC}/{f}", f)
    s = open("index.html").read()
    a = '["Maths", "Physics", "Chemistry", "Biology", "Economics"]'
    assert a in s
    open("index.html", "w").write(s.replace(a, '["Maths", "Physics", "Chemistry", "Biology", "Economics"]'))


MARKETING = "marketing:5, market research:5, segmentation:5, market share:5, marketing mix:5, product life cycle:5, boston matrix:5, promotion:4, branding:4, price elasticity:4, demand:2, supply:2"
PEOPLE = "motivation:5, leadership:5, recruitment:5, training:4, organisational structure:5, herzberg:5, maslow:5, taylor:5, span of control:5, delegation:5, employee:3, staff:2, entrepreneur:5, business objective:4"
FINANCE = "cash flow:5, break-even:5, break even:5, budget:4, profit margin:5, gross profit:5, income statement:5, statement of financial position:5, liquidity:5, current ratio:5, source of finance:5, revenue:2, costs:2"
OPERATIONS = "capacity utilisation:5, productivity:5, lean production:5, just-in-time:5, jit:5, kaizen:5, quality:4, stock control:5, inventory:4, efficiency:3, supply chain:5"
STRATEGY = "corporate strategy:5, ansoff:5, porter:5, swot:5, pestle:5, decision tree:5, investment appraisal:5, payback:5, net present value:5, average rate of return:5, merger:5, takeover:5, corporate culture:5, change:2, stakeholder:4"
GLOBAL = "globalisation:5, multinational:5, mnc:5, emerging econom:5, exchange rate:5, tariff:5, trade bloc:5, protectionism:5, foreign direct investment:5, fdi:5, offshoring:5, outsourcing:4, glocalisation:5, ethics:4, export:3, import:3"
BUSINESS = {
    "U1": {"Marketing": MARKETING, "People & entrepreneurs": PEOPLE},
    "U2": {"Finance": FINANCE, "Operations": OPERATIONS, "Marketing": MARKETING},
    "U3": {"Strategy & decisions": STRATEGY, "Finance": FINANCE, "People & entrepreneurs": PEOPLE},
    "U4": {"Global business": GLOBAL, "Strategy & decisions": STRATEGY, "Marketing": MARKETING},
}

if __name__ == "__main__":
    main()
