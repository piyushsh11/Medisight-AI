# MediSight AI

A multimodal clinical decision-support prototype that combines medical images, patient vitals, and free-text symptom descriptions to surface possible conditions for physician review.

> **Disclaimer:** MediSight AI assists medical professionals and does not replace physician judgment, diagnosis, or treatment planning. This is a prototype — probability rankings require clinician review and the system does not invent missing patient details.

---

## Overview

MediSight AI walks a clinician through a four-step intake flow — **Upload → Vitals → Symptoms → Result** — and produces a ranked list of possible conditions alongside a vitals-based risk assessment and an AI-generated case summary.

### Core Features

- **Image-Aware Analysis** — supports chest X-ray and skin lesion image intake with preview.
- **Vitals Intelligence** — captures key vitals (SpO2, BP, heart rate, respiratory rate, temperature) and flags abnormal readings to contextualize probable conditions and urgency.
- **Multimodal Summary** — combines image, symptom, and vitals signals into weighted condition likelihoods, an overall risk score, and actionable recommendations.
- **Case History** — logs prior cases with urgency level for quick reference.

## How It Works

1. **Upload** — the user selects an image type (e.g., Chest X-ray) and uploads a diagnostic image.
2. **Vitals** — core vitals and risk indicators are entered.
3. **Symptoms** — free-text symptom description, with optional duration and severity.
4. **Result** — the backend scores each candidate condition against a disease profile catalog (image / symptom / vitals match weighting), computes an overall risk score and urgency classification, and calls the Gemini API (`gemini-2.5-flash-lite`) to generate a natural-language case summary, rationale ("Why this was suggested"), recommendations, and clinician follow-up questions.

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | Python, Flask |
| AI Model | Google Gemini API (`gemini-2.5-flash-lite`) |
| Frontend | HTML, CSS, vanilla JS |

## Project Structure

```
MediSight AI/
├── backend/
│   ├── app.py
│   ├── services/
│   │   └── disease_catalog.py   # DiseaseProfile definitions (symptoms, vitals, image terms)
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/
│       ├── upload.html
│       ├── vitals.html
│       ├── symptoms.html
│       ├── result.html
│       └── history.html
├── requirements.txt
├── .env.example
└── README.md
```

> Adjust this tree to match your actual repo layout before committing.

## Getting Started

### Prerequisites

- Python 3.10+
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/medisight-ai.git
cd medisight-ai

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# then edit .env and add your GEMINI_API_KEY
```



## Environment Variables

| Variable         | Description                          |
|------------------|---------------------------------------|
| `GEMINI_API_KEY` | API key for the Gemini API (required) |

A `.env.example` file is included as a template — never commit your actual `.env` file (see `.gitignore`).

## Roadmap

- [ ] Replace mock/fallback scoring with a trained image-classification model
- [ ] Add authentication for clinician accounts
- [ ] Persist case history to a database instead of in-memory/local storage
- [ ] Expand disease profile catalog


## Author

Built by Piyush, B.Tech Cybersecurity student at NMIMS (MPSTME).
