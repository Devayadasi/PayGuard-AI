
from pathlib import Path
from datetime import datetime, timezone
import json
import os

import joblib
import numpy as np
import pandas as pd
import shap

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field
from typing import Literal

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    func
)

from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# ==========================================================
# 1. CONFIGURATION AND PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

# Use DATABASE_URL if provided.
# Otherwise, construct the connection using Render DB_* variables.

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    db_url = DATABASE_URL
else:
    required_vars = [
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_NAME"
    ]

    missing_vars = [
        key for key in required_vars
        if not os.getenv(key)
    ]

    if missing_vars:
        raise RuntimeError(
            f"Missing database environment variables: {', '.join(missing_vars)}"
        )

    db_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "4000")),
        database=os.getenv("DB_NAME", "payguard_db")
    )

# TiDB Cloud requires an SSL connection.
connect_args = {}

if os.getenv("DB_SSL", "true").lower() == "true":
    connect_args = {
        "ssl_verify_cert": True,
        "ssl_verify_identity": True
    }


# ==========================================================
# 2. LOAD MACHINE LEARNING MODEL
# ==========================================================

MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "fraud_model.joblib"
METADATA_PATH = MODEL_DIR / "metadata.json"

if not MODEL_PATH.exists() or not METADATA_PATH.exists():
    raise FileNotFoundError(
        "Model files not found in backend/app/models/"
    )

model = joblib.load(MODEL_PATH)

with open(METADATA_PATH, "r") as file:
    metadata = json.load(file)

FEATURES = metadata["features"]

APPROVE_LIMIT = metadata["risk_bands"]["approve_below"]
BLOCK_LIMIT = metadata["risk_bands"]["block_from"]


# ==========================================================
# 3. SHAP EXPLAINABILITY ENGINE
# ==========================================================

explainer = shap.TreeExplainer(model)


# ==========================================================
# 4. MYSQL DATABASE CONNECTION
# ==========================================================

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ==========================================================
# 5. DATABASE TABLE
# ==========================================================

class TransactionRecord(Base):

    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    step = Column(Integer, nullable=False)

    transaction_type = Column(
        String(20),
        nullable=False
    )

    amount = Column(Float, nullable=False)

    old_balance_org = Column(
        Float,
        nullable=False
    )

    old_balance_dest = Column(
        Float,
        nullable=False
    )

    fraud_probability = Column(
        Float,
        nullable=False
    )

    risk_score = Column(
        Float,
        nullable=False
    )

    decision = Column(
        String(20),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ==========================================================
# 6. DATABASE SESSION
# ==========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==========================================================
# 7. FASTAPI APPLICATION
# ==========================================================

app = FastAPI(
    title="PayGuard AI",
    description=(
        "AI-powered payment fraud detection "
        "and risk intelligence platform"
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================================
# 8. APPLICATION STARTUP
# ==========================================================

@app.on_event("startup")
def startup():

    try:

        with engine.connect():
            pass

        Base.metadata.create_all(bind=engine)

        print("MySQL connected successfully!")
        print("PayGuard AI transactions table is ready.")
        print("Machine learning model loaded successfully!")
        print("SHAP explainability engine loaded successfully!")

    except Exception as error:

        print(f"Application startup failed: {error}")
        raise


# ==========================================================
# 9. TRANSACTION INPUT SCHEMA
# ==========================================================

class Transaction(BaseModel):

    step: int = Field(ge=0)

    type: Literal[
        "CASH_IN",
        "CASH_OUT",
        "DEBIT",
        "PAYMENT",
        "TRANSFER"
    ]

    amount: float = Field(ge=0)

    oldbalanceOrg: float = Field(ge=0)

    oldbalanceDest: float = Field(ge=0)


# ==========================================================
# 10. FEATURE ENGINEERING
# Must match the Colab training pipeline
# ==========================================================

def prepare_features(transaction: Transaction):

    data = {

        "step": transaction.step,

        "amount": transaction.amount,

        "oldbalanceOrg": transaction.oldbalanceOrg,

        "oldbalanceDest": transaction.oldbalanceDest,

        "amount_to_orig_balance":
            transaction.amount /
            (transaction.oldbalanceOrg + 1),

        "log_amount":
            np.log1p(transaction.amount),

        "hour_sin":
            np.sin(
                2 * np.pi *
                (transaction.step % 24) / 24
            ),

        "hour_cos":
            np.cos(
                2 * np.pi *
                (transaction.step % 24) / 24
            ),

        "type_CASH_IN":
            int(transaction.type == "CASH_IN"),

        "type_CASH_OUT":
            int(transaction.type == "CASH_OUT"),

        "type_DEBIT":
            int(transaction.type == "DEBIT"),

        "type_PAYMENT":
            int(transaction.type == "PAYMENT"),

        "type_TRANSFER":
            int(transaction.type == "TRANSFER")
    }

    features_df = pd.DataFrame([data])

    return features_df[FEATURES]


# ==========================================================
# 11. RISK SCORING AND DECISION ENGINE
# ==========================================================

def calculate_decision(risk_score):

    if risk_score >= BLOCK_LIMIT:
        return "BLOCK"

    elif risk_score >= APPROVE_LIMIT:
        return "REVIEW"

    return "APPROVE"


# ==========================================================
# 12. HOME AND HEALTH ENDPOINTS
# ==========================================================

@app.get("/")
def home():

    return {
        "message": "Welcome to PayGuard AI",
        "status": "API is running",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "model_loaded": True,
        "database": "connected",
        "explainability": "enabled"
    }


# ==========================================================
# 13. MODEL INFORMATION
# ==========================================================

@app.get("/api/model-info")
def model_info():

    return {
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"],
        "features_count": len(FEATURES),
        "features": FEATURES,
        "risk_bands": metadata["risk_bands"],
        "explainability": "SHAP TreeExplainer"
    }


# ==========================================================
# 14. PREDICT TRANSACTION AND SAVE TO MYSQL
# ==========================================================

@app.post("/api/predict")
def predict_transaction(
    transaction: Transaction,
    db: Session = Depends(get_db)
):

    try:

        features = prepare_features(transaction)

        fraud_probability = float(
            model.predict_proba(features)[0][1]
        )

        risk_score = round(
            fraud_probability * 100,
            2
        )

        decision = calculate_decision(risk_score)

        record = TransactionRecord(

            step=transaction.step,

            transaction_type=transaction.type,

            amount=transaction.amount,

            old_balance_org=transaction.oldbalanceOrg,

            old_balance_dest=transaction.oldbalanceDest,

            fraud_probability=fraud_probability,

            risk_score=risk_score,

            decision=decision
        )

        db.add(record)

        db.commit()

        db.refresh(record)

        return {

            "success": True,

            "transaction_id": record.id,

            "transaction": transaction.model_dump(),

            "fraud_probability": round(
                fraud_probability,
                6
            ),

            "risk_score": risk_score,

            "decision": decision,

            "message": f"Transaction classified as {decision}"
        }

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )


# ==========================================================
# 15. TRANSACTION HISTORY
# ==========================================================

@app.get("/api/transactions")
def get_transactions(
    limit: int = 100,
    db: Session = Depends(get_db)
):

    if not 1 <= limit <= 500:

        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 500"
        )

    records = (

        db.query(TransactionRecord)

        .order_by(TransactionRecord.id.desc())

        .limit(limit)

        .all()
    )

    return [

        {

            "id": row.id,

            "step": row.step,

            "type": row.transaction_type,

            "amount": row.amount,

            "fraud_probability": row.fraud_probability,

            "risk_score": row.risk_score,

            "decision": row.decision,

            "created_at": row.created_at.isoformat()

        }

        for row in records
    ]


# ==========================================================
# 16. DASHBOARD STATISTICS
# ==========================================================

@app.get("/api/stats")
def dashboard_stats(
    db: Session = Depends(get_db)
):

    total = (

        db.query(
            func.count(TransactionRecord.id)
        ).scalar() or 0
    )

    results = (

        db.query(
            TransactionRecord.decision,
            func.count(TransactionRecord.id)
        )

        .group_by(TransactionRecord.decision)

        .all()
    )

    counts = {

        "APPROVE": 0,

        "REVIEW": 0,

        "BLOCK": 0
    }

    for decision, count in results:
        counts[decision] = count

    average_risk = (

        db.query(
            func.avg(TransactionRecord.risk_score)
        ).scalar()

        if total else 0
    )

    return {

        "total_transactions": total,

        "approved": counts["APPROVE"],

        "under_review": counts["REVIEW"],

        "blocked": counts["BLOCK"],

        "average_risk_score": round(
            float(average_risk or 0),
            2
        )
    }


# ==========================================================
# 17. SHAP TRANSACTION EXPLAINABILITY
# ==========================================================

@app.get("/api/explain/{transaction_id}")
def explain_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):

    record = (

        db.query(TransactionRecord)

        .filter(
            TransactionRecord.id == transaction_id
        )

        .first()
    )

    if not record:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    try:

        # Reconstruct transaction from database

        transaction = Transaction(

            step=record.step,

            type=record.transaction_type,

            amount=record.amount,

            oldbalanceOrg=record.old_balance_org,

            oldbalanceDest=record.old_balance_dest
        )

        # Prepare model features

        features = prepare_features(transaction)

        # Calculate SHAP values

        shap_values = explainer.shap_values(features)

        # Handle different SHAP output formats

        if isinstance(shap_values, list):

            contributions = np.asarray(
                shap_values[1]
            )[0]

        else:

            values = np.asarray(shap_values)

            if values.ndim == 3:

                contributions = values[0, :, 1]

            elif values.ndim == 2:

                contributions = values[0]

            else:

                raise ValueError(
                    f"Unexpected SHAP output shape: {values.shape}"
                )

        explanations = []

        for feature, contribution in zip(
            FEATURES,
            contributions
        ):

            contribution = float(contribution)

            if contribution > 0:

                impact = "Increases fraud prediction"

            elif contribution < 0:

                impact = "Decreases fraud prediction"

            else:

                impact = "No significant impact"

            explanations.append({

                "feature": feature,

                "contribution": round(
                    contribution,
                    6
                ),

                "impact": impact

            })

        # Rank by absolute contribution

        explanations.sort(

            key=lambda item: abs(
                item["contribution"]
            ),

            reverse=True
        )

        return {

            "success": True,

            "transaction_id": record.id,

            "decision": record.decision,

            "fraud_probability": record.fraud_probability,

            "risk_score": record.risk_score,

            "explanation_method": "SHAP TreeExplainer",

            "explanations": explanations

        }

    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=f"SHAP explanation failed: {str(error)}"

        )
