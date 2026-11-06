"""One-off: prints the Google Slides batches that draw the deck template (id in tools/deck.py).
Only needed if the template is lost or redesigned. Weekly decks are copies of it, filled by tools/deck.py.
Usage: python tools/deck_template.py <batch 0|1|2>"""
import json, sys

POOL, PLASTER, TERRA, SUN, AQUA, INK, SAND, MUTE = "0E4A5A", "F7F0E4", "C8553D", "F2B134", "7CC6CF", "14303A", "E8DCC6", "6B7A80"
HEAD, BODY, MONO = "Bricolage Grotesque", "DM Sans", "DM Mono"
EMU = 914400


def rgb(h): return {"red": round(int(h[:2], 16) / 255, 3), "green": round(int(h[2:4], 16) / 255, 3), "blue": round(int(h[4:], 16) / 255, 3)}
def pt(n): return {"magnitude": n, "unit": "PT"}


def slide(sid, bg):
    return [{"createSlide": {"objectId": sid, "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
            {"updatePageProperties": {"objectId": sid, "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(bg)}}}}, "fields": "pageBackgroundFill"}}]


def box(page, oid, x, y, w, h, text=None, size=14, font=BODY, bold=False, color=INK, align=None, fill=None, kind="TEXT_BOX", anchor=None, gap=None):
    r = [{"createShape": {"objectId": oid, "shapeType": kind, "elementProperties": {"pageObjectId": page,
          "size": {"width": {"magnitude": int(w * EMU), "unit": "EMU"}, "height": {"magnitude": int(h * EMU), "unit": "EMU"}},
          "transform": {"scaleX": 1, "scaleY": 1, "translateX": int(x * EMU), "translateY": int(y * EMU), "unit": "EMU"}}}}]
    if fill:
        r.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": {"shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(fill)}}},
                  "outline": {"propertyState": "NOT_RENDERED"}}, "fields": "shapeBackgroundFill,outline"}})
    if anchor:
        r.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": {"contentAlignment": anchor}, "fields": "contentAlignment"}})
    if text:
        r += [{"insertText": {"objectId": oid, "text": text}},
              {"updateTextStyle": {"objectId": oid, "textRange": {"type": "ALL"}, "fields": "fontFamily,fontSize,bold,foregroundColor",
               "style": {"fontFamily": font, "fontSize": pt(size), "bold": bold, "foregroundColor": {"opaqueColor": {"rgbColor": rgb(color)}}}}}]
        if align:
            r.append({"updateParagraphStyle": {"objectId": oid, "textRange": {"type": "ALL"}, "style": {"alignment": align}, "fields": "alignment"}})
        if gap:
            r.append({"updateParagraphStyle": {"objectId": oid, "textRange": {"type": "ALL"}, "style": {"spaceBelow": pt(gap)}, "fields": "spaceBelow"}})
    return r


def kicker(page, text, color=TERRA, x=.4):
    return box(page, page + "_k", x, .28, 7, .3, text, 10, MONO, color=color)


def src(page, token="src", color=MUTE, w=9.2):
    return box(page, page + "_s", .4, 5.2, w, .3, "{{%s}}" % token, 9, color=color)


def img(page, oid, x, y, w, h, token):  # tools/deck.py swaps the {{token}} shape for a picture, cropped to this frame
    return box(page, oid, x, y, w, h, "{{%s}}" % token, 9, color=MUTE, fill=SAND, kind="RECTANGLE")


def arch(page, oid, x, top, w, fill):
    """A villa arch: a circle on a rectangle that runs off the bottom of the slide."""
    return box(page, oid + "_a", x, top, w, w, fill=fill, kind="ELLIPSE") + box(page, oid + "_b", x, top + w / 2, w, 5.625 - top - w / 2, fill=fill, kind="RECTANGLE")


def table(page, oid, x, y, widths, head, tokens, rows, size, row_h, right=()):
    """Styles the header and first row only: rows inserted below a styled row inherit its text style."""
    r = [{"createTable": {"objectId": oid, "rows": 2, "columns": len(widths), "elementProperties": {"pageObjectId": page,
          "size": {"width": {"magnitude": int(sum(widths) * EMU), "unit": "EMU"}, "height": {"magnitude": int(row_h * 2 * EMU), "unit": "EMU"}},
          "transform": {"scaleX": 1, "scaleY": 1, "translateX": int(x * EMU), "translateY": int(y * EMU), "unit": "EMU"}}}}]
    for c, w in enumerate(widths):
        r.append({"updateTableColumnProperties": {"objectId": oid, "columnIndices": [c], "tableColumnProperties": {"columnWidth": {"magnitude": int(w * EMU), "unit": "EMU"}}, "fields": "columnWidth"}})
    for i in range(2):
        for c in range(len(widths)):
            cell = {"rowIndex": i, "columnIndex": c}
            r.append({"insertText": {"objectId": oid, "cellLocation": cell, "text": head[c] if i == 0 else "{{%s1_%s}}" % (oid[0], tokens[c])}})
            r.append({"updateTextStyle": {"objectId": oid, "cellLocation": cell, "textRange": {"type": "ALL"}, "fields": "fontFamily,fontSize,bold,foregroundColor",
                      "style": {"fontFamily": MONO if i == 0 else BODY, "fontSize": pt(size - 1 if i == 0 else size), "bold": i == 1 and c == 0, "foregroundColor": {"opaqueColor": {"rgbColor": rgb(MUTE if i == 0 else INK)}}}}})
    edge = {"tableBorderFill": {"solidFill": {"color": {"rgbColor": rgb(PLASTER)}}}, "weight": pt(.25)}
    line = {"tableBorderFill": {"solidFill": {"color": {"rgbColor": rgb("D3C6AE")}}}, "weight": pt(.75)}
    for pos, props in (("ALL", edge), ("INNER_HORIZONTAL", line), ("BOTTOM", line)):
        r.append({"updateTableBorderProperties": {"objectId": oid, "borderPosition": pos, "tableBorderProperties": props, "fields": "tableBorderFill,weight"}})
    r.append({"insertTableRows": {"tableObjectId": oid, "cellLocation": {"rowIndex": 1, "columnIndex": 0}, "insertBelow": True, "number": rows - 1}})
    for i in range(2, rows + 1):
        for c, t in enumerate(tokens):
            r.append({"insertText": {"objectId": oid, "cellLocation": {"rowIndex": i, "columnIndex": c}, "text": "{{%s%d_%s}}" % (oid[0], i, t)}})
    for c in right:
        for i in range(rows + 1):
            r.append({"updateParagraphStyle": {"objectId": oid, "cellLocation": {"rowIndex": i, "columnIndex": c}, "textRange": {"type": "ALL"}, "style": {"alignment": "END"}, "fields": "alignment"}})
    return r


def b0():
    r = slide("v_cover", POOL) + [{"deleteObject": {"objectId": "p"}}]  # the blank slide a new file starts with
    r += arch("v_cover", "cv_o", 5.5, .55, 3.9, TERRA) + arch("v_cover", "cv_m", 6.0, 1.05, 2.9, PLASTER) + arch("v_cover", "cv_i", 6.5, 1.55, 1.9, AQUA)
    r += box("v_cover", "cv_sun", 7.05, 2.1, .8, .8, fill=SUN, kind="ELLIPSE") + box("v_cover", "cv_sea", 6.5, 3.75, 1.9, 1.875, fill=POOL, kind="RECTANGLE")
    r += box("v_cover", "cv_kk", .4, .28, 5, .3, "WEEKLY TREND REPORT", 10, MONO, color=SUN)
    r += box("v_cover", "cv_tt", .4, 1.1, 5, 2.3, "This Week\nin the Villa", 50, HEAD, True, PLASTER)
    r += box("v_cover", "cv_th", .4, 3.5, 4.8, .8, "{{theme}}", 16, color=PLASTER)
    r += box("v_cover", "cv_wk", .4, 5.0, 4.8, .3, "Week of {{week}}", 10, MONO, color=SUN)
    r += slide("v_week", PLASTER) + kicker("v_week", "THE WEEK IN ONE LOOK")
    r += box("v_week", "wk_ti", .4, .6, 9.2, 1.3, "{{glance_title}}", 32, HEAD, True)
    for i, x in enumerate((.5, 2.8, 5.1, 7.4), 1):
        r += box("v_week", f"wk_r{i}", x, 2.15, 2.1, .02, fill=INK, kind="RECTANGLE")
        r += box("v_week", f"wk_n{i}", x - .1, 2.2, 2.3, .95, "{{n%d}}" % i, 50, HEAD, True, TERRA)
        r += box("v_week", f"wk_l{i}", x - .1, 3.15, 2.3, .4, "{{l%d}}" % i, 12)
    r += box("v_week", "wk_nt", .4, 3.8, 9.2, 1.1, "{{glance_note}}", 15)
    r += src("v_week")
    r += slide("v_story", POOL) + img("v_story", "st_img", 6.0, 0, 4, 5.625, "img_story") + kicker("v_story", "THE BIG STORY", SUN)
    r += box("v_story", "st_ti", .4, .6, 5.4, 1.5, "{{story_title}}", 28, HEAD, True, PLASTER)
    r += box("v_story", "st_bd", .4, 2.15, 5.4, 2.95, "{{story_bullets}}", 13, color=PLASTER, gap=7)
    r += src("v_story", color=AQUA, w=5.4)
    return r


def b1():
    r = slide("v_mom", PLASTER) + kicker("v_mom", "MOMENTS WORTH KNOWING")
    r += box("v_mom", "mo_ti", .4, .55, 9.2, .6, "Four moments that shaped the week", 26, HEAD, True)
    for i, x in enumerate((.5, 2.8, 5.1, 7.4), 1):
        r += img("v_mom", f"mo_i{i}", x, 1.25, 2.1, 1.85, f"img_m{i}")
        r += box("v_mom", f"mo_h{i}", x - .1, 3.15, 2.3, .6, "{{m%d_head}}" % i, 12, bold=True)
        r += box("v_mom", f"mo_b{i}", x - .1, 3.72, 2.3, 1.35, "{{m%d_text}}" % i, 10.5)
    r += src("v_mom")
    page = "v_tr1"
    r += slide(page, PLASTER) + kicker(page, "{{kick}}")
    r += box(page, "a_ttl", .4, .52, 9.2, .5, "{{t_title}}", 22, HEAD, True)
    ids = {page: "v_tr2", "v_tr1_k": "v_tr2_k", "v_tr1_s": "v_tr2_s", "a_ttl": "b_ttl"}
    for i in range(1, 7):
        x = .5 + (i - 1) * 1.52
        r += img(page, f"a_im{i}", x, 1.05, 1.4, 1.95, f"img_c{i}")
        r += box(page, f"a_pl{i}", x, 3.06, .92, .22, "{{c%d_status}}" % i, 8, MONO, fill=SAND, kind="ROUND_RECTANGLE", align="CENTER", anchor="MIDDLE")
        r += box(page, f"a_ct{i}", x + .55, 3.02, .95, .3, "{{c%d_n}}" % i, 9, MONO, align="END")
        r += box(page, f"a_nm{i}", x - .1, 3.27, 1.6, .6, "{{c%d_name}}" % i, 10.5, bold=True)
        r += box(page, f"a_cx{i}", x - .1, 3.83, 1.6, .85, "{{c%d_ctx}}" % i, 9)
        r += box(page, f"a_sd{i}", x - .1, 4.68, 1.6, .45, "{{c%d_audio}}" % i, 8, MONO, color=MUTE)
        ids.update({f"a_{k}{i}": f"b_{k}{i}" for k in ("im", "pl", "ct", "nm", "cx", "sd")})
    r += src(page)
    r.append({"duplicateObject": {"objectId": page, "objectIds": ids}})
    r += slide("v_peak", POOL) + kicker("v_peak", "WHAT'S PEAKING", SUN)
    r += box("v_peak", "pk_ti", .4, .55, 9.2, .7, "{{peak_title}}", 24, HEAD, True, PLASTER)
    for i, (st, c) in enumerate((("Rising", AQUA), ("Peaking", TERRA), ("Steady", SAND), ("Past peak", MUTE))):
        x, k = .5 + i * 2.3, st.split()[0].lower()
        r += box("v_peak", f"pk_b{k}", x, 1.4, 2.1, .06, fill=c, kind="RECTANGLE")
        r += box("v_peak", f"pk_h{k}", x - .1, 1.48, 2.3, .4, st + "  {{%s_n}}" % k, 13, HEAD, True, PLASTER)
        r += box("v_peak", f"pk_l{k}", x - .1, 1.9, 2.3, 3.25, "{{%s_list}}" % k, 10, color=PLASTER, gap=3)
    r += src("v_peak", color=AQUA)
    return r


def b2():
    r = slide("v_date", PLASTER) + kicker("v_date", "ON THE CLOCK")
    r += box("v_date", "dt_ti", .4, .55, 9.2, .6, "{{date_title}}", 24, HEAD, True)
    r += table("v_date", "d_tab", .5, 1.3, [2.9, 2.9, .95, .75, 1.5], ["TREND", "AUDIO", "STATUS", "VIDEOS", "RUNS TO"], ["name", "audio", "status", "n", "ends"], 6, 11, .5, right=(3,))
    r += src("v_date")
    r += slide("v_word", PLASTER) + kicker("v_word", "THE WORDS")
    r += box("v_word", "wd_ti", .4, .55, 9.2, .6, "{{lang_title}}", 22, HEAD, True)
    r += table("v_word", "w_tab", .5, 1.25, [1.5, .95, .8, .75], ["WORD", "STATUS", "LOOKUPS", "CHANGE"], ["word", "status", "n", "chg"], 8, 10, .39, right=(2, 3))
    r += img("v_word", "wd_img", 4.8, 1.3, 4.7, 3.58, "img_words")
    r += src("v_word", "lang_note")
    r += slide("v_case", PLASTER) + img("v_case", "cs_img", 0, 0, 3.6, 5.625, "img_case") + kicker("v_case", "CASE STUDY", x=3.8)
    r += box("v_case", "cs_ti", 3.8, .55, 5.8, 1.2, "{{case_title}}", 24, HEAD, True)
    for i in range(1, 5):
        y = 1.85 + (i - 1) * .8
        r += box("v_case", f"cs_d{i}", 3.8, y, 1.3, .7, "{{c%d_when}}" % i, 10, MONO, color=TERRA)
        r += box("v_case", f"cs_t{i}", 5.05, y - .04, 4.55, .75, "{{c%d_what}}" % i, 13)
    r += box("v_case", "cs_sr", 3.8, 5.2, 5.8, .3, "{{src}}", 9, color=MUTE)
    r += slide("v_play", SUN) + kicker("v_play", "THE PLAY", INK)
    r += box("v_play", "pl_ti", .4, .55, 9.2, 1.2, "{{brand_title}}", 28, HEAD, True)
    r += box("v_play", "pl_nm", .4, 1.85, 3.4, 1.5, "{{brand_num}}", 76, HEAD, True)
    r += box("v_play", "pl_lb", .4, 3.4, 3.2, 1.3, "{{brand_label}}", 13)
    for oid, x, head, tok in (("pl_a", 3.9, "RUN IT", "brand_use"), ("pl_b", 6.8, "WATCH OUT", "brand_risk")):
        r += box("v_play", oid + "r", x + .1, 2.0, 2.6, .02, fill=INK, kind="RECTANGLE")
        r += box("v_play", oid + "h", x, 2.05, 2.8, .35, head, 10, MONO)
        r += box("v_play", oid + "t", x, 2.4, 2.8, 2.6, "{{%s}}" % tok, 13)
    r += slide("v_end", POOL) + arch("v_end", "en_o", 6.6, 1.3, 2.8, TERRA) + arch("v_end", "en_i", 7.2, 1.9, 1.6, AQUA)
    r += box("v_end", "en_tt", .4, 1.5, 6, 1.8, "Back next\nWednesday", 50, HEAD, True, PLASTER)
    r += box("v_end", "en_ll", .4, 3.6, 6, .4, "Full report, every example and source", 14, color=SUN)
    return r


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps([b0, b1, b2][int(sys.argv[1])](), ensure_ascii=False, separators=(",", ":")))
