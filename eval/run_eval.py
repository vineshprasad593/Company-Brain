import json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ai"))
from answer import answer

cases = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

# optional: python eval/run_eval.py 11 12 13   runs only those question numbers
wanted = {int(a) for a in sys.argv[1:] if a.isdigit()}
passed = ran = 0

for number, case in enumerate(cases, 1):
    if wanted and number not in wanted:
        continue
    r = answer(case["q"], case.get("role", "employee"))
    err = str(r.get("error", ""))
    if r["type"] == "error" and ("429" in err or "rate limit" in err.lower()):
        print(f"STOPPED at question {number}: Groq rate limit reached. Try again later.")
        break
    ran += 1
    problems = []
    if "route" in case and r["route"] != case["route"]:
        problems.append(f"route was {r['route']}, wanted {case['route']}")
    if r["type"] != case["type"]:
        problems.append(f"type was {r['type']}, wanted {case['type']}")
    for text in case.get("contains", []):
        if text.lower() not in r["answer"].lower():
            problems.append(f"answer is missing '{text}'")
    if problems:
        print(f"FAIL {number}:", case["q"])
        for p in problems:
            print("      ", p)
    else:
        passed += 1
        print(f"PASS {number}:", case["q"])
    time.sleep(2)

print(f"\n{passed} of {ran} passed")