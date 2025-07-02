# backfill_company_profiles.py
import os
import requests
import time
import psycopg2
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
BASE_URL = os.getenv('BASE_URL')
ADMIN_JWT = os.getenv('ADMIN_JWT')
DATABASE_URL = os.getenv('DATABASE_URL')
# Time to wait between API calls to avoid overwhelming the service
CALL_INTERVAL_SECONDS = 2

def get_unprofiled_company_ids():
    """Fetches company IDs that don't have a profile yet."""
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not found in .env file.")
        return []
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM companies
                WHERE id NOT IN (SELECT company_id FROM company_profiles)
                ORDER BY id;
            """)
            ids = [row[0] for row in cur.fetchall()]
            print(f"✅ Found {len(ids)} companies to process.")
            return ids
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database or fetch IDs: {e}")
        return []
    finally:
        if conn:
            conn.close()

def process_company(company_id):
    """Calls the admin endpoint to research a single company."""
    if not BASE_URL or not ADMIN_JWT:
        print("❌ ERROR: BASE_URL or ADMIN_JWT not found in .env file. Aborting.")
        return False

    url = f"{BASE_URL}/api/admin/research-company/{company_id}"
    headers = {
        "Authorization": f"Bearer {ADMIN_JWT}",
        "Content-Type": "application/json"
    }

    try:
        print(f"⚙️  Processing company ID: {company_id}...")
        response = requests.post(url, headers=headers, timeout=60) # 60-second timeout for AI call

        if response.status_code == 200:
            print(f"✅ SUCCESS: Company ID {company_id} processed successfully.")
            return True
        else:
            print(f"⚠️  WARN: Failed to process company ID {company_id}. Status: {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Network request failed for company ID {company_id}: {e}")
        return False

def main():
    """Main execution function."""
    company_ids = get_unprofiled_company_ids()
    
    if not company_ids:
        print("No companies to process or database connection failed. Exiting.")
        return

    total_companies = len(company_ids)
    success_count = 0
    failure_count = 0

    for i, company_id in enumerate(company_ids):
        print(f"\n--- Progress: {i+1}/{total_companies} ---")
        if process_company(company_id):
            success_count += 1
        else:
            failure_count += 1
        
        # Don't sleep after the very last call
        if i < total_companies - 1:
            print(f"🕒  Waiting for {CALL_INTERVAL_SECONDS} seconds...")
            time.sleep(CALL_INTERVAL_SECONDS)

    print("\n\n--- 📊 Backfill Complete ---")
    print(f"Total Companies Processed: {total_companies}")
    print(f"✅ Successes: {success_count}")
    print(f"❌ Failures: {failure_count}")
    print("--------------------------")

if __name__ == "__main__":
    main()