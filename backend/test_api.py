import requests
import json
import random

BASE_URL = "http://127.0.0.1:8000"

def test_lending_platform():
    print("[*] Starting Lending Platform End-to-End API Tests...")
    
    # 1. Register a new test admin
    admin_username = f"admin_{random.randint(1000, 9999)}"
    register_payload = {
        "username": admin_username,
        "password": "testpassword123",
        "role": "admin"
    }
    
    reg_res = requests.post(f"{BASE_URL}/api/auth/register", json=register_payload)
    assert reg_res.status_code == 200, f"Register failed: {reg_res.text}"
    print(f"[OK] Admin registration success: {admin_username}")
    
    # 2. Login test admin
    login_payload = {
        "username": admin_username,
        "password": "testpassword123"
    }
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["accessToken"]
    print("[OK] Admin login success, token retrieved")
    
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. Submit borrower application (19 fields)
    borrower_payload = {
        "name": "Rajesh Kumar",
        "mobileNumber": "9876543210",
        "typeOfBusiness": "fashion",
        "businessAddress": "123 Commercial St, MG Road",
        "businessState": "Karnataka",
        "businessDistrict": "Bangalore Urban",
        "businessPinCode": "560001",
        "amountApplied": 350000,
        "applicationStatus": 0,
        
        "businessName": "Rajesh Textiles",
        "businessCategory": "Retail",
        "panNumber": "ABCDE1234F",
        "aadhaarNumber": "123456789012",
        "yearsInBusiness": 4,
        "monthlyRevenue": 150000,
        "monthlyTransactionCount": 200,
        "averageTransactionValue": 750,
        "phonepeUsageMetrics": {
            "merchantTransactions": 180,
            "averageTicketSize": 800
        },
        "bankAccountDetails": {
            "accNumber": "987654321023",
            "ifsc": "SBIN0001234",
            "accType": "Current"
        },
        "existingLoans": [],
        "purposeOfLoan": "Inventory Purchase",
        "digitalPaymentPercentage": 82.5,
        "businessSector": "fashion",
        "uploadedDocuments": []
    }
    
    submit_res = requests.post(f"{BASE_URL}/api/borrower/submit", json=borrower_payload)
    assert submit_res.status_code == 200, f"Submit failed: {submit_res.text}"
    userId = submit_res.json()["userId"]
    print(f"[OK] Borrower application submitted successfully. UserId: {userId}")
    
    # 4. Fetch admin applications list
    apps_res = requests.get(f"{BASE_URL}/api/admin/applications", headers=auth_headers)
    assert apps_res.status_code == 200, f"Get apps failed: {apps_res.text}"
    apps = apps_res.json()
    assert any(a["userId"] == userId for a in apps), "Submitted app not in admin listing"
    print("[OK] Borrower app appears in secure admin listing")
    
    # 5. Fetch Loan Decision analysis
    analysis_res = requests.get(f"{BASE_URL}/api/admin/analysis/{userId}", headers=auth_headers)
    assert analysis_res.status_code == 200, f"Get analysis failed: {analysis_res.text}"
    report = analysis_res.json()
    
    print("\n[Risk Engine Analysis Output]")
    print(f"   - Business Score: {report['businessScore']}/100")
    print(f"   - Approval Probability: {report['approvalProbability']}%")
    print(f"   - Risk Classification: {report['riskLevel']}")
    print(f"   - AI Recommendation: {report['recommendation']}")
    print(f"   - Max Credit Allowed: RS {report['allowedCredit']}")
    print(f"   - PAN Verification: {report['kyc']['pan']['status']} ({report['kyc']['pan']['holderType']})")
    print(f"   - Aadhaar Verification: {report['kyc']['aadhaar']['status']}")
    print(f"   - Fraud Suspicious Flag: {report['fraudCheck']['isSuspicious']}")
    print(f"   - AI Pros: {report['explainableAI']['pros']}")
    print(f"   - AI Cons: {report['explainableAI']['cons']}")
    
    assert "businessScore" in report, "Decision missing businessScore"
    assert "explainableAI" in report, "Decision missing explainableAI"
    print("[OK] Loan Decision Engine validated successfully")
    
    # 6. Audited Accept status update
    update_payload = {
        "userId": userId,
        "status": "accept",
        "approvedAmount": 250000
    }
    update_res = requests.post(f"{BASE_URL}/api/admin/update-status", json=update_payload, headers=auth_headers)
    assert update_res.status_code == 200, f"Update status failed: {update_res.text}"
    print("[OK] Borrower application accepted and approved amount set (audited)")
    
    # 7. Get dashboard summary
    dashboard_res = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=auth_headers)
    assert dashboard_res.status_code == 200, f"Get dashboard failed: {dashboard_res.text}"
    dashboard = dashboard_res.json()
    assert dashboard["totalApplications"] > 0, "Dashboard reporting 0 apps"
    assert dashboard["approvedCount"] > 0, "Dashboard approved count should be > 0"
    print("\n[Admin Dashboard Summary]")
    print(f"   - Total Pipeline: {dashboard['totalApplications']}")
    print(f"   - Approved Rate: {dashboard['approvedCount']} Approved / {dashboard['rejectedCount']} Rejected / {dashboard['reviewCount']} Pending")
    print(f"   - Average Risk Score: {dashboard['averageBusinessScore']}")
    print(f"   - Suspected Fraud cases: {dashboard['fraudAlertsCount']}")
    print("[OK] Admin Dashboard Aggregations validated successfully")
    
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY! Alternate scoring platform is fully operational.")

if __name__ == "__main__":
    test_lending_platform()
