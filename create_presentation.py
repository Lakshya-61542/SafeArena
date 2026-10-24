"""Complete PowerPoint presentation builder for SafeArena Hackathon Pitch Deck.
Produces widescreen 16:9 editable slides with native PowerPoint shapes, typography, and styling.
Enhanced with high-contrast typography, directional flow badges, and rich layout composition.
"""
import os
import sys
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Slide Dimensions (16:9 Widescreen)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Premium Cybersecurity Color Palette
BG_COLOR = RGBColor(10, 14, 23)        # #0A0E17 Deep Navy / Near-Black
CARD_BG = RGBColor(17, 24, 39)         # #111827 Dark Slate Card
CARD_BORDER = RGBColor(31, 41, 55)     # #1F2937 Subtle Border
CARD_HOVER = RGBColor(24, 33, 53)      # #182135 Elevated Card

# Accent Colors
CYAN = RGBColor(0, 229, 255)           # #00E5FF Electric Cyan
TEAL = RGBColor(20, 184, 166)          # #14B8A6 Teal
BLUE = RGBColor(59, 130, 246)          # #3B82F6 Cobalt Blue
RED = RGBColor(239, 68, 68)            # #EF4444 Crimson Red
AMBER = RGBColor(245, 158, 11)         # #F59E0B Warning Amber
GREEN = RGBColor(16, 185, 129)         # #10B981 Emerald Green
PURPLE = RGBColor(168, 85, 247)        # #A855F7 Violet

# Text Colors
TEXT_WHITE = RGBColor(248, 250, 252)   # #F8FAFC Pure Crisp White
TEXT_BRIGHT = RGBColor(241, 245, 249)  # #F1F5F9 Ultra-Bright Slate (Maximum Contrast)
TEXT_MUTED = RGBColor(226, 232, 240)   # #E2E8F0 High Contrast Crisp Slate
TEXT_DIM = RGBColor(148, 163, 184)     # #94A3B8 Dim / Metadata Slate

FONT_FAMILY = "Segoe UI"


def set_slide_background(slide):
    """Fill slide with deep dark background."""
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT
    )
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_COLOR
    bg_shape.line.fill.background()
    return bg_shape


def add_header(slide, tag_text, title_text, subtitle_text=""):
    """Consistent, professional top header on standard slides."""
    # Tag / Category pill
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.5), Inches(0.28))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = tag_text.upper()
    p_tag.font.name = FONT_FAMILY
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.62))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_FAMILY
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE

    # Subtitle (if present)
    if subtitle_text:
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.36), Inches(11.7), Inches(0.32))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_left = tf_sub.margin_top = tf_sub.margin_right = tf_sub.margin_bottom = 0
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle_text
        p_sub.font.name = FONT_FAMILY
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED


def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER, border_width=1):
    """Add a card container with rounded corners and border."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    card.fill.solid()
    card.fill.fore_color.rgb = bg
    card.line.color.rgb = border
    card.line.width = Pt(border_width)
    return card


def add_pill(slide, left, top, width, height, text, bg_color, text_color, font_size=9, bold=True):
    """Add a small badge/pill."""
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = bg_color
    pill.line.fill.background()
    tf = pill.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = FONT_FAMILY
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = text_color
    p.alignment = PP_ALIGN.CENTER
    return pill


def set_speaker_notes(slide, notes):
    """Attach presenter speaker notes to the slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes.strip()


# ==============================================================================
# SLIDE BUILDERS (POLISHED & REFINED)
# ==============================================================================

def build_slide_1(prs):
    """Slide 1 — The Hero Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)

    # Event & Category Badges
    add_pill(slide, Inches(0.8), Inches(0.6), Inches(2.3), Inches(0.32), "HACK IN HILLS '26", CYAN, BG_COLOR, font_size=10, bold=True)
    add_pill(slide, Inches(3.2), Inches(0.6), Inches(3.1), Inches(0.32), "CYBERSECURITY & AI DEFENSE TRACK", CARD_BG, CYAN, font_size=10, bold=True)

    # Main Project Title
    tbox = slide.shapes.add_textbox(Inches(0.8), Inches(1.15), Inches(6.4), Inches(1.3))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "SafeArena"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(50)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    # Tagline
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(2.45), Inches(6.4), Inches(0.45))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = "Isolate  →  Control  →  Detect  →  Prove"
    p_tag.font.name = FONT_FAMILY
    p_tag.font.size = Pt(16)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN

    # Subtitle & Description
    desc_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.0), Inches(5.8), Inches(2.3))
    tf_desc = desc_box.text_frame
    tf_desc.word_wrap = True
    p1 = tf_desc.paragraphs[0]
    p1.text = "A Controlled Security Testing Environment for AI Systems"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_after = Pt(10)

    p2 = tf_desc.add_paragraph()
    p2.text = (
        "SafeArena enables authorized adversarial AI evaluation while preventing unauthorized "
        "cross-zone lateral movement. Every request is mediated by a default-deny security gateway, "
        "monitored for prompt-injection threats, and sealed in a tamper-evident SHA-256 audit ledger."
    )
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(11)
    p2.font.color.rgb = TEXT_MUTED

    # Metadata Card at Bottom Left
    add_card(slide, Inches(0.8), Inches(5.5), Inches(5.8), Inches(1.35), bg=CARD_BG, border=CARD_BORDER)
    meta_box = slide.shapes.add_textbox(Inches(1.0), Inches(5.62), Inches(5.4), Inches(1.1))
    tf_meta = meta_box.text_frame
    tf_meta.word_wrap = True
    
    pm1 = tf_meta.paragraphs[0]
    pm1.text = "TEAM: VSV The Tech Giants"
    pm1.font.name = FONT_FAMILY
    pm1.font.size = Pt(11)
    pm1.font.bold = True
    pm1.font.color.rgb = CYAN

    pm2 = tf_meta.add_paragraph()
    pm2.text = "PROJECT STATUS: Functional Working Prototype (103 Unit & API Tests Passing)"
    pm2.font.name = FONT_FAMILY
    pm2.font.size = Pt(9.5)
    pm2.font.color.rgb = TEXT_WHITE

    pm3 = tf_meta.add_paragraph()
    pm3.text = "DEPLOYMENT MODES: Local Policy Simulation  |  Multi-Container Docker Isolation"
    pm3.font.name = FONT_FAMILY
    pm3.font.size = Pt(9.5)
    pm3.font.color.rgb = TEXT_MUTED

    # Right Hero Visual: Architectural Overview Card
    add_card(slide, Inches(6.9), Inches(1.15), Inches(5.6), Inches(5.7), bg=CARD_BG, border=CYAN, border_width=1.5)
    
    # Hero Visual Header
    vh_box = slide.shapes.add_textbox(Inches(7.2), Inches(1.4), Inches(5.0), Inches(0.4))
    tf_vh = vh_box.text_frame
    p_vh = tf_vh.paragraphs[0]
    p_vh.text = "PROTECTED TOPOLOGY ARCHITECTURE"
    p_vh.font.name = FONT_FAMILY
    p_vh.font.size = Pt(11)
    p_vh.font.bold = True
    p_vh.font.color.rgb = CYAN

    # Zone Box 1: Red Sandbox
    add_card(slide, Inches(7.2), Inches(1.9), Inches(2.3), Inches(1.15), bg=CARD_HOVER, border=RED, border_width=1.5)
    add_pill(slide, Inches(7.35), Inches(2.02), Inches(0.85), Inches(0.24), "RED ZONE", RED, TEXT_WHITE, font_size=8)
    z1_box = slide.shapes.add_textbox(Inches(7.35), Inches(2.32), Inches(2.0), Inches(0.65))
    tf_z1 = z1_box.text_frame
    tf_z1.word_wrap = True
    pz1 = tf_z1.paragraphs[0]
    pz1.text = "Adversarial Probes\nAttack Tooling & Fuzzing"
    pz1.font.name = FONT_FAMILY
    pz1.font.size = Pt(9.5)
    pz1.font.color.rgb = TEXT_WHITE

    # Zone Box 2: Blue Sandbox
    add_card(slide, Inches(9.9), Inches(1.9), Inches(2.3), Inches(1.15), bg=CARD_HOVER, border=BLUE, border_width=1.5)
    add_pill(slide, Inches(10.05), Inches(2.02), Inches(0.85), Inches(0.24), "BLUE ZONE", BLUE, TEXT_WHITE, font_size=8)
    z2_box = slide.shapes.add_textbox(Inches(10.05), Inches(2.32), Inches(2.0), Inches(0.65))
    tf_z2 = z2_box.text_frame
    tf_z2.word_wrap = True
    pz2 = tf_z2.paragraphs[0]
    pz2.text = "Defensive State\nProtected Resources & Rules"
    pz2.font.name = FONT_FAMILY
    pz2.font.size = Pt(9.5)
    pz2.font.color.rgb = TEXT_WHITE

    # Central Gateway Box
    add_card(slide, Inches(7.2), Inches(3.25), Inches(5.0), Inches(1.2), bg=CARD_HOVER, border=CYAN, border_width=2)
    add_pill(slide, Inches(7.35), Inches(3.38), Inches(1.8), Inches(0.25), "SECURITY GATEWAY", CYAN, BG_COLOR, font_size=8.5, bold=True)
    add_pill(slide, Inches(10.2), Inches(3.38), Inches(1.8), Inches(0.25), "POLICY: DEFAULT-DENY", AMBER, BG_COLOR, font_size=8, bold=True)
    gw_box = slide.shapes.add_textbox(Inches(7.35), Inches(3.72), Inches(4.7), Inches(0.6))
    tf_gw = gw_box.text_frame
    tf_gw.word_wrap = True
    pgw = tf_gw.paragraphs[0]
    pgw.text = "Central Policy Enforcement  ·  Injection Heuristic Inspection  ·  Zero Cross-Zone Bypass"
    pgw.font.name = FONT_FAMILY
    pgw.font.size = Pt(9.5)
    pgw.font.bold = True
    pgw.font.color.rgb = TEXT_WHITE

    # Zone Box 3: Client LLM
    add_card(slide, Inches(7.2), Inches(4.65), Inches(5.0), Inches(0.95), bg=CARD_HOVER, border=PURPLE, border_width=1.5)
    add_pill(slide, Inches(7.35), Inches(4.78), Inches(1.4), Inches(0.24), "CLIENT LLM ZONE", PURPLE, TEXT_WHITE, font_size=8)
    llm_box = slide.shapes.add_textbox(Inches(8.9), Inches(4.78), Inches(3.1), Inches(0.7))
    tf_llm = llm_box.text_frame
    tf_llm.word_wrap = True
    pllm = tf_llm.paragraphs[0]
    pllm.text = "Isolated Target AI System (Deterministic Mock or Google Gemini API)"
    pllm.font.name = FONT_FAMILY
    pllm.font.size = Pt(9)
    pllm.font.color.rgb = TEXT_WHITE

    # Audit Trail Strip at Bottom of Card
    add_card(slide, Inches(7.2), Inches(5.8), Inches(5.0), Inches(0.8), bg=CARD_HOVER, border=GREEN, border_width=1)
    add_pill(slide, Inches(7.35), Inches(5.92), Inches(1.5), Inches(0.22), "SHA-256 AUDIT CHAIN", GREEN, BG_COLOR, font_size=8, bold=True)
    aud_box = slide.shapes.add_textbox(Inches(9.0), Inches(5.9), Inches(3.1), Inches(0.6))
    tf_aud = aud_box.text_frame
    tf_aud.word_wrap = True
    paud = tf_aud.paragraphs[0]
    paud.text = "Cryptographic Record Linking & Head Checkpoint"
    paud.font.name = FONT_FAMILY
    paud.font.size = Pt(8.5)
    paud.font.color.rgb = TEXT_MUTED

    set_speaker_notes(
        slide,
        "Good morning judges. We are team VSV The Tech Giants, presenting SafeArena. "
        "As generative AI and autonomous agents enter production, organizations must conduct rigorous adversarial "
        "testing. But testing AI systems today without strict controls is dangerous: red teams running prompt injections "
        "can accidentally compromise backend databases or staging environments. "
        "SafeArena introduces an integrated, controlled testing environment based on four principles: "
        "Isolate, Control, Detect, and Prove. We segregate testing into isolated zones, enforce a default-deny gateway, "
        "detect prompt injections, and mathematically prove every decision using a SHA-256 audit ledger."
    )


def build_slide_2(prs):
    """Slide 2 — The Problem"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "01 // THE THREAT LANDSCAPE",
        "The Danger of Uncontrolled AI Security Testing",
        "Evaluating AI systems in shared, unsegmented environments introduces severe security and operational liabilities."
    )

    card_w = Inches(3.64)
    card_h = Inches(4.1)
    card_top = Inches(1.85)

    # Card 1: Uncontained Testing
    add_card(slide, Inches(0.8), card_top, card_w, card_h, border=RED, border_width=1.5)
    add_pill(slide, Inches(1.05), card_top + Inches(0.25), Inches(1.6), Inches(0.28), "RED TEAM RISK", RED, TEXT_WHITE, font_size=9)
    
    t1_box = slide.shapes.add_textbox(Inches(1.05), card_top + Inches(0.65), Inches(3.14), Inches(3.2))
    tf1 = t1_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Uncontained Adversarial Blast Radius"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_after = Pt(10)

    items1 = [
        "Adversarial prompts, jailbreaks, and autonomous agent exploits are often tested on shared corporate networks.",
        "Without hard network and process isolation, payloads can execute lateral movement toward internal databases or defenses.",
        "Uncontrolled tests can inadvertently exfiltrate sensitive credentials, canary tokens, or proprietary prompts.",
        "CRITICAL RISK: Testing red-team exploits can unintentionally compromise internal production state."
    ]
    for it in items1:
        p = tf1.add_paragraph()
        p.text = "• " + it
        p.font.name = FONT_FAMILY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED if not it.startswith("CRITICAL") else RED
        p.font.bold = it.startswith("CRITICAL")
        p.space_after = Pt(6)

    # Card 2: Missing Policy Gateway
    add_card(slide, Inches(4.84), card_top, card_w, card_h, border=AMBER, border_width=1.5)
    add_pill(slide, Inches(5.09), card_top + Inches(0.25), Inches(1.8), Inches(0.28), "ENFORCEMENT GAP", AMBER, BG_COLOR, font_size=9)

    t2_box = slide.shapes.add_textbox(Inches(5.09), card_top + Inches(0.65), Inches(3.14), Inches(3.2))
    tf2 = t2_box.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Direct, Unmediated Access Paths"
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(13)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE
    p2.space_after = Pt(10)

    items2 = [
        "Testing tools routinely connect directly to target LLM endpoints without an intervening policy enforcement layer.",
        "There is no active policy inspection determining whether the caller is authorized to invoke specific model tools or modes.",
        "Cross-zone communications (such as red attackers probing blue defenses) proceed unhindered.",
        "CRITICAL RISK: Security teams cannot enforce granular access boundaries between testers, models, and defended assets."
    ]
    for it in items2:
        p = tf2.add_paragraph()
        p.text = "• " + it
        p.font.name = FONT_FAMILY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED if not it.startswith("CRITICAL") else AMBER
        p.font.bold = it.startswith("CRITICAL")
        p.space_after = Pt(6)

    # Card 3: Malleable Telemetry
    add_card(slide, Inches(8.88), card_top, card_w, card_h, border=CYAN, border_width=1.5)
    add_pill(slide, Inches(9.13), card_top + Inches(0.25), Inches(1.8), Inches(0.28), "EVIDENTIARY BLINDSPOT", CYAN, BG_COLOR, font_size=9)

    t3_box = slide.shapes.add_textbox(Inches(9.13), card_top + Inches(0.65), Inches(3.14), Inches(3.2))
    tf3 = t3_box.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "Ephemeral & Malleable Audit Logs"
    p3.font.name = FONT_FAMILY
    p3.font.size = Pt(13)
    p3.font.bold = True
    p3.font.color.rgb = TEXT_WHITE
    p3.space_after = Pt(10)

    items3 = [
        "Test logs are frequently relegated to terminal stdout, ephemeral debug files, or mutable database tables.",
        "Standard log files can be arbitrarily edited, truncated, reordered, or deleted by system operators or attackers.",
        "Auditors, governance boards, and GRC teams have zero cryptographic assurance of what actually happened during testing.",
        "CRITICAL RISK: Inability to prove non-repudiation or satisfy emerging AI compliance frameworks (NIST AI RMF, EU AI Act)."
    ]
    for it in items3:
        p = tf3.add_paragraph()
        p.text = "• " + it
        p.font.name = FONT_FAMILY
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED if not it.startswith("CRITICAL") else CYAN
        p.font.bold = it.startswith("CRITICAL")
        p.space_after = Pt(6)

    # Bottom Callout Summary
    bot_card = add_card(slide, Inches(0.8), Inches(6.15), Inches(11.72), Inches(0.75), bg=CARD_HOVER, border=CARD_BORDER)
    bot_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.22), Inches(11.3), Inches(0.6))
    tf_bot = bot_box.text_frame
    tf_bot.word_wrap = True
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = (
        "CORE PROBLEM: AI security testing requires an environment where red teams can be aggressively adversarial, "
        "blue assets remain strictly untouchable, and every security event is cryptographically non-repudiable."
    )
    p_bot.font.name = FONT_FAMILY
    p_bot.font.size = Pt(10)
    p_bot.font.bold = True
    p_bot.font.color.rgb = TEXT_WHITE

    set_speaker_notes(
        slide,
        "Why is AI security testing fundamentally different and more challenging? "
        "First, when red teams test prompt injections and agent jailbreaks, they aren't just sending static text. "
        "Modern LLMs invoke tools, call internal APIs, and access memory. If you run red-team testing in a flat environment, "
        "an injected payload can trigger unexpected lateral access into blue-team defensive state or company data. "
        "Second, there is rarely an intermediary policy gate. Testers query models directly without access control enforcement. "
        "Third, standard application logs provide zero cryptographic proof. An operator can edit or delete a log line, "
        "meaning you cannot prove to an auditor what was tested. SafeArena addresses this entire problem chain."
    )


def build_slide_3(prs):
    """Slide 3 — Why Existing Approaches Leave a Gap (High-Contrast Redesign)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "02 // THE DESIGN GAP",
        "Why Existing Approaches Leave an Evidentiary Void",
        "Current tooling treats testing, network isolation, policy enforcement, and audit logging as disconnected silos."
    )

    card_w = Inches(3.64)
    card_h = Inches(4.55)
    card_top = Inches(1.85)

    # Column 1: Ad-Hoc Scripting
    add_card(slide, Inches(0.8), card_top, card_w, card_h, border=RED, border_width=1)
    add_pill(slide, Inches(1.05), card_top + Inches(0.2), Inches(1.8), Inches(0.26), "AD-HOC SCRIPTING", RED, TEXT_WHITE, font_size=8.5)
    
    t1_box = slide.shapes.add_textbox(Inches(1.05), card_top + Inches(0.55), Inches(3.14), Inches(3.8))
    tf1 = t1_box.text_frame
    tf1.word_wrap = True
    
    p = tf1.paragraphs[0]
    p.text = "Uncontrolled / Raw Scripts"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(10)

    rows1 = [
        ("Environment", "Local Python scripts, curl, or Jupyter"),
        ("Zone Isolation", "None: shared host OS & local network"),
        ("Policy Control", "None: direct socket connections to model"),
        ("Event Visibility", "Ephemeral stdout prints; lost on exit"),
        ("Audit Integrity", "Non-existent: raw logs are editable text"),
        ("Defensibility", "Zero proof of what actually occurred")
    ]
    for label, val in rows1:
        p = tf1.add_paragraph()
        run1 = p.add_run()
        run1.text = f"{label}: "
        run1.font.bold = True
        run1.font.color.rgb = TEXT_WHITE
        run1.font.size = Pt(9.5)

        run2 = p.add_run()
        run2.text = val
        run2.font.bold = False
        run2.font.color.rgb = TEXT_MUTED
        run2.font.size = Pt(9)
        p.space_after = Pt(6)

    # Column 2: Fragmented Enterprise Tools (Enhanced Contrast)
    add_card(slide, Inches(4.84), card_top, card_w, card_h, border=AMBER, border_width=1)
    add_pill(slide, Inches(5.09), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "FRAGMENTED ENTERPRISE", AMBER, BG_COLOR, font_size=8.5)

    t2_box = slide.shapes.add_textbox(Inches(5.09), card_top + Inches(0.55), Inches(3.14), Inches(3.8))
    tf2 = t2_box.text_frame
    tf2.word_wrap = True

    p = tf2.paragraphs[0]
    p.text = "Generic Proxies + Heavy SIEMs"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(10)

    rows2 = [
        ("Environment", "Complex cloud VPCs with generic proxies"),
        ("Zone Isolation", "Coarse-grained network security groups"),
        ("Policy Control", "Generic L7 HTTP rules; blind to AI threats"),
        ("Event Visibility", "Delayed batch ingestion into cloud SIEMs"),
        ("Audit Integrity", "Mutable SQL records; vulnerable to root"),
        ("Defensibility", "High cost; disconnected from AI context")
    ]
    for label, val in rows2:
        p = tf2.add_paragraph()
        run1 = p.add_run()
        run1.text = f"{label}: "
        run1.font.bold = True
        run1.font.color.rgb = TEXT_WHITE
        run1.font.size = Pt(9.5)

        run2 = p.add_run()
        run2.text = val
        run2.font.bold = False
        run2.font.color.rgb = TEXT_MUTED
        run2.font.size = Pt(9)
        p.space_after = Pt(6)

    # Column 3: SafeArena Integrated Blueprint
    add_card(slide, Inches(8.88), card_top, card_w, card_h, border=CYAN, border_width=2)
    add_pill(slide, Inches(9.13), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "SAFEARENA BLUEPRINT", CYAN, BG_COLOR, font_size=8.5, bold=True)

    t3_box = slide.shapes.add_textbox(Inches(9.13), card_top + Inches(0.55), Inches(3.14), Inches(3.8))
    tf3 = t3_box.text_frame
    tf3.word_wrap = True

    p = tf3.paragraphs[0]
    p.text = "Unified AI Security Fabric"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(10)

    rows3 = [
        ("Environment", "Dedicated Red/Blue sandboxes + Gateway"),
        ("Zone Isolation", "Docker internal subnets + dropped caps"),
        ("Policy Control", "Default-deny gateway with AI inspection"),
        ("Event Visibility", "Immediate, structured, severity-rated stream"),
        ("Audit Integrity", "Tamper-evident SHA-256 hash chains"),
        ("Defensibility", "Mathematically verifiable audit proof")
    ]
    for label, val in rows3:
        p = tf3.add_paragraph()
        run1 = p.add_run()
        run1.text = f"{label}: "
        run1.font.bold = True
        run1.font.color.rgb = CYAN
        run1.font.size = Pt(9.5)

        run2 = p.add_run()
        run2.text = val
        run2.font.bold = True
        run2.font.color.rgb = TEXT_WHITE
        run2.font.size = Pt(9)
        p.space_after = Pt(6)

    # Bottom Key Takeaway
    bot_card = add_card(slide, Inches(0.8), Inches(6.55), Inches(11.72), Inches(0.5), bg=CARD_HOVER, border=CYAN, border_width=1)
    bot_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.6), Inches(11.3), Inches(0.4))
    tf_bot = bot_box.text_frame
    tf_bot.word_wrap = True
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = "THE TAKEAWAY: SafeArena is not just a testing script or a generic firewall; it is an integrated, auditable security fabric."
    p_bot.font.name = FONT_FAMILY
    p_bot.font.size = Pt(9.5)
    p_bot.font.bold = True
    p_bot.font.color.rgb = CYAN

    set_speaker_notes(
        slide,
        "Let's be completely fair to existing tools. Organizations either use ad-hoc scripting or try to adapt enterprise SIEMs. "
        "With ad-hoc scripts, there is zero network isolation, zero policy mediation, and zero auditability. "
        "With enterprise tooling, you have generic Layer 7 proxies and centralized SIEMs. But these systems are blind "
        "to AI prompt injection heuristics, cost tens of thousands of dollars, and still store records in mutable database rows. "
        "SafeArena was designed to close this exact architectural gap: a lightweight, self-contained environment that unites "
        "container isolation, default-deny policy mediation, real-time event telemetry, and cryptographic audit proofs."
    )


def build_slide_4(prs):
    """Slide 4 — Our Solution: The SafeArena Framework"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "03 // ARCHITECTURAL PILLARS",
        "The SafeArena Framework: One Integrated Workflow",
        "A closed-loop security architecture designed to isolate testing, control access, detect threats, and prove integrity."
    )

    card_w = Inches(2.68)
    card_h = Inches(4.7)
    card_top = Inches(1.85)

    # Pillar 1: ISOLATE
    add_card(slide, Inches(0.8), card_top, card_w, card_h, border=BLUE, border_width=1.5)
    add_pill(slide, Inches(1.0), card_top + Inches(0.2), Inches(1.2), Inches(0.28), "1. ISOLATE", BLUE, TEXT_WHITE, font_size=9, bold=True)
    add_pill(slide, Inches(1.0), card_top + Inches(0.55), Inches(1.8), Inches(0.22), "ZONE SEGREGATION", CARD_BG, BLUE, font_size=8)

    t1 = slide.shapes.add_textbox(Inches(1.0), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Physical & Logical Zone Containment"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(8)

    bullets1 = [
        "Red Sandbox (adversarial testing) and Blue Sandbox (defensive state) exist in completely separate zones.",
        "In Docker mode, each zone is bound to an isolated bridge network (red_net, blue_net, llm_net).",
        "Networks configured with internal: true (no direct cross-zone routing and no public internet route).",
        "Container hardening: read-only root filesystems, dropped capabilities (cap_drop: ALL), unprivileged user."
    ]
    for b in bullets1:
        p = tf1.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Pillar 2: CONTROL
    add_card(slide, Inches(3.81), card_top, card_w, card_h, border=CYAN, border_width=1.5)
    add_pill(slide, Inches(4.01), card_top + Inches(0.2), Inches(1.2), Inches(0.28), "2. CONTROL", CYAN, BG_COLOR, font_size=9, bold=True)
    add_pill(slide, Inches(4.01), card_top + Inches(0.55), Inches(2.0), Inches(0.22), "SECURITY GATEWAY", CARD_BG, CYAN, font_size=8)

    t2 = slide.shapes.add_textbox(Inches(4.01), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf2 = t2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Default-Deny Policy Enforcement"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(8)

    bullets2 = [
        "The Security Gateway is the only entity attached to all zone networks; direct bypass is impossible.",
        "Strict default-deny policy: anything not explicitly authorized is blocked immediately.",
        "Authorized: Red → LLM (ALLOW), Blue → LLM (ALLOW).",
        "Unauthorized: Red → Blue (DENY 403), Blue → Red (DENY 403).",
        "Blocked requests are dropped at the gateway; payloads never touch the target destination."
    ]
    for b in bullets2:
        p = tf2.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Pillar 3: DETECT
    add_card(slide, Inches(6.82), card_top, card_w, card_h, border=AMBER, border_width=1.5)
    add_pill(slide, Inches(7.02), card_top + Inches(0.2), Inches(1.2), Inches(0.28), "3. DETECT", AMBER, BG_COLOR, font_size=9, bold=True)
    add_pill(slide, Inches(7.02), card_top + Inches(0.55), Inches(1.9), Inches(0.22), "EVENT TELEMETRY", CARD_BG, AMBER, font_size=8)

    t3 = slide.shapes.add_textbox(Inches(7.02), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf3 = t3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "Severity-Rated Security Events"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(8)

    bullets3 = [
        "Every decision produces a structured security event persisted to SQLite (events.db).",
        "Granular severity ratings: INFO (normal allowed calls), MEDIUM (injection heuristic hit), HIGH (policy violation), CRITICAL (canary leak).",
        "Regex heuristics detect adversarial prompt patterns and inspect model refusal states.",
        "Live operator console offers instant multi-parameter filtering and full-text search."
    ]
    for b in bullets3:
        p = tf3.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Pillar 4: PROVE
    add_card(slide, Inches(9.83), card_top, card_w, card_h, border=GREEN, border_width=1.5)
    add_pill(slide, Inches(10.03), card_top + Inches(0.2), Inches(1.2), Inches(0.28), "4. PROVE", GREEN, BG_COLOR, font_size=9, bold=True)
    add_pill(slide, Inches(10.03), card_top + Inches(0.55), Inches(1.9), Inches(0.22), "SHA-256 AUDIT LEDGER", CARD_BG, GREEN, font_size=8)

    t4 = slide.shapes.add_textbox(Inches(10.03), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf4 = t4.text_frame
    tf4.word_wrap = True
    p = tf4.paragraphs[0]
    p.text = "Tamper-Evident Hash Chaining"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(8)

    bullets4 = [
        "Every request is cryptographically appended to an immutable JSONL audit ledger (audit_log.jsonl).",
        "Record N embeds the SHA-256 digest of Record N-1, creating an unbroken mathematical chain from GENESIS.",
        "A separate head checkpoint (_head.json) detects tail truncation and record deletions.",
        "Single-click verification recalculates every hash in milliseconds; proven against 7 corruption scenarios."
    ]
    for b in bullets4:
        p = tf4.add_paragraph()
        p.text = "• " + b
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    set_speaker_notes(
        slide,
        "Here is the core SafeArena architecture, captured in four words: Isolate, Control, Detect, and Prove. "
        "First, we isolate the actors. In Docker mode, Red, Blue, and LLM zones run in hardened containers on distinct internal subnets. "
        "Second, we control communication. The Security Gateway is the only bridge. It enforces a strict default-deny policy. "
        "Third, we detect threats. Blocked cross-zone access raises high-severity events; prompt injection heuristic hits raise medium events. "
        "Fourth, we prove what happened. Every decision is hashed using SHA-256 and chained to the previous record. "
        "This gives organizations mathematical proof of their AI safety evaluations."
    )


def build_slide_5(prs):
    """Slide 5 — System Architecture (Enhanced with Directional Flow Badges & Visual Connectivity)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "04 // DEFENSE-IN-DEPTH TOPOLOGY",
        "SafeArena System Architecture & Gateway Mediation",
        "Strict gateway mediation guarantees that adversarial testing is contained while unauthorized paths are blocked."
    )

    # Top Center: Client LLM Card
    add_card(slide, Inches(3.4), Inches(1.85), Inches(3.4), Inches(1.05), bg=CARD_HOVER, border=PURPLE, border_width=1.5)
    add_pill(slide, Inches(3.55), Inches(1.95), Inches(1.4), Inches(0.24), "CLIENT LLM ZONE", PURPLE, TEXT_WHITE, font_size=8)
    add_pill(slide, Inches(5.05), Inches(1.95), Inches(1.5), Inches(0.24), "llm_net: internal", CARD_BG, TEXT_DIM, font_size=7.5)
    llm_t = slide.shapes.add_textbox(Inches(3.55), Inches(2.22), Inches(3.1), Inches(0.6))
    tf_llm = llm_t.text_frame
    tf_llm.word_wrap = True
    pllm = tf_llm.paragraphs[0]
    pllm.text = "llm-service:8103  ·  Isolated Internal Subnet\nDeterministic Local Mock or Google Gemini API"
    pllm.font.name = FONT_FAMILY
    pllm.font.size = Pt(8.5)
    pllm.font.color.rgb = TEXT_WHITE

    # Connector Badge between Gateway and LLM
    add_pill(slide, Inches(4.0), Inches(2.98), Inches(2.2), Inches(0.24), "▲ AUTHORIZED DISPATCH", PURPLE, TEXT_WHITE, font_size=7.5, bold=True)

    # Middle Center: Security Gateway
    add_card(slide, Inches(3.2), Inches(3.3), Inches(3.8), Inches(1.75), bg=CARD_HOVER, border=CYAN, border_width=2)
    add_pill(slide, Inches(3.35), Inches(3.42), Inches(1.8), Inches(0.26), "SECURITY GATEWAY", CYAN, BG_COLOR, font_size=9, bold=True)
    add_pill(slide, Inches(5.2), Inches(3.42), Inches(1.65), Inches(0.26), "PORT 8000 (LOOPBACK)", CARD_BG, CYAN, font_size=7.5)
    
    gw_t = slide.shapes.add_textbox(Inches(3.35), Inches(3.75), Inches(3.5), Inches(1.2))
    tf_gw = gw_t.text_frame
    tf_gw.word_wrap = True
    pgw1 = tf_gw.paragraphs[0]
    pgw1.text = "Policy Engine (Default-Deny Evaluation Matrix)"
    pgw1.font.name = FONT_FAMILY
    pgw1.font.size = Pt(9)
    pgw1.font.bold = True
    pgw1.font.color.rgb = TEXT_WHITE

    pgw2 = tf_gw.add_paragraph()
    pgw2.text = "Prompt Injection Heuristic Inspection & Refusals"
    pgw2.font.name = FONT_FAMILY
    pgw2.font.size = Pt(8.5)
    pgw2.font.color.rgb = TEXT_MUTED

    pgw3 = tf_gw.add_paragraph()
    pgw3.text = "Cryptographic Audit Dispatcher & Event Emitter"
    pgw3.font.name = FONT_FAMILY
    pgw3.font.size = Pt(8.5)
    pgw3.font.color.rgb = TEXT_MUTED

    # Left: Red Sandbox
    add_card(slide, Inches(0.8), Inches(3.3), Inches(1.8), Inches(1.75), bg=CARD_HOVER, border=RED, border_width=1.5)
    add_pill(slide, Inches(0.95), Inches(3.42), Inches(1.0), Inches(0.24), "RED SANDBOX", RED, TEXT_WHITE, font_size=8)
    add_pill(slide, Inches(0.95), Inches(3.7), Inches(1.5), Inches(0.2), "red_net: internal", CARD_BG, TEXT_DIM, font_size=7.5)
    red_t = slide.shapes.add_textbox(Inches(0.95), Inches(3.95), Inches(1.5), Inches(1.0))
    tf_red = red_t.text_frame
    tf_red.word_wrap = True
    pred = tf_red.paragraphs[0]
    pred.text = "red-service:8101\nAdversarial testing\nAttack payloads\nUnprivileged root"
    pred.font.name = FONT_FAMILY
    pred.font.size = Pt(8.5)
    pred.font.color.rgb = TEXT_MUTED

    # Flow Badge: Red to Gateway (cleanly positioned in the 0.6" gap between 2.6 and 3.2)
    add_pill(slide, Inches(2.62), Inches(4.0), Inches(0.56), Inches(0.26), "ALLOW ►", GREEN, BG_COLOR, font_size=7, bold=True)

    # Right: Blue Sandbox
    add_card(slide, Inches(7.6), Inches(3.3), Inches(1.8), Inches(1.75), bg=CARD_HOVER, border=BLUE, border_width=1.5)
    add_pill(slide, Inches(7.75), Inches(3.42), Inches(1.0), Inches(0.24), "BLUE SANDBOX", BLUE, TEXT_WHITE, font_size=8)
    add_pill(slide, Inches(7.75), Inches(3.7), Inches(1.5), Inches(0.2), "blue_net: internal", CARD_BG, TEXT_DIM, font_size=7.5)
    blue_t = slide.shapes.add_textbox(Inches(7.75), Inches(3.95), Inches(1.5), Inches(1.0))
    tf_blue = blue_t.text_frame
    tf_blue.word_wrap = True
    pblue = tf_blue.paragraphs[0]
    pblue.text = "blue-service:8102\nDefensive state\nProtected assets\nRestricted access"
    pblue.font.name = FONT_FAMILY
    pblue.font.size = Pt(8.5)
    pblue.font.color.rgb = TEXT_MUTED

    # Flow Badge: Blue to Gateway (cleanly positioned in the 0.6" gap between 7.0 and 7.6)
    add_pill(slide, Inches(7.02), Inches(4.0), Inches(0.56), Inches(0.26), "◄ ALLOW", GREEN, BG_COLOR, font_size=7, bold=True)

    # Cross-Zone Blocked Barrier at Center
    add_pill(slide, Inches(3.2), Inches(5.12), Inches(3.8), Inches(0.22), "RED ◄── [BLOCKED: 403 FORBIDDEN] ──► BLUE", RED, TEXT_WHITE, font_size=7.5, bold=True)

    # Bottom Left: Event Store
    add_card(slide, Inches(0.8), Inches(5.42), Inches(4.1), Inches(1.3), bg=CARD_HOVER, border=AMBER, border_width=1)
    add_pill(slide, Inches(0.95), Inches(5.52), Inches(1.7), Inches(0.22), "SECURITY EVENT STORE", AMBER, BG_COLOR, font_size=8, bold=True)
    ev_t = slide.shapes.add_textbox(Inches(0.95), Inches(5.8), Inches(3.8), Inches(0.8))
    tf_ev = ev_t.text_frame
    tf_ev.word_wrap = True
    pev = tf_ev.paragraphs[0]
    pev.text = "SQLite (data/events.db)  ·  ACID Persistence\nParameterized queries, severity indexing (Info→Critical), audit foreign key"
    pev.font.name = FONT_FAMILY
    pev.font.size = Pt(8.5)
    pev.font.color.rgb = TEXT_WHITE

    # Bottom Right: Audit Store & Checkpoint
    add_card(slide, Inches(5.1), Inches(5.42), Inches(4.1), Inches(1.3), bg=CARD_HOVER, border=GREEN, border_width=1)
    add_pill(slide, Inches(5.25), Inches(5.52), Inches(1.7), Inches(0.22), "HASH-CHAINED AUDIT", GREEN, BG_COLOR, font_size=8, bold=True)
    au_t = slide.shapes.add_textbox(Inches(5.25), Inches(5.8), Inches(3.8), Inches(0.8))
    tf_au = au_t.text_frame
    tf_au.word_wrap = True
    pau = tf_au.paragraphs[0]
    pau.text = "JSONL (data/audit_log.jsonl)  ·  SHA-256 Links\nCheckpoint (_head.json) detects tail truncation & record deletions"
    pau.font.name = FONT_FAMILY
    pau.font.size = Pt(8.5)
    pau.font.color.rgb = TEXT_WHITE

    # Right Side: Access Policy Matrix & Rules Card
    add_card(slide, Inches(9.45), Inches(1.85), Inches(3.08), Inches(4.87), bg=CARD_BG, border=CARD_BORDER)
    add_pill(slide, Inches(9.65), Inches(2.0), Inches(2.68), Inches(0.28), "ACCESS POLICY MATRIX", CARD_HOVER, CYAN, font_size=9, bold=True)

    pm_t = slide.shapes.add_textbox(Inches(9.65), Inches(2.35), Inches(2.68), Inches(4.2))
    tf_pm = pm_t.text_frame
    tf_pm.word_wrap = True
    
    p = tf_pm.paragraphs[0]
    p.text = "Explicit Policy Rules:"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(6)

    rules = [
        ("Red → LLM", "ALLOW (200)", GREEN, "Authorized adversarial probe via Gateway"),
        ("Blue → LLM", "ALLOW (200)", GREEN, "Authorized defensive prompt via Gateway"),
        ("Red → Blue", "DENY (403)", RED, "Blocked: Cannot touch defense state"),
        ("Blue → Red", "DENY (403)", RED, "Blocked: Cannot inspect attack payload"),
        ("LLM → Red", "DENY (403)", RED, "Blocked: Model cannot initiate outbound"),
        ("Unknown", "DENY (403)", RED, "Default-deny on unlisted zone / route")
    ]
    for route, action, col, expl in rules:
        p = tf_pm.add_paragraph()
        run1 = p.add_run()
        run1.text = f"{route}: "
        run1.font.bold = True
        run1.font.color.rgb = TEXT_WHITE
        run1.font.size = Pt(9)

        run2 = p.add_run()
        run2.text = action
        run2.font.bold = True
        run2.font.color.rgb = col
        run2.font.size = Pt(9)

        p2 = tf_pm.add_paragraph()
        p2.text = f"  └ {expl}"
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(7.5)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_after = Pt(4)

    set_speaker_notes(
        slide,
        "Slide 5 shows our core defense-in-depth architecture. Notice three critical architectural details: "
        "First, network separation. Red, Blue, and LLM services run on three separate internal Docker networks: "
        "red_net, blue_net, and llm_net. They have no route to each other and no route to the internet. "
        "Second, the Security Gateway is the only bridge connected to all three networks. It enforces our default-deny matrix. "
        "Red can reach the LLM through the gateway. Blue can reach the LLM through the gateway. "
        "However, Red attempting to reach Blue directly is blocked at the gateway with an HTTP 403 Forbidden. "
        "The blocked payload is dropped immediately and never forwarded. "
        "Third, persistence: decisions are committed to SQLite for rapid querying and appended to the SHA-256 audit ledger."
    )


def build_slide_6(prs):
    """Slide 6 — How a Request Works"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "05 // THE REQUEST LIFECYCLE",
        "How a Request Works: From Ingress to Cryptographic Proof",
        "A rigorous 6-stage evaluation pipeline executed in milliseconds for every single test invocation."
    )

    step_w = Inches(1.85)
    step_h = Inches(4.3)
    step_top = Inches(1.85)
    gap = Inches(0.12)

    steps = [
        ("1. INGRESS", "Probe Ingress", CYAN, [
            "Source zone initiates request to Gateway API.",
            "JSON payload: {source, target, payload}.",
            "Gateway captures timestamp and generates unique request_id and session_id."
        ]),
        ("2. EVALUATE", "Policy Check", AMBER, [
            "Policy engine normalizes source and target.",
            "Queries explicit access matrix.",
            "Default-deny rule: anything unlisted is marked unauthorized.",
            "Decision object formed."
        ]),
        ("3. ENFORCE", "Gate Decision", RED, [
            "If DENIED (e.g. Red→Blue): Immediate HTTP 403 response.",
            "Payload is completely dropped; never forwarded.",
            "If ALLOWED (Red→LLM): Passed to inspection pipeline."
        ]),
        ("4. INSPECT", "Heuristics & LLM", PURPLE, [
            "Regex heuristic scans for prompt injection patterns.",
            "Payload forwarded to Client LLM (mock or Gemini).",
            "Model response, refusal, or canary leak captured."
        ]),
        ("5. CHAIN", "SHA-256 Ledger", GREEN, [
            "Canonical JSON created (sorted keys, ASCII safe).",
            "hash = SHA256(canonical JSON + prev_hash).",
            "Appended to audit_log.jsonl.",
            "Atomic update to _head.json."
        ]),
        ("6. TELEMETRY", "Events & UI", BLUE, [
            "Structured security event committed to SQLite.",
            "Event stores audit_hash foreign reference.",
            "Live UI updates: counters, event log, and audit verification table."
        ])
    ]

    for i, (pill_txt, title, col, bullets) in enumerate(steps):
        left = Inches(0.8) + i * (step_w + gap)
        add_card(slide, left, step_top, step_w, step_h, border=col, border_width=1.5)
        add_pill(slide, left + Inches(0.15), step_top + Inches(0.2), step_w - Inches(0.3), Inches(0.26), pill_txt, col, BG_COLOR if col != RED and col != PURPLE and col != BLUE else TEXT_WHITE, font_size=8, bold=True)
        
        sb = slide.shapes.add_textbox(left + Inches(0.12), step_top + Inches(0.55), step_w - Inches(0.24), step_h - Inches(0.65))
        tf = sb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(6)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = "• " + b
            pb.font.name = FONT_FAMILY
            pb.font.size = Pt(8)
            pb.font.color.rgb = TEXT_MUTED
            pb.space_after = Pt(4)

    # Bottom Control-Level Clarification Banner
    bot_card = add_card(slide, Inches(0.8), Inches(6.3), Inches(11.72), Inches(0.75), bg=CARD_HOVER, border=CYAN, border_width=1)
    bot_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.38), Inches(11.3), Inches(0.6))
    tf_bot = bot_box.text_frame
    tf_bot.word_wrap = True
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = (
        "DUAL-LAYER CONTROL ARCHITECTURE: The Security Gateway policy decision is an application-level control (inspecting payload and metadata). "
        "Docker network segmentation provides a separate, physical network-level control (preventing raw socket bypass between zones)."
    )
    p_bot.font.name = FONT_FAMILY
    p_bot.font.size = Pt(9.5)
    p_bot.font.bold = True
    p_bot.font.color.rgb = CYAN

    set_speaker_notes(
        slide,
        "Let's trace the journey of a single security test request through SafeArena. "
        "Step 1: The test runner posts a payload with a declared source and target. "
        "Step 2: The policy engine evaluates the route against our default-deny matrix. "
        "Step 3: If unauthorized, like Red attempting to reach Blue, the gateway terminates the connection immediately with HTTP 403. "
        "The payload is discarded and never forwarded. "
        "Step 4: If authorized, such as Red querying the LLM, the payload passes through heuristic prompt injection detection and reaches the model. "
        "Step 5: The gateway calculates the SHA-256 hash of the transaction, canonicalizes the JSON, chains it to the previous record, "
        "and updates the head checkpoint. "
        "Step 6: A structured security event is saved to SQLite, linking directly to the audit hash. "
        "Notice our dual control: the Gateway handles application policy; Docker handles Layer-3 network isolation."
    )


def build_slide_7(prs):
    """Slide 7 — Security Engineering and Trust"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "06 // CRYPTOGRAPHIC ASSURANCE",
        "Security Engineering & Verifiable Trust Architecture",
        "How SafeArena uses SHA-256 hash chaining to detect tampering, and our defensible threat boundaries."
    )

    card_w = Inches(3.64)
    card_h = Inches(4.7)
    card_top = Inches(1.85)

    # Card 1: Hash Chain Mechanics
    add_card(slide, Inches(0.8), card_top, card_w, card_h, border=CYAN, border_width=1.5)
    add_pill(slide, Inches(1.05), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "SHA-256 HASH CHAINING", CYAN, BG_COLOR, font_size=8.5, bold=True)

    t1 = slide.shapes.add_textbox(Inches(1.05), card_top + Inches(0.55), Inches(3.14), Inches(4.0))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Mathematical Integrity Mechanics"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_after = Pt(8)

    pts1 = [
        ("Append-Only JSONL", "Every decision appends a canonical JSON line to data/audit_log.jsonl."),
        ("Canonical Serialization", "json.dumps with sort_keys=True and ensure_ascii=True eliminates encoding ambiguity."),
        ("Cryptographic Linking", "Record N contains prev_hash = SHA256(Record N-1). First record anchors to GENESIS."),
        ("Head Checkpoint", "Latest count and head hash written atomically to _head.json."),
        ("Tail Protection", "Deleting lines from the end of the log triggers a checkpoint count mismatch during verification.")
    ]
    for k, v in pts1:
        p = tf1.add_paragraph()
        run1 = p.add_run()
        run1.text = f"{k}: "
        run1.font.bold = True
        run1.font.color.rgb = TEXT_WHITE
        run1.font.size = Pt(8.5)

        run2 = p.add_run()
        run2.text = v
        run2.font.bold = False
        run2.font.color.rgb = TEXT_MUTED
        run2.font.size = Pt(8.5)
        p.space_after = Pt(6)

    # Card 2: Tamper Detection in Action
    add_card(slide, Inches(4.84), card_top, card_w, card_h, border=AMBER, border_width=1.5)
    add_pill(slide, Inches(5.09), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "TAMPER DETECTION PROOF", AMBER, BG_COLOR, font_size=8.5, bold=True)

    t2 = slide.shapes.add_textbox(Inches(5.09), card_top + Inches(0.55), Inches(3.14), Inches(4.0))
    tf2 = t2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Concrete Tamper Detection"
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(12)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE
    p2.space_after = Pt(8)

    pts2 = [
        ("Tamper Scenario", "Adversary changes 1 character in Record #2 (e.g. BLOCKED → ALLOWED)."),
        ("Immediate Impact", "SHA-256 digest of Record #2 changes completely."),
        ("Chain Break", "Record #3's prev_hash points to old hash #2. Mismatch detected!"),
        ("7 Automated Tamper Tests", "Validates against: Edit, Edit+Rehash, Middle Deletion, Reordering, Forged Insert, Tail Truncation, and Corrupt JSON lines."),
        ("Verified Outcome", "100% of simulated corruption attacks detected without modifying live log.")
    ]
    for k, v in pts2:
        p = tf2.add_paragraph()
        run1 = p.add_run()
        run1.text = f"{k}: "
        run1.font.bold = True
        run1.font.color.rgb = AMBER if k == "Verified Outcome" else TEXT_WHITE
        run1.font.size = Pt(8.5)

        run2 = p.add_run()
        run2.text = v
        run2.font.bold = (k == "Verified Outcome")
        run2.font.color.rgb = TEXT_WHITE if k == "Verified Outcome" else TEXT_MUTED
        run2.font.size = Pt(8.5)
        p.space_after = Pt(6)

    # Card 3: Defensible Trust Boundaries
    add_card(slide, Inches(8.88), card_top, card_w, card_h, border=GREEN, border_width=1.5)
    add_pill(slide, Inches(9.13), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "HONEST TRUST MODEL", GREEN, BG_COLOR, font_size=8.5, bold=True)

    t3 = slide.shapes.add_textbox(Inches(9.13), card_top + Inches(0.55), Inches(3.14), Inches(4.0))
    tf3 = t3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "Defensible Threat Boundaries"
    p3.font.name = FONT_FAMILY
    p3.font.size = Pt(12)
    p3.font.bold = True
    p3.font.color.rgb = TEXT_WHITE
    p3.space_after = Pt(8)

    pts3 = [
        "No Exaggerated Claims: We do not claim SafeArena is unhackable or a silver bullet.",
        "Documented Limitation: A local hash chain catches in-flight edits, reordering, and truncations. However, an attacker with full host OS root access could rewrite both the log and checkpoint.",
        "Production Roadmap for Root Protection:",
        "  1. External HMAC key stored in KMS / HSM.",
        "  2. WORM (Write-Once-Read-Many) S3 Object Lock storage.",
        "  3. Periodically publishing head hashes to an external public transparency log or blockchain."
    ]
    for pt in pts3:
        p = tf3.add_paragraph()
        p.text = "• " + pt if not pt.startswith("  ") else pt
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = CYAN if pt.startswith("  ") else TEXT_MUTED
        p.space_after = Pt(4)

    set_speaker_notes(
        slide,
        "Slide 7 explains how we mathematically prove the integrity of testing records. "
        "Every event is appended to a JSONL log where each row embeds the SHA-256 hash of the row before it. "
        "If someone changes a single letter in an earlier record, that record's hash changes. "
        "The very next record's previous hash link is instantly broken, and our verifier flags the exact row number. "
        "We also implemented a checkpoint file to catch tail truncation if an attacker tries to delete the latest lines. "
        "Crucially, we believe in honest cybersecurity engineering: a local hash chain alone cannot stop an attacker "
        "who has complete root filesystem access and rewrites both the log and checkpoint simultaneously. "
        "In our roadmap, we address this via external HMAC signing and WORM cloud storage."
    )


def build_slide_8(prs):
    """Slide 8 — Product Experience and Demonstration"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "07 // OPERATOR DASHBOARD & EVIDENCE",
        "The SafeArena Console: Live Telemetry & Verification",
        "A zero-dependency, high-visibility operator interface built with strict Content Security Policy and live verification."
    )

    # Left Column: Genuine Application Screenshot
    screenshot_path = Path(r"C:\Users\lenovo\.gemini\antigravity\scratch\SafeArena\safearena_dashboard.png")
    if screenshot_path.exists():
        add_card(slide, Inches(0.8), Inches(1.85), Inches(6.8), Inches(4.55), bg=CARD_BG, border=CYAN, border_width=1.5)
        slide.shapes.add_picture(str(screenshot_path), Inches(0.9), Inches(1.95), width=Inches(6.6), height=Inches(4.35))
    else:
        add_card(slide, Inches(0.8), Inches(1.85), Inches(6.8), Inches(4.55), bg=CARD_BG, border=CYAN, border_width=1.5)

    # Right Column: 4 Key Interactive Features
    add_card(slide, Inches(7.8), Inches(1.85), Inches(4.72), Inches(4.55), bg=CARD_BG, border=CARD_BORDER)
    add_pill(slide, Inches(8.05), Inches(2.05), Inches(2.4), Inches(0.26), "OPERATOR CAPABILITIES", CARD_HOVER, CYAN, font_size=8.5, bold=True)

    rf_box = slide.shapes.add_textbox(Inches(8.05), Inches(2.4), Inches(4.25), Inches(3.8))
    tf_rf = rf_box.text_frame
    tf_rf.word_wrap = True

    features = [
        ("1. Live Zone Status & One-Click Scenarios", [
            "Interactive buttons trigger authorized Red→LLM queries, Blue defensive prompts, and unauthorized Red→Blue attempts.",
            "Gateway visual indicator switches dynamically from idle to active / blocked (turns red on 403 violations)."
        ]),
        ("2. Filterable Security Event Stream", [
            "Real-time event feed powered by SQLite.",
            "Filter dynamically by severity (info, medium, high, critical), decision (ALLOWED, BLOCKED), zone, or text query."
        ]),
        ("3. Instant Audit Chain Verification", [
            "Single-click 'Verify audit chain' button recomputes every SHA-256 hash across the ledger in milliseconds.",
            "Displays verified head hash and total audit record count."
        ]),
        ("4. 7-Scenario Automated Tamper Test", [
            "Push-button self-test copies the log into a tempdir and corrupts copies 7 ways; asserts the verifier catches every single one."
        ])
    ]

    for title, bullets in features:
        p = tf_rf.add_paragraph() if tf_rf.paragraphs[0].text else tf_rf.paragraphs[0]
        p.text = title
        p.font.name = FONT_FAMILY
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(2)

        for b in bullets:
            pb = tf_rf.add_paragraph()
            pb.text = "• " + b
            pb.font.name = FONT_FAMILY
            pb.font.size = Pt(8)
            pb.font.color.rgb = TEXT_MUTED
            pb.space_after = Pt(3)

    # Bottom Verified Stats Ribbon
    bot_card = add_card(slide, Inches(0.8), Inches(6.5), Inches(11.72), Inches(0.55), bg=CARD_HOVER, border=GREEN, border_width=1)
    bot_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.58), Inches(11.3), Inches(0.4))
    tf_bot = bot_box.text_frame
    tf_bot.word_wrap = True
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = "VERIFIED TEST EVIDENCE: 103 Automated Tests Passing  ·  Playwright UI Smoke Test Passed  ·  Zero Inline Scripts (XSS Hardened)  ·  Parameterised SQL"
    p_bot.font.name = FONT_FAMILY
    p_bot.font.size = Pt(9.5)
    p_bot.font.bold = True
    p_bot.font.color.rgb = GREEN

    set_speaker_notes(
        slide,
        "Here you are looking at an authentic screenshot of the running SafeArena console. "
        "We built this as a zero-external-dependency, lightweight web dashboard adhering to a strict Content Security Policy. "
        "On the left, the operator has instant visibility into the zones and can trigger pre-configured test scenarios. "
        "When Red attempts to reach Blue, the gateway card immediately turns red, the blocked counter increments, "
        "and a high-severity POLICY_VIOLATION event is committed to SQLite. "
        "With one click on 'Verify audit chain', SafeArena recomputes every SHA-256 hash across the entire log. "
        "Clicking 'Run tamper test' proves our integrity verification by intentionally corrupting log copies seven different ways. "
        "Our entire test suite of 103 automated tests passed in 8.1 seconds."
    )


def build_slide_9(prs):
    """Slide 9 — Technology Stack and Implementation"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "08 // TECHNICAL IMPLEMENTATION",
        "SafeArena Technology Stack & Engineering Status",
        "Grounded in clean, hardened primitives with an honest distinction between implemented features and future roadmap."
    )

    card_w = Inches(2.68)
    card_h = Inches(4.65)
    card_top = Inches(1.85)

    # Card 1: Backend & Gateway
    add_card(slide, Inches(0.8), card_top, card_w, card_h, border=CYAN, border_width=1.5)
    add_pill(slide, Inches(1.0), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "GATEWAY & BACKEND", CYAN, BG_COLOR, font_size=8.5, bold=True)
    add_pill(slide, Inches(1.0), card_top + Inches(0.55), Inches(1.8), Inches(0.22), "IMPLEMENTED & VERIFIED", GREEN, BG_COLOR, font_size=7.5, bold=True)

    t1 = slide.shapes.add_textbox(Inches(1.0), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "Python 3.12 / Flask 3.1"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(6)

    pts1 = [
        "Modular Core: Engine modules (policy.py, gateway.py, audit.py, events.py) are completely framework-agnostic.",
        "FastAPI Port-Ready: Original MVP envisioned in FastAPI; built in Flask for offline zero-dep testability; app.py rewrite ready.",
        "Security Controls: Host/Origin header validation, strict CSP, rate limiting on POSTs, parameterised queries."
    ]
    for pt in pts1:
        p = tf1.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Card 2: Isolation & Docker
    add_card(slide, Inches(3.81), card_top, card_w, card_h, border=BLUE, border_width=1.5)
    add_pill(slide, Inches(4.01), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "ISOLATION & DOCKER", BLUE, TEXT_WHITE, font_size=8.5, bold=True)
    add_pill(slide, Inches(4.01), card_top + Inches(0.55), Inches(2.0), Inches(0.22), "COMPOSE TOPOLOGY READY", CYAN, BG_COLOR, font_size=7.5, bold=True)

    t2 = slide.shapes.add_textbox(Inches(4.01), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf2 = t2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Multi-Container Topology"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(6)

    pts2 = [
        "Docker Compose v2: 4 dedicated containers (gateway, red-service, blue-service, llm-service).",
        "Isolated Bridges: red_net, blue_net, llm_net configured with internal: true.",
        "Container Hardening: read_only: true, tmpfs: [/tmp], cap_drop: [ALL], security_opt: [no-new-privileges:true].",
        "Status: Local simulation verified; Docker topology verified via compose unit tests."
    ]
    for pt in pts2:
        p = tf2.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Card 3: Cryptography & Storage
    add_card(slide, Inches(6.82), card_top, card_w, card_h, border=GREEN, border_width=1.5)
    add_pill(slide, Inches(7.02), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "AUDIT & EVENT STORAGE", GREEN, BG_COLOR, font_size=8.5, bold=True)
    add_pill(slide, Inches(7.02), card_top + Inches(0.55), Inches(1.8), Inches(0.22), "IMPLEMENTED & VERIFIED", GREEN, BG_COLOR, font_size=7.5, bold=True)

    t3 = slide.shapes.add_textbox(Inches(7.02), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf3 = t3.text_frame
    tf3.word_wrap = True
    p = tf3.paragraphs[0]
    p.text = "SHA-256 & SQLite DB"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(6)

    pts3 = [
        "Python hashlib: SHA-256 for canonical JSON record hashing.",
        "JSONL Append-Only: High throughput log file with atomic checkpoint file (_head.json).",
        "SQLite 3 Events: events.db with LIKE-escaping, SQL-injection immunity, and closed connection safety on Windows.",
        "Zero-Loss Rotation: Old chains archived to data/archive/ with cryptographic head anchoring."
    ]
    for pt in pts3:
        p = tf3.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Card 4: AI Model Integration
    add_card(slide, Inches(9.83), card_top, card_w, card_h, border=PURPLE, border_width=1.5)
    add_pill(slide, Inches(10.03), card_top + Inches(0.2), Inches(2.2), Inches(0.26), "AI MODEL INTEGRATION", PURPLE, TEXT_WHITE, font_size=8.5, bold=True)
    add_pill(slide, Inches(10.03), card_top + Inches(0.55), Inches(1.8), Inches(0.22), "MOCK + GEMINI API READY", CYAN, BG_COLOR, font_size=7.5, bold=True)

    t4 = slide.shapes.add_textbox(Inches(10.03), card_top + Inches(0.85), Inches(2.28), Inches(3.6))
    tf4 = t4.text_frame
    tf4.word_wrap = True
    p = tf4.paragraphs[0]
    p.text = "Client LLM Abstraction"
    p.font.name = FONT_FAMILY
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(6)

    pts4 = [
        "Deterministic Local Mock: Supports 3 evaluation modes: benign prompt, injection refusal, and canary token leak.",
        "Google Gemini API: Pluggable upstream integration via LLM_PROVIDER=gemini and GEMINI_API_KEY in .env.",
        "Zero-Leak Key Architecture: Keys reside strictly in gateway memory; never returned in API responses, never logged, never sent to zones."
    ]
    for pt in pts4:
        p = tf4.add_paragraph()
        p.text = "• " + pt
        p.font.name = FONT_FAMILY
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(5)

    # Bottom Clarification
    bot_card = add_card(slide, Inches(0.8), Inches(6.6), Inches(11.72), Inches(0.48), bg=CARD_HOVER, border=CARD_BORDER)
    bot_box = slide.shapes.add_textbox(Inches(1.0), Inches(6.65), Inches(11.3), Inches(0.35))
    tf_bot = bot_box.text_frame
    tf_bot.word_wrap = True
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = "TRANSPARENCY NOTE: Local mode demonstrates policy enforcement only. Multi-container network isolation is claimed when Docker mode runs."
    p_bot.font.name = FONT_FAMILY
    p_bot.font.size = Pt(8.5)
    p_bot.font.bold = True
    p_bot.font.color.rgb = AMBER

    set_speaker_notes(
        slide,
        "Slide 9 outlines our technology stack with complete technical honesty. "
        "Our core engines—policy enforcement, audit chaining, event logging, and prompt heuristics—are completely modular Python. "
        "We chose Flask for this build because it ran flawlessly without external internet dependencies in isolated test environments, "
        "and the architecture is completely decoupled so porting to FastAPI requires only rewriting app.py. "
        "In our Docker topology, all zone containers drop all Linux capabilities and run with read-only root filesystems. "
        "For AI models, we support both a deterministic local mock—which simulates benign prompts, refusals, and canary leaks—and "
        "live Google Gemini API calls. API keys stay exclusively on the gateway; they are never logged or exposed to zone containers."
    )


def build_slide_10(prs):
    """Slide 10 — Target Users and Real-World Applications (Enhanced Vertical Balance)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "09 // MARKET & TARGET PERSONAS",
        "Target Users & Real-World AI Security Applications",
        "Empowering security engineers, AI development teams, and compliance officers with controlled testing infrastructure."
    )

    card_w = Inches(2.68)
    card_h = Inches(4.7)
    card_top = Inches(1.85)

    personas = [
        ("AI RED TEAMS", RED, "Adversarial AI Testers", [
            ("Core Challenge", "Need to test aggressive jailbreaks, recursive prompt injections, and autonomous agent exploits safely."),
            ("SafeArena Value", "Blast-proof isolated sandbox where payloads cannot escape into companion tools or corporate assets."),
            ("Primary Use Case", "Automated red-teaming, prompt injection fuzzing, and model guardrail stress-testing.")
        ], "Outcome: Zero Staging Escapes"),
        ("APPSEC & DEVSECOPS", BLUE, "Enterprise Security Teams", [
            ("Core Challenge", "Ensuring multi-tenant LLM applications enforce strict boundaries and do not leak internal state."),
            ("SafeArena Value", "Automated security gate in CI/CD that validates default-deny policies before production release."),
            ("Primary Use Case", "Pre-deployment policy validation for multi-agent systems and enterprise RAG pipelines.")
        ], "Outcome: Automated CI/CD Gates"),
        ("AI GRC & AUDITORS", GREEN, "Governance & Compliance", [
            ("Core Challenge", "Satisfying emerging AI safety regulations (EU AI Act, NIST AI RMF, ISO 42001) with verifiable proof."),
            ("SafeArena Value", "Tamper-evident SHA-256 audit ledger proves exactly what prompts were tested, allowed, or blocked."),
            ("Primary Use Case", "Evidentiary documentation for third-party security audits and regulatory compliance filings.")
        ], "Outcome: Non-Repudiable Evidence"),
        ("ACADEMIC & RANGES", PURPLE, "Education & Training", [
            ("Core Challenge", "Teaching AI adversarial security and prompt injection defense in a safe, repeatable laboratory."),
            ("SafeArena Value", "Self-contained environment that students cannot break out of; immediate visual feedback on attack outcomes."),
            ("Primary Use Case", "Hands-on student AI capture-the-flag (CTF) challenges and defensive training.")
        ], "Outcome: Safe Student CTF Lab")
    ]

    for i, (tag, col, title, bullets, outcome) in enumerate(personas):
        left = Inches(0.8) + i * (card_w + Inches(0.33))
        add_card(slide, left, card_top, card_w, card_h, border=col, border_width=1.5)
        add_pill(slide, left + Inches(0.15), card_top + Inches(0.2), card_w - Inches(0.3), Inches(0.26), tag, col, BG_COLOR if col != RED and col != PURPLE and col != BLUE else TEXT_WHITE, font_size=8.5, bold=True)
        
        t = slide.shapes.add_textbox(left + Inches(0.12), card_top + Inches(0.55), card_w - Inches(0.24), Inches(3.2))
        tf = t.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_FAMILY
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(8)

        for label, text in bullets:
            pb = tf.add_paragraph()
            run1 = pb.add_run()
            run1.text = f"{label}:\n"
            run1.font.bold = True
            run1.font.color.rgb = col
            run1.font.size = Pt(8.5)

            run2 = pb.add_run()
            run2.text = text
            run2.font.bold = False
            run2.font.color.rgb = TEXT_MUTED
            run2.font.size = Pt(8)
            pb.space_after = Pt(6)

        # Bottom Outcome Pill
        add_pill(slide, left + Inches(0.15), card_top + Inches(4.2), card_w - Inches(0.3), Inches(0.32), outcome, CARD_HOVER, col, font_size=8, bold=True)

    set_speaker_notes(
        slide,
        "Who needs SafeArena today? We identified four primary stakeholder groups. "
        "First, AI Red Teams who need a blast-proof environment to run aggressive exploits without risking enterprise assets. "
        "Second, AppSec and DevSecOps engineers validating LLM guardrails in CI/CD pipelines before shipping models to production. "
        "Third, AI Governance, Risk, and Compliance officers who need non-repudiable audit logs to satisfy the EU AI Act "
        "and NIST AI Risk Management Framework. "
        "Fourth, universities and cyber ranges training the next generation of AI security defenders. "
        "SafeArena gives each of these personas a controlled, repeatable, and mathematically verifiable testing ground."
    )


def build_slide_11(prs):
    """Slide 11 — Innovation, Feasibility, and Expected Impact (Enhanced Vertical Balance)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)
    add_header(
        slide,
        "10 // INNOVATION & ROADMAP",
        "Measured Innovation & Phased Engineering Roadmap",
        "A pragmatic development roadmap progressing from our verified prototype to enterprise-grade trust infrastructure."
    )

    card_w = Inches(2.68)
    card_h = Inches(4.7)
    card_top = Inches(1.85)

    phases = [
        ("PHASE 1", GREEN, "Core Prototype", "100% COMPLETED", [
            ("Policy Engine", "Framework-decoupled policy engine with strict default-deny enforcement."),
            ("SHA-256 Ledger", "Hash-chained JSONL audit ledger with _head.json checkpointing."),
            ("Event Storage", "SQLite persistent event store with multi-filter indexing."),
            ("Operator Console", "Zero-dependency web console with 103 unit and integration tests passing.")
        ], "Status: Production-Grade PoC"),
        ("PHASE 2", CYAN, "Container Isolation", "DOCKER READY", [
            ("Network Subnets", "Multi-container Docker Compose with internal bridge networks (red, blue, llm)."),
            ("Container Security", "Hardened containers: read-only root, dropped caps, no-new-privileges."),
            ("Isolation Script", "Host-side automated connectivity probe script (docker_isolation_test.py)."),
            ("Mode Detection", "Local simulation vs Docker runtime indicator on dashboard.")
        ], "Status: Container Verified"),
        ("PHASE 3", AMBER, "Cryptographic Identity", "NEXT MILESTONE", [
            ("mTLS / Signed JWTs", "Mutual TLS or signed JWT tokens for cryptographic zone attestation."),
            ("Identity Provenance", "Eliminate caller-asserted identity; enforce cryptographic provenance per zone."),
            ("Dynamic DSL", "Dynamic YAML policy DSL with hot-reloading rules."),
            ("Heuristic Models", "Advanced semantic prompt-injection classifiers.")
        ], "Status: Next Sprint"),
        ("PHASE 4", PURPLE, "Enterprise Trust Scale", "FUTURE VISION", [
            ("Hardware Keys", "Hardware Security Module (HSM) / AWS KMS integration for audit log signing."),
            ("WORM Storage", "Write-Once-Read-Many cloud storage integration (AWS S3 Object Lock)."),
            ("Transparency Log", "Public transparency log publishing for non-repudiable verification."),
            ("Multi-Node Swarms", "Distributed multi-node testbed for multi-agent swarm evaluations.")
        ], "Status: Enterprise Scale")
    ]

    for i, (phase_tag, col, title, status, bullets, footer_status) in enumerate(phases):
        left = Inches(0.8) + i * (card_w + Inches(0.33))
        add_card(slide, left, card_top, card_w, card_h, border=col, border_width=1.5)
        add_pill(slide, left + Inches(0.15), card_top + Inches(0.2), Inches(1.1), Inches(0.26), phase_tag, col, BG_COLOR if col != PURPLE and col != CYAN else TEXT_WHITE, font_size=8.5, bold=True)
        add_pill(slide, left + Inches(1.35), card_top + Inches(0.2), Inches(1.18), Inches(0.26), status, CARD_BG, col, font_size=7.5, bold=True)
        
        t = slide.shapes.add_textbox(left + Inches(0.12), card_top + Inches(0.55), card_w - Inches(0.24), Inches(3.2))
        tf = t.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_FAMILY
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(8)

        for label, text in bullets:
            pb = tf.add_paragraph()
            run1 = pb.add_run()
            run1.text = f"{label}: "
            run1.font.bold = True
            run1.font.color.rgb = col
            run1.font.size = Pt(8.5)

            run2 = pb.add_run()
            run2.text = text
            run2.font.bold = False
            run2.font.color.rgb = TEXT_MUTED
            run2.font.size = Pt(8)
            pb.space_after = Pt(5)

        # Bottom Milestone Pill
        add_pill(slide, left + Inches(0.15), card_top + Inches(4.2), card_w - Inches(0.3), Inches(0.32), footer_status, CARD_HOVER, col, font_size=8, bold=True)

    set_speaker_notes(
        slide,
        "Here is our engineering roadmap. We built SafeArena with a clear, realistic trajectory. "
        "Phase 1 is complete and fully tested: a functional core prototype with default-deny policy, SHA-256 audit chaining, "
        "SQLite event storage, and a live web console, verified by 103 automated tests. "
        "Phase 2 is Docker-ready: multi-container composition with internal bridge networks and automated probe testing. "
        "Phase 3 introduces cryptographic identity: replacing caller-asserted zone headers with mutual TLS or signed JWTs, "
        "ensuring that zone identities cannot be spoofed. "
        "Phase 4 scales this to enterprise production: integrating Hardware Security Modules for cryptographic key signing, "
        "WORM cloud storage for immutable audit persistence, and multi-node testing for autonomous agent swarms."
    )


def build_slide_12(prs):
    """Slide 12 — Closing: Isolate. Control. Detect. Prove."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide)

    # Top Brand Badges
    add_pill(slide, Inches(0.8), Inches(0.6), Inches(2.2), Inches(0.32), "SAFEARENA CONCLUSION", CYAN, BG_COLOR, font_size=9.5, bold=True)
    add_pill(slide, Inches(3.1), Inches(0.6), Inches(2.4), Inches(0.32), "HACK IN HILLS '26", CARD_BG, CYAN, font_size=9.5, bold=True)

    # Core Closing Quotation Card (Centerpiece)
    add_card(slide, Inches(0.8), Inches(1.15), Inches(11.73), Inches(2.2), bg=CARD_BG, border=CYAN, border_width=2)
    q_box = slide.shapes.add_textbox(Inches(1.1), Inches(1.35), Inches(11.1), Inches(1.8))
    tf_q = q_box.text_frame
    tf_q.word_wrap = True

    pq1 = tf_q.paragraphs[0]
    pq1.text = "“Test AI systems in a controlled environment."
    pq1.font.name = FONT_FAMILY
    pq1.font.size = Pt(26)
    pq1.font.bold = True
    pq1.font.color.rgb = TEXT_WHITE
    pq1.space_after = Pt(4)

    pq2 = tf_q.add_paragraph()
    pq2.text = "Enforce the rules. Record what happens. Verify the evidence.”"
    pq2.font.name = FONT_FAMILY
    pq2.font.size = Pt(26)
    pq2.font.bold = True
    pq2.font.color.rgb = CYAN

    # 4 Summary Pillar Cards
    card_w = Inches(2.78)
    card_h = Inches(1.8)
    card_top = Inches(3.55)
    gap = Inches(0.2)

    pillars = [
        ("ISOLATE", BLUE, "Segregated Sandboxes", "Red, Blue, and LLM zones run in separate network subnets with dropped capabilities."),
        ("CONTROL", CYAN, "Default-Deny Gateway", "Every request is evaluated; unauthorized lateral movement blocked with 403 Forbidden."),
        ("DETECT", AMBER, "Real-Time Telemetry", "Severity-rated events and injection heuristics committed to SQLite and operator UI."),
        ("PROVE", GREEN, "SHA-256 Audit Ledger", "Mathematical proof of integrity; verified against 7 distinct tamper scenarios.")
    ]

    for i, (name, col, subtitle, desc) in enumerate(pillars):
        left = Inches(0.8) + i * (card_w + gap)
        add_card(slide, left, card_top, card_w, card_h, bg=CARD_HOVER, border=col, border_width=1.5)
        add_pill(slide, left + Inches(0.15), card_top + Inches(0.18), Inches(1.2), Inches(0.24), name, col, BG_COLOR if col != BLUE else TEXT_WHITE, font_size=8.5, bold=True)
        
        tb = slide.shapes.add_textbox(left + Inches(0.15), card_top + Inches(0.48), card_w - Inches(0.3), card_h - Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = subtitle
        p.font.name = FONT_FAMILY
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(4)

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_FAMILY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_WHITE

    # Bottom Team Credit & Call-to-Action Bar
    add_card(slide, Inches(0.8), Inches(5.55), Inches(11.73), Inches(1.3), bg=CARD_HOVER, border=CARD_BORDER)
    cta_box = slide.shapes.add_textbox(Inches(1.1), Inches(5.68), Inches(11.1), Inches(1.05))
    tf_cta = cta_box.text_frame
    tf_cta.word_wrap = True

    pcta1 = tf_cta.paragraphs[0]
    pcta1.text = "SafeArena  ·  Created by VSV The Tech Giants  ·  Hack in Hills '26"
    pcta1.font.name = FONT_FAMILY
    pcta1.font.size = Pt(12)
    pcta1.font.bold = True
    pcta1.font.color.rgb = CYAN
    pcta1.space_after = Pt(4)

    pcta2 = tf_cta.add_paragraph()
    pcta2.text = "Working Codebase & Automated Test Suite Ready for Evaluation  ·  Open Architecture  ·  Python 3.12 / Docker"
    pcta2.font.name = FONT_FAMILY
    pcta2.font.size = Pt(10)
    pcta2.font.color.rgb = TEXT_WHITE
    pcta2.space_after = Pt(4)

    pcta3 = tf_cta.add_paragraph()
    pcta3.text = "Thank you judges! We welcome your questions."
    pcta3.font.name = FONT_FAMILY
    pcta3.font.size = Pt(9.5)
    pcta3.font.bold = True
    pcta3.font.color.rgb = GREEN

    set_speaker_notes(
        slide,
        "To conclude: SafeArena provides the missing foundation for trustworthy adversarial AI testing. "
        "Test AI systems in a controlled environment. Enforce the rules. Record what happens. Verify the evidence. "
        "We are VSV The Tech Giants, and SafeArena is built, tested, and ready for your evaluation. "
        "Thank you so much, and we look forward to your questions."
    )


# ==============================================================================
# MAIN GENERATOR FUNCTION
# ==============================================================================

def main():
    print("Initializing PowerPoint presentation...")
    prs = pptx.Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    print("Building Slide 1: Hero...")
    build_slide_1(prs)

    print("Building Slide 2: The Problem...")
    build_slide_2(prs)

    print("Building Slide 3: Why Existing Approaches Leave a Gap...")
    build_slide_3(prs)

    print("Building Slide 4: Our Solution...")
    build_slide_4(prs)

    print("Building Slide 5: System Architecture...")
    build_slide_5(prs)

    print("Building Slide 6: How a Request Works...")
    build_slide_6(prs)

    print("Building Slide 7: Security Engineering and Trust...")
    build_slide_7(prs)

    print("Building Slide 8: Product Experience and Demonstration...")
    build_slide_8(prs)

    print("Building Slide 9: Technology Stack and Implementation...")
    build_slide_9(prs)

    print("Building Slide 10: Target Users and Real-World Applications...")
    build_slide_10(prs)

    print("Building Slide 11: Innovation, Feasibility, and Roadmap...")
    build_slide_11(prs)

    print("Building Slide 12: Closing...")
    build_slide_12(prs)

    output_path = Path(r"C:\Users\lenovo\.gemini\antigravity\scratch\SafeArena\SafeArena_Premium_Pitch_Deck.pptx")
    prs.save(str(output_path))
    print(f"Presentation generated successfully with {len(prs.slides)} slides at: {output_path}")


if __name__ == "__main__":
    main()
