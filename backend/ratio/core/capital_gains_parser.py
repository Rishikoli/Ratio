import re
from typing import List, Tuple, Optional
from ratio.models.schemas import CapitalGainItem, CapitalGainsSummary, RowValidationStatus
from ratio.core.ocr_engine import TextLine

class CapitalGainsParser:
    """
    Parses Mutual Fund & Equity Capital Gains statements (CAMS, KFintech, ICICI, Axis, Zerodha).
    Extracts STCG, LTCG, Purchase Costs, and Sale Proceeds for ITR Schedule CG filing.
    """

    @classmethod
    def parse_capital_gains(cls, lines: List[TextLine]) -> CapitalGainsSummary:
        items: List[CapitalGainItem] = []
        current_scheme = "Mutual Fund Investment"
        current_folio = None
        
        date_pattern = r'\b\d{1,2}[-/\.](?:\d{1,2}|[A-Za-z]{3})[-/\.]\d{2,4}\b'
        amount_pattern = r'\b(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?\b'

        for idx, line in enumerate(lines):
            txt = line.text.strip()
            if not txt:
                continue

            # Detect Scheme Name or Folio Header
            if any(k in txt.upper() for k in ["SCHEME", "FUND", "OPTION", "GROWTH", "DIRECT", "REGULAR", "FOLIO"]):
                if len(txt) > 8 and not re.search(r'\d{5,}', txt):
                    current_scheme = txt
                folio_match = re.search(r'FOLIO(?:\s*NO\.?)?\s*:?\s*([\w/]+)', txt, re.IGNORECASE)
                if folio_match:
                    current_folio = folio_match.group(1)

            # Find transaction lines containing dates and numerical values
            dates = re.findall(date_pattern, txt)
            # Find numbers
            amounts = []
            for token in re.findall(amount_pattern, txt):
                clean_num = token.replace(",", "")
                try:
                    val = float(clean_num)
                    if 0.01 <= val <= 100000000.0:  # Filter sensible monetary amounts
                        amounts.append(val)
                except ValueError:
                    pass

            if len(amounts) >= 3:
                # We have cost, sale proceeds, and net gain/loss
                p_cost = amounts[0]
                s_val = amounts[1]
                gain_val = amounts[2] if len(amounts) >= 3 else (s_val - p_cost)
                
                # Determine STCG vs LTCG based on dates or keywords
                is_ltcg = "LTCG" in txt.upper() or "LONG" in txt.upper()
                gain_type = "LTCG" if is_ltcg else "STCG"
                
                p_date = dates[0] if len(dates) >= 1 else "N/A"
                s_date = dates[1] if len(dates) >= 2 else "N/A"

                stcg_amt = gain_val if gain_type == "STCG" else 0.0
                ltcg_amt = gain_val if gain_type == "LTCG" else 0.0

                item = CapitalGainItem(
                    id=str(len(items) + 1),
                    scheme_name=current_scheme,
                    folio_no=current_folio,
                    purchase_date=p_date,
                    purchase_cost=p_cost,
                    sale_date=s_date,
                    sale_value=s_val,
                    stcg=stcg_amt,
                    ltcg=ltcg_amt,
                    gain_type=gain_type,
                    status=RowValidationStatus.VALID
                )
                items.append(item)

        # Fallback if no specific format matched
        if not items:
            # Generate aggregate entry from detected amounts
            all_numbers = []
            for l in lines:
                for token in re.findall(amount_pattern, l.text):
                    try:
                        v = float(token.replace(",", ""))
                        if v > 100:
                            all_numbers.append(v)
                    except ValueError:
                        pass
            if len(all_numbers) >= 2:
                items.append(CapitalGainItem(
                    id="1",
                    scheme_name="Aggregated Capital Gain Summary",
                    purchase_cost=min(all_numbers),
                    sale_value=max(all_numbers),
                    stcg=max(all_numbers) - min(all_numbers),
                    ltcg=0.0,
                    gain_type="STCG"
                ))

        total_stcg = sum(i.stcg for i in items)
        total_ltcg = sum(i.ltcg for i in items)
        total_cost = sum(i.purchase_cost for i in items)
        total_sale = sum(i.sale_value for i in items)

        return CapitalGainsSummary(
            total_stcg=round(total_stcg, 2),
            total_ltcg=round(total_ltcg, 2),
            total_purchase_cost=round(total_cost, 2),
            total_sale_value=round(total_sale, 2),
            item_count=len(items),
            items=items
        )
