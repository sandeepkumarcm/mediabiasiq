import re

# ── Fear Words List ───────────────────────────────────────
FEAR_WORDS = [
    # Disaster words
    "crisis", "disaster", "catastrophe", "catastrophic", "collapse",
    "devastating", "devastation", "destruction", "carnage", "massacre",
    # Threat words
    "threat", "threatening", "danger", "dangerous", "alarming",
    "alarmed", "emergency", "urgent", "warning", "severe",
    # Emotional shock words
    "shocking", "horrifying", "terrifying", "terrified", "nightmare",
    "brutal", "horrific", "appalling", "outrageous", "disgraceful",
    # Extreme words
    "extreme", "radical", "explosive", "violent", "chaos", "panic",
    "invasion", "attack", "weapons", "warfare",
    # Extra fear words
    "catastrophically", "deadly", "fatal", "killed", "murder",
    "genocide", "terrorism", "terrorist", "bomb", "nuclear",
    "epidemic", "pandemic", "outbreak", "contamination", "poison"
]

# ── Clickbait Patterns ────────────────────────────────────
CLICKBAIT_PATTERNS = [
    r"you won'?t believe",
    r"what happened next",
    r"the truth about",
    r"nobody is talking about",
    r"what they don'?t want you to know",
    r"the real reason",
    r"here'?s why",
    r"this is why",
    r"will shock you",
    r"left people speechless",
    r"breaks the internet",
    r"goes viral",
    r"changed forever",
    r"never be the same",
    r"doctors hate",
    r"one weird trick",
    r"scientists discover",
    r"\d+\s+reasons why",
    r"\d+\s+things",
    r"\d+\s+ways to",
    r"\d+\s+secrets",
    r"\bbreaking\b",
    r"\burgent\b",
    r"\balert\b",
    r"developing story",
    r"just in",
    r"happening now",
    r"you need to know",
    r"this will change",
    r"must see",
    r"mind blowing",
    r"jaw dropping"
]


def _calculate_fear_score(text: str) -> dict:
    if not text:
        return {"score": 0.0, "triggers": []}

    text_lower = text.lower()
    triggers = []

    for word in FEAR_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            triggers.append(word)

    unique_count = len(triggers)
    score = min((unique_count / 10) * 100, 100)

    return {"score": round(score, 2), "triggers": triggers}


def _calculate_clickbait_score(title: str, text: str) -> dict:
    if not title:
        title = ""
    if not text:
        text = ""

    title_lower = title.lower()
    text_lower = text.lower()
    triggers = []

    for pattern in CLICKBAIT_PATTERNS:
        try:
            title_match = re.search(pattern, title_lower)
            text_match = re.search(pattern, text_lower)
            if title_match:
                triggers.append(pattern)
            elif text_match:
                triggers.append(pattern)
        except re.error:
            continue

    unique_count = len(triggers)
    score = min(unique_count * 25, 100)

    return {"score": round(score, 2), "triggers": triggers}


def detect_extra_bias(title: str, text: str) -> dict:
    if not title:
        title = ""
    if not text:
        text = ""

    combined_text = title + " " + text

    fear_result = _calculate_fear_score(combined_text)
    clickbait_result = _calculate_clickbait_score(title, text)

    fear_score = fear_result["score"]
    clickbait_score = clickbait_result["score"]

    fear_detected = fear_score >= 40
    clickbait_detected = clickbait_score >= 35

    labels = []
    if fear_detected:
        labels.append("FEAR-MONGERING")
    if clickbait_detected:
        labels.append("CLICKBAIT")
    if not labels:
        labels.append("NONE")

    return {
        "labels": labels,
        "fear_score": fear_score,
        "clickbait_score": clickbait_score,
        "fear_triggers": fear_result["triggers"],
        "clickbait_triggers": clickbait_result["triggers"],
        "fear_detected": fear_detected,
        "clickbait_detected": clickbait_detected
    }


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING EXTRA CLASSIFIER")
    print("="*55)

    tests = [
        {
            "name": "Test 1 — Clear fear-mongering",
            "title": "CATASTROPHIC Crisis Will DESTROY Everything You Love",
            "text": "Alarming reports show dangerous and threatening situation is causing panic and chaos across the nation as experts warn of devastating collapse",
            "expect_fear": True,
            "expect_clickbait": False
        },
        {
            "name": "Test 2 — Clear clickbait",
            "title": "You Won't Believe What Doctors Found — 10 Secrets They Don't Want You To Know",
            "text": "Scientists discover one weird trick that changed everything forever",
            "expect_fear": False,
            "expect_clickbait": True
        },
        {
            "name": "Test 3 — Both fear and clickbait",
            "title": "SHOCKING: You Won't Believe This Catastrophic Disaster That Will Destroy Everything",
            "text": "Alarming and dangerous situation developing as experts warn this is urgent breaking news",
            "expect_fear": True,
            "expect_clickbait": True
        },
        {
            "name": "Test 4 — Neutral article",
            "title": "Senate passes infrastructure bill with bipartisan support",
            "text": "The Senate voted today to approve a new infrastructure package. The bill received support from both parties and will fund road and bridge repairs across the country",
            "expect_fear": False,
            "expect_clickbait": False
        },
        {
            "name": "Test 5 — Breaking news",
            "title": "Breaking: President signs new climate bill",
            "text": "The president signed the climate protection act into law this morning at the White House",
            "expect_fear": False,
            "expect_clickbait": False
        }
    ]

    all_passed = True

    for test in tests:
        print(f"\n{test['name']}")
        result = detect_extra_bias(test["title"], test["text"])

        print(f"  Labels          : {result['labels']}")
        print(f"  Fear Score      : {result['fear_score']}%")
        print(f"  Fear Triggers   : {result['fear_triggers']}")
        print(f"  Clickbait Score : {result['clickbait_score']}%")
        print(f"  Clickbait Triggers: {result['clickbait_triggers']}")

        fear_ok = result["fear_detected"] == test["expect_fear"]
        clickbait_ok = result["clickbait_detected"] == test["expect_clickbait"]

        if fear_ok and clickbait_ok:
            print("  Result: PASS ✅")
        else:
            print("  Result: FAIL ❌")
            if not fear_ok:
                print(f"  Expected fear_detected={test['expect_fear']} but got {result['fear_detected']}")
            if not clickbait_ok:
                print(f"  Expected clickbait_detected={test['expect_clickbait']} but got {result['clickbait_detected']}")
            all_passed = False

    print("\n" + "="*55)
    if all_passed:
        print("EXTRA CLASSIFIER WORKING CORRECTLY")
    else:
        print("SOME TESTS FAILED — check above")
    print("="*55)