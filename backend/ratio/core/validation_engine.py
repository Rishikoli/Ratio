from typing import List, Tuple
from datetime import datetime
from ratio.models.schemas import Transaction, ValidationSummary, GapAlert, RowValidationStatus

class ValidationEngine:
    """
    Financial logic validation engine for Ratio:
    1. Mathematical Balance Validation (Previous Balance + Credit - Debit == Current Balance).
    2. Missing Page & Gap Detection across page boundaries and date sequences.
    """

    @classmethod
    def validate_statement(cls, transactions: List[Transaction], document_type: str = "BANK_STATEMENT") -> Tuple[List[Transaction], ValidationSummary]:
        if not transactions:
            return [], ValidationSummary(
                total_rows=0, valid_rows=0, review_rows=0, error_rows=0,
                has_gaps=False, gaps=[], overall_confidence=1.0
            )

        # Non-bank statement types (AIS, Capital Gains, Mutual Funds) do not have a running bank balance
        is_running_balance_doc = document_type in ["BANK_STATEMENT", "GENERIC"]

        valid_count = 0
        review_count = 0
        error_count = 0
        gaps: List[GapAlert] = []

        prev_trx: Transaction = None

        for idx, trx in enumerate(transactions):
            # Check row-to-row mathematical continuity for running balance documents
            if is_running_balance_doc and prev_trx is not None:
                expected_balance = prev_trx.balance + (trx.credit or 0.0) - (trx.debit or 0.0)
                actual_balance = trx.balance
                diff = abs(expected_balance - actual_balance)

                if diff > 0.05:  # Tolerance for rounding
                    # Check if this is across a page boundary (Missing Page Indicator)
                    if trx.page_number > prev_trx.page_number:
                        gap_msg = (
                            f"⚠ Warning: Missing transactions detected between {prev_trx.date} and {trx.date}. "
                            f"Balance mismatch of ₹{diff:,.2f} (Expected: ₹{expected_balance:,.2f}, Actual: ₹{actual_balance:,.2f}). "
                            f"Please upload the missing page between Page {prev_trx.page_number} and Page {trx.page_number}."
                        )
                        trx.status = RowValidationStatus.GAP_DETECTED
                        trx.validation_message = gap_msg

                        gaps.append(GapAlert(
                            alert_type="MISSING_PAGE",
                            from_date=prev_trx.date,
                            to_date=trx.date,
                            expected_balance=expected_balance,
                            actual_balance=actual_balance,
                            difference=diff,
                            page_after=prev_trx.page_number,
                            message=gap_msg
                        ))
                        error_count += 1
                    else:
                        # Row-level OCR or math error
                        err_msg = (
                            f"Math Mismatch: Previous ({prev_trx.balance}) + Credit ({trx.credit or 0}) - Debit ({trx.debit or 0}) "
                            f"equals ₹{expected_balance:,.2f}, but OCR read ₹{actual_balance:,.2f}."
                        )
                        trx.status = RowValidationStatus.REVIEW_NEEDED
                        trx.validation_message = err_msg
                        review_count += 1
                else:
                    trx.status = RowValidationStatus.VALID
                    trx.validation_message = "Validated successfully"
                    valid_count += 1
            else:
                # First transaction in statement
                trx.status = RowValidationStatus.VALID
                trx.validation_message = "Opening transaction"
                valid_count += 1

            prev_trx = trx

        total_rows = len(transactions)
        overall_conf = float(valid_count) / float(total_rows) if total_rows > 0 else 1.0

        summary = ValidationSummary(
            total_rows=total_rows,
            valid_rows=valid_count,
            review_rows=review_count,
            error_rows=error_count,
            has_gaps=len(gaps) > 0,
            gaps=gaps,
            overall_confidence=round(overall_conf, 2)
        )

        return transactions, summary
