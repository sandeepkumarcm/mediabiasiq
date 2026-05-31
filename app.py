import streamlit as st
import sys
import os
import json
import time
import re
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import plotly.graph_objects as go

# ── Path setup ────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Page config MUST be first ─────────────────────────────
st.set_page_config(
    page_title="MediaBiasIQ — News Bias Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Imports from project ──────────────────────────────────
from scraper.article_scraper import scrape_article
from model.bias_classifier import classify_bias
from model.extra_classifier import detect_extra_bias
from explainability.shap_explainer import get_biased_sentences, get_plain_english_explanation
from rewriter.llm_rewriter import rewrite_neutral, DISCLAIMER
from diff.diff_generator import generate_diff, get_diff_stats, get_word_diff
from credibility.source_checker import check_source_credibility, get_credibility_verdict, get_all_sources
from comparison.article_comparator import compare_articles
from dashboard.charts import (
    bias_score_chart, bias_distribution_pie, load_confusion_matrix,
    load_metrics, metrics_table, bias_gauge_chart, session_summary_chart,
    BIAS_COLORS, SEVERITY_COLORS
)

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif !important; }
.stApp {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
    min-height: 100vh;
}
.main-header {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 0 40px rgba(59,130,246,0.1);
}
.main-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3B82F6, #8B5CF6, #EC4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
}
.main-subtitle { color: #94A3B8; font-size: 1.1rem; font-weight: 400; }
.badge-left {
    background: linear-gradient(135deg, #1D4ED8, #3B82F6);
    color: white; padding: 8px 20px; border-radius: 50px;
    font-weight: 700; font-size: 1.1rem; display: inline-block;
    box-shadow: 0 0 20px rgba(59,130,246,0.4);
    animation: badgePop 0.5s ease;
}
.badge-center {
    background: linear-gradient(135deg, #15803D, #22C55E);
    color: white; padding: 8px 20px; border-radius: 50px;
    font-weight: 700; font-size: 1.1rem; display: inline-block;
    box-shadow: 0 0 20px rgba(34,197,94,0.4);
    animation: badgePop 0.5s ease;
}
.badge-right {
    background: linear-gradient(135deg, #B91C1C, #EF4444);
    color: white; padding: 8px 20px; border-radius: 50px;
    font-weight: 700; font-size: 1.1rem; display: inline-block;
    box-shadow: 0 0 20px rgba(239,68,68,0.4);
    animation: badgePop 0.5s ease;
}
.glass-card {
    background: rgba(30,41,59,0.8);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 20px; margin: 8px 0;
    backdrop-filter: blur(10px); transition: all 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(59,130,246,0.4);
    box-shadow: 0 0 20px rgba(59,130,246,0.1);
    transform: translateY(-2px);
}
.sentence-high {
    border-left: 4px solid #EF4444; background: rgba(239,68,68,0.1);
    padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;
    animation: slideIn 0.4s ease;
}
.sentence-medium {
    border-left: 4px solid #F97316; background: rgba(249,115,22,0.1);
    padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;
    animation: slideIn 0.5s ease;
}
.sentence-low {
    border-left: 4px solid #EAB308; background: rgba(234,179,8,0.1);
    padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;
    animation: slideIn 0.6s ease;
}
.diff-removed {
    background: rgba(239,68,68,0.15); border-left: 3px solid #EF4444;
    padding: 8px 12px; margin: 2px 0; border-radius: 0 4px 4px 0;
    color: #FCA5A5; font-family: monospace;
}
.diff-added {
    background: rgba(34,197,94,0.15); border-left: 3px solid #22C55E;
    padding: 8px 12px; margin: 2px 0; border-radius: 0 4px 4px 0;
    color: #86EFAC; font-family: monospace;
}
.word-removed {
    background: rgba(239,68,68,0.2); color: #FCA5A5;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 4px 10px; border-radius: 20px;
    font-size: 0.85rem; margin: 3px; display: inline-block;
}
.word-added {
    background: rgba(34,197,94,0.2); color: #86EFAC;
    border: 1px solid rgba(34,197,94,0.4);
    padding: 4px 10px; border-radius: 20px;
    font-size: 0.85rem; margin: 3px; display: inline-block;
}
.bias-warning {
    background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(185,28,28,0.2));
    border: 1px solid rgba(239,68,68,0.5); border-radius: 8px;
    padding: 12px 20px; margin: 12px 0; animation: pulse 2s infinite;
}
.fear-warning {
    background: linear-gradient(135deg, rgba(249,115,22,0.2), rgba(194,65,12,0.2));
    border: 1px solid rgba(249,115,22,0.5); border-radius: 8px;
    padding: 12px 20px; margin: 12px 0;
}
.neutral-success {
    background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(21,128,61,0.2));
    border: 1px solid rgba(34,197,94,0.5); border-radius: 8px;
    padding: 12px 20px; margin: 12px 0;
}
.perf-bar {
    background: rgba(15,23,42,0.9); border: 1px solid rgba(59,130,246,0.3);
    border-radius: 8px; padding: 10px 16px; margin: 8px 0;
    font-size: 0.85rem; color: #94A3B8;
}
.before-after-card {
    background: rgba(30,41,59,0.9); border-radius: 12px;
    padding: 20px; margin: 12px 0;
    border: 1px solid rgba(255,255,255,0.1);
}
.lang-warning {
    background: rgba(234,179,8,0.15); border: 1px solid rgba(234,179,8,0.4);
    border-radius: 8px; padding: 10px 16px; margin: 8px 0;
    color: #FDE68A; font-size: 0.9rem;
}
.calibration-card {
    background: rgba(30,41,59,0.9); border: 1px solid rgba(139,92,246,0.3);
    border-radius: 10px; padding: 16px; margin: 8px 0;
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.7; } }
@keyframes fadeInDown { from { opacity:0; transform:translateY(-20px); } to { opacity:1; transform:translateY(0); } }
@keyframes badgePop { 0% { transform:scale(0); opacity:0; } 70% { transform:scale(1.1); } 100% { transform:scale(1); opacity:1; } }
@keyframes slideIn { from { opacity:0; transform:translateX(-20px); } to { opacity:1; transform:translateX(0); } }
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,23,42,0.8); border-radius: 12px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; color: #94A3B8; font-weight: 500; padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.2) !important;
    color: #3B82F6 !important; font-weight: 600;
}
.stButton > button {
    background: linear-gradient(135deg, #3B82F6, #8B5CF6);
    color: white; border: none; border-radius: 8px;
    font-weight: 600; padding: 8px 24px; transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(59,130,246,0.4);
}
.stTextInput > div > div > input {
    background: rgba(30,41,59,0.8) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #F1F5F9 !important; border-radius: 8px !important;
}
div[data-testid="metric-container"] {
    background: rgba(30,41,59,0.6);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 12px;
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
@media (max-width: 768px) {
    .main-title { font-size: 1.8rem; }
    .glass-card { padding: 12px; }
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────
defaults = {
    "history": [], "current_article": None, "current_bias": None,
    "current_sentences": None, "current_rewrite": None,
    "current_extra": None, "current_credibility": None,
    "url_cache": {}, "comparison_result": None,
    "last_analysis_time": 0, "analysis_times": {},
    "rewrite_bias": None, "show_confetti": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Example URLs ──────────────────────────────────────────
EXAMPLE_URLS = {
    "fox": "https://www.foxnews.com/politics/trump-threatened-blow-up-oman-why-tiny-gulf-kingdom-caught-between-dc-iran",
    "bbc": "https://www.bbc.com/news/world-asia-india-37346570",
    "the hindu": "https://www.thehindu.com/news/national/karnataka/karnataka-cm-news-leadership-change-live-updates-dk-shivakumar-siddaramaiah-congress-meet-rajya-sabha-seat-may-28-2026/article71029253.ece"
}

# ── Helper Functions ──────────────────────────────────────
def get_badge_html(label: str, size: str = "normal") -> str:
    font_size = "1.1rem" if size == "normal" else "0.85rem"
    padding = "8px 20px" if size == "normal" else "4px 12px"
    label_lower = str(label).lower()
    if label_lower == "left":
        return f'<span class="badge-left" style="font-size:{font_size};padding:{padding}">⬅️ LEFT</span>'
    elif label_lower == "center":
        return f'<span class="badge-center" style="font-size:{font_size};padding:{padding}">⚖️ CENTER</span>'
    elif label_lower == "right":
        return f'<span class="badge-right" style="font-size:{font_size};padding:{padding}">➡️ RIGHT</span>'
    else:
        return f'<span style="background:#475569;color:white;padding:{padding};border-radius:50px;font-weight:700;font-size:{font_size}">{label}</span>'

def get_trust_score(bias_confidence, fear_score, clickbait_score, found_in_db):
    trust = 100
    trust -= (bias_confidence - 50) * 0.4
    trust -= fear_score * 0.3
    trust -= clickbait_score * 0.2
    if not found_in_db:
        trust -= 10
    return max(0, min(100, int(trust)))

def get_reading_diversity_score(history):
    if len(history) < 2:
        return 50
    counts = Counter([h.get("label", "UNKNOWN") for h in history])
    total = len(history)
    left_pct = counts.get("LEFT", 0) / total
    center_pct = counts.get("CENTER", 0) / total
    right_pct = counts.get("RIGHT", 0) / total
    ideal = 1/3
    deviation = abs(left_pct - ideal) + abs(center_pct - ideal) + abs(right_pct - ideal)
    return max(0, min(100, int((1 - deviation / 2) * 100)))

def get_complexity_score(text):
    if not text:
        return {"score": 50, "level": "Unknown", "avg_words_per_sentence": 0}
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 0]
    if not sentences:
        return {"score": 50, "level": "Unknown", "avg_words_per_sentence": 0}
    avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
    words = text.split()
    avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
    complexity = (avg_words * 2) + (avg_word_length * 5)
    if complexity < 30: level = "Simple"
    elif complexity < 50: level = "Moderate"
    elif complexity < 70: level = "Advanced"
    else: level = "Graduate"
    return {"score": min(100, int(complexity)), "level": level, "avg_words_per_sentence": round(avg_words, 1)}

# ── NEW: Language Detection ───────────────────────────────
def detect_language(text: str) -> dict:
    if not text or len(text) < 50:
        return {"language": "unknown", "is_english": True, "confidence": 0}
    sample = text[:500]
    ascii_count = sum(1 for c in sample if ord(c) < 128)
    ascii_ratio = ascii_count / len(sample)
    is_english = ascii_ratio > 0.85
    devanagari = sum(1 for c in sample if '\u0900' <= c <= '\u097F')
    tamil = sum(1 for c in sample if '\u0B80' <= c <= '\u0BFF')
    arabic = sum(1 for c in sample if '\u0600' <= c <= '\u06FF')
    if devanagari > 10:
        return {"language": "Hindi", "is_english": False, "confidence": min(100, devanagari * 5)}
    elif tamil > 10:
        return {"language": "Tamil", "is_english": False, "confidence": min(100, tamil * 5)}
    elif arabic > 10:
        return {"language": "Arabic", "is_english": False, "confidence": min(100, arabic * 5)}
    return {"language": "English", "is_english": True, "confidence": int(ascii_ratio * 100)}

# ── NEW: Source Bias History ──────────────────────────────
def get_source_bias_history(history: list) -> dict:
    source_data = {}
    for h in history:
        try:
            domain = urlparse(h.get("url", "")).netloc.replace("www.", "")
        except:
            domain = "unknown"
        if not domain:
            continue
        if domain not in source_data:
            source_data[domain] = {"labels": [], "confidences": []}
        source_data[domain]["labels"].append(h.get("label", "UNKNOWN"))
        source_data[domain]["confidences"].append(h.get("confidence", 0))
    result = {}
    for domain, data in source_data.items():
        avg_conf = sum(data["confidences"]) / len(data["confidences"])
        label_counts = Counter(data["labels"])
        most_common_label = label_counts.most_common(1)[0][0]
        result[domain] = {
            "avg_confidence": round(avg_conf, 1),
            "dominant_label": most_common_label,
            "article_count": len(data["labels"])
        }
    return result

def create_source_bias_history_chart(source_data: dict) -> go.Figure:
    if not source_data:
        fig = go.Figure()
        fig.add_annotation(text="Analyze more articles to see source trends",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=14, color="#94A3B8"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250)
        return fig
    domains = list(source_data.keys())
    avg_confs = [source_data[d]["avg_confidence"] for d in domains]
    labels = [source_data[d]["dominant_label"] for d in domains]
    counts = [source_data[d]["article_count"] for d in domains]
    colors = [BIAS_COLORS.get(l, "#94A3B8") for l in labels]
    fig = go.Figure(go.Bar(
        x=domains, y=avg_confs, marker_color=colors,
        text=[f"{l}<br>{c:.0f}% avg<br>{n} articles" for l, c, n in zip(labels, avg_confs, counts)],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Avg Bias: %{y:.1f}%<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="📰 Source Bias History", font=dict(size=16, color="#F1F5F9"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.6)",
        font=dict(color="#CBD5E1"), height=300, showlegend=False,
        yaxis=dict(range=[0, 120], gridcolor="rgba(255,255,255,0.05)"),
        margin=dict(t=50, b=60, l=40, r=20)
    )
    return fig

def create_bias_dna_chart(bias_confidence, fear_score, clickbait_score, credibility_confidence, complexity_score):
    cred_map = {"HIGH": 90, "MEDIUM": 60, "LOW": 30}
    cred_value = cred_map.get(credibility_confidence, 50)
    categories = ["Political Bias", "Fear Level", "Clickbait", "Source Risk", "Language Complexity"]
    values = [bias_confidence, fear_score, clickbait_score, 100 - cred_value, complexity_score]
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=categories_closed, fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3B82F6", width=2), name="Article Profile"
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15,23,42,0.8)",
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(color="#94A3B8", size=10), gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(tickfont=dict(color="#CBD5E1", size=11), gridcolor="rgba(255,255,255,0.1)")
        ),
        title=dict(text="🧬 Article Bias DNA", font=dict(size=16, color="#F1F5F9"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)", height=350,
        margin=dict(t=60, b=20, l=40, r=40), showlegend=False
    )
    return fig

def create_sentence_heatmap(text, biased_sentences):
    if not text or not biased_sentences:
        return text or ""
    sentence_scores = {}
    for s in biased_sentences:
        key = s.get("sentence", "")[:50]
        sentence_scores[key] = (s.get("bias_score", 0), s.get("direction", "CENTER"))
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    html_parts = []
    for sentence in sentences[:20]:
        matched = False
        for key, (score, direction) in sentence_scores.items():
            if sentence[:50] in key or key in sentence[:50]:
                if direction == "LEFT":
                    color = f"rgba(59,130,246,{score/100:.2f})"
                    border = "#3B82F6"
                elif direction == "RIGHT":
                    color = f"rgba(239,68,68,{score/100:.2f})"
                    border = "#EF4444"
                else:
                    color = "rgba(34,197,94,0.1)"
                    border = "#22C55E"
                html_parts.append(
                    f'<span style="background:{color};border-bottom:2px solid {border};'
                    f'padding:2px 4px;border-radius:3px;margin:1px;display:inline;" '
                    f'title="Bias: {score:.1f}% | {direction}">{sentence}</span> '
                )
                matched = True
                break
        if not matched:
            html_parts.append(f'<span style="color:#CBD5E1;">{sentence}</span> ')
    return "".join(html_parts)

def generate_report_json(article, bias, extra, sentences, credibility):
    report = {
        "report_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "article": {"title": article.get("title",""), "url": article.get("url",""), "word_count": article.get("word_count",0)},
        "bias_analysis": {"label": bias.get("label",""), "confidence": bias.get("confidence",0), "scores": bias.get("scores",{})},
        "extra_signals": {"fear_detected": extra.get("fear_detected",False), "fear_score": extra.get("fear_score",0),
                          "clickbait_detected": extra.get("clickbait_detected",False), "clickbait_score": extra.get("clickbait_score",0)},
        "top_biased_sentences": [{"sentence": s.get("sentence",""), "score": s.get("bias_score",0),
                                   "severity": s.get("severity",""), "direction": s.get("direction","")} for s in sentences[:3]],
        "source_credibility": {"domain": credibility.get("domain",""), "allsides_rating": credibility.get("allsides_rating",""),
                               "found_in_database": credibility.get("found_in_database",False)}
    }
    return json.dumps(report, indent=2)

# ── NEW: PDF Export ───────────────────────────────────────
def generate_pdf_report(article, bias, extra, sentences, credibility):
    try:
        from fpdf import FPDF

        # ── Helper to clean text for PDF ─────────────────
        def clean(text, max_len=None):
            if not text:
                return ""
            # Remove non-latin characters that fpdf2 cannot handle
            cleaned = text.encode("latin-1", "ignore").decode("latin-1")
            if max_len:
                cleaned = cleaned[:max_len]
            return cleaned

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header background
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(0, 0, 210, 40, 'F')

        # Title
        pdf.set_text_color(59, 130, 246)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_y(12)
        pdf.cell(0, 10, "MediaBiasIQ", align="C", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 6, "News Bias Detection & Analysis Report", align="C", ln=True)
        pdf.set_y(48)

        # Article Info
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Article Information", ln=True)
        pdf.set_draw_color(59, 130, 246)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 41, 59)
        title = clean(article.get("title", "Unknown"), 80)
        pdf.multi_cell(0, 7, f"Title: {title}")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)
        url = clean(article.get("url", ""), 80)
        pdf.cell(0, 6, f"URL: {url}", ln=True)
        pdf.cell(0, 6, f"Word Count: {article.get('word_count', 0)} words", ln=True)
        pdf.cell(0, 6, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)

        # Bias Analysis
        label = bias.get("label", "UNKNOWN")
        confidence = bias.get("confidence", 0)
        scores = bias.get("scores", {})

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Bias Analysis", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        if label == "LEFT":
            pdf.set_text_color(59, 130, 246)
        elif label == "RIGHT":
            pdf.set_text_color(239, 68, 68)
        else:
            pdf.set_text_color(34, 197, 94)

        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Verdict: {label}  ({confidence:.1f}% confidence)", ln=True)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6,
            f"LEFT: {scores.get('LEFT',0):.1f}%  |  "
            f"CENTER: {scores.get('CENTER',0):.1f}%  |  "
            f"RIGHT: {scores.get('RIGHT',0):.1f}%", ln=True)
        pdf.ln(4)

        # Extra Signals
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Extra Bias Signals", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)
        fear_status = f"DETECTED ({extra.get('fear_score',0):.0f}%)" if extra.get("fear_detected") else f"Not Detected ({extra.get('fear_score',0):.0f}%)"
        click_status = f"DETECTED ({extra.get('clickbait_score',0):.0f}%)" if extra.get("clickbait_detected") else f"Not Detected ({extra.get('clickbait_score',0):.0f}%)"
        pdf.cell(0, 6, f"Fear-Mongering: {fear_status}", ln=True)
        pdf.cell(0, 6, f"Clickbait: {click_status}", ln=True)
        pdf.ln(4)

        # Source Credibility
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Source Credibility", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 6, f"Domain: {clean(credibility.get('domain', 'Unknown'))}", ln=True)
        allsides = credibility.get('allsides_rating')
        pdf.cell(0, 6, f"AllSides Rating: {allsides if allsides else 'Not in database'}", ln=True)
        pdf.ln(4)

        # Top Biased Sentences
        if sentences:
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 8, "Top Biased Sentences", ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            for i, s in enumerate(sentences[:3], 1):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.cell(0, 6,
                    f"#{i} - {s.get('severity','LOW')} severity - "
                    f"{s.get('bias_score',0):.1f}% - {s.get('direction','')}",
                    ln=True)
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(71, 85, 105)
                sentence_text = clean(s.get("sentence",""), 120)
                pdf.multi_cell(0, 5, f'"{sentence_text}..."')
                pdf.ln(2)

        # Footer
        pdf.set_y(-20)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5,
            "Generated by MediaBiasIQ - DistilBERT | SHAP | GPT-3.5 | 85.06% accuracy on AllSides 17K dataset",
            align="C", ln=True)

        return bytes(pdf.output())

    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None

# ── Analysis Runner ───────────────────────────────────────
def run_analysis(url):
    now = time.time()
    times = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    try:
        t0 = time.time()
        status_text.markdown("🕷️ **Step 1/4** — Scraping article...")
        progress_bar.progress(10)
        article = scrape_article(url)
        times["scraping"] = round(time.time() - t0, 1)
        if article.get("error"):
            st.error(f"❌ {article['error']}")
            progress_bar.empty(); status_text.empty()
            return False

        # Language detection
        lang_result = detect_language(article.get("text", ""))
        if not lang_result["is_english"]:
            st.markdown(f'<div class="lang-warning">⚠️ This article appears to be in <strong>{lang_result["language"]}</strong>. Bias detection works best on English articles. Results may vary.</div>', unsafe_allow_html=True)

        t1 = time.time()
        status_text.markdown("🤖 **Step 2/4** — Classifying political bias...")
        progress_bar.progress(30)
        bias_result = classify_bias(article["text"])
        times["classification"] = round(time.time() - t1, 1)
        if bias_result.get("error"):
            st.warning(f"⚠️ {bias_result['error']}")

        t2 = time.time()
        status_text.markdown("🔍 **Step 3/4** — Finding biased sentences...")
        progress_bar.progress(60)
        sentences = get_biased_sentences(article["text"], top_n=5)
        times["shap"] = round(time.time() - t2, 1)

        status_text.markdown("📊 **Step 4/4** — Running extra analysis...")
        progress_bar.progress(85)
        extra = detect_extra_bias(article.get("title",""), article["text"])
        credibility = check_source_credibility(url)
        progress_bar.progress(100)

        st.session_state.current_article = article
        st.session_state.current_bias = bias_result
        st.session_state.current_sentences = sentences
        st.session_state.current_extra = extra
        st.session_state.current_credibility = credibility
        st.session_state.current_rewrite = None
        st.session_state.rewrite_bias = None
        st.session_state.analysis_times = times

        st.session_state.url_cache[url] = {
            "article": article, "bias": bias_result,
            "sentences": sentences, "extra": extra, "credibility": credibility
        }
        st.session_state.history.append({
            "url": url, "title": article.get("title","Unknown"),
            "label": bias_result.get("label","UNKNOWN"),
            "confidence": bias_result.get("confidence",0)
        })

        if bias_result.get("label") == "CENTER" and bias_result.get("confidence", 0) > 60:
            st.session_state.show_confetti = True

        total = round(time.time() - now, 1)
        times["total"] = total
        status_text.empty()
        progress_bar.empty()
        st.success(f"✅ Analysis complete in {total}s")
        st.markdown(f"""
        <div class="perf-bar">
            ⚡ Scraped: {times.get('scraping',0)}s &nbsp;|&nbsp;
            🤖 Classified: {times.get('classification',0)}s &nbsp;|&nbsp;
            🔍 SHAP: {times.get('shap',0)}s &nbsp;|&nbsp;
            📊 Total: {total}s
        </div>
        """, unsafe_allow_html=True)
        st.session_state.last_analysis_time = time.time()
        return True
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        progress_bar.empty(); status_text.empty()
        return False

# ── HEADER ────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">🔍 MediaBiasIQ</div>
    <div class="main-subtitle">AI-powered News Bias Detector • Explainable AI • GPT-3.5 Neutral Rewriter</div>
    <div style="margin-top:8px;color:#CBD5E1;font-size:1rem;">
        Detects <strong style="color:#3B82F6;">LEFT</strong> • 
        <strong style="color:#22C55E;">CENTER</strong> • 
        <strong style="color:#EF4444;">RIGHT</strong> political bias in any news article
    </div>
    <div style="margin-top:12px;color:#475569;font-size:0.85rem;">
        DistilBERT fine-tuned on Faith1712/Allsides_political_bias_proper (17,362 articles) &nbsp;•&nbsp; 
        <strong style="color:#22C55E;">85.06% accuracy</strong> &nbsp;•&nbsp; 
        GPT-3.5 Rewriter &nbsp;•&nbsp; SHAP Explainability
    </div>
</div>
""", unsafe_allow_html=True)

# ── Confetti for neutral article ──────────────────────────
if st.session_state.show_confetti:
    st.markdown("""
    <div class="neutral-success">
        🎉 <strong>Well Balanced Article!</strong> — This article shows neutral, factual reporting. Great reading choice!
    </div>
    """, unsafe_allow_html=True)
    st.session_state.show_confetti = False

# ── Stats Bar ─────────────────────────────────────────────
metrics_data = load_metrics()
all_sources = get_all_sources()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📰 Articles Analyzed", len(st.session_state.history))
with col2:
    st.metric("🗄️ Sources in Database", len(all_sources))
with col3:
    if metrics_data["found"]:
        acc = metrics_data["metrics"].get("overall_accuracy", 0) * 100
        st.metric("🤖 Model Accuracy", f"{acc:.2f}%")
    else:
        st.metric("🤖 Model Accuracy", "85.06%")
with col4:
    diversity = get_reading_diversity_score(st.session_state.history)
    st.metric("🎯 Reading Diversity", f"{diversity}/100")

st.divider()

# ── URL Input ─────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    url_input = st.text_input(
        "Enter article URL",
         placeholder="https://www.bbc.com/news/...",
         key="url_input",
         label_visibility="hidden"
   )
with col_btn:
    st.write("")
    st.write("")
    analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

# ── Example Buttons ───────────────────────────────────────
st.markdown("<div style='color:#64748B;font-size:0.8rem;margin-bottom:4px;'>⚡ Quick examples — click to analyze instantly:</div>", unsafe_allow_html=True)
ex_col1, ex_col2, ex_col3 = st.columns(3)
with ex_col1:
    if st.button("🦊 Fox News Example", use_container_width=True):
        if time.time() - st.session_state.last_analysis_time >= 2:
            run_analysis(EXAMPLE_URLS["fox"])
        st.rerun()
with ex_col2:
    if st.button("🌐 BBC Example", use_container_width=True):
        if time.time() - st.session_state.last_analysis_time >= 2:
            run_analysis(EXAMPLE_URLS["bbc"])
        st.rerun()
with ex_col3:
    if st.button("📰 The Hindu", use_container_width=True):
        if time.time() - st.session_state.last_analysis_time >= 2:
            run_analysis(EXAMPLE_URLS["ndtv"])
        st.rerun()

# ── Recent URLs ───────────────────────────────────────────
if st.session_state.history:
    recent_urls = list(dict.fromkeys([h["url"] for h in st.session_state.history[-5:]]))
    if recent_urls:
        with st.expander("🕐 Recent URLs"):
            for recent_url in reversed(recent_urls):
                short = recent_url[:80] + "..." if len(recent_url) > 80 else recent_url
                if st.button(f"↩️ {short}", key=f"recent_{hash(recent_url)}"):
                    st.session_state.url_input = recent_url
                    st.rerun()

# ── Analyze Button Logic ──────────────────────────────────
if analyze_btn:
    if not url_input:
        st.warning("⚠️ Please paste a news article URL first")
    elif time.time() - st.session_state.last_analysis_time < 2:
        st.warning("⏱️ Please wait a moment before analyzing again")
    elif url_input in st.session_state.url_cache:
        cached = st.session_state.url_cache[url_input]
        st.session_state.current_article = cached["article"]
        st.session_state.current_bias = cached["bias"]
        st.session_state.current_sentences = cached["sentences"]
        st.session_state.current_extra = cached["extra"]
        st.session_state.current_credibility = cached["credibility"]
        st.session_state.current_rewrite = None
        st.session_state.rewrite_bias = None
        st.success("⚡ Loaded from cache — instant results!")
    else:
        run_analysis(url_input)

# ── 6 TABS ────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎯 Bias Analysis", "🔦 Sentence Highlights",
    "✍️ Neutral Rewrite", "⚖️ Article Comparison",
    "📊 Evaluation Dashboard", "📋 Session History"
])

# ══════════════════════════════════════════════════════════
# TAB 1 — BIAS ANALYSIS
# ══════════════════════════════════════════════════════════
with tab1:
    if not st.session_state.current_article:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#475569;">
            <div style="font-size:4rem;margin-bottom:16px;">🔍</div>
            <div style="font-size:1.4rem;font-weight:600;color:#94A3B8;">Ready to analyze</div>
            <div style="font-size:1rem;margin-top:8px;">Paste any news article URL above and click Analyze</div>
            <div style="margin-top:16px;font-size:0.9rem;color:#334155;">Or click one of the example buttons above for instant demo</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        article = st.session_state.current_article
        bias = st.session_state.current_bias
        extra = st.session_state.current_extra
        credibility = st.session_state.current_credibility

        if bias and bias.get("confidence", 0) > 75:
            st.markdown('<div class="bias-warning">⚠️ <strong>High Bias Detected</strong> — This article shows strong political framing. Read with critical thinking.</div>', unsafe_allow_html=True)
        if extra and extra.get("fear_detected"):
            st.markdown('<div class="fear-warning">🚨 <strong>Fear-Mongering Detected</strong> — This article uses emotionally charged fear language.</div>', unsafe_allow_html=True)

        title_safe = article.get('title', 'Article').replace('<', '&lt;').replace('>', '&gt;')
        authors_html = '👤 ' + ', '.join(article.get('authors', [])) if article.get('authors') else ''
        date_html = '&nbsp;&nbsp;📅 ' + str(article.get('publish_date', ''))[:10] if article.get('publish_date') else ''
        domain_html = credibility.get('domain', '') if credibility else ''
        word_count = article.get('word_count', 0)
        st.markdown(
            f'<div class="glass-card">'
            f'<div style="font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:8px;">{title_safe}</div>'
            f'<div style="color:#94A3B8;font-size:0.9rem;">'
            f'{authors_html}{date_html}'
            f'&nbsp;&nbsp;📝 {word_count} words'
            f'&nbsp;&nbsp;⏱️ ~{max(1, word_count//200)} min read'
            f'&nbsp;&nbsp;🌐 {domain_html}'
            f'</div></div>',
            unsafe_allow_html=True
        )

        col_main, col_gauge = st.columns([3, 2])
        with col_main:
            if bias:
                label = bias.get("label", "UNKNOWN")
                confidence = bias.get("confidence", 0)
                scores = bias.get("scores", {})
                left_pct = scores.get("LEFT", 0)
                center_pct = scores.get("CENTER", 0)
                right_pct = scores.get("RIGHT", 0)

                st.markdown(f"""
                <div class="glass-card">
                    <div style="margin-bottom:12px;">
                        {get_badge_html(label)}
                        <span style="color:#94A3B8;font-size:0.9rem;margin-left:12px;">{confidence:.1f}% confidence</span>
                    </div>
                    <div style="margin:12px 0;">
                        <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:6px;">Bias Score Breakdown</div>
                        <div style="display:flex;border-radius:8px;overflow:hidden;height:28px;">
                            <div style="width:{left_pct}%;background:#3B82F6;display:flex;align-items:center;justify-content:center;font-size:0.75rem;color:white;font-weight:600;">{left_pct:.0f}%</div>
                            <div style="width:{center_pct}%;background:#22C55E;display:flex;align-items:center;justify-content:center;font-size:0.75rem;color:white;font-weight:600;">{center_pct:.0f}%</div>
                            <div style="width:{right_pct}%;background:#EF4444;display:flex;align-items:center;justify-content:center;font-size:0.75rem;color:white;font-weight:600;">{right_pct:.0f}%</div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#64748B;margin-top:4px;">
                            <span>⬅️ LEFT</span><span>⚖️ CENTER</span><span>➡️ RIGHT</span>
                        </div>
                    </div>
                    <div style="color:#CBD5E1;font-size:0.95rem;line-height:1.6;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;">
                        💡 {get_plain_english_explanation(bias, st.session_state.current_sentences or [])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # NEW — Confidence Breakdown
                with st.expander("🔬 Why this confidence score? (Technical breakdown)"):
                    chunks_used = bias.get("chunking_used", False)
                    st.markdown(f"""
                    <div class="calibration-card">
                        <div style="font-size:0.9rem;color:#CBD5E1;line-height:1.8;">
                            <strong style="color:#8B5CF6;">How {confidence:.0f}% was calculated:</strong><br>
                            📄 Article chunking: <strong>{'Yes — averaged across multiple chunks' if chunks_used else 'No — single pass (short article)'}</strong><br>
                            🔢 LEFT score: <strong>{left_pct:.1f}%</strong> &nbsp;|&nbsp;
                               CENTER score: <strong>{center_pct:.1f}%</strong> &nbsp;|&nbsp;
                               RIGHT score: <strong>{right_pct:.1f}%</strong><br>
                            🏆 Predicted class: <strong>{label}</strong> (highest softmax probability)<br>
                            📊 Confidence = softmax probability of predicted class = <strong>{confidence:.1f}%</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                trust_score = get_trust_score(
                    confidence,
                    extra.get("fear_score", 0) if extra else 0,
                    extra.get("clickbait_score", 0) if extra else 0,
                    credibility.get("found_in_database", False) if credibility else False
                )
                trust_color = "#22C55E" if trust_score >= 70 else "#F97316" if trust_score >= 40 else "#EF4444"
                trust_msg = "✅ Generally Trustworthy" if trust_score >= 70 else "⚠️ Read Critically" if trust_score >= 40 else "❌ High Manipulation Risk"
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;margin-top:8px;">
                    <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:4px;">🛡️ Article Trust Score</div>
                    <div style="font-size:2.5rem;font-weight:800;color:{trust_color};">{trust_score}</div>
                    <div style="font-size:0.8rem;color:#64748B;">out of 100</div>
                    <div style="font-size:0.8rem;color:#94A3B8;margin-top:4px;">{trust_msg}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_gauge:
            if bias:
                fig_gauge = bias_gauge_chart(bias.get("confidence", 0), bias.get("label", "UNKNOWN"))
                st.plotly_chart(fig_gauge, use_container_width=True)
                fig_pie = bias_distribution_pie(bias.get("scores", {}))
                st.plotly_chart(fig_pie, use_container_width=True)

        complexity = get_complexity_score(article.get("text", ""))
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: st.metric("📚 Reading Level", complexity["level"])
        with col_c2: st.metric("📏 Avg Words/Sentence", complexity["avg_words_per_sentence"])
        with col_c3: st.metric("🔤 Complexity Score", f"{complexity['score']}/100")

        if bias and extra and credibility:
            verdict_result = get_credibility_verdict(bias.get("label", ""), credibility)
            fig_dna = create_bias_dna_chart(
                bias.get("confidence", 0), extra.get("fear_score", 0),
                extra.get("clickbait_score", 0), verdict_result.get("confidence", "LOW"),
                complexity["score"]
            )
            st.plotly_chart(fig_dna, use_container_width=True)

        st.subheader("🚨 Extra Bias Signals")
        if extra:
            col_fear, col_click = st.columns(2)
            with col_fear:
                if extra.get("fear_detected"):
                    st.error(f"😱 **Fear-Mongering** — Score: {extra['fear_score']:.0f}%")
                    triggers = extra.get("fear_triggers", [])[:8]
                    if triggers:
                        html = " ".join([f'<span class="word-removed">{w}</span>' for w in triggers])
                        st.markdown(f"**Triggers:** {html}", unsafe_allow_html=True)
                else:
                    st.success(f"✅ No Fear-Mongering — Score: {extra.get('fear_score',0):.0f}%")
            with col_click:
                if extra.get("clickbait_detected"):
                    st.warning(f"🎣 **Clickbait** — Score: {extra['clickbait_score']:.0f}%")
                    st.markdown(f"**Patterns found:** {len(extra.get('clickbait_triggers',[]))} patterns")
                else:
                    st.success(f"✅ No Clickbait — Score: {extra.get('clickbait_score',0):.0f}%")

        st.subheader("🏛️ Source Credibility Check")
        if credibility and bias:
            verdict_result = get_credibility_verdict(bias.get("label", ""), credibility)
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                rating_html = get_badge_html(credibility.get('allsides_rating','UNKNOWN'), 'small') if credibility.get('allsides_rating') else '<span style="color:#64748B">Not in database</span>'
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:8px;">Source Profile</div>
                    <div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;">🌐 {credibility.get('source_name', credibility.get('domain','Unknown'))}</div>
                    <div style="margin-top:8px;">{rating_html} <span style="color:#64748B;font-size:0.85rem;margin-left:8px;">AllSides Rating</span></div>
                    <div style="color:#64748B;font-size:0.8rem;margin-top:8px;">Database: {credibility.get('database_size',0)} sources tracked</div>
                </div>
                """, unsafe_allow_html=True)
            with col_s2:
                verdict = verdict_result.get("verdict", "")
                explanation = verdict_result.get("explanation", "")
                if verdict == "HIGH CONFIDENCE":
                    st.success(f"✅ **{verdict}** — {explanation}")
                elif verdict == "CONFLICTING SIGNALS":
                    st.warning(f"⚠️ **{verdict}** — {explanation}")
                else:
                    st.info(f"ℹ️ **{verdict}** — {explanation}")

        # Download buttons — JSON + PDF
        if article and bias and extra and credibility:
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                report_json = generate_report_json(article, bias, extra or {}, st.session_state.current_sentences or [], credibility or {})
                st.download_button(
                    label="📥 Download Report (JSON)",
                    data=report_json,
                    file_name=f"bias_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            with dl_col2:
                pdf_bytes = generate_pdf_report(article, bias, extra or {}, st.session_state.current_sentences or [], credibility or {})
                if pdf_bytes:
                    st.download_button(
                        label="📄 Download Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"bias_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.info("Install fpdf2 for PDF export: pip install fpdf2")

        st.markdown('<div style="color:#475569;font-size:0.8rem;margin-top:16px;text-align:center;">🤖 Model accuracy: 85.06% on Faith1712/Allsides test set— predictions may not be 100% accurate. Always read critically.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 2 — SENTENCE HIGHLIGHTS
# ══════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.current_article:
        st.info("👆 Analyze an article first to see sentence highlights")
    else:
        article = st.session_state.current_article
        sentences = st.session_state.current_sentences or []
        bias = st.session_state.current_bias

        st.subheader("🔦 Most Biased Sentences")
        st.markdown('<div style="color:#94A3B8;font-size:0.9rem;margin-bottom:16px;">These sentences most influenced the bias prediction. &nbsp; 🔴 <strong>HIGH</strong> (70%+) &nbsp; 🟠 <strong>MEDIUM</strong> (40-70%) &nbsp; 🟡 <strong>LOW</strong> (below 40%)</div>', unsafe_allow_html=True)

        if bias:
            explanation = get_plain_english_explanation(bias, sentences)
            st.info(f"💡 **Why this article is biased:** {explanation}")

        if sentences:
            for s in sentences:
                severity = s.get("severity", "LOW")
                score = s.get("bias_score", 0)
                direction = s.get("direction", "CENTER")
                sentence_text = s.get("sentence", "")
                severity_emoji = "🔴" if severity == "HIGH" else "🟠" if severity == "MEDIUM" else "🟡"
                css_class = f"sentence-{severity.lower()}"
                direction_badge = get_badge_html(direction, "small")
                st.markdown(f"""
                <div class="{css_class}">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <span style="font-weight:700;color:#F1F5F9;">{severity_emoji} {severity}</span>
                        <span style="display:flex;align-items:center;gap:8px;">
                            {direction_badge}
                            <span style="background:rgba(255,255,255,0.1);color:#CBD5E1;padding:4px 10px;border-radius:20px;font-size:0.8rem;font-weight:600;">{score:.1f}%</span>
                        </span>
                    </div>
                    <div style="color:#E2E8F0;line-height:1.6;">"{sentence_text}"</div>
                    <div style="margin-top:8px;font-size:0.8rem;color:#64748B;">
                        LEFT: {s.get('left_score',0):.1f}% &nbsp;|&nbsp; CENTER: {s.get('center_score',0):.1f}% &nbsp;|&nbsp; RIGHT: {s.get('right_score',0):.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("✅ No strongly biased sentences detected. Article may be relatively neutral.")

        st.subheader("🌡️ Article Bias Heatmap")
        st.markdown('<div style="color:#94A3B8;font-size:0.85rem;margin-bottom:12px;">🔵 Blue = LEFT leaning &nbsp; 🔴 Red = RIGHT leaning &nbsp; 🟢 Green = Neutral &nbsp; Hover over sentences for scores</div>', unsafe_allow_html=True)
        heatmap_html = create_sentence_heatmap(article.get("text", ""), sentences)
        st.markdown(f'<div class="glass-card" style="line-height:2;font-size:0.95rem;">{heatmap_html}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — NEUTRAL REWRITE
# ══════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.current_article:
        st.info("👆 Analyze an article first to use the rewriter")
    else:
        article = st.session_state.current_article
        bias = st.session_state.current_bias

        st.subheader("✍️ Neutral Rewrite with GPT-3.5")
        st.info("💰 Rewriting costs approximately $0.002 per article using GPT-3.5")

        if st.button("✍️ Rewrite Article in Neutral Tone", key="rewrite_btn"):
            with st.spinner("✍️ GPT-3.5 is rewriting in neutral tone..."):
                rewrite_result = rewrite_neutral(article["text"])
                st.session_state.current_rewrite = rewrite_result
                if rewrite_result.get("error"):
                    st.error(f"❌ {rewrite_result['error']}")
                else:
                    with st.spinner("🤖 Analyzing rewritten text for bias..."):
                        rewrite_bias = classify_bias(rewrite_result["rewritten_text"])
                        st.session_state.rewrite_bias = rewrite_bias

        if st.session_state.current_rewrite and not st.session_state.current_rewrite.get("error"):
            rewrite = st.session_state.current_rewrite
            original_text = article["text"]
            neutral_text = rewrite.get("rewritten_text", "")

            # Before / After Bias Score
            if bias and st.session_state.rewrite_bias:
                orig_label = bias.get("label", "UNKNOWN")
                orig_conf = bias.get("confidence", 0)
                new_label = st.session_state.rewrite_bias.get("label", "UNKNOWN")
                new_conf = st.session_state.rewrite_bias.get("confidence", 0)
                improvement = round(orig_conf - new_conf, 1)
                improvement_color = "#22C55E" if improvement > 0 else "#EF4444"
                improvement_text = f"↓ {improvement}% less biased" if improvement > 0 else f"↑ {abs(improvement)}% more biased"
                st.markdown(f"""
                <div class="before-after-card">
                    <div style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:16px;">📊 Bias Score: Before vs After Rewrite</div>
                    <div style="display:flex;justify-content:space-around;align-items:center;">
                        <div style="text-align:center;">
                            <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:8px;">ORIGINAL</div>
                            {get_badge_html(orig_label)}
                            <div style="font-size:1.5rem;font-weight:800;color:#F1F5F9;margin-top:8px;">{orig_conf:.1f}%</div>
                        </div>
                        <div style="text-align:center;font-size:2rem;color:#64748B;">→</div>
                        <div style="text-align:center;">
                            <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:8px;">AFTER REWRITE</div>
                            {get_badge_html(new_label)}
                            <div style="font-size:1.5rem;font-weight:800;color:#F1F5F9;margin-top:8px;">{new_conf:.1f}%</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:8px;">IMPROVEMENT</div>
                            <div style="font-size:1.3rem;font-weight:800;color:{improvement_color};">{improvement_text}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            col_orig, col_neutral = st.columns(2)
            with col_orig:
                st.subheader("📄 Original Article")
                st.text_area("", original_text, height=400, disabled=True, key="orig_text")
            with col_neutral:
                st.subheader("✅ Neutral Version")
                st.text_area("", neutral_text, height=400, disabled=True, key="neutral_text")
                if st.button("📋 Copy Neutral Text", key="copy_btn"):
                    st.code(neutral_text, language=None)
                    st.success("✅ Select all and copy (Ctrl+A, Ctrl+C)")

            diff_blocks = generate_diff(original_text, neutral_text)
            stats = get_diff_stats(diff_blocks)
            word_diff = get_word_diff(original_text, neutral_text)

            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1: st.metric("Lines Removed", stats.get("lines_removed", 0))
            with col_s2: st.metric("Lines Added", stats.get("lines_added", 0))
            with col_s3: st.metric("Total Changes", stats.get("total_changes", 0))
            with col_s4: st.metric("% Changed", f"{stats.get('percent_changed',0)}%")

            col_w1, col_w2 = st.columns(2)
            with col_w1:
                st.markdown("**❌ Removed Biased Words**")
                removed_html = " ".join([f'<span class="word-removed">{w}</span>' for w in word_diff.get("top_removed_words", [])[:10]])
                st.markdown(removed_html or "None detected", unsafe_allow_html=True)
            with col_w2:
                st.markdown("**✅ Added Neutral Words**")
                added_html = " ".join([f'<span class="word-added">{w}</span>' for w in word_diff.get("top_added_words", [])[:10]])
                st.markdown(added_html or "None detected", unsafe_allow_html=True)

            st.subheader("🔄 Line by Line Changes")
            diff_count = 0
            for block in diff_blocks:
                if block["type"] == "removed":
                    st.markdown(f'<div class="diff-removed">➖ {block["text"]}</div>', unsafe_allow_html=True)
                    diff_count += 1
                elif block["type"] == "added":
                    st.markdown(f'<div class="diff-added">➕ {block["text"]}</div>', unsafe_allow_html=True)
                    diff_count += 1
                if diff_count > 30:
                    st.markdown('<div style="color:#64748B;font-size:0.85rem;">... showing first 30 changes</div>', unsafe_allow_html=True)
                    break

            st.warning(f"⚠️ {DISCLAIMER}")

# ══════════════════════════════════════════════════════════
# TAB 4 — ARTICLE COMPARISON
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("⚖️ Compare Two Articles Side by Side")
    st.info("🔍 Paste two articles on the **same topic** from different sources to see how differently they frame the story")

    st.markdown("""
    <div class="glass-card" style="margin-bottom:16px;">
        <div style="font-size:0.9rem;color:#94A3B8;">
            💡 <strong>Suggested pair:</strong> Search "Ukraine war" or "US economy" on Fox News and BBC — paste both URLs below<br><br>
            🎯 <strong>Best results:</strong> Same news event, different sources — Fox News vs BBC or Times of India vs The Wire
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_url1, col_url2 = st.columns(2)
    with col_url1:
        compare_url1 = st.text_input("Article 1 URL", placeholder="https://www.foxnews.com/...", key="compare_url1")
    with col_url2:
        compare_url2 = st.text_input("Article 2 URL", placeholder="https://www.bbc.com/...", key="compare_url2")

    if st.button("⚖️ Compare Articles", type="primary", key="compare_btn"):
        if compare_url1 and compare_url2:
            with st.spinner("🔄 Analyzing both articles... This takes 2-3 minutes"):
                result = compare_articles(compare_url1, compare_url2)
                st.session_state.comparison_result = result
                if result.get("error"):
                    st.error(f"❌ {result['error']}")
        else:
            st.warning("⚠️ Please paste both URLs")

    if not st.session_state.comparison_result:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#475569;">
            <div style="font-size:3rem;margin-bottom:12px;">⚖️</div>
            <div style="font-size:1.1rem;color:#94A3B8;">Compare two articles to see how Fox News and BBC cover the same story differently</div>
            <div style="font-size:0.85rem;margin-top:8px;color:#334155;">Paste two URLs above and click Compare Articles</div>
        </div>
        """, unsafe_allow_html=True)
    elif not st.session_state.comparison_result.get("error"):
        result = st.session_state.comparison_result
        art1 = result.get("article1", {})
        art2 = result.get("article2", {})
        verdict = result.get("verdict", {})

        st.success(f"📊 **{result.get('comparison_summary','')}**")

        col_a1, col_a2 = st.columns(2)
        for col, art, num in [(col_a1, art1, 1), (col_a2, art2, 2)]:
            with col:
                label = art.get("bias_label", "UNKNOWN")
                confidence = art.get("bias_confidence", 0)
                domain = art.get("source_domain", f"Article {num}")
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-size:1rem;font-weight:700;color:#94A3B8;margin-bottom:8px;">Article {num} — {domain}</div>
                    <div style="font-size:0.95rem;color:#F1F5F9;margin-bottom:12px;">{art.get('title','Unknown')[:80]}...</div>
                    <div style="margin-bottom:8px;">{get_badge_html(label)} <span style="color:#94A3B8;margin-left:8px;">{confidence:.1f}%</span></div>
                    <div style="font-size:0.85rem;color:#64748B;">
                        😱 Fear: {art.get('fear_score',0):.0f}% &nbsp;|&nbsp;
                        🎣 Clickbait: {art.get('clickbait_score',0):.0f}% &nbsp;|&nbsp;
                        📝 {art.get('word_count',0)} words
                    </div>
                    <div style="font-size:0.85rem;color:#64748B;margin-top:4px;">AllSides: {art.get('allsides_rating','Unknown')}</div>
                </div>
                """, unsafe_allow_html=True)
                sentences = art.get("top_biased_sentences", [])
                if sentences:
                    st.markdown("**Top Biased Sentences:**")
                    for s in sentences[:3]:
                        sev = s.get("severity", "LOW")
                        css = f"sentence-{sev.lower()}"
                        st.markdown(f'<div class="{css}" style="font-size:0.85rem;"><strong>{s.get("bias_score",0):.0f}%</strong> — {s.get("sentence","")[:100]}...</div>', unsafe_allow_html=True)

        st.subheader("🏆 Verdict")
        col_v1, col_v2 = st.columns(2)
        with col_v1: st.error(f"📊 **More Biased:** {verdict.get('more_biased_source','')}")
        with col_v2: st.success(f"✅ **More Balanced:** {verdict.get('less_biased_source','')}")
        st.info(f"📝 {verdict.get('verdict','')}")
        st.warning(f"💡 {verdict.get('recommendation','')}")

        scores1 = art1.get("bias_scores", {})
        scores2 = art2.get("bias_scores", {})
        domain1 = art1.get("source_domain", "Article 1")
        domain2 = art2.get("source_domain", "Article 2")
        fig_compare = go.Figure()
        for cat, color in [("LEFT","#3B82F6"), ("CENTER","#22C55E"), ("RIGHT","#EF4444")]:
            fig_compare.add_trace(go.Bar(
                name=cat, x=[domain1, domain2],
                y=[scores1.get(cat,0), scores2.get(cat,0)],
                marker_color=color,
                text=[f"{scores1.get(cat,0):.1f}%", f"{scores2.get(cat,0):.1f}%"],
                textposition="outside"
            ))
        fig_compare.update_layout(
            barmode="group",
            title=dict(text="📊 Bias Score Comparison", font=dict(color="#F1F5F9"), x=0.5),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.6)",
            font=dict(color="#CBD5E1"), height=350,
            legend=dict(font=dict(color="#CBD5E1"), bgcolor="rgba(0,0,0,0)")
        )
        st.plotly_chart(fig_compare, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 5 — EVALUATION DASHBOARD
# ══════════════════════════════════════════════════════════
with tab5:
    st.subheader("📊 Model Evaluation Dashboard")
    st.info("These metrics show how well our fine-tuned DistilBERT model performs on the Faith1712/Allsides_political_bias_proper test set")
    metrics_result = load_metrics()
    cm_result = load_confusion_matrix()

    if not metrics_result["found"]:
        st.warning("⚠️ Metrics not found. Run `python model/evaluation.py` from terminal first.")
    else:
        metrics = metrics_result["metrics"]
        accuracy = metrics.get("overall_accuracy", 0) * 100
        weighted_f1 = metrics.get("weighted_f1", 0)
        total_samples = metrics.get("total_test_samples", 0)

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric("🎯 Overall Accuracy", f"{accuracy:.2f}%")
        with col_m2: st.metric("📈 Weighted F1 Score", f"{weighted_f1:.4f}")
        with col_m3: st.metric("🔢 Test Samples", total_samples)

        st.subheader("Per Class Performance")
        fig_table = metrics_table(metrics)
        st.plotly_chart(fig_table, use_container_width=True)

        # NEW — Calibration Analysis
        st.subheader("🔬 Model Calibration Analysis")
        per_class = metrics.get("per_class", {})
        cal_col1, cal_col2, cal_col3 = st.columns(3)
        for col, cls in zip([cal_col1, cal_col2, cal_col3], ["LEFT", "CENTER", "RIGHT"]):
            with col:
                prec = per_class.get(cls, {}).get("precision", 0) * 100
                rec = per_class.get(cls, {}).get("recall", 0) * 100
                f1 = per_class.get(cls, {}).get("f1", 0) * 100
                color = BIAS_COLORS.get(cls, "#94A3B8")
                if prec >= 85: cal_status = "✅ Well calibrated"
                elif prec >= 75: cal_status = "⚠️ Moderate"
                else: cal_status = "❌ Needs improvement"
                st.markdown(f"""
                <div class="calibration-card">
                    <div style="font-size:1rem;font-weight:700;color:{color};margin-bottom:8px;">{cls}</div>
                    <div style="font-size:0.85rem;color:#CBD5E1;line-height:1.8;">
                        Precision: <strong>{prec:.1f}%</strong><br>
                        Recall: <strong>{rec:.1f}%</strong><br>
                        F1: <strong>{f1:.1f}%</strong><br>
                        Status: {cal_status}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.subheader("Confusion Matrix")
        if cm_result["found"]:
            st.image(cm_result["image"], caption="DistilBERT Political Bias Classification — Confusion Matrix", use_column_width=True)
        else:
            st.info(cm_result.get("message", "Confusion matrix not found"))

        st.subheader("Model Information")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown("""
            <div class="glass-card">
                <div style="color:#94A3B8;font-size:0.85rem;margin-bottom:12px;">Model Details</div>
                <div style="color:#F1F5F9;line-height:2;">
                    🤖 <strong>Model:</strong> DistilBERT fine-tuned<br>
                    📚 <strong>Base:</strong> distilbert-base-uncased<br>
                    📊 <strong>Dataset:</strong> AllSides Political Bias<br>
                    🏋️ <strong>Epochs:</strong> 4<br>
                    📏 <strong>Max Length:</strong> 512 tokens<br>
                    🎯 <strong>Labels:</strong> LEFT / CENTER / RIGHT
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_info2:
            eval_date = metrics.get("evaluation_date", "2025-05-24")
            st.markdown(f"""
            <div class="glass-card">
                <div style="color:#94A3B8;font-size:0.85rem;margin-bottom:12px;">Evaluation Details</div>
                <div style="color:#F1F5F9;line-height:2;">
                    📅 <strong>Date:</strong> {eval_date}<br>
                    🔢 <strong>Samples:</strong> {total_samples}<br>
                    📰 <strong>Source:</strong> Faith1712/Allsides_political_bias_proper<br>
                    🚀 <strong>Platform:</strong> HuggingFace Spaces<br>
                    💻 <strong>Hardware:</strong> CPU inference<br>
                    📈 <strong>Best Class F1:</strong> LEFT 86.49%
                </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 6 — SESSION HISTORY
# ══════════════════════════════════════════════════════════
with tab6:
    st.subheader("📋 Session History")
    if not st.session_state.history:
        st.markdown("""
        <div style="text-align:center;padding:60px;color:#475569;">
            <div style="font-size:3rem;margin-bottom:16px;">📋</div>
            <div style="font-size:1.2rem;color:#94A3B8;">No articles analyzed yet</div>
            <div style="font-size:0.9rem;margin-top:8px;">Analyze articles to see your reading history and diversity score</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        history = st.session_state.history
        label_counts = Counter([h.get("label", "UNKNOWN") for h in history])

        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        with col_h1: st.metric("📰 Total Analyzed", len(history))
        with col_h2: st.metric("⬅️ LEFT", label_counts.get("LEFT", 0))
        with col_h3: st.metric("⚖️ CENTER", label_counts.get("CENTER", 0))
        with col_h4: st.metric("➡️ RIGHT", label_counts.get("RIGHT", 0))

        diversity = get_reading_diversity_score(history)
        div_color = "#22C55E" if diversity >= 70 else "#F97316" if diversity >= 40 else "#EF4444"
        div_msg = "🌈 Excellent — Reading diverse perspectives!" if diversity >= 70 else "⚠️ Moderate — Try reading more balanced sources" if diversity >= 40 else "❌ Low — Reading mostly one-sided content"
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;margin:12px 0;">
            <div style="font-size:0.9rem;color:#94A3B8;margin-bottom:4px;">🎯 Reading Diversity Score</div>
            <div style="font-size:2.5rem;font-weight:800;color:{div_color};">{diversity}/100</div>
            <div style="font-size:0.85rem;color:#64748B;">{div_msg}</div>
        </div>
        """, unsafe_allow_html=True)

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_summary = session_summary_chart(history)
            st.plotly_chart(fig_summary, use_container_width=True)
        with col_chart2:
            fig_history = bias_score_chart(history)
            st.plotly_chart(fig_history, use_container_width=True)

        # NEW — Source Bias History
        if len(history) >= 2:
            st.subheader("📰 Source Bias History")
            source_data = get_source_bias_history(history)
            if len(source_data) >= 2:
                fig_source = create_source_bias_history_chart(source_data)
                st.plotly_chart(fig_source, use_container_width=True)
                for domain, data in source_data.items():
                    badge = get_badge_html(data["dominant_label"], "small")
                    st.markdown(
                        f'<div style="color:#CBD5E1;font-size:0.85rem;margin:2px 0;">'
                        f'{badge} &nbsp; <strong>{domain}</strong> — avg {data["avg_confidence"]}% bias — {data["article_count"]} articles</div>',
                        unsafe_allow_html=True
                    )

        st.subheader("Articles Analyzed")
        for h in reversed(history):
            label = h.get("label", "UNKNOWN")
            col_b, col_t, col_c, col_d = st.columns([1, 4, 1, 2])
            with col_b:
                st.markdown(get_badge_html(label, "small"), unsafe_allow_html=True)
            with col_t:
                st.markdown(f'<div style="color:#CBD5E1;font-size:0.9rem;padding-top:6px;">{h.get("title","Unknown")[:60]}</div>', unsafe_allow_html=True)
            with col_c:
                st.markdown(f'<div style="color:#94A3B8;font-size:0.9rem;padding-top:6px;">{h.get("confidence",0):.1f}%</div>', unsafe_allow_html=True)
            with col_d:
                try:
                    domain = urlparse(h.get("url","")).netloc.replace("www.","")
                except:
                    domain = "Unknown"
                st.markdown(f'<div style="color:#64748B;font-size:0.85rem;padding-top:6px;">{domain}</div>', unsafe_allow_html=True)

        if st.button("🗑️ Clear Session History"):
            st.session_state.history = []
            st.session_state.url_cache = {}
            st.rerun()

# ── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:1.5rem;font-weight:800;color:#3B82F6;">🔍 MediaBiasIQ</div>
        <div style="font-size:0.8rem;color:#64748B;">v1.0.0 — Portfolio Project</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**About**")
    st.markdown('<div style="color:#94A3B8;font-size:0.85rem;line-height:1.8;">MediaBiasIQ detects political bias in news articles using fine-tuned DistilBERT and explains exactly which sentences caused the bias using Explainable AI.</div>', unsafe_allow_html=True)

    st.markdown("**Tech Stack**")
    for icon, name, color in [
        ("🤖","DistilBERT fine-tuned","#3B82F6"),
        ("📊","AllSides Dataset 17K","#22C55E"),
        ("🧠","SHAP Explainability","#8B5CF6"),
        ("✍️","GPT-3.5 Rewriter","#F59E0B"),
        ("📈","Plotly Charts","#EC4899"),
        ("🚀","Streamlit UI","#EF4444"),
        ("🐍","PyTorch + HuggingFace","#94A3B8"),
    ]:
        st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-radius:6px;padding:6px 10px;margin:4px 0;color:{color};font-size:0.85rem;">{icon} {name}</div>', unsafe_allow_html=True)

    st.markdown("**Model Performance**")
    st.markdown("""
    <div class="glass-card">
        <div style="color:#F1F5F9;font-size:0.85rem;line-height:2;">
            🎯 Accuracy: <strong style="color:#22C55E;">85.06%</strong><br>
            📈 F1 Score: <strong style="color:#22C55E;">0.8498</strong><br>
            📰 Dataset: <strong>17,362 articles</strong><br>
            🏷️ Classes: LEFT / CENTER / RIGHT
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Links**")
    st.markdown("""
    <div style="color:#94A3B8;font-size:0.85rem;line-height:2;">
            🐙 <a href="https://github.com/sandeepkumarcm/mediabiasiq" style="color:#3B82F6;">GitHub Repository</a><br>
            🤗 <a href="https://huggingface.co/spaces/sandeepcm/mediabiasiq" style="color:#3B82F6;">HuggingFace Space</a><br>
            📄 <a href="https://huggingface.co/sandeepcm/news-bias-distilbert" style="color:#3B82F6;">Model Card</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:20px;padding:12px;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.3);border-radius:8px;text-align:center;">
        <div style="color:#3B82F6;font-size:0.85rem;font-weight:600;">Built for 10 LPA ML Engineer Roles</div>
        <div style="color:#64748B;font-size:0.75rem;margin-top:4px;">Portfolio Project 2025</div>
    </div>
    """, unsafe_allow_html=True)