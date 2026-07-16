import joblib
import re
import socket
import tldextract

# Load saved model and vectorizer
model = joblib.load("spam_model.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

def predict_msg(text):
    text_vector = vectorizer.transform([text])

    prediction = model.predict(text_vector)[0]

    prob = model.predict_proba(text_vector)
    spam_prob = prob[0][1]

    return prediction, spam_prob

spam_words = [
    "free","win","winner","won","prize",
    "offer","click","buy","urgent",
    "money","lottery","congratulations",
    "claim","gift","reward"
]

def find_spam_words(text):
    words = text.lower().split()
    detected = []

    for word in words:
        if word in spam_words:
            detected.append(word)

    return list(set(detected))

def highlight_words(text, suspicious):
    
    words = text.split()
    highlighted = []

    for word in words:
        clean_word = word.lower().strip(".,!?")

        if clean_word in suspicious:
            highlighted.append(
                f"<span style='color:red;font-weight:bold'>{word}</span>"
            )
        else:
            highlighted.append(word)

    return " ".join(highlighted)

def advanced_url_analysis(url):
    reasons = []
    risk_score = 0

    # Extract domain info
    extracted = tldextract.extract(url)
    domain = extracted.domain
    suffix = extracted.suffix
    full_domain = f"{domain}.{suffix}"

    # Get IP address
    try:
        ip_address = socket.gethostbyname(full_domain)
    except:
        ip_address = "Unable to fetch IP"
        reasons.append("Domain could not be resolved")
        risk_score += 20

    # RULES
    if len(url) > 60:
        reasons.append("URL is too long")
        risk_score += 15

    if "@" in url:
        reasons.append("Contains '@' symbol (possible phishing)")
        risk_score += 25

    if url.count('.') > 3:
        reasons.append("Too many subdomains")
        risk_score += 15

    if url.startswith("http://"):
        reasons.append("Not using HTTPS")
        risk_score += 20

    suspicious_tlds = ["xyz", "tk", "ru", "ml"]
    if suffix in suspicious_tlds:
        reasons.append(f"Suspicious domain extension: .{suffix}")
        risk_score += 25

    # FINAL STATUS
    if risk_score > 60:
        status = "HIGH RISK"
    elif risk_score > 30:
        status = "SUSPICIOUS"
    else:
        status = "SAFE"

    return {
        "domain": full_domain,
        "ip": ip_address,
        "risk_score": risk_score,
        "status": status,
        "reasons": reasons
    }