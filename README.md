# DECISION PATH AUDITOR - AI Governance & Policy Evaluation Platform

---

## 1. Project Overview

Decision Path Auditor is an AI-powered compliance and governance platform designed to inspect, explain, and audit automated decisions. Instead of acting as a "black box" that only outputs a final approval or rejection, it evaluates candidate applications or bulk datasets against enterprise policy rules, redacts sensitive applicant data using zero-knowledge PII tokenization, and records every decision in an immutable historical ledger.

---

## 2. Problem Statement

Many automated decision systems in regulated industries (such as Banking, Education, Healthcare, and Government Welfare) approve or reject applications without providing a clear, verifiable reason. Furthermore, storing unencrypted applicant personal data (PII) creates severe data privacy and regulatory compliance risks.

Decision Path Auditor solves this by automating transparent policy auditing while protecting sensitive data through cryptographic tokenization.

---

## 3. Objective

- Provide an explainable, human-readable audit trail for every automated decision
- Evaluate applications against statutory, financial, and eligibility rules
- Protect applicant privacy using zero-knowledge PII tokenization
- Calculate dynamic compliance scores (%) and risk levels (LOW, MEDIUM, HIGH)
- Enable bulk compliance auditing across entire datasets (.csv, .xlsx, .json)
- Maintain an immutable, searchable historical audit ledger

---

## 4. Technologies Used

- **Frontend:** Streamlit (Glassmorphism Executive UI)
- **Programming Language:** Python 3.10+
- **Data Processing:** Pandas, NumPy, OpenPyXL (Excel `.xlsx` support)
- **Explainable AI:** Groq Llama-3.3-70B API (with automatic offline fallback)
- **Security & Cryptography:** SHA-256 Hashing, AES-256 Tokenization

---

## 5. Project Workflow

1. User selects a Governance Module from the sidebar (**Policy Evaluator**, **Universal Dataset Auditor**, or **Audit Ledger**).
2. User submits application details, uploads a dataset file, or loads the 10-record enterprise sample dataset.
3. Sensitive applicant data (PAN, Aadhaar, SSN, income) is tokenized using cryptographic hashing.
4. The compliance engine evaluates each parameter against statutory and enterprise policy rules.
5. A dynamic **Compliance Score (%)** and **Risk Rating** are computed.
6. The AI reasoning engine generates clear, plain-English explanations and causal justifications.
7. Results are displayed on interactive executive dashboards and tables.
8. Evaluation records are permanently logged in the searchable audit ledger.
9. Users can download complete audited compliance reports as CSV files.

---

## 6. Folder Structure

```
Path_Auditor/
│
├── streamlit_app.py        # Core Streamlit SaaS Executive Dashboard & Evaluation Engine
├── run_streamlit.bat       # One-click Windows launcher script
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation (this file)
├── ARCHITECTURE.md         # System design & architecture diagrams
├── SEQUENCE_DIAGRAM.md     # Step-by-step causal reasoning sequence diagrams
├── ER_DIAGRAM.md           # 11-table database schema dictionary
├── API_DOCUMENTATION.md    # API endpoint specifications
├── DEPLOYMENT_GUIDE.md     # Cloud deployment instructions
└── .gitignore              # Git ignore rules for secrets and caches
```

---

## 7. Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   ```

2. **Navigate into the project folder:**
   ```bash
   cd Path_Auditor
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment (Windows):**
   ```bash
   venv\Scripts\activate
   ```

5. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 8. How to Run

### Option 1: One-Click Launch (Windows)
Double-click the startup batch script in the project root:
```bash
run_streamlit.bat
```

### Option 2: Run via Terminal
Run the Streamlit application directly from your terminal:
```bash
streamlit run streamlit_app.py --server.port 8501
```
Then open your browser and navigate to **`http://localhost:8501`**.

---

## 9. How to Use

1. **Select a Mode in the Sidebar:**
   - **Policy Evaluator:** Test individual applications (e.g., Education Scholarship, Government Scheme, or Refund Request).
   - **Universal Dataset Auditor (Bulk Data):** Choose between:
     - **1. Sample Bulk Dataset (10 Records):** Test instantly with 10 pre-configured enterprise records.
     - **2. Upload Dataset File:** Upload any custom `.csv`, `.xlsx`, or `.json` file.
     - **3. Paste Raw CSV / JSON Data:** Paste raw data directly into the text box.
   - **Audit Ledger:** View, search, and filter historical audit records by ID or risk level.
2. **Run Evaluation:** Click **`Evaluate Policy Compliance`** (for single applications) or **`Run Universal Compliance Audit on All Records`** (for bulk data).
3. **Inspect & Download:** Review the compliance score, risk rating, and causal justification, then click **`Download Full Audited Report (CSV)`** to export.

---

## 10. Sample Input

### Single Application Example:
- **Applicant Name:** Ananya Sharma
- **Age:** 19
- **CGPA / Grade Score:** 9.4
- **Family Annual Income:** ₹2,10,000
- **Days Since Application:** 3

### Bulk Dataset Example (.csv):
```csv
Applicant Name,Age,Course,Score_CGPA,Income,Days_Pending
Ananya Sharma,19,B.Tech AI,9.4,210000,3
Rohan Gupta,21,B.Com Honors,5.2,450000,12
Suresh Kumar,42,Agriculture,8.1,175000,15
```

---

## 11. Sample Output

### Single Application Result:
- **Compliance Score:** `98.4%`
- **Risk Level:** `LOW`
- **Audit Decision:** `APPROVED`
- **Justification:** `All statutory and enterprise rules satisfied. Applicant demonstrates a CGPA of 9.4 and Family Annual Income of ₹2,10,000, fully qualifying for scholarship support.`

### Bulk Dataset Result:
- **Total Audited:** `10 Records`
- **Approved (%):** `70.0%`
- **Review / Rejected (%):** `30.0%`
- **Average Compliance Score:** `82.6%`
- **Export Option:** One-click CSV download of audited records.

---

## 12. Future Enhancements

- **Multi-Agent Collaborative Auditing:** Specialized AI sub-agents for financial, legal, and fraud verification.
- **Automated Regulatory OCR Parsing:** Direct ingestion of PDF compliance guidelines.
- **Custom Policy Rule Builder UI:** Visual drag-and-drop rule creator for non-technical compliance officers.
- **Enterprise RBAC & SSO:** Integration with OAuth2 / Active Directory.

---

## 13. Conclusion

Decision Path Auditor successfully bridges the gap between automated AI efficiency and regulatory compliance. By combining zero-knowledge PII tokenization, dynamic compliance scoring, and human-readable causal reasoning, it ensures that every automated decision is transparent, fair, and mathematically verifiable.

---

## 14. Author

**Surya**  
*Final Year B.Tech – Artificial Intelligence and Data Science*
