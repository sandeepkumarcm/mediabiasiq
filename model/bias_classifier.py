import os
import json
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, pipeline

# ── Path setup ────────────────────────────────────────────
MODEL_PATH = "sandeepcm/news-bias-distilbert"

# ── Label mapping ─────────────────────────────────────────
id2label = {0: "LEFT", 1: "CENTER", 2: "RIGHT"}
label2id = {"LEFT": 0, "CENTER": 1, "RIGHT": 2}

# Load label_config.json if exists
# Labels are hardcoded — model loads from HuggingFace Hub
id2label = {0: "LEFT", 1: "CENTER", 2: "RIGHT"}
label2id = {"LEFT": 0, "CENTER": 1, "RIGHT": 2}

# ── Device setup ──────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Load model and tokenizer once at module level ─────────
tokenizer = None
model = None
_pipeline = None

def _load_model():
    global tokenizer, model
    if not MODEL_PATH:
       print("ERROR: Model path not set")
       return False
    try:
        tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
        model.to(device)
        model.eval()
        print("Bias classifier model loaded successfully")
        print(f"Device: {device}")
        return True
    except Exception as e:
        print(f"ERROR loading model: {str(e)}")
        return False

# Load at import time
_model_loaded = _load_model()


def _chunk_text(text: str, chunk_size: int = 400) -> list:
    if not text or len(text.strip()) == 0:
        return []
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def classify_bias(text: str) -> dict:
    error_return = {
        "label": None,
        "confidence": 0,
        "scores": {"LEFT": 0, "CENTER": 0, "RIGHT": 0},
        "error": None
    }

    if not _model_loaded:
        error_return["error"] = "Model not loaded. Please run Colab training first."
        return error_return

    if not text or len(text.strip()) < 10:
        error_return["error"] = "Text too short to classify."
        return error_return

    try:
        chunks = _chunk_text(text)
        if not chunks:
            error_return["error"] = "Could not split text into chunks."
            return error_return

        chunking_used = len(chunks) > 1
        all_probs = []

        with torch.no_grad():
            for chunk in chunks:
                inputs = tokenizer(
                    chunk,
                    max_length=512,
                    truncation=True,
                    padding=True,
                    return_tensors="pt"
                ).to(device)

                outputs = model(**inputs)
                probs = F.softmax(outputs.logits, dim=-1)
                all_probs.append(probs)

        avg_probs = torch.mean(torch.cat(all_probs, dim=0), dim=0)
        predicted_class = torch.argmax(avg_probs).item()
        confidence = avg_probs[predicted_class].item() * 100

        scores = {
            "LEFT": round(avg_probs[0].item() * 100, 2),
            "CENTER": round(avg_probs[1].item() * 100, 2),
            "RIGHT": round(avg_probs[2].item() * 100, 2)
        }

        return {
            "label": id2label[predicted_class],
            "confidence": round(confidence, 2),
            "scores": scores,
            "chunking_used": chunking_used,
            "error": None
        }

    except Exception as e:
        error_return["error"] = f"Classification error: {str(e)}"
        return error_return


def get_classifier_pipeline():
    global _pipeline
    if not _model_loaded:
        return None
    if _pipeline is None:
        try:
            _pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                return_all_scores=True,
                device=0 if torch.cuda.is_available() else -1
            )
        except Exception as e:
            print(f"Pipeline creation error: {str(e)}")
            return None
    return _pipeline


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING BIAS CLASSIFIER")
    print("="*55)

    tests = [
        {
            "name": "Test 1 — LEFT leaning",
            "text": "The Republican party has once again failed working class Americans by cutting social programs and giving tax breaks to billionaires while ordinary families struggle to survive"
        },
        {
            "name": "Test 2 — RIGHT leaning",
            "text": "The radical left Democrats are pushing socialist agendas that will destroy small businesses and take away the freedoms that Americans have fought for"
        },
        {
            "name": "Test 3 — CENTER/neutral",
            "text": "The Senate passed the infrastructure bill today with votes from both parties. The bill includes funding for roads, bridges and broadband internet"
        },
        {
            "name": "Test 4 — Long article (chunking test)",
            "text": "The Republican party has once again failed working class Americans by cutting social programs and giving tax breaks to billionaires while ordinary families struggle to survive " * 10
        }
    ]

    all_passed = True
    for test in tests:
        print(f"\n{test['name']}")
        result = classify_bias(test["text"])
        if result["error"]:
            print(f"  ERROR: {result['error']}")
            all_passed = False
        else:
            print(f"  Label     : {result['label']}")
            print(f"  Confidence: {result['confidence']}%")
            print(f"  Scores    : LEFT={result['scores']['LEFT']}% CENTER={result['scores']['CENTER']}% RIGHT={result['scores']['RIGHT']}%")
            print(f"  Chunking  : {'Yes' if result.get('chunking_used') else 'No'}")

    print("\n" + "="*55)
    if all_passed:
        print("BIAS CLASSIFIER WORKING CORRECTLY")
    else:
        print("SOME TESTS FAILED — check errors above")
    print("="*55)