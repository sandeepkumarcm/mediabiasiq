import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.article_scraper import scrape_article
from model.bias_classifier import classify_bias
from model.extra_classifier import detect_extra_bias
from explainability.shap_explainer import get_biased_sentences
from credibility.source_checker import check_source_credibility


def _analyze_single_article(url: str) -> dict:
    # Step 1 — Scrape
    scraped = scrape_article(url)
    if scraped.get("error"):
        return {
            "url": url,
            "error": f"Could not scrape article: {scraped['error']}"
        }

    title = scraped.get("title") or ""
    text = scraped.get("text") or ""
    word_count = scraped.get("word_count", 0)

    if not text or len(text.strip()) < 100:
        return {
            "url": url,
            "error": "Article text too short or empty after scraping"
        }

    # Step 2 — Classify bias
    bias_result = classify_bias(text)

    # Step 3 — Extra classifier
    extra_result = detect_extra_bias(title, text)

    # Step 4 — Biased sentences
    biased_sentences = get_biased_sentences(text, top_n=3)

    # Step 5 — Source credibility
    credibility_result = check_source_credibility(url)

    return {
        "url": url,
        "title": title,
        "text": text,
        "word_count": word_count,
        "bias_label": bias_result.get("label", "UNKNOWN"),
        "bias_confidence": bias_result.get("confidence", 0),
        "bias_scores": bias_result.get("scores", {"LEFT": 0, "CENTER": 0, "RIGHT": 0}),
        "fear_detected": extra_result.get("fear_detected", False),
        "fear_score": extra_result.get("fear_score", 0),
        "clickbait_detected": extra_result.get("clickbait_detected", False),
        "clickbait_score": extra_result.get("clickbait_score", 0),
        "top_biased_sentences": biased_sentences,
        "source_domain": credibility_result.get("domain", ""),
        "allsides_rating": credibility_result.get("allsides_rating", None),
        "error": None
    }


def _generate_verdict(article1: dict, article2: dict) -> dict:
    label1 = article1.get("bias_label", "UNKNOWN")
    label2 = article2.get("bias_label", "UNKNOWN")
    conf1 = article1.get("bias_confidence", 0)
    conf2 = article2.get("bias_confidence", 0)
    source1 = article1.get("source_domain", "Source 1")
    source2 = article2.get("source_domain", "Source 2")

    bias_difference = round(abs(conf1 - conf2), 2)

    if conf1 >= conf2:
        more_biased = source1
        less_biased = source2
    else:
        more_biased = source2
        less_biased = source1

    same_direction = label1 == label2

    # Build verdict
    if label1 == label2:
        verdict = (
            f"Both {source1} and {source2} show {label1} bias "
            f"({conf1:.1f}% vs {conf2:.1f}% confidence). They appear "
            f"to share a similar political perspective on this topic."
        )
    elif (label1 == "LEFT" and label2 == "RIGHT") or (label1 == "RIGHT" and label2 == "LEFT"):
        verdict = (
            f"{source1} leans {label1} ({conf1:.1f}% confidence) "
            f"while {source2} leans {label2} ({conf2:.1f}% confidence). "
            f"These sources present significantly different political perspectives "
            f"on this topic. Reading both gives a more complete picture."
        )
    elif label1 == "CENTER" or label2 == "CENTER":
        neutral_source = source1 if label1 == "CENTER" else source2
        biased_source = source2 if label1 == "CENTER" else source1
        biased_label = label2 if label1 == "CENTER" else label1
        biased_conf = conf2 if label1 == "CENTER" else conf1
        neutral_conf = conf1 if label1 == "CENTER" else conf2
        verdict = (
            f"{biased_source} presents this topic with {biased_label} framing "
            f"({biased_conf:.1f}%) while {neutral_source} covers it more neutrally "
            f"({neutral_conf:.1f}%). Consider {neutral_source} for a more balanced view."
        )
    else:
        verdict = (
            f"Both sources present this topic relatively neutrally. "
            f"{source1} scores {conf1:.1f}% center confidence and "
            f"{source2} scores {conf2:.1f}%."
        )

    # Recommendation
    if bias_difference > 40:
        recommendation = "Large bias gap detected. These sources tell very different versions of this story."
    elif bias_difference > 20:
        recommendation = "Moderate bias difference. Cross-reference these sources for a balanced view."
    else:
        recommendation = "Similar bias levels. Both sources lean in the same general direction."

    return {
        "verdict": verdict,
        "more_biased_source": more_biased,
        "less_biased_source": less_biased,
        "bias_difference": bias_difference,
        "same_direction": same_direction,
        "recommendation": recommendation
    }


def compare_articles(url1: str, url2: str) -> dict:
    error_return = {
        "article1": None,
        "article2": None,
        "verdict": None,
        "comparison_summary": None,
        "error": None
    }

    if not url1 or not url2:
        error_return["error"] = "Both URLs are required"
        return error_return

    if url1 == url2:
        print("Warning: Both URLs are identical — comparing same article to itself")

    print("Analyzing Article 1...")
    article1 = _analyze_single_article(url1)
    if article1.get("error"):
        error_return["error"] = f"Article 1 could not be scraped: {article1['error']}"
        return error_return

    print("Analyzing Article 2...")
    article2 = _analyze_single_article(url2)
    if article2.get("error"):
        error_return["error"] = f"Article 2 could not be scraped: {article2['error']}"
        return error_return

    verdict = _generate_verdict(article1, article2)

    source1 = article1.get("source_domain", "Source 1")
    source2 = article2.get("source_domain", "Source 2")
    label1 = article1.get("bias_label", "UNKNOWN")
    label2 = article2.get("bias_label", "UNKNOWN")
    conf1 = article1.get("bias_confidence", 0)
    conf2 = article2.get("bias_confidence", 0)

    comparison_summary = (
        f"{source1}: {label1} ({conf1:.1f}%) vs "
        f"{source2}: {label2} ({conf2:.1f}%)"
    )

    return {
        "article1": article1,
        "article2": article2,
        "verdict": verdict,
        "comparison_summary": comparison_summary,
        "error": None
    }


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING ARTICLE COMPARATOR")
    print("="*55)

    print("""
To test article_comparator.py:
1. Find two news articles on the SAME topic from different sources
2. Recommended pairs:
   - Fox News article vs BBC article on same US political story
   - Times of India vs The Wire on same India story
3. Replace url1 and url2 below with your chosen URLs
4. Run: python comparison/article_comparator.py
    """)

    url1 = "https://www.foxnews.com/politics/exclusive-tulsi-gabbard-resigns-from-trump-cabinet"
    url2 = "https://www.bbc.com/news/articles/cvgj2gkv1x1o"

    if "REPLACE" in url1 or "REPLACE" in url2:
        print("Please replace placeholder URLs with real news URLs before testing")
        print("Edit the url1 and url2 variables at the bottom of this file")
        sys.exit(0)

    result = compare_articles(url1, url2)

    if result["error"]:
        print(f"ERROR: {result['error']}")
    else:
        print(f"\nCOMPARISON SUMMARY:")
        print(f"  {result['comparison_summary']}")

        print(f"\nVERDICT:")
        print(f"  {result['verdict']['verdict']}")

        print(f"\nRECOMMENDATION:")
        print(f"  {result['verdict']['recommendation']}")

        print(f"\nMore biased source: {result['verdict']['more_biased_source']}")
        print(f"Less biased source: {result['verdict']['less_biased_source']}")
        print(f"Bias difference   : {result['verdict']['bias_difference']}%")

        if result["article1"]["top_biased_sentences"]:
            top = result["article1"]["top_biased_sentences"][0]
            print(f"\nArticle 1 most biased sentence:")
            print(f"  {top['sentence'][:100]}...")
            print(f"  Score: {top['bias_score']}% — {top['severity']} — {top['direction']}")

        if result["article2"]["top_biased_sentences"]:
            top = result["article2"]["top_biased_sentences"][0]
            print(f"\nArticle 2 most biased sentence:")
            print(f"  {top['sentence'][:100]}...")
            print(f"  Score: {top['bias_score']}% — {top['severity']} — {top['direction']}")

        print("\nARTICLE COMPARATOR WORKING CORRECTLY")