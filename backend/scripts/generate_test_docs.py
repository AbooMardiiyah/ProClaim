"""
ProClaim - Mock Document Generator for Testing

Generates fake Nigerian hospital documents (PDFs) for a SINGLE patient encounter.
All documents share the same patient name, NHIA ID, hospital, date, and physician,
but each represents a different part of the encounter (outpatient register, lab,
pharmacy, billing, comprehensive summary).

Usage:
    cd proclaim/backend
    pip install fpdf2
    python scripts/generate_test_docs.py

Output: /tmp/proclaim/test_docs/  (5 sample PDFs)
"""
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from fpdf import FPDF, XPos, YPos

OUTPUT_DIR = Path("/tmp/proclaim/test_docs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Nigerian mock data ────────────────────────────────────────────────────────
FIRST_NAMES = ["Chinedu", "Amina", "Olumide", "Fatima", "Emeka", "Ngozi", "Abdul", "Yemi", "Chioma", "Ibrahim"]
LAST_NAMES = ["Okafor", "Bello", "Adeyemi", "Mohammed", "Eze", "Obi", "Yusuf", "Adeleke", "Nwosu", "Suleiman"]
HOSPITALS = ["Lagos General Hospital", "Ikeja Medical Centre", "Abuja City Hospital", "UCH Ibadan", "LUTH Idi-Araba"]
DIAGNOSES = [
    "Uncomplicated malaria",
    "Typhoid fever",
    "Upper respiratory tract infection",
    "Hypertension",
    "Type 2 diabetes mellitus",
    "Peptic ulcer disease",
    "Urinary tract infection",
    "Acute gastroenteritis",
]
PHYSICIANS = ["Dr. O. Akinwale", "Dr. N. Mohammed", "Dr. C. Okonkwo", "Dr. F. Adebayo", "Dr. J. Ibrahim"]
PROCEDURES = [
    "Outpatient consultation",
    "Malaria rapid diagnostic test",
    "Full blood count",
    "Urinalysis",
    "Chest x-ray",
    "HIV test",
    "Liver function test",
    "Wound dressing",
]


def random_date() -> str:
    d = datetime.now() - timedelta(days=random.randint(0, 60))
    return d.strftime("%d/%m/%Y")


def random_nhia_id() -> str:
    return f"NH{random.randint(100000, 999999)}"


@dataclass
class PatientEncounter:
    """Shared data for one patient's hospital visit across all documents."""

    first_name: str
    last_name: str
    hospital: str
    diagnosis: str
    physician: str
    procedure: str
    nhia_id: str
    date_of_service: str
    physician_id: str
    consultation_fee: int
    lab_fee: int
    drug_fee: int
    total_cost: int

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


def create_encounter(seed: int = 42) -> PatientEncounter:
    """
    Create a patient encounter. Pass a different seed to get a different patient
    while keeping all runs with the same seed identical.

    Example:
        create_encounter()        # default patient (seed=42)
        create_encounter(seed=7)  # different patient
    """
    rng = random.Random(seed)
    cons = rng.randint(15, 50) * 100
    lab = rng.randint(10, 30) * 100
    drug = rng.randint(10, 40) * 100
    return PatientEncounter(
        first_name=rng.choice(FIRST_NAMES),
        last_name=rng.choice(LAST_NAMES),
        hospital=rng.choice(HOSPITALS),
        diagnosis=rng.choice(DIAGNOSES),
        physician=rng.choice(PHYSICIANS),
        procedure=rng.choice(PROCEDURES),
        nhia_id=f"NH{rng.randint(100000, 999999)}",
        date_of_service=(datetime.now() - timedelta(days=rng.randint(0, 60))).strftime("%d/%m/%Y"),
        physician_id=f"MD{rng.randint(1000, 9999)}",
        consultation_fee=cons,
        lab_fee=lab,
        drug_fee=drug,
        total_cost=cons + lab + drug,
    )


DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


class MockDoc(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", DEJAVU_PATH)
        self.add_font("DejaVu", "B", DEJAVU_PATH.replace("Sans.ttf", "Sans-Bold.ttf"))

    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.cell(0, 10, self.hospital_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("DejaVu", "", 9)
        self.cell(0, 5, "Patient Encounter Document - NHIA Aligned", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)


def _row(pdf: FPDF, label: str, value: str) -> None:
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(60, 8, f"{label}:")
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def generate_outpatient_register(enc: PatientEncounter) -> Path:
    pdf = MockDoc()
    pdf.hospital_name = enc.hospital
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "OUTPATIENT REGISTER", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 11)

    data = [
        ("Patient Name", enc.full_name),
        ("NHIA ID", enc.nhia_id),
        ("Date of Service", enc.date_of_service),
        ("Hospital Name", enc.hospital),
        ("Primary Diagnosis", enc.diagnosis),
        ("ICD-10 Code", "-"),
        ("Procedure", enc.procedure),
        ("NHIA Tariff Code", "-"),
        ("Physician Name", enc.physician),
        ("Physician ID", enc.physician_id),
        ("Consultation Fee", f"₦{enc.consultation_fee:,}"),
        ("Drug Cost", "₦0"),
        ("Lab Cost", "₦0"),
        ("Total Cost", f"₦{enc.consultation_fee:,}"),
    ]
    for label, value in data:
        _row(pdf, label, value)

    pdf.ln(10)
    pdf.set_font("DejaVu", "", 9)
    pdf.cell(0, 5, "Signed by attending physician", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, f"Ref: PC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    path = OUTPUT_DIR / "outpatient_register.pdf"
    pdf.output(str(path))
    return path


def generate_lab_report(enc: PatientEncounter) -> Path:
    pdf = MockDoc()
    pdf.hospital_name = enc.hospital
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "LABORATORY REPORT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 11)

    info = [
        ("Patient Name", enc.full_name),
        ("NHIA ID", enc.nhia_id),
        ("Date of Service", enc.date_of_service),
        ("Hospital Name", enc.hospital),
        ("Test", "Full Blood Count (FBC)"),
        ("Haemoglobin", f"{random.randint(11, 16)}.g/dL"),
        ("PCV", f"{random.randint(35, 48)}%"),
        ("WBC", f"{random.randint(4000, 11000)} /mm³"),
        ("Total Cost", f"₦{enc.lab_fee:,}"),
    ]
    for label, value in info:
        _row(pdf, label, value)

    path = OUTPUT_DIR / "lab_report.pdf"
    pdf.output(str(path))
    return path


def generate_pharmacy_log(enc: PatientEncounter) -> Path:
    drugs = random.sample([
        ("Artemether/Lumefantrine", 1200),
        ("Amoxicillin Capsules", 800),
        ("Paracetamol", 300),
        ("Metronidazole", 600),
        ("Omeprazole", 450),
    ], k=random.randint(2, 4))

    pdf = MockDoc()
    pdf.hospital_name = enc.hospital
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "PHARMACY DISPENSARY LOG", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 11)

    info = [
        ("Patient Name", enc.full_name),
        ("NHIA ID", enc.nhia_id),
        ("Date of Service", enc.date_of_service),
        ("Hospital Name", enc.hospital),
    ]
    for label, value in info:
        _row(pdf, label, value)

    pdf.ln(5)
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(80, 8, "Drug")
    pdf.cell(40, 8, "Price")
    pdf.ln(8)
    pdf.set_font("DejaVu", "", 11)
    drug_total = 0
    for drug, price in drugs:
        pdf.cell(80, 8, drug)
        pdf.cell(40, 8, f"₦{price:,}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        drug_total += price

    pdf.ln(5)
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(80, 8, "Total Drug Cost:")
    pdf.cell(40, 8, f"₦{drug_total:,}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    path = OUTPUT_DIR / "pharmacy_log.pdf"
    pdf.output(str(path))
    return path


def generate_billing_receipt(enc: PatientEncounter) -> Path:
    pdf = MockDoc()
    pdf.hospital_name = enc.hospital
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "BILLING RECEIPT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 11)

    info = [
        ("Patient Name", enc.full_name),
        ("NHIA ID", enc.nhia_id),
        ("Date of Service", enc.date_of_service),
        ("Hospital Name", enc.hospital),
        ("Consultation Fee", f"₦{enc.consultation_fee:,}"),
        ("Drug Cost", f"₦{enc.drug_fee:,}"),
        ("Lab Cost", f"₦{enc.lab_fee:,}"),
        ("Total Cost", f"₦{enc.total_cost:,}"),
    ]
    for label, value in info:
        _row(pdf, label, value)

    pdf.ln(10)
    pdf.set_font("DejaVu", "", 9)
    pdf.cell(0, 5, "Payment received. Thank you.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    path = OUTPUT_DIR / "billing_receipt.pdf"
    pdf.output(str(path))
    return path


def generate_comprehensive_claim(enc: PatientEncounter) -> Path:
    """A single multi-section document combining all info."""
    pdf = MockDoc()
    pdf.hospital_name = enc.hospital
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "NHIA PATIENT ENCOUNTER SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(5)
    pdf.set_font("DejaVu", "", 11)

    sections = [
        ("Patient Information", [
            ("Patient Name", enc.full_name),
            ("NHIA ID", enc.nhia_id),
            ("Date of Service", enc.date_of_service),
            ("Hospital Name", enc.hospital),
        ]),
        ("Clinical Information", [
            ("Primary Diagnosis", enc.diagnosis),
            ("ICD-10 Code", "-"),
            ("Procedure", enc.procedure),
            ("NHIA Tariff Code", "-"),
            ("Physician Name", enc.physician),
            ("Physician ID", enc.physician_id),
        ]),
        ("Financial Summary", [
            ("Consultation Fee", f"₦{enc.consultation_fee:,}"),
            ("Drug Cost", f"₦{enc.drug_fee:,}"),
            ("Lab Cost", f"₦{enc.lab_fee:,}"),
            ("Total Cost", f"₦{enc.total_cost:,}"),
        ]),
    ]

    for title, rows in sections:
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("DejaVu", "", 11)
        for label, value in rows:
            _row(pdf, label, value)
        pdf.ln(3)

    path = OUTPUT_DIR / "comprehensive_claim.pdf"
    pdf.output(str(path))
    return path


if __name__ == "__main__":
    encounter = create_encounter()
    docs = [
        generate_outpatient_register(encounter),
        generate_lab_report(encounter),
        generate_pharmacy_log(encounter),
        generate_billing_receipt(encounter),
        generate_comprehensive_claim(encounter),
    ]
    print(f"Generated {len(docs)} test documents for {encounter.full_name} in {OUTPUT_DIR}:")
    for d in docs:
        print("  -", d.name)
