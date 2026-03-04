"""
ML Prediction service for Sentira AI — Professional Grade.
Loads trained ensemble models and provides prediction interface
with advanced preprocessing matching the training pipeline.
"""
import os
import re
import joblib
import numpy as np
import difflib

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml_models")

# Global model references
_sentiment_model = None
_category_model = None
_urgency_model = None

# Self-learning cache
# Format: { "processed_text": {"sentiment": s, "category": c, "urgency": u} }
CORRECTION_CACHE = {}

# ════════════════════════════════════════════════════════════════
# PREPROCESSING (must match train.py exactly)
# ════════════════════════════════════════════════════════════════

CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "don't": "do not", "doesn't": "does not",
    "didn't": "did not", "isn't": "is not", "aren't": "are not", "wasn't": "was not",
    "weren't": "were not", "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
    "wouldn't": "would not", "shouldn't": "should not", "couldn't": "could not",
    "mustn't": "must not", "shan't": "shall not", "it's": "it is", "i'm": "i am",
    "you're": "you are", "we're": "we are", "they're": "they are", "he's": "he is",
    "she's": "she is", "that's": "that is", "what's": "what is", "there's": "there is",
    "i've": "i have", "you've": "you have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "i'd": "i would", "you'd": "you would", "we'd": "we would", "they'd": "they would",
    "let's": "let us", "who's": "who is", "how's": "how is", "ain't": "is not",
}

EMOJI_MAP = {
    "😊": " happy ", "😃": " happy ", "😄": " happy ", "🙂": " happy ", "😁": " grinning ",
    "😍": " love ", "❤️": " love ", "💕": " love ", "👍": " good ", "👎": " bad ",
    "😡": " angry ", "😠": " angry ", "🤬": " angry ", "😤": " frustrated ",
    "😢": " sad ", "😭": " crying ", "💔": " heartbroken ", "😞": " disappointed ",
    "🔥": " excellent ", "⭐": " star ", "🌟": " star ", "💯": " perfect ",
    "🤮": " disgusting ", "💩": " terrible ", "🚀": " fast ", "🐌": " slow ",
    "😒": " annoyed ", "🙄": " sarcastic ", "😏": " sarcastic ", "👏": " applause ",
    "🤦": " facepalm ", "😑": " unamused ", "😐": " neutral ",
}

NEGATION_WORDS = {"not", "no", "never", "neither", "nobody", "nothing", "nowhere",
                  "nor", "cannot", "without", "hardly", "barely", "scarcely", "seldom"}

SARCASM_MARKERS = [
    "oh great", "oh wonderful", "oh perfect", "oh fantastic", "oh brilliant",
    "oh sure", "oh yeah right", "yeah right", "sure thing", "oh joy",
    "how wonderful", "how lovely", "how nice", "just what i needed",
    "thanks for nothing", "gee thanks",
    "new record", "what a surprise", "color me surprised",
    "slow clap",
]

NEGATIVE_CONTEXT = {
    "crash", "crashes", "crashed", "crashing", "broke", "broken", "break", "breaking",
    "slow", "lag", "laggy", "freeze", "froze", "freezes", "freezing",
    "bug", "bugs", "buggy", "error", "errors", "fail", "fails", "failed", "failing",
    "terrible", "horrible", "awful", "worst", "bad", "worse", "useless", "unusable",
    "waste", "garbage", "trash", "disaster", "mess", "broken", "nothing",
    "waiting", "wait", "lost", "lose", "losing", "disappear", "disappeared",
    "drain", "drains", "empty", "wrong", "incorrect", "paint dry",
}


def preprocess_text(text: str) -> str:
    """Advanced text preprocessing matching the training pipeline."""
    if not text or not text.strip():
        raise ValueError("Empty text provided")
    t = text.lower().strip()
    # Emoji conversion
    for emoji, word in EMOJI_MAP.items():
        t = t.replace(emoji, word)
    # Contraction expansion
    for contraction, expansion in CONTRACTIONS.items():
        t = t.replace(contraction, expansion)
    # Normalize excessive punctuation
    t = re.sub(r'([!?.])\1{2,}', r'\1\1', t)
    t = re.sub(r'(.)\1{3,}', r'\1\1', t)
    # Normalize whitespace
    t = re.sub(r'\s+', ' ', t).strip()

    # Negation tagging
    words = t.split()
    result, negate = [], False
    for w in words:
        if w in NEGATION_WORDS:
            negate = True
            result.append(w)
        elif negate and w in {".", "!", "?", ",", ";", "but", "however", "although"}:
            negate = False
            result.append(w)
        elif negate:
            result.append(f"NEG_{w}")
        else:
            result.append(w)
    t = " ".join(result)

    # Context-aware sarcasm detection: marker + negative context required
    has_marker = any(marker in t for marker in SARCASM_MARKERS)
    has_negative = any(neg in t for neg in NEGATIVE_CONTEXT)
    if has_marker and has_negative:
        t = "SARCASM_FLAG " + t
    return t


# ════════════════════════════════════════════════════════════════
# MODEL LOADING & PREDICTION
# ════════════════════════════════════════════════════════════════

def load_models():
    """Load all trained models into memory."""
    global _sentiment_model, _category_model, _urgency_model

    print("🔄 Loading ML models...")

    sentiment_path = os.path.join(MODELS_DIR, "sentiment_model.joblib")
    category_path = os.path.join(MODELS_DIR, "category_model.joblib")
    urgency_path = os.path.join(MODELS_DIR, "urgency_model.joblib")

    if not all(os.path.exists(p) for p in [sentiment_path, category_path, urgency_path]):
        raise FileNotFoundError(
            "ML models not found. Run: python -m app.ml.train"
        )

    _sentiment_model = joblib.load(sentiment_path)
    _category_model = joblib.load(category_path)
    _urgency_model = joblib.load(urgency_path)

    print("✅ All ML models loaded successfully!")


def add_correction(original_text: str, sentiment: str, category: str, urgency: str):
    """Add a human correction to the active memory cache."""
    cleaned = preprocess_text(original_text)
    CORRECTION_CACHE[cleaned] = {
        "sentiment": sentiment,
        "category": category,
        "urgency": urgency
    }
    print(f"🧠 AI Learned new correction for: {cleaned[:30]}...")


def predict(text: str) -> dict:
    """
    Run all 3 ensemble models on the input text.
    First checks the self-learning memory cache for similar corrected inputs.
    """
    if _sentiment_model is None:
        raise RuntimeError("Models not loaded. Call load_models() first.")

    cleaned = preprocess_text(text)
    
    # ── Self-Learning Override Check ──
    # Check if we have a very similar text in the correction cache
    for cached_text, overrides in CORRECTION_CACHE.items():
        similarity = difflib.SequenceMatcher(None, cleaned, cached_text).ratio()
        if similarity >= 0.85:
            # Overriding model with human correction
            return {
                "sentiment": overrides["sentiment"],
                "sentiment_confidence": 1.0,
                "category": overrides["category"],
                "category_confidence": 1.0,
                "urgency": overrides["urgency"],
                "urgency_confidence": 1.0,
            }

    text_input = [cleaned]

    # Sentiment prediction
    sentiment_pred = _sentiment_model.predict(text_input)[0]
    sentiment_proba = _sentiment_model.predict_proba(text_input)[0]
    sentiment_conf = float(np.max(sentiment_proba))

    # Category prediction
    category_pred = _category_model.predict(text_input)[0]
    category_proba = _category_model.predict_proba(text_input)[0]
    category_conf = float(np.max(category_proba))

    # Urgency prediction
    urgency_pred = _urgency_model.predict(text_input)[0]
    urgency_proba = _urgency_model.predict_proba(text_input)[0]
    urgency_conf = float(np.max(urgency_proba))

    # ── Sentiment-aware urgency adjustment ──
    # Positive feedback should never have high/critical urgency.
    if sentiment_pred == "positive" and sentiment_conf > 0.5:
        if urgency_pred in ("high", "critical", "medium"):
            urgency_pred = "low"
            classes = list(_urgency_model.classes_)
            if "low" in classes:
                urgency_conf = float(urgency_proba[classes.index("low")])
            else:
                urgency_conf = round(sentiment_conf * 0.8, 4)

    # ── Sarcasm-aware adjustment ──
    # If sarcasm was detected in preprocessing but sentiment came out positive,
    # override to negative (sarcasm typically masks negative sentiment).
    if "SARCASM_FLAG" in cleaned and sentiment_pred == "positive":
        # Check if negative probability is reasonable
        sent_classes = list(_sentiment_model.classes_)
        if "negative" in sent_classes:
            neg_idx = sent_classes.index("negative")
            neg_prob = float(sentiment_proba[neg_idx])
            if neg_prob > 0.1:  # if there's any negative signal
                sentiment_pred = "negative"
                sentiment_conf = max(neg_prob, 0.65)
                # Also adjust urgency since it's now negative
                if urgency_pred == "low":
                    urgency_pred = "medium"
                    if "medium" in list(_urgency_model.classes_):
                        med_idx = list(_urgency_model.classes_).index("medium")
                        urgency_conf = float(urgency_proba[med_idx])

    return {
        "sentiment": sentiment_pred,
        "sentiment_confidence": round(sentiment_conf, 4),
        "category": category_pred,
        "category_confidence": round(category_conf, 4),
        "urgency": urgency_pred,
        "urgency_confidence": round(urgency_conf, 4),
    }


def get_model_info() -> dict:
    """Return info about loaded models."""
    if _sentiment_model is None:
        return {"status": "not loaded"}

    return {
        "status": "loaded",
        "models": {
            "sentiment": {
                "classes": list(_sentiment_model.classes_),
                "type": "VotingClassifier (LinearSVC + LogReg + NB + ComplementNB)",
            },
            "category": {
                "classes": list(_category_model.classes_),
                "type": "VotingClassifier (LinearSVC + LogReg + NB + ComplementNB)",
            },
            "urgency": {
                "classes": list(_urgency_model.classes_),
                "type": "VotingClassifier (LinearSVC + LogReg + NB + ComplementNB)",
            },
        },
    }
