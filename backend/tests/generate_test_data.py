import fitz  # PyMuPDF
import os

def create_sample_sbi_statement(output_pdf_path: str, simulate_missing_page: bool = False):
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    p1_text = """STATE BANK OF INDIA - ACCOUNT STATEMENT
Account Number: 30123456789 | IFSC: SBIN0001234
Account Holder: M/s Apex Tech Solutions | Branch: Mumbai Main

Txn Date    Value Date   Description                 Ref No        Debit (INR)   Credit (INR)  Balance (INR)
-------------------------------------------------------------------------------------------------------------
01-04-2026  01-04-2026   OPENING BALANCE                                                       1,50,000.00
02-04-2026  02-04-2026   UPI/PAYMENT/VENDOR_A        UTR90112      15,000.00                   1,35,000.00
03-04-2026  03-04-2026   NEFT/CLIENT_DEPOSIT         NEFT9841                    50,000.00     1,85,000.00
05-04-2026  05-04-2026   CHQ/PAYROLL_APRIL           CHQ00412      45,000.00                   1,40,000.00
10-04-2026  10-04-2026   ATM/CASH_WITHDRAWAL         ATM4401       10,000.00                   1,30,000.00
-------------------------------------------------------------------------------------------------------------
Page 1 of 3 (Closing Page Balance: INR 1,30,000.00)
"""
    page1.insert_text((40, 50), p1_text, fontsize=10)

    # Page 2 (Intermediate page - skipped if simulate_missing_page is True)
    if not simulate_missing_page:
        page2 = doc.new_page()
        p2_text = """STATE BANK OF INDIA - ACCOUNT STATEMENT (Contd.)

Txn Date    Value Date   Description                 Ref No        Debit (INR)   Credit (INR)  Balance (INR)
-------------------------------------------------------------------------------------------------------------
12-04-2026  12-04-2026   UPI/OFFICE_RENT             UTR90455      20,000.00                   1,10,000.00
15-04-2026  15-04-2026   DIRECT_TAX_PAYMENT          TAX11099      18,000.00                     92,000.00
-------------------------------------------------------------------------------------------------------------
Page 2 of 3 (Closing Page Balance: INR 92,000.00)
"""
        page2.insert_text((40, 50), p2_text, fontsize=10)

    # Page 3 (or Page 2 in missing page scenario)
    page3 = doc.new_page()
    p3_text = """STATE BANK OF INDIA - ACCOUNT STATEMENT (Contd.)

Txn Date    Value Date   Description                 Ref No        Debit (INR)   Credit (INR)  Balance (INR)
-------------------------------------------------------------------------------------------------------------
18-04-2026  18-04-2026   UPI/SOFTWARE_SUBSCRIPTION   UTR99011       2,000.00                     90,000.00
20-04-2026  20-04-2026   NEFT/INVOICE_881            NEFT8891                    25,000.00     1,15,000.00
-------------------------------------------------------------------------------------------------------------
Page 3 of 3 (Closing Page Balance: INR 1,15,000.00)
"""
    page3.insert_text((40, 50), p3_text, fontsize=10)

    doc.save(output_pdf_path)
    doc.close()
    print(f"Generated test PDF: {output_pdf_path}")

if __name__ == "__main__":
    os.makedirs("/home/aditya/Heart/test_data", exist_ok=True)
    create_sample_sbi_statement("/home/aditya/Heart/test_data/sample_sbi_complete.pdf", False)
    create_sample_sbi_statement("/home/aditya/Heart/test_data/sample_sbi_missing_page.pdf", True)
