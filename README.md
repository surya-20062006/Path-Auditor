# DECISION PATH AUDITOR - AI Governance & Policy Evaluation Platform

---

## 1. Project Overview

Decision Path Auditor is a compliance and governance web application designed to evaluate and explain automated decisions. Instead of acting as a "black box" that only gives a final approval or rejection, it checks applicant details and datasets against defined policy rules, redacts sensitive personal data using cryptographic tokenization, and logs every evaluation in a searchable audit ledger.

---

## 2. Problem Statement

Many automated systems used in banking, scholarships, healthcare, and government schemes approve or reject applications without giving applicants or auditors a clear explanation. In addition, storing plain-text sensitive personal information (PII) creates data privacy risks and violates regulatory compliance standards.

Decision Path Auditor automates transparent policy checking while protecting sensitive data through cryptographic tokenization and generating clear reasons for every decision.

---

## 3. Objective

- Provide a transparent, human-readable audit trail for automated decisions
- Evaluate candidate applications against statutory, eligibility, and financial rules
- Protect applicant privacy using cryptographic PII tokenization
- Calculate dynamic compliance scores (%) and risk levels (LOW, MEDIUM, HIGH)
- Enable bulk compliance auditing across full datasets (.csv, .xlsx, .json)
- Maintain a searchable historical audit ledger for review and verification

---

## 4. Technologies Used

- **Frontend:** Streamlit (Modern Interactive Dashboard)
- **Programming Language:** Python 3.10+
- **Data Processing:** Pandas, NumPy, OpenPyXL (Excel `.xlsx` support)
- **Explainable AI:** Groq Llama-3.3-70B API (with automatic offline fallback)
- **Security & Cryptography:** SHA-256 Hashing, AES-256 Data Tokenization

---

## 5. Project Workflow

1. User selects a Governance Module from the sidebar (**Policy Evaluator**, **Universal Dataset Auditor**, or **Audit Ledger**).
2. User enters application details, uploads a dataset file, or loads the 10-record sample dataset.
3. Sensitive personal data (PAN, Aadhaar, SSN, income) is tokenized using cryptographic hashing.
4. The evaluation engine checks each parameter against domain policy rules.
5. A dynamic **Compliance Score (%)** and **Risk Rating** are calculated.
6. The reasoning engine generates plain-English explanations and justifications.
7. Results are displayed on interactive dashboards and tables.
8. Evaluation records are permanently saved in the searchable audit ledger.
9. Users can download complete audited compliance reports as CSV files.

---

## 6. Folder Structure

```
Path_Auditor/
│
├── streamlit_app.py        # Core Streamlit Web Dashboard & Evaluation Engine
├── run_streamlit.bat       # One-click Windows launcher script
├── requirements.txt        # Python project dependencies
├── README.md               # Project documentation (this file)
├── ARCHITECTURE.md         # System design & architecture diagrams
├── SEQUENCE_DIAGRAM.md     # Step-by-step evaluation sequence diagrams
├── ER_DIAGRAM.md           # Database schema documentation
├── API_DOCUMENTATION.md    # API endpoint specifications
├── DEPLOYMENT_GUIDE.md     # Deployment instructions
└── .gitignore              # Git rules for secrets and cache exclusions
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
   - **Policy Evaluator:** Test individual applications (Education Scholarship, Government Scheme, or Refund Request).
   - **Universal Dataset Auditor (Bulk Data):** Choose between:
     - **1. Sample Bulk Dataset (10 Records):** Test instantly with 10 sample enterprise records.
     - **2. Upload Dataset File:** Upload your custom `.csv`, `.xlsx`, or `.json` file.
     - **3. Paste Raw CSV / JSON Data:** Paste raw data directly into the text box.
   - **Audit Ledger:** View, search, and filter historical audit records by ID or risk level.
2. **Run Evaluation:** Click **`Evaluate Policy Compliance`** (for single applications) or **`Run Universal Compliance Audit on All Records`** (for bulk data).
3. **Inspect & Download:** Review the compliance score, risk rating, and justification, then click **`Download Full Audited Report (CSV)`** to export.

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

- **Multi-Agent Collaborative Auditing:** Specialized agents for financial, legal, and fraud verification.
- **Automated Regulatory OCR Parsing:** Direct ingestion of PDF compliance guidelines.
- **Custom Policy Rule Builder UI:** Visual rule creator for compliance officers.
- **Enterprise RBAC & SSO:** Integration with OAuth2 / Active Directory authentication.

---

## 13. Conclusion

Decision Path Auditor bridges the gap between automated efficiency and regulatory compliance. By combining cryptographic PII tokenization, dynamic compliance scoring, and human-readable causal reasoning, it ensures that every automated decision is transparent, fair, and verifiable.

---

## 14. Author

**Surya**  
*Final Year B.Tech – Artificial Intelligence and Data Science*
