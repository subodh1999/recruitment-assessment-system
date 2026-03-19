# Automated End-to-End Recruitment & Talent Assessment System

A full-stack recruitment automation platform that discovers developer talent via the GitHub API, predicts candidate eligibility using machine learning, and delivers a secure coding assessment through a Django web app with Docker-sandboxed code execution.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Django](https://img.shields.io/badge/Django-Web_App-green?logo=django)
![Docker](https://img.shields.io/badge/Docker-Sandboxed-blue?logo=docker)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange?logo=scikitlearn)


---

## Overview

Traditional recruitment pipelines rely on manual resume screening and subjective assessments. This system automates the entire workflow:

1. **Discover** — Fetch and profile developer candidates from GitHub's API
2. **Predict** — Classify candidate eligibility using ML (K-Means + Logistic Regression)
3. **Assess** — Deliver a timed coding exam in a secure, sandboxed environment
4. **Decide** — Role-based dashboards for HR and Project Managers to review and hire

---

## Architecture

```
GitHub API → Data Ingestion Pipeline → PostgreSQL
                                           ↓
                                    Preprocessing & Feature Engineering
                                           ↓
                                    K-Means Clustering (pseudo-labeling)
                                           ↓
                                    Model Training (Logistic Regression, SVM, Random Forest)
                                           ↓
                                    Prediction on new candidates → "Selected" / "Rejected"
                                           ↓
                                    Selected → Email with exam credentials
                                           ↓
                                    Django Web App (Docker-sandboxed coding exam)
                                           ↓
                                    HR Dashboard → PM Review → Hire/Reject
```

---

## Components

### 1. Data Engineering — GitHub API Pipeline

- **Dual pipeline system:** Separate workflows for sourcing unknown candidates and collecting training data
- **Comprehensive profiling:** Collects 19+ metrics per user — repos, stars, forks, PRs, issues, contributions, languages, account age, and more
- **Rate limit handling:** Intelligent retry with exponential backoff
- **Concurrent processing:** Multi-threaded enrichment for batch performance
- **Resume capability:** Tracks processed users to avoid duplicates across runs

**Key files:** `github fetching/data_fetching_db.py`, `github fetching/database.py`

### 2. Machine Learning Pipeline

- **Preprocessing:** Null handling, feature engineering, log transformation, StandardScaler normalization
- **Unsupervised labeling:** K-Means clustering (k=2) to segment candidates into eligibility groups on an initially unlabeled dataset
- **Model comparison:** Evaluated Logistic Regression, SVM, and Random Forest with SMOTE for class imbalance
- **Selected model:** Logistic Regression (F1 = 0.99) after cross-validation
- **Deployment:** Model serialized via Pickle and stored in PostgreSQL for production inference
- **Live prediction:** Runs on newly fetched candidates, appending "Selected" or "Rejected" status

**Key files:** `code/main.py`, `code/prediction.py`, `code/preprocessing.py`, `code/Version2-checkpoint.ipynb`

### 3. Web Platform — Django Coding Assessment

- **Secure code execution:** Candidate-submitted Python code runs in a sandboxed Docker container
- **Dynamic question delivery:** Random selection of 3 questions per candidate from the database
- **Automated grading:** Compares output against expected results → Pass/Fail
- **Role-based dashboards:**
  - **Candidate:** Take exam, write and run code, submit solutions
  - **HR:** View candidates, send exam invitations, send offer/rejection emails
  - **Project Manager:** Review submitted code, see test results, confirm or reject
- **Email automation:** Automated exam links and hiring notifications

**Key files:** `UI/` directory (Django project with Dockerfile)

---

## Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python 3.8+ |
| Web Framework | Django |
| Database | PostgreSQL |
| ML | scikit-learn, SMOTE, K-Means, Logistic Regression, SVM, Random Forest |
| Containerization | Docker (sandboxed code execution) |
| Data Source | GitHub REST API |
| Serialization | Pickle (model persistence in DB) |

---

## Project Structure

```
recruitment-assessment-system/
├── README.md
├── .gitignore
├── hushHushRecruiter.pdf               # Project specification
│
├── github fetching/                     # Data engineering pipeline
│   ├── data_fetching_db.py             # GitHub API client + ingestion
│   └── database.py                     # PostgreSQL manager
│
├── code/                                # ML pipeline
│   ├── main.py                         # Training: fetch → clean → cluster → train → serialize
│   ├── prediction.py                   # Inference on new candidates
│   ├── preprocessing.py                # Feature engineering & scaling
│   ├── Version2-checkpoint.ipynb       # Exploration notebook
│   ├── requirements.txt
│   ├── README.md
│   ├── UserStories(HushHushRecruiter).pptx
│   └── UserStories(HushHushRecruiter).txt
│
├── UI/                                  # Django web application
│   ├── Dockerfile                      # Sandboxed Python execution
│   ├── test.py
│   └── UI/                             # Django project root
│
└── presentation/                        # Project presentation
```

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- PostgreSQL running locally
- Docker Desktop installed and running
- GitHub Personal Access Token

### 1. Clone the Repository

```bash
git clone https://github.com/subodh1999/recruitment-assessment-system.git
cd recruitment-assessment-system
```

### 2. Set Up the Database

Create a PostgreSQL database and configure credentials in a `.env` file:

```env
GITHUB_TOKEN=your_github_token
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

### 3. Run the Data Pipeline

```bash
# Fetch training data from GitHub
cd "github fetching"
python data_fetching_db.py training

# Fetch candidates for prediction
python data_fetching_db.py sourcing
```

### 4. Train the Model & Run Predictions

```bash
cd code
pip install -r requirements.txt
python main.py          # Train model
python prediction.py    # Predict on new candidates
```

### 5. Launch the Web Application

```bash
cd UI/UI
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# Build the Docker image for code execution
cd ../
docker build -t python-compiler .

# Run migrations and start server
cd UI
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py populate_questions
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`

---

## Data Schema

The pipeline collects 19+ features per GitHub user:

| Feature | Description |
|---------|-------------|
| `username` | GitHub username (Primary Key) |
| `followers` | Number of followers |
| `public_repos` | Number of public repositories |
| `total_stars_received` | Total stars across all repos |
| `total_forks_received` | Total forks across all repos |
| `primary_languages` | Top 3 programming languages |
| `prs_opened / merged` | Pull request activity |
| `issues_opened / closed` | Issue activity |
| `total_contributions` | Total contribution count |
| `account_age_days` | Account age in days |
| ... | + 9 more features |

---

## Author

**Subodh Nadkar**
M.Sc. Applied Data Science & Analytics — SRH University Heidelberg

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://www.linkedin.com/in/subodh-nadkar)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?logo=github)](https://github.com/subodh1999)

---
