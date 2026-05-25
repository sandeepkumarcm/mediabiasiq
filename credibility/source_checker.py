import re

# ── AllSides Ratings Database ─────────────────────────────
ALLSIDES_RATINGS = {
    # LEFT sources
    "huffpost.com": "LEFT",
    "motherjones.com": "LEFT",
    "thenation.com": "LEFT",
    "vox.com": "LEFT",
    "slate.com": "LEFT",
    "theguardian.com": "LEFT",
    "buzzfeednews.com": "LEFT",
    "newrepublic.com": "LEFT",
    "thewire.in": "LEFT",
    "theintercept.com": "LEFT",
    "democracynow.org": "LEFT",
    "jacobinmag.com": "LEFT",
    "alternet.org": "LEFT",

    # CENTER-LEFT sources
    "nytimes.com": "CENTER-LEFT",
    "washingtonpost.com": "CENTER-LEFT",
    "cnn.com": "CENTER-LEFT",
    "msnbc.com": "CENTER-LEFT",
    "nbcnews.com": "CENTER-LEFT",
    "time.com": "CENTER-LEFT",
    "theatlantic.com": "CENTER-LEFT",
    "politico.com": "CENTER-LEFT",
    "ndtv.com": "CENTER-LEFT",
    "thehindu.com": "CENTER-LEFT",
    "abcnews.go.com": "CENTER-LEFT",
    "cbsnews.com": "CENTER-LEFT",

    # CENTER sources
    "reuters.com": "CENTER",
    "apnews.com": "CENTER",
    "bbc.com": "CENTER",
    "bbc.co.uk": "CENTER",
    "pbs.org": "CENTER",
    "thehill.com": "CENTER",
    "csmonitor.com": "CENTER",
    "hindustantimes.com": "CENTER",
    "livemint.com": "CENTER",
    "scroll.in": "CENTER",
    "business-standard.com": "CENTER",
    "theprint.in": "CENTER",
    "factcheck.org": "CENTER",

    # CENTER-RIGHT sources
    "wsj.com": "CENTER-RIGHT",
    "economist.com": "CENTER-RIGHT",
    "forbes.com": "CENTER-RIGHT",
    "usatoday.com": "CENTER-RIGHT",
    "newsweek.com": "CENTER-RIGHT",
    "timesofindia.com": "CENTER-RIGHT",
    "economictimes.indiatimes.com": "CENTER-RIGHT",
    "financialexpress.com": "CENTER-RIGHT",
    "reason.com": "CENTER-RIGHT",
    "nationalreview.com": "CENTER-RIGHT",

    # RIGHT sources
    "foxnews.com": "RIGHT",
    "breitbart.com": "RIGHT",
    "nypost.com": "RIGHT",
    "dailywire.com": "RIGHT",
    "washingtonexaminer.com": "RIGHT",
    "republicworld.com": "RIGHT",
    "opindia.com": "RIGHT",
    "swarajyamag.com": "RIGHT",
    "zeenews.india.com": "RIGHT",
    "news18.com": "RIGHT",
    "oann.com": "RIGHT",
    "thedailycaller.com": "RIGHT",
}

# ── Readable source names ─────────────────────────────────
SOURCE_NAMES = {
    "huffpost.com": "HuffPost",
    "motherjones.com": "Mother Jones",
    "thenation.com": "The Nation",
    "vox.com": "Vox",
    "slate.com": "Slate",
    "theguardian.com": "The Guardian",
    "buzzfeednews.com": "BuzzFeed News",
    "newrepublic.com": "New Republic",
    "thewire.in": "The Wire",
    "theintercept.com": "The Intercept",
    "nytimes.com": "New York Times",
    "washingtonpost.com": "Washington Post",
    "cnn.com": "CNN",
    "msnbc.com": "MSNBC",
    "nbcnews.com": "NBC News",
    "time.com": "TIME",
    "theatlantic.com": "The Atlantic",
    "politico.com": "Politico",
    "ndtv.com": "NDTV",
    "thehindu.com": "The Hindu",
    "reuters.com": "Reuters",
    "apnews.com": "AP News",
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
    "pbs.org": "PBS",
    "thehill.com": "The Hill",
    "csmonitor.com": "Christian Science Monitor",
    "hindustantimes.com": "Hindustan Times",
    "livemint.com": "Livemint",
    "scroll.in": "Scroll",
    "business-standard.com": "Business Standard",
    "wsj.com": "Wall Street Journal",
    "economist.com": "The Economist",
    "forbes.com": "Forbes",
    "usatoday.com": "USA Today",
    "newsweek.com": "Newsweek",
    "timesofindia.com": "Times of India",
    "economictimes.indiatimes.com": "Economic Times",
    "financialexpress.com": "Financial Express",
    "foxnews.com": "Fox News",
    "breitbart.com": "Breitbart",
    "nypost.com": "New York Post",
    "dailywire.com": "Daily Wire",
    "washingtonexaminer.com": "Washington Examiner",
    "republicworld.com": "Republic World",
    "opindia.com": "OpIndia",
    "swarajyamag.com": "Swarajya Mag",
    "zeenews.india.com": "Zee News",
    "news18.com": "News18",
}


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    try:
        url = url.strip().lower()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        domain = url.split('/')[0]
        domain = domain.split('?')[0]
        domain = domain.split('#')[0]
        return domain.strip()
    except Exception:
        return ""


def check_source_credibility(url: str) -> dict:
    domain = _extract_domain(url)

    if not domain:
        return {
            "domain": "",
            "source_name": "Unknown Source",
            "allsides_rating": None,
            "found_in_database": False,
            "database_size": len(ALLSIDES_RATINGS)
        }

    # Direct lookup
    if domain in ALLSIDES_RATINGS:
        return {
            "domain": domain,
            "source_name": SOURCE_NAMES.get(domain, domain.title()),
            "allsides_rating": ALLSIDES_RATINGS[domain],
            "found_in_database": True,
            "database_size": len(ALLSIDES_RATINGS)
        }

    # Try removing subdomain
    parts = domain.split('.')
    if len(parts) > 2:
        base_domain = '.'.join(parts[-2:])
        if base_domain in ALLSIDES_RATINGS:
            return {
                "domain": domain,
                "source_name": SOURCE_NAMES.get(base_domain, base_domain.title()),
                "allsides_rating": ALLSIDES_RATINGS[base_domain],
                "found_in_database": True,
                "database_size": len(ALLSIDES_RATINGS)
            }

    return {
        "domain": domain,
        "source_name": "Unknown Source",
        "allsides_rating": None,
        "found_in_database": False,
        "database_size": len(ALLSIDES_RATINGS)
    }


def get_credibility_verdict(model_label: str, credibility_result: dict) -> dict:
    if not credibility_result.get("found_in_database"):
        return {
            "verdict": "UNVERIFIED SOURCE",
            "explanation": "This source is not in our database. Model prediction cannot be cross-validated.",
            "confidence": "LOW",
            "model_prediction": model_label,
            "allsides_rating": None,
            "agree": False
        }

    allsides_rating = credibility_result.get("allsides_rating", "")
    model_label = model_label.upper() if model_label else ""

    agree_rules = [
        ("LEFT", "LEFT"),
        ("LEFT", "CENTER-LEFT"),
        ("CENTER", "CENTER"),
        ("CENTER", "CENTER-LEFT"),
        ("CENTER", "CENTER-RIGHT"),
        ("RIGHT", "RIGHT"),
        ("RIGHT", "CENTER-RIGHT"),
    ]

    agree = (model_label, allsides_rating) in agree_rules

    if agree:
        return {
            "verdict": "HIGH CONFIDENCE",
            "explanation": (
                f"Both our AI model and AllSides database agree this source leans "
                f"{allsides_rating}. This prediction is highly reliable."
            ),
            "confidence": "HIGH",
            "model_prediction": model_label,
            "allsides_rating": allsides_rating,
            "agree": True
        }
    else:
        return {
            "verdict": "CONFLICTING SIGNALS",
            "explanation": (
                f"Our model predicts {model_label} but AllSides rates this source as "
                f"{allsides_rating}. Read this article with extra critical thinking."
            ),
            "confidence": "MEDIUM",
            "model_prediction": model_label,
            "allsides_rating": allsides_rating,
            "agree": False
        }


def get_all_sources() -> dict:
    return ALLSIDES_RATINGS


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING SOURCE CHECKER")
    print("="*55)

    tests = [
        {"url": "https://www.bbc.com/news/world", "expect_rating": "CENTER", "expect_found": True},
        {"url": "https://www.foxnews.com/politics/story", "expect_rating": "RIGHT", "expect_found": True},
        {"url": "https://www.reuters.com/world/", "expect_rating": "CENTER", "expect_found": True},
        {"url": "https://www.ndtv.com/india-news/story", "expect_rating": "CENTER-LEFT", "expect_found": True},
        {"url": "https://www.somerandomblog.com/article", "expect_rating": None, "expect_found": False},
    ]

    all_passed = True

    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}: {test['url']}")
        result = check_source_credibility(test["url"])
        print(f"  Domain        : {result['domain']}")
        print(f"  Source Name   : {result['source_name']}")
        print(f"  AllSides Rating: {result['allsides_rating']}")
        print(f"  Found in DB   : {result['found_in_database']}")

        if (result["allsides_rating"] == test["expect_rating"] and
                result["found_in_database"] == test["expect_found"]):
            print("  Result: PASS ✅")
        else:
            print("  Result: FAIL ❌")
            all_passed = False

    # Test 6 — HIGH CONFIDENCE verdict
    print("\nTest 6: BBC + model predicts CENTER")
    bbc_result = check_source_credibility("https://www.bbc.com/news")
    verdict = get_credibility_verdict("CENTER", bbc_result)
    print(f"  Verdict     : {verdict['verdict']}")
    print(f"  Explanation : {verdict['explanation']}")
    print(f"  Confidence  : {verdict['confidence']}")
    if verdict["verdict"] == "HIGH CONFIDENCE":
        print("  Result: PASS ✅")
    else:
        print("  Result: FAIL ❌")
        all_passed = False

    # Test 7 — CONFLICTING SIGNALS verdict
    print("\nTest 7: Fox News + model predicts LEFT")
    fox_result = check_source_credibility("https://www.foxnews.com/politics")
    verdict = get_credibility_verdict("LEFT", fox_result)
    print(f"  Verdict     : {verdict['verdict']}")
    print(f"  Explanation : {verdict['explanation']}")
    print(f"  Confidence  : {verdict['confidence']}")
    if verdict["verdict"] == "CONFLICTING SIGNALS":
        print("  Result: PASS ✅")
    else:
        print("  Result: FAIL ❌")
        all_passed = False

    print("\n" + "="*55)
    if all_passed:
        print("SOURCE CHECKER WORKING CORRECTLY")
    else:
        print("SOME TESTS FAILED — check above")
    print("="*55)