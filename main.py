import glob
import os

import streamlit as st
from dotenv import load_dotenv

from app.mock_backup import create_backup, cleanup_old_backups
from app.verifier import verify_backup, run_ai_dynamic_validation, restore_backup, SANDBOX_DB
from app.pdf_generator import generate_pdf

load_dotenv()

st.set_page_config(
    page_title="Backup Verification Simulator", layout="wide"
)

# Initialize Session State
if "standard_results" not in st.session_state:
    st.session_state.standard_results = None
if "ai_results" not in st.session_state:
    st.session_state.ai_results = None

st.title("Backup Verification Simulator")
st.markdown("Automated nightly backup verification using Gemini and GitHub Issues.")
st.markdown("---")

# Sidebar for controls
with st.sidebar:
    st.header("System Controls")
    
    st.subheader("Data Generation")
    if st.button("Generate New Backup", use_container_width=True):
        with st.spinner("Generating backup..."):
            create_backup()
        st.success("Backup created successfully.")
        
    st.subheader("Storage Maintenance")
    if st.button("Clean Old Backups", use_container_width=True):
        with st.spinner("Cleaning old backups (keeping 7)..."):
            cleanup_old_backups(keep=7)
        st.success("Storage cleanup complete.")

# Dashboard Metrics
st.header("Dashboard")
col1, col2, col3 = st.columns(3)
backup_dir = "database/backup"
source_db = "database/main.db"

backups = []
if os.path.exists(backup_dir):
    backups = sorted(glob.glob(os.path.join(backup_dir, "*.db")), reverse=True)

col1.metric("Total Backups", len(backups))

if os.path.exists(source_db):
    source_size = os.path.getsize(source_db) / (1024 * 1024)
    col2.metric("Source DB Size", f"{source_size:.2f} MB")
else:
    col2.metric("Source DB Size", "0 MB")

if backups:
    latest_size = os.path.getsize(backups[0]) / (1024 * 1024)
    col3.metric("Latest Backup Size", f"{latest_size:.2f} MB")
else:
    col3.metric("Latest Backup Size", "0 MB")

st.markdown("---")
st.header("Available Backups")

if not backups:
    st.info("No backups found. Generate one from the sidebar.")
else:
    selected_backup = st.selectbox("Select a backup to verify", backups)

    colA, colB = st.columns(2)
    with colA:
        verify_clicked = st.button("Static Validation", use_container_width=True)
    with colB:
        ai_clicked = st.button("Dynamic Validation", use_container_width=True)

    if verify_clicked:
        with st.spinner("Restoring, validating, and generating report..."):
            st.session_state.standard_results = verify_backup(selected_backup)
            st.session_state.ai_results = None

    if ai_clicked:
        with st.spinner("Restoring backup and querying AI for SQL anomaly tests..."):
            restore_backup(selected_backup)
            st.session_state.ai_results = run_ai_dynamic_validation(SANDBOX_DB)
            st.session_state.standard_results = None

    # Render Results
    if st.session_state.standard_results:
        results = st.session_state.standard_results
        st.subheader("Verification Results")

        # Status badge
        if results["status"] == "PASS":
            st.success("STATUS: PASS")
        else:
            st.error("STATUS: FAIL")

        # Details and Errors in expanders
        with st.expander("Validation Details", expanded=True):
            for detail in results["details"]:
                st.write(detail)

            if results["errors"]:
                st.markdown("### Errors Found:")
                for error in results["errors"]:
                    st.write(error)

        st.subheader("AI Narrative Report")
        st.info(results["report"])

        if results["issue_url"]:
            st.warning(f"GitHub Issue Filed: [View Issue]({results['issue_url']})")

        # Generate and provide PDF download
        pdf_content = f"Status: {results['status']}\n\n"
        pdf_content += f"Details:\n" + "\n".join([f"[+] {d}" for d in results["details"]]) + "\n\n"
        if results["errors"]:
            pdf_content += f"Errors:\n" + "\n".join([f"[-] {e}" for e in results["errors"]]) + "\n\n"
        pdf_content += f"AI Narrative Report:\n{results['report']}"
        
        pdf_bytes = generate_pdf(f"Verification Report: {os.path.basename(selected_backup)}", pdf_content)
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"verification_{os.path.basename(selected_backup)}.pdf",
            mime="application/pdf"
        )

    elif st.session_state.ai_results:
        ai_results = st.session_state.ai_results
        st.subheader("AI Dynamic Validation Results")
        if ai_results.get("status") == "ERROR" or "error" in ai_results:
            st.error(f"Error: {ai_results.get('error')}")
        else:
            validation_results = ai_results.get("results", [])
            if isinstance(validation_results, list):
                for res in validation_results:
                    if isinstance(res, dict):
                        st.markdown(f"**Test**: {res.get('description')}")
                        st.code(res.get('query', ''), language="sql")
                        if res.get('passed'):
                            st.success("No anomalies found.")
                        else:
                            if res.get('error'):
                                st.error(f"Error Executing Query: {res.get('error')}")
                            else:
                                st.error(f"Failed: Found {res.get('rows_found')} anomalous rows!")
                        st.markdown("---")
            
            st.subheader("AI Narrative Report")
            ai_report = ai_results.get("report", "No report generated.")
            st.info(ai_report)

            issue_url = ai_results.get("issue_url")
            if isinstance(issue_url, str):
                st.warning(f"GitHub Issue Filed for Anomalies: [View Issue]({issue_url})")
                
            pdf_content = "AI Dynamic Validation Report\n\n"
            if isinstance(validation_results, list):
                for res in validation_results:
                    if isinstance(res, dict):
                        pdf_content += f"Test: {res.get('description')}\n"
                        pdf_content += f"Query:\n{res.get('query', '')}\n"
                        if res.get('passed'):
                            pdf_content += "Status: PASS\n"
                        else:
                            pdf_content += f"Status: FAIL (Found {res.get('rows_found')} rows)\n"
                            if res.get('error'):
                                pdf_content += f"Error: {res.get('error')}\n"
                        pdf_content += "\n"
            pdf_content += f"AI Narrative Report:\n{ai_report}"

            pdf_bytes = generate_pdf(f"AI Dynamic Validation: {os.path.basename(selected_backup)}", pdf_content)
            st.download_button(
                label="Download AI Validation PDF",
                data=pdf_bytes,
                file_name=f"ai_validation_{os.path.basename(selected_backup)}.pdf",
                mime="application/pdf"
            )
