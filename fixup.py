"""Re-read only the school papers and merge them into the finished build."""
import collections, json, re, sys
import build
sys.path.insert(0, "/Users/khaledalseiari/foq/ial-quiz-private")
import extract, predict, topics

papers, skipped = build.school_papers()
print(len(papers), "school papers; skipped:", skipped, flush=True)
full = json.load(open("pdfs/manifest.json"))
public = [p for p in full if "2026" not in p["session"]]
prev = [q for q in json.load(open("data/questions.json")) if "2026" not in q["session"]]
json.dump(papers, open("pdfs/manifest.json", "w"), indent=1)
extract.main()
json.dump(public + papers, open("pdfs/manifest.json", "w"), indent=1)
school = json.load(open("data/questions.json"))
raw = [q for q in json.load(open("data/raw_questions.json")) if "2026" not in q["session"]] + school
json.dump(raw, open("data/raw_questions.json", "w"), separators=(",", ":"))

series = [{**q, "session": re.sub(r" [AR]$", "", q["session"])} for q in raw]
specs = dict(predict.SPECS)
broad = {**topics.TOPICS, **{("Business", u): v for u, v in build.BUSINESS.items()}}
for key, spec in broad.items():
    specs.setdefault(key, {t: ("Broad topic", build.clean(w)) for t, w in spec.items()})
order = ["Maths", "Physics", "Chemistry", "Biology", "Economics", "Business", "Psychology"]
index = []
for (subject, unit), spec in sorted(specs.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1])):
    out = predict.analyse(series, subject, unit, spec)
    key = f"{subject.lower()}_{unit.lower()}"
    json.dump(out, open(f"data/predict_{key}.json", "w"), separators=(",", ":"))
    index.append({"key": key, "subject": subject, "unit": unit, "papers": len(out["sessions"]),
                  "from": out["sessions"][0], "to": out["sessions"][-1]})
json.dump(index, open("data/predict_index.json", "w"), indent=1)

known = topics.COMPILED
topics.COMPILED = collections.defaultdict(dict, known)  # units without a topic list become "Other"
topics.COMPILED.update({("Business", u): topics.compile_topics(s) for u, s in build.BUSINESS.items()})
topics.main()  # data/questions.json holds only the school papers at this point
tagged = json.load(open("data/questions.json"))
json.dump(prev + tagged, open("data/questions.json", "w"), separators=(",", ":"))
print("final", len(prev) + len(tagged), flush=True)
