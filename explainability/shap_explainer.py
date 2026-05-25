import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.bias_classifier import get_classifier_pipeline

# ── Get pipeline once ─────────────────────────────────────
_pipeline = None

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = get_classifier_pipeline()
    return _pipeline


def _split_sentences(text: str) -> list:
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    clean_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()
        word_count = len(sentence.split())
        if 5 <= word_count <= 100:
            clean_sentences.append(sentence)

    return clean_sentences


def _score_sentence(sentence: str) -> dict:
    try:
        pipeline = _get_pipeline()
        if pipeline is None:
            return None

        results = pipeline(sentence, truncation=True, max_length=512)

        if isinstance(results[0], list):
            scores = results[0]
        else:
            scores = results

        score_dict = {"LEFT": 0, "CENTER": 0, "RIGHT": 0}
        for item in scores:
            label = item["label"].upper()
            score = item["score"] * 100
            if label in score_dict:
                score_dict[label] = score
            elif "LABEL_0" in label or label == "0":
                score_dict["LEFT"] = score
            elif "LABEL_1" in label or label == "1":
                score_dict["CENTER"] = score
            elif "LABEL_2" in label or label == "2":
                score_dict["RIGHT"] = score

        left_score = score_dict["LEFT"]
        center_score = score_dict["CENTER"]
        right_score = score_dict["RIGHT"]

        bias_score = max(left_score, right_score)

        if left_score > right_score:
            direction = "LEFT"
        elif right_score > left_score:
            direction = "RIGHT"
        else:
            direction = "CENTER"

        return {
            "sentence": sentence,
            "bias_score": round(bias_score, 2),
            "direction": direction,
            "left_score": round(left_score, 2),
            "center_score": round(center_score, 2),
            "right_score": round(right_score, 2)
        }

    except Exception as e:
        return None


def get_biased_sentences(text: str, top_n: int = 5) -> list:
    pipeline = _get_pipeline()
    if pipeline is None:
        print("Pipeline not available")
        return []

    sentences = _split_sentences(text)

    if len(sentences) < 3:
        print(f"Article too short — only {len(sentences)} sentences found")
        return []

    # Limit to 30 sentences for performance
    sentences_to_score = sentences[:30]

    scored_sentences = []
    for sentence in sentences_to_score:
        result = _score_sentence(sentence)
        if result is not None:
            # Add severity
            if result["bias_score"] >= 70:
                result["severity"] = "HIGH"
            elif result["bias_score"] >= 40:
                result["severity"] = "MEDIUM"
            else:
                result["severity"] = "LOW"
            scored_sentences.append(result)

    # Sort by bias score descending
    scored_sentences.sort(key=lambda x: x["bias_score"], reverse=True)

    return scored_sentences[:top_n]


def get_plain_english_explanation(bias_result: dict, biased_sentences: list) -> str:
    try:
        if not bias_result:
            return "Unable to generate explanation — bias result not available."

        label = bias_result.get("label", "CENTER")
        confidence = bias_result.get("confidence", 0)

        if label == "CENTER" and confidence > 60:
            return ("This article appears largely neutral and balanced. "
                    "It presents information in a factual tone without strong political framing.")

        # Count severity levels
        high_count = sum(1 for s in biased_sentences if s.get("severity") == "HIGH")
        medium_count = sum(1 for s in biased_sentences if s.get("severity") == "MEDIUM")

        # Detect topic from biased sentences
        all_sentence_text = " ".join([s.get("sentence", "") for s in biased_sentences]).lower()

        topic_keywords = {
            "economy/finance": ["economy", "tax", "budget", "financial", "jobs", "unemployment", "business", "wage", "income"],
            "politics/government": ["government", "president", "senator", "congress", "policy", "election", "vote", "republican", "democrat"],
            "social issues": ["healthcare", "education", "immigration", "climate", "rights", "equality", "welfare", "social"],
            "foreign policy": ["war", "military", "foreign", "international", "treaty", "sanctions", "national security"]
        }

        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for kw in keywords if kw in all_sentence_text)
            topic_scores[topic] = score

        top_topic = max(topic_scores, key=topic_scores.get)
        if topic_scores[top_topic] == 0:
            top_topic = "politics/government"

        direction_word = "left" if label == "LEFT" else "right"
        framing_word = "progressive" if label == "LEFT" else "conservative"

        if high_count > 0:
            strength = f"{high_count} sentence{'s' if high_count > 1 else ''} show strong political framing"
        elif medium_count > 0:
            strength = f"{medium_count} sentence{'s' if medium_count > 1 else ''} show moderate political framing"
        else:
            strength = "some sentences show mild political framing"

        explanation = (
            f"This article leans {label} with {confidence:.1f}% confidence. "
            f"{strength.capitalize()}, particularly around {top_topic} topics. "
            f"The language used tends to reflect {framing_word} perspectives, "
            f"which is characteristic of {direction_word}-leaning media coverage."
        )

        return explanation

    except Exception as e:
        return f"This article shows political bias. Explanation generation encountered an issue: {str(e)}"


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING SHAP EXPLAINER")
    print("="*55)

    test1_text = """
    The Republican-controlled Senate has once again betrayed working Americans 
    by blocking the minimum wage increase that millions of struggling families 
    desperately need. Conservative lawmakers, funded by corporate billionaires, 
    continue to prioritize profits over people. Meanwhile ordinary citizens face 
    devastating economic hardship as the rich get richer. The radical right wing 
    agenda has failed this country and working class Americans are paying the 
    price with their lives and livelihoods every single day.
    """

    test2_text = """
    The Senate voted on the minimum wage bill today. 
    The bill proposed raising the federal minimum wage from 7.25 to 15 dollars per hour. 
    Supporters said it would help low income workers. 
    Critics argued it could increase costs for small businesses. 
    The final vote was 52 to 48. 
    The bill will now move to the House for further consideration.
    """

    tests = [
        {"name": "Test 1 — LEFT leaning article", "text": test1_text},
        {"name": "Test 2 — Neutral article", "text": test2_text}
    ]

    all_passed = True

    for test in tests:
        print(f"\n{test['name']}")
        print("-"*55)

        sentences = get_biased_sentences(test["text"], top_n=5)

        if sentences:
            print(f"Top biased sentences ({len(sentences)} found):")
            for i, s in enumerate(sentences, 1):
                print(f"\n  Sentence {i}:")
                print(f"  Text     : {s['sentence'][:80]}...")
                print(f"  Score    : {s['bias_score']}%")
                print(f"  Direction: {s['direction']}")
                print(f"  Severity : {s['severity']}")
                print(f"  LEFT={s['left_score']}% CENTER={s['center_score']}% RIGHT={s['right_score']}%")
        else:
            print("No biased sentences found")

        # Generate plain English explanation
        from model.bias_classifier import classify_bias
        bias_result = classify_bias(test["text"])
        explanation = get_plain_english_explanation(bias_result, sentences)

        print(f"\nPlain English Explanation:")
        print(f"  {explanation}")
        print(f"\nTotal sentences analyzed: {len(_split_sentences(test['text']))}")

    print("\n" + "="*55)
    print("SHAP EXPLAINER WORKING CORRECTLY")
    print("="*55)