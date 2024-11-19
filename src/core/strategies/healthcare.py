from typing import Dict, List, Optional
import re
from .base import BaseIndustryStrategy
import logging

logger = logging.getLogger(__name__)

class HealthcareIndustryStrategy(BaseIndustryStrategy):
    @property
    def industry_name(self) -> str:
        return "healthcare"

    @property
    def document_types(self) -> List[str]:
        return [
            "medical_record",
            "prescription",
            "lab_report",
            "medical_bill",
            "insurance_claim",
            "medical_imaging",
            "discharge_summary",
            "vaccination_record"
        ]

    @property
    def keywords(self) -> Dict[str, List[str]]:
        return {
            "medical_record": [
                "patient history",
                "vital signs",
                "medical record number",
                "chief complaint",
                "diagnosis",
                "treatment plan",
                "allergies",
                "medications",
                "physical examination",
                "medical history",
                "family history",
                "social history"
            ],
            "prescription": [
                "rx",
                "prescribe",
                "dosage",
                "refill",
                "pharmacy",
                "sig",
                "dispense",
                "prescription",
                "medication",
                "take as directed",
                "tablets",
                "capsules"
            ],
            "lab_report": [
                "lab results",
                "test date",
                "reference range",
                "specimen",
                "laboratory",
                "collected",
                "test name",
                "values",
                "units",
                "normal range",
                "analysis",
                "methodology"
            ],
            "medical_bill": [
                "amount due",
                "service date",
                "billing code",
                "charges",
                "insurance",
                "payment",
                "cpt code",
                "provider",
                "itemized charges",
                "adjustment",
                "balance",
                "due date"
            ],
            "insurance_claim": [
                "claim number",
                "policy number",
                "coverage",
                "insured",
                "benefits",
                "authorization",
                "provider",
                "diagnosis code",
                "icd code",
                "subscriber",
                "group number",
                "pre-authorization"
            ],
            "medical_imaging": [
                "radiology",
                "imaging",
                "scan",
                "x-ray",
                "mri",
                "ct scan",
                "ultrasound",
                "impression",
                "technique",
                "contrast",
                "findings",
                "comparison"
            ],
            "discharge_summary": [
                "discharge date",
                "admission date",
                "hospital course",
                "follow up",
                "discharge diagnosis",
                "medications",
                "condition",
                "disposition",
                "follow-up care",
                "discharge instructions",
                "admission diagnosis",
                "hospital stay"
            ],
            "vaccination_record": [
                "vaccine",
                "immunization",
                "dose",
                "vaccination date",
                "lot number",
                "administered",
                "next due date",
                "manufacturer",
                "injection site",
                "vaccine type",
                "immunity",
                "booster"
            ]
        }

    def custom_rules(self, text: str, metadata: dict) -> Optional[str]:
        """Apply healthcare document specific rules."""
        text = text.lower()
        
        if self._contains_phi(text):
            if self._contains_lab_patterns(text):
                return "lab_report"
            if self._contains_prescription_patterns(text):
                return "prescription"
            if self._contains_imaging_patterns(text):
                return "medical_imaging"

        if self._contains_discharge_patterns(text):
            return "discharge_summary"
        if self._contains_vaccination_patterns(text):
            return "vaccination_record"
        if self._contains_billing_patterns(text):
            return "medical_bill"

        if metadata.get('tables'):
            if self._is_lab_results_table(metadata['tables']):
                return "lab_report"
            if self._is_vital_signs_table(metadata['tables']):
                return "medical_record"
            if self._is_billing_table(metadata['tables']):
                return "medical_bill"

        return None

    def _contains_phi(self, text: str) -> bool:
        phi_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b(MRN|Medical Record Number):\s*\d+\b',  # Medical Record Number
            r'\bDOB:\s*\d{1,2}/\d{1,2}/\d{2,4}\b',  # Date of Birth
            r'\b(patient|name):\s*[A-Za-z\s,]+\b',  # Patient Name
            r'\b(address|phone|email):\s*.+\b'  # Contact Information
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in phi_patterns)

    def _contains_lab_patterns(self, text: str) -> bool:
        lab_patterns = [
            r'(test|lab)\s+results?',
            r'reference\s+range',
            r'specimen\s+(collected|type)',
            r'normal\s+range',
            r'\b(high|low)\b.*\b(value|result)\b',
            r'laboratory\s+report',
            r'collection\s+date',
            r'test\s+performed'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in lab_patterns)

    def _contains_prescription_patterns(self, text: str) -> bool:
        rx_patterns = [
            r'\brx\b',
            r'take\s+\d+\s+(tablet|capsule)',
            r'refills?:\s*\d+',
            r'sig:',
            r'dispense:\s*\d+',
            r'prescribed\s+by',
            r'pharmacy',
            r'medication\s+order'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in rx_patterns)

    def _contains_imaging_patterns(self, text: str) -> bool:
        imaging_patterns = [
            r'(radiology|imaging)\s+report',
            r'(mri|ct|x-ray|ultrasound)\s+findings',
            r'impression:',
            r'technique:',
            r'contrast(\s+material)?:',
            r'comparison:',
            r'anatomic\s+region'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in imaging_patterns)

    def _contains_discharge_patterns(self, text: str) -> bool:
        discharge_patterns = [
            r'discharge\s+summary',
            r'admission\s+date',
            r'discharge\s+date',
            r'hospital\s+course',
            r'follow\s+up',
            r'discharge\s+medications',
            r'discharge\s+diagnosis',
            r'discharge\s+instructions'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in discharge_patterns)

    def _contains_vaccination_patterns(self, text: str) -> bool:
        vaccination_patterns = [
            r'vaccine\s+record',
            r'immunization\s+history',
            r'(vaccine|immunization)\s+administered',
            r'lot\s+number',
            r'next\s+dose\s+due',
            r'vaccination\s+site',
            r'dose\s+(\d+|series)'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in vaccination_patterns)

    def _contains_billing_patterns(self, text: str) -> bool:
        billing_patterns = [
            r'bill(ing)?\s+statement',
            r'amount\s+due',
            r'payment\s+due\s+date',
            r'insurance\s+claim',
            r'cpt\s+code',
            r'total\s+charges',
            r'patient\s+responsibility'
        ]
        return any(bool(re.search(pattern, text, re.I)) for pattern in billing_patterns)

    def _is_lab_results_table(self, tables: List[List[str]]) -> bool:
        lab_headers = {
            'test', 'result', 'value', 'range', 'units', 'reference',
            'normal', 'specimen', 'collection'
        }
        for table in tables:
            if not table:
                continue
            headers = {cell.lower() for cell in table[0]}
            if len(headers & lab_headers) >= 3:
                return True
        return False

    def _is_vital_signs_table(self, tables: List[List[str]]) -> bool:
        vital_headers = {
            'temperature', 'pulse', 'blood pressure', 'respiration',
            'height', 'weight', 'bmi', 'oxygen', 'pain'
        }
        for table in tables:
            if not table:
                continue
            headers = {cell.lower() for cell in table[0]}
            if len(headers & vital_headers) >= 3:
                return True
        return False

    def _is_billing_table(self, tables: List[List[str]]) -> bool:
        billing_headers = {
            'code', 'description', 'charge', 'amount', 'date',
            'service', 'payment', 'adjustment', 'balance'
        }
        for table in tables:
            if not table:
                continue
            headers = {cell.lower() for cell in table[0]}
            if len(headers & billing_headers) >= 3:
                return True
        return False
