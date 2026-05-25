import difflib
import re

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "and", "but", "or", "nor", "for", "yet", "so", "in", "on",
    "at", "to", "of", "with", "by", "from", "up", "about", "into",
    "through", "after", "over", "between", "out", "against", "that",
    "this", "it", "its", "their", "they", "them", "he", "she", "his",
    "her", "we", "our", "you", "your", "i", "my", "me", "as", "if",
    "not", "also", "just", "than", "then", "when", "where", "which",
    "who", "what", "how", "all", "more", "most", "some", "such", "no"
}


def generate_diff(original_text: str, neutral_text: str) -> list:
    if not original_text or not neutral_text:
        return []

    original_text = original_text.strip()
    neutral_text = neutral_text.strip()

    if original_text == neutral_text:
        return [{"type": "same", "text": "No changes detected"}]

    original_lines = [line.strip() for line in original_text.splitlines() if line.strip()]
    neutral_lines = [line.strip() for line in neutral_text.splitlines() if line.strip()]

    diff = list(difflib.unified_diff(
        original_lines,
        neutral_lines,
        lineterm=""
    ))

    blocks = []
    for line in diff:
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        elif line.startswith("-"):
            text = line[1:].strip()
            if text:
                blocks.append({"type": "removed", "text": text})
        elif line.startswith("+"):
            text = line[1:].strip()
            if text:
                blocks.append({"type": "added", "text": text})
        elif line.startswith(" "):
            text = line[1:].strip()
            if text:
                blocks.append({"type": "same", "text": text})

    return blocks[:60]


def get_diff_stats(diff_blocks: list) -> dict:
    if not diff_blocks:
        return {
            "total_blocks": 0,
            "lines_removed": 0,
            "lines_added": 0,
            "lines_same": 0,
            "total_changes": 0,
            "percent_changed": 0.0,
            "summary": "No diff data available"
        }

    total_blocks = len(diff_blocks)
    lines_removed = sum(1 for b in diff_blocks if b["type"] == "removed")
    lines_added = sum(1 for b in diff_blocks if b["type"] == "added")
    lines_same = sum(1 for b in diff_blocks if b["type"] == "same")
    total_changes = lines_removed + lines_added

    if total_blocks > 0:
        percent_changed = round((total_changes / total_blocks) * 100, 1)
    else:
        percent_changed = 0.0

    summary = (
        f"{total_changes} lines changed ({percent_changed}% of article). "
        f"{lines_removed} lines removed, {lines_added} lines added."
    )

    return {
        "total_blocks": total_blocks,
        "lines_removed": lines_removed,
        "lines_added": lines_added,
        "lines_same": lines_same,
        "total_changes": total_changes,
        "percent_changed": percent_changed,
        "summary": summary
    }


def get_word_diff(original_text: str, neutral_text: str) -> dict:
    if not original_text:
        original_text = ""
    if not neutral_text:
        neutral_text = ""

    def extract_words(text):
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return set(w for w in words if w not in STOPWORDS and len(w) > 2)

    original_words = extract_words(original_text)
    neutral_words = extract_words(neutral_text)

    removed_words = original_words - neutral_words
    added_words = neutral_words - original_words

    def count_occurrences(words, text):
        text_lower = text.lower()
        return sorted(words, key=lambda w: text_lower.count(w), reverse=True)

    top_removed = count_occurrences(removed_words, original_text)[:10]
    top_added = count_occurrences(added_words, neutral_text)[:10]

    return {
        "top_removed_words": top_removed,
        "top_added_words": top_added,
        "total_words_removed": len(removed_words),
        "total_words_added": len(added_words)
    }


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  TESTING DIFF GENERATOR")
    print("="*55)

    original1 = """
    The heartless Republican politicians have once again betrayed struggling Americans. 
    These corrupt lawmakers funded by greedy billionaires continue their ruthless war on the poor. 
    The devastating impact of their cruel policies destroys lives.
    """

    neutral1 = """
    Republican politicians voted against the wage increase bill. 
    Lawmakers cited concerns about economic impacts. 
    Critics argue the decision affects low income Americans. 
    The impact of the policy is being debated.
    """

    original2 = "The president signed the bill today."
    neutral2 = "The president signed the bill today."

    tests = [
        {
            "name": "Test 1 — Clear differences",
            "original": original1,
            "neutral": neutral1,
            "expect_changes": True
        },
        {
            "name": "Test 2 — Identical texts",
            "original": original2,
            "neutral": neutral2,
            "expect_changes": False
        }
    ]

    all_passed = True

    for test in tests:
        print(f"\n{test['name']}")
        print("-"*55)

        diff_blocks = generate_diff(test["original"], test["neutral"])
        stats = get_diff_stats(diff_blocks)
        word_diff = get_word_diff(test["original"], test["neutral"])

        print("DIFF BLOCKS:")
        for block in diff_blocks:
            print(f"  [{block['type']}] {block['text'][:70]}")

        print(f"\nDIFF STATS:")
        print(f"  Total blocks    : {stats['total_blocks']}")
        print(f"  Lines removed   : {stats['lines_removed']}")
        print(f"  Lines added     : {stats['lines_added']}")
        print(f"  Lines same      : {stats['lines_same']}")
        print(f"  Percent changed : {stats['percent_changed']}%")
        print(f"  Summary         : {stats['summary']}")

        print(f"\nWORD DIFF:")
        print(f"  Top removed words : {word_diff['top_removed_words']}")
        print(f"  Top added words   : {word_diff['top_added_words']}")
        print(f"  Total removed     : {word_diff['total_words_removed']}")
        print(f"  Total added       : {word_diff['total_words_added']}")

        if test["expect_changes"] and stats["total_changes"] > 0:
            print("\n  Result: PASS ✅")
        elif not test["expect_changes"] and stats["total_changes"] == 0:
            print("\n  Result: PASS ✅")
        else:
            print("\n  Result: FAIL ❌")
            all_passed = False

    print("\n" + "="*55)
    if all_passed:
        print("DIFF GENERATOR WORKING CORRECTLY")
    else:
        print("SOME TESTS FAILED — check above")
    print("="*55)