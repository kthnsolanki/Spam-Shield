# 🛡️ Spam Shield — AI-Based Message & URL Security System

> An AI-powered web application that detects spam messages, analyses malicious URLs, and scans bulk message files — built with FastAPI, Naive Bayes, and SQLite.

---

## 📌 Overview

Spam Shield is a full-stack machine learning web application developed as a university project. It classifies SMS and email messages as **spam or legitimate (ham)** using a Naive Bayes classifier trained on over 35,000 real-world samples. The platform includes user authentication, three scan modules, and a personal scan history — all accessible through a clean web interface without any external tools.

---

## ✨ Features

| Feature | Description |
|---|---|
| ✉️ **Message Scanner** | Classify any SMS or email as spam/ham with confidence percentage and highlighted spam keywords |
| 🔗 **URL Checker** | Deep rule-based analysis — HTTPS check, domain resolution, IP lookup, TLD risk, subdomain count |
| 📂 **Batch Scanner** | Upload a `.txt` or `.csv` file and scan hundreds of messages at once with a full results table |
| 🔐 **User Authentication** | Register and login with JWT tokens and bcrypt-hashed passwords |
| 🗄️ **Scan History** | Every scan is saved to a personal SQLite database — filterable by type, deletable per record |
| 🎨 **Modern UI** | Responsive web interface built with pure HTML/CSS/JS — no frameworks required |

---

## 🧠 ML Architecture

| Component | Detail |
|---|---|
| Algorithm | Multinomial Naive Bayes |
| Feature Extraction | TF-IDF Vectorizer (sklearn) |
| Training Dataset 1 | Enron Email Dataset — 29,779 samples |
| Training Dataset 2 | UCI SMS Spam Collection — 5,572 samples |
| Combined Dataset | 35,351 samples (shuffled, 80/20 split) |
| Model Accuracy | ~98% on test set |
| Saved Files | `spam_model.pkl`, `tfidf_vectorizer.pkl` |

---

## 🗂️ Project Structure

```
spam_shield/
│
├── app.py                  # FastAPI backend — all routes and auth logic
├── model_util.py           # ML prediction, spam word detection, URL analysis
├── database.py             # SQLAlchemy models — User and ScanHistory tables
│
├── spam_model.pkl          # Trained Naive Bayes model
├── tfidf_vectorizer.pkl    # Fitted TF-IDF vectorizer
├── spam_shield.db          # SQLite database (auto-created on first run)
│
├── templates/
│   └── index.html          # Full frontend — auth, 3 modules, history view
│
├── comb_db.ipynb           # Notebook: combining Enron + SMS datasets
└── train_test.ipynb        # Notebook: model training and evaluation
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/spam-shield.git
cd spam-shield
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn jinja2 python-multipart scikit-learn pandas joblib sqlalchemy "passlib[bcrypt]" "bcrypt==4.0.1" PyJWT tldextract
```

### 3. Make sure these files are present

```
spam_model.pkl
tfidf_vectorizer.pkl
templates/index.html
```

### 4. Run the application

```bash
python app.py
```

### 5. Open in browser

```
http://localhost:8000
```

---

## 🚀 Usage

1. **Register** a new account or **Sign In** with existing credentials
2. Use the **Message Scan** tab to paste any suspicious SMS or email
3. Use the **URL Checker** tab to analyse any URL for phishing indicators
4. Use the **Batch Scanner** tab to upload a `.txt` or `.csv` file for bulk analysis
5. Click **History** in the top bar to view, filter, and delete your past scans

---

## 🗃️ Database Schema

### `users` table

| Field | Type | Constraint |
|---|---|---|
| id | INT | PRIMARY KEY, AUTO INCREMENT |
| username | VARCHAR(50) | NOT NULL, UNIQUE |
| email | VARCHAR(120) | NOT NULL, UNIQUE |
| hashed_password | VARCHAR | NOT NULL |
| created_at | DATETIME | DEFAULT UTC NOW |

### `scan_history` table

| Field | Type | Constraint |
|---|---|---|
| id | INT | PRIMARY KEY, AUTO INCREMENT |
| user_id | INT | FOREIGN KEY → users.id |
| scan_type | VARCHAR(20) | "message" / "url" / "batch" |
| input_content | TEXT | NOT NULL |
| result | VARCHAR(50) | spam / ham / SAFE / HIGH RISK |
| confidence | FLOAT | NULLABLE |
| extra_info | TEXT | NULLABLE (reserved) |
| created_at | DATETIME | DEFAULT UTC NOW |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Machine Learning | Scikit-learn (Naive Bayes + TF-IDF) |
| Database | SQLite via SQLAlchemy ORM |
| Authentication | JWT (PyJWT) + bcrypt (passlib) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| URL Analysis | tldextract, socket (Python stdlib) |

---

## 📋 Requirements

```
fastapi
uvicorn
jinja2
python-multipart
scikit-learn
pandas
joblib
sqlalchemy
passlib[bcrypt]
bcrypt==4.0.1
PyJWT
tldextract
```

---

## 📖 References

- Metsis et al. (2006) — Spam Filtering with Naive Bayes
- Almeida et al. (2011) — UCI SMS Spam Collection Dataset
- Enron Email Dataset — Carnegie Mellon University
- Scikit-learn Documentation — https://scikit-learn.org
- FastAPI Documentation — https://fastapi.tiangolo.com

---

## 👨‍💻 Author

Developed as a **University Project — 2026**
Department of Computer Science

---

## 📄 License

This project is for academic purposes only.
