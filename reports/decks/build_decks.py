"""Builds the FORESIGHT executive readout and pitch deck as native, editable PPTX.

Every rupee figure is computed here from artifacts/risk_snapshot.csv.
Forecast accuracy comes from a verified re-run of src/backtest.py (4 folds, H=8):
the committed artifacts/metrics.json is stale (test-run output) and is not used.

Run:  python reports/decks/build_decks.py
"""
from pathlib import Path

import pandas as pd
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

# ---------- source numbers ----------
r = pd.read_csv(ROOT / "artifacts" / "risk_snapshot.csv")
RO = r[r.action == "REORDER NOW"].sort_values("sales_at_risk_inr", ascending=False)
MD = r[r.action == "MARKDOWN / CLEAR"].sort_values("capital_locked_inr", ascending=False)
N_SKU, N_RO, N_MD = len(r), len(RO), len(MD)
N_OK = N_SKU - N_RO - N_MD
SAR = RO.sales_at_risk_inr.sum()                       # sales at risk, reorder quadrant
LOCKED = MD.capital_locked_inr.sum()                   # cash locked, markdown quadrant
PO_COST = (RO.stockout_gap_units * RO.unit_cost).sum() # cost to close every gap
TOP5 = RO.sales_at_risk_inr.head(5).sum() / SAR
TOP_MD = MD.iloc[0]
MIN_MARGIN = (r.unit_price / r.unit_cost).min()
EX = RO.iloc[0]                                        # worked example SKU
LT_MIN, LT_MAX = r.lead_time_days.min(), r.lead_time_days.max()

# Verified backtest re-run (WAPE, share of units sold)
WAPE = {"Same week\nlast year": 0.3317, "Linear\nmodel": 0.2319,
        "Gradient\nboosting": 0.2095, "Random forest\n(selected)": 0.2079}
BASE, BEST, BIAS = 0.3317, 0.2079, -0.0081
ERR_CUT = (BASE - BEST) / BASE

L = lambda v: f"₹{v / 1e5:.1f} L"                     # lakh
assert N_RO == 10 and N_MD == 9 and abs(ERR_CUT - 0.373) < 0.001
assert MIN_MARGIN * 0.8 > 1  # 20% markdown still sells above cost

# ---------- design system ----------
INK, MUTED, RULE = RGBColor(0x1B, 0x1F, 0x24), RGBColor(0x5F, 0x6B, 0x7A), RGBColor(0xD5, 0xDA, 0xE1)
NAVY, RED, AMBER = RGBColor(0x1F, 0x3A, 0x5F), RGBColor(0xB4, 0x23, 0x18), RGBColor(0xB7, 0x6E, 0x00)
GREY, TINT, WHITE = RGBColor(0xC9, 0xCF, 0xD6), RGBColor(0xF3, 0xF5, 0xF7), RGBColor(0xFF, 0xFF, 0xFF)
HEAD, BODY = "Georgia", "Calibri"
X0, CW = 0.65, 12.03  # left margin, content width (inches)


def text(sh, x, y, w, h, s, size=14, color=INK, bold=False, font=BODY,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
    tb = sh.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(s.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing:
            p.space_after = Pt(spacing)
        run = p.add_run()
        run.text = line
        f = run.font
        f.size, f.bold, f.name, f.color.rgb = Pt(size), bold, font, color
    return tb


def rule(sh, x, y, w, color=RULE, weight=0.75, vertical=False):
    ln = sh.add_connector(1, Inches(x), Inches(y),
                          Inches(x if vertical else x + w), Inches(y + w if vertical else y))
    ln.line.color.rgb, ln.line.width = color, Pt(weight)
    return ln


def box(sh, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE):
    b = sh.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        b.fill.background()
    else:
        b.fill.solid()
        b.fill.fore_color.rgb = fill
    if line is None:
        b.line.fill.background()
    else:
        b.line.color.rgb, b.line.width = line, Pt(1)
    b.shadow.inherit = False
    return b


def arrow(sh, x, y, w=0.45):
    a = box(sh, x, y - 0.11, w, 0.22, fill=GREY, shape=MSO_SHAPE.RIGHT_ARROW)
    return a


def fade(slide, shapes):
    """Native 'Fade' entrance, one click per shape/group, in order."""
    ids = iter(range(3, 1000))
    clicks = ""
    for s in shapes:
        a, b, c, d = next(ids), next(ids), next(ids), next(ids)
        clicks += f'''<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>
<p:par><p:cTn id="{b}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:par><p:cTn id="{c}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="clickEffect">
<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:set><p:cBhvr><p:cTn id="{d}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
<p:tgtEl><p:spTgt spid="{s.shape_id}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>
<p:to><p:strVal val="visible"/></p:to></p:set>
<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{next(ids)}" dur="400"/>
<p:tgtEl><p:spTgt spid="{s.shape_id}"/></p:tgtEl></p:cBhvr></p:animEffect>
</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'''
    xml = f'''<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:tnLst><p:par>
<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{clicks}</p:childTnLst></p:cTn>
<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'''
    slide._element.append(etree.fromstring(xml))


class Deck:
    def __init__(self, footer):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
        self.footer, self.n = footer, 0

    def slide(self, stage, headline, source="", notes=""):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.n += 1
        sh = s.shapes
        if stage:
            text(sh, X0, 0.42, 8, 0.3, stage.upper(), 10, NAVY, bold=True)
        if headline:
            text(sh, X0, 0.72, CW, 1.1, headline, 26, INK, font=HEAD, anchor=MSO_ANCHOR.TOP)
        rule(sh, X0, 6.95, CW)
        text(sh, X0, 7.02, 10.5, 0.3, source or self.footer, 9, MUTED)
        text(sh, 12.18, 7.02, 0.5, 0.3, str(self.n), 9, MUTED, align=PP_ALIGN.RIGHT)
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s, sh

    def save(self, name):
        self.prs.save(OUT / name)
        print("saved", OUT / name)


def bar_chart(sh, x, y, w, h, cats, vals, colors, fmt, horizontal=True, font=12, gap=55):
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("v", vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    ch = sh.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    ch.has_legend = ch.has_title = False
    ch.font.size, ch.font.name, ch.font.color.rgb = Pt(font), BODY, INK
    va, ca = ch.value_axis, ch.category_axis
    va.visible, va.has_major_gridlines = False, False
    va.minimum_scale = 0
    ca.format.line.color.rgb = RULE
    ca.has_major_gridlines = False
    from pptx.enum.chart import XL_TICK_MARK
    ca.major_tick_mark = XL_TICK_MARK.NONE
    if horizontal:
        ca.reverse_order = True
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format, dl.number_format_is_linked = fmt, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size, dl.font.bold = Pt(font), True
    for i, c in enumerate(colors):
        pt = plot.series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c
    return ch


def table(sh, x, y, w, rows, col_w, header_fill=None, size=13, row_h=0.62, bold_col=None):
    t = sh.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w),
                     Inches(row_h * len(rows))).table
    tblPr = t._tbl.tblPr
    tblPr.set("firstRow", "0")
    tblPr.set("bandRow", "0")
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # "No Style, Table Grid" -> we then clear borders
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = header_fill if (i == 0 and header_fill) else WHITE
            c.margin_left, c.margin_right = Inches(0.08), Inches(0.08)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame
            tf.word_wrap = True
            tf.text = str(val)
            for p in tf.paragraphs:
                for run in p.runs:
                    f = run.font
                    f.name, f.size = BODY, Pt(size if i else size - 2)
                    f.bold = i == 0 or j == bold_col
                    f.color.rgb = (WHITE if header_fill else MUTED) if i == 0 else INK
            # hairline bottom border only
            tcPr = c._tc.get_or_add_tcPr()
            for k, tag in enumerate(("a:lnL", "a:lnR", "a:lnT", "a:lnB")):  # must precede the fill
                ln = etree.Element(qn(tag), w="9525" if tag == "a:lnB" else "0")
                tcPr.insert(k, ln)
                if tag == "a:lnB":
                    sf = etree.SubElement(ln, qn("a:solidFill"))
                    etree.SubElement(sf, qn("a:srgbClr"), val="D5DAE1")
                else:
                    etree.SubElement(ln, qn("a:noFill"))
    return t


# ---------- reusable visuals ----------
def unit_chart(sh):
    """40 squares = 40 SKUs, grouped by action. Returns the 3 groups for progressive reveal."""
    groups = []
    spec = [(N_RO, 5, RED, "RUNNING SHORT", L(SAR), "sales at risk before the\nnext supplier delivery", 0.65),
            (N_MD, 5, AMBER, "OVERSTOCKED", L(LOCKED), "cash tied up in stock the next\n12 weeks will not sell", 4.6),
            (N_OK, 7, GREY, "HEALTHY", f"{N_OK} SKUs", "stock covers demand, with\na safety buffer", 8.55)]
    for n, cols, color, label, big, cap, x in spec:
        g = sh.add_group_shape()
        text(g.shapes, x, 2.15, 3.6, 0.3, f"{label}  ·  {n} SKUs", 12, color if color != GREY else MUTED, bold=True)
        for k in range(n):
            box(g.shapes, x + (k % cols) * 0.52, 2.6 + (k // cols) * 0.52, 0.42, 0.42, fill=color)
        text(g.shapes, x, 4.35, 3.6, 0.6, big, 30, INK, font=HEAD)
        text(g.shapes, x, 5.0, 3.6, 0.7, cap, 13, MUTED)
        groups.append(g)
    return groups


def cash_chart(sh):
    bar_chart(sh, X0, 2.2, 7.9, 3.4,
              [f"Cash needed to close all {N_RO} gaps (at cost)",
               f"Cash tied up in the {N_MD} overstocked SKUs (at cost)"],
              [PO_COST / 1e5, LOCKED / 1e5], [NAVY, AMBER], '"₹"0.0" L"', font=14, gap=45)
    x = 9.2
    text(sh, x, 2.2, 3.5, 0.9, f"{LOCKED / PO_COST:.1f}×", 44, AMBER, font=HEAD)
    text(sh, x, 3.1, 3.5, 0.6, "the cash the reorders need", 14, MUTED)
    rule(sh, x, 3.85, 3.4)
    text(sh, x, 4.0, 3.5, 1.4, f"Even at 20% off, excess stock still sells above cost: "
                               f"the lowest-priced SKU sells at {MIN_MARGIN:.1f}× its cost.", 13, INK)
    rule(sh, x, 5.2, 3.4)
    text(sh, x, 5.35, 3.5, 0.9, f"Revenue the reorders protect: {L(SAR)}", 13, INK, bold=True)


def steps(sh, items, y=2.15, top_num=True):
    n = len(items)
    colw = CW / n
    groups = []
    for i, (title, desc) in enumerate(items):
        g = sh.add_group_shape()
        x = X0 + i * colw
        if i:
            rule(g.shapes, x - 0.15, y, 1.9, vertical=True)
        text(g.shapes, x, y, 0.8, 0.6, str(i + 1), 30, NAVY, font=HEAD)
        text(g.shapes, x, y + 0.7, colw - 0.4, 0.5, title, 16, INK, bold=True)
        text(g.shapes, x, y + 1.15, colw - 0.4, 1.2, desc, 13, MUTED)
        groups.append(g)
    return groups


SRC_RISK = "Source: FORESIGHT risk engine, artifacts/risk_snapshot.csv (stock as of 31 Dec 2025, NorthBay Living sample data)."
SRC_BT = ("Source: re-run of FORESIGHT back-test (src/backtest.py), 4 rolling test windows Aug–Dec 2025, "
          "8 weeks each, 40 SKUs. WAPE = total absolute error ÷ total units sold.")


# ======================================================================
# DECK 1 — EXECUTIVE READOUT (CFO / COO)
# ======================================================================
def executive():
    d = Deck("Project FORESIGHT · Executive readout · NorthBay Living sample data")

    # 1 Title
    s, sh = d.slide("", "")
    text(sh, X0, 1.55, 11, 0.3, "EXECUTIVE READOUT  ·  NORTHBAY LIVING  ·  SEPTEMBER 2026", 11, NAVY, bold=True)
    text(sh, X0, 2.05, 11, 1.9, "Fix the stock mix,\nand it pays for itself", 44, INK, font=HEAD)
    text(sh, X0, 4.2, 9.8, 0.9, f"{L(SAR)} of sales at risk and {L(LOCKED)} of cash locked in excess stock, "
                                f"inside the same {N_SKU}-SKU range.", 18, MUTED)
    text(sh, X0, 6.2, 11, 0.3, "Project FORESIGHT  ·  Demand & inventory intelligence  ·  Prepared by Anshul", 12, INK)
    s.notes_slide.notes_text_frame.text = (
        "One sentence: we are not over- or under-buying overall; we are buying the wrong things. "
        "The fix is funded by stock we already own.")

    # 2 Executive summary
    s, sh = d.slide("Executive summary",
                    "Clear the excess, use the cash to reorder, and move buying to a weekly forecast",
                    SRC_RISK, "Read top to bottom: situation, cost, cause, decision. Every number is sourced later in the deck.")
    rows = [("THE SITUATION", f"{N_RO} of {N_SKU} SKUs hold less than half the stock they need to last until the next supplier delivery.", f"{N_RO} SKUs", RED),
            ("", f"{N_MD} SKUs hold far more stock than the next 12 weeks will sell.", f"{N_MD} SKUs", AMBER),
            ("WHAT IT COSTS", f"{L(SAR)} of sales at risk, and {L(LOCKED)} of cash tied up in excess stock.", f"₹{(SAR + LOCKED) / 1e7:.2f} Cr", INK),
            ("WHAT CHANGES IT", f"A forecast that misses by {BEST:.0%} of units sold, against {BASE:.0%} for a same-week-last-year rule.", f"−{ERR_CUT:.0%} error", NAVY),
            ("THE DECISION", f"Approve {L(PO_COST)} of reorders, paid for by clearing excess, plus a 90-day weekly-planning pilot.", "90 days", NAVY)]
    y = 2.0
    for label, stmt, num, col in rows:
        text(sh, X0, y + 0.1, 2.2, 0.4, label, 10, MUTED, bold=True)
        text(sh, 3.0, y, 6.9, 0.8, stmt, 16, INK, anchor=MSO_ANCHOR.MIDDLE)
        text(sh, 10.0, y, 2.68, 0.8, num, 24, col, font=HEAD, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        rule(sh, X0 if label else 3.0, y + 0.88, CW - (0 if label else 2.35))
        y += 0.95

    # 3 Context — before
    s, sh = d.slide("Context",
                    "Today's buying rule averages the last four weeks, so it cannot see seasons or supplier wait times",
                    f"Source: FORESIGHT project report (current planning practice); supplier lead times {LT_MIN}–{LT_MAX} days from inventory snapshot.",
                    "This is the 'before'. The rule is not wrong, it is blind: it looks backward and assumes stock arrives instantly.")
    labels = ["Last 4 weeks\nof sales", "Take the\naverage", "Order roughly\nthe same again"]
    for i, lab in enumerate(labels):
        x = X0 + i * 4.1
        box(sh, x, 2.3, 3.1, 1.2, line=INK)
        text(sh, x, 2.3, 3.1, 1.2, lab, 17, INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 2:
            arrow(sh, x + 3.3, 2.9, 0.6)
    for x, note in [(X0 + 4.1, "Blind to seasonal peaks\nand promotions"),
                    (X0 + 8.2, f"Assumes stock arrives at once;\nsuppliers take {LT_MIN} to {LT_MAX} days")]:
        rule(sh, x + 1.55, 3.5, 0.55, RED, 1.5, vertical=True)
        text(sh, x, 4.15, 3.1, 0.8, note, 14, RED, align=PP_ALIGN.CENTER)
    rule(sh, X0, 5.4, CW)
    text(sh, X0, 5.6, CW, 0.9, f"Result: every SKU gets the same attention, whether ₹0 or "
                               f"{L(EX.sales_at_risk_inr)} is at stake.", 20, INK, font=HEAD)

    # 4 Tension — unit chart
    s, sh = d.slide("Tension",
                    f"One range, two opposite problems: {N_RO} SKUs are running short while {N_MD} sit on excess",
                    SRC_RISK + " Each square is one SKU.",
                    "Click 1: short. Click 2: overstocked. Click 3: healthy. Land the point that both problems exist at the same time.")
    fade(s, unit_chart(sh))
    text(sh, X0, 6.1, CW, 0.6, "The problem is not how much we buy. It is where the money goes.", 18, INK, font=HEAD)

    # 5 Tension — concentration
    s, sh = d.slide("Tension",
                    f"Five SKUs carry {TOP5:.0%} of the revenue at risk, so the first orders are obvious",
                    SRC_RISK + " Sales at risk = shortfall units × selling price.",
                    "Where to act first. The top two alone are ₹24.6 lakh.")
    cats = [f"{row.subcategory} · {row.sku_id[3:]}" for row in RO.itertuples()]
    bar_chart(sh, X0, 1.95, 8.4, 4.85, cats, list(RO.sales_at_risk_inr / 1e5),
              [RED] * 5 + [GREY] * (N_RO - 5), '"₹"0.0" L"', font=12, gap=40)
    x = 9.5
    text(sh, x, 2.1, 3.2, 0.9, f"{TOP5:.0%}", 44, RED, font=HEAD)
    text(sh, x, 3.0, 3.2, 0.6, f"of {L(SAR)} sits in five SKUs", 14, MUTED)
    rule(sh, x, 3.75, 3.2)
    lt5 = RO.head(5).lead_time_days.max()
    text(sh, x, 3.9, 3.2, 1.6, f"Their suppliers take up to {lt5} days. An order placed this week "
                               f"lands in about {lt5 // 7} weeks.", 14, INK)

    # 6 Insight — forecast accuracy
    s, sh = d.slide("Insight",
                    f"The new forecast misses by {BEST:.0%} of units sold; a same-week-last-year rule misses by {BASE:.0%}",
                    SRC_BT,
                    "Simple first: out of every 100 units sold, the model is off by about 21, the benchmark by about 33. "
                    "Bias −0.8% means the model neither pads nor starves orders.")
    bar_chart(sh, X0, 1.95, 7.9, 4.8, list(WAPE), [v * 100 for v in WAPE.values()],
              [MUTED, GREY, GREY, NAVY], '0.0"%"', horizontal=False, font=13, gap=70)
    x = 9.2
    text(sh, x, 2.1, 3.5, 0.9, f"−{ERR_CUT:.0%}", 44, NAVY, font=HEAD)
    text(sh, x, 3.0, 3.5, 0.6, "forecast error versus the benchmark", 14, MUTED)
    rule(sh, x, 3.75, 3.4)
    text(sh, x, 3.9, 3.5, 1.2, "Every point of error becomes a missed sale or stock nobody buys.", 14, INK)
    rule(sh, x, 5.0, 3.4)
    text(sh, x, 5.15, 3.5, 1.2, f"No lean either way: it under-forecasts by just {abs(BIAS):.1%} overall.", 14, INK)

    # 7 Mechanism — progressive reveal
    s, sh = d.slide("How it works",
                    "The engine asks one question per SKU: will stock last until the next delivery arrives?",
                    "Source: FORESIGHT risk engine (src/risk.py, src/impact.py); example row from artifacts/risk_snapshot.csv.",
                    "Reveal one step per click, then the worked example. Technical depth (safety stock = 1.65 σ √L) is in the appendix only if asked.")
    g = steps(sh, [("Forecast demand", "Predicts units sold for each SKU, week by week, 8 weeks ahead."),
                   ("Demand until delivery", "Sums the forecast over the supplier's lead time, plus a buffer that covers 95% of weeks."),
                   ("Compare with stock", "Checks stock on hand and on order against that need."),
                   ("Put a rupee value on it", "Shortfall × price = sales at risk.\nExcess × cost = cash locked.")])
    ex = sh.add_group_shape()
    box(ex.shapes, X0, 4.55, CW, 2.05, fill=TINT)
    text(ex.shapes, X0 + 0.3, 4.72, 11, 0.35,
         f"WORKED EXAMPLE  ·  {EX.subcategory} ({EX.sku_id[3:]}), {EX.lead_time_days}-day supplier lead time", 11, MUTED, bold=True)
    price = EX.sales_at_risk_inr / EX.stockout_gap_units
    eq = [(f"{EX.reorder_level:.0f}", "units needed"), ("−", ""), (f"{EX.available_stock}", "in stock + on order"),
          ("=", ""), (f"{EX.stockout_gap_units:.0f}", "units short"), ("×", ""),
          (f"₹{price:,.0f}", "selling price"), ("=", ""), (L(EX.sales_at_risk_inr), "sales at risk")]
    xs = X0 + 0.3
    for val, cap in eq:
        w = 0.45 if not cap else 1.75
        col = RED if cap == "sales at risk" else (MUTED if not cap else INK)
        text(ex.shapes, xs, 5.2, w, 0.7, val, 28, col, font=HEAD, align=PP_ALIGN.CENTER)
        if cap:
            text(ex.shapes, xs, 5.95, w, 0.4, cap, 11, MUTED, align=PP_ALIGN.CENTER)
        xs += w + 0.08
    fade(s, g + [ex])

    # 8 Implication — self-funding
    s, sh = d.slide("Implication",
                    "Clearing the excess releases twice the cash the reorders need",
                    SRC_RISK + " Reorder cost = shortfall units × unit cost. Assumes excess stock sells through.",
                    "CFO point: no new working capital is needed; we recycle cash already sitting in the warehouse. Timing: markdown cash lags the POs by a few weeks.")
    cash_chart(sh)

    # 9 Decision
    s, sh = d.slide("Decision",
                    f"Three approvals protect {L(SAR)} of sales, funded by stock we already own",
                    SRC_RISK + " Owners are proposals.",
                    "Ask for all three today. Decision 1 is time-critical: the longest lead time is five weeks.")
    table(sh, X0, 2.0, CW, [
        ["", "Decision", "Money", "Proposed owner", "Done when"],
        ["1", f"Release purchase orders for the {N_RO} short SKUs, top five first",
         f"{L(PO_COST)} spend, protects {L(SAR)} of sales", "Head of Operations", "All POs placed this week"],
        ["2", f"Clear excess on {N_MD} SKUs, starting with one cushion line that holds "
              f"{TOP_MD.capital_locked_inr / LOCKED:.0%} of the locked cash", f"Releases up to {L(LOCKED)}",
         "Merchandising Lead", "Markdowns live within 2 weeks"],
        ["3", "Run the weekly buying review from the FORESIGHT queue for 90 days", "No new spend",
         "COO", "Review held every Monday"],
    ], [0.45, 4.6, 2.9, 1.9, 2.18], size=14, row_h=0.95)
    for i, c in enumerate([RED, AMBER, NAVY]):
        box(sh, X0, 2.0 + 0.95 * (i + 1) + 0.2, 0.06, 0.55, fill=c)

    # 10 Action — 90 days
    s, sh = d.slide("Action",
                    "The next 90 days, judged on three numbers",
                    "Targets are proposals for leadership to confirm. Today's values: artifacts/risk_snapshot.csv and back-test re-run.",
                    "Timeline first, then the scorecard we report back on every week.")
    phases = [("WEEKS 1–2", 2, "Place the 10 purchase orders. Move the Monday buying review to the FORESIGHT queue."),
              ("WEEKS 3–4", 2, "Launch markdowns on the 9 overstocked SKUs. Reorders start landing."),
              ("WEEKS 5–12", 8, "Connect the ERP stock feed so the queue refreshes itself. Report the three numbers weekly.")]
    x, unit = X0, CW / 12
    for label, wks, desc in phases:
        w = wks * unit
        box(sh, x, 2.0, w - 0.06, 0.14, fill=NAVY)
        text(sh, x, 2.25, w - 0.2, 0.3, label, 11, NAVY, bold=True)
        text(sh, x, 2.6, max(w - 0.25, 1.75), 1.4, desc, 12, INK)
        x += w
    table(sh, X0, 4.25, CW, [
        ["Measure", "Today", "Proposed 90-day target"],
        ["SKUs short of stock before their next delivery", f"{N_RO}", "0"],
        ["Cash tied up in excess stock", L(LOCKED), f"Below {L(LOCKED / 2)} (half)"],
        ["Forecast error (WAPE) on live weeks", f"{BEST:.1%} in back-test", "21% or better"],
    ], [6.0, 2.8, 3.23], size=14, row_h=0.6)

    # 11 Appendix — method & limits
    s, sh = d.slide("Appendix A",
                    "How to read these numbers: method, assumptions, and limits",
                    "Sources: src/config.py, src/backtest.py, src/risk.py, data/sample/*.csv.",
                    "Be upfront about limits; it builds trust with finance.")
    for x, title, items in [
        (X0, "METHOD", [
            f"Data: {N_SKU} SKUs, 104 weeks, 25,893 daily sales rows, stock snapshot 31 Dec 2025.",
            "Forecast test: 4 rolling windows, 8 weeks each; the model only sees data before each window.",
            "Safety buffer: covers 95% of weeks, scaled by supplier lead time.",
            "Overstock: stock beyond 12 weeks of forecast demand plus the buffer.",
            "Rupee values: shortfall × selling price; excess × unit cost."]),
        (6.85, "LIMITS", [
            "Sample data set, not live NorthBay feeds. Re-run on live data before committing spend.",
            "The back-test scores each week with the latest actuals known; accuracy 8 weeks out will be lower.",
            "One stock snapshot. Positions change weekly, hence the weekly rhythm.",
            "Sales at risk is a ceiling: it assumes every short unit would have sold."])]:
        text(sh, x, 2.0, 5.6, 0.3, title, 11, NAVY, bold=True)
        y = 2.45
        for it in items:
            rule(sh, x, y, 5.6)
            text(sh, x, y + 0.1, 5.6, 0.75, it, 13, INK)
            y += 0.85

    # 12 Appendix — architecture
    s, sh = d.slide("Appendix B",
                    "One engine, two doors: a dashboard for planners and an API for the ERP",
                    "Source: repository (src/, app/, service/, api/); 23 of 23 automated tests passing (pytest, 27 Sep 2026).",
                    "For the CTO. The same scoring code sits behind both doors, and a test checks they agree.")
    text(sh, X0, 2.2, 2.0, 0.3, "INPUTS", 10, MUTED, bold=True)
    for i, src in enumerate(["Daily sales", "SKU price & cost", "Promo calendar", "Stock & open orders"]):
        box(sh, X0, 2.55 + i * 0.62, 2.0, 0.5, line=RULE)
        text(sh, X0, 2.55 + i * 0.62, 2.0, 0.5, src, 12, INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    arrow(sh, 2.8, 3.73, 0.4)
    engine = [("Clean & check", "5 cleaning rules,\nweekly roll-up"), ("Forecast", "Random forest,\n8 weeks ahead"),
              ("Risk & ₹ value", "95% buffer,\n12-week excess window")]
    for i, (t, sub) in enumerate(engine):
        x = 3.35 + i * 2.45
        box(sh, x, 3.1, 2.0, 1.25, fill=NAVY)
        text(sh, x, 3.1, 2.0, 1.25, t, 14, WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(sh, x, 4.45, 2.0, 0.7, sub, 11, MUTED, align=PP_ALIGN.CENTER)
        if i < 2:
            arrow(sh, x + 2.05, 3.73, 0.35)
    text(sh, 3.35, 2.7, 7, 0.3, "FORESIGHT ENGINE", 10, NAVY, bold=True)
    arrow(sh, 10.15, 3.73, 0.4)
    for i, (t, sub) in enumerate([("Planner dashboard", "Ranked queue, CSV export"), ("Scoring API", "For ERP / warehouse systems")]):
        y = 2.6 + i * 1.35
        box(sh, 10.65, y, 2.03, 1.1, line=INK)
        text(sh, 10.65, y + 0.15, 2.03, 0.4, t, 13, INK, bold=True, align=PP_ALIGN.CENTER)
        text(sh, 10.65, y + 0.55, 2.03, 0.4, sub, 10, MUTED, align=PP_ALIGN.CENTER)
    rule(sh, X0, 5.6, CW)
    text(sh, X0, 5.75, CW, 0.8, "23 automated tests, including one that confirms the dashboard and the API "
                                "return identical scores for the same SKU.", 16, INK, font=HEAD)

    d.save("FORESIGHT_Executive_Readout.pptx")


# ======================================================================
# DECK 2 — PITCH DECK (prospective D2C brand leadership)
# ======================================================================
def pitch():
    d = Deck("FORESIGHT · Proof points from the NorthBay Living pilot analysis (sample data)")

    # 1 Title
    s, sh = d.slide("", "")
    text(sh, X0, 1.55, 11, 0.3, "FORESIGHT  ·  DEMAND & INVENTORY INTELLIGENCE", 11, NAVY, bold=True)
    text(sh, X0, 2.05, 11.5, 1.9, "Every Monday: what to buy,\nwhat to clear, and what it's worth", 42, INK, font=HEAD)
    text(sh, X0, 4.25, 9.8, 0.9, "For D2C brands that run out of bestsellers while cash sits in slow stock.", 18, MUTED)
    text(sh, X0, 6.2, 11, 0.3, "Prepared by Anshul", 12, INK)

    # 2 Problem
    s, sh = d.slide("The problem",
                    "Growing brands run short and overstocked at the same time",
                    SRC_RISK + " Each square is one SKU.",
                    "Use NorthBay, a 40-SKU home brand, as the mirror: 'Does this look like your range?'")
    fade(s, unit_chart(sh))
    text(sh, X0, 6.1, CW, 0.6, f"At NorthBay Living, a {N_SKU}-SKU home brand, on a single day.", 18, INK, font=HEAD)

    # 3 Why it persists — before / after
    s, sh = d.slide("Why it persists",
                    "Spreadsheet planning treats a ₹14 lakh problem the same as a ₹0 one",
                    "Source: FORESIGHT project report (spreadsheet practice); FORESIGHT capabilities verified in repository.",
                    "Before/after. Read across each row.")
    table(sh, X0, 2.0, CW, [
        ["", "4-week-average spreadsheet", "FORESIGHT"],
        ["Looks ahead", "Repeats the last month", "8-week forecast for every SKU"],
        ["Supplier wait time", "Ignored", "Built into every stock check"],
        ["Priority", "Every SKU looks equal", "Ranked by rupees at stake"],
        ["Audit trail", "Manual edits, no history", "Same answer every run, tested"],
        ["Explains itself", "No", "One-line reason for every SKU"],
    ], [3.0, 4.3, 4.73], header_fill=NAVY, size=15, row_h=0.72, bold_col=0)

    # 4 Solution — the queue itself
    s, sh = d.slide("The product",
                    "The output is a ranked to-do list, not another dashboard",
                    SRC_RISK + " Rows shown exactly as the engine writes them (top 3 of each action).",
                    "This is what a planner opens on Monday. Sorted by rupees, with the reason in plain words.")
    q = pd.concat([RO.head(3).assign(val=RO.head(3).sales_at_risk_inr, act="Reorder now"),
                   MD.head(3).assign(val=MD.head(3).capital_locked_inr, act="Clear excess")]).sort_values("val", ascending=False)
    rows = [["SKU", "Action", "Why", "₹ at stake"]]
    rows += [[f"{x.subcategory}\n{x.sku_id[3:]}", x.act, x.action_rationale, L(x.val)] for x in q.itertuples()]
    t = table(sh, X0, 1.95, CW, rows, [2.1, 1.6, 6.63, 1.7], size=12, row_h=0.68)
    for i, x in enumerate(q.itertuples(), 1):
        t.cell(i, 1).text_frame.paragraphs[0].runs[0].font.color.rgb = RED if x.act == "Reorder now" else AMBER
        t.cell(i, 1).text_frame.paragraphs[0].runs[0].font.bold = True
        t.cell(i, 3).text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT

    # 5 How it works
    s, sh = d.slide("How it works",
                    "Three steps turn sales history into a priced action",
                    "Source: FORESIGHT pipeline (src/forecast.py, src/risk.py, src/impact.py).",
                    "One step per click. Keep it to the question: will stock last until the next delivery?")
    fade(s, steps(sh, [("Forecast", "Predicts each SKU's weekly sales, 8 weeks ahead, from history, seasons, prices and promotions."),
                       ("Check against lead time", "Will stock on hand and on order last until the supplier's next delivery, with a 95% buffer?"),
                       ("Price the gap", "Turns every shortfall into sales at risk and every excess into cash locked, then ranks them.")]))
    rule(sh, X0, 5.2, CW)
    text(sh, X0, 5.4, CW, 0.8, "Planners get the answer and the reason. No model to operate, no formulas to maintain.",
         18, INK, font=HEAD)

    # 6 Proof
    s, sh = d.slide("Proof",
                    f"One pass over NorthBay's range found ₹{(SAR + LOCKED) / 1e7:.2f} crore to act on",
                    SRC_BT.replace("Source: ", "Sources: ") + " Rupee values: artifacts/risk_snapshot.csv.",
                    "Three numbers, one click each.")
    g = []
    for i, (big, col, cap) in enumerate([(f"−{ERR_CUT:.0%}", NAVY, "forecast error versus a\nsame-week-last-year rule"),
                                         (L(SAR), RED, f"sales at risk flagged,\nacross {N_RO} SKUs"),
                                         (L(LOCKED), AMBER, f"cash to release,\nacross {N_MD} SKUs")]):
        grp = sh.add_group_shape()
        x = X0 + i * 4.01
        if i:
            rule(grp.shapes, x - 0.3, 2.5, 2.6, vertical=True)
        text(grp.shapes, x, 2.6, 3.7, 1.1, big, 48, col, font=HEAD)
        text(grp.shapes, x, 3.8, 3.6, 1.0, cap, 15, MUTED)
        g.append(grp)
    fade(s, g)
    rule(sh, X0, 5.5, CW)
    text(sh, X0, 5.7, CW, 0.8, "Enough to pay for every reorder from stock already on the shelf, with cash left over.", 18, INK, font=HEAD)

    # 7 Economics
    s, sh = d.slide("The economics",
                    "The fix funds itself: excess stock covers the reorder bill twice over",
                    SRC_RISK + " Reorder cost = shortfall units × unit cost. Assumes excess stock sells through.",
                    "For the CFO in the room: no new working capital.")
    cash_chart(sh)

    # 8 Trust
    s, sh = d.slide("Why trust it",
                    "Every recommendation shows its working",
                    "Sources: artifacts/risk_snapshot.csv; tests/ (23 of 23 passing, 27 Sep 2026); src/backtest.py.",
                    "Finance teams adopt what they can audit.")
    text(sh, X0, 2.1, 6.4, 0.3, f"WHAT THE PLANNER SEES FOR {EX.subcategory.upper()} ({EX.sku_id[3:]})", 10, MUTED, bold=True)
    rule(sh, X0, 2.55, 1.45, NAVY, 3, vertical=True)
    text(sh, X0 + 0.3, 2.55, 6.0, 3.0, f"“{EX.action_rationale}”", 22, INK, font=HEAD)
    x, y = 7.6, 2.1
    for fact in ["Tested on 4 past periods it never saw during training",
                 "23 automated checks run on every change",
                 "Dashboard and API return identical scores, checked by a test"]:
        rule(sh, x, y, 5.08)
        text(sh, x, y + 0.15, 5.08, 0.9, fact, 16, INK)
        y += 1.1

    # 9 Offer
    s, sh = d.slide("The offer",
                    "Start with a 90-day pilot on your top 40 SKUs",
                    "Pilot structure mirrors the NorthBay rollout plan (reports/executive_readout_outline.md).",
                    "Low-commitment entry: results on their own history before any process change.")
    x, unit = X0, CW / 12
    for label, wks, title, desc in [("WEEKS 1–2", 2, "Back-test", "Run on your own history. See the accuracy before you change anything."),
                                    ("WEEKS 3–4", 2, "First queue", "Your ranked list of reorders and markdowns, in rupees."),
                                    ("WEEKS 5–12", 8, "Weekly rhythm", "Monday review runs from the queue. We report three numbers weekly.")]:
        w = wks * unit
        box(sh, x, 2.0, w - 0.06, 0.14, fill=NAVY)
        text(sh, x, 2.25, w - 0.2, 0.3, label, 11, NAVY, bold=True)
        text(sh, x, 2.6, max(w - 0.25, 1.75), 0.4, title, 15, INK, bold=True)
        text(sh, x, 3.0, max(w - 0.25, 1.75), 1.3, desc, 12, MUTED)
        x += w
    rule(sh, X0, 4.7, CW)
    text(sh, X0, 4.85, 2.4, 0.3, "SUCCESS MEANS", 10, MUTED, bold=True)
    for i, m in enumerate(["Fewer SKUs short before delivery", "Less cash in excess stock", "Forecast error held on live weeks"]):
        text(sh, X0 + i * 4.01, 5.25, 3.8, 0.8, m, 17, INK, font=HEAD)

    # 10 Ask
    s, sh = d.slide("Next step",
                    "To start, we need four files you already have",
                    "Input tables: data/sample/ (sales_daily, sku_master, calendar, inventory_snapshots).",
                    "Close on the data request and a date for the back-test readout.")
    for i, (f, why) in enumerate([("Daily sales, 24 months", "Learns demand and seasonality"),
                                  ("SKU list with price and cost", "Puts rupees on every gap"),
                                  ("Promotions & holiday calendar", "Explains the spikes"),
                                  ("Current stock, open orders, lead times", "Sets the starting position")]):
        y = 2.05 + i * 0.8
        rule(sh, X0, y, 7.2)
        text(sh, X0, y + 0.15, 0.5, 0.5, str(i + 1), 20, NAVY, font=HEAD)
        text(sh, X0 + 0.6, y + 0.18, 3.6, 0.5, f, 16, INK, bold=True)
        text(sh, X0 + 4.3, y + 0.2, 2.9, 0.5, why, 13, MUTED)
    box(sh, 8.4, 2.05, 4.28, 3.2, fill=TINT)
    text(sh, 8.7, 2.3, 3.8, 0.3, "CONTACT", 10, MUTED, bold=True)
    text(sh, 8.7, 2.7, 3.8, 0.5, "Anshul", 22, INK, font=HEAD)
    text(sh, 8.7, 3.35, 3.8, 1.7, "linkedin.com/in/anshul-chaudhary-508138308\n"
                                  "github.com/morid648/foresight-demand-intelligence\n"
                                  "foresight-demand-intelligence.vercel.app", 11, INK, spacing=6)

    d.save("FORESIGHT_Pitch_Deck.pptx")


if __name__ == "__main__":
    executive()
    pitch()
