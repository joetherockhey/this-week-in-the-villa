"""data/words.json -> data/words/<monday>.json and img/words.png.

Measures how often each word is looked up on English Wiktionary (Wikimedia pageviews, free, no key).
ponytail: lookups stand in for use. Nothing free counts words in TikTok comments, so read it as curiosity about a word.
Entries with no "titles" are phrases with no page: their status is set by hand in words.json.
Usage: python tools/words.py [chart]   (chart: only redraw img/words.png)
"""
import datetime, json, pathlib, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEEKS = 26
ORDER = {"Rising": 0, "Peaking": 1, "Steady": 2, "Past peak": 3}


def status(daily):
    """Last 14 days against the 14 before, and against the best 14 days on record."""
    now, before = sum(daily[-14:]), sum(daily[-28:-14])
    peak = max(sum(daily[i:i + 14]) for i in range(len(daily) - 13))
    change = (now - before) / before if before else 0
    if now < 40: return "Steady", change  # too few lookups for a percentage to mean anything
    if change >= .2: return "Rising", change
    if now >= .85 * peak and now >= 1.25 * sum(daily) / len(daily) * 14: return "Peaking", change  # near its best, and well above its norm
    if change <= -.2 or now <= .6 * peak: return "Past peak", change
    return "Steady", change


def fetch(title, start, end):
    u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wiktionary/all-access/user/"
         f"{urllib.parse.quote(title.replace(' ', '_'), safe='')}/daily/{start:%Y%m%d}/{end:%Y%m%d}")
    for wait in (2, 10, 30, 60):
        time.sleep(wait)
        try:
            items = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "trend-report/1.0"})))["items"]
            return {i["timestamp"][:8]: i["views"] for i in items}
        except urllib.error.HTTPError as e:
            if e.code == 404: return {}  # no page, or no views yet
            if e.code != 429: raise
    raise SystemExit(f"Wikimedia kept refusing {title}")


def chart(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, plaster, colours = "#14303A", "#F7F0E4", ("#C8553D", "#1E8A9C", "#D99A1C", "#14303A")
    fig, ax = plt.subplots(figsize=(4.6, 3.5), dpi=220, facecolor=plaster)
    ax.set_facecolor(plaster)
    measured = [r for r in rows if r.get("weekly")]
    top = [r for r in measured if r["status"] == "Rising"][:3] + [min(measured, key=lambda r: r["change"])]  # what's climbing, and the steepest fall
    for r, c in zip(top, colours):
        v = r["weekly"]
        v = [sum(v[max(0, i - 2):i + 1]) / len(v[max(0, i - 2):i + 1]) for i in range(len(v))]  # three-week average: single weeks are noisy
        y = [x / max(v) * 100 for x in v]
        ax.plot(y, color=c, linewidth=2.2)
        ax.annotate(r["word"], (len(y) - 1, y[-1]), xytext=(5, 0), textcoords="offset points", color=c, fontsize=9, fontweight="bold", va="center")
    ax.set_xlim(0, WEEKS + 5)
    ax.set_ylim(0, 108)
    ax.set_xticks([0, WEEKS - 1], [f"{WEEKS} weeks ago", "This week"], fontsize=8, color=ink)
    ax.set_yticks([0, 100], ["0", "Own peak"], fontsize=8, color=ink)
    ax.tick_params(length=0)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(ink)
    fig.tight_layout()
    fig.savefig(path, facecolor=plaster)


def redraw():
    """Redraw the chart from saved data, without calling Wikimedia again."""
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    chart(json.loads((ROOT / f"data/words/{monday}.json").read_text("utf-8"))["words"], ROOT / "img/words.png")


def main():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    end = today - datetime.timedelta(days=2)  # the last full day Wikimedia has settled
    start = end - datetime.timedelta(days=WEEKS * 7 - 1)
    days = [(start + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(WEEKS * 7)]
    rows = []
    for w in json.loads((ROOT / "data/words.json").read_text("utf-8")):
        if "titles" not in w:
            rows.append(w)
            continue
        got = [fetch(t, start, end) for t in w["titles"]]
        daily = [sum(g.get(d, 0) for g in got) for d in days]
        st, change = status(daily)
        rows.append({"word": w["word"], "means": w["means"], "status": st, "change": round(change, 3), "lookups": sum(daily[-7:]),
                     "weekly": [sum(daily[i:i + 7]) for i in range(0, len(daily), 7)]})
        print(w["word"], st, f"{change:+.0%}", rows[-1]["lookups"])
    rows.sort(key=lambda r: (r.get("weekly") is None, ORDER.get(r["status"], 9), -r.get("change", 0)))
    (ROOT / "data/words").mkdir(exist_ok=True)
    (ROOT / f"data/words/{monday}.json").write_text(json.dumps({"through": str(end), "words": rows}, ensure_ascii=False, indent=1), "utf-8")
    chart(rows, ROOT / "img/words.png")


def demo():
    flat = [10] * 60
    assert status(flat)[0] == "Steady"
    assert status([10] * 46 + [20] * 14)[0] == "Rising"
    assert status([20] * 14 + [10] * 32 + [14] * 14)[0] == "Rising"
    assert status([50] * 30 + [40] * 16 + [20] * 14)[0] == "Past peak"
    assert status([10] * 32 + [30] * 28)[0] == "Peaking"
    assert status([1] * 60)[0] == "Steady"


if __name__ == "__main__":
    demo()
    redraw() if sys.argv[1:] == ["chart"] else main()
