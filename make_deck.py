"""Generate the AI Real Estate Agent presentation deck.

Run:    python make_deck.py
Output: AI_Real_Estate_Agent.pptx

Editorial design system, matched to the React frontend.
Every slide shares a masthead, a numbered section eyebrow, and a footer
bar — so the deck reads like one continuous brief, not seven orphan pages.
Typography: Georgia (display), Segoe UI (body), Consolas (mono).
All three ship with Windows 11 — no fallbacks on demo day.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ============================================================
# DESIGN TOKENS
# ============================================================
CANVAS     = RGBColor(0xF6, 0xF1, 0xE8)  # cream page
PAPER      = RGBColor(0xFB, 0xF7, 0xEF)  # card surface
SURFACE    = RGBColor(0xEF, 0xE7, 0xDA)  # subtle tint
DEEP       = RGBColor(0xE6, 0xDA, 0xC5)  # deeper tint
GHOST      = RGBColor(0xDF, 0xD4, 0xBE)  # faint decorative

INK        = RGBColor(0x2F, 0x3A, 0x39)  # primary text
INK_SOFT   = RGBColor(0x4A, 0x55, 0x53)  # softer primary
MUTED      = RGBColor(0x6B, 0x75, 0x6F)  # secondary
FAINT      = RGBColor(0x9B, 0xA1, 0x9A)  # tertiary

TERRACOTTA = RGBColor(0xC8, 0x55, 0x3D)  # accent
TERRA_DEEP = RGBColor(0x9E, 0x3F, 0x2A)
TEAL       = RGBColor(0x2F, 0x6F, 0x6A)  # positive metrics
BRASS      = RGBColor(0xB8, 0x8B, 0x4A)  # secondary accent

HAIRLINE   = RGBColor(0xCF, 0xC5, 0xB4)
DIVIDER    = RGBColor(0xDD, 0xD4, 0xC3)

SERIF = "Georgia"
SANS  = "Segoe UI"
MONO  = "Consolas"

# ============================================================
# DECK
# ============================================================
prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]

# ------------------------------------------------------------
# PRIMITIVES
# ------------------------------------------------------------
def paint_canvas(slide, color=CANVAS):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    r.fill.solid(); r.fill.fore_color.rgb = color
    r.line.fill.background()
    tree = r._element.getparent()
    tree.remove(r._element); tree.insert(2, r._element)

def new_slide():
    s = prs.slides.add_slide(BLANK)
    paint_canvas(s)
    return s

def _frame(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tb, tf

def text(slide, l, t, w, h, s,
         font=SANS, size=18, bold=False, italic=False, color=INK,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.2):
    tb, tf = _frame(slide, l, t, w, h)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    r = p.add_run()
    r.text = s
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return tb

def multi(slide, l, t, w, h, lines,
          font=SANS, size=18, bold=False, italic=False, color=INK,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.25,
          space_after=0):
    tb, tf = _frame(slide, l, t, w, h)
    tf.vertical_anchor = anchor
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        if space_after:
            p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = ln
        r.font.name = font
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
    return tb

def hairline(slide, x1, y1, x2, y2, color=HAIRLINE, w=0.75):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(w)
    return c

def rect(slide, l, t, w, h, fill=None, stroke=None, stroke_w=0.75):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    if fill is None: r.fill.background()
    else: r.fill.solid(); r.fill.fore_color.rgb = fill
    if stroke is None: r.line.fill.background()
    else:
        r.line.color.rgb = stroke
        r.line.width = Pt(stroke_w)
    return r

def rrect(slide, l, t, w, h, fill=None, stroke=None, stroke_w=0.75, radius=0.06):
    r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    r.adjustments[0] = radius
    if fill is None: r.fill.background()
    else: r.fill.solid(); r.fill.fore_color.rgb = fill
    if stroke is None: r.line.fill.background()
    else:
        r.line.color.rgb = stroke
        r.line.width = Pt(stroke_w)
    return r

def oval(slide, l, t, w, h, fill=None, stroke=None, stroke_w=0.75):
    r = slide.shapes.add_shape(MSO_SHAPE.OVAL, l, t, w, h)
    if fill is None: r.fill.background()
    else: r.fill.solid(); r.fill.fore_color.rgb = fill
    if stroke is None: r.line.fill.background()
    else:
        r.line.color.rgb = stroke
        r.line.width = Pt(stroke_w)
    return r

# ------------------------------------------------------------
# CHROME (appears on every inner slide)
# ------------------------------------------------------------
def chrome(slide, n, section):
    """Masthead + section eyebrow + footer bar."""

    # --- masthead top-left: terracotta square + mark
    rect(slide, Inches(0.6), Inches(0.45), Inches(0.13), Inches(0.13), fill=TERRACOTTA)
    text(slide, Inches(0.82), Inches(0.42), Inches(5), Inches(0.25),
         "AIRE  \u00b7  AI REAL ESTATE AGENT",
         font=MONO, size=9, color=INK)

    # --- masthead top-right: edition
    text(slide, Inches(8.5), Inches(0.42), Inches(4.23), Inches(0.25),
         "SPRING 2026  \u00b7  A PRODUCT BRIEF",
         font=MONO, size=9, color=MUTED, align=PP_ALIGN.RIGHT)

    # --- hairline under masthead
    hairline(slide, Inches(0.6), Inches(0.78), Inches(12.73), Inches(0.78), color=HAIRLINE)

    # --- section eyebrow
    text(slide, Inches(0.6), Inches(0.92), Inches(10), Inches(0.25),
         f"{n:02d} / 07     \u00b7     {section.upper()}",
         font=MONO, size=9, color=TERRACOTTA, bold=True)

    # --- bottom hairline + footer strip
    hairline(slide, Inches(0.6), Inches(7.02), Inches(12.73), Inches(7.02), color=HAIRLINE)
    text(slide, Inches(0.6), Inches(7.12), Inches(6), Inches(0.22),
         "AIRE  \u00b7  AI REAL ESTATE AGENT",
         font=MONO, size=8, color=FAINT)
    text(slide, Inches(6.5), Inches(7.12), Inches(6.23), Inches(0.22),
         "SE FACTORY  \u00b7  AIE BOOTCAMP  \u00b7  WEEK 2  \u00b7  2026",
         font=MONO, size=8, color=FAINT, align=PP_ALIGN.RIGHT)


# ============================================================
# SLIDE 1 — COVER
# ============================================================
def slide_cover():
    s = new_slide()

    # --- masthead (cover-specific: no section eyebrow) ---
    rect(s, Inches(0.6), Inches(0.45), Inches(0.14), Inches(0.14), fill=TERRACOTTA)
    text(s, Inches(0.84), Inches(0.41), Inches(5), Inches(0.25),
         "AIRE  \u00b7  AI REAL ESTATE AGENT",
         font=MONO, size=9, color=INK, bold=True)
    text(s, Inches(8.5), Inches(0.41), Inches(4.23), Inches(0.25),
         "SPRING 2026  \u00b7  EDITION 01",
         font=MONO, size=9, color=MUTED, align=PP_ALIGN.RIGHT)
    hairline(s, Inches(0.6), Inches(0.8), Inches(12.73), Inches(0.8), color=HAIRLINE)

    # --- thin secondary rule, deep terracotta, aligned right ---
    hairline(s, Inches(0.6), Inches(1.18), Inches(3.0), Inches(1.18),
             color=TERRACOTTA, w=1.6)

    # small kicker above headline
    text(s, Inches(0.6), Inches(1.3), Inches(10), Inches(0.25),
         "A PRODUCT BRIEF  /  NATURAL-LANGUAGE REAL ESTATE",
         font=MONO, size=10, color=MUTED, bold=True)

    # --- hero: two-line serif headline ---
    multi(s, Inches(0.6), Inches(2.35), Inches(12.2), Inches(3.3),
          ["Price any home", "from a sentence."],
          font=SERIF, size=96, color=INK, line_spacing=1.02)

    # --- subtitle ---
    text(s, Inches(0.62), Inches(5.3), Inches(11.5), Inches(0.45),
         "A natural-language real-estate estimator, grounded in 2,000+ real Ames sales.",
         font=SERIF, size=20, italic=True, color=INK_SOFT)

    text(s, Inches(0.62), Inches(5.8), Inches(11.5), Inches(0.4),
         "One sentence in.  One priced answer out.  With reasoning attached.",
         font=SANS, size=14, color=MUTED)

    # --- bottom meta band ---
    hairline(s, Inches(0.6), Inches(6.6), Inches(12.73), Inches(6.6), color=HAIRLINE)

    text(s, Inches(0.6), Inches(6.75), Inches(3), Inches(0.22),
         "BY", font=MONO, size=8, color=FAINT)
    text(s, Inches(0.6), Inches(6.96), Inches(6), Inches(0.3),
         "SE Factory  \u00b7  AIE Bootcamp",
         font=SERIF, size=14, italic=True, color=INK)

    text(s, Inches(4.5), Inches(6.75), Inches(3), Inches(0.22),
         "EDITION", font=MONO, size=8, color=FAINT)
    text(s, Inches(4.5), Inches(6.96), Inches(4), Inches(0.3),
         "Week 2  \u00b7  2026",
         font=SERIF, size=14, italic=True, color=INK)

    text(s, Inches(8.5), Inches(6.75), Inches(4.23), Inches(0.22),
         "PAGES", font=MONO, size=8, color=FAINT, align=PP_ALIGN.RIGHT)
    text(s, Inches(8.5), Inches(6.96), Inches(4.23), Inches(0.3),
         "Seven, with a demo.",
         font=SERIF, size=14, italic=True, color=INK, align=PP_ALIGN.RIGHT)

    # --- footer ---
    hairline(s, Inches(0.6), Inches(7.28), Inches(12.73), Inches(7.28), color=HAIRLINE)
    text(s, Inches(0.6), Inches(7.34), Inches(12.13), Inches(0.18),
         "\u2014  Turn the page.", font=MONO, size=8, color=FAINT)


# ============================================================
# SLIDE 2 — PROBLEM
# ============================================================
def slide_problem():
    s = new_slide()
    chrome(s, 1, "The problem")

    # ---------- LEFT COLUMN (headline + three pain points) ----------
    # small kicker above headline
    text(s, Inches(0.6), Inches(1.4), Inches(7), Inches(0.25),
         "WHY BUYING A HOME IS STILL A FORM",
         font=MONO, size=9, color=MUTED, bold=True)

    # headline (huge)
    multi(s, Inches(0.6), Inches(1.85), Inches(7), Inches(2.6),
          ["Pricing a home",
           "shouldn\u2019t require",
           "a spreadsheet."],
          font=SERIF, size=52, color=INK, line_spacing=1.02)

    # hairline under headline
    hairline(s, Inches(0.6), Inches(4.7), Inches(6.9), Inches(4.7),
             color=TERRACOTTA, w=1.25)

    # three numbered problem lines
    items = [
        ("I.",   "Buyers see prices, not the logic behind them."),
        ("II.",  "Agents default to instinct \u2014 which doesn\u2019t scale."),
        ("III.", "Traditional tools demand 80 structured fields before they\u2019ll answer."),
    ]
    y = Inches(4.95)
    for num, body in items:
        text(s, Inches(0.6), y, Inches(0.6), Inches(0.4),
             num, font=SERIF, size=16, italic=True, color=TERRACOTTA)
        text(s, Inches(1.1), y + Inches(0.04), Inches(5.9), Inches(0.4),
             body, font=SANS, size=14, color=INK_SOFT)
        y += Inches(0.55)

    # ---------- RIGHT COLUMN (the contrast visualization) ----------
    cx = Inches(7.9)
    cw = Inches(4.83)

    # --- "THE OLD WAY" card ---
    text(s, cx, Inches(1.4), cw, Inches(0.25),
         "THE OLD WAY", font=MONO, size=9, color=MUTED, bold=True)
    hairline(s, cx, Inches(1.72), cx + cw, Inches(1.72), color=HAIRLINE)

    # 8 field rows (labels + placeholders)
    fields = [
        "Overall quality", "Above-grade area", "Lot area", "Year built",
        "Full baths", "Bedrooms", "Garage cars", "Neighborhood",
    ]
    for i, name in enumerate(fields):
        y_i = Inches(1.95 + i * 0.28)
        text(s, cx, y_i, Inches(1.9), Inches(0.22),
             name, font=MONO, size=8, color=MUTED)
        rect(s, cx + Inches(1.95), y_i + Inches(0.02),
             Inches(2.9), Inches(0.18),
             fill=SURFACE, stroke=HAIRLINE, stroke_w=0.5)
        # a single faint tick mark inside the field (the unfilled form look)
        text(s, cx + Inches(2.05), y_i - Inches(0.01),
             Inches(2.8), Inches(0.2),
             "\u2014", font=MONO, size=8, color=FAINT)

    # " ... and 72 more " line
    text(s, cx, Inches(4.3), cw, Inches(0.25),
         "\u2026 and 72 more before a price is returned.",
         font=SANS, size=10, italic=True, color=FAINT)

    # --- arrow down + THE NEW WAY ---
    text(s, cx, Inches(4.65), cw, Inches(0.3),
         "\u2193", font=SERIF, size=18, color=MUTED, align=PP_ALIGN.CENTER)

    text(s, cx, Inches(5.0), cw, Inches(0.25),
         "THE NEW WAY", font=MONO, size=9, color=TERRACOTTA, bold=True)
    hairline(s, cx, Inches(5.32), cx + cw, Inches(5.32), color=TERRACOTTA, w=1.25)

    # the single sentence in a cream card
    rect(s, cx, Inches(5.5), cw, Inches(1.3),
         fill=PAPER, stroke=TERRACOTTA, stroke_w=1.5)

    # big opening quote
    text(s, cx + Inches(0.22), Inches(5.45), Inches(0.6), Inches(0.9),
         "\u201C", font=SERIF, size=56, color=TERRACOTTA)

    multi(s, cx + Inches(0.75), Inches(5.68), cw - Inches(1.0), Inches(1.0),
          ["3-bed ranch in OldTown,",
           "1,400 sqft, good shape."],
          font=SERIF, size=17, italic=True, color=INK, line_spacing=1.25)


# ============================================================
# SLIDE 3 — PRODUCT
# ============================================================
def slide_product():
    s = new_slide()
    chrome(s, 2, "The product")

    # kicker
    text(s, Inches(0.6), Inches(1.4), Inches(10), Inches(0.25),
         "WHAT THE USER ACTUALLY GETS",
         font=MONO, size=9, color=MUTED, bold=True)

    # headline
    multi(s, Inches(0.6), Inches(1.85), Inches(12.2), Inches(1.7),
          ["A natural-language price,",
           "with reasoning attached."],
          font=SERIF, size=48, color=INK, line_spacing=1.04)

    # hairline
    hairline(s, Inches(0.6), Inches(4.15), Inches(12.73), Inches(4.15),
             color=HAIRLINE)

    # --- three cards ---
    card_y = Inches(4.35)
    card_h = Inches(2.45)
    gap    = Inches(0.3)
    total_w = Inches(12.13)
    card_w  = (total_w - gap * 2) / 3
    card_x0 = Inches(0.6)

    def card(i, num, label, body_font, body_size, body_italic,
             body_lines, footnote=None, price_mode=False):
        x = card_x0 + (card_w + gap) * i

        # card frame
        rect(s, x, card_y, card_w, card_h, fill=PAPER, stroke=HAIRLINE, stroke_w=0.75)

        # ghost big number in top-right
        text(s, x + card_w - Inches(1.5), card_y + Inches(0.2),
             Inches(1.3), Inches(1.5),
             num, font=SERIF, size=80, color=GHOST,
             align=PP_ALIGN.RIGHT, italic=True)

        # top-left: mono label
        text(s, x + Inches(0.35), card_y + Inches(0.3),
             card_w - Inches(0.7), Inches(0.25),
             label, font=MONO, size=10, color=TERRACOTTA, bold=True)

        # hairline under label
        hairline(s, x + Inches(0.35), card_y + Inches(0.68),
                 x + Inches(1.2), card_y + Inches(0.68),
                 color=TERRACOTTA, w=1.25)

        # body
        if price_mode:
            # huge $ + number, terracotta $ + ink number
            text(s, x + Inches(0.35), card_y + Inches(1.0),
                 Inches(0.7), Inches(1.0),
                 "$", font=MONO, size=62, color=TERRACOTTA)
            text(s, x + Inches(0.9), card_y + Inches(1.0),
                 card_w - Inches(1.1), Inches(1.0),
                 "167,887", font=MONO, size=62, color=INK)

            text(s, x + Inches(0.35), card_y + Inches(1.95),
                 card_w - Inches(0.7), Inches(0.25),
                 "USD  \u00b7  POINT ESTIMATE",
                 font=MONO, size=9, color=MUTED)
        else:
            multi(s, x + Inches(0.35), card_y + Inches(1.0),
                  card_w - Inches(0.7), card_h - Inches(1.3),
                  body_lines,
                  font=body_font, size=body_size, italic=body_italic,
                  color=INK, line_spacing=1.3)

        if footnote:
            text(s, x + Inches(0.35), card_y + card_h - Inches(0.4),
                 card_w - Inches(0.7), Inches(0.25),
                 footnote, font=MONO, size=9, color=MUTED)

    # 01 DESCRIBE — a sentence in italic serif, with an open quote
    card(0, "01", "DESCRIBE",
         SERIF, 18, True,
         ["\u201C3-bed ranch in OldTown,",
          "1,400 sqft, good shape.\u201D"],
         footnote="INPUT  \u00b7  FREE-FORM TEXT")

    # 02 PRICE — the hero card
    card(1, "02", "PRICE",
         MONO, 62, False, [], price_mode=True)

    # 03 REASON — reasoning in serif
    card(2, "03", "REASON",
         SERIF, 15, True,
         ["Below the $160K median",
          "for this neighborhood \u2014",
          "smaller lot, older condition."],
         footnote="OUTPUT  \u00b7  PLAIN ENGLISH")


# ============================================================
# SLIDE 4 — SYSTEM FLOW
# ============================================================
def slide_flow():
    s = new_slide()
    chrome(s, 3, "System flow")

    # kicker
    text(s, Inches(0.6), Inches(1.4), Inches(10), Inches(0.25),
         "HOW THE PIPELINE WORKS",
         font=MONO, size=9, color=MUTED, bold=True)

    # headline
    multi(s, Inches(0.6), Inches(1.85), Inches(12.2), Inches(1.6),
          ["Three stages.",
           "One sentence in, one priced answer out."],
          font=SERIF, size=40, color=INK, line_spacing=1.06)

    # --- subtitle line ---
    text(s, Inches(0.6), Inches(4.1), Inches(12.13), Inches(0.3),
         "A language model extracts the features.  An sklearn model prices them.  A second language model explains the result.",
         font=SERIF, size=14, italic=True, color=INK_SOFT)

    # ---------------- DIAGRAM ----------------
    # horizontal axis
    axis_y = Inches(5.4)
    axis_x1 = Inches(1.2)
    axis_x2 = Inches(12.13)
    hairline(s, axis_x1, axis_y, axis_x2, axis_y, color=HAIRLINE, w=1.0)

    # 5 node centers
    centers = [Inches(1.2), Inches(3.93), Inches(6.67), Inches(9.4), Inches(12.13)]

    stages_top = [
        "Sentence",
        "Extraction",
        "Prediction",
        "Interpretation",
        "Response",
    ]
    stages_bot = [
        ["free-form", "user text"],
        ["GPT-4o-mini", "+ Pydantic"],
        ["Random Forest", "on Ames"],
        ["GPT-4o-mini", "+ stats"],
        ["price", "+ reasoning"],
    ]
    accent = {1, 2, 3}  # filled terracotta for the 3 pipeline stages

    dia_outer = Inches(0.42)
    dia_inner = Inches(0.22)

    for i, cx in enumerate(centers):
        # outer ring
        if i in accent:
            oval(s, cx - dia_outer/2, axis_y - dia_outer/2, dia_outer, dia_outer,
                 fill=PAPER, stroke=TERRACOTTA, stroke_w=1.5)
            oval(s, cx - dia_inner/2, axis_y - dia_inner/2, dia_inner, dia_inner,
                 fill=TERRACOTTA)
        else:
            oval(s, cx - dia_outer/2, axis_y - dia_outer/2, dia_outer, dia_outer,
                 fill=PAPER, stroke=INK, stroke_w=1.25)
            oval(s, cx - dia_inner/2, axis_y - dia_inner/2, dia_inner, dia_inner,
                 fill=INK)

        # stage number above (mono small)
        text(s, cx - Inches(1.25), axis_y - Inches(1.3),
             Inches(2.5), Inches(0.25),
             f"{i+1:02d}", font=MONO, size=9, color=MUTED,
             align=PP_ALIGN.CENTER)

        # stage title (serif italic)
        text(s, cx - Inches(1.3), axis_y - Inches(1.0),
             Inches(2.6), Inches(0.5),
             stages_top[i], font=SERIF, size=22, italic=True, color=INK,
             align=PP_ALIGN.CENTER)

        # below the axis: mono detail
        multi(s, cx - Inches(1.3), axis_y + Inches(0.4),
              Inches(2.6), Inches(0.8),
              stages_bot[i],
              font=MONO, size=10, color=MUTED,
              align=PP_ALIGN.CENTER, line_spacing=1.35)

    # tiny action verbs between nodes (below axis, between circles)
    verbs = ["reads", "predicts", "explains", "returns"]
    for i, verb in enumerate(verbs):
        cx_mid = (centers[i] + centers[i+1]) / 2
        text(s, cx_mid - Inches(0.8), axis_y - Inches(0.22),
             Inches(1.6), Inches(0.25),
             verb, font=SERIF, size=11, italic=True, color=MUTED,
             align=PP_ALIGN.CENTER)

    # --- tech stack footer ---
    hairline(s, Inches(0.6), Inches(6.75), Inches(12.73), Inches(6.75),
             color=HAIRLINE)
    text(s, Inches(0.6), Inches(6.8), Inches(12.13), Inches(0.25),
         "STACK",
         font=MONO, size=9, color=MUTED, bold=True)
    text(s, Inches(1.5), Inches(6.8), Inches(11.23), Inches(0.25),
         "FastAPI  \u00b7  React + Vite  \u00b7  Pydantic v2  \u00b7  scikit-learn 1.5  \u00b7  OpenAI 1.51",
         font=MONO, size=10, color=INK)


# ============================================================
# SLIDE 5 — INTELLIGENCE
# ============================================================
def slide_intelligence():
    s = new_slide()
    chrome(s, 4, "The intelligence")

    # kicker
    text(s, Inches(0.6), Inches(1.4), Inches(10), Inches(0.25),
         "WHY THIS IS MORE THAN A GPT WRAPPER",
         font=MONO, size=9, color=MUTED, bold=True)

    # headline
    multi(s, Inches(0.6), Inches(1.85), Inches(12.2), Inches(1.6),
          ["Two language models,",
           "around a model that knows the market."],
          font=SERIF, size=36, color=INK, line_spacing=1.05)

    hairline(s, Inches(0.6), Inches(4.2), Inches(12.73), Inches(4.2),
             color=HAIRLINE)

    # three columns
    col_y  = Inches(4.45)
    col_x0 = Inches(0.6)
    col_w  = Inches(4.04)
    gap    = Inches(0.04)

    columns = [
        {
            "num": "01",
            "title": "Extraction",
            "body1": "GPT-4o-mini, few-shot,",
            "body2": "Pydantic-validated.",
            "metric_big": "+37",
            "metric_unit": "pts",
            "metric_label": "v2 vs v1  \u00b7  labeled queries",
        },
        {
            "num": "02",
            "title": "Prediction",
            "body1": "Random Forest on Ames,",
            "body2": "imputers fitted in the Pipeline.",
            "metric_big": "0.896",
            "metric_unit": "R\u00b2",
            "metric_label": "RMSE $25,652  \u00b7  held-out test",
        },
        {
            "num": "03",
            "title": "Interpretation",
            "body1": "Grounded in training medians",
            "body2": "and neighborhood averages.",
            "metric_big": "0",
            "metric_unit": "drift",
            "metric_label": "explains the model, not the market",
        },
    ]

    for i, c in enumerate(columns):
        x = col_x0 + (col_w + gap) * i

        # column number
        text(s, x, col_y, col_w, Inches(0.3),
             c["num"], font=MONO, size=11, color=MUTED, bold=True)
        # title
        text(s, x, col_y + Inches(0.3), col_w, Inches(0.6),
             c["title"], font=SERIF, size=26, italic=True, color=INK)

        # terracotta rule
        hairline(s, x, col_y + Inches(1.02),
                 x + Inches(1.15), col_y + Inches(1.02),
                 color=TERRACOTTA, w=1.5)

        # description
        multi(s, x, col_y + Inches(1.2), col_w, Inches(0.9),
              [c["body1"], c["body2"]],
              font=SANS, size=13, color=INK_SOFT, line_spacing=1.35)

        # big metric — number huge + unit beside
        text(s, x, col_y + Inches(2.05), Inches(2.7), Inches(0.9),
             c["metric_big"], font=MONO, size=44, color=TEAL)
        text(s, x + Inches(2.6), col_y + Inches(2.4),
             Inches(1.3), Inches(0.4),
             c["metric_unit"], font=MONO, size=13, color=TEAL)

        # metric label
        text(s, x, col_y + Inches(2.95), col_w, Inches(0.3),
             c["metric_label"], font=MONO, size=9, color=MUTED)

        # vertical divider
        if i < 2:
            hairline(s, x + col_w + gap/2, col_y + Inches(0.2),
                     x + col_w + gap/2, col_y + Inches(3.15),
                     color=HAIRLINE, w=0.5)

    # caveat
    hairline(s, Inches(0.6), Inches(7.75), Inches(12.73), Inches(7.75),
             color=HAIRLINE)


# ============================================================
# SLIDE 6 — LIVE DEMO
# ============================================================
def slide_demo():
    s = new_slide()
    chrome(s, 5, "Live demo")

    # LEFT column: kicker + headline + speaker cues
    text(s, Inches(0.6), Inches(1.4), Inches(5.5), Inches(0.25),
         "FROM SENTENCE TO ESTIMATE, LIVE",
         font=MONO, size=9, color=MUTED, bold=True)

    multi(s, Inches(0.6), Inches(1.85), Inches(5.8), Inches(2.4),
          ["Let\u2019s price", "a house."],
          font=SERIF, size=56, color=INK, line_spacing=1.02)

    # cue divider
    hairline(s, Inches(0.6), Inches(4.3), Inches(5.9), Inches(4.3),
             color=TERRACOTTA, w=1.25)

    text(s, Inches(0.6), Inches(4.45), Inches(5), Inches(0.25),
         "SPEAKER CUES", font=MONO, size=9, color=MUTED, bold=True)

    cues = [
        ("01", "Type the OldTown example."),
        ("02", "Point at each pipeline stage"),
        ("",   "    as it lights up."),
        ("03", "Read the price aloud, then"),
        ("",   "    one line of the reasoning."),
        ("04", "Reset. If time: NridgHt luxury."),
    ]
    y = Inches(4.8)
    for num, body in cues:
        text(s, Inches(0.6), y, Inches(0.4), Inches(0.25),
             num, font=MONO, size=10, color=TERRACOTTA, bold=True)
        text(s, Inches(1.0), y, Inches(5), Inches(0.25),
             body, font=MONO, size=10, color=INK)
        y += Inches(0.25)

    # ---------- RIGHT column: premium product mockup ----------
    fx = Inches(6.7)
    fy = Inches(1.35)
    fw = Inches(6.15)
    fh = Inches(5.5)

    # outer frame (browser)
    rect(s, fx, fy, fw, fh, fill=PAPER, stroke=HAIRLINE, stroke_w=1.0)

    # top chrome bar
    top_h = Inches(0.4)
    rect(s, fx, fy, fw, top_h, fill=SURFACE, stroke=HAIRLINE, stroke_w=0.5)
    hairline(s, fx, fy + top_h, fx + fw, fy + top_h, color=HAIRLINE)

    # three dots
    d = Inches(0.12)
    oval(s, fx + Inches(0.2), fy + Inches(0.13), d, d, fill=TERRACOTTA)
    oval(s, fx + Inches(0.4), fy + Inches(0.13), d, d, fill=BRASS)
    oval(s, fx + Inches(0.6), fy + Inches(0.13), d, d, fill=TEAL)

    # URL pill
    url_w = Inches(3.0)
    url_x = fx + (fw - url_w) / 2
    rrect(s, url_x, fy + Inches(0.1), url_w, Inches(0.22),
          fill=PAPER, stroke=HAIRLINE, stroke_w=0.5, radius=0.2)
    text(s, url_x, fy + Inches(0.11), url_w, Inches(0.2),
         "aire.local  /  predict", font=MONO, size=9, color=MUTED,
         align=PP_ALIGN.CENTER)

    # --- stage indicator strip (3 stages across top of content) ---
    st_y = fy + Inches(0.6)
    st_h = Inches(0.55)
    st_pad = Inches(0.35)
    st_w = fw - st_pad * 2
    # background
    rect(s, fx + st_pad, st_y, st_w, st_h, fill=SURFACE, stroke=None)
    hairline(s, fx + st_pad, st_y + st_h, fx + st_pad + st_w, st_y + st_h,
             color=HAIRLINE, w=0.5)

    stage_w = st_w / 3
    stage_labels = ["EXTRACT", "PREDICT", "EXPLAIN"]
    for i, lab in enumerate(stage_labels):
        sx = fx + st_pad + stage_w * i
        # checkmark (teal dot)
        oval(s, sx + Inches(0.15), st_y + Inches(0.18),
             Inches(0.18), Inches(0.18), fill=TEAL)
        text(s, sx + Inches(0.15), st_y + Inches(0.15),
             Inches(0.18), Inches(0.22),
             "\u2713", font=SANS, size=10, bold=True, color=PAPER,
             align=PP_ALIGN.CENTER)

        # label
        text(s, sx + Inches(0.45), st_y + Inches(0.2),
             stage_w - Inches(0.5), Inches(0.22),
             lab, font=MONO, size=9, color=INK, bold=True)

        # divider
        if i < 2:
            hairline(s, sx + stage_w, st_y + Inches(0.1),
                     sx + stage_w, st_y + st_h - Inches(0.1),
                     color=HAIRLINE, w=0.5)

    # --- content area ---
    cx = fx + Inches(0.45)
    cy = fy + Inches(1.35)
    cw = fw - Inches(0.9)

    # section eyebrow
    text(s, cx, cy, cw, Inches(0.25),
         "04   ESTIMATE", font=MONO, size=10, color=TERRACOTTA, bold=True)
    hairline(s, cx, cy + Inches(0.3), cx + Inches(0.9), cy + Inches(0.3),
             color=TERRACOTTA, w=1.25)

    # big price (terracotta $ + ink number)
    text(s, cx - Inches(0.05), cy + Inches(0.4),
         Inches(0.9), Inches(1.7),
         "$", font=MONO, size=80, color=TERRACOTTA)
    text(s, cx + Inches(0.7), cy + Inches(0.4),
         cw - Inches(0.9), Inches(1.7),
         "167,887", font=MONO, size=80, color=INK)

    # unit
    text(s, cx, cy + Inches(1.9),
         cw, Inches(0.25),
         "USD  \u00b7  POINT ESTIMATE", font=MONO, size=9, color=MUTED)

    # reasoning
    hairline(s, cx, cy + Inches(2.3), cx + cw, cy + Inches(2.3), color=HAIRLINE)

    text(s, cx, cy + Inches(2.45), cw, Inches(0.3),
         "REASONING", font=MONO, size=9, color=MUTED, bold=True)

    multi(s, cx, cy + Inches(2.7), cw, Inches(1.0),
          ["\u201CBelow the $160,000 neighborhood median.",
           "A smaller lot and an older overall condition",
           "pull the estimate down.\u201D"],
          font=SERIF, size=13, italic=True, color=INK, line_spacing=1.35)

    # chips row
    hairline(s, cx, cy + Inches(4.1), cx + cw, cy + Inches(4.1), color=HAIRLINE)
    text(s, cx, cy + Inches(4.2), cw, Inches(0.25),
         "FEATURES  \u00b7  4 UNDERSTOOD, 8 IMPUTED",
         font=MONO, size=9, color=MUTED, bold=True)

    chips = [
        ("BedroomAbvGr", "3"),
        ("Neighborhood", "OldTown"),
        ("GrLivArea",    "1,400"),
        ("OverallQual",  "5*"),
    ]
    chip_gap = Inches(0.08)
    chip_w = (cw - chip_gap * 3) / 4
    chip_y = cy + Inches(4.5)
    chip_h = Inches(0.55)
    for i, (k, v) in enumerate(chips):
        cx_i = cx + (chip_w + chip_gap) * i
        rrect(s, cx_i, chip_y, chip_w, chip_h,
              fill=SURFACE, stroke=HAIRLINE, stroke_w=0.5, radius=0.15)
        text(s, cx_i + Inches(0.1), chip_y + Inches(0.05),
             chip_w - Inches(0.2), Inches(0.22),
             k, font=MONO, size=8, color=MUTED)
        text(s, cx_i + Inches(0.1), chip_y + Inches(0.25),
             chip_w - Inches(0.2), Inches(0.3),
             v, font=SERIF, size=14, italic=True, color=INK)

    # footnote
    text(s, cx, chip_y + chip_h + Inches(0.08), cw, Inches(0.22),
         "*  imputed from training-set median",
         font=MONO, size=8, color=MUTED)


# ============================================================
# SLIDE 7 — CLOSING
# ============================================================
def slide_closing():
    s = new_slide()
    chrome(s, 6, "What\u2019s next")

    # kicker
    text(s, Inches(0.6), Inches(1.4), Inches(10), Inches(0.25),
         "SHIPPED, END-TO-END",
         font=MONO, size=9, color=MUTED, bold=True)

    # small section header
    text(s, Inches(0.6), Inches(1.8), Inches(10), Inches(0.55),
         "Everything you just saw is already live.",
         font=SERIF, size=24, italic=True, color=INK_SOFT)

    # three checked lines
    hairline(s, Inches(0.6), Inches(2.6), Inches(12.73), Inches(2.6),
             color=HAIRLINE)

    items = [
        ("Stage 1 + ML + Stage 2, wired through FastAPI and a React front end.",
         "app/main.py  \u00b7  app/chain/  \u00b7  frontend/"),
        ("Prompt v2 chosen against labeled ground truth.",
         "v2 mean accuracy 0.983  \u00b7  v1 mean accuracy 0.617"),
        ("Dockerised for one-command deploy.",
         "docker compose up  \u00b7  backend:8000  \u00b7  frontend:3000"),
    ]
    y = Inches(2.85)
    for body, detail in items:
        # teal check
        oval(s, Inches(0.6), y + Inches(0.08),
             Inches(0.22), Inches(0.22), fill=TEAL)
        text(s, Inches(0.6), y + Inches(0.04),
             Inches(0.22), Inches(0.25),
             "\u2713", font=SANS, size=11, bold=True, color=PAPER,
             align=PP_ALIGN.CENTER)

        text(s, Inches(1.0), y, Inches(11.5), Inches(0.35),
             body, font=SANS, size=15, color=INK)
        text(s, Inches(1.0), y + Inches(0.38), Inches(11.5), Inches(0.25),
             detail, font=MONO, size=9, color=MUTED)
        y += Inches(0.7)

    # NEXT strip
    hairline(s, Inches(0.6), y + Inches(0.05), Inches(12.73), y + Inches(0.05),
             color=HAIRLINE)
    text(s, Inches(0.6), y + Inches(0.2), Inches(1.3), Inches(0.3),
         "NEXT", font=MONO, size=10, color=TERRACOTTA, bold=True)
    text(s, Inches(1.6), y + Inches(0.18), Inches(11.13), Inches(0.35),
         "Comparable listings  \u00b7  confidence intervals around every price.",
         font=SERIF, size=15, italic=True, color=INK)

    # closing line — biggest type in the deck
    # terracotta hairline above closing
    hairline(s, Inches(5.25), Inches(5.95),
             Inches(8.08), Inches(5.95),
             color=TERRACOTTA, w=2.0)

    multi(s, Inches(0.6), Inches(6.1), Inches(12.13), Inches(1.0),
          ["Real estate,",
           "finally in plain English."],
          font=SERIF, size=44, color=INK, line_spacing=1.04,
          align=PP_ALIGN.CENTER)


# ============================================================
# BUILD
# ============================================================
slide_cover()
slide_problem()
slide_product()
slide_flow()
slide_intelligence()
slide_demo()
slide_closing()

out = "AI_Real_Estate_Agent.pptx"
prs.save(out)
print(f"wrote {out}  ·  {len(prs.slides)} slides")
