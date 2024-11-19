from typing import Dict, List, Optional
import re
from .base import BaseIndustryStrategy
import logging

logger = logging.getLogger(__name__)

class FinancialIndustryStrategy(BaseIndustryStrategy):
    @property
    def industry_name(self) -> str:
        return "financial"

    @property
    def document_types(self) -> List[str]:
        return [
            "bank_statement",
            "credit_card_statement",
            "invoice",
            "tax_return",
            "payroll",
            "loan_application",
            "financial_report"
        ]

    @property
    def keywords(self) -> Dict[str, List[str]]:
        return {
            "bank_statement": [
                "account balance",
                "transaction history",
                "deposit",
                "withdrawal",
                "account number",
                "statement period",
                "opening balance",
                "closing balance"
            ],
            "credit_card_statement": [
                "credit limit",
                "minimum payment",
                "statement balance",
                "apr",
                "credit card",
                "card number",
                "payment due date",
                "interest charges"
            ],
            "invoice": [
                "invoice number",
                "bill to",
                "payment terms",
                "due date",
                "subtotal",
                "total amount",
                "tax",
                "invoice date"
            ],
            "tax_return": [
                "tax year",
                "taxable income",
                "deductions",
                "tax paid",
                "tax return",
                "social security",
                "filing status",
                "irs"
            ],
            "payroll": [
                "salary",
                "wages",
                "deductions",
                "net pay",
                "gross pay",
                "pay period",
                "employee id",
                "payroll date"
            ],
            "loan_application": [
                "loan amount",
                "interest rate",
                "term",
                "collateral",
                "borrower",
                "credit score",
                "monthly payment",
                "application date"
            ],
            "financial_report": [
                "balance sheet",
                "income statement",
                "cash flow",
                "assets",
                "liabilities",
                "equity",
                "profit",
                "loss"
            ]
        }

    def custom_rules(self, text: str, metadata: dict) -> Optional[str]:
        """Apply financial document specific rules."""
        text = text.lower()
        
        # Check for account number patterns
        if self._contains_account_number(text):
            if self._contains_credit_card_patterns(text):
                return "credit_card_statement"
            if self._contains_bank_patterns(text):
                return "bank_statement"

        # Check for invoice patterns
        if self._contains_invoice_patterns(text):
            return "invoice"

        # Check for tax return patterns
        if self._contains_tax_patterns(text):
            return "tax_return"

        # Check tables in metadata
        if metadata.get('tables'):
            if self._is_financial_statement_table(metadata['tables']):
                return "financial_report"
            if self._is_payroll_table(metadata['tables']):
                return "payroll"

        return None

    def _contains_account_number(self, text: str) -> bool:
        account_patterns = [
            r'\b\d{10,12}\b',  # Basic account number
            r'\b\d{4}[\s-]\d{4}[\s-]\d{4}\b',  # Formatted account number
            r'account\s*#?\s*:\s*\d+',  # Labeled account number
        ]
        return any(bool(re.search(pattern, text)) for pattern in account_patterns)

    def _contains_credit_card_patterns(self, text: str) -> bool:
        cc_patterns = [
            r'\b(?:\d{4}[\s-]){3}\d{4}\b',  # Credit card number format
            r'credit\s+card',
            r'card\s+member',
            r'minimum\s+payment',
            r'apr'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in cc_patterns)

    def _contains_bank_patterns(self, text: str) -> bool:
        bank_patterns = [
            r'\b(opening|closing)\s+balance',
            r'\b(deposit|withdrawal)',
            r'transaction\s+history',
            r'statement\s+period',
            r'available\s+balance'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in bank_patterns)

    def _contains_invoice_patterns(self, text: str) -> bool:
        invoice_patterns = [
            r'invoice\s+number',
            r'bill\s+to',
            r'payment\s+terms',
            r'due\s+date',
            r'total\s+amount'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in invoice_patterns)

    def _contains_tax_patterns(self, text: str) -> bool:
        tax_patterns = [
            r'form\s+1040',
            r'tax\s+return',
            r'taxable\s+income',
            r'irs',
            r'tax\s+year'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in tax_patterns)

    def _is_financial_statement_table(self, tables: List[List[str]]) -> bool:
        financial_headers = {
            'assets', 'liabilities', 'equity', 'revenue', 'expenses',
            'income', 'balance', 'cash flow', 'profit', 'loss'
        }
        
        for table in tables:
            if not table:
                continue
            headers = {cell.lower() for cell in table[0]}
            if len(headers & financial_headers) >= 2:
                return True
        return False

    def _is_payroll_table(self, tables: List[List[str]]) -> bool:
        payroll_headers = {
            'salary', 'wages', 'deductions', 'net pay', 'gross pay',
            'employee', 'hours', 'overtime', 'taxes'
        }
        
        for table in tables:
            if not table:
                continue
            headers = {cell.lower() for cell in table[0]}
            if len(headers & payroll_headers) >= 3:
                return True
        return False
