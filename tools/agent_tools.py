import time
import json
from typing import Dict, Any, Tuple


def credit_score_lookup(user_id: str, loan_amount: float) -> Dict[str, Any]:
    """
    Simulates an enterprise credit bureau lookup tool.
    Returns credit score, tier, and debt-to-income (DTI) ratio.
    """
    time.sleep(0.15)  # Simulate network latency
    # Deterministic simulation based on user_id hash for consistent demos/testing
    score_seed = (hash(user_id) % 350) + 500  # Score between 500 and 850
    tier = "EXCELLENT" if score_seed >= 750 else ("GOOD" if score_seed >= 670 else "FAIR" if score_seed >= 580 else "POOR")
    dti_ratio = round(0.28 if score_seed >= 700 else 0.42, 2)
    return {
        "user_id": user_id,
        "credit_score": score_seed,
        "credit_tier": tier,
        "dti_ratio": dti_ratio,
        "bureau_reference_id": f"BUR-2026-{abs(hash(user_id)) % 100000}"
    }


def kyc_verification_check(user_id: str, document_type: str = "PAN") -> Dict[str, Any]:
    """
    Simulates a regulatory KYC & AML verification check.
    """
    time.sleep(0.12)
    return {
        "user_id": user_id,
        "document_type": document_type,
        "kyc_verified": True,
        "aml_flagged": False,
        "compliance_jurisdiction": "IN-US-EU",
        "verification_timestamp": "2026-07-30T10:00:00Z"
    }


def loan_eligibility_calculator(credit_score: int, annual_income: float, requested_loan: float) -> Dict[str, Any]:
    """
    Calculates loan eligibility and assigns an enterprise risk level.
    """
    time.sleep(0.10)
    max_allowable_loan = annual_income * 3.5
    is_eligible = (credit_score >= 650) and (requested_loan <= max_allowable_loan)
    
    if credit_score >= 760 and requested_loan <= (annual_income * 2.0):
        risk_level = "low"
        interest_rate = 8.25
    elif credit_score >= 680 and requested_loan <= max_allowable_loan:
        risk_level = "medium"
        interest_rate = 10.50
    elif credit_score >= 600:
        risk_level = "high"
        interest_rate = 14.75
    else:
        risk_level = "critical"
        interest_rate = 18.00

    return {
        "is_eligible": is_eligible,
        "risk_level": risk_level,
        "assigned_interest_rate_pct": interest_rate,
        "max_allowable_loan_usd": round(max_allowable_loan, 2),
        "policy_rule_applied": "ENTERPRISE_RISK_RULE_402_B"
    }


ENTERPRISE_TOOLS_REGISTRY = {
    "credit_score_lookup": credit_score_lookup,
    "kyc_verification_check": kyc_verification_check,
    "loan_eligibility_calculator": loan_eligibility_calculator,
}
