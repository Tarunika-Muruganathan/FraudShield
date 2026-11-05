from datetime import datetime, timezone
import json
import re
from typing import Any

from app.models.case import Case
from app.models.evidence import Evidence


def parse_date_str(date_str: str | None) -> datetime | None:
    """
    Parses ambiguous date strings into a timezone-aware UTC datetime for safe chronological comparison.
    """
    if not date_str:
        return None
    cleaned = date_str.strip()
    if not cleaned:
        return None

    # Handle standard ISO formats
    iso_match = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", cleaned)
    if iso_match:
        try:
            year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            return datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
        except ValueError:
            pass

    # Common date formats
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y.%m.%d",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d %Y",
        "%B %d %Y",
    ]

    # Clean punctuation
    candidate = re.sub(r"(st|nd|rd|th),?", "", cleaned, flags=re.IGNORECASE).strip()
    for fmt in formats:
        try:
            dt = datetime.strptime(candidate, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def parse_amount_val(amt_str: str | None) -> float | None:
    """
    Normalizes currency / amount strings (e.g. '$249.99', '1,250.00', '249,99') into floats.
    """
    if not amt_str:
        return None
    cleaned = re.sub(r"[^0-9.,]", "", str(amt_str)).strip()
    if not cleaned:
        return None

    # European format with comma as decimal (e.g. 249,99)
    if "," in cleaned and "." not in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]

    # Standard comma-separated thousands (e.g. 1,249.50)
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_str(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", s).lower()


def run_case_verification(case: Case, evidence_items: list[Evidence]) -> dict[str, Any]:
    """
    Deterministic Fraud Verification Engine.
    Cross-references case declarations with extracted evidence intelligence.
    Identifies inconsistencies, timeline inversions, matching claims, and evidence gaps.
    Does not declare guilt or make judicial findings.
    """
    discrepancies: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    missing_evidence: list[dict[str, Any]] = []

    # Filter out evidence items that have document intelligence
    active_evidence = [e for e in evidence_items if e.document_data is not None]
    
    # Check for unreadable documents
    for e in active_evidence:
        if e.document_data.ocr_status == "unreadable":
            missing_evidence.append({
                "code": "UNREADABLE_EVIDENCE_DOCUMENT",
                "severity": "WARNING",
                "title": "Unreadable Evidence File",
                "description": f"Evidence file '{e.filename}' contains unreadable or corrupted document data ({e.document_data.ocr_error or 'OCR yielded no legible characters'}).",
            })

    # --- 1. EVIDENCE SUFFICIENCY CHECKS ---
    if len(evidence_items) == 0:
        missing_evidence.append({
            "code": "NO_EVIDENCE_ATTACHED",
            "severity": "WARNING",
            "title": "No Evidence Attached",
            "description": f"Case {case.order_id} has zero uploaded evidence files. Inconsistencies cannot be evaluated without documentary proof.",
        })

    # Check for presence of delivery proof
    has_delivery_proof = any(
        e.document_data and (e.document_data.tracking_number or e.document_data.delivery_status or e.document_data.delivery_date)
        for e in active_evidence
    )
    if case.dispute_type in ("non_delivery", "fake_delivery") and not has_delivery_proof:
        missing_evidence.append({
            "code": "MISSING_DELIVERY_PROOF",
            "severity": "WARNING",
            "title": "Missing Delivery Proof",
            "description": f"Dispute type is '{case.dispute_type}', but no courier tracking receipt or delivery confirmation was found in the evidence locker.",
        })

    # Check for presence of payment proof
    has_payment_proof = any(
        e.document_data and (e.document_data.transaction_id or e.document_data.payment_amount or e.document_data.payment_reference)
        for e in active_evidence
    )
    if not has_payment_proof and len(evidence_items) > 0:
        missing_evidence.append({
            "code": "MISSING_PAYMENT_PROOF",
            "severity": "WARNING",
            "title": "Missing Payment Proof",
            "description": "No payment receipt, transaction confirmation, or financial documentation has been uploaded.",
        })

    # --- 2. ORDER ID VERIFICATION ---
    case_order_norm = normalize_str(case.order_id)
    order_id_matches = []
    for e in active_evidence:
        doc = e.document_data
        if doc and doc.order_id:
            doc_order_norm = normalize_str(doc.order_id)
            if doc_order_norm == case_order_norm:
                order_id_matches.append(e.evidence_id)
            elif case_order_norm and doc_order_norm:
                discrepancies.append({
                    "code": "ORDER_ID_MISMATCH",
                    "severity": "CRITICAL",
                    "domain": "ORDER",
                    "title": "Order ID Contradiction",
                    "description": f"Declared Case Order ID '{case.order_id}' contradicts document extracted Order ID '{doc.order_id}' in '{e.filename}'.",
                    "evidence_ids": [e.evidence_id],
                })

    if order_id_matches:
        matches.append({
            "domain": "ORDER",
            "title": "Order ID Corroborated",
            "description": f"Order ID '{case.order_id}' was verified across {len(order_id_matches)} evidence document(s).",
            "evidence_ids": order_id_matches,
        })

    # --- 3. TRANSACTION ID & PAYMENT VERIFICATION ---
    case_txn_norm = normalize_str(case.transaction_id)
    seen_txns: dict[str, str] = {}  # txn_norm -> evidence_id

    for e in active_evidence:
        doc = e.document_data
        if not doc:
            continue

        # 3.1 Failed or Declined Status (CRITICAL)
        if doc.payment_status:
            status_clean = doc.payment_status.lower()
            if any(fail_word in status_clean for fail_word in ("fail", "declin", "cancel", "reject")):
                discrepancies.append({
                    "code": "PAYMENT_STATUS_FAILED_OR_DECLINED",
                    "severity": "CRITICAL",
                    "domain": "PAYMENT",
                    "title": "Payment Document Indicates Failure / Decline",
                    "description": f"Uploaded payment document '{e.filename}' indicates payment status '{doc.payment_status}' rather than a successful settlement.",
                    "evidence_ids": [e.evidence_id],
                })
            elif any(succ_word in status_clean for succ_word in ("success", "paid", "complet", "settle")):
                matches.append({
                    "domain": "PAYMENT",
                    "title": "Payment Settlement Claim Reported",
                    "description": f"Document '{e.filename}' reports payment status '{doc.payment_status}'. (Note: self-reported claim, pending bank reconciliation).",
                    "evidence_ids": [e.evidence_id],
                })

        # 3.2 Transaction ID Matching
        if doc.transaction_id:
            txn_norm = normalize_str(doc.transaction_id)
            if case_txn_norm:
                if txn_norm == case_txn_norm:
                    matches.append({
                        "domain": "PAYMENT",
                        "title": "Transaction ID Corroborated",
                        "description": f"Transaction ID '{case.transaction_id}' matches payment evidence '{e.filename}'.",
                        "evidence_ids": [e.evidence_id],
                    })
                else:
                    discrepancies.append({
                        "code": "TRANSACTION_ID_MISMATCH",
                        "severity": "CRITICAL",
                        "domain": "PAYMENT",
                        "title": "Transaction ID Contradiction",
                        "description": f"Declared transaction ID '{case.transaction_id}' conflicts with receipt transaction ID '{doc.transaction_id}' in '{e.filename}'.",
                        "evidence_ids": [e.evidence_id],
                    })

            # Check for multiple contradictory receipts
            if seen_txns and txn_norm not in seen_txns:
                other_ev_id = next(iter(seen_txns.values()))
                discrepancies.append({
                    "code": "MULTIPLE_CONFLICTING_TRANSACTIONS",
                    "severity": "CRITICAL",
                    "domain": "PAYMENT",
                    "title": "Conflicting Transaction References",
                    "description": f"Multiple evidence files report conflicting transaction IDs ('{doc.transaction_id}').",
                    "evidence_ids": [e.evidence_id, other_ev_id],
                })
            seen_txns[txn_norm] = e.evidence_id

    # --- 4. AMOUNT & CURRENCY RECONCILIATION ---
    invoice_amounts = []
    payment_amounts = []

    for e in active_evidence:
        doc = e.document_data
        if not doc:
            continue
        if doc.order_amount:
            val = parse_amount_val(doc.order_amount)
            if val is not None:
                invoice_amounts.append((val, doc.currency or "USD", e.evidence_id))
        if doc.payment_amount:
            val = parse_amount_val(doc.payment_amount)
            if val is not None:
                payment_amounts.append((val, doc.currency or "USD", e.evidence_id))

    # Cross-compare Invoice Order Amount vs Payment Amount
    for inv_val, inv_curr, inv_ev_id in invoice_amounts:
        for pay_val, pay_curr, pay_ev_id in payment_amounts:
            # Currency check
            if inv_curr and pay_curr and inv_curr.upper() != pay_curr.upper():
                discrepancies.append({
                    "code": "CURRENCY_MISMATCH",
                    "severity": "WARNING",
                    "domain": "PAYMENT",
                    "title": "Currency Mismatch",
                    "description": f"Invoice currency '{inv_curr}' contradicts payment receipt currency '{pay_curr}'.",
                    "evidence_ids": [inv_ev_id, pay_ev_id],
                })

            diff = abs(inv_val - pay_val)
            if diff > 0.01:
                variance_pct = (diff / inv_val) * 100 if inv_val > 0 else 100
                is_crit = variance_pct > 25.0 or diff > 100.0
                discrepancies.append({
                    "code": "AMOUNT_MISMATCH_SIGNIFICANT" if is_crit else "AMOUNT_MISMATCH_MINOR",
                    "severity": "CRITICAL" if is_crit else "WARNING",
                    "domain": "PAYMENT",
                    "title": "Financial Amount Discrepancy",
                    "description": f"Invoice order amount ({inv_curr} {inv_val:.2f}) does not match paid receipt amount ({pay_curr} {pay_val:.2f}). Variance: {diff:.2f} ({variance_pct:.1f}%).",
                    "evidence_ids": [inv_ev_id, pay_ev_id],
                })
            else:
                matches.append({
                    "domain": "PAYMENT",
                    "title": "Financial Amount Corroborated",
                    "description": f"Invoice amount and payment receipt amount match exactly at {pay_curr} {pay_val:.2f}.",
                    "evidence_ids": [inv_ev_id, pay_ev_id],
                })

    # --- 5. TIMELINE ANOMALIES & CHRONOLOGY (CRITICAL) ---
    order_dates = []
    payment_dates = []
    delivery_dates = []

    for e in active_evidence:
        doc = e.document_data
        if not doc:
            continue
        if doc.order_date:
            dt = parse_date_str(doc.order_date)
            if dt:
                order_dates.append((dt, doc.order_date, e.evidence_id))
        if doc.payment_date:
            dt = parse_date_str(doc.payment_date)
            if dt:
                payment_dates.append((dt, doc.payment_date, e.evidence_id))
        if doc.delivery_date:
            dt = parse_date_str(doc.delivery_date)
            if dt:
                delivery_dates.append((dt, doc.delivery_date, e.evidence_id))

    # Check: Delivery Date occurs BEFORE Order Date
    for del_dt, del_str, del_ev_id in delivery_dates:
        for ord_dt, ord_str, ord_ev_id in order_dates:
            if del_dt < ord_dt:
                discrepancies.append({
                    "code": "TIMELINE_INVERSION_DELIVERY_BEFORE_ORDER",
                    "severity": "CRITICAL",
                    "domain": "TIMELINE",
                    "title": "Timeline Inversion: Delivery Occurred Before Order",
                    "description": f"Courier delivery date ({del_str}) occurs prior to the commercial order date ({ord_str}). This severe chronological contradiction strongly indicates a recycled or fabricated tracking proof.",
                    "evidence_ids": [del_ev_id, ord_ev_id],
                })
            else:
                matches.append({
                    "domain": "TIMELINE",
                    "title": "Chronological Order-to-Delivery Flow Valid",
                    "description": f"Order date ({ord_str}) precedes courier delivery date ({del_str}).",
                    "evidence_ids": [ord_ev_id, del_ev_id],
                })

    # Check: Delivery Date occurs BEFORE Payment Date
    for del_dt, del_str, del_ev_id in delivery_dates:
        for pay_dt, pay_str, pay_ev_id in payment_dates:
            if del_dt < pay_dt:
                discrepancies.append({
                    "code": "TIMELINE_INVERSION_DELIVERY_BEFORE_PAYMENT",
                    "severity": "CRITICAL",
                    "domain": "TIMELINE",
                    "title": "Timeline Inversion: Delivery Occurred Before Payment",
                    "description": f"Courier delivery date ({del_str}) occurs prior to the payment date ({pay_str}). Shipments are expected to follow payment settlement in commercial transactions.",
                    "evidence_ids": [del_ev_id, pay_ev_id],
                })

    # --- 6. IDENTITY & RECIPIENT RECONCILIATION ---
    cust_norm = normalize_str(case.customer_name)
    for e in active_evidence:
        doc = e.document_data
        if not doc:
            continue
        if doc.recipient_information and cust_norm:
            recip_norm = normalize_str(doc.recipient_information)
            if cust_norm in recip_norm or recip_norm in cust_norm:
                matches.append({
                    "domain": "IDENTITY",
                    "title": "Delivery Recipient Matches Customer",
                    "description": f"Courier delivery recipient '{doc.recipient_information}' matches customer '{case.customer_name}'.",
                    "evidence_ids": [e.evidence_id],
                })
            else:
                discrepancies.append({
                    "code": "RECIPIENT_NAME_MISMATCH",
                    "severity": "WARNING",
                    "domain": "IDENTITY",
                    "title": "Delivery Recipient Divergence",
                    "description": f"Courier proof lists recipient '{doc.recipient_information}' which differs from customer name '{case.customer_name}'.",
                    "evidence_ids": [e.evidence_id],
                })

    # --- 7. DETERMINISTIC RISK SCORING ---
    # Baseline: 10
    # Each CRITICAL: +35 points
    # Each WARNING: +15 points
    # Each MATCH: -5 points
    score = 10
    num_critical = sum(1 for d in discrepancies if d["severity"] == "CRITICAL")
    num_warning = sum(1 for d in discrepancies if d["severity"] == "WARNING") + len(missing_evidence)
    num_matches = len(matches)

    score += (num_critical * 35)
    score += (num_warning * 15)
    score -= (num_matches * 5)
    risk_score = max(0, min(100, score))

    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # --- 8. FORENSIC SUMMARY GENERATOR ---
    summary_parts = [
        f"FraudShield deterministic verification engine evaluated {len(active_evidence)} evidence document(s) against Case {case.order_id}."
    ]
    if num_critical > 0:
        summary_parts.append(f"FLAGGED: {num_critical} critical documentary contradiction(s) detected.")
    if num_warning > 0:
        summary_parts.append(f"{num_warning} warning(s) or evidence deficit(s) identified.")
    if num_matches > 0:
        summary_parts.append(f"{num_matches} claim(s) were successfully corroborated across files.")

    summary_parts.append(
        f"Assessed Risk Score: {risk_score}/100 ({risk_level}). "
        "Investigative Notice: These documentary flags indicate timeline and content inconsistencies across uploaded files. "
        "They do not constitute a legal or judicial determination of fraud or guilt, and must be reviewed by an authorized investigator."
    )
    summary = " ".join(summary_parts)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "summary": summary,
        "discrepancies": discrepancies,
        "matches": matches,
        "missing_evidence": missing_evidence,
    }

