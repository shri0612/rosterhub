import os
import time
import requests


WORKFORCE_API_BASE_URL = os.getenv("WORKFORCE_API_BASE_URL", "").rstrip("/")
WORKFORCE_ANALYSE_REQUEST_PATH = os.getenv("WORKFORCE_ANALYSE_REQUEST_PATH", "/api/v1/workforce/analyse-request")
WORKFORCE_ANALYSE_RESULT_PATH = os.getenv("WORKFORCE_ANALYSE_RESULT_PATH", "/api/v1/workforce/analyse-result")


def _request_url():
    return f"{WORKFORCE_API_BASE_URL}{WORKFORCE_ANALYSE_REQUEST_PATH}"


def _result_url():
    return f"{WORKFORCE_API_BASE_URL}{WORKFORCE_ANALYSE_RESULT_PATH}"


def submit_analysis_request(payload: dict, timeout: int = 15) -> dict:
    if not WORKFORCE_API_BASE_URL:
        msg = "WORKFORCE_API_BASE_URL not configured."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}

    try:
        print(f"[ANALYTICS] SUBMIT -> URL: {_request_url()}")
        print(f"[ANALYTICS] SUBMIT -> Payload: {payload}")

        response = requests.post(
            _request_url(),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        body = response.json()

        print(f"[ANALYTICS] SUBMIT <- HTTP {response.status_code}")
        print(f"[ANALYTICS] SUBMIT <- Response: {body}")

        return {
            "success": True,
            "job_id": body.get("job_id"),
            "status": body.get("status"),
            "raw": body,
        }

    except requests.exceptions.Timeout:
        msg = "Workforce API submit timed out. Possible reason: friend's EC2 instance is stopped or API is slow."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}

    except requests.exceptions.RequestException as e:
        msg = f"Workforce API submit failed: {str(e)}. Possible reason: friend's EC2 instance is stopped / API down / wrong URL."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}

    except ValueError:
        msg = "Workforce API submit returned invalid JSON."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}


def fetch_analysis_result(job_id: str, timeout: int = 15) -> dict:
    if not WORKFORCE_API_BASE_URL:
        msg = "WORKFORCE_API_BASE_URL not configured."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}

    try:
        print(f"[ANALYTICS] RESULT -> URL: {_result_url()}?job_id={job_id}")

        response = requests.get(
            _result_url(),
            params={"job_id": job_id},
            timeout=timeout,
        )
        response.raise_for_status()
        body = response.json()

        print(f"[ANALYTICS] RESULT <- HTTP {response.status_code}")
        print(f"[ANALYTICS] RESULT <- Response: {body}")

        return {
            "success": True,
            "status": body.get("status"),
            "job_id": body.get("job_id"),
            "result": body.get("result"),
            "raw": body,
        }

    except requests.exceptions.Timeout:
        msg = "Workforce API result polling timed out. Possible reason: friend's EC2 instance is stopped or API is slow."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}

    except requests.exceptions.RequestException as e:
        msg = f"Workforce API result polling failed: {str(e)}. Possible reason: friend's EC2 instance is stopped / API down."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}

    except ValueError:
        msg = "Workforce API result polling returned invalid JSON."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {"success": False, "error": msg}


def submit_and_wait_for_analysis(payload: dict, max_retries: int = 6, delay_seconds: int = 2) -> dict:
    submit_result = submit_analysis_request(payload)
    if not submit_result.get("success"):
        return {
            "success": False,
            "error": submit_result.get("error", "Failed to submit analysis request."),
            "job_id": None,
        }

    job_id = submit_result.get("job_id")
    if not job_id:
        msg = "Workforce API did not return a job_id."
        print(f"[ANALYTICS][ERROR] {msg}")
        return {
            "success": False,
            "error": msg,
            "job_id": None,
        }

    for _ in range(max_retries):
        result_response = fetch_analysis_result(job_id)
        if not result_response.get("success"):
            return {
                "success": False,
                "error": result_response.get("error", "Failed to fetch analysis result."),
                "job_id": job_id,
            }

        status = (result_response.get("status") or "").lower()
        print(f"[ANALYTICS] POLL job_id={job_id} status={status}")

        if status == "completed":
            print(f"[ANALYTICS] COMPLETED job_id={job_id}")
            return {
                "success": True,
                "job_id": job_id,
                "result": result_response.get("result") or {},
            }

        if status == "failed":
            msg = "Workforce API returned failed status."
            print(f"[ANALYTICS][ERROR] {msg} job_id={job_id}")
            return {
                "success": False,
                "job_id": job_id,
                "error": msg,
            }

        time.sleep(delay_seconds)

    msg = f"Analysis result still pending after retries (job_id={job_id})."
    print(f"[ANALYTICS][ERROR] {msg}")
    return {
        "success": False,
        "job_id": job_id,
        "error": msg,
    }