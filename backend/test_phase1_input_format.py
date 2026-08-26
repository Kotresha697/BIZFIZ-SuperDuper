from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.main import (
    BorrowerModel,
    STANDARD_APPLICATION_FIELDS,
    normalize_borrower_data,
    submit_borrower_application,
)


VALID_APPLICATION = {
    "name": "Rahul Kumar",
    "mobileNumber": "9876543210",
    "email": "rahul@gmail.com",
    "businessName": "Rahul Fashion Store",
    "businessSector": "fashion",
    "businessCategory": "Retail",
    "businessAddress": "MG Road",
    "businessState": "karnataka",
    "businessDistrict": "bengaluru urban",
    "businessPinCode": "560001",
    "yearsInBusiness": 3,
    "monthlyRevenue": 150000,
    "monthlyTransactionCount": 250,
    "averageTransactionValue": 600,
    "digitalPaymentPercentage": 70,
    "amountApplied": 300000,
    "purposeOfLoan": "Working Capital",
    "tenureMonths": 24,
}


class FakeCollection:
    def __init__(self):
        self.documents = []

    def find_one(self, *_args, **_kwargs):
        return None

    def insert_one(self, document):
        self.documents.append(document.copy())
        return SimpleNamespace(inserted_id="507f1f77bcf86cd799439011")


class FakeDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]


def _score_report():
    return {
        "bizfizScore": 82,
        "riskCategory": "Low",
        "recommendation": "Approved",
        "eligibleAmount": 240000,
        "disclaimer": "Test",
    }


class Phase1InputFormatTests(unittest.TestCase):
    def test_normalize_borrower_data_standardizes_text_fields(self):
        normalized = normalize_borrower_data({
            "name": "  Rahul Kumar  ",
            "mobileNumber": " 9876543210 ",
            "businessState": " Karnataka ",
            "businessDistrict": " Bengaluru Urban ",
            "typeOfBusiness": " FASHION ",
            "businessPinCode": 560001,
        })

        self.assertEqual(normalized["name"], "Rahul Kumar")
        self.assertEqual(normalized["mobileNumber"], "9876543210")
        self.assertEqual(normalized["businessState"], "karnataka")
        self.assertEqual(normalized["businessDistrict"], "bengaluru urban")
        self.assertEqual(normalized["businessSector"], "fashion")
        self.assertEqual(normalized["businessPinCode"], "560001")

    def test_submit_accepts_standard_json_and_stores_only_standard_fields(self):
        fake_db = FakeDB()

        with patch("backend.main.db", fake_db), \
            patch("backend.main.scoring_service.calculate_bizfiz_score", return_value=_score_report()), \
            patch("backend.main.ml_engine.run_fraud_check", return_value={"isSuspicious": False}):
            response = submit_borrower_application(
                BorrowerModel(**VALID_APPLICATION),
                current_user={"sub": "client-123", "role": "client"},
            )

        self.assertEqual(response["msg"], "Borrower application submitted and evaluated successfully")
        stored_application = fake_db["borrowers"].documents[0]
        self.assertEqual(list(stored_application.keys())[:len(STANDARD_APPLICATION_FIELDS)], STANDARD_APPLICATION_FIELDS)
        self.assertEqual(stored_application["businessSector"], "fashion")
        self.assertEqual(stored_application["businessState"], "karnataka")
        self.assertEqual(stored_application["businessDistrict"], "bengaluru urban")
        self.assertEqual(stored_application["clientId"], "client-123")


    def test_submit_rejects_invalid_sector_values_with_400(self):
        invalid_sectors = ["Fashion", "FASHION", "Fashion Store", "fashion-business"]

        for invalid_sector in invalid_sectors:
            invalid_application = VALID_APPLICATION.copy()
            invalid_application["businessSector"] = invalid_sector

            with self.subTest(businessSector=invalid_sector), patch("backend.main.db", FakeDB()):
                with self.assertRaises(HTTPException) as context:
                    submit_borrower_application(BorrowerModel(**invalid_application))

                self.assertEqual(context.exception.status_code, 400)
                self.assertIn("businessSector must be one of", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
