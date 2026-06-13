import glob
import os

import streamlit as st
from dotenv import load_dotenv

from app.mock_backup import create_backup, cleanup_old_backups
from app.verifier import verify_backup, run_ai_dynamic_validation, restore_backup, SANDBOX_DB

load_dotenv()

st.set_page_config(
    page_title="Backup Verification Simulator", page_icon="🛡️", layout="wide"
)

st.title("🛡️ Backup Verification Simulator")
st.markdown("Automated nightly backup verification using Gemini and GitHub Issues.")

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    if st.button("Generate New Backup"):
        with st.spinner("Generating backup..."):
            create_backup()
        st.success("Backup created (check logs for corruption status).")
        
    st.markdown("---")
    if st.button("🧹 Clean Old Backups"):
        with st.spinner("Cleaning old backups (keeping 7)..."):
            cleanup_old_backups(keep=7)
        st.success("Storage cleanup complete.")

# Dashboard Metrics
st.header("📊 Dashboard")
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
        verify_clicked = st.button("🔍 Verify Backup (Standard)")
    with colB:
        ai_clicked = st.button("🧠 AI Dynamic Validation")

    if verify_clicked:
        with st.spinner("Restoring, validating, and generating report..."):
            results = verify_backup(selected_backup)

        st.subheader("Verification Results")

        # Status badge
        if results["status"] == "PASS":
            st.success("STATUS: PASS")
        else:
            st.error("STATUS: FAIL")

        # Details and Errors in expanders
        with st.expander("Validation Details", expanded=True):
            for detail in results["details"]:
                st.write(f"✔️ {detail}")

            if results["errors"]:
                st.markdown("### Errors Found:")
                for error in results["errors"]:
                    st.write(f"❌ {error}")

        st.subheader("AI Narrative Report (Gemini)")
        st.info(results["report"])

        if results["issue_url"]:
            st.warning(
                f"A GitHub issue was filed: [View Issue]({results['issue_url']})"
            )

    if ai_clicked:
        with st.spinner("Restoring backup and querying AI for SQL anomaly tests..."):
            restore_backup(selected_backup)
            ai_results = run_ai_dynamic_validation(SANDBOX_DB)
            
        st.subheader("🧠 AI Dynamic Validation Results")
        if ai_results.get("status") == "ERROR":
            st.error(f"Error: {ai_results.get('error')}")
        else:
            for res in ai_results.get("results", []):
                st.markdown(f"**Test**: {res['description']}")
                st.code(res['query'], language="sql")
                if res['passed']:
                    st.success("✔️ PASS - No anomalies found.")
                else:
                    if res.get('error'):
                        st.error(f"❌ ERROR Executing Query: {res['error']}")
                    else:
                        st.error(f"❌ FAIL - Found {res['rows_found']} anomalous rows!")
                st.markdown("---")
