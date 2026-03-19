import os
import requests


PAYROLL_API_URL = os.getenv("PAYROLL_API_URL")


def call_payroll_api(payload: dict, timeout: int = 15) -> dict:
    """
    Calls the external Payroll Calculator API (AWS Lambda via API Gateway).

    Returns normalized response:
    {
        "success": True/False,
        "data": {...},
        "error": "..."
    }
    """
    if not PAYROLL_API_URL:
        msg = "PAYROLL_API_URL is not configured in environment variables."
        print(f"[PAYROLL][ERROR] {msg}")
        return {
            "success": False,
            "error": msg
        }

    try:
        print(f"[PAYROLL] REQUEST -> URL: {PAYROLL_API_URL}")
        print(f"[PAYROLL] REQUEST -> Payload: {payload}")
        print("[PAYROLL] REQUEST -> Target expected: AWS API Gateway -> Lambda")

        response = requests.post(PAYROLL_API_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        body = response.json()

        print(f"[PAYROLL] RESPONSE <- HTTP {response.status_code}")
        print(f"[PAYROLL] RESPONSE <- Body: {body}")

        if body.get("success") is True:
            print("[PAYROLL] SUCCESS <- Payroll calculated by external API (AWS Lambda).")
            return {
                "success": True,
                "data": body.get("data", {})
            }

        print("[PAYROLL][ERROR] API returned success=False")
        return {
            "success": False,
            "error": body.get("error", "Payroll API returned unsuccessful response.")
        }

    except requests.exceptions.Timeout:
        msg = "Payroll API request timed out. Possible issue: API Gateway/Lambda unavailable or slow."
        print(f"[PAYROLL][ERROR] {msg}")
        return {"success": False, "error": msg}

    except requests.exceptions.RequestException as e:
        msg = f"Payroll API request failed: {str(e)}"
        print(f"[PAYROLL][ERROR] {msg}")
        return {"success": False, "error": msg}

    except ValueError:
        msg = "Payroll API returned invalid JSON."
        print(f"[PAYROLL][ERROR] {msg}")
        return {"success": False, "error": msg}