import os
import shutil
import sqlite3
import json

from google import genai

from .github_integration import file_github_issue

SANDBOX_DB = "database/sandbox/sandbox_database.db"


def restore_backup(backup_path):
    """Restores a backup to a sandbox environment."""
    os.makedirs(os.path.dirname(SANDBOX_DB), exist_ok=True)
    if os.path.exists(SANDBOX_DB):
        os.remove(SANDBOX_DB)
    shutil.copy2(backup_path, SANDBOX_DB)
    print(f"Restored {backup_path} to sandbox.")


def run_validation_queries():
    """Runs validation queries against the sandbox DB and returns the results."""
    results = {"status": "PASS", "details": [], "errors": []}

    if not os.path.exists(SANDBOX_DB):
        results["status"] = "FAIL"
        results["errors"].append("Sandbox database file is missing after restoration.")
        return results

    conn = None
    try:
        conn = sqlite3.connect(SANDBOX_DB)
        cursor = conn.cursor()

        # Query 1: Check users count
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        results["details"].append(f"Users table count: {users_count}")
        if users_count == 0:
            results["status"] = "FAIL"
            results["errors"].append("Users table is empty.")

        # Query 2: Check transactions count
        cursor.execute("SELECT COUNT(*) FROM transactions")
        txn_count = cursor.fetchone()[0]
        results["details"].append(f"Transactions table count: {txn_count}")
        if txn_count == 0:
            results["status"] = "FAIL"
            results["errors"].append("Transactions table is empty.")

        # Query 3: Check data integrity (amount sum)
        cursor.execute("SELECT SUM(amount) FROM transactions")
        total_amount = cursor.fetchone()[0]
        results["details"].append(f"Total transactions sum: {total_amount}")
        if total_amount is None:
            results["status"] = "FAIL"
            results["errors"].append("Total transactions sum is NULL.")

    except sqlite3.OperationalError as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Database error: {str(e)}")
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Unexpected error: {str(e)}")
    finally:
        if conn is not None:
            conn.close()

    return results


def generate_report(backup_filename, validation_results):
    """Uses Gemini API to generate a narrative report of the verification."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Gemini API key not configured. Mock report: Validation completed."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert database administrator AI. A nightly database backup has been restored into a sandbox and validated.
Here are the details:
Backup File: {backup_filename}
Validation Status: {validation_results["status"]}

Validation Details:
{chr(10).join(validation_results["details"])}

Validation Errors (if any):
{chr(10).join(validation_results["errors"]) if validation_results["errors"] else "None"}

Please write a brief, professional narrative report explaining whether the backup is healthy and restorable. If it failed, highlight the issues found. Do not include markdown headers like `#` or `**` heavily, just standard text.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Failed to generate report via Gemini: {str(e)}"


def verify_backup(backup_path):
    """End-to-end verification process for a given backup."""
    backup_filename = os.path.basename(backup_path)

    # 1. Restore
    restore_backup(backup_path)

    # 2. Validate
    results = run_validation_queries()

    # 3. Narrate with LLM
    report = generate_report(backup_filename, results)

    issue_url = None
    # 4. File issue if failed
    if results["status"] == "FAIL":
        issue_title = f"Backup Verification Failed: {backup_filename}"
        issue_url = file_github_issue(issue_title, report)

    return {
        "status": results["status"],
        "details": results["details"],
        "errors": results["errors"],
        "report": report,
        "issue_url": issue_url,
    }


def run_ai_dynamic_validation(sandbox_db_path):
    """Dynamically generates and executes SQL queries using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
         return {"error": "API Key missing or invalid"}
         
    conn = None
    try:
        conn = sqlite3.connect(sandbox_db_path)
        cursor = conn.cursor()
        
        # Extract schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schemas = [row[0] for row in cursor.fetchall() if row[0]]
        schema_text = "\n".join(schemas)
        
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are a Database Administrator AI. Analyze the following SQLite schema:
        {schema_text}
        
        Write exactly 2 SQL queries that check for data anomalies (e.g. negative amounts, orphaned records, or anything relevant).
        Return ONLY valid JSON in this exact format, with no markdown formatting or backticks:
        [
          {{"description": "Check for negative amounts", "query": "SELECT * FROM transactions WHERE amount < 0"}}
        ]
        """
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        
        # Parse JSON
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        queries = json.loads(raw_text.strip())
        
        results = []
        for q in queries:
            try:
                cursor.execute(q["query"])
                rows = cursor.fetchall()
                results.append({
                    "description": q["description"], 
                    "query": q["query"], 
                    "rows_found": len(rows), 
                    "passed": len(rows) == 0,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "description": q["description"], 
                    "query": q["query"], 
                    "rows_found": 0, 
                    "passed": False,
                    "error": str(e)
                })
                
        return {"status": "SUCCESS", "results": results}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
    finally:
        if conn:
            conn.close()
