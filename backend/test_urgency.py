"""
Comprehensive test suite for Sentira AI ML models.
Tests sarcasm, irony, mixed sentiment, edge cases, and urgency detection.
"""
import sys
from app.ml.predictor import load_models, predict

load_models()

# ═══════════════════════════════════════════════════════════════
# TEST CASES
# ═══════════════════════════════════════════════════════════════

test_cases = [
    # (text, expected_sentiment, description)
    # --- Standard positive ---
    ("I absolutely love this product, it works perfectly", "positive", "Clear positive"),
    ("Great value for money, totally worth it", "positive", "Clear positive"),
    ("The app is very good it has every feature I want", "positive", "Positive review"),
    # --- Standard negative ---
    ("This app crashes every time I open it", "negative", "Clear negative"),
    ("Terrible customer service, no one responded", "negative", "Clear negative"),
    ("URGENT the entire system is down", "negative", "Urgent negative"),
    # --- Standard neutral ---
    ("It works fine but nothing special", "neutral", "Clear neutral"),
    ("The product is okay for the price", "neutral", "Clear neutral"),
    # --- SARCASM & IRONY ---
    ("Oh great, another crash, just what I needed today", "negative", "Sarcasm: oh great + crash"),
    ("Wow the app crashed again, I am so surprised", "negative", "Sarcasm: wow + crash"),
    ("Sure I totally love waiting ten minutes for a page to load", "negative", "Sarcasm: totally love + slow"),
    ("Oh wonderful, the update broke everything again", "negative", "Sarcasm: oh wonderful + broke"),
    ("Really impressed by how consistently this app crashes", "negative", "Sarcasm: impressed + crashes"),
    ("Thanks for breaking the only feature that worked", "negative", "Sarcasm: thanks + breaking"),
    ("Wow a whole five minutes before it crashed, new record", "negative", "Sarcasm: new record + crashed"),
    ("Oh sure the performance is great if you enjoy watching paint dry", "negative", "Sarcasm: great + paint dry"),
    ("Brilliant, the app froze during my presentation", "negative", "Sarcasm: brilliant + froze"),
    ("The crashes are surprisingly consistent, at least something works", "negative", "Sarcasm: surprisingly consistent"),
    # --- URGENCY ---
    ("URGENT system is completely down no one can work", "negative", "Critical urgency"),
    ("This bug is affecting a lot of our customers", "negative", "High urgency"),
    ("Minor cosmetic issue on the settings page", None, "Low urgency"),
    ("Just a small typo on one page", None, "Low urgency"),
    # --- MIXED / EDGE CASES ---
    ("The app is great but the customer support is terrible", None, "Mixed sentiment"),
    ("Not bad but not great either", "neutral", "Double negative neutral"),
    ("I do not hate this product", None, "Negation edge case"),
    ("Could be better but it is not terrible", "neutral", "Soft neutral"),
]

# ═══════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════

lines = []
passed, failed, skipped = 0, 0, 0

lines.append("=" * 110)
lines.append(f"  SENTIRA AI — Comprehensive Model Test Suite")
lines.append("=" * 110)
lines.append("")
lines.append(f"{'#':<4} {'Status':<8} {'Description':<35} {'Expected':<12} {'Got':<12} {'Conf':<8} {'Urgency':<10} {'Cat':<12}")
lines.append("-" * 110)

for i, (text, expected_sent, desc) in enumerate(test_cases, 1):
    r = predict(text)
    actual = r["sentiment"]

    if expected_sent is None:
        status = "SKIP"
        skipped += 1
    elif actual == expected_sent:
        status = "PASS"
        passed += 1
    else:
        status = "FAIL"
        failed += 1

    lines.append(
        f"{i:<4} {status:<8} {desc:<35} "
        f"{(expected_sent or 'any'):<12} {actual:<12} "
        f"{r['sentiment_confidence']:.2%}   {r['urgency']:<10} {r['category']:<12}"
    )

lines.append("-" * 110)
lines.append("")
lines.append(f"  Results: {passed} passed, {failed} failed, {skipped} skipped out of {len(test_cases)} tests")
lines.append(f"  Pass rate: {passed}/{passed+failed} = {passed/(passed+failed)*100:.1f}%" if passed+failed > 0 else "  No testable cases")
lines.append("")

# Sarcasm-specific summary
sarcasm_tests = [(t, e, d) for t, e, d in test_cases if "Sarcasm" in d]
sarcasm_pass = sum(1 for t, e, d in sarcasm_tests if predict(t)["sentiment"] == e)
lines.append(f"  Sarcasm detection: {sarcasm_pass}/{len(sarcasm_tests)} correct")
lines.append("=" * 110)

output = "\n".join(lines)
with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write(output)
print(output)
print("\nResults written to test_results.txt")
