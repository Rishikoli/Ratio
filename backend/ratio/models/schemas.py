from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RowValidationStatus(str, Enum):
    VALID = "VALID"
    REVIEW_NEEDED = "REVIEW_NEEDED"
    GAP_DETECTED = "GAP_DETECTED"
    ERROR = "ERROR"

class DocumentType(str, Enum):
    BANK_STATEMENT = "BANK_STATEMENT"
    CAPITAL_GAINS = "CAPITAL_GAINS"
    MUTUAL_FUND = "MUTUAL_FUND"
    AIS = "AIS"

class Transaction(BaseModel):
    id: str
    date: str
    description: str
    reference: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: float
    status: RowValidationStatus = RowValidationStatus.VALID
    validation_message: Optional[str] = None
    page_number: int = 1

class CapitalGainItem(BaseModel):
    id: str
    scheme_name: str
    folio_no: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: float = 0.0
    sale_date: Optional[str] = None
    sale_value: float = 0.0
    stcg: float = 0.0
    ltcg: float = 0.0
    gain_type: str = "STCG"  # STCG or LTCG
    is_grandfathered: bool = False
    status: RowValidationStatus = RowValidationStatus.VALID

class CapitalGainsSummary(BaseModel):
    total_stcg: float = 0.0
    total_ltcg: float = 0.0
    total_purchase_cost: float = 0.0
    total_sale_value: float = 0.0
    item_count: int = 0
    items: List[CapitalGainItem] = []

class GapAlert(BaseModel):
    alert_type: str = "MISSING_PAGE"  # MISSING_PAGE, BALANCE_MISMATCH
    start_page: int = 1
    end_page: int = 1
    page_after: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    expected_balance: float = 0.0
    actual_balance: float = 0.0
    difference: float = 0.0
    message: str = ""

class ValidationSummary(BaseModel):
    total_rows: int = 0
    valid_rows: int = 0
    review_rows: int = 0
    error_rows: int = 0
    has_gaps: bool = False
    gaps: List[GapAlert] = []
    overall_confidence: float = 1.0

class StatementMetadata(BaseModel):
    institution: str = "Unknown Institution"
    account_number: Optional[str] = None
    statement_period: Optional[str] = None
    source_file: str = "document.pdf"
    filename: Optional[str] = None
    total_pages: int = 1
    processed_pages: int = 1
    document_type: str = "BANK_STATEMENT"  # BANK_STATEMENT, CAPITAL_GAINS, MUTUAL_FUND, AIS

    def __init__(self, **data):
        # Sync filename and source_file if only one is provided
        if 'filename' in data and 'source_file' not in data:
            data['source_file'] = data['filename']
        elif 'source_file' in data and 'filename' not in data:
            data['filename'] = data['source_file']
        super().__init__(**data)

class ExtractionResult(BaseModel):
    metadata: StatementMetadata
    transactions: List[Transaction] = []
    capital_gains: Optional[CapitalGainsSummary] = None
    validation: ValidationSummary
    logs: List[str] = []

class RevalidateRequest(BaseModel):
    metadata: StatementMetadata
    transactions: List[Transaction]
    capital_gains: Optional[CapitalGainsSummary] = None
