"""data/trends.json + data/tea/<monday>.json -> the Google Slides requests that fill one copy of the template.

Usage: python tools/deck.py [<monday>]   (default: the newest data/tea/*.json). Prints the requests as JSON.
Fails if a line is too long for its box: Slides never shrinks text, so a long line would spill.
The weekly steps are in the weekly-tea skill. Images are fetched by Google, so the week must be pushed first.
"""
import json, pathlib, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://joetherockhey.github.io/apparent-trends"
TEMPLATE = "1qWBqoIiHIKewJVAg5YMMqE9UqdN90heBTncnI5NZKE8"  # 'The Weekly Tea (template)' in Joe's Drive; tools/deck_template.py drew it
STATUS_FILL = {"Rising": "D5E8D4", "Peaking": "FFF2CC", "Steady": "CFE2F3", "Past peak": "EAD1DC"}
BERRY = "9C1F52"
LIMITS = {"theme": 70, "glance_title": 75, "glance_note": 230, "story_title": 75, "story_bullets": 360, "lang_title": 60, "lang_note": 120,
          "case_title": 90, "case_story": 75, "brand_title": 75, "brand_num": 9, "brand_label": 90, "brand_use": 165, "brand_risk": 165,
          "src": 130, "tbl1": 60, "tbl2": 60, "tbl3": 60, "head": 48, "text": 150, "when": 12, "what": 85, "name": 42, "audio": 50, "ctx": 70, "label": 30}


def rgb(h): return {"red": round(int(h[:2], 16) / 255, 3), "green": round(int(h[2:4], 16) / 255, 3), "blue": round(int(h[4:], 16) / 255, 3)}


def short(n):
    if not n: return "n/a"
    for div, suf in ((1e6, "M"), (1e3, "K")):
        if n >= div: return f"{n / div:.1f}".rstrip("0").rstrip(".") + suf
    return str(n)


def fits(kind, s):
    assert len(s) <= LIMITS[kind], f"{kind} is {len(s)} chars, limit {LIMITS[kind]}: {s}"
    return s


def sub(token, text, pages=None):
    r = {"replaceAllText": {"containsText": {"text": "{{%s}}" % token}, "replaceText": text}}
    if pages: r["replaceAllText"]["pageObjectIds"] = pages
    return r


def pic(token, url):
    return {"replaceAllShapesWithImage": {"containsText": {"text": "{{%s}}" % token}, "imageUrl": url, "imageReplaceMethod": "CENTER_CROP"}}


def link(tab, row, col, url):
    return {"updateTextStyle": {"objectId": tab, "cellLocation": {"rowIndex": row, "columnIndex": col}, "textRange": {"type": "ALL"}, "fields": "link,underline,foregroundColor",
            "style": {"link": {"url": url}, "underline": True, "foregroundColor": {"opaqueColor": {"rgbColor": rgb(BERRY)}}}}}


def table(tab, page, rows, trends, tea, cover):
    r = []
    for i, t in enumerate(rows, 1):
        short_ = tea["rows"][t["name"]]
        r += [sub(f"r{i}_name", fits("name", short_.get("name", t["name"])), [page]), sub(f"r{i}_audio", fits("audio", short_["audio"]), [page]),
              sub(f"r{i}_status", t["status"], [page]), sub(f"r{i}_n", short(t.get("usage_n")), [page]), sub(f"r{i}_ctx", fits("ctx", short_["ctx"]), [page]),
              link(tab, i, 0, t["examples"][0]["url"])]
        if t.get("sound_url"): r.append(link(tab, i, 1, t["sound_url"]))
        r.append({"updateTableCellProperties": {"objectId": tab, "tableRange": {"location": {"rowIndex": i, "columnIndex": 2}, "rowSpan": 1, "columnSpan": 1},
                  "tableCellProperties": {"tableCellBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(STATUS_FILL[t["status"]])}}}}, "fields": "tableCellBackgroundFill"}})
    for i in range(6, len(rows), -1):  # bottom up, so row numbers stay right
        r.append({"deleteTableRow": {"tableObjectId": tab, "cellLocation": {"rowIndex": i, "columnIndex": 0}}})
    return r


def requests(monday):
    tea = json.loads((ROOT / f"data/tea/{monday}.json").read_text("utf-8"))
    trends = json.loads((ROOT / f"data/weeks/{monday}.json").read_text("utf-8"))
    d = datetime.date.fromisoformat(monday)
    week = f"{d.day} {d:%B %Y}"
    idx = {t["name"]: i for i, t in enumerate(trends, 1)}
    cover = lambda name: f"{SITE}/archive/{monday}/img/{idx[name]}.jpg"
    ever = [t for t in trends if t["longevity"] == "evergreen"]
    seas = [t for t in trends if t["longevity"] != "evergreen"]

    r = [sub("week", week), sub("theme", fits("theme", tea["theme"])), sub("range", f"Week of\n{week}"), sub("src", fits("src", tea["src"]))]
    for k in ("glance_title", "glance_note", "story_title", "lang_title", "lang_note", "case_title", "case_story", "brand_title", "brand_num", "brand_label", "brand_use", "brand_risk"):
        r.append(sub(k, fits(k, tea[k])))
    r.append(sub("story_bullets", fits("story_bullets", "\n".join(tea["story_bullets"]))))
    for i, (n, label) in enumerate(tea["glance"], 1):
        r += [sub(f"n{i}", str(n)), sub(f"l{i}", fits("label", label))]
    for i, m in enumerate(tea["moments"], 1):
        r += [sub(f"m{i}_head", fits("head", m["head"])), sub(f"m{i}_text", fits("text", m["text"])), pic(f"img_m{i}", m.get("img") or cover(m["trend"]))]
    for i, (when, what) in enumerate(tea["case_steps"], 1):
        r += [sub(f"c{i}_when", fits("when", when)), sub(f"c{i}_what", fits("what", what))]
    r += [pic("img_story", cover(tea["story_trend"])), pic("img_case", cover(tea["case_trend"]))]
    for tab, page, rows, key in (("t1_tab", "sl_t1", ever[:6], "tbl1"), ("t2_tab", "sl_t2", ever[6:12], "tbl2"), ("t3_tab", "sl_t3", seas[:6], "tbl3")):
        r.append(sub("tbl_title", fits(key, tea[key]), [page]))
        r += table(tab, page, rows, trends, tea, cover)
    for i, (word, where, status) in enumerate(tea["language"], 1):
        r += [sub(f"r{i}_word", word, ["s_lang"]), sub(f"r{i}_where", where, ["s_lang"]), sub(f"r{i}_status", status, ["s_lang"])]
    for i in range(7, len(tea["language"]), -1):
        r.append({"deleteTableRow": {"tableObjectId": "lg_tab", "cellLocation": {"rowIndex": i, "columnIndex": 0}}})
    r.append({"updateTextStyle": {"objectId": "en_ll", "textRange": {"type": "ALL"}, "fields": "link,foregroundColor",
              "style": {"link": {"url": f"{SITE}/archive/{monday}/"}, "foregroundColor": {"opaqueColor": {"rgbColor": rgb(BERRY)}}}}})
    return r


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    weeks = sorted(p.stem for p in (ROOT / "data/tea").glob("*.json"))
    req = requests(sys.argv[1] if len(sys.argv) > 1 else weeks[-1])
    print(json.dumps(req, ensure_ascii=False, separators=(",", ":")))
