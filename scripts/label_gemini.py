"""Label photos using Gemini API with contact sheets.
Supports GEMINI_API_KEY from environment or .env.
"""
import base64, glob, json, os, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, LABELS, WORK, ROOT, categories, load, save

SHEETS_PER_BATCH = 3
WORKERS = int(os.environ.get("GEMINI_WORKERS", 4))
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

def get_gemini_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env_file = os.path.join(ROOT, ".env")
    if os.path.exists(env_file):
        for line in open(env_file):
            k, _, v = line.strip().partition("=")
            if k.strip() == "GEMINI_API_KEY" and v.strip():
                return v.strip().strip('"').strip("'")
    return None

API_KEY = get_gemini_key()
if not API_KEY:
    sys.exit("GEMINI_API_KEY not found in environment or .env")

sheet_dir = os.path.join(WORK, "sheets")
sheets = sorted(glob.glob(os.path.join(sheet_dir, "sheet_*.jpg")), key=lambda p: int(re.search(r"sheet_(\d+)", p).group(1)))
inv = load(os.path.join(DATA, "inventory.json"))
cats = categories()
os.makedirs(LABELS, exist_ok=True)

folders = "\n".join(f"- {c['key']} ({c['kind']}): {c['rule']}" for c in cats)
batches = [sheets[i:i + SHEETS_PER_BATCH] for i in range(0, len(sheets), SHEETS_PER_BATCH)]
if "--only" in sys.argv:
    batches = batches[:int(sys.argv[sys.argv.index("--only") + 1])]

def ids_in(batch):
    ids = []
    for s in batch:
        idx = int(re.search(r"sheet_(\d+)", s).group(1))
        first = idx * 30
        last = first + 30
        ids.extend([str(r["id"]) for r in inv[first:last]])
    return ids

def call_gemini(batch_files, prompt_text):
    parts = []
    for s_path in batch_files:
        with open(s_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": b64
            }
        })
    parts.append({"text": prompt_text})
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        candidates = res_data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts_out = content.get("parts", [])
            if parts_out:
                return parts_out[0].get("text", "")
    return ""

def run(n, batch):
    out = os.path.join(LABELS, f"claude_{n:02d}.json")
    want = ids_in(batch)
    if os.path.exists(out) and set(want) <= set(load(out, {})):
        return n, len(want), 0.0, "cached"
        
    prompt = (
        "You sort a camera roll into folders. These are the folders, as key (kind): what goes in it\n"
        f"{folders}\n\n"
        "Look at each of these contact sheet images attached.\n"
        "Each sheet shows up to 30 square previews, each tagged in yellow with a number (its id). "
        "A tag with VIDEO is a video and must get a (video) folder. Every other tile is a photo and must get a "
        "(photo) folder. PNG usually means a screenshot. Give every id you see exactly one folder key from the list.\n\n"
        "Reply with a JSON object mapping id to folder key, like {\"12\": \"food\", \"13\": \"selfies\"}. No other text."
    )
    
    t0, why = time.time(), ""
    for attempt in range(4):
        if attempt:
            time.sleep(3 * attempt)
        try:
            text = call_gemini(batch, prompt)
        except Exception as e:
            why = str(e)
            print(f"  batch {n + 1}: try {attempt + 1} API error ({why}), retrying", flush=True)
            continue
            
        m = re.search(r"\{[^{}]*\}", text, re.S)
        try:
            raw_labels = json.loads(m.group(0)) if m else json.loads(text)
            labels = {str(k): v for k, v in raw_labels.items() if str(k) in want}
        except Exception:
            labels = {}
            
        if len(labels) >= 0.8 * len(want):
            save(out, labels)
            return n, len(labels), 0.0, f"{time.time() - t0:.1f}s" + (f", try {attempt + 1}" if attempt else "")
            
        why = f"got {len(labels)}/{len(want)} keys"
        print(f"  batch {n + 1}: try {attempt + 1} incomplete ({why}), retrying", flush=True)
        
    raise RuntimeError(f"batch {n + 1} failed after 4 tries: {why}")

if __name__ == "__main__":
    print(f"Gemini is labelling {len(inv)} files in {len(batches)} batches ({WORKERS} at a time, model {MODEL})...", flush=True)
    t0, done, failed = time.time(), 0, []
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(run, n, b) for n, b in enumerate(batches)]
        for f in as_completed(futs):
            try:
                n, k, c, how = f.result()
                done += 1
                print(f"PROGRESS {done} {len(batches)}", flush=True)
                print(f"  batch {done}/{len(batches)} done: {k} files ({how})", flush=True)
            except Exception as e:
                failed.append(str(e))
                print(f"  {e}", flush=True)

    labelled = set()
    for f in glob.glob(os.path.join(LABELS, "*.json")):
        labelled |= set(load(f, {}))
    missing = len(inv) - len(labelled & {str(r["id"]) for r in inv})
    print(f"Done in {time.time() - t0:.0f}s: {len(inv) - missing} labelled, {missing} missing"
          + (f", {len(failed)} batches failed (run again to retry)" if failed else ""), flush=True)
    sys.exit(1 if failed else 0)
