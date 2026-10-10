import json, os, subprocess, sys, tempfile, threading

ASSIGNMENTS = {
    "Average of a List": {
        "func": "average",
        "desc": "Write average(nums) that returns the mean of a list. Return 0 for an empty list.",
        "starter": "def average(nums):\n    return sum(nums) / len(nums)\n",
        "tests": [([[1, 2, 3]], 2), ([[10]], 10), ([[-4, 4, 6]], 2), ([[]], 0)],
    },
    "Palindrome Checker": {
        "func": "is_palindrome",
        "desc": "Write is_palindrome(s): True if s reads the same backwards, ignoring case and spaces.",
        "starter": "def is_palindrome(s):\n    return s == s[::-1]\n",
        "tests": [(["racecar"], True), (["hello"], False), (["RaceCar"], True), (["nurses run"], True)],
    },
}

RUNNER = r'''
import json, sys
data = json.loads(sys.stdin.read())
ns = {}
try:
    exec(data["code"], ns)
    fn = ns[data["func"]]
except Exception as e:
    print(json.dumps({"fatal": f"{type(e).__name__}: {e}"})); sys.exit()
out = []
for args in data["args"]:
    try:
        out.append({"ok": True, "value": fn(*args)})
    except Exception as e:
        out.append({"ok": False, "error": f"{type(e).__name__}: {e}"})
print(json.dumps({"results": out}, default=repr))
'''

def _run_in_thread(code, func, all_args):
    """Fallback if a separate Python process cannot start (seen on some Windows setups)."""
    box = {}

    def target():
        ns = {}
        try:
            exec(code, ns)
            fn = ns[func]
        except Exception as e:
            box["data"] = {"fatal": f"{type(e).__name__}: {e}"}
            return
        out = []
        for args in all_args:
            try:
                out.append({"ok": True, "value": fn(*args)})
            except Exception as e:
                out.append({"ok": False, "error": f"{type(e).__name__}: {e}"})
        box["data"] = {"results": out}

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(5)
    return box.get("data", {"fatal": "Timeout: possible infinite loop"})


def _run_in_process(payload):
    runner_file = os.path.join(tempfile.gettempdir(), "antigpt_runner.py")
    with open(runner_file, "w", encoding="utf-8") as f:
        f.write(RUNNER)
    p = subprocess.run([sys.executable, runner_file], input=payload, capture_output=True,
                       text=True, encoding="utf-8", timeout=5)
    lines = [l for l in p.stdout.strip().splitlines() if l.startswith("{")]
    if not lines:
        raise RuntimeError(p.stderr.strip()[-300:] or "no output")
    return json.loads(lines[-1])


def grade(code, a):
    args = [t[0] for t in a["tests"]]
    payload = json.dumps({"code": code, "func": a["func"], "args": args})
    try:
        data = _run_in_process(payload)
    except subprocess.TimeoutExpired:
        data = {"fatal": "Timeout: possible infinite loop"}
    except Exception:
        data = _run_in_thread(code, a["func"], args)
    results = []
    for i, (t_args, expected) in enumerate(a["tests"]):
        r = {"ok": False, "error": data["fatal"]} if "fatal" in data else data["results"][i]
        results.append({"input": t_args, "expected": expected, "got": r.get("value"),
                        "error": r.get("error"), "passed": r["ok"] and r.get("value") == expected})
    return results
