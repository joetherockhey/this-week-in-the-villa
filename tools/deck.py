"""data/weeks + data/deck + data/words for one Monday -> the Google Slides requests that fill one copy of the template.

Usage: python tools/deck.py [<monday>]   (default: the newest data/deck/*.json). Prints the requests as JSON.
Fails if a line is too long for its box: Slides never shrinks text, so a long line would spill.
The weekly steps are in the trend-report skill. Images are fetched by Google, so the week must be pushed first.
"""
import json, pathlib, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://joetherockhey.github.io/this-week-in-the-villa"
TEMPLATE = "1rvdR3fjF2m_mhh2mmFXs_AuJB1XRXVV-R7u6RrdSg8I"  # 'This Week in the Villa (template)' in Joe's Drive; tools/deck_template.py drew it
PILL = {"Rising": ("3A2C7A", "FBF8FF"), "Peaking": ("6D45D1", "FBF8FF"), "Steady": ("ECE5FA", "211847"), "Past peak": ("DDD3F2", "5F5885")}
TERRA, POOL, MUTE, INK = "6D45D1", "3A2C7A", "5F5885", "211847"
LIMITS = {"theme": 70, "glance_title": 75, "glance_note": 230, "story_title": 70, "story_bullets": 360, "lang_title": 50, "peak_title": 62,
          "case_title": 75, "brand_title": 75, "brand_num": 6, "brand_label": 90, "brand_use": 165, "brand_risk": 165,
          "src": 130, "tbl1": 62, "tbl2": 62, "tbl3": 62, "head": 48, "text": 150, "when": 12, "what": 85, "name": 36, "audio": 50, "ctx": 70, "label": 30}


def rgb(h): return {"red": round(int(h[:2], 16) / 255, 3), "green": round(int(h[2:4], 16) / 255, 3), "blue": round(int(h[4:], 16) / 255, 3)}


def short(n):
    if not n: return "n/a"
    for div, suf in ((1e6, "M"), (1e3, "K")):
        if n >= div: return f"{n / div:.1f}".rstrip("0").rstrip(".") + suf
    return str(n)


def fits(kind, s):
    assert len(s) <= LIMITS[kind], f"{kind} is {len(s)} chars, limit {LIMITS[kind]}: {s}"
    return s


def sub(token, text, page=None):
    r = {"replaceAllText": {"containsText": {"text": "{{%s}}" % token}, "replaceText": text}}
    if page: r["replaceAllText"]["pageObjectIds"] = [page]
    return r


def pic(token, url, page=None):
    r = {"replaceAllShapesWithImage": {"containsText": {"text": "{{%s}}" % token}, "imageUrl": url, "imageReplaceMethod": "CENTER_CROP"}}
    if page: r["replaceAllShapesWithImage"]["pageObjectIds"] = [page]
    return r


def style(oid, fields, st, cell=None):
    r = {"objectId": oid, "textRange": {"type": "ALL"}, "fields": fields, "style": st}
    if cell: r["cellLocation"] = {"rowIndex": cell[0], "columnIndex": cell[1]}
    return {"updateTextStyle": r}


def tint(oid, h, cell=None):
    return style(oid, "foregroundColor", {"foregroundColor": {"opaqueColor": {"rgbColor": rgb(h)}}}, cell)


def link(oid, url, h, cell=None):
    """Slides paints links its own blue, so set the colour in the same request."""
    return style(oid, "link,foregroundColor,underline", {"link": {"url": url}, "underline": False, "foregroundColor": {"opaqueColor": {"rgbColor": rgb(h)}}}, cell)


def cards(p, page, rows, tea, cover):
    r = []
    for i, t in enumerate(rows, 1):
        row = tea["rows"][t["name"]]
        fill, text = PILL[t["status"]]
        r += [sub(f"c{i}_name", fits("name", row.get("name", t["name"])), page), sub(f"c{i}_ctx", fits("ctx", row["ctx"]), page), sub(f"c{i}_audio", fits("audio", row["audio"]), page),
              sub(f"c{i}_status", t["status"], page), sub(f"c{i}_n", short(t.get("usage_n")), page), pic(f"img_c{i}", cover(t["name"]), page),
              {"updateShapeProperties": {"objectId": f"{p}_pl{i}", "shapeProperties": {"shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(fill)}}}}, "fields": "shapeBackgroundFill"}},
              tint(f"{p}_pl{i}", text), link(f"{p}_nm{i}", t["examples"][0]["url"], INK)]
        if t.get("sound_url"): r.append(link(f"{p}_sd{i}", t["sound_url"], MUTE))
    return r


def requests(monday):
    tea = json.loads((ROOT / f"data/deck/{monday}.json").read_text("utf-8"))
    trends = json.loads((ROOT / f"data/weeks/{monday}.json").read_text("utf-8"))
    wd = json.loads((ROOT / f"data/words/{monday}.json").read_text("utf-8"))
    d = datetime.date.fromisoformat(monday)
    idx = {t["name"]: i for i, t in enumerate(trends, 1)}
    cover = lambda name: f"{SITE}/archive/{monday}/img/{idx[name]}.jpg"
    ever = [t for t in trends if t["longevity"] == "evergreen"]
    seas = [t for t in trends if t["longevity"] != "evergreen"]
    label = lambda t: tea["rows"].get(t["name"], {}).get("name", t["name"])

    r = [sub("week", f"{d.day} {d:%B %Y}"), sub("theme", fits("theme", tea["theme"])), sub("src", fits("src", tea["src"]))]
    for k in ("glance_title", "glance_note", "story_title", "peak_title", "lang_title", "case_title", "brand_title", "brand_num", "brand_label", "brand_use", "brand_risk"):
        r.append(sub(k, fits(k, tea[k])))
    r.append(sub("story_bullets", fits("story_bullets", "\n".join(tea["story_bullets"]))))
    r += [sub("kick", "THE TRENDS: TOP OF THE LIST", "v_tr1"), sub("kick", "THE TRENDS: NEXT UP", "v_tr2"), sub("t_title", fits("tbl1", tea["tbl1"]), "v_tr1"),
          sub("t_title", fits("tbl2", tea["tbl2"]), "v_tr2"), sub("date_title", fits("tbl3", tea["tbl3"]))]
    for i, (n, text) in enumerate(tea["glance"], 1):
        r += [sub(f"n{i}", str(n)), sub(f"l{i}", fits("label", text))]
    for i, m in enumerate(tea["moments"], 1):
        r += [sub(f"m{i}_head", fits("head", m["head"])), sub(f"m{i}_text", fits("text", m["text"])), pic(f"img_m{i}", m.get("img") or cover(m["trend"]))]
    for i, (when, what) in enumerate(tea["case_steps"], 1):
        r += [sub(f"c{i}_when", fits("when", when), "v_case"), sub(f"c{i}_what", fits("what", what), "v_case")]
    r += [pic("img_story", cover(tea["story_trend"])), pic("img_case", cover(tea["case_trend"])), pic("img_words", f"{SITE}/archive/{monday}/img/words.png?v={wd['through']}")]
    r += cards("a", "v_tr1", ever[:6], tea, cover) + cards("b", "v_tr2", ever[6:12], tea, cover)

    for st in PILL:
        k = st.split()[0].lower()
        names = [label(t) for t in trends if t["status"] == st]
        r += [sub(f"{k}_n", str(len(names))), sub(f"{k}_list", "\n".join(names) or "None this week")]

    for i, t in enumerate(seas[:6], 1):
        row = tea["rows"][t["name"]]
        r += [sub(f"d{i}_name", fits("name", row.get("name", t["name"]))), sub(f"d{i}_audio", fits("audio", row["audio"])), sub(f"d{i}_status", t["status"]),
              sub(f"d{i}_n", short(t.get("usage_n"))), sub(f"d{i}_ends", t.get("ends") or ""), tint("d_tab", {"Rising": POOL, "Peaking": TERRA}.get(t["status"], MUTE), (i, 2)),
              link("d_tab", t["examples"][0]["url"], INK, (i, 0))]
        if t.get("sound_url"): r.append(link("d_tab", t["sound_url"], INK, (i, 1)))
    for i in range(6, len(seas[:6]), -1):  # bottom up, so row numbers stay right
        r.append({"deleteTableRow": {"tableObjectId": "d_tab", "cellLocation": {"rowIndex": i, "columnIndex": 0}}})

    measured = [w for w in wd["words"] if "weekly" in w]
    up = [w for w in measured if w["status"] != "Past peak"]
    down = sorted((w for w in measured if w["status"] == "Past peak"), key=lambda w: w["change"])
    for i, w in enumerate((up + down)[:8], 1):
        r += [sub(f"w{i}_word", w["word"]), sub(f"w{i}_status", w["status"]), sub(f"w{i}_n", f'{w["lookups"]:,}'), sub(f"w{i}_chg", f'{w["change"]:+.0%}'),
              tint("w_tab", {"Rising": POOL, "Peaking": TERRA}.get(w["status"], MUTE), (i, 1))]
    e = datetime.date.fromisoformat(wd["through"])
    r.append(sub("lang_note", f"Lookups on English Wiktionary over 7 days. Change compares the 14 days to {e.day} {e:%b} with the 14 before. Lookups show curiosity, not a count of use."))
    r.append(link("en_ll", f"{SITE}/archive/{monday}/", "F7C9DC"))
    return r


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    weeks = sorted(p.stem for p in (ROOT / "data/deck").glob("*.json"))
    print(json.dumps(requests(sys.argv[1] if len(sys.argv) > 1 else weeks[-1]), ensure_ascii=False, separators=(",", ":")))
