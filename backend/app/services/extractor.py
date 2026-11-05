import re
from typing import Any


def clean_val(val: str | None) -> str | None:
    if not val:
        return None
    val = val.strip(" :.-,;\"'`‘\n\r\t")
    return val if len(val) > 0 else None


def extract_document_intelligence(raw_text: str) -> dict[str, Any]:
    """
    Applies deterministic heuristic patterns to extract financial, order, and courier tracking fields
    from OCR raw text. Returns dictionary of extracted fields without fabricating missing values.
    Store unavailable fields as None.
    """
    empty_result: dict[str, Any] = {
        # Payment fields
        "transaction_id": None,
        "payment_amount": None,
        "currency": None,
        "payment_date": None,
        "payment_status": None,
        "sender_name": None,
        "receiver_name": None,
        "payment_reference": None,
        # Order fields
        "order_id": None,
        "order_date": None,
        "product_description": None,
        "order_amount": None,
        "customer_information": None,
        # Delivery fields
        "tracking_number": None,
        "delivery_date": None,
        "delivery_status": None,
        "recipient_information": None,
        "delivery_address": None,
    }

    if not raw_text or not raw_text.strip():
        return empty_result

    text = raw_text

    # --- 1. PAYMENT EXTRACTION ---

    # 1.1 Transaction ID
    txn_match = re.search(
        r"(?:transaction\s*(?:id|1d|ref(?:erence)?|no\.?|#)|txn\s*(?:id|1d|ref|no\.?|#)|utr(?:\s*no\.?)?)[\s:.-]*([A-Za-z0-9\-_]{6,40})",
        text,
        re.IGNORECASE,
    )
    transaction_id = clean_val(txn_match.group(1)) if txn_match else None
    if not transaction_id:
        fallback_txn = re.search(r"\b(TXN-[0-9]{4,16}|UTR[0-9]{8,18})\b", text, re.IGNORECASE)
        if fallback_txn:
            transaction_id = fallback_txn.group(1).strip()

    # 1.2 Payment Reference
    ref_match = re.search(
        r"(?:payment\s*ref(?:erence)?(?:\s*no\.?|#)?|upi\s*ref(?:erence)?(?:\s*no\.?|#)?|bank\s*ref(?:erence)?(?:\s*no\.?|#)?|ref(?:erence)?\s*(?:no\.?|#)|ref\s*code)[\s:.-]*([A-Za-z0-9\-_]{6,40})",
        text,
        re.IGNORECASE,
    )
    payment_reference = clean_val(ref_match.group(1)) if ref_match else None
    # If transaction_id and payment_reference ended up identical, that's fine, but if ref is distinct, capture it
    if not payment_reference and not transaction_id:
        gen_ref = re.search(r"(?:reference|ref)[\s:.-]*([A-Za-z0-9\-_]{6,40})", text, re.IGNORECASE)
        if gen_ref:
            payment_reference = clean_val(gen_ref.group(1))

    # 1.3 Currency and Payment Amount
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
            raw_amt = clean_val(raw_amt)
            if raw_amt and "," in raw_amt and len(raw_amt.split(",")[-1]) == 2 and "." not in raw_amt:
                raw_amt = raw_amt.rsplit(",", 1)[0] + "." + raw_amt.rsplit(",", 1)[1]
            payment_amount = raw_amt
        if curr_token:
            currency = curr_token.strip()

    if not currency:
        curr_scan = re.search(r"\b(INR|USD|EUR|GBP|₹|\$|€|£)\b", text)
        if curr_scan:
            currency = curr_scan.group(1).strip()

    # 1.4 Payment Date
    date_pattern = r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})"
    date_match = re.search(
        rf"(?:date|paid\s*on|payment\s*date|txn\s*date)[\s:.-]*{date_pattern}",
        text,
        re.IGNORECASE,
    )
    payment_date = clean_val(date_match.group(1)) if date_match else None

    # 1.5 Payment Status
    status_match = re.search(
        r"(?:payment\s*status|payment\s*state|status)[\s:.-]*(success(?:ful)?|paid|completed|pending|failed|declined|settled)",
        text,
        re.IGNORECASE,
    )
    payment_status = clean_val(status_match.group(1).capitalize()) if status_match else None
    if not payment_status:
        # Check for standalone status indicator if payment context exists
        quick_pay_status = re.search(r"\b(SUCCESS|PAID|COMPLETED|SETTLED|PAYMENT FAILED)\b", text, re.IGNORECASE)
        if quick_pay_status and (payment_amount or transaction_id or "receipt" in text.lower()):
            payment_status = quick_pay_status.group(1).capitalize()

    # 1.6 Sender Name
    sender_match = re.search(
        r"\b(?:from|sender|payer|billed\s*to)\b[\s:.-]*([A-Za-z][a-zA-Z\s\.]{2,40})",
        text,
        re.IGNORECASE,
    )
    sender_name = clean_val(sender_match.group(1)) if sender_match else None
    if sender_name and "\n" in sender_name:
        sender_name = sender_name.split("\n")[0].strip()

    # 1.7 Receiver Name
    receiver_match = re.search(
        r"\b(?:to|merchant(?:\s*name)?|seller(?:\s*name)?|beneficiary|payee)\b[\s:.-]*([A-Za-z][a-zA-Z\s\.]{2,40})",
        text,
        re.IGNORECASE,
    )
    receiver_name = clean_val(receiver_match.group(1)) if receiver_match else None
    if receiver_name and "\n" in receiver_name:
        receiver_name = receiver_name.split("\n")[0].strip()

    # --- 2. ORDER EXTRACTION ---

    # 2.1 Order ID
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

    # 2.2 Order Date
    order_date_match = re.search(
        rf"(?:order\s*date|ordered\s*(?:on|at)|invoice\s*date|purchase\s*date)[\s:.-]*{date_pattern}",
        text,
        re.IGNORECASE,
    )
    order_date = clean_val(order_date_match.group(1)) if order_date_match else None

    # 2.3 Product Description
    product_match = re.search(
        r"(?:product(?:\s*name|\s*desc(?:ription)?)?|item(?:\s*name|\s*desc(?:ription)?)?|description)[\s:.-]*([A-Za-z0-9][^\n\r]{2,80})",
        text,
        re.IGNORECASE,
    )
    product_description = clean_val(product_match.group(1)) if product_match else None
    if product_description and "\n" in product_description:
        product_description = product_description.split("\n")[0].strip()

    # 2.4 Order Amount
    order_amt_match = re.search(
        r"(?:order\s*total|order\s*amount|subtotal|invoice\s*total)[\s:.-]*([₹$€£]|INR|USD|EUR|GBP|Rs\.?)?\s*([\d,]+(?:[\.,]\d{2})?)",
        text,
        re.IGNORECASE,
    )
    order_amount = None
    if order_amt_match:
        raw_order_amt = order_amt_match.group(2)
        if raw_order_amt and any(c.isdigit() for c in raw_order_amt):
            order_amount = clean_val(raw_order_amt)

    # 2.5 Customer Information
    customer_match = re.search(
        r"(?:customer(?:\s*name|\s*info|\s*details)?|buyer(?:\s*name)?|client)[\s:.-]*([A-Za-z0-9][a-zA-Z0-9\s,\.@\-_]{2,60})",
        text,
        re.IGNORECASE,
    )
    customer_information = clean_val(customer_match.group(1)) if customer_match else None
    if customer_information and "\n" in customer_information:
        customer_information = customer_information.split("\n")[0].strip()

    # --- 3. DELIVERY EXTRACTION ---

    # 3.1 Tracking Number
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

    # 3.2 Delivery Date
    del_date_match = re.search(
        rf"(?:delivery\s*date|delivered\s*on|expected\s*delivery|dispatched\s*on)[\s:.-]*{date_pattern}",
        text,
        re.IGNORECASE,
    )
    delivery_date = clean_val(del_date_match.group(1)) if del_date_match else None

    # 3.3 Delivery Status
    del_status_match = re.search(
        r"(?:delivery\s*status|shipment\s*status|courier\s*status)[\s:.-]*(delivered|in\s*transit|out\s*for\s*delivery|dispatched|returned|undelivered)",
        text,
        re.IGNORECASE,
    )
    delivery_status = clean_val(del_status_match.group(1).capitalize()) if del_status_match else None
    if not delivery_status:
        quick_del = re.search(r"\b(Delivered|In Transit|Out for Delivery|Dispatched|Returned)\b", text, re.IGNORECASE)
        if quick_del and (tracking_number or "courier" in text.lower() or "delivery" in text.lower() or "shipment" in text.lower()):
            delivery_status = quick_del.group(1).capitalize()

    # 3.4 Recipient Information
    recip_match = re.search(
        r"(?:recipient(?:\s*name|\s*info)?|deliver\s*to|consignee|ship\s*to)[\s:.-]*([A-Za-z0-9][a-zA-Z0-9\s,\.@\-_]{2,60})",
        text,
        re.IGNORECASE,
    )
    recipient_information = clean_val(recip_match.group(1)) if recip_match else None
    if recipient_information and "\n" in recipient_information:
        recipient_information = recipient_information.split("\n")[0].strip()

    # 3.5 Delivery Address
    addr_match = re.search(
        r"(?:delivery\s*address|shipping\s*address|ship\s*to\s*address|destination(?:\s*address)?)[\s:.-]*([A-Za-z0-9#][^\n\r]{5,100})",
        text,
        re.IGNORECASE,
    )
    delivery_address = clean_val(addr_match.group(1)) if addr_match else None

    return {
        # Payment fields
        "transaction_id": transaction_id,
        "payment_amount": payment_amount,
        "currency": currency,
        "payment_date": payment_date,
        "payment_status": payment_status,
        "sender_name": sender_name,
        "receiver_name": receiver_name,
        "payment_reference": payment_reference,
        # Order fields
        "order_id": order_id,
        "order_date": order_date,
        "product_description": product_description,
        "order_amount": order_amount,
        "customer_information": customer_information,
        # Delivery fields
        "tracking_number": tracking_number,
        "delivery_date": delivery_date,
        "delivery_status": delivery_status,
        "recipient_information": recipient_information,
        "delivery_address": delivery_address,
    }
