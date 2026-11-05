import re
from typing import Any


def clean_val(val: str | None) -> str | None:
    if not val:
        return None
    val = val.strip(" :.-,;\"'`‘\n\r\t")
    return val if len(val) > 0 else None


def extract_document_intelligence(raw_text: str) -> dict[str, Any]:
    """
    Applies deterministic heuristic patterns to extract financial and courier tracking fields
    from OCR raw text. Returns dictionary of extracted fields without fabricating missing values.
    """
    if not raw_text or not raw_text.strip():
        return {
            "transaction_id": None,
            "order_id": None,
            "payment_amount": None,
            "currency": None,
            "payment_date": None,
            "payment_status": None,
            "sender_name": None,
            "receiver_name": None,
            "tracking_number": None,
            "delivery_date": None,
            "delivery_status": None,
        }

    text = raw_text

    # 1. Transaction ID
    txn_match = re.search(
        r"(?:transaction\s*(?:id|1d|ref(?:erence)?|no\.?|#)|txn\s*(?:id|1d|ref|no\.?|#)|utr(?:\s*no\.?)?|ref\s*no\.?|reference)[\s:.-]*([A-Za-z0-9\-_]{6,40})",
        text,
        re.IGNORECASE,
    )
    transaction_id = clean_val(txn_match.group(1)) if txn_match else None

    # Fallback transaction ID if pattern like TXN-5001 or UTR123456789 exists isolated
    if not transaction_id:
        fallback_txn = re.search(r"\b(TXN-[0-9]{4,16}|UTR[0-9]{8,18})\b", text, re.IGNORECASE)
        if fallback_txn:
            transaction_id = fallback_txn.group(1).strip()

    # 2. Order ID
    order_match = re.search(
        r"(?:order\s*(?:id|1d|number|no\.?|#)|ord[\-_])[\s:.-]*([A-Za-z0-9\-_]{4,40})",
        text,
        re.IGNORECASE,
    )
    order_id = clean_val(order_match.group(1)) if order_match else None
    if not order_id:
        fallback_ord = re.search(r"\b(ORD[\-_]?[0-9A-Za-z]{3,12})\b", text, re.IGNORECASE)
        if fallback_ord:
            order_id = fallback_ord.group(1).strip()

    # 3. Currency and Payment Amount
    amount_match = re.search(
        r"(?:['\"‘`]?\s*(?:total\s*(?:amount)?|amount\s*paid|grand\s*total|invoice\s*amount|amount))[\s:.-]*([₹$€£]|INR|USD|EUR|GBP|Rs\.?)?\s*([\d,]+(?:[\.,]\d{2})?)",
        text,
        re.IGNORECASE,
    )
    currency = None
    payment_amount = None

    if amount_match:
        curr_token = amount_match.group(1)
        raw_amt = amount_match.group(2)
        if raw_amt and any(c.isdigit() for c in raw_amt):
            # Clean trailing punctuation
            raw_amt = clean_val(raw_amt)
            # If formatted like 499,00 or 4999,00 normalize to decimal
            if raw_amt and "," in raw_amt and len(raw_amt.split(",")[-1]) == 2 and "." not in raw_amt:
                raw_amt = raw_amt.rsplit(",", 1)[0] + "." + raw_amt.rsplit(",", 1)[1]
            payment_amount = raw_amt
        if curr_token:
            currency = curr_token.strip()

    # If currency not found in amount line, scan globally
    if not currency:
        curr_scan = re.search(r"\b(INR|USD|EUR|GBP|₹|\$|€|£)\b", text)
        if curr_scan:
            currency = curr_scan.group(1).strip()

    # 4. Payment Date
    date_pattern = r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})"
    date_match = re.search(
        rf"(?:date|paid\s*on|payment\s*date|txn\s*date)[\s:.-]*{date_pattern}",
        text,
        re.IGNORECASE,
    )
    payment_date = clean_val(date_match.group(1)) if date_match else None

    # 5. Payment Status
    status_match = re.search(
        r"(?:payment\s*status|payment\s*state|status)[\s:.-]*(success(?:ful)?|paid|completed|pending|failed|declined|settled)",
        text,
        re.IGNORECASE,
    )
    payment_status = clean_val(status_match.group(1).capitalize()) if status_match else None

    # 6. Sender Name
    sender_match = re.search(
        r"(?:from|sender|payer|customer(?:\s*name)?|billed\s*to)[\s:.-]*([A-Za-z][a-zA-Z\s\.]{2,40})",
        text,
        re.IGNORECASE,
    )
    sender_name = clean_val(sender_match.group(1)) if sender_match else None
    if sender_name and "\n" in sender_name:
        sender_name = sender_name.split("\n")[0].strip()

    # 7. Receiver Name
    receiver_match = re.search(
        r"(?:to|recipient|receiver|merchant(?:\s*name)?|seller(?:\s*name)?|beneficiary)[\s:.-]*([A-Za-z][a-zA-Z\s\.]{2,40})",
        text,
        re.IGNORECASE,
    )
    receiver_name = clean_val(receiver_match.group(1)) if receiver_match else None
    if receiver_name and "\n" in receiver_name:
        receiver_name = receiver_name.split("\n")[0].strip()

    # 8. Tracking Number
    track_match = re.search(
        r"(?:tracking\s*(?:number|no\.?|id|1d|#)|awb(?:\s*no\.?)?|consignment\s*no\.?|waybill)[\s:.-]*([A-Za-z0-9][A-Za-z0-9\s\-]{4,35})",
        text,
        re.IGNORECASE,
    )
    tracking_number = clean_val(track_match.group(1)) if track_match else None
    if tracking_number:
        if "\n" in tracking_number:
            tracking_number = tracking_number.split("\n")[0].strip()
        if re.match(r"^[A-Za-z0-9\s\-]+$", tracking_number):
            tracking_number = tracking_number.replace(" ", "")

    if not tracking_number:
        fallback_track = re.search(r"\b(TRK[0-9A-Za-z]{6,25})\b", text, re.IGNORECASE)
        if fallback_track:
            tracking_number = fallback_track.group(1).strip()

    # 9. Delivery Date
    del_date_match = re.search(
        rf"(?:delivery\s*date|delivered\s*on|expected\s*delivery|dispatched\s*on)[\s:.-]*{date_pattern}",
        text,
        re.IGNORECASE,
    )
    delivery_date = clean_val(del_date_match.group(1)) if del_date_match else None

    # 10. Delivery Status
    del_status_match = re.search(
        r"(?:delivery\s*status|shipment\s*status|courier\s*status)[\s:.-]*(delivered|in\s*transit|out\s*for\s*delivery|dispatched|returned|undelivered)",
        text,
        re.IGNORECASE,
    )
    delivery_status = clean_val(del_status_match.group(1).capitalize()) if del_status_match else None

    # Fallback delivery status if keyword present
    if not delivery_status:
        quick_del = re.search(r"\b(Delivered|In Transit|Out for Delivery|Dispatched|Returned)\b", text, re.IGNORECASE)
        if quick_del and (tracking_number or "courier" in text.lower() or "delivery" in text.lower()):
            delivery_status = quick_del.group(1).capitalize()

    return {
        "transaction_id": transaction_id,
        "order_id": order_id,
        "payment_amount": payment_amount,
        "currency": currency,
        "payment_date": payment_date,
        "payment_status": payment_status,
        "sender_name": sender_name,
        "receiver_name": receiver_name,
        "tracking_number": tracking_number,
        "delivery_date": delivery_date,
        "delivery_status": delivery_status,
    }
