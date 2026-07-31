@echo off
cd /d "d:\PROJECT\Path_Auditor"
echo Starting Decision Path Auditor Streamlit Frontend...
python -m streamlit run streamlit_app.py --server.port 8501
