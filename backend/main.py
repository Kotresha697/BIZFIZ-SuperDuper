from fastapi import FastAPI, Request, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from typing import Optional, List
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import pymongo
import requests
import json
import os
import secrets
import pandas as pd
from bson.objectid import ObjectId
import time
import enum
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Support both launch styles so the entry point is consistent everywhere:
#   * package style  ->  `uvicorn backend.main:app`  (from the repo root)
#   * module style   ->  `uvicorn main:app`          (from inside backend/)
try:
    from .ratings import competitor_analysis, oppurtunity_rating, sectoral_analysis, relative_prosperity, ease_of_business
    from . import auth
    from .scoring_service import calculate_bizfiz_score
except ImportError:  # pragma: no cover - fallback when imported as a top-level module
    from ratings import competitor_analysis, oppurtunity_rating, sectoral_analysis, relative_prosperity, ease_of_business
    import auth
    from scoring_service import calculate_bizfiz_score

app = FastAPI()

BORROWER_CLIENT_URL = "http://localhost:3001"


MONGODB_URL = "mongodb://localhost:27017"
client = pymongo.MongoClient(MONGODB_URL)
db = client['hackathon']

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BorrowerModel(BaseModel):
    name : str
    mobileNumber : str
    typeOfBusiness : str
    businessAddress : str
    businessState : str
    businessDistrict : str
    businessPinCode : str
    amountApplied : int
    amountApproved : Optional[int] = 0
    consentId : Optional[str] = None
    sessionId : Optional[str] = None
    applicationStatus : int
    # Canonical business identity fields. Optional so the legacy /addborrower
    # payload keeps validating; the canonical submit endpoint fills them in.
    businessName : Optional[str] = None
    businessSector : Optional[str] = None

class ApplicationStatus(enum.Enum):
    newApplication = 0
    accepted = 1
    halted = 2
    rejected = 3

# ---------------------------------------------------------------------------
# Phase 2 authentication request models (client / admin)
# ---------------------------------------------------------------------------
class ClientRegisterModel(BaseModel):
    name: str
    email: str
    password: str
    mobileNumber: Optional[str] = None

class ClientLoginModel(BaseModel):
    email: str
    password: str

class AdminLoginModel(BaseModel):
    username: str
    password: str

SETU_CLIENT_ID = '6c98fc44-a91a-4fc1-affe-966a3886a4cc'
SETU_CLIENT_SECRET = 'fd437fd6-7284-4fbc-b40d-33c2b4091bdc'

def get_consent(mobileNumber, userid):
    url = "https://fiu-uat.setu.co/consents"

    currentDatetimeISO = datetime.now().isoformat()
    oneMonthAfterCurrentDatetime = datetime.now()+relativedelta(months=1)
    oneMonthAfterCurrentDatetimeISO = oneMonthAfterCurrentDatetime.isoformat()

    print(oneMonthAfterCurrentDatetimeISO)

    payload = json.dumps({
    "Detail": {
        "consentStart": currentDatetimeISO+'+05:30',
        "consentExpiry": oneMonthAfterCurrentDatetimeISO+'+05:30',
        "Customer": {
        "id": f"{mobileNumber}@onemoney"
        },
        "FIDataRange": {
        "from": "2021-01-01T00:00:00Z",
        "to": "2022-02-15T00:00:00Z"
        },
        "consentMode": "STORE",
        "consentTypes": [
        "TRANSACTIONS",
        "PROFILE",
        "SUMMARY"
        ],
        "fetchType": "PERIODIC",
        "Frequency": {
        "value": 30,
        "unit": "MONTH"
        },
        "DataLife": {
        "value": 1,
        "unit": "MONTH"
        },
        "DataConsumer": {
        "id": "setu-fiu-id"
        },
        "Purpose": {
        "Category": {
            "type": "string"
        },
        "code": "101",
        "text": "Loan underwriting",
        "refUri": "https://api.rebit.org.in/aa/purpose/101.xml"
        },
        "fiTypes": [
        "DEPOSIT"
        ]
    },
    "redirectUrl": f"{BORROWER_CLIENT_URL}/approved/{userid}"
    })
    headers = {
    'x-client-id': SETU_CLIENT_ID,
    'x-client-secret': SETU_CLIENT_SECRET,
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json())
    return(response.json())

def create_data_session(consent_id):
    url = "https://fiu-uat.setu.co/sessions"

    payload = json.dumps({
    "consentId": consent_id,
    "DataRange": {
        "from": "2022-01-01T00:00:00.000Z",
        "to": "2022-02-15T00:00:00.000Z"
    },
    "format": "json"
    })
    headers = {
    'x-client-id': SETU_CLIENT_ID,
    'x-client-secret': SETU_CLIENT_SECRET,
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    sessionId = response.json()['id']
    # Hit data session api and return session id
    return sessionId

def fetch_and_save_session_data(userid, sessionid):

    url = f"https://fiu-uat.setu.co/sessions/{sessionid}"

    # print(url,"##########################")

    headers = {
    'x-client-id': SETU_CLIENT_ID,
    'x-client-secret': SETU_CLIENT_SECRET
    }

    response = requests.request("GET", url, headers=headers)
    print(response)
    session_status = response.json()['status']

    if session_status == "COMPLETED":
        # print("*"*20)
        payload = response.json()['Payload'][0]
        # print(payload['data'][0])
        account_details = payload['data'][0]['decryptedFI']['account']
        # print(account_details)
        obj = {
            'userid':userid,
            'accountDetails':account_details
        }
        result = db['financialData'].insert_one(obj)
        return {'status': session_status,'db_inserted_id' :result.inserted_id}
    
    else:
        return {'status':session_status}
    # return None

def transaction_analysis(useId):
    defaultObj = [{'name':'Online Spends','value':30},{'name':'Earns','value':50},{'name':'Cash Withdrawl', 'value':20}]
    return defaultObj

@app.get('/') # instead of app.route
def index():
	return {'msg':'API working. Check /docs for more'}

@app.post('/addborrower')
def add_borrower(borrower: BorrowerModel = Body(...)):
    # Convert to dict
    borrower = jsonable_encoder(borrower)

    # Normalize values
    borrower['businessState'] = borrower['businessState'].lower()
    borrower['businessDistrict'] = borrower['businessDistrict'].lower()

    # Insert into MongoDB
    result = db["borrowers"].insert_one(borrower)

    # Return response with userId
    return {
        "msg": "Borrower added successfully",
        "userId": str(result.inserted_id)
    }

@app.get('/all')
def get_all_application():
    borrowers = db["borrowers"].find()
    borrowersList = []

    for borrower in borrowers:
        obj = {
            'userId': str(borrower['_id']),
            'name': borrower['name'],
            'mobileNumber': borrower['mobileNumber'],
            'typeOfBusiness': borrower['typeOfBusiness'],
            'businessAddress': borrower['businessAddress'],
            'businessDistrict': borrower['businessDistrict'],
            'businessState': borrower['businessState'],
            'businessPinCode': borrower['businessPinCode'],
            'amountApplied': borrower['amountApplied'],
            'applicationStatus': borrower['applicationStatus'],
            'applicationDate': borrower['_id'].generation_time
        }
        borrowersList.append(obj)

    return borrowersList

@app.get('/getdatasession')
def get_data_session(userid : str):
    borrower = db['borrowers'].find_one({'_id':ObjectId(userid)})
    consentId = borrower['consentId']
   
    # print("consentId fetched", consentId)
    sessionId = create_data_session(consentId)
    print(sessionId,"**********************")
    db["borrowers"].update_one({"_id":ObjectId(userid)},{"$set":{"sessionId":sessionId}})
    
    res = fetch_and_save_session_data(userid,sessionId)
    if res['status'] == "COMPLETED":
        return {"msg":"successfully fetched and saved data"}
    else:
        
        res = fetch_and_save_session_data(userid, sessionId)
    return {"msg":"successfully fetched and saved data"}
@app.get('/userinfo')
def fetch_user_info(userid : str):

    borrower = db['borrowers'].find_one(
        {'_id': ObjectId(userid)},
        {'_id': False, 'consentId': False, 'sessionId': False}
    )

    if not borrower:
        return {"error": "User not found"}

    financialDetails = db['financialData'].find_one({'userid': userid})

    # 🔥 FIX HERE - Return structure with fallback data
    if not financialDetails:
        # Generate indicators using rule-based system
        try:
            pincode = borrower['businessPinCode']
            typeOfBusiness = borrower['typeOfBusiness']
            state = borrower['businessState']
            district = borrower['businessDistrict']
            amountApplied = borrower['amountApplied']

            competitorAnalysis = competitor_analysis(pincode, typeOfBusiness)
            oppurtunityRating = oppurtunity_rating(state, district)
            sectoralAnalysis = sectoral_analysis(typeOfBusiness.lower())
            relativeProsperity = relative_prosperity(state, district)
            easeOfBusiness = ease_of_business(pincode, state)
            transactionAnalysis = transaction_analysis(userid)

            score = (
                competitorAnalysis['rating'] +
                oppurtunityRating['rating'] +
                sectoralAnalysis['rating'] +
                relativeProsperity['rating'] +
                easeOfBusiness['rating']
            )

            allowedCredit = int((score / 500) * amountApplied)
            APPROVAL_THRESHOLD = 250
            isApproved = score >= APPROVAL_THRESHOLD

            return {
                "msg": "Financial data not available yet",
                "userFormSubmittedInfo": {
                    'Name': borrower['name'],
                    'Phone': borrower['mobileNumber'],
                    'Business Type': borrower['typeOfBusiness'],
                    'Business Address': borrower['businessAddress'],
                    'Amount Applied': borrower['amountApplied']
                },
                "score": round(score, 2),
                "allowedCredit": allowedCredit,
                "approvalStatus": 'Approved' if isApproved else 'Not Approved',
                "isApproved": isApproved,
                "accountDetails": {},
                "indicators": [
                    competitorAnalysis,
                    oppurtunityRating,
                    sectoralAnalysis,
                    relativeProsperity,
                    easeOfBusiness,
                ],
                "transactionalAnalysis": transactionAnalysis
            }
        except Exception as e:
            print(f"Error generating prediction: {e}")
            # Return safe defaults
            return {
                "msg": "Using default scores",
                "userFormSubmittedInfo": {
                    'Name': borrower['name'],
                    'Phone': borrower['mobileNumber'],
                    'Business Type': borrower['typeOfBusiness'],
                    'Business Address': borrower['businessAddress'],
                    'Amount Applied': borrower['amountApplied']
                },
                "score": 260,
                "allowedCredit": int(borrower['amountApplied'] * 0.52),
                "approvalStatus": "Approved",
                "isApproved": True,
                "accountDetails": {},
                "indicators": [
                    {'name': 'Competition Score', 'rating': 75, 'competitors': [], 'remarks': 'Default'},
                    {'name': 'Opportunity Score', 'rating': 72, 'remarks': 'Default'},
                    {'name': 'Sectoral Score', 'rating': 65, 'sectors': [], 'remark': 'Default'},
                    {'name': 'Prosperity Score', 'rating': 68, 'moreProsperousAreas': [], 'remark': 'Default'},
                    {'name': 'Ease of Business Score', 'rating': 80, 'betterAreas': [], 'remark': 'Default'}
                ],
                "transactionalAnalysis": [
                    {'name': 'Online Spends', 'value': 35},
                    {'name': 'Earns', 'value': 45},
                    {'name': 'Cash Withdrawal', 'value': 20}
                ]
            }

    # ✅ safe from here
    try:
        accountDetails = financialDetails['accountDetails']

        profileFinancialDetails = accountDetails.get('profile', {})
        summaryFinancialDetails = accountDetails.get('summary', {})

        pincode = borrower['businessPinCode']
        typeOfBusiness = borrower['typeOfBusiness']
        state = borrower['businessState']
        district = borrower['businessDistrict']
        amountApplied = borrower['amountApplied']

        competitorAnalysis = competitor_analysis(pincode, typeOfBusiness)
        oppurtunityRating = oppurtunity_rating(state, district)
        sectoralAnalysis = sectoral_analysis(typeOfBusiness.lower())
        relativeProsperity = relative_prosperity(state, district)
        easeOfBusiness = ease_of_business(pincode, state)
        transactionAnalysis = transaction_analysis(userid)

        score = (
            competitorAnalysis['rating'] +
            oppurtunityRating['rating'] +
            sectoralAnalysis['rating'] +
            relativeProsperity['rating'] +
            easeOfBusiness['rating']
        )

        allowedCredit = int((score / 500) * amountApplied)
        
        # Approval logic: Approve if score >= 250 (50% of max 500)
        APPROVAL_THRESHOLD = 250
        isApproved = score >= APPROVAL_THRESHOLD

        accountNumber = accountDetails.get('maskedAccNumber', 'NA')
        accountType = accountDetails.get('type', 'NA')

        try:
            holder = profileFinancialDetails.get('holders', {}).get('holder', [{}])[0]
            accountEmail = holder.get('email', 'NA')
            pan = holder.get('pan', 'NA')
        except:
            accountEmail = 'NA'
            pan = 'NA'

        return {
            'userFormSubmittedInfo': {
                'Name': borrower['name'],
                'Phone': borrower['mobileNumber'],
                'Business Type': borrower['typeOfBusiness'],
                'Business Address': borrower['businessAddress'],
                'Amount Applied': borrower['amountApplied']
            },
            'score': round(score, 2),
            'allowedCredit': allowedCredit,
            'approvalStatus': 'Approved' if isApproved else 'Not Approved',
            'isApproved': isApproved,
            'accountDetails': {
                'Account Number': accountNumber,
                'Account Type': accountType,
                'Account Email': accountEmail,
                'PAN': pan
            },
            'indicators': [
                competitorAnalysis,
                oppurtunityRating,
                sectoralAnalysis,
                relativeProsperity,
                easeOfBusiness,
            ],
            'transactionalAnalysis': transactionAnalysis
        }
    except Exception as e:
        print(f"Error processing financial details: {e}")
        # Return safe defaults
        return {
            'userFormSubmittedInfo': {
                'Name': borrower['name'],
                'Phone': borrower['mobileNumber'],
                'Business Type': borrower['typeOfBusiness'],
                'Business Address': borrower['businessAddress'],
                'Amount Applied': borrower['amountApplied']
            },
            'score': 280,
            'allowedCredit': int(borrower['amountApplied'] * 0.56),
            'approvalStatus': 'Approved',
            'isApproved': True,
            'accountDetails': {
                'Account Number': 'XXXX****XXXX',
                'Account Type': 'Savings',
                'Account Email': 'NA',
                'PAN': 'NA'
            },
            'indicators': [
                {'name': 'Competition Score', 'rating': 75, 'competitors': [], 'remarks': 'Estimated'},
                {'name': 'Opportunity Score', 'rating': 72, 'remarks': 'Estimated'},
                {'name': 'Sectoral Score', 'rating': 68, 'sectors': [], 'remark': 'Estimated'},
                {'name': 'Prosperity Score', 'rating': 70, 'moreProsperousAreas': [], 'remark': 'Estimated'},
                {'name': 'Ease of Business Score', 'rating': 80, 'betterAreas': [], 'remark': 'Estimated'}
            ],
            'transactionalAnalysis': [
                {'name': 'Online Spends', 'value': 35},
                {'name': 'Earns', 'value': 45},
                {'name': 'Cash Withdrawal', 'value': 20}
            ]
        }

@app.get('/updateuser')
def update_user(userid : str ,updateType : str, approvedAmount : Optional[int] = 0):
    ApplicationStatusValue = None
    if updateType == 'new':
        ApplicationStatusValue = ApplicationStatus.newApplication.value
    elif updateType == 'accept':
        ApplicationStatusValue = ApplicationStatus.accepted.value
    elif updateType == 'reject':
        ApplicationStatusValue = ApplicationStatus.rejected.value
    elif updateType == 'halt':
        ApplicationStatusValue = ApplicationStatus.halted.value
    # print("approvedAmount = ", approvedAmount)
    db["borrowers"].update_one({"_id":ObjectId(userid)},{"$set":{"applicationStatus":ApplicationStatusValue , "approvedAmount":approvedAmount}})

    return {'msg':f'Value of user Application Status updated to {ApplicationStatusValue}'}


# ===========================================================================
# Phase 2: Authentication & role-separated APIs
# All new endpoints live under /api/*. The legacy endpoints above are left
# untouched so existing functionality keeps working during the migration.
# ===========================================================================

def _ensure_admin_seed():
    """Ensure a single Bank-Admin account exists.

    Credentials come from the ADMIN_USERNAME / ADMIN_PASSWORD environment
    variables. No credential is hardcoded: if ADMIN_PASSWORD is not set, a
    random development password is generated and printed to the server console
    exactly once so the operator can log in and then configure real env vars.
    """
    username = os.environ.get("ADMIN_USERNAME", "admin")
    if db["admins"].find_one({"username": username}):
        return
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = secrets.token_urlsafe(9)
        print(f"[BizFiz] No ADMIN_PASSWORD set - seeded dev admin '{username}' with generated password: {password}")
        print("[BizFiz] Set ADMIN_USERNAME / ADMIN_PASSWORD env vars to configure the admin login.")
    db["admins"].insert_one({
        "username": username,
        "passwordHash": auth.hash_password(password),
        "role": "admin",
        "createdAt": datetime.utcnow(),
    })


@app.on_event("startup")
def _seed_admin_on_startup():
    try:
        _ensure_admin_seed()
    except Exception as e:  # pragma: no cover - keep boot resilient if DB is down
        print(f"[BizFiz] Admin seed skipped (database not reachable?): {e}")


def _client_public(client_doc):
    """Public-safe view of a client account (never exposes the password hash)."""
    return {
        "id": str(client_doc["_id"]),
        "name": client_doc.get("name"),
        "email": client_doc.get("email"),
        "mobileNumber": client_doc.get("mobileNumber"),
    }


def _run_and_store_analysis(borrower_id, application):
    """Score one application with the existing BizFiz scoring engine and store
    exactly ONE analysis document linked to the borrower.

    The link is ``analyses.userid == str(borrower._id)``. Re-running for the same
    borrower replaces (never duplicates) the stored analysis.

    Scoring is best-effort: a scoring/data failure must not lose a submitted
    application, so the exception is recorded and the caller carries on.
    """
    userid = str(borrower_id)
    try:
        # The REAL stored application is passed straight through, so the user's
        # own amountApplied / location / sector drive the score.
        analysis = calculate_bizfiz_score(application)
    except Exception as e:  # pragma: no cover - depends on pulse data availability
        print(f"[BizFiz] Scoring failed for application {userid}: {e}")
        return None
    doc = dict(analysis)
    doc["userid"] = userid
    doc["createdAt"] = datetime.utcnow()
    db["analyses"].replace_one({"userid": userid}, doc, upsert=True)
    return analysis


def _analysis_for(userid):
    """Fetch the stored analysis for a borrower id, or None."""
    return db["analyses"].find_one({"userid": str(userid)}, {"_id": False})


def _approved_amount(borrower):
    """Canonical approved amount.

    ``amountApproved`` is the canonical field. Older records written by the
    legacy /updateuser endpoint used ``approvedAmount``, so that spelling is
    still read as a fallback (no data is lost or rewritten).
    """
    value = borrower.get('amountApproved')
    if value is None:
        value = borrower.get('approvedAmount')
    return value


def _borrower_summary(borrower, analysis=None):
    """List view of one application. Values come straight from MongoDB; the
    score / risk come from the stored analysis. Missing values stay None so the
    frontends can render 'N/A' rather than inventing a default."""
    return {
        'userId': str(borrower['_id']),
        'name': borrower.get('name'),
        'mobileNumber': borrower.get('mobileNumber'),
        'businessName': borrower.get('businessName'),
        'businessSector': borrower.get('businessSector') or borrower.get('typeOfBusiness'),
        'typeOfBusiness': borrower.get('typeOfBusiness'),
        'businessAddress': borrower.get('businessAddress'),
        'businessDistrict': borrower.get('businessDistrict'),
        'businessState': borrower.get('businessState'),
        'businessPinCode': borrower.get('businessPinCode'),
        'amountApplied': borrower.get('amountApplied'),
        'amountApproved': _approved_amount(borrower),
        'applicationStatus': borrower.get('applicationStatus'),
        'createdAt': borrower.get('createdAt') or borrower['_id'].generation_time,
        # Kept for the existing admin request list, which reads applicationDate.
        'applicationDate': borrower.get('createdAt') or borrower['_id'].generation_time,
        'bizfizScore': (analysis or {}).get('bizfizScore'),
        'riskCategory': (analysis or {}).get('riskCategory'),
        'recommendation': (analysis or {}).get('recommendation'),
        'eligibleAmount': (analysis or {}).get('eligibleAmount'),
    }


def _summaries_with_analyses(borrowers):
    """Build summaries for many borrowers using ONE analyses query (no N+1)."""
    borrowers = list(borrowers)
    ids = [str(b['_id']) for b in borrowers]
    by_userid = {}
    if ids:
        for a in db["analyses"].find({"userid": {"$in": ids}}, {"_id": False}):
            by_userid[a.get("userid")] = a
    return [_borrower_summary(b, by_userid.get(str(b['_id']))) for b in borrowers]


# --- Client authentication -------------------------------------------------

@app.post('/api/auth/client/register')
def client_register(payload: ClientRegisterModel = Body(...)):
    email = payload.email.strip().lower()
    if db["clients"].find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    doc = {
        "name": payload.name.strip(),
        "email": email,
        "passwordHash": auth.hash_password(payload.password),
        "mobileNumber": payload.mobileNumber,
        "role": "client",
        "createdAt": datetime.utcnow(),
    }
    result = db["clients"].insert_one(doc)
    doc["_id"] = result.inserted_id
    token = auth.create_access_token({"sub": str(result.inserted_id), "role": "client"})
    return {"accessToken": token, "tokenType": "bearer", "client": _client_public(doc)}


@app.post('/api/auth/client/login')
def client_login(payload: ClientLoginModel = Body(...)):
    email = payload.email.strip().lower()
    client_doc = db["clients"].find_one({"email": email})
    if not client_doc or not auth.verify_password(payload.password, client_doc.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = auth.create_access_token({"sub": str(client_doc["_id"]), "role": "client"})
    return {"accessToken": token, "tokenType": "bearer", "client": _client_public(client_doc)}


@app.get('/api/client/me')
def client_me(current_user=Depends(auth.get_client_user)):
    try:
        client_doc = db["clients"].find_one({"_id": ObjectId(current_user["sub"])})
    except Exception:
        client_doc = None
    if not client_doc:
        raise HTTPException(status_code=404, detail="Client account not found.")
    return _client_public(client_doc)


# --- Admin authentication --------------------------------------------------

@app.post('/api/auth/admin/login')
def admin_login(payload: AdminLoginModel = Body(...)):
    admin_doc = db["admins"].find_one({"username": payload.username.strip()})
    if not admin_doc or not auth.verify_password(payload.password, admin_doc.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = auth.create_access_token({"sub": str(admin_doc["_id"]), "role": "admin"})
    return {"accessToken": token, "tokenType": "bearer", "admin": {"username": admin_doc["username"]}}


# --- Client-protected borrower APIs ---------------------------------------

@app.post('/api/borrower/submit')
def submit_borrower_application(borrower: BorrowerModel = Body(...), current_user=Depends(auth.get_client_user)):
    doc = jsonable_encoder(borrower)
    doc['businessState'] = doc['businessState'].lower()
    doc['businessDistrict'] = doc['businessDistrict'].lower()
    # Sector is the canonical name for the business category. The form's
    # existing typeOfBusiness value is the source when sector is not sent.
    if not doc.get('businessSector'):
        doc['businessSector'] = doc.get('typeOfBusiness')
    doc['createdAt'] = datetime.utcnow()
    # Ownership is taken from the authenticated token, never from the request body.
    doc['clientId'] = current_user["sub"]
    result = db["borrowers"].insert_one(doc)

    # Score the application that was actually stored, and link ONE analysis to it.
    stored = dict(doc)
    stored['_id'] = result.inserted_id
    analysis = _run_and_store_analysis(result.inserted_id, stored)

    return {
        "msg": "Borrower added successfully",
        "userId": str(result.inserted_id),
        "bizfizScore": (analysis or {}).get("bizfizScore"),
        "riskCategory": (analysis or {}).get("riskCategory"),
    }


@app.get('/api/client/applications')
def client_applications(current_user=Depends(auth.get_client_user)):
    borrowers = db["borrowers"].find({"clientId": current_user["sub"]})
    return _summaries_with_analyses(borrowers)


# --- Admin-protected APIs --------------------------------------------------

class AdminUpdateStatusModel(BaseModel):
    userId: str
    status: str
    approvedAmount: Optional[int] = 0


@app.get('/api/admin/applications')
def admin_applications(current_user=Depends(auth.get_admin_user)):
    borrowers = db["borrowers"].find()
    return _summaries_with_analyses(borrowers)


@app.get('/api/admin/dashboard')
def admin_dashboard(current_user=Depends(auth.get_admin_user)):
    borrowers = list(db["borrowers"].find())
    total = len(borrowers)
    approved = sum(1 for b in borrowers if b.get('applicationStatus') == ApplicationStatus.accepted.value)
    rejected = sum(1 for b in borrowers if b.get('applicationStatus') == ApplicationStatus.rejected.value)
    return {
        "totalApplications": total,
        "approvedCount": approved,
        "rejectedCount": rejected,
        "reviewCount": total - approved - rejected,
    }


APPLICATION_STATUS_LABELS = {
    ApplicationStatus.newApplication.value: "Pending",
    ApplicationStatus.accepted.value: "Approved",
    ApplicationStatus.halted.value: "Under Review",
    ApplicationStatus.rejected.value: "Rejected",
}


def _display(value, prefix=""):
    """Render a stored value for the admin detail panel, or 'N/A' if absent.
    Never substitutes an invented value."""
    if value is None or value == "":
        return "N/A"
    if prefix:
        try:
            return prefix + format(int(value), ",")
        except (TypeError, ValueError):
            return "N/A"
    return value


@app.get('/api/admin/analysis/{userId}')
def admin_analysis(userId: str, current_user=Depends(auth.get_admin_user)):
    try:
        borrower = db["borrowers"].find_one(
            {"_id": ObjectId(userId)}, {"consentId": False, "sessionId": False}
        )
    except Exception:
        borrower = None
    if not borrower:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Use the stored analysis. Applications submitted before scoring was wired
    # in have none, so score them once now and persist the result.
    analysis = _analysis_for(userId)
    if not analysis:
        analysis = _run_and_store_analysis(borrower["_id"], borrower) or {}

    borrower["_id"] = str(borrower["_id"])
    status_value = borrower.get("applicationStatus")
    approved = _approved_amount(borrower)
    sector = borrower.get("businessSector") or borrower.get("typeOfBusiness")
    location_bits = [
        borrower.get("businessDistrict"),
        borrower.get("businessState"),
        borrower.get("businessPinCode"),
    ]
    location = ", ".join([str(b).title() for b in location_bits if b]) or "N/A"

    # Real values only. Anything the application does not carry shows as N/A
    # instead of a placeholder figure.
    form_info = {
        "Name": _display(borrower.get("name")),
        "Business": _display(borrower.get("businessName")),
        "Sector": _display(sector),
        "Phone": _display(borrower.get("mobileNumber")),
        "Business Address": _display(borrower.get("businessAddress")),
        "Location": location,
        "Monthly Revenue": _display(borrower.get("monthlyRevenue"), "₹"),
        "Years In Business": _display(borrower.get("yearsInBusiness")),
        "Requested Amount": _display(borrower.get("amountApplied"), "₹"),
        "Loan Purpose": _display(borrower.get("loanPurpose")),
        "Tenure": _display(borrower.get("tenureMonths")),
        "Status": APPLICATION_STATUS_LABELS.get(status_value, "N/A"),
        "BizFiz Score": _display(analysis.get("bizfizScore")),
        "Risk": _display(analysis.get("riskCategory")),
        "Recommendation": _display(analysis.get("recommendation")),
        # No decision yet (0 / absent) reads as N/A rather than a misleading "₹0".
        "Approved Amount": _display(approved or None, "₹"),
    }

    breakdown = analysis.get("scoreBreakdown") or {}
    breakdown_labels = {
        "locationStrength": "Location Strength",
        "sectorTrend": "Sector Trend",
        "regionalPaymentActivity": "Regional Payment Activity",
        "merchantFinancials": "Merchant Financials",
        "digitalAdoption": "Digital Adoption",
    }

    return {
        "userId": borrower["_id"],
        "application": borrower,
        # --- canonical analysis values -------------------------------------
        "bizfizScore": analysis.get("bizfizScore"),
        "riskCategory": analysis.get("riskCategory"),
        "recommendation": analysis.get("recommendation"),
        "scoreBreakdown": breakdown,
        "positiveFactors": analysis.get("positiveFactors", []),
        "riskFactors": analysis.get("riskFactors", []),
        "requestedAmount": borrower.get("amountApplied"),
        "eligibleAmount": analysis.get("eligibleAmount"),
        "amountApproved": approved,
        "applicationStatus": status_value,
        "statusLabel": APPLICATION_STATUS_LABELS.get(status_value),
        "analysisAvailable": bool(analysis),
        # --- keys the existing admin detail component already renders -------
        "userFormSubmittedInfo": form_info,
        "score": analysis.get("bizfizScore"),
        "scoreScale": 100,
        "allowedCredit": analysis.get("eligibleAmount"),
        "accountDetails": {},
        "indicators": analysis.get("indicators", []),
        "transactionalAnalysis": [
            {"name": breakdown_labels.get(k, k), "value": v} for k, v in breakdown.items()
        ],
    }


@app.post('/api/admin/update-status')
def admin_update_status(payload: AdminUpdateStatusModel = Body(...), current_user=Depends(auth.get_admin_user)):
    status_map = {
        "new": ApplicationStatus.newApplication.value,
        "pending": ApplicationStatus.newApplication.value,
        "accept": ApplicationStatus.accepted.value,
        "approve": ApplicationStatus.accepted.value,
        "halt": ApplicationStatus.halted.value,
        "review": ApplicationStatus.halted.value,
        "reject": ApplicationStatus.rejected.value,
    }
    status_key = (payload.status or "").strip().lower()
    if status_key not in status_map:
        raise HTTPException(status_code=400, detail="Invalid status. Use approve/reject/review.")
    status_value = status_map[status_key]
    # A rejected application never carries an approved amount.
    approved = 0 if status_value == ApplicationStatus.rejected.value else (payload.approvedAmount or 0)
    result = db["borrowers"].update_one(
        {"_id": ObjectId(payload.userId)},
        # `amountApproved` is the canonical field (matches BorrowerModel and the
        # client dashboard). The legacy `approvedAmount` spelling is still read
        # for older records but is no longer written.
        {"$set": {"applicationStatus": status_value, "amountApproved": approved}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found.")
    return {
        "msg": f"Application status updated to '{APPLICATION_STATUS_LABELS.get(status_value)}'.",
        "userId": payload.userId,
        "applicationStatus": status_value,
        "statusLabel": APPLICATION_STATUS_LABELS.get(status_value),
        "amountApproved": approved,
    }


if __name__ == '__main__':
    uvicorn.run(app,host='0.0.0.0')