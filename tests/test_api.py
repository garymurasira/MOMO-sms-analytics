"""
tests/test_api.py
Tests all API endpoints with valid and invalid credentials.
Run with the server already started: python api/server.py
"""

import requests
import json
import os

BASE_URL = "http://localhost:8000"
VALID_AUTH = ("admin", "password123")
INVALID_AUTH = ("wronguser", "wrongpass")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

created_id = None


def save_result(filename, content):
    path = os.path.join(SCREENSHOTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Saved: screenshots/{filename}")


def format_response(label, response):
    return (
        f"=== {label} ===\n"
        f"Status : {response.status_code}\n"
        f"Headers: {dict(response.headers)}\n"
        f"Body   : {response.text[:500]}\n"
        f"{'=' * 50}\n"
    )


def test_get_all_valid():
    print("\n[1] GET /transactions — valid credentials (expect 200)")
    r = requests.get(f"{BASE_URL}/transactions", auth=VALID_AUTH)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert isinstance(data, list), "Expected a list"
    assert len(data) > 0, "Expected non-empty list"
    save_result("01_get_all_200.txt", format_response("GET /transactions — 200 OK", r))
    print(f"  PASS — {len(data)} transactions returned")


def test_get_all_unauthorized():
    print("\n[2] GET /transactions — no credentials (expect 401)")
    r = requests.get(f"{BASE_URL}/transactions")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    assert "WWW-Authenticate" in r.headers, "Expected WWW-Authenticate header"
    save_result("02_get_all_401.txt", format_response("GET /transactions — 401 Unauthorized", r))
    print(f"  PASS — 401 returned with WWW-Authenticate header")


def test_get_all_wrong_credentials():
    print("\n[3] GET /transactions — wrong credentials (expect 401)")
    r = requests.get(f"{BASE_URL}/transactions", auth=INVALID_AUTH)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    save_result("03_get_all_wrong_creds_401.txt", format_response("GET /transactions — wrong creds 401", r))
    print(f"  PASS — 401 returned for wrong credentials")


def test_get_one_valid():
    print("\n[4] GET /transactions/1 — valid credentials (expect 200)")
    r = requests.get(f"{BASE_URL}/transactions/1", auth=VALID_AUTH)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["id"] == 1, "Expected id=1"
    save_result("04_get_one_200.txt", format_response("GET /transactions/1 — 200 OK", r))
    print(f"  PASS — transaction id=1 returned")


def test_get_one_not_found():
    print("\n[5] GET /transactions/99999 — non-existent ID (expect 404)")
    r = requests.get(f"{BASE_URL}/transactions/99999", auth=VALID_AUTH)
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    save_result("05_get_one_404.txt", format_response("GET /transactions/99999 — 404 Not Found", r))
    print(f"  PASS — 404 returned for non-existent ID")


def test_post_valid():
    global created_id
    print("\n[6] POST /transactions — valid credentials (expect 201)")
    payload = {
        "type": "Payment to Code Holder",
        "amount": 5000.0,
        "fee": 100.0,
        "sender": "Merci Ndekwe",
        "receiver": "MTN Rwanda",
        "timestamp": "2024-06-01T09:00:00+00:00"
    }
    r = requests.post(f"{BASE_URL}/transactions", auth=VALID_AUTH, json=payload)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}"
    created_id = r.json().get("id")
    save_result("06_post_201.txt", format_response("POST /transactions — 201 Created", r))
    print(f"  PASS — new transaction created with id={created_id}")


def test_post_unauthorized():
    print("\n[7] POST /transactions — no credentials (expect 401)")
    r = requests.post(f"{BASE_URL}/transactions", json={"amount": 1000})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    save_result("07_post_401.txt", format_response("POST /transactions — 401 Unauthorized", r))
    print(f"  PASS — 401 returned")


def test_put_valid():
    print(f"\n[8] PUT /transactions/{created_id} — valid credentials (expect 200)")
    r = requests.put(f"{BASE_URL}/transactions/{created_id}", auth=VALID_AUTH, json={"amount": 6000.0})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.json()["amount"] == 6000.0, "Expected updated amount"
    save_result("08_put_200.txt", format_response(f"PUT /transactions/{created_id} — 200 OK", r))
    print(f"  PASS — transaction updated")


def test_put_not_found():
    print("\n[9] PUT /transactions/99999 — non-existent ID (expect 404)")
    r = requests.put(f"{BASE_URL}/transactions/99999", auth=VALID_AUTH, json={"amount": 1000})
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    save_result("09_put_404.txt", format_response("PUT /transactions/99999 — 404 Not Found", r))
    print(f"  PASS — 404 returned")


def test_delete_valid():
    print(f"\n[10] DELETE /transactions/{created_id} — valid credentials (expect 204)")
    r = requests.delete(f"{BASE_URL}/transactions/{created_id}", auth=VALID_AUTH)
    assert r.status_code == 204, f"Expected 204, got {r.status_code}"
    save_result("10_delete_204.txt", format_response(f"DELETE /transactions/{created_id} — 204 No Content", r))
    print(f"  PASS — transaction deleted")


def test_delete_not_found():
    print("\n[11] DELETE /transactions/99999 — non-existent ID (expect 404)")
    r = requests.delete(f"{BASE_URL}/transactions/99999", auth=VALID_AUTH)
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    save_result("11_delete_404.txt", format_response("DELETE /transactions/99999 — 404 Not Found", r))
    print(f"  PASS — 404 returned")


if __name__ == "__main__":
    tests = [
        test_get_all_valid,
        test_get_all_unauthorized,
        test_get_all_wrong_credentials,
        test_get_one_valid,
        test_get_one_not_found,
        test_post_valid,
        test_post_unauthorized,
        test_put_valid,
        test_put_not_found,
        test_delete_valid,
        test_delete_not_found,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR — {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Text results saved to screenshots/")
    print(f"{'=' * 50}")
