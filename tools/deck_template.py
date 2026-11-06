"""One-off: prints the Google Slides batches that draw 'The Weekly Tea (template)' (ids in tools/deck.py).
Only needed if the template is lost or redesigned. Weekly decks are copies of it, filled by tools/deck.py.
Usage: python tools/deck_template.py <batch 0|1|2>"""
import json, sys

ROSE, BONE, CREAM, CARD, CHAR, BERRY, MUTE = "D4A5BE", "E8E4DD", "F9F4F0", "F1E4E6", "242322", "9C1F52", "6F6A68"
HEAD, BODY = "Fraunces", "Inter Tight"
EMU = 914400


def rgb(h): return {"red": round(int(h[:2], 16) / 255, 3), "green": round(int(h[2:4], 16) / 255, 3), "blue": round(int(h[4:], 16) / 255, 3)}
def pt(n): return {"magnitude": n, "unit": "PT"}


def slide(sid, bg):
    return [{"createSlide": {"objectId": sid, "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
            {"updatePageProperties": {"objectId": sid, "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(bg)}}}}, "fields": "pageBackgroundFill"}}]


def box(page, oid, x, y, w, h, text=None, size=14, font=BODY, bold=False, color=CHAR, align=None, fill=None, kind="TEXT_BOX", anchor=None, bullets=False):
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
        if bullets:
            r.append({"createParagraphBullets": {"objectId": oid, "textRange": {"type": "ALL"}, "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})
    return r


def title(page, text, h=1.1, size=28):
    return box(page, page + "_ti", .5, .35, 9, h, text, size, HEAD, True)


def img(page, oid, x, y, w, h, token):  # tools/deck.py swaps the {{token}} shape for a picture, cropped to this frame
    return box(page, oid, x, y, w, h, "{{%s}}" % token, 10, color=MUTE, fill=CARD, kind="RECTANGLE")


def table(page, oid, y, widths, head, tokens, rows, size, row_h, right=()):
    """Styles the header and first row only: rows inserted below a styled row inherit its text style."""
    r = [{"createTable": {"objectId": oid, "rows": 2, "columns": len(widths), "elementProperties": {"pageObjectId": page,
          "size": {"width": {"magnitude": int(sum(widths) * EMU), "unit": "EMU"}, "height": {"magnitude": int(row_h * 2 * EMU), "unit": "EMU"}},
          "transform": {"scaleX": 1, "scaleY": 1, "translateX": int(.5 * EMU), "translateY": int(y * EMU), "unit": "EMU"}}}}]
    for c, w in enumerate(widths):
        r.append({"updateTableColumnProperties": {"objectId": oid, "columnIndices": [c], "tableColumnProperties": {"columnWidth": {"magnitude": int(w * EMU), "unit": "EMU"}}, "fields": "columnWidth"}})
    for i in range(2):
        for c in range(len(widths)):
            cell = {"rowIndex": i, "columnIndex": c}
            r.append({"insertText": {"objectId": oid, "cellLocation": cell, "text": head[c] if i == 0 else "{{r1_%s}}" % tokens[c]}})
            r.append({"updateTextStyle": {"objectId": oid, "cellLocation": cell, "textRange": {"type": "ALL"}, "fields": "fontFamily,fontSize,bold,foregroundColor",
                      "style": {"fontFamily": BODY, "fontSize": pt(size), "bold": i == 0 or c == 0, "foregroundColor": {"opaqueColor": {"rgbColor": rgb(CHAR)}}}}})
    edge = {"tableBorderFill": {"solidFill": {"color": {"rgbColor": rgb(CREAM)}}}, "weight": pt(.25)}
    line = {"tableBorderFill": {"solidFill": {"color": {"rgbColor": rgb("D9CFCC")}}}, "weight": pt(.75)}
    for pos, props in (("ALL", edge), ("INNER_HORIZONTAL", line), ("BOTTOM", line)):
        r.append({"updateTableBorderProperties": {"objectId": oid, "borderPosition": pos, "tableBorderProperties": props, "fields": "tableBorderFill,weight"}})
    r.append({"insertTableRows": {"tableObjectId": oid, "cellLocation": {"rowIndex": 1, "columnIndex": 0}, "insertBelow": True, "number": rows - 1}})
    for i in range(2, rows + 1):
        for c, t in enumerate(tokens):
            r.append({"insertText": {"objectId": oid, "cellLocation": {"rowIndex": i, "columnIndex": c}, "text": "{{r%d_%s}}" % (i, t)}})
    for c in right:
        for i in range(rows + 1):
            r.append({"updateParagraphStyle": {"objectId": oid, "cellLocation": {"rowIndex": i, "columnIndex": c}, "textRange": {"type": "ALL"}, "style": {"alignment": "END"}, "fields": "alignment"}})
    return r


def b0():
    r = slide("s_cover", ROSE)
    r += box("s_cover", "cv_saucer", 4.75, .45, 4.7, 4.7, fill=BONE, kind="ELLIPSE")
    r += box("s_cover", "cv_handle", 8.1, 2.6, 1.05, .4, fill=CREAM, kind="ROUND_RECTANGLE")
    r += box("s_cover", "cv_cup", 5.6, 1.3, 3, 3, fill=CREAM, kind="ELLIPSE")
    r += box("s_cover", "cv_tea", 5.85, 1.55, 2.5, 2.5, fill=BERRY, kind="ELLIPSE")
    r += box("s_cover", "cv_title", .5, 1.0, 4.2, 3.0, "The\nWeekly\nTea", 54, HEAD, True)
    r += box("s_cover", "cv_week", .5, 4.6, 4.2, .45, "Week of {{week}}", 14)
    r += slide("s_intro", ROSE)
    r += box("s_intro", "in_text", .5, .5, 9, 4.6, "This is a little haven where we talk about what’s currently trending across social media & culture. I’ll be keeping this as a library of culture so we can look back on trends that have come and gone.", 30, HEAD, anchor="MIDDLE")
    r += slide("s_div", CHAR)
    r += box("s_div", "dv_theme", .5, .5, 9, .6, "{{theme}}", 18, color=CREAM)
    r += box("s_div", "dv_range", .5, 1.5, 9, 3.4, "{{range}}", 60, HEAD, True, CREAM, anchor="BOTTOM")
    r += slide("s_glance", CREAM) + title("s_glance", "{{glance_title}}")
    for i, x in enumerate((.5, 2.8, 5.1, 7.4), 1):
        r += box("s_glance", f"gl_c{i}", x, 1.7, 2.1, 1.75, fill=CARD, kind="ROUND_RECTANGLE")
        r += box("s_glance", f"gl_n{i}", x + .1, 1.8, 1.9, .85, "{{n%d}}" % i, 40, HEAD, True, BERRY)
        r += box("s_glance", f"gl_l{i}", x + .1, 2.65, 1.9, .7, "{{l%d}}" % i, 14)
    r += box("s_glance", "gl_note", .5, 3.7, 9, 1.3, "{{glance_note}}", 16)
    r += slide("s_story", CREAM) + title("s_story", "{{story_title}}")
    r += img("s_story", "st_img", .5, 1.6, 2.6, 3.4, "img_story")
    r += box("s_story", "st_body", 3.4, 1.6, 6.1, 3.4, "{{story_bullets}}", 16, bullets=True)
    r += box("s_story", "st_src", .5, 5.1, 9, .3, "{{src}}", 10, color=MUTE)
    return r


def b1():
    r = slide("s_mom", CREAM) + title("s_mom", "Social media moments worth mentioning", .6)
    r += box("s_mom", "mo_sub", .5, .9, 9, .35, "Would you like a side with that?", 14)
    for i, x in enumerate((.5, 2.8, 5.1, 7.4), 1):
        r += img("s_mom", f"mo_i{i}", x, 1.35, 2.1, 1.75, f"img_m{i}")
        r += box("s_mom", f"mo_h{i}", x - .1, 3.15, 2.3, .5, "{{m%d_head}}" % i, 12, bold=True)
        r += box("s_mom", f"mo_b{i}", x - .1, 3.6, 2.3, 1.5, "{{m%d_text}}" % i, 11)
    r += box("s_mom", "mo_src", .5, 5.1, 9, .3, "{{src}}", 10, color=MUTE)
    r += slide("sl_t1", CREAM) + box("sl_t1", "t1_ti", .5, .35, 9, .75, "{{tbl_title}}", 24, HEAD, True)
    r += table("sl_t1", "t1_tab", 1.1, [2.1, 2.2, .95, .75, 3.0], ["Trend", "Audio", "Status", "Videos", "Context"], ["name", "audio", "status", "n", "ctx"], 6, 11, .56, right=(3,))
    r += box("sl_t1", "t1_src", .5, 5.1, 9, .3, "{{src}}", 10, color=MUTE)
    for n in (3, 2):  # each copy lands straight after the original, so 3 goes first
        r.append({"duplicateObject": {"objectId": "sl_t1", "objectIds": {"sl_t1": f"sl_t{n}", "t1_tab": f"t{n}_tab", "t1_ti": f"t{n}_ti", "t1_src": f"t{n}_src"}}})
    return r


def b2():
    r = slide("s_lang", CREAM) + title("s_lang", "{{lang_title}}", .75, 24)
    r += table("s_lang", "lg_tab", 1.1, [4, 2.5, 2.5], ["Word or phrase", "Location", "Status"], ["word", "where", "status"], 7, 14, .46)
    r += box("s_lang", "lg_src", .5, 5.1, 9, .3, "{{lang_note}}", 10, color=MUTE)
    r += slide("s_cdiv", ROSE)
    r += box("s_cdiv", "cd_aa", .5, 1.3, 9, .9, "Trend Case Study:", 40, HEAD, True)
    r += box("s_cdiv", "cd_bb", .5, 2.2, 9, 1.8, "{{case_title}}", 30, HEAD)
    r += slide("s_case", CREAM) + title("s_case", "{{case_story}}")
    r += img("s_case", "cs_img", .5, 1.6, 2.4, 3.4, "img_case")
    for i in range(1, 5):
        y = 1.6 + (i - 1) * .87
        r += box("s_case", f"cs_d{i}", 3.2, y, 1.4, .75, "{{c%d_when}}" % i, 14, bold=True, color=BERRY)
        r += box("s_case", f"cs_t{i}", 4.6, y, 4.9, .75, "{{c%d_what}}" % i, 14)
    r += box("s_case", "cs_src", .5, 5.1, 9, .3, "{{src}}", 10, color=MUTE)
    r += slide("s_brand", CREAM) + title("s_brand", "{{brand_title}}")
    r += box("s_brand", "br_cd", .5, 1.6, 3, 3.4, fill=CHAR, kind="ROUND_RECTANGLE")
    r += box("s_brand", "br_nm", .65, 2.0, 2.7, 1.1, "{{brand_num}}", 44, HEAD, True, CREAM)
    r += box("s_brand", "br_lb", .65, 3.1, 2.7, 1.6, "{{brand_label}}", 14, color=CREAM)
    for oid, y, head, tok in (("br_a", 1.6, "How a brand could run it", "brand_use"), ("br_b", 3.4, "Watch out", "brand_risk")):
        r += box("s_brand", oid + "c", 3.8, y, 5.7, 1.6, fill=CARD, kind="ROUND_RECTANGLE")
        r += box("s_brand", oid + "h", 3.95, y + .1, 5.4, .4, head, 14, bold=True, color=BERRY)
        r += box("s_brand", oid + "t", 3.95, y + .47, 5.4, 1.05, "{{%s}}" % tok, 14)
    r += slide("s_end", CREAM)
    r += box("s_end", "en_tt", .5, 1.1, 9, 2.6, "See you next\nweek :)", 60, HEAD, True, BERRY)
    r += box("s_end", "en_ll", .5, 4.2, 9, .45, "Full report with every example and source", 14)
    return r


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps([b0, b1, b2][int(sys.argv[1])](), ensure_ascii=False, separators=(",", ":")))
