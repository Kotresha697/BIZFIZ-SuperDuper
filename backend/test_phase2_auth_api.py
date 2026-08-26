"""
Phase 2 automated tests: authentication & role separation.

These tests exercise the REAL backend logic without requiring a running
MongoDB, a live HTTP server, or the optional `httpx` test dependency:

  * The canonical auth endpoint functions in ``backend.main`` are called
    directly against an in-memory fake database.
  * The real ``backend.auth`` dependency guards (``get_client_user`` /
    ``get_admin_user`` / ``get_current_user``) are invoked exactly the way
    FastAPI invokes them, to prove the 401 / 403 role behaviour.
  * The live FastAPI route table is introspected to prove that each protected
    path actually has the correct guard attached (not just hidden nav).

Run it from the PROJECT ROOT:

    python -m pytest backend/test_phase2_auth_api.py -v
        (or)
    python backend/test_phase2_auth_api.py

Covers backend TEST 1-8 from the Phase 2 spec. Frontend TEST 9-12 are
manual/browser checks documented in the Phase 2 report.
"""
import os
import sys

# --- make the `backend` package importable no matter the working dir --------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# --- deterministic admin credentials for the seed (set BEFORE importing app) -
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "phase2-admin-pass")

# --- environment resilience: some sandboxes ship a broken pyOpenSSL, which
#     makes `import pymongo` crash. pymongo works fine on stdlib ssl, so if
#     OpenSSL is unhealthy we neutralise it. This is a no-op on healthy machines.
try:  # pragma: no cover - environment dependent
    import OpenSSL  # noqa: F401
except Exception:  # pragma: no cover
    sys.modules["OpenSSL"] = None

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from bson.objectid import ObjectId

import backend.main as m
from backend import auth


# ---------------------------------------------------------------------------
# Minimal in-memory MongoDB stand-in (only the operations main.py uses)
# ---------------------------------------------------------------------------
class _FakeResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _FakeUpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count
        self.modified_count = matched_count


class FakeCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(doc)
        return _FakeResult(doc["_id"])

    def _match(self, query):
        query = query or {}
        return [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]

    def find_one(self, query=None, projection=None):
        matches = self._match(query)
        return dict(matches[0]) if matches else None

    def find(self, query=None, projection=None):
        query = query or {}
        # Support the {"field": {"$in": [...]}} form used for batched lookups.
        def matches(d):
            for k, v in query.items():
                if isinstance(v, dict) and "$in" in v:
                    if d.get(k) not in v["$in"]:
                        return False
                elif d.get(k) != v:
                    return False
            return True
        return [dict(d) for d in self.docs if matches(d)]

    def _original(self, query):
        for d in self.docs:
            if all(d.get(k) == v for k, v in (query or {}).items()):
                return d
        return None

    def update_one(self, query, update):
        target = self._original(query)
        if target is not None:
            target.update(update.get("$set", {}))
        return _FakeUpdateResult(1 if target is not None else 0)

    def replace_one(self, query, doc, upsert=False):
        target = self._original(query)
        if target is not None:
            _id = target.get("_id")
            target.clear()
            target.update(doc)
            if _id is not None:
                target["_id"] = _id
            return _FakeUpdateResult(1)
        if upsert:
            self.insert_one(dict(doc))
        return _FakeUpdateResult(0)


class FakeDB:
    def __init__(self):
        self.cols = {}

    def __getitem__(self, name):
        return self.cols.setdefault(name, FakeCollection())


def _fresh_db():
    """Install a clean fake DB and (re)seed the admin account."""
    m.db = FakeDB()
    m._ensure_admin_seed()
    return m.db


def _creds(token):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _expect_http_error(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except HTTPException as e:
        return e.status_code
    raise AssertionError("Expected an HTTPException but none was raised")


# ---------------------------------------------------------------------------
# TEST 1 - Client register succeeds
# ---------------------------------------------------------------------------
def test_1_client_register_success():
    _fresh_db()
    res = m.client_register(m.ClientRegisterModel(
        name="Rajesh Kumar", email="Rajesh@Example.com", password="pw123456", mobileNumber="9876543210"
    ))
    assert "accessToken" in res and res["accessToken"]
    assert res["client"]["email"] == "rajesh@example.com"      # normalised
    assert "passwordHash" not in res["client"]                 # never exposed
    assert auth.decode_access_token(res["accessToken"])["role"] == "client"
    # duplicate email -> 400
    assert _expect_http_error(
        m.client_register,
        m.ClientRegisterModel(name="Dup", email="rajesh@example.com", password="x"),
    ) == 400


# ---------------------------------------------------------------------------
# TEST 2 - Client login returns a JWT carrying role=client
# ---------------------------------------------------------------------------
def test_2_client_login_role_client():
    _fresh_db()
    m.client_register(m.ClientRegisterModel(name="A", email="a@b.com", password="secret1"))
    res = m.client_login(m.ClientLoginModel(email="a@b.com", password="secret1"))
    payload = auth.decode_access_token(res["accessToken"])
    assert payload["role"] == "client"
    assert payload["sub"]
    # wrong password -> 401
    assert _expect_http_error(
        m.client_login, m.ClientLoginModel(email="a@b.com", password="WRONG")
    ) == 401


# ---------------------------------------------------------------------------
# TEST 3 - Client accesses /api/client/me successfully with a client token
# ---------------------------------------------------------------------------
def test_3_client_me_success():
    _fresh_db()
    reg = m.client_register(m.ClientRegisterModel(name="Meera", email="meera@x.com", password="pw12345"))
    token = reg["accessToken"]
    # the guard accepts a client token ...
    guarded = auth.get_client_user(_creds(token))
    assert guarded["role"] == "client"
    me = m.client_me(current_user=guarded)
    assert me["email"] == "meera@x.com"
    assert me["name"] == "Meera"


# ---------------------------------------------------------------------------
# TEST 4 - Client hitting an admin API -> 403
# ---------------------------------------------------------------------------
def test_4_client_on_admin_route_forbidden():
    _fresh_db()
    reg = m.client_register(m.ClientRegisterModel(name="C", email="c@x.com", password="pw12345"))
    client_token = reg["accessToken"]
    # get_admin_user is the exact guard on /api/admin/dashboard
    assert _expect_http_error(auth.get_admin_user, _creds(client_token)) == 403


# ---------------------------------------------------------------------------
# TEST 5 - Admin login returns a JWT carrying role=admin
# ---------------------------------------------------------------------------
def test_5_admin_login_role_admin():
    _fresh_db()
    res = m.admin_login(m.AdminLoginModel(
        username=os.environ["ADMIN_USERNAME"], password=os.environ["ADMIN_PASSWORD"]
    ))
    payload = auth.decode_access_token(res["accessToken"])
    assert payload["role"] == "admin"
    assert res["admin"]["username"] == os.environ["ADMIN_USERNAME"]
    # wrong password -> 401
    assert _expect_http_error(
        m.admin_login, m.AdminLoginModel(username="admin", password="nope")
    ) == 401


# ---------------------------------------------------------------------------
# TEST 6 - Admin accesses /api/admin/dashboard successfully
# ---------------------------------------------------------------------------
def test_6_admin_dashboard_success():
    _fresh_db()
    res = m.admin_login(m.AdminLoginModel(
        username=os.environ["ADMIN_USERNAME"], password=os.environ["ADMIN_PASSWORD"]
    ))
    admin_user = auth.get_admin_user(_creds(res["accessToken"]))   # guard passes
    dash = m.admin_dashboard(current_user=admin_user)
    assert dash["totalApplications"] == 0
    assert set(["totalApplications", "approvedCount", "rejectedCount", "reviewCount"]).issubset(dash.keys())


# ---------------------------------------------------------------------------
# TEST 7 - Admin accesses protected admin application APIs successfully
#          (also proves client-owned submission shows up for admin)
# ---------------------------------------------------------------------------
def test_7_admin_application_apis_success():
    _fresh_db()
    # a client submits an application (client-protected endpoint)
    reg = m.client_register(m.ClientRegisterModel(name="Owner", email="owner@x.com", password="pw12345"))
    client_user = auth.get_client_user(_creds(reg["accessToken"]))
    borrower = m.BorrowerModel(
        name="Owner", mobileNumber="9990001111", typeOfBusiness="fashion",
        businessAddress="1 MG Road", businessState="Karnataka", businessDistrict="Bangalore",
        businessPinCode="560001", amountApplied=200000, applicationStatus=0,
    )
    submitted = m.submit_borrower_application(borrower, current_user=client_user)
    assert submitted["userId"]

    # admin lists all applications
    admin_res = m.admin_login(m.AdminLoginModel(
        username=os.environ["ADMIN_USERNAME"], password=os.environ["ADMIN_PASSWORD"]))
    admin_user = auth.get_admin_user(_creds(admin_res["accessToken"]))
    apps = m.admin_applications(current_user=admin_user)
    assert any(a["userId"] == submitted["userId"] for a in apps)

    # admin analysis + update-status are admin-protected and functional
    analysis = m.admin_analysis(submitted["userId"], current_user=admin_user)
    assert analysis["userId"] == submitted["userId"]
    upd = m.admin_update_status(
        m.AdminUpdateStatusModel(userId=submitted["userId"], status="accept", approvedAmount=150000),
        current_user=admin_user,
    )
    assert "updated" in upd["msg"].lower()

    # the client sees only their OWN applications
    own = m.client_applications(current_user=client_user)
    assert len(own) == 1 and own[0]["userId"] == submitted["userId"]


# ---------------------------------------------------------------------------
# TEST 8 - No token / invalid token on a protected API -> 401
# ---------------------------------------------------------------------------
def test_8_missing_or_invalid_token_401():
    # missing credentials
    assert _expect_http_error(auth.get_current_user, None) == 401
    assert _expect_http_error(auth.get_client_user, None) == 401
    assert _expect_http_error(auth.get_admin_user, None) == 401
    # malformed / invalid token
    assert _expect_http_error(auth.get_current_user, _creds("not-a-real-token")) == 401


# ---------------------------------------------------------------------------
# WIRING - prove each protected path actually has the right guard attached
# ---------------------------------------------------------------------------
def _route_dependency_calls(route):
    calls = set()
    dependant = getattr(route, "dependant", None)
    if dependant is not None:
        for dep in dependant.dependencies:
            if getattr(dep, "call", None) is not None:
                calls.add(dep.call)
    return calls


def _find_route(path, method="GET"):
    for r in m.app.routes:
        if getattr(r, "path", None) == path and method in getattr(r, "methods", set()):
            return r
    raise AssertionError(f"Route {method} {path} not registered")


def test_wiring_client_routes_have_client_guard():
    for path, method in [("/api/client/me", "GET"),
                         ("/api/client/applications", "GET"),
                         ("/api/borrower/submit", "POST")]:
        calls = _route_dependency_calls(_find_route(path, method))
        assert auth.get_client_user in calls, f"{method} {path} missing client guard"


def test_wiring_admin_routes_have_admin_guard():
    for path, method in [("/api/admin/dashboard", "GET"),
                         ("/api/admin/applications", "GET"),
                         ("/api/admin/analysis/{userId}", "GET"),
                         ("/api/admin/update-status", "POST")]:
        calls = _route_dependency_calls(_find_route(path, method))
        assert auth.get_admin_user in calls, f"{method} {path} missing admin guard"


def test_wiring_public_auth_routes_are_open():
    for path, method in [("/api/auth/client/register", "POST"),
                         ("/api/auth/client/login", "POST"),
                         ("/api/auth/admin/login", "POST")]:
        calls = _route_dependency_calls(_find_route(path, method))
        assert auth.get_client_user not in calls and auth.get_admin_user not in calls


# ---------------------------------------------------------------------------
# Standalone runner (no pytest required)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
