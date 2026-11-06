# PayGuard AI – AI-Powered Payment Fraud Detection & Risk Intelligence Platform

PayGuard AI is an end-to-end machine learning application that analyses financial transactions, estimates fraud risk, and provides explainable predictions using SHAP.

The platform classifies transactions into three categories: **APPROVE, REVIEW, and BLOCK**, while maintaining transaction history and analytics through a hosted MySQL-compatible database.

## Live Demo

- **Frontend:** [https://payguard-ai-yrgp.onrender.com](https://payguard-ai-yrgp.onrender.com)
- **Backend API:** [https://payguard-ai-v75n.onrender.com](https://payguard-ai-v75n.onrender.com)
- **API Documentation:** [https://payguard-ai-v75n.onrender.com/docs](https://payguard-ai-v75n.onrender.com/docs)
- **GitHub Repository:** [https://github.com/Devayadasi/PayGuard-AI](https://github.com/Devayadasi/PayGuard-AI)

## Features

- **Fraud Detection:** Random Forest machine learning model for transaction classification.
- **Risk Scoring:** Generates a fraud risk score between 0 and 100.
- **Decision Engine:** Automatically classifies transactions as APPROVE, REVIEW, or BLOCK.
- **Explainable AI:** SHAP-based explanations showing how individual features influence predictions.
- **Transaction Monitoring:** Stores and retrieves analysed transaction records.
- **Analytics Dashboard:** Displays transaction statistics, decision distributions, and average risk scores.
- **REST API:** FastAPI endpoints for prediction, transaction history, analytics, and explanations.
- **Cloud Deployment:** Frontend and backend deployed separately on Render, with TiDB Cloud providing hosted MySQL-compatible database storage.

## Technology Stack

| Category             | Technologies                |
| -------------------- | --------------------------- |
| Programming Language | Python, JavaScript          |
| Machine Learning     | Scikit-learn, Random Forest |
| Explainable AI       | SHAP                        |
| Backend              | FastAPI                     |
| Frontend             | HTML, CSS, JavaScript       |
| Database             | MySQL, TiDB Cloud           |
| Data Processing      | Pandas, NumPy               |
| ORM                  | SQLAlchemy                  |
| Visualization        | Chart.js                    |
| Model Serialization  | Joblib                      |
| Deployment           | Render                      |

## System Architecture

```text
              User
               |
               v
       Frontend Dashboard
        HTML / CSS / JS
               |
               v
          FastAPI Backend
               |
        +------+------+
        |             |
        v             v
  Random Forest    SHAP Engine
     Model        Explainability
        |             |
        +------+------+
               |
               v
       Risk Scoring Engine
               |
       +-------+-------+
       |       |       |
       v       v       v
    APPROVE  REVIEW   BLOCK
               |
               v
          TiDB Cloud
        MySQL Database
               |
               v
      Transaction History
       and Analytics
```

## Machine Learning Model

PayGuard AI uses a Random Forest classifier trained on the **PaySim synthetic mobile money transaction dataset**.

### Dataset Information

- Dataset: PaySim
- Original records: 6,362,620 transactions
- Features include transaction step, transaction type, amount, and account balances.
- Fraudulent transactions are highly imbalanced compared with legitimate transactions.

### Feature Engineering

The model uses transaction and engineered features, including:

- Transaction amount
- Origin and destination account balances
- Amount-to-origin-balance ratio
- Log-transformed transaction amount
- Cyclical time features
- Transaction-type encoded features

Identifiers, post-transaction balances, and the dataset's `isFlaggedFraud` field were excluded from model inputs.

### Model Evaluation

The dataset was split chronologically into training, validation, and test sets. Class imbalance was addressed during training.

Evaluation metrics include:

- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC

The model achieved strong results on the held-out synthetic test data. These results should not be interpreted as expected performance on real-world banking transactions.

## Explainable AI with SHAP

SHAP (SHapley Additive exPlanations) is integrated using `TreeExplainer`.

It helps explain individual model predictions by showing:

- Features that increase fraud prediction.
- Features that decrease fraud prediction.
- Relative contribution values for each feature.

This provides more transparency than returning a fraud prediction alone.

## API Endpoints

| Method | Endpoint                        | Description                  |
| ------ | ------------------------------- | ---------------------------- |
| GET    | `/`                             | API welcome message          |
| GET    | `/api/health`                   | Health status                |
| GET    | `/api/model-info`               | Model information            |
| POST   | `/api/predict`                  | Analyse a transaction        |
| GET    | `/api/transactions`             | Retrieve transaction history |
| GET    | `/api/stats`                    | Dashboard statistics         |
| GET    | `/api/explain/{transaction_id}` | SHAP explanation             |

Interactive API documentation is available through FastAPI Swagger UI:

[https://payguard-ai-v75n.onrender.com/docs](https://payguard-ai-v75n.onrender.com/docs)

## Project Structure

```text
PayGuard-AI/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── models/
│   │       ├── fraud_model.joblib
│   │       └── metadata.json
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── .gitignore
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Devayadasi/PayGuard-AI.git
cd PayGuard-AI
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
```

Activate the environment on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure database credentials

Create a `.env` file inside the `backend` directory.

Configure either a SQLAlchemy `DATABASE_URL` or the following database variables:

```env
DB_HOST=your_database_host
DB_PORT=4000
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_NAME=payguard_db
DB_SSL=true
```

Use your own MySQL-compatible database credentials. Never commit `.env` or expose database passwords publicly.

### 4. Start the backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### 5. Run the frontend

Open `frontend/index.html` using a local development server or browser.

For local development, configure the frontend API URL in `frontend/script.js` to:

```javascript
const API_URL = "http://127.0.0.1:8000";
```

For the deployed frontend, use the Render backend URL.

## Deployment

The application is deployed using separate Render services:

- **Static Site:** Hosts the HTML, CSS, and JavaScript frontend.
- **Web Service:** Runs the FastAPI backend.
- **TiDB Cloud:** Hosts the MySQL-compatible transaction database.

The frontend communicates with the backend through REST API requests.

## Limitations and Future Scope

- PaySim is a synthetic dataset and does not represent actual customer banking transactions.
- Model performance on synthetic data does not guarantee real-world fraud detection accuracy.
- The current application provides request-response transaction scoring, not a production payment-processing integration.
- The system is an educational and portfolio prototype, not a production-validated financial security system.

Potential future improvements include:

- Testing on additional real-world, appropriately licensed datasets.
- Authentication and role-based access control.
- Advanced fraud monitoring and alerting.
- Model drift monitoring and periodic retraining.
- Integration with payment systems and external risk signals.

## Author

**Deva Yadasi**
B.Tech | National Institute of Technology Warangal

GitHub: [https://github.com/Devayadasi](https://github.com/Devayadasi)

---

*PayGuard AI – Making transaction risk detection more transparent through machine learning and explainable AI.*
