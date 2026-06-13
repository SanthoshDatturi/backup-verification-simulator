# Backup Verification Simulator

Backups run nightly, but nobody checks if they are restorable. This project aims to change that.
The **Backup Verification Simulator** provides an automated system to verify SQLite database backups, using AI to narrate the results and automatically filing GitHub issues upon failure.

## Features

- **Mock Backup Generation**: Simulates nightly backups of a primary SQLite database, occasionally introducing simulated corruption.
- **Sandbox Restoration**: Restores a selected backup to a secure sandbox environment for validation.
- **Validation Queries**: Runs basic health checks (row counts, data integrity) to ensure the backup is intact.
- **AI Narrative (Gemini)**: Utilizes the Google Gemini AI API to generate a readable summary of the backup's health.
- **Automated Alerts (GitHub)**: Automatically files a GitHub issue in the specified repository if a backup fails validation.
- **Streamlit Interface**: Provides a clean UI to manage backups and trigger verifications.

## Prerequisites

- Python 3.12+
- A Google Gemini API Key
- A GitHub Personal Access Token

## Setup Instructions

1. **Clone the repository** (if not already done)

   ```bash
   git clone <repo-url>
   cd "Backup Verification Simulator"
   ```

2. **Set up Virtual Environment**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory and add your credentials:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GITHUB_TOKEN=your_github_token_here
   GITHUB_REPO=your_username/your_repo_name_here
   ```

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run main.py
   ```
2. Open your browser and navigate to the local URL provided by Streamlit.
3. Use the sidebar to **Generate New Backup**. Some backups will randomly be corrupted to demonstrate the failure process.
4. Select a backup from the dropdown and click **Verify Backup**.
5. View the AI-generated report and check GitHub if a failure occurred.

## Architecture

- `mock_backup.py`: Handles source DB creation and generates mock backups.
- `verifier.py`: The core agent that restores the sandbox DB, runs validation queries, and calls the Gemini API.
- `github_integration.py`: Handles interaction with the GitHub API.
- `main.py`: Streamlit frontend.
