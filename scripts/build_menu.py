"""Pull Gather (Place Vanier) menus from UBC Nutrislice and write menu.json.

Usage: python3 scripts/build_menu.py START_DATE DAYS [--estimate]

Nutrislice lists no nutrition data for Vanier, so macros come from
scripts/estimates.txt. With --estimate and ANTHROPIC_API_KEY set, foods that
have no estimate yet are sent to Claude and the answers are appended there.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from typing import List

BASE = "https://ubc.api.nutrislice.com/menu/api/weeks/school/ubc-gather-place-vanier-residence/menu-type/"
MEALS = [("gather-place-vanier-residence-breakfast", "Breakfast"),
         ("gather-place-vanier-residence-lunch", "Lunch & Dinner"),
         ("gather-place-vanier-residence-baked-goods-desserts", "Baked Goods & Desserts")]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EST_PATH = os.path.join(ROOT, "scripts", "estimates.txt")


def load_estimates():
    est = {}
    for line in open(EST_PATH):
        if line.startswith("#") or not line.strip():
            continue
        fid, k, p, c, f, unit = line.rstrip("\n").split("|")
        est[fid] = dict(k=float(k), p=float(p), c=float(c), f=float(f), u=unit)
    return est


def fetch(start, end):
    foods, menus = {}, {}
    for slug, meal in MEALS:
        week = start - dt.timedelta(days=(start.weekday() + 1) % 7)  # Nutrislice weeks start Sunday
        while week <= end:
            url = f"{BASE}{slug}/{week:%Y/%m/%d}/"
            data = json.load(urllib.request.urlopen(url, timeout=60))
            for day in data["days"]:
                d = dt.date.fromisoformat(day["date"])
                if not start <= d <= end:
                    continue
                station, groups = "", []
                for it in day["menu_items"]:
                    if it.get("is_station_header") or it.get("is_section_title"):
                        station = (it.get("text") or "").strip()
                        continue
                    fo = it.get("food")
                    if not fo:
                        continue
                    fid = str(fo["id"])
                    icons = sorted({i["name"] for i in (fo.get("icons") or {}).get("food_icons", [])})
                    foods[fid] = dict(n=fo["name"].strip(), ing=(fo.get("ingredients") or "")[:300], tags=icons)
                    if not groups or groups[-1][0] != station:
                        groups.append([station, []])
                    groups[-1][1].append(fid)
                if groups:
                    menus.setdefault(day["date"], {})[meal] = groups
            week += dt.timedelta(days=7)
    return foods, menus


def estimate_with_claude(missing):
    """missing: list of (food_id, food dict). Returns {food_id: (k, p, c, f, serving)}."""
    import anthropic
    from pydantic import BaseModel

    class FoodEstimate(BaseModel):
        id: str
        kcal: float
        protein: float
        carbs: float
        fat: float
        serving: str

    class Estimates(BaseModel):
        items: List[FoodEstimate]

    client = anthropic.Anthropic()
    out = {}
    for i in range(0, len(missing), 40):
        chunk = missing[i:i + 40]
        listing = "\n".join(f"- id {fid}: {f['n']}. Ingredients: {f['ing'] or 'not listed'}" for fid, f in chunk)
        prompt = (
            "These foods are served at Gather, the Place Vanier residence dining hall at UBC. "
            "Nutrislice lists them as one portion but gives no nutrition data.\n"
            "For each, estimate calories, protein, carbs and fat (grams) for one typical dining-hall serving, "
            "and name that serving briefly (for example '1 burger', 'plate', 'bowl', '1 slice', '1 tbsp', '1 cookie').\n"
            "Sauces and spreads are about 1 tbsp; sandwich-bar proteins about 2 oz; cheese one slice; "
            "entrees served with rice or noodles include them.\n"
            f"Return one item per food, using the given id.\n\n{listing}"
        )
        try:
            response = client.messages.parse(
                model="claude-opus-5-5",
                max_tokens=16000,
                messages=[{"role": "user", "content": prompt}],
                output_format=Estimates,
            )
        except anthropic.AuthenticationError:
            print("Claude API key was rejected; skipping estimates", file=sys.stderr)
            return out
        except anthropic.RateLimitError:
            print("Rate limited by the Claude API; will retry tomorrow", file=sys.stderr)
            return out
        except anthropic.APIStatusError as e:
            print(f"Claude API error {e.status_code}; skipping this batch", file=sys.stderr)
            continue
        except anthropic.APIConnectionError:
            print("Could not reach the Claude API; skipping estimates", file=sys.stderr)
            return out
        if response.stop_reason == "refusal" or response.parsed_output is None:
            print("Claude returned no estimates for this batch", file=sys.stderr)
            continue
        wanted = {fid for fid, _ in chunk}
        for e in response.parsed_output.items:
            if e.id in wanted:
                serving = e.serving.replace("|", "/").replace("\n", " ").strip()[:40] or "portion"
                out[e.id] = (max(0, e.kcal), max(0, e.protein), max(0, e.carbs), max(0, e.fat), serving)
    return out


def main():
    start = dt.date.fromisoformat(sys.argv[1])
    end = start + dt.timedelta(days=int(sys.argv[2]) - 1)
    foods, menus = fetch(start, end)
    est = load_estimates()

    missing = [(fid, f) for fid, f in foods.items() if fid not in est]
    if missing and "--estimate" in sys.argv:
        if os.environ.get("ANTHROPIC_API_KEY"):
            new = estimate_with_claude(missing)
            with open(EST_PATH, "a") as fh:
                for fid, (k, p, c, f, unit) in new.items():
                    fh.write(f"{fid}|{round(k)}|{round(p, 1)}|{round(c, 1)}|{round(f, 1)}|{unit}\n")
            print(f"Estimated {len(new)} new foods with Claude")
            est = load_estimates()
        else:
            print("ANTHROPIC_API_KEY not set; new foods stay without estimates", file=sys.stderr)

    for fid, f in foods.items():
        f.update(est.get(fid, {}))
    still_missing = [(fid, f["n"]) for fid, f in foods.items() if "k" not in f]
    out = {"source": "UBC Nutrislice: Gather | Place Vanier Residence", "from": str(start), "to": str(end),
           "built": dt.datetime.now().isoformat(timespec="minutes"), "foods": foods, "menus": menus}
    with open(os.path.join(ROOT, "menu.json"), "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"{len(foods)} foods, {len(menus)} days, {len(still_missing)} without estimates")
    for fid, name in still_missing:
        print(f"  {fid}  {name}")


main()
