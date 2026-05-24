import os
import shutil
import asyncio
import sentinel_config
import sentinel_db
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def run_tests():
    print("=========================================")
    print("   PROACTIVE SYSTEM SENTINEL VERIFIER   ")
    print("=========================================")
    
    # 1. Test Configuration Loading
    print("\n[+] Testing configuration loading...")
    config = sentinel_config.load_config()
    print(f"    Sandbox Directory: {config.sandbox_dir}")
    print(f"    Audit Interval: {config.audit_interval}s")
    
    # Ensure sandbox directory exists
    os.makedirs(config.sandbox_dir, exist_ok=True)
    
    # 2. Test SQLite Database Initialization
    print("\n[+] Testing SQLite Database initialization...")
    sentinel_db.init_db()
    print("    SQLite DB initialized successfully.")
    
    # 3. Create dummy test files in the sandbox directory
    print("\n[+] Generating dummy test files in sandbox...")
    
    # File 1: Python Code
    code_path = os.path.join(config.sandbox_dir, "bubble_sort.py")
    with open(code_path, "w") as f:
        f.write("""
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
""")
    print(f"    Created Code file: {code_path}")
        
    # File 2: Simple Document
    doc_path = os.path.join(config.sandbox_dir, "meeting_notes.txt")
    with open(doc_path, "w") as f:
        f.write("""
Meeting Minutes - May 24, 2026
Attendees: Alice, Bob, Charlie
Agenda: Discuss the Q2 architectural roadmap and the integration of our Google Antigravity SDK components.
We agreed to use SQLite for lightweight local storage and rich for our console layouts.
""")
    print(f"    Created Document file: {doc_path}")

    # File 3: Invoice
    invoice_path = os.path.join(config.sandbox_dir, "invoice_48291.txt")
    with open(invoice_path, "w") as f:
        f.write("""
INVOICE - GLOBAL TECH SERVICES
Invoice Number: #48291
Date: 2026-05-24
Bill To: Sadeep (Proactive Sentinel Project)
Items:
1. Python SDK Orchestration Consulting - $1,200.00
2. CLI Layout Design Workshop - $450.00
Total Due: $1,650.00
Payment due in 15 days.
""")
    print(f"    Created Invoice file: {invoice_path}")

    # 4. Trigger Sandbox Scan (requires Gemini API)
    print("\n[+] Triggering Smart Workspace Organizer Scan...")
    try:
        import sentinel_agent
        count = await sentinel_agent.trigger_manual_scan()
        print(f"    Organized {count} files successfully!")
    except Exception as e:
        print(f"    [!] Error during manual scan (is GEMINI_API_KEY valid?): {e}")

    # 5. Check SQLite Database logs
    print("\n[+] Retrieving File Organization History from SQLite...")
    ops = sentinel_db.get_file_ops(limit=5)
    for op in ops:
        print(f"    - File: {op['file_name']} -> {op['category']} | Status: {op['status']}")
        print(f"      AI Reasoning: {op['reasoning']}")

    print("\n=========================================")
    print("        VERIFICATION COMPLETE            ")
    print("=========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
