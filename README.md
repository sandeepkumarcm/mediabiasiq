# 🔍 MediaBiasIQ — AI-Powered News Bias Detector & Neutral Rewriter

[![Live Demo](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Demo-yellow?style=for-the-badge)](https://huggingface.co/spaces/sandeepcm/mediabiasiq)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Accuracy](https://img.shields.io/badge/Accuracy-85.06%25-success?style=for-the-badge)](https://huggingface.co/spaces/sandeepcm/mediabiasiq)
[![F1 Score](https://img.shields.io/badge/F1%20Score-0.8498-blue?style=for-the-badge)](https://huggingface.co/spaces/sandeepcm/mediabiasiq)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace-orange?style=for-the-badge)](https://huggingface.co/sandeepcm)

> **Detects LEFT • CENTER • RIGHT political bias in any news article — explains which sentences caused it — rewrites it neutrally using GPT-3.5**

---

## 🎬 Live Demo

[![Demo Video](https://img.youtube.com/vi/wIfUuQsAAbE/maxresdefault.jpg)](https://www.youtube.com/watch?v=wIfUuQsAAbE)

▶️ **[Watch Full Demo on YouTube](https://www.youtube.com/watch?v=wIfUuQsAAbE)** | 🔗 **[Try Live App](https://huggingface.co/spaces/sandeepcm/mediabiasiq)**

---

## 🎯 The Problem

Most people consume news without realizing how word choice, framing, and emotional language shape their opinion. Existing bias-checkers give a vague label with no explanation. **MediaBiasIQ goes further** — it tells you *what* the bias is, *which sentences* caused it, and *rewrites* the article to be neutral while keeping every fact intact.

---

## 🖥️ App Screenshots

### Homepage
<img width="1872" height="842" alt="Screenshot 2026-07-13 161302" src="https://github.com/user-attachments/assets/28264ea8-b241-40d6-85b5-77c54b889707" />


### Bias Analysis | Sentence Highlights
<img width="1882" height="841" alt="Screenshot 2026-07-13 161423" src="https://github.com/user-attachments/assets/66874a01-66af-4410-a50d-c79daae64548" />
 | <img width="1835" height="860" alt="Screenshot 2026-07-13 161510" src="https://github.com/user-attachments/assets/a71c6ab9-2658-4566-9a25-e11346426a5a" />

| **Bias Analysis** — LEFT/CENTER/RIGHT classification with confidence score and pie chart | **Sentence Highlights** — SHAP-powered heatmap showing exactly which sentences are biased |

### Neutral Rewrite | Article Comparison
| <img width="1841" height="865" alt="Screenshot 2026-07-13 162344" src="https://github.com/user-attachments/assets/bdb851bc-b6b2-44af-9d2c-502f412d0800" />
 |<img width="1846" height="840" alt="Screenshot 2026-07-13 162234" src="https://github.com/user-attachments/assets/ddea4087-c589-41f4-ac12-1f8229eb90ae" />
|
| **Neutral Rewrite** — GPT-3.5 rewrites biased sentences. Red = removed, Green = replaced | **Article Comparison** — Two sources, same topic, side-by-side bias verdict |

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎯 **Bias Classification** | Fine-tuned DistilBERT classifies any article as LEFT / CENTER / RIGHT in under 2 seconds |
| 🔦 **Sentence-Level Explainability** | SHAP highlights the exact sentences that drove the bias prediction with severity scores |
| ✍️ **Neutral Rewriting** | GPT-3.5 rewrites biased sentences in neutral, factual language — facts always preserved |
| 🔄 **Diff View** | Side-by-side original vs neutral with red/green diff — see exactly what changed |
| ⚖️ **Article Comparison** | Paste two URLs on the same topic — see how differently sources frame the same event |
| 🗄️ **Source Credibility Check** | Cross-references 60+ news sources against AllSides bias ratings |
| 📊 **Live Evaluation Dashboard** | Confusion matrix, F1 scores, precision/recall — model accuracy proven live in app |
| 🚨 **Fear & Clickbait Detection** | Rule-based detection of fear-mongering and clickbait language patterns |
| 📋 **Session History** | Tracks every article analyzed with reading diversity score |

---

## ⚙️ How It Works

```
News URL
   │
   ▼
🕷️  Article Scraper (Newspaper3k + BeautifulSoup)
   │  Extracts clean title, text, author, date
   ▼
🤖  Bias Classifier (Fine-tuned DistilBERT)
   │  Outputs LEFT / CENTER / RIGHT + confidence scores
   ▼
🚨  Extra Bias Detector (Rule-based)
   │  Fear-mongering & clickbait pattern detection
   ▼
🔦  Explainability Engine (SHAP)
   │  Scores every sentence — highlights top biased ones
   ▼
🗄️  Source Credibility Checker
   │  Cross-checks domain against 60+ source database
   ▼
✍️  Neutral Rewriter (GPT-3.5)
   │  Rewrites biased sentences — keeps all facts intact
   ▼
🔄  Diff Generator (Python difflib)
   │  Shows exactly what changed between versions
   ▼
📊  Streamlit UI — 6 interactive tabs
```

---

## 📊 Model Performance

Evaluated on **3,473 held-out test articles** from the AllSides Political Bias dataset:

| Metric | Score |
|---|---|
| 🎯 Overall Accuracy | **85.06%** |
| 📈 Weighted F1 Score | **0.8498** |
| 🔢 Test Samples | **3,473** |
| 📰 Training Dataset | **17,362 articles** |

### Per-Class Performance

| Class | Precision | Recall | F1 Score |
|---|---|---|---|
| ⬅️ LEFT | 81.5% | 92.1% | **86.5%** |
| ⚖️ CENTER | 91.7% | 78.5% | **84.6%** |
| ➡️ RIGHT | 86.5% | 80.0% | **83.1%** |

### Evaluation Dashboard
<img width="1862" height="842" alt="Screenshot 2026-07-13 162554" src="https://github.com/user-attachments/assets/7144e565-0c9f-4fb0-bcbe-a37015244971" />


### Model Architecture

| Parameter | Value |
|---|---|
| Base Model | `distilbert-base-uncased` |
| Architecture | DistilBertForSequenceClassification |
| Transformer Layers | 6 |
| Attention Heads | 12 |
| Hidden Dimension | 768 |
| FFN Dimension | 3,072 |
| Max Sequence Length | 512 tokens |
| Vocabulary Size | 30,522 |
| Activation | GELU |
| Dropout | 0.1 (attention), 0.2 (classifier) |
| Training Dataset | Faith1712/Allsides_political_bias_proper |
| Epochs | 4 |
| Framework | HuggingFace Transformers 5.0.0 |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Bias Classification | Fine-tuned DistilBERT (PyTorch) | Political bias detection |
| Training Dataset | AllSides Political Bias (17,362 articles) | Model fine-tuning |
| Explainability | SHAP | Sentence-level bias scoring |
| Neutral Rewriting | GPT-3.5 API (OpenAI) | Bias-free article rewriting |
| Article Scraping | Newspaper3k + BeautifulSoup | URL to clean text |
| Extra Detection | Rule-based classifier | Fear-mongering + clickbait |
| Visualization | Plotly | Interactive charts |
| UI Framework | Streamlit | Web application |
| Deployment | HuggingFace Spaces | Free live hosting |
| Evaluation | Scikit-learn | Metrics + confusion matrix |
| Security | python-dotenv | API key management |

---

## 📂 Project Structure

```
mediabiasiq/
│
├── scraper/
│   └── article_scraper.py        # Extracts clean article text from any URL
│
├── model/
│   ├── train_distilbert.py       # Fine-tuning script (run on Google Colab)
│   ├── bias_classifier.py        # Loads model, runs inference with chunking
│   ├── extra_classifier.py       # Fear-mongering & clickbait detection
│   ├── evaluation.py             # Generates accuracy, F1, confusion matrix
│   └── saved_model/              # Fine-tuned DistilBERT weights
│
├── explainability/
│   └── shap_explainer.py         # Sentence-level SHAP bias scoring
│
├── rewriter/
│   └── llm_rewriter.py           # GPT-3.5 neutral rewriting
│
├── diff/
│   └── diff_generator.py         # Original vs neutral comparison
│
├── credibility/
│   └── source_checker.py         # AllSides source credibility lookup
│
├── comparison/
│   └── article_comparator.py     # Two-article side-by-side comparison
│
├── dashboard/
│   └── charts.py                 # Plotly charts + evaluation visuals
│
├── assets/                       # Screenshots for README
├── app.py                        # Main Streamlit application
├── requirements.txt
├── .env                          # API keys (never pushed to GitHub)
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup

```bash
# Clone the repo
git clone https://github.com/sandeepkumarcm/mediabiasiq.git
cd mediabiasiq

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## 🔧 Engineering Highlights

- **Long article handling** — DistilBERT has a 512 token limit. Articles are chunked into 400-word segments, inference run on each chunk, probability scores averaged across all chunks for a single final prediction
- **Sentence-level SHAP** — Instead of slow token-level SHAP, each sentence is scored independently through the classifier. Bias score = distance from CENTER prediction. Top 5 most biased sentences returned
- **GPT temperature 0.3** — Low temperature ensures factual, non-creative rewriting. GPT stays close to original facts while neutralizing emotional framing
- **Source credibility layer** — Model prediction cross-validated against AllSides ratings for 60+ sources. Outputs HIGH CONFIDENCE, CONFLICTING SIGNALS, or UNVERIFIED SOURCE
- **Live accuracy proof** — Confusion matrix and F1 scores embedded directly in the app. Model claims are verifiable live — not just stated on a resume

---

## ⚠️ Current Limitations

- English articles only — regional language bias (Hindi, Tamil) not supported
- Source credibility database covers 60 sources — niche sources return unverified
- CENTER class recall is 78.5% — lowest of the three classes
- GPT-3.5 rewriting costs ~$0.002 per article

---

## 🔮 Future Roadmap

- Multilingual bias detection (Hindi, Tamil, regional Indian languages)
- Browser extension for one-click analysis while reading
- Fine-tune a dedicated rewriting model on biased→neutral sentence pairs
- Real-time bias monitoring dashboard across multiple sources
- Expand credibility database beyond 60 sources

---

## 📄 Resume Line

```
Built a news bias detection system using fine-tuned DistilBERT (85.06% accuracy 
on AllSides 17K dataset) with sentence-level SHAP explainability, GPT-3.5 neutral 
rewriting, source credibility validation, and live article comparison mode — 
deployed on HuggingFace Spaces.
```

---

## 🔗 Links

| | Link |
|---|---|
| 🤗 Live App | [huggingface.co/spaces/sandeepcm/mediabiasiq](https://huggingface.co/spaces/sandeepcm/mediabiasiq) |
| 🎬 Demo Video | [youtube.com/watch?v=wIfUuQsAAbE](https://www.youtube.com/watch?v=wIfUuQsAAbE) |
| 🐙 GitHub | [github.com/sandeepkumarcm](https://github.com/sandeepkumarcm) |
| 📊 Dataset | [Faith1712/Allsides_political_bias_proper](https://huggingface.co/datasets/Faith1712/Allsides_political_bias_proper) |

---

## 👤 Author

**Sandeep Kumar**
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://linkedin.com/in/YOURPROFILEURL)
[![GitHub](https://img.shields.io/badge/GitHub-sandeepkumarcm-black?style=flat&logo=github)](https://github.com/sandeepkumarcm)
[![HuggingFace](https://img.shields.io/badge/🤗-sandeepcm-orange?style=flat)](https://huggingface.co/sandeepcm)

---

