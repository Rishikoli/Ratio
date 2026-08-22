import unittest
from ratio.models.schemas import Transaction, RowValidationStatus
from ratio.core.validation_engine import ValidationEngine

class TestValidationEngine(unittest.TestCase):

    def test_valid_transactions(self):
        t1 = Transaction(id="1", date="2026-04-01", description="Dep", debit=None, credit=5000.0, balance=50000.0, page_number=1)
        t2 = Transaction(id="2", date="2026-04-02", description="Wth", debit=1000.0, credit=None, balance=49000.0, page_number=1)
        
        trxs, summary = ValidationEngine.validate_statement([t1, t2])
        self.assertEqual(summary.valid_rows, 2)
        self.assertEqual(summary.review_rows, 0)
        self.assertFalse(summary.has_gaps)

    def test_missing_page_gap_detection(self):
        # Page 1 ends at 50,000 balance
        t1 = Transaction(id="1", date="2026-04-01", description="Txn 1", debit=None, credit=5000.0, balance=50000.0, page_number=1)
        # Page 2 starts at 42,000 balance (missing 8,000 page gap)
        t2 = Transaction(id="2", date="2026-04-10", description="Txn 2", debit=1000.0, credit=None, balance=41000.0, page_number=2)
        
        trxs, summary = ValidationEngine.validate_statement([t1, t2])
        self.assertTrue(summary.has_gaps)
        self.assertEqual(len(summary.gaps), 1)
        self.assertEqual(summary.gaps[0].alert_type, "MISSING_PAGE")
        self.assertEqual(summary.gaps[0].difference, 8000.0)
        self.assertEqual(trxs[1].status, RowValidationStatus.GAP_DETECTED)
        self.assertIn("Missing transactions detected", trxs[1].validation_message)

if __name__ == '__main__':
    unittest.main()
