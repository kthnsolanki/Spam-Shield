import re
import socket
import html
from urllib.parse import urlparse

import joblib

# ── Load saved model and vectorizer ─────────────────────────────────────────
model = joblib.load("spam_model.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")


# ── Message prediction ──────────────────────────────────────────────────────
def predict_msg(text: str):
    """
    Returns (label, spam_probability) where label is 'spam' or 'ham'
    and spam_probability is a float between 0 and 1.
    """
    text_vector = vectorizer.transform([text])
    raw_prediction = model.predict(text_vector)[0]

    # Figure out which column in predict_proba corresponds to "spam",
    # regardless of whether the model's classes are ['ham','spam'] or [0,1].
    classes = list(model.classes_)
    proba = model.predict_proba(text_vector)[0]

    spam_idx = None
    for i, c in enumerate(classes):
        if str(c).lower() in ("spam", "1"):
            spam_idx = i
            break
    if spam_idx is None:
        # fall back: assume the last class is "spam"
        spam_idx = len(classes) - 1

    spam_prob = float(proba[spam_idx])
    label = "spam" if str(raw_prediction).lower() in ("spam", "1") else "ham"

    return label, spam_prob


# ── Suspicious word detection ───────────────────────────────────────────────
SPAM_TRIGGER_WORDS = [
    "free", "win", "winner", "won", "cash", "prize", "reward", "gift",
    "urgent", "act now", "limited time", "click here", "click below",
    "buy now", "order now", "call now", "text now", "subscribe",
    "guarantee", "guaranteed", "no cost", "no obligation", "risk free",
    "credit", "loan", "debt", "refinance", "investment", "earn money",
    "make money", "extra income", "work from home", "million dollars",
    "congratulations", "selected", "claim", "verify your account",
    "verify now", "confirm your account", "password", "bank account",
    "social security", "account suspended", "unsubscribe", "offer expires",
    "100% free", "special promotion", "exclusive deal", "discount",
    "lottery", "jackpot", "casino", "viagra", "weight loss", "miracle",
    "double your", "cheap", "lowest price", "act immediately",
]


def find_spam_words(text: str):
    """
    Returns a list of spam-trigger words/phrases found in `text`
    (case-insensitive), preserving the order they appear in.
    """
    lower_text = text.lower()
    found = []
    for phrase in SPAM_TRIGGER_WORDS:
        if phrase in lower_text and phrase not in found:
            found.append(phrase)
    return found


def highlight_words(text: str, suspicious_words):
    """
    Wraps each occurrence of a suspicious word/phrase in `text` with
    <span style='color:red;font-weight:bold'>...</span>, matching whole
    words/phrases case-insensitively. Rest of the text is HTML-escaped.
    """
    if not suspicious_words:
        return html.escape(text)

    # Longest phrases first so multi-word phrases aren't partially matched
    sorted_words = sorted(suspicious_words, key=len, reverse=True)
    pattern = re.compile(
        r"(" + "|".join(re.escape(w) for w in sorted_words) + r")",
        re.IGNORECASE,
    )

    parts = []
    last_end = 0
    for m in pattern.finditer(text):
        parts.append(html.escape(text[last_end:m.start()]))
        parts.append(
            f"<span style='color:red;font-weight:bold'>{html.escape(m.group(0))}</span>"
        )
        last_end = m.end()
    parts.append(html.escape(text[last_end:]))

    return "".join(parts)


# ── URL analysis ─────────────────────────────────────────────────────────
SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "xyz", "top", "work", "click", "loan"}
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "shorte.st", "adf.ly", "tiny.cc",
}
SUSPICIOUS_KEYWORDS = [
    "login", "verify", "account", "secure", "update", "confirm",
    "banking", "paypal", "signin", "password", "suspended", "urgent",
    "webscr", "billing", "unlock", "recover",
]


def advanced_url_analysis(url: str):
    """
    Returns a dict with:
      status: 'HIGH RISK' | 'SUSPICIOUS' | 'SAFE'
      risk_score: 0-100
      domain: str
      ip: str or None
      reasons: list[str]
    """
    reasons = []
    score = 0

    raw_url = url.strip()
    if not re.match(r"^[a-zA-Z]+://", raw_url):
        raw_url = "http://" + raw_url

    parsed = urlparse(raw_url)
    domain = parsed.netloc.split("@")[-1].split(":")[0] or "unknown"

    # 1. Not using HTTPS
    if parsed.scheme != "https":
        score += 15
        reasons.append("Connection is not secured with HTTPS")

    # 2. IP address used instead of a domain name
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        score += 25
        reasons.append("URL uses a raw IP address instead of a domain name")

    # 3. '@' symbol in URL (classic phishing trick)
    if "@" in url:
        score += 25
        reasons.append("URL contains an '@' symbol, which can hide the real destination")

    # 4. Known URL shortener
    if domain.lower() in URL_SHORTENERS:
        score += 15
        reasons.append("URL uses a link-shortening service, hiding the real destination")

    # 5. Excessive subdomains
    subdomain_count = domain.count(".")
    if subdomain_count >= 3:
        score += 15
        reasons.append("URL has an unusually high number of subdomains")

    # 6. Suspicious TLD
    tld = domain.rsplit(".", 1)[-1].lower() if "." in domain else ""
    if tld in SUSPICIOUS_TLDS:
        score += 15
        reasons.append(f"Domain uses a high-risk top-level domain (.{tld})")

    # 7. Hyphens in domain (often used to mimic real brands)
    if domain.count("-") >= 2:
        score += 10
        reasons.append("Domain contains multiple hyphens, often used to impersonate brands")

    # 8. Very long URL
    if len(url) > 75:
        score += 10
        reasons.append("URL is unusually long")

    # 9. Suspicious keywords in the URL
    lower_url = url.lower()
    matched_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_url]
    if matched_keywords:
        score += min(20, 5 * len(matched_keywords))
        reasons.append("URL contains sensitive keywords: " + ", ".join(matched_keywords[:4]))

    risk_score = min(100, score)

    if risk_score >= 60:
        status = "HIGH RISK"
    elif risk_score >= 30:
        status = "SUSPICIOUS"
    else:
        status = "SAFE"

    # Resolve IP (best-effort, don't fail the whole request if DNS fails)
    try:
        ip = socket.gethostbyname(domain)
    except Exception:
        ip = None

    return {
        "status": status,
        "risk_score": risk_score,
        "domain": domain,
        "ip": ip,
        "reasons": reasons,
    }
