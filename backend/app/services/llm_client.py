import json
import os
from typing import Any
import httpx


class LLMClientError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMTimeoutError(LLMClientError):
    """Raised when the LLM provider times out."""
    pass


class LLMUnavailableError(LLMClientError):
    """Raised when the LLM endpoint is unreachable or returns 5xx."""
    pass


class LLMResponseValidationError(LLMClientError):
    """Raised when the model response fails strict JSON or schema parsing."""
    pass


def get_llm_config() -> dict[str, Any]:
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    api_key = os.environ.get("LLM_API_KEY", "").strip()

    # If no key or provider is explicitly 'mock', use mock provider
    if not api_key or provider == "mock":
        provider = "mock"
    elif not provider:
        provider = "deepseek"

    default_urls = {
        "deepseek": "https://api.deepseek.com/v1",
        "openai": "https://api.openai.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "ollama": "http://localhost:11434/v1",
    }
    default_models = {
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-1.5-flash",
        "ollama": "llama3",
        "mock": "deterministic-mock-v1",
    }

    base_url = os.environ.get("LLM_BASE_URL", "").strip() or default_urls.get(provider, "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "").strip() or default_models.get(provider, "gpt-4o-mini")

    try:
        timeout = float(os.environ.get("LLM_TIMEOUT", "30"))
    except ValueError:
        timeout = 30.0

    try:
        temp = float(os.environ.get("LLM_TEMPERATURE", "0.1"))
    except ValueError:
        temp = 0.1

    try:
        max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2048"))
    except ValueError:
        max_tokens = 2048

    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),
        "model": model,
        "timeout": timeout,
        "temperature": temp,
        "max_tokens": max_tokens,
    }


def call_llm(messages: list[dict[str, str]], json_mode: bool = True) -> str:
    """
    Sends request to the configured LLM provider using OpenAI-compatible chat completions protocol.
    Returns the raw string output of the assistant response.
    """
    config = get_llm_config()

    if config["provider"] == "mock":
        return generate_mock_llm_response(messages)

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    endpoint = f"{config['base_url']}/chat/completions"

    payload: dict[str, Any] = {
        "model": config["model"],
        "messages": messages,
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        with httpx.Client(timeout=config["timeout"]) as client:
            resp = client.post(endpoint, headers=headers, json=payload)

            if resp.status_code == 401 or resp.status_code == 403:
                raise LLMUnavailableError(
                    f"LLM authentication failed with provider '{config['provider']}'. Please verify your LLM_API_KEY."
                )
            elif resp.status_code == 429:
                raise LLMUnavailableError(
                    f"LLM rate limit reached with provider '{config['provider']}'. Please retry in a few moments."
                )
            elif resp.status_code >= 500:
                raise LLMUnavailableError(
                    f"LLM provider '{config['provider']}' service unavailable (status {resp.status_code})."
                )
            elif resp.status_code >= 400:
                raise LLMClientError(
                    f"LLM provider returned error status {resp.status_code}: {resp.text}"
                )

            data = resp.json()
            choices = data.get("choices", [])
            if not choices or "message" not in choices[0]:
                raise LLMResponseValidationError("LLM response did not contain expected choices structure.")

            content = choices[0]["message"].get("content", "")
            if not content:
                raise LLMResponseValidationError("LLM returned an empty content message.")
            return content.strip()

    except httpx.TimeoutException as te:
        raise LLMTimeoutError(f"Request to LLM provider timed out after {config['timeout']} seconds.") from te
    except httpx.NetworkError as ne:
        raise LLMUnavailableError(f"Network error connecting to LLM provider endpoint: {str(ne)}") from ne
    except (LLMClientError, LLMTimeoutError, LLMUnavailableError, LLMResponseValidationError):
        raise
    except Exception as e:
        raise LLMClientError(f"Unexpected error communicating with LLM provider: {str(e)}") from e


def generate_mock_llm_response(messages: list[dict[str, str]]) -> str:
    """
    Deterministic offline fallback provider.
    Inspects messages for case context, evidence IDs, and verification findings,
    and returns a schema-valid grounded investigation JSON response.
    """
    prompt_str = "\n".join(m.get("content", "") for m in messages)

    # Check if this is a follow-up chat message or a full investigation
    is_chat = any("investigator question:" in m.get("content", "").lower() for m in messages)

    if is_chat:
        # Return conversational answer citing evidence
        return (
            "Based on the case records and uploaded evidence, the delivery proof was reported on "
            "the courier dispatch slip while the order invoice details the commercial agreement. "
            "All findings are recorded in the documentary audit. If additional tracking information is needed, "
            "requesting an official carrier delivery manifest is recommended."
        )

    # Full investigation analysis:
    # Find evidence IDs mentioned in prompt
    import re
    ev_ids = re.findall(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", prompt_str)
    # Deduplicate while preserving order
    valid_cited_ids = list(dict.fromkeys(ev_ids))

    has_critical = "TIMELINE_INVERSION" in prompt_str or "PAYMENT_STATUS_FAILED" in prompt_str or "CRITICAL" in prompt_str
    has_amount_mismatch = "AMOUNT_MISMATCH" in prompt_str
    has_missing_evidence = "MISSING_" in prompt_str or "NO_EVIDENCE" in prompt_str

    observations = []
    discrepancies = []
    missing_info = []
    recommendations = []

    if valid_cited_ids:
        observations.append({
            "title": "Documentary Evidence Analyzed",
            "observation": f"Successfully examined {len(valid_cited_ids)} verified documentary evidence record(s).",
            "domain": "ORDER",
            "evidence_ids": valid_cited_ids[:2],
            "is_supported": True,
            "support_note": "Corroborated against registered case evidence records."
        })

    if has_critical:
        discrepancies.append({
            "code": "CRITICAL_TIMELINE_OR_STATUS_ANOMALY",
            "severity": "CRITICAL",
            "title": "Severe Documentary Inconsistency Identified",
            "explanation": "Chronological timeline anomaly or failed payment status detected. The sequence of events contradicts standard commercial practices.",
            "evidence_ids": valid_cited_ids[:2]
        })
        recommendations.append({
            "priority": "HIGH",
            "action": "Request Official Carrier Tracking Manifest",
            "rationale": "Verify actual physical dispatch and delivery timestamps directly with courier API or carrier representative."
        })

    if has_amount_mismatch:
        discrepancies.append({
            "code": "FINANCIAL_AMOUNT_DISCREPANCY",
            "severity": "WARNING",
            "title": "Invoice vs Payment Amount Variance",
            "explanation": "The order total claimed on the invoice diverges from the amount reported on the payment slip.",
            "evidence_ids": valid_cited_ids[:2]
        })
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Obtain Bank Settlement Statement",
            "rationale": "Confirm exact net funds received in merchant merchant account to resolve receipt discrepancy."
        })

    if has_missing_evidence:
        missing_info.append("Carrier proof of delivery or signed delivery confirmation is missing from the evidence locker.")
        recommendations.append({
            "priority": "HIGH",
            "action": "Demand Delivery Proof from Seller",
            "rationale": "Seller has not supplied a signed delivery receipt or courier manifest for this dispute."
        })

    if not observations:
        observations.append({
            "title": "Evidence Sufficiency Check",
            "observation": "Documentary claims could not be corroborated due to lack of uploaded files.",
            "domain": "ORDER",
            "evidence_ids": [],
            "is_supported": True,
            "support_note": "No evidence uploaded."
        })

    if not recommendations:
        recommendations.append({
            "priority": "LOW",
            "action": "Standard Settlement Processing",
            "rationale": "Evidence documents appear consistent with registered case declarations."
        })

    mock_investigation = {
        "summary": "FraudShield AI Investigation Agent synthesized case declarations, document intelligence, and deterministic verification findings. "
                   "All findings are based strictly on uploaded documentary records and must be reviewed by a human fraud investigator before final adjudication.",
        "key_observations": observations,
        "identified_discrepancies": discrepancies,
        "missing_information": missing_info,
        "recommended_actions": recommendations,
        "supporting_evidence_ids": valid_cited_ids,
        "related_verification_codes": ["TIMELINE_INVERSION_DELIVERY_BEFORE_ORDER"] if has_critical else [],
        "confidence_explanation": "Findings represent cross-document comparison of submitted files. Receipts and tracking slips represent unverified party claims until confirmed by banking or carrier authorities.",
        "human_review_status": "pending_review",
    }
    return json.dumps(mock_investigation)

