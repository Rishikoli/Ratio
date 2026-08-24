import os
import json
import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

from ratio.models.schemas import Transaction, StatementMetadata, DocumentType, RowValidationStatus
from ratio.core.ocr_engine import TextLine
from ratio.core.document_loader import DocumentPage

CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'bank_configs')

class ParserRouter:
    """
    Identifies bank type from statement text, selects configuration,
    and extracts structured transactions from text lines.
    """
    
    def __init__(self):
        self.configs: Dict[str, dict] = {}
        self._load_configs()
        
    def _load_configs(self):
        if not os.path.exists(CONFIG_DIR):
            return
        for file in os.listdir(CONFIG_DIR):
            if file.endswith('.json'):
                path = os.path.join(CONFIG_DIR, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.configs[data.get('bank_code', file)] = data
                except Exception:
                    pass

    def identify_bank(self, all_lines: List[TextLine]) -> Tuple[str, dict]:
        header_text = " ".join([l.text for l in all_lines[:200]]).upper()
        
        # Check for special statement types first
        if "ANNUAL INFORMATION STATEMENT" in header_text or "AIS" in header_text or "INCOME TAX DEPARTMENT" in header_text:
            return "AIS", {
                "bank_name": "Annual Information Statement (AIS)",
                "bank_code": "AIS",
                "keywords": ["AIS", "ANNUAL INFORMATION STATEMENT", "INCOME TAX"]
            }
        elif "CAPITAL GAIN" in header_text or "CAPITAL GAINS" in header_text:
            return "CAPITAL_GAINS", {
                "bank_name": "Mutual Fund Capital Gains Statement",
                "bank_code": "CAPITAL_GAINS",
                "keywords": ["CAPITAL GAINS", "MUTUAL FUND", "NAV", "UNITS"]
            }
        elif "MUTUAL FUND" in header_text or "STATEMENT OF ACCOUNT" in header_text:
            return "MUTUAL_FUND", {
                "bank_name": "Mutual Fund Statement of Account",
                "bank_code": "MUTUAL_FUND",
                "keywords": ["MUTUAL FUND", "FOLIO", "NAV", "UNITS"]
            }
        
        best_match = "GENERIC"
        highest_score = 0
        
        for code, cfg in self.configs.items():
            if code == "GENERIC":
                continue
            keywords = cfg.get("keywords", [])
            score = 0
            for kw in keywords:
                kw_up = kw.upper()
                if kw_up in header_text:
                    score += 1
                elif fuzz is not None and len(kw_up) > 4:
                    if fuzz.partial_ratio(kw_up, header_text) >= 88:
                        score += 1
            if score > highest_score:
                highest_score = score
                best_match = code
                
        if highest_score < 2 and "GENERIC" in self.configs:
            return "GENERIC", self.configs["GENERIC"]
            
        return best_match, self.configs.get(best_match, self.configs.get("GENERIC", {}))

    def _is_metadata_or_noise(self, text: str) -> bool:
        upper = text.upper()
        noise_keywords = [
            "GENERATION DATE", "GENERATED ON", "PRINT DATE", "PRINTED ON",
            "PAGE ", "PAGE NO", "SYSTEM GENERATED", "DISCLAIMER",
            "INCOME TAX DEPARTMENT", "GOVT OF INDIA", "GOVERNMENT OF INDIA",
            "ANNUAL INFORMATION STATEMENT", "FORM 26AS", "TAX DEDUCTED AT SOURCE",
            "COMPUTER GENERATED", "THIS IS A SYSTEM", "SUMMARY OF TAX",
            "DATE :", "TIME :", "TIMESTAMP"
        ]
        if any(kw in upper for kw in noise_keywords):
            return True
        # Lines with just dates or timestamps
        if re.fullmatch(r'[\d\-/\.\s\:\,\w]{1,25}', text) and ("DATE" in upper or "TIME" in upper):
            return True
        return False

    def parse_document(self, filename: str, pages: List[DocumentPage], all_lines: List[TextLine]) -> Tuple[StatementMetadata, List[Transaction]]:
        bank_code, config = self.identify_bank(all_lines)
        
        metadata = StatementMetadata(
            source_file=filename,
            filename=filename,
            document_type=config.get("bank_code", "BANK_STATEMENT"),
            institution=config.get("bank_name", "Unknown Institution"),
            total_pages=len(pages),
            processed_pages=len(pages)
        )
        
        transactions: List[Transaction] = []
        
        # Regex patterns for transaction parsing
        date_pattern = r'(\d{1,2}[-/\.\s](?:\d{1,2}|[A-Za-z]{3})[-/\.\s]\d{2,4})'
        
        line_idx = 0
        while line_idx < len(all_lines):
            line = all_lines[line_idx]
            txt = line.text.strip()
            
            # Skip metadata and system noise lines
            if self._is_metadata_or_noise(txt):
                line_idx += 1
                continue

            # Find date at start of line or transaction entry
            date_match = re.search(date_pattern, txt)
            if date_match:
                extracted_date = self._normalize_date(date_match.group(1))
                if extracted_date:
                    # Attempt to extract amounts (Debit, Credit, Balance) from line
                    trx = self._parse_transaction_row(all_lines, line_idx, extracted_date)
                    if trx:
                        transactions.append(trx)
            line_idx += 1

        self._self_heal_transactions(transactions)

        return metadata, transactions

    def _self_heal_transactions(self, transactions: List[Transaction]):
        """
        Mathematical Self-Healing:
        Validates Previous Balance - Debit + Credit = Current Balance.
        If a balance is incorrect, but can be fixed to match math constraints,
        auto-correct it and lower confidence to flag it.
        """
        if not transactions:
            return

        for i in range(1, len(transactions)):
            prev_trx = transactions[i-1]
            curr_trx = transactions[i]

            if prev_trx.balance is not None:
                expected_balance = prev_trx.balance
                if curr_trx.debit is not None:
                    expected_balance -= curr_trx.debit
                if curr_trx.credit is not None:
                    expected_balance += curr_trx.credit
                
                expected_balance = round(expected_balance, 2)
                curr_balance_rounded = round(curr_trx.balance, 2) if curr_trx.balance is not None else None

                if curr_balance_rounded != expected_balance:
                    # Self-heal the balance
                    curr_trx.balance = expected_balance
                    # Lower confidence to indicate it was auto-corrected
                    curr_trx.confidence = max(0.1, curr_trx.confidence - 0.4)
                    if not curr_trx.description.endswith("[Auto-Healed]"):
                        curr_trx.description += " [Auto-Healed]"

    def _normalize_date(self, raw_date: str) -> Optional[str]:
        raw_date = raw_date.strip().replace('.', '/').replace('-', '/')
        formats = [
            "%d/%m/%Y", "%d/%b/%Y", "%d/%m/%y", "%d/%b/%y",
            "%Y/%m/%d", "%d %b %Y", "%d-%b-%Y", "%d-%m-%Y"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(raw_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None

    @staticmethod
    def _clean_amount_string(raw: str) -> Optional[float]:
        if not raw:
            return None
        # Remove currency symbols and surrounding noise
        cleaned = re.sub(r'[₹RsINR\$€]', '', raw, flags=re.IGNORECASE).strip()
        if not cleaned:
            return None
            
        # European format: 1.000,50 -> 1000.50
        if re.match(r'^\d{1,3}(\.\d{3})+,\d{2}$', cleaned):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        # Indian / Standard format: 1,00,000.50 or 100,000.50
        else:
            cleaned = cleaned.replace(',', '')
            
        try:
            val = float(cleaned)
            return val
        except ValueError:
            return None

    def _parse_transaction_row(self, lines: List[TextLine], start_idx: int, date_str: str) -> Optional[Transaction]:
        line = lines[start_idx]
        text = line.text
        
        # Exclude metadata text
        if self._is_metadata_or_noise(text):
            return None

        # Clean currency symbols
        clean_text = re.sub(r'[₹\$€]|Rs\.?\b|INR\b', '', text, flags=re.IGNORECASE)

        # Extract all numbers/amounts from the line
        amounts = re.findall(r'[\d,]+\.\d{2}|\b\d{1,3}(?:\.\d{3})+,\d{2}\b', clean_text)
        
        if not amounts:
            # Try whole numbers if decimal absent
            raw_nums = re.findall(r'\b\d{3,7}\b', clean_text)
            # Filter out numbers that match typical calendar years (2020-2029) or page numbers
            amounts = [n for n in raw_nums if not (2020 <= int(n) <= 2030)]
            
        if not amounts:
            return None
            
        float_amounts = []
        for amt in amounts:
            parsed_val = self._clean_amount_string(amt)
            if parsed_val is not None:
                # Filter out exact calendar year values if parsed as float
                if 2020.0 <= parsed_val <= 2030.0 and "." not in amt:
                    continue
                float_amounts.append(parsed_val)
                
        if not float_amounts:
            return None
            
        balance = float_amounts[-1]  # Last amount is usually Balance
        debit = None
        credit = None
        
        # Check if line indicates Debit vs Credit
        lower_txt = text.lower()
        if len(float_amounts) >= 2:
            txn_amt = float_amounts[-2]
            
            # 1. Explicit keyword check
            if any(k in lower_txt for k in ["dr", "debit", "withdraw", "paid", "to ", "utr", "chq", "atm", "tax"]):
                debit = txn_amt
                credit = None
            elif any(k in lower_txt for k in ["cr", "credit", "deposit", "by ", "neft", "rtgs", "salary"]):
                credit = txn_amt
                debit = None
            else:
                # Default: if description doesn't specify, treat as debit
                debit = txn_amt
                credit = None
        else:
            # Single amount present
            debit = float_amounts[0]
            credit = None
            
        # Clean description (remove date, time, and amounts from line text)
        desc = re.sub(r'\d{1,2}[-/\.\s](?:\d{1,2}|[A-Za-z]{3})[-/\.\s]\d{2,4}', '', text)
        desc = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?', '', desc)
        desc = re.sub(r'[\d,]+\.\d{2}', '', desc).strip()
        desc = re.sub(r'[\,\:\-]', ' ', desc).strip()
        desc = re.sub(r'\s+', ' ', desc)
        
        if not desc or len(desc) < 3:
            desc = f"Transaction on {date_str}"
            
        return Transaction(
            id=str(uuid.uuid4())[:8],
            date=date_str,
            description=desc,
            debit=debit,
            credit=credit,
            balance=balance,
            page_number=line.page_number,
            confidence=line.confidence
        )
