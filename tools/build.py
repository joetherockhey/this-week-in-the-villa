"""data/trends.json + data/shots.json + data/deck/<monday>.json + tools/site.css -> index.html, a frozen copy in archive/<monday>/, and archive/index.html
(all past reports plus each trend's history). Raw data is kept in data/weeks/.

trends.json is kept in rank order: evergreen trends first, then seasonal, each by usage_n (videos made).
"""
import json, html, datetime, pathlib, shutil, urllib.parse, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME = "This Week in the Villa"
trends = json.loads((ROOT / "data/trends.json").read_text("utf-8"))
shots = json.loads((ROOT / "data/shots.json").read_text("utf-8"))
today = datetime.date.today()
monday = today - datetime.timedelta(days=today.weekday())
wk = f"{monday.day} {monday:%B %Y}"
e = lambda s: html.escape(str(s or ""))
STATUS = {"Rising": "rise", "Peaking": "peak", "Steady": "flat", "Past peak": "fade", "Active slang": "flat"}
day = lambda d: f"{d.day} {d:%b %Y}"

# Every week each trend was listed. ponytail: matched by exact name, so keep a trend's name the same between weeks.
(ROOT / "data/weeks").mkdir(exist_ok=True)
shutil.copy(ROOT / "data/trends.json", ROOT / f"data/weeks/{monday}.json")
weeks = {datetime.date.fromisoformat(p.stem): json.loads(p.read_text("utf-8")) for p in sorted((ROOT / "data/weeks").glob("*.json"))}
hist = {}
for w, ts in weeks.items():
    for i, t in enumerate(ts, 1):
        hist.setdefault(t["name"], []).append((w, i, t))


def host(u):
    return urllib.parse.urlparse(u).netloc.replace("www.", "")


def who(u):
    """@handle and upload date (TikTok video ids carry their upload time in the top 32 bits)."""
    m = re.search(r"tiktok\.com/@([^/]+)/video/(\d+)", u)
    if not m: return "Instagram reel" if "instagram.com" in u else host(u)
    d = datetime.datetime.fromtimestamp(int(m.group(2)) >> 32, datetime.UTC).date()
    return f"@{m.group(1)}, {d.day} {d:%b %Y}"


def short(n):
    if not n: return ""
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div: return f"{n / div:.1f}".rstrip("0").rstrip(".") + suf
    return str(n)


def examples(t):
    rows = []
    for x in t["examples"]:
        stats = " · ".join(s for s in (f"{short(x.get('plays'))} plays" if x.get("plays") else "",
                                        f"{short(x.get('likes'))} likes" if x.get("likes") else "") if s)
        rows.append(f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(who(x["url"]).split(",")[0])}</a>'
                    f'<span>{e(stats)}{" · " + e(x["note"]) if x.get("note") else ""}</span></li>')
    return "".join(rows)


def card(i, t):
    shot = shots.get(str(i))
    if shot and shot["kind"] == "ai":
        cap = "AI illustration. No example post could be captured."
    elif shot:
        cap = f'<a href="{e(shot["url"])}" target="_blank" rel="noopener">{e(who(shot["url"]))}</a>'
    pic = shot and f'<img src="img/{i}.jpg?v={today}" alt="{"AI illustration" if shot["kind"] == "ai" else "Example post"} for {e(t["name"])}" loading="lazy">'
    if shot and shot["kind"] != "ai":
        pic = f'<a class="pic" href="{e(shot["url"])}" target="_blank" rel="noopener">{pic}</a>'
    img = f'<figure>{pic}<figcaption>{cap}</figcaption></figure>' if shot else '<figure class="noimg"></figure>'
    sound = (f'<a href="{e(t["sound_url"])}" target="_blank" rel="noopener">{e(t["sound"])}</a>' if t.get("sound_url") else e(t.get("sound"))) or "No set sound. It's a format."
    risk = f'<dt>Watch out</dt><dd>{e(t["risk"])}</dd>' if t.get("risk") else ""
    srcs = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(host(u))}</a>' for u in t["sources"])
    first = hist[t["name"]][0]
    was = f", {short(first[2].get('usage_n'))} videos then" if first[2].get("usage_n") else ""
    listed = f"Since the week of {day(first[0])}{was}" if first[0] < monday else "New this week"
    when = "Works any week" if t["longevity"] == "evergreen" else f"Time-bound, runs until {e(t.get('ends'))}"
    return f"""
<article class="trend" id="t{i}">
  {img}
  <div class="body">
    <p class="meta"><span class="rk">{i}</span>{st(t["status"])}<span>{when}</span><span>{e(" + ".join(t["platforms"]))}</span></p>
    <h3>{e(t["name"])}</h3>
    <p class="what">{e(t["what"])}</p>
    <dl>
      <dt>Usage</dt><dd>{e(t["usage"])}</dd>
      <dt>Origin</dt><dd>{e(t["origin"])}</dd>
      <dt>On this list</dt><dd>{e(listed)}</dd>
      <dt>Sound</dt><dd>{sound}</dd>
      <dt>Brand idea</dt><dd>{e(t["brand_use"])}</dd>
      {risk}
    </dl>
    <ul class="ex">{examples(t)}</ul>
    <p class="src">Sources: {srcs}</p>
  </div>
</article>"""


def spark(v, w, h, area=False):
    """26 weeks scaled to the word's own peak, ending on a dot."""
    top = max(v) or 1
    pts = [(i * w / (len(v) - 1), h - 3 - x / top * (h - 6)) for i, x in enumerate(v)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    fill = f'<polygon points="0,{h} {line} {w},{h}" fill="currentColor" opacity=".22"/>' if area else ""
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" role="img" aria-label="26 weeks of lookups">{fill}<polyline points="{line}" fill="none" '
            f'stroke="currentColor" stroke-width="{2.4 if area else 1.5}" stroke-linejoin="round"/><circle cx="{w}" cy="{pts[-1][1]:.1f}" r="{3.6 if area else 2.2}" fill="currentColor"/></svg>')


def st(status):
    return f'<span class="st {STATUS.get(status, "flat")}"><i></i>{e(status)}</span>'


def pct(c):
    return f"{c:+.0%}".replace("-", "\u2212")


def cover(i, lazy=True):
    return f'<img src="img/{i}.jpg?v={today}" alt="Example post for {e(trends[i - 1]["name"])}"{" loading=\"lazy\"" if lazy else ""}>'


def label(t):
    return deck["rows"][t["name"]].get("name", t["name"])


def ends(t):
    return re.sub(r" \d{4}$", "", t.get("ends") or "")


def list_row(i, t):
    """Date-bound counts run across every year the sound has been around, so they carry their end date instead of 'videos'."""
    n = short(t.get("usage_n")) or "n/a"
    n = f"{n} videos" if t["longevity"] == "evergreen" else f"{n}, to {ends(t)}"
    return (f'<a class="a-row" href="#t{i}"><div class="th">{cover(i)}</div><span class="rk">{i}</span><div><h4>{e(label(t))}</h4><small>{e(deck["rows"][t["name"]]["ctx"])}</small></div>'
            f'<div class="r">{st(t["status"])}<span class="num">{e(n)}</span></div></a>')


def top_word(w):
    return (f'<div><h3>{e(w["word"])}</h3><p>{e(w["means"])}</p>{st(w["status"])}<span class="num">{pct(w["change"])}, {w["lookups"]:,} lookups in 7 days</span>{spark(w["weekly"], 300, 70, True)}</div>')


def wall_word(w):
    return f'<div><h4>{e(w["word"])}</h4><div class="ln">{st(w["status"])}<span class="num">{pct(w["change"])}</span></div>{spark(w["weekly"], 160, 34)}</div>'


words_data = json.loads((ROOT / f"data/words/{monday}.json").read_text("utf-8"))
words = [w for w in words_data["words"] if "weekly" in w]
phrases = [w for w in words_data["words"] if "weekly" not in w]
through = day(datetime.date.fromisoformat(words_data["through"]))
deck_file = ROOT / f"data/deck/{monday}.json"
assert deck_file.exists(), f"write {deck_file.name} first: the page's headlines come from it"
deck = json.loads(deck_file.read_text("utf-8"))
idx = {t["name"]: i for i, t in enumerate(trends, 1)}
ever = [(i, t) for i, t in enumerate(trends, 1) if t["longevity"] == "evergreen"]
seas = [(i, t) for i, t in enumerate(trends, 1) if t["longevity"] != "evergreen"]
order = {"Rising": 0, "Peaking": 1, "Steady": 2, "Past peak": 3}
words = sorted(words, key=lambda w: (order[w["status"]], -w["change"]))
css = (ROOT / "tools/site.css").read_text("utf-8")
fonts = '<link rel="icon" href="/this-week-in-the-villa/icon-64.png"><link rel="apple-touch-icon" href="/this-week-in-the-villa/icon-180.png">\n<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,400..800&family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400..700&display=swap" rel="stylesheet">'


def arcade(name):
    i = idx[name]
    t = trends[i - 1]
    when = f"To {ends(t)}<br>" if t.get("ends") else ""
    unit = "all years" if t["longevity"] != "evergreen" else "videos"
    return f'<li><a class="pic" href="#t{i}">{cover(i)}</a><h3>{e(label(t))}</h3><p>{when}<span class="num">{short(t.get("usage_n"))} {unit}</span></p></li>'


def moment(m):
    i = idx[m["trend"]]
    return f'<article><h3>{e(m["head"])}</h3><p>{e(m["text"])}</p><a href="#t{i}">{e(label(trends[i - 1]))}, number {i}</a></article>'


def five(i, t):
    return (f'<li><a href="#t{i}"><span class="pic">{cover(i)}</span><h3><span>{i}</span>{e(label(t))}</h3>'
            f'<div class="meta">{st(t["status"])}<span class="num">{short(t.get("usage_n"))} videos</span></div></a></li>')


lead_i, lead = ever[0]
others = [i for i, t in ever if t["name"] != deck["story_trend"]]
trio = [others[0], idx[deck["story_trend"]], others[2]]  # the week's story in the middle, between two of the biggest trends
dated = f"""<div class="a-dated"><h3>{e(deck["tbl3"])}</h3><p>Post soon or skip. Video counts cover every year the sound has run.</p><div class="a-rows">{"".join(list_row(i, t) for i, t in seas)}</div></div>""" if seas else ""
phrase_list = "".join(f'<li>{e(w["word"])}{st(w["status"])}</li>' for w in phrases)

page = f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NAME} · Week of {wk}</title>
<meta name="description" content="{len(trends)} social trends ranked by how much they're used, for the week of {wk}.">
{fonts}
<style>
{css}</style>
</head>
<body>
<header class="a-hero">
 <div class="a-nav"><b>Week of {wk}</b><span><a href="#words">Words</a><a href="slides/">Weekly slides</a><a href="archive/">Past reports</a><a href="how/">How it works</a></span></div>
 <p class="a-mast">This Week <br>in the Villa</p>
 <div class="a-col"><div class="a-what"><p>What's trending on TikTok and Instagram each week, and how brands can use it.</p><a class="a-btn" href="how/">See how it works</a></div>
 <div class="a-lead"><p class="a-kick">This week</p><h1>{e(deck["glance_title"])}</h1></div></div>
 <div class="a-trio">{"".join(f'<a href="#t{i}">{cover(i, False)}</a>' for i in trio)}</div>
</header>
<section class="a-feature"><div class="wrap"><h2>{e(deck["story_title"])}</h2>
 <div class="a-fgrid"><ul class="a-facts">{"".join(f"<li>{e(b)}</li>" for b in deck["story_bullets"])}</ul><ul class="a-arcade">{"".join(arcade(n) for n in deck["story_trends"])}</ul></div></div></section>
<section class="a-moments"><div class="wrap"><h2>Also this week</h2>{"".join(moment(m) for m in deck["moments"])}</div></section>
<section class="a-list"><div class="wrap"><h2>The list</h2><p>{len(trends)} TikTok and Reels trends, ranked by how many videos use them. Trends that work any week come first.</p>
 <div class="a-one"><a class="pic" href="#t{lead_i}">{cover(lead_i)}</a><div><div class="rk">{lead_i}</div><h3>{e(label(lead))}</h3><div class="meta">{st(lead["status"])}<span class="num">{short(lead.get("usage_n"))} videos</span></div><p class="tx">{e(lead["what"])}</p><p class="tx"><b>Brand idea:</b> {e(lead["brand_use"])}</p></div></div>
 <ul class="a-five">{"".join(five(i, t) for i, t in ever[1:5])}</ul>
 <div class="a-rows">{"".join(list_row(i, t) for i, t in ever[5:])}</div>
 {dated}
</div></section>
<section class="a-words" id="words"><div class="wrap"><p class="a-kick">What Gen Z is saying</p><h2>{e(deck["lang_title"])}</h2><div class="a-wtop">{"".join(top_word(w) for w in words[:2])}</div><div class="a-wall">{"".join(wall_word(w) for w in words[2:])}</div>
 <ul class="a-phr">{phrase_list}</ul><p class="a-wnote">Status compares the last 14 days of Wiktionary lookups with the 14 before, and with each word's best stretch in 26 weeks. Lookups show curiosity about a word, so read them as a sign of use. Data runs to {through}. Each line is 26 weeks, scaled to that word's own peak. Phrases have no dictionary page, so their status is read by hand.</p></div></section>
<section class="a-full"><div class="wrap"><h2>Full write-ups</h2>
<main>{"".join(card(i, t) for i, t in enumerate(trends, 1))}</main></div></section>
<div class="wrap how" id="how">
  <p>How this works: each Wednesday the latest round-ups (New Engen, SocialPilot, Buffer, Postdom and others) are checked against the live TikTok sound pages. Video counts come from the sound page or the round-up quoting them, as of the date shown. Plays and likes on the examples come from TikTok's own post data at the time of checking.</p>
  <p>Example images are the cover frames of the linked posts, shown for reference. Check a sound's licensing before using it on a brand account.</p>
  <p>Compiled {today.day} {today:%B %Y}.</p>
</div>
<footer class="a-foot"><div class="wrap big"><div><a class="lk" href="slides/">Weekly slides</a><p>This week: {e(deck["theme"])}</p></div><div><a class="lk" href="archive/">Past reports</a><p>Every report as it ran, and when each trend first made the list.</p></div></div></footer>
</body>
</html>
"""
(ROOT / "index.html").write_text(page, "utf-8")

# Freeze this week. Images are numbered and reused every week, so each report keeps its own copy.
snap = ROOT / "archive" / str(monday)
snap.mkdir(parents=True, exist_ok=True)
(snap / "index.html").write_text(page.replace('href="archive/"', 'href="../"').replace('href="slides/"', 'href="../../slides/"').replace('href="how/"', 'href="../../how/"').replace('href="./"', 'href="../../"'), "utf-8")
shutil.copytree(ROOT / "img", snap / "img", dirs_exist_ok=True)

# archive/index.html: every report, then every trend with when it first showed up.
reports = "".join(f'<tr><td><a href="{w}/">Week of {w.day} {w:%B %Y}</a></td><td class="num">{len(ts)} trends</td></tr>'
                  for w, ts in sorted(weeks.items(), reverse=True))


def hist_row(seen):
    (w0, _, t0), (w1, i1, t1) = seen[0], seen[-1]
    a, b = short(t0.get("usage_n")) or "n/a", short(t1.get("usage_n")) or "n/a"
    return (f'<tr><td><a href="{w1}/#t{i1}">{e(t1["name"])}</a><span class="origin">{e(t1["origin"])}</span></td>'
            f'<td class="first">{day(w0)}</td><td class="when">{"This week" if w1 == monday else day(w1)}</td>'
            f'<td class="num">{a if w0 == w1 else a + " → " + b}</td></tr>')


rows = "".join(hist_row(s) for s in sorted(hist.values(), key=lambda s: (s[0][0], s[-1][2].get("usage_n") or 0), reverse=True))


def shell(title, crumb, home, h1, lead, body):
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{fonts}
<style>
{css}</style>
</head>
<body>
<header class="sub-top"><div class="wrap"><div class="a-nav"><a href="{home}"><b>{NAME}</b></a><span>{crumb}</span></div><h1>{h1}</h1><p class="lead">{lead}</p></div></header>
<div class="wrap sub">{body}</div>
</body>
</html>
"""


(ROOT / "archive/index.html").write_text(shell(f"{NAME} Past Reports", "Past reports", "../", "Past reports", "Every weekly report as it ran, and when each trend first made the list.", f"""
<h2>Weekly reports</h2>
<p>Each one is frozen as it was published.</p>
<table><tbody>{reports}</tbody></table>
<h2>Trend history</h2>
<p>Newest to the list first. The line under each name says when the trend actually began. Videos show the count when first listed, then when last listed.</p>
<table><thead><tr><th>Trend</th><th>First listed</th><th class="when">Last listed</th><th class="num">Videos</th></tr></thead><tbody>{rows}</tbody></table>
"""), "utf-8")

# how/index.html: the explainer. Its pictures and numbers come from this week's data, so it never goes stale.
how_data = {"trends": [{"r": i, "name": label(t), "n": short(t.get("usage_n")) or "n/a", "ev": t["longevity"] == "evergreen"} for i, t in enumerate(trends, 1)],
            "counts": {k: sum(t["status"] == k for t in trends) for k in order},
            "word": {"word": words[0]["word"], "weekly": words[0]["weekly"], "pct": pct(words[0]["change"])},
            "real": sum(v["kind"] != "ai" for v in shots.values()), "ai": sum(v["kind"] == "ai" for v in shots.values()),
            "weeks": len(weeks), "v": str(today)}
(ROOT / "how").mkdir(exist_ok=True)
how = (ROOT / "tools/how.html").read_text("utf-8")
for k, v in (("__FONTS__", fonts), ("__CSS__", css), ("__DATA__", json.dumps(how_data, ensure_ascii=False))):
    how = how.replace(k, v)
(ROOT / "how/index.html").write_text(how, "utf-8")

# slides/index.html: one link per week's Google Slides deck (data/decks.json, written by the trend-report skill).
decks = json.loads((ROOT / "data/decks.json").read_text("utf-8"))
deck_rows = "".join(f'<tr><td><a href="{e(d["url"])}" target="_blank" rel="noopener">Week of {day(datetime.date.fromisoformat(w))}</a><span class="origin">{e(d["theme"])}</span></td>'
                    f'<td class="num"><a href="{e(d["url"])}" target="_blank" rel="noopener">Open slides <span aria-hidden="true">→</span></a></td></tr>'
                    for w, d in sorted(decks.items(), reverse=True))
(ROOT / "slides").mkdir(exist_ok=True)
(ROOT / "slides/index.html").write_text(shell(f"{NAME} Slides", "Weekly slides", "../", "Weekly slides", "Each week's findings as a Google Slides deck, newest first.", f"<h2>All decks</h2><table><tbody>{deck_rows}</tbody></table>"), "utf-8")
assert all((ROOT / f"archive/{w}/index.html").exists() for w in weeks), "a week in data/weeks has no archived page"
print("built", len(trends), "trends,", len(weeks), "weeks archived")
