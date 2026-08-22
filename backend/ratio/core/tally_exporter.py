import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List
from ratio.models.schemas import StatementMetadata, Transaction

class TallyExporter:
    """
    Exports extracted transactions as Tally Prime XML Vouchers.
    Enables one-click import into Tally ledgers.
    """

    @classmethod
    def generate_xml(cls, metadata: StatementMetadata, transactions: List[Transaction]) -> str:
        envelope = ET.Element("ENVELOPE")
        
        header = ET.SubElement(envelope, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
        
        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        
        req_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(req_desc, "REPORTNAME").text = "Vouchers"
        
        req_data = ET.SubElement(import_data, "REQUESTDATA")
        
        for trx in transactions:
            tally_msg = ET.SubElement(req_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            voucher = ET.SubElement(tally_msg, "VOUCHER", {"VTYPE": "Payment" if trx.debit else "Receipt", "ACTION": "Create"})
            
            # Date in YYYYMMDD format
            clean_date = trx.date.replace("-", "")
            ET.SubElement(voucher, "DATE").text = clean_date
            ET.SubElement(voucher, "NARRATION").text = f"{trx.description} (Ref: {trx.reference or 'N/A'})"
            ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Bank Payment" if trx.debit else "Bank Receipt"
            
            # Bank Ledger Entry
            bank_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(bank_entry, "LEDGERNAME").text = metadata.institution
            ET.SubElement(bank_entry, "ISDEEMEDPOSITIVE").text = "YES" if trx.credit else "NO"
            amount_val = (trx.credit or 0.0) if trx.credit else -(trx.debit or 0.0)
            ET.SubElement(bank_entry, "AMOUNT").text = f"{amount_val:.2f}"
            
            # Counter Ledger Entry (Suspense Account for accountant allocation)
            counter_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(counter_entry, "LEDGERNAME").text = "Suspense Account"
            ET.SubElement(counter_entry, "ISDEEMEDPOSITIVE").text = "NO" if trx.credit else "YES"
            counter_amount = -(trx.credit or 0.0) if trx.credit else (trx.debit or 0.0)
            ET.SubElement(counter_entry, "AMOUNT").text = f"{counter_amount:.2f}"

        xml_str = minidom.parseString(ET.tostring(envelope)).toprettyxml(indent="  ")
        return xml_str
