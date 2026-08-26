"""
Phase 3 automated tests: end-to-end loan application flow (user <-> admin).

Exercises the REAL backend logic without a running MongoDB or HTTP server: the
canonical endpoint functions in ``backend.main`` are called directly against the
in-memory fake database from the Phase 2 suite, with the real auth guards.

Covers the exact flow from the Phase 3 spec:

    user submits 150000
        -> borrowers.amountApplied == 150000 (never a default)
        -> one analyses doc linked by analyses.userid
        -> admin list shows 150000
        -> admin approves 120000
        -> user sees Approved / requested 150000 / approved 120000

Plus Reject and Under Review, and the client-isolation rule.

Run it from the PROJECT ROOT:

    python backend/test_phase3_application_flow.py
        (or)
    python -m pytest backend/test_phase3_application_flow.py -v
"""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "phase3-admin-pass")

# Same environment-resilience shim as the Phase 2 suite (broken pyOpenSSL).
try:  # pragma: no cover - environment dependent
    import OpenSSL  # noqa: F401
except Exception:  # pragma: no cover
    sys.modules["OpenSSL"] = None

import backend.main as m
from backend import auth
from backend.test_phase2_auth_api import FakeDB, _creds, _expect_http_error
from bson.objectid import ObjectId


REQUESTED = 150000
APPROVED = 120000


def _register_client(email="merchant@example.com"):
    res = m.client_register(m.ClientRegisterModel(
        name="Rajesh Kumar", email=email, password="pw123456", mobileNumber="9876543210"
    ))
    return res["accessToken"]


def _admin_token():
    res = m.admin_login(m.AdminLoginModel(username="admin", password="phase3-admin-pass"))
    return res["accessToken"]


def _fresh():
    m.db = FakeDB()
    m._ensure_admin_seed()
    return m.db


def _application(amount=REQUESTED, **overrides):
    payload = dict(
        name="Rajesh Kumar",
        mobileNumber="9876543210",
        typeOfBusiness="fashion",
        businessName="Rajesh Fashion House",
        businessAddress="12 MG Road",
        businessState="Karnataka",
        businessDistrict="Bangalore Urban",
        businessPinCode="560001",
        amountApplied=amount,
        applicationStatus=0,
    )
    payload.update(overrides)
    return m.BorrowerModel(**payload)


def _submit(client_token, amount=REQUESTED, **overrides):
    user = auth.get_client_user(_creds(client_token))
    return m.submit_borrower_application(_application(amount, **overrides), current_user=user)


def _client_list(client_token):
    user = auth.get_client_user(_creds(client_token))
    return m.client_applications(current_user=user)


def _admin_list(admin_token):
    user = auth.get_admin_user(_creds(admin_token))
    return m.admin_applications(current_user=user)


def _admin_detail(admin_token, user_id):
    user = auth.get_admin_user(_creds(admin_token))
    return m.admin_analysis(user_id, current_user=user)


def _decide(admin_token, user_id, status, amount=0):
    user = auth.get_admin_user(_creds(admin_token))
    return m.admin_update_status(
        m.AdminUpdateStatusModel(userId=user_id, status=status, approvedAmount=amount),
        current_user=user,
    )


# ---------------------------------------------------------------------------
# 1 - The user's real amount is submitted and stored (never a default)
# ---------------------------------------------------------------------------
def test_1_real_amount_is_stored():
    _fresh()
    token = _register_client()
    submitted = _submit(token, 150000)
    stored = m.db["borrowers"].find_one({"_id": ObjectId(submitted["userId"])})

    assert stored["amountApplied"] == 150000, stored["amountApplied"]
    assert stored["amountApplied"] != 300000
    assert stored["applicationStatus"] == 0, "a new application must be Pending (0)"

    # Required canonical fields (Phase 3 section 2)
    for field in ("clientId", "name", "businessName", "businessSector", "businessState",
                  "businessDistrict", "businessPinCode", "amountApplied",
                  "applicationStatus", "createdAt"):
        assert stored.get(field) not in (None, ""), f"missing required field: {field}"

    # A different amount must flow through unchanged too.
    other = _submit(token, 250000)
    stored2 = m.db["borrowers"].find_one({"_id": ObjectId(other["userId"])})
    assert stored2["amountApplied"] == 250000

    # The form sends businessSector explicitly; it must be stored as sent.
    explicit = _submit(token, 175000, typeOfBusiness="hospitality", businessSector="hospitality")
    stored3 = m.db["borrowers"].find_one({"_id": ObjectId(explicit["userId"])})
    assert stored3["businessSector"] == "hospitality"
    assert stored3["amountApplied"] == 175000


# ---------------------------------------------------------------------------
# 2 - Exactly ONE analysis is stored, linked by analyses.userid
# ---------------------------------------------------------------------------
def test_2_one_analysis_linked_to_borrower():
    _fresh()
    token = _register_client()
    submitted = _submit(token, REQUESTED)
    user_id = submitted["userId"]

    linked = m.db["analyses"].find({"userid": user_id})
    assert len(linked) == 1, f"expected exactly 1 analysis, got {len(linked)}"

    analysis = linked[0]
    assert analysis["userid"] == user_id
    assert isinstance(analysis["bizfizScore"], (int, float))
    assert analysis["riskCategory"] in ("Low", "Moderate", "High")
    # Scoring must receive the REAL requested amount, not a fallback.
    assert analysis["requestedAmount"] == REQUESTED, analysis["requestedAmount"]

    # Re-scoring the same application replaces, never duplicates.
    oid = ObjectId(user_id)
    m._run_and_store_analysis(oid, m.db["borrowers"].find_one({"_id": oid}))
    assert len(m.db["analyses"].find({"userid": user_id})) == 1


# ---------------------------------------------------------------------------
# 3 - The user sees only their own applications, with real values
# ---------------------------------------------------------------------------
def test_3_client_sees_own_applications_with_real_values():
    _fresh()
    token_a = _register_client("a@example.com")
    token_b = _register_client("b@example.com")
    submitted = _submit(token_a, REQUESTED)
    _submit(token_b, 999000)

    mine = _client_list(token_a)
    assert len(mine) == 1, "client must see only their own applications"
    row = mine[0]
    assert row["userId"] == submitted["userId"]
    assert row["amountApplied"] == REQUESTED
    assert row["businessName"] == "Rajesh Fashion House"
    assert row["businessSector"] == "fashion"
    assert isinstance(row["bizfizScore"], (int, float)), "score must reach the dashboard"
    assert row["riskCategory"] in ("Low", "Moderate", "High")
    assert row["applicationStatus"] == 0

    other = _client_list(token_b)
    assert len(other) == 1 and other[0]["amountApplied"] == 999000


# ---------------------------------------------------------------------------
# 4 - Admin list shows the submitted application with the real amount
# ---------------------------------------------------------------------------
def test_4_admin_sees_real_requested_amount():
    _fresh()
    token = _register_client()
    submitted = _submit(token, REQUESTED)

    rows = _admin_list(_admin_token())
    assert len(rows) == 1
    row = rows[0]
    assert row["userId"] == submitted["userId"], "admin must link by the real MongoDB id"
    assert row["amountApplied"] == REQUESTED, row["amountApplied"]
    assert row["applicationDate"] is not None, "request list renders applicationDate"


# ---------------------------------------------------------------------------
# 5 - Admin detail shows real values, no fake fallback data
# ---------------------------------------------------------------------------
def test_5_admin_detail_shows_real_values():
    _fresh()
    token = _register_client()
    submitted = _submit(token, REQUESTED)
    detail = _admin_detail(_admin_token(), submitted["userId"])

    assert detail["userId"] == submitted["userId"]
    assert detail["requestedAmount"] == REQUESTED
    assert isinstance(detail["bizfizScore"], (int, float))
    assert detail["riskCategory"] in ("Low", "Moderate", "High")
    assert detail["recommendation"]
    assert detail["statusLabel"] == "Pending"
    assert detail.get("analysisPending") is None, "stub flag must be gone"

    info = detail["userFormSubmittedInfo"]
    assert info["Name"] == "Rajesh Kumar"
    assert info["Business"] == "Rajesh Fashion House"
    assert info["Requested Amount"] == "₹150,000", info["Requested Amount"]
    assert info["Status"] == "Pending"
    # Values the application genuinely does not carry must read N/A, not a figure.
    assert info["Loan Purpose"] == "N/A"
    assert info["Tenure"] == "N/A"
    assert info["Monthly Revenue"] == "N/A"

    # The existing detail component renders these keys.
    assert len(detail["indicators"]) == 5, "existing indicator panel needs 5 ratings"
    assert detail["scoreScale"] == 100
    assert len(detail["transactionalAnalysis"]) == 5

    # Unknown id -> 404 rather than invented data
    assert _expect_http_error(_admin_detail, _admin_token(), "64b7f9a2c8e4d51234567890") == 404


# ---------------------------------------------------------------------------
# 6 - THE FULL SPEC FLOW: approve 120000 and the user sees it
# ---------------------------------------------------------------------------
def test_6_full_flow_approve():
    _fresh()
    token = _register_client()
    admin = _admin_token()
    submitted = _submit(token, REQUESTED)
    user_id = submitted["userId"]

    # admin sees the real requested amount
    assert _admin_list(admin)[0]["amountApplied"] == REQUESTED

    # admin approves a different amount
    res = _decide(admin, user_id, "approve", APPROVED)
    assert res["applicationStatus"] == 1
    assert res["amountApproved"] == APPROVED
    assert res["statusLabel"] == "Approved"

    # MongoDB is the single source of truth
    stored = m.db["borrowers"].find_one({"_id": ObjectId(user_id)})
    assert stored["applicationStatus"] == 1
    assert stored["amountApproved"] == APPROVED, "canonical field must be written"
    assert stored["amountApplied"] == REQUESTED, "requested amount must be untouched"

    # the user now sees Approved + both amounts
    row = _client_list(token)[0]
    assert row["applicationStatus"] == 1
    assert row["amountApplied"] == REQUESTED
    assert row["amountApproved"] == APPROVED

    # and so does the admin detail panel
    detail = _admin_detail(admin, user_id)
    assert detail["amountApproved"] == APPROVED
    assert detail["userFormSubmittedInfo"]["Approved Amount"] == "₹120,000"
    assert detail["userFormSubmittedInfo"]["Status"] == "Approved"


# ---------------------------------------------------------------------------
# 7 - Reject and Under Review
# ---------------------------------------------------------------------------
def test_7_reject_and_under_review():
    _fresh()
    token = _register_client()
    admin = _admin_token()

    rejected_id = _submit(token, REQUESTED)["userId"]
    res = _decide(admin, rejected_id, "reject", 0)
    assert res["applicationStatus"] == 3 and res["statusLabel"] == "Rejected"

    review_id = _submit(token, REQUESTED)["userId"]
    res = _decide(admin, review_id, "review", 0)
    assert res["applicationStatus"] == 2 and res["statusLabel"] == "Under Review"

    by_id = {r["userId"]: r for r in _client_list(token)}
    assert by_id[rejected_id]["applicationStatus"] == 3
    assert by_id[review_id]["applicationStatus"] == 2

    # A rejection must never carry an approved amount, even if one is sent.
    other_id = _submit(token, REQUESTED)["userId"]
    _decide(admin, other_id, "reject", 90000)
    stored = m.db["borrowers"].find_one({"_id": ObjectId(other_id)})
    assert stored["amountApproved"] == 0

    # Unknown status is refused rather than silently defaulted.
    assert _expect_http_error(_decide, admin, review_id, "maybe", 0) == 400
    # Unknown application -> 404
    assert _expect_http_error(_decide, admin, "64b7f9a2c8e4d51234567890", "approve", 1) == 404


# ---------------------------------------------------------------------------
# 8 - Legacy records still read correctly (back-compat, no data rewrite)
# ---------------------------------------------------------------------------
def test_8_legacy_approvedAmount_still_read():
    _fresh()
    token = _register_client()
    user_id = _submit(token, REQUESTED)["userId"]
    # Simulate a record written by the legacy /updateuser endpoint: it set
    # `approvedAmount` and never wrote the canonical `amountApproved`.
    stored = m.db["borrowers"]._original({"_id": ObjectId(user_id)})
    stored.pop("amountApproved", None)
    stored["applicationStatus"] = 1
    stored["approvedAmount"] = 99000

    row = _client_list(token)[0]
    assert row["amountApproved"] == 99000, "legacy approvedAmount must still surface"


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
