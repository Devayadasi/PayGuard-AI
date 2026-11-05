
# PayGuard AI

### AI-Powered Payment Fraud Detection & Risk Intelligence Platform

PayGuard AI is a machine learning-based fraud detection platform that analyses payment transactions, calculates risk scores, classifies suspicious activity and provides explainable AI insights.

## Features

- AI-powered fraud detection
- Transaction risk scoring (0–100)
- Automated decisions: APPROVE, REVIEW and BLOCK
- SHAP-based explainable AI
- Transaction history and monitoring
- Interactive analytics dashboard
- MySQL database integration
- REST API using FastAPI

## Technology Stack

- Python
- Pandas and NumPy
- Scikit-learn
- Random Forest
- SHAP
- FastAPI
- MySQL
- SQLAlchemy
- HTML, CSS and JavaScript
- Chart.js

## Dataset

PayGuard AI uses the PaySim synthetic mobile-money transaction dataset for model training and evaluation.

## Project Structure

```text
PayGuard-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── models/
│   │       ├── fraud_model.joblib
│   │       └── metadata.json
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .gitignore
└── README.md
```

## Run Locally

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Configure your MySQL connection in `backend/.env`.

Start the API:

```bash
uvicorn app.main:app --reload
```

API documentation:

http://127.0.0.1:8000/docs

Open `frontend/index.html` using VS Code Live Server.

## Disclaimer

This is an educational portfolio prototype trained on synthetic transaction data. It is not validated for production payment decisions.
