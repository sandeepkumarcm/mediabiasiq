import os
import json
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image

# ── Color Constants ───────────────────────────────────────
BIAS_COLORS = {
    "LEFT": "#3B82F6",
    "CENTER": "#22C55E",
    "RIGHT": "#EF4444",
    "CENTER-LEFT": "#60A5FA",
    "CENTER-RIGHT": "#F87171",
    "UNKNOWN": "#94A3B8"
}

SEVERITY_COLORS = {
    "HIGH": "#EF4444",
    "MEDIUM": "#F97316",
    "LOW": "#EAB308"
}

# ── File paths ────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFUSION_MATRIX_PATH = os.path.join(BASE_DIR, "dashboard", "confusion_matrix.png")
METRICS_JSON_PATH = os.path.join(BASE_DIR, "dashboard", "metrics.json")


def bias_score_chart(history: list) -> go.Figure:
    if not history:
        fig = go.Figure()
        fig.add_annotation(
            text="No articles analyzed yet — paste a URL above to get started",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#94A3B8")
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300
        )
        return fig

    titles = [h.get("title", "Unknown")[:30] + "..." if len(h.get("title", "")) > 30
              else h.get("title", "Unknown") for h in history]
    confidences = [h.get("confidence", 0) for h in history]
    labels = [h.get("label", "UNKNOWN") for h in history]
    colors = [BIAS_COLORS.get(l, "#94A3B8") for l in labels]
    hover_texts = [
        f"<b>{h.get('title', 'Unknown')}</b><br>"
        f"Label: {h.get('label', 'UNKNOWN')}<br>"
        f"Confidence: {h.get('confidence', 0):.1f}%<br>"
        f"URL: {h.get('url', '')[:50]}..."
        for h in history
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=titles,
        y=confidences,
        marker_color=colors,
        text=[f"{l}<br>{c:.1f}%" for l, c in zip(labels, confidences)],
        textposition="outside",
        hovertext=hover_texts,
        hoverinfo="text",
        textfont=dict(size=11, color="white"),
    ))

    fig.update_layout(
        title=dict(
            text="📊 Bias Confidence by Article",
            font=dict(size=18, color="#F1F5F9"),
            x=0.5
        ),
        xaxis=dict(
        title=dict(text="Article", font=dict(color="#94A3B8")),  # ✅
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(255,255,255,0.05)"
    ),
        yaxis=dict(
        title=dict(text="Confidence %", font=dict(color="#94A3B8")),  # ✅
        range=[0, 120],
        tickfont=dict(color="#CBD5E1"),
        gridcolor="rgba(255,255,255,0.05)"
    ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        height=400,
        showlegend=False,
        margin=dict(t=60, b=80, l=60, r=20)
    )
    return fig


def bias_distribution_pie(scores: dict) -> go.Figure:
    if not scores:
        scores = {"LEFT": 33.3, "CENTER": 33.3, "RIGHT": 33.3}

    labels = list(scores.keys())
    values = list(scores.values())
    colors = [BIAS_COLORS.get(l, "#94A3B8") for l in labels]

    max_idx = values.index(max(values))
    pull = [0.08 if i == max_idx else 0 for i in range(len(values))]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0,
        pull=pull,
        marker=dict(
            colors=colors,
            line=dict(color="#0F172A", width=2)
        ),
        textinfo="label+percent",
        textfont=dict(size=13, color="white"),
        hovertemplate="<b>%{label}</b><br>Score: %{value:.1f}%<extra></extra>"
    )])

    fig.update_layout(
        title=dict(
            text="🎯 Bias Score Distribution",
            font=dict(size=16, color="#F1F5F9"),
            x=0.5
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        legend=dict(
            font=dict(color="#CBD5E1"),
            bgcolor="rgba(0,0,0,0)"
        ),
        margin=dict(t=60, b=20, l=20, r=20)
    )
    return fig


def load_confusion_matrix() -> dict:
    if os.path.exists(CONFUSION_MATRIX_PATH):
        try:
            image = Image.open(CONFUSION_MATRIX_PATH)
            return {"image": image, "found": True}
        except Exception as e:
            return {
                "image": None,
                "found": False,
                "message": f"Error loading confusion matrix: {str(e)}"
            }
    return {
        "image": None,
        "found": False,
        "message": "Confusion matrix not found. Please run model/evaluation.py first from your terminal."
    }


def load_metrics() -> dict:
    if os.path.exists(METRICS_JSON_PATH):
        try:
            with open(METRICS_JSON_PATH, "r") as f:
                metrics = json.load(f)
            return {"metrics": metrics, "found": True}
        except Exception as e:
            return {
                "metrics": None,
                "found": False,
                "message": f"Error loading metrics: {str(e)}"
            }
    return {
        "metrics": None,
        "found": False,
        "message": "Metrics not found. Please run model/evaluation.py first from your terminal."
    }


def metrics_table(metrics: dict) -> go.Figure:
    if not metrics:
        fig = go.Figure()
        fig.add_annotation(
            text="No metrics available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#94A3B8")
        )
        return fig

    per_class = metrics.get("per_class", {})
    weighted_f1 = metrics.get("weighted_f1", 0)
    overall_accuracy = metrics.get("overall_accuracy", 0)

    classes = ["LEFT", "CENTER", "RIGHT"]
    precisions = [round(per_class.get(c, {}).get("precision", 0), 3) for c in classes]
    recalls = [round(per_class.get(c, {}).get("recall", 0), 3) for c in classes]
    f1s = [round(per_class.get(c, {}).get("f1", 0), 3) for c in classes]

    row_colors = ["#1E3A5F", "#1A3350", "#162D47"]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["<b>Class</b>", "<b>Precision</b>", "<b>Recall</b>", "<b>F1 Score</b>"],
            fill_color="#1E293B",
            font=dict(color="white", size=14),
            align="center",
            height=40,
            line=dict(color="#334155", width=1)
        ),
        cells=dict(
            values=[
                classes + ["Weighted Avg"],
                precisions + [round(weighted_f1, 3)],
                recalls + [round(overall_accuracy, 3)],
                f1s + [round(weighted_f1, 3)]
            ],
            fill_color=[
                row_colors + ["#0F2942"],
                row_colors + ["#0F2942"],
                row_colors + ["#0F2942"],
                row_colors + ["#0F2942"]
            ],
            font=dict(color=["#60A5FA", "#22C55E", "#EF4444", "#F8FAFC"] + ["#FBBF24"], size=13),
            align="center",
            height=36,
            line=dict(color="#334155", width=1)
        )
    )])

    fig.update_layout(
        title=dict(
            text="📈 Per Class Model Performance Metrics",
            font=dict(size=16, color="#F1F5F9"),
            x=0.5
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        height=280,
        margin=dict(t=60, b=10, l=10, r=10)
    )
    return fig


def bias_gauge_chart(confidence: float, label: str) -> go.Figure:
    color = BIAS_COLORS.get(label, "#94A3B8")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        number=dict(
            suffix="%",
            font=dict(size=28, color=color)
        ),
        title=dict(
            text=f"Bias Strength — <b>{label}</b>",
            font=dict(size=16, color="#F1F5F9")
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickcolor="#CBD5E1",
                tickfont=dict(color="#CBD5E1", size=11)
            ),
            bar=dict(color=color, thickness=0.25),
            bgcolor="rgba(30,41,59,0.8)",
            borderwidth=1,
            bordercolor="#334155",
            steps=[
                dict(range=[0, 40], color="rgba(34,197,94,0.15)"),
                dict(range=[40, 70], color="rgba(249,115,22,0.15)"),
                dict(range=[70, 100], color="rgba(239,68,68,0.15)")
            ],
            threshold=dict(
                line=dict(color="#FBBF24", width=3),
                thickness=0.8,
                value=70
            )
        )
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=280,
        margin=dict(t=60, b=20, l=30, r=30),
        font=dict(color="#F1F5F9")
    )
    return fig


def session_summary_chart(history: list) -> go.Figure:
    if not history:
        fig = go.Figure(data=[go.Pie(
            labels=["No Data"],
            values=[1],
            hole=0.5,
            marker=dict(colors=["#1E293B"]),
            textinfo="none",
            hoverinfo="none"
        )])
        fig.add_annotation(
            text="0<br>Articles",
            x=0.5, y=0.5,
            font=dict(size=16, color="#94A3B8"),
            showarrow=False
        )
        fig.update_layout(
            title=dict(
                text="📋 Session Analysis Summary",
                font=dict(size=16, color="#F1F5F9"),
                x=0.5
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            height=320,
            showlegend=False,
            margin=dict(t=60, b=20, l=20, r=20)
        )
        return fig

    from collections import Counter
    label_counts = Counter([h.get("label", "UNKNOWN") for h in history])
    total = len(history)

    labels = list(label_counts.keys())
    values = list(label_counts.values())
    colors = [BIAS_COLORS.get(l, "#94A3B8") for l in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(
            colors=colors,
            line=dict(color="#0F172A", width=2)
        ),
        textinfo="label+value",
        textfont=dict(size=13, color="white"),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
    )])

    fig.add_annotation(
        text=f"<b>{total}</b><br>Articles",
        x=0.5, y=0.5,
        font=dict(size=18, color="#F1F5F9"),
        showarrow=False
    )

    fig.update_layout(
        title=dict(
            text="📋 Session Analysis Summary",
            font=dict(size=16, color="#F1F5F9"),
            x=0.5
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        legend=dict(
            font=dict(color="#CBD5E1", size=12),
            bgcolor="rgba(0,0,0,0)"
        ),
        margin=dict(t=60, b=20, l=20, r=20)
    )
    return fig


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING DASHBOARD CHARTS")
    print("="*55)

    sample_history = [
        {"url": "https://bbc.com/1", "title": "BBC Article on Economy",
         "label": "CENTER", "confidence": 71.3},
        {"url": "https://foxnews.com/1", "title": "Fox News Article on Economy",
         "label": "RIGHT", "confidence": 84.7},
        {"url": "https://theguardian.com/1", "title": "Guardian Article on Policy",
         "label": "LEFT", "confidence": 78.2}
    ]

    sample_scores = {"LEFT": 15.2, "CENTER": 71.3, "RIGHT": 13.5}

    sample_metrics = {
        "overall_accuracy": 0.873,
        "weighted_f1": 0.861,
        "per_class": {
            "LEFT": {"precision": 0.88, "recall": 0.85, "f1": 0.86},
            "CENTER": {"precision": 0.84, "recall": 0.89, "f1": 0.86},
            "RIGHT": {"precision": 0.89, "recall": 0.88, "f1": 0.88}
        }
    }

    all_passed = True

    tests = [
        ("bias_score_chart", lambda: bias_score_chart(sample_history)),
        ("bias_distribution_pie", lambda: bias_distribution_pie(sample_scores)),
        ("metrics_table", lambda: metrics_table(sample_metrics)),
        ("bias_gauge_chart", lambda: bias_gauge_chart(84.7, "RIGHT")),
        ("session_summary_chart", lambda: session_summary_chart(sample_history)),
    ]

    for name, func in tests:
        try:
            result = func()
            if result is not None:
                print(f"Function {name} returned Figure: OK ✅")
            else:
                print(f"Function {name} returned None ❌")
                all_passed = False
        except Exception as e:
            print(f"Function {name} FAILED: {str(e)} ❌")
            all_passed = False

    # Test file loading
    cm_result = load_confusion_matrix()
    if cm_result["found"]:
        print(f"Function load_confusion_matrix: confusion_matrix.png FOUND ✅")
    else:
        print(f"Function load_confusion_matrix: NOT FOUND — {cm_result.get('message', '')} ⚠️")

    metrics_result = load_metrics()
    if metrics_result["found"]:
        print(f"Function load_metrics: metrics.json FOUND ✅")
    else:
        print(f"Function load_metrics: NOT FOUND — {metrics_result.get('message', '')} ⚠️")

    print("\n" + "="*55)
    if all_passed:
        print("DASHBOARD CHARTS WORKING CORRECTLY")
    else:
        print("SOME TESTS FAILED — check above")
    print("="*55)