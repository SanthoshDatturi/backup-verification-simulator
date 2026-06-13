import glob
import os

import streamlit as st
from dotenv import load_dotenv

from app.mock_backup import create_backup
from app.verifier import verify_backup

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

st.header("Available Backups")
backup_dir = "database/backup"
if not os.path.exists(backup_dir):
    st.info("No backups found. Generate one from the sidebar.")
else:
    # List backups
    backups = sorted(glob.glob(os.path.join(backup_dir, "*.db")), reverse=True)

    if not backups:
        st.info("No backups found. Generate one from the sidebar.")
    else:
        selected_backup = st.selectbox("Select a backup to verify", backups)

        if st.button("Verify Backup"):
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
