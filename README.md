# Backup Verification Simulator

## Problem Statement

Automated verification of nightly database backups is crucial for enterprise data integrity. Often, database backups corrupt silently due to partial table drops, nullification of critical values, orphaned records, or duplicates—all of which standard file-size checks fail to catch. This project simulates an automated nightly backup process that uses Artificial Intelligence to dynamically test the structural and logical integrity of the database against a wide variety of anomalies before a catastrophic recovery is required.

## Features Implemented

- **Mock Backup Generator with Corruptions (`app/mock_backup.py`)**: Automatically generates SQLite databases with dummy `users` and `transactions` data. It features a built-in 60% probability of varied corruptions including: dropping tables, emptying rows, nullifying transaction amounts, and duplicating users based on randomized thresholds.
- **Static Validation (`app/verifier.py`)**: Runs hardcoded, traditional static assertions against the restored backup (e.g., verifying row counts > 0 and validating `SUM(amount)` integrity) to serve as a baseline verification step.
- **Dynamic Two-Pass AI Validation (`app/verifier.py`)**: First, it uses Gemini 2.5 Flash to read the database schema and autonomously author an executable suite of SQL anomaly checks. Second, it executes those queries and feeds the actual results back to the AI to generate a natural-language narrative health report.
- **Professional PDF Generation (`app/pdf_generator.py`)**: Generates enterprise-grade, stylized PDF verification reports natively using the `reportlab` Platypus engine. Includes syntax-highlighted code blocks, status badges, and strict header/footer templating.
- **Automated GitHub Integration (`app/github_integration.py`)**: Automatically files GitHub Issues alerting the engineering team if the backup validation fails or anomalies are detected.
- **Stateful Dashboard (`main.py`)**: A Streamlit dashboard that allows manual triggering of backups, validation runs, and seamless session-state retention so UI elements and PDF downloads work reliably.

## Architecture Overview

The application is built around a **Streamlit** dashboard that acts as the user interface and control center.

1. **Data Layer**: `sqlite3` manages the local mock database backups inside `database/backup` and isolates a safe sandbox environment `database/sandbox/sandbox_database.db` for executing tests.
2. **AI Engine Layer**: The `google-genai` SDK interfaces with Gemini 2.5 Flash, strictly enforcing JSON outputs via **Pydantic** models (`ValidationQueries`) to guarantee stable parsing of generated SQL.
3. **Reporting Layer**: `reportlab` handles PDF formatting and typography, while `PyGithub` interfaces with the GitHub REST API for automated issue management using the `GITHUB_TOKEN`.

## Tools and Technologies Used

- **Language**: Python 3.x
- **Frontend/UI**: Streamlit
- **Database**: SQLite3
- **AI/LLM API**: Google Gemini 2.5 Flash (`google-genai`)
- **Validation/Schema Engine**: Pydantic
- **PDF Generation**: ReportLab (Platypus Engine)
- **Version Control API**: PyGithub

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone [YOUR_REPO_LINK]
   cd backup-verification-simulator
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell/CMD):
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   Create a `.env` file in the root directory (you can use `.env.example` as a reference) and add the following keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GITHUB_TOKEN=your_github_personal_access_token_here
   GITHUB_REPO=yourusername/your-repo-name
   ```

## Run Instructions

Start the Streamlit application by running the following command in your terminal:

```bash
streamlit run main.py
```

This will start a local server and open the dashboard in your default web browser (typically at `http://localhost:8501`).

## Sample Input and Sample Output

- **Sample Input**: A generated SQLite backup database (`.db` file) containing `users` and `transactions` schemas. The backup is selected from the Streamlit UI dropdown.
- **Sample Output**:
  - **PDF Report**: A comprehensive ReportLab PDF displaying the exact SQL queries executed (e.g., `SELECT * FROM transactions WHERE amount < 0`), the rows found, and a professional AI-written narrative confirming the database health.
  - **GitHub Issue**: If anomalies (e.g. negative transactions) are detected during validation, an issue titled "AI Validation Failed: Data Anomalies Detected" is automatically created in the configured repository containing the exact query failures.

## AI Capability Demonstrated

This project demonstrates **Dynamic Code Generation, Structured Output Enforcement, and Context-Aware Analysis**.
Rather than hardcoding database checks, the Gemini AI is dynamically fed the raw `sqlite_master` schema and uses Pydantic structured schemas to autonomously output an executable list of targeted SQL queries. A second AI pass demonstrates context-aware narrative generation, taking the raw execution results (including SQL errors and anomalous row counts) and synthesizing them into a human-readable diagnosis of the database's health.

## Assumptions and Limitations

- **Assumptions**: The system assumes the source database schema is relatively stable and its `sqlite_master` representation fits within the token limits of the LLM. It also assumes the local environment has internet access to reach the Gemini and GitHub APIs.
- **Limitations**: Currently restricted to SQLite databases. Extremely large enterprise databases might take a long time to restore to the local sandbox environment. While the AI's dynamically generated SQL queries are executed in an isolated sandbox database, executing AI-generated SQL always carries theoretical injection risks if the LLM hallucinates destructive commands (though mitigated entirely by the sandboxed file copy architecture).
