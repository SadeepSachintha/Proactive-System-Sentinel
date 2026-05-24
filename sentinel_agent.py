import os
import shutil
import psutil
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.triggers import every, on_file_change, TriggerContext
from google.antigravity.types import Image, Document

import sentinel_config
import sentinel_db
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.gemini/antigravity/sentinel_agent.log")),
        logging.StreamHandler()
    ]
)

class FileCategory(BaseModel):
    category: str = Field(description="Strictly one of: Code, Documents, Images, Invoices, Archives, Miscellaneous")
    reasoning: str = Field(description="A 1-sentence reasoning for this categorization")

def get_dir_size_mb(path) -> float:
    """Computes total directory size in MB."""
    if not os.path.exists(path):
        return 0.0
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
    return total_size / (1024 * 1024)

# =============================================================================
# 1. Periodic System Audit Trigger
# =============================================================================
async def audit_system(ctx: TriggerContext):
    """Triggered periodically to monitor resources and log alerts."""
    config = sentinel_config.load_config()
    
    # 1. Fetch system metrics
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    sandbox_size = get_dir_size_mb(config.sandbox_dir)
    
    # 2. Check latest metric for growth rate
    latest = sentinel_db.get_latest_metrics()
    growth_mb = 0.0
    if latest:
        growth_mb = max(0.0, sandbox_size - latest["sandbox_size_mb"])
        
    # 3. Log current metrics to database
    sentinel_db.log_metrics(cpu, ram, disk, sandbox_size)
    logging.info(f"AUDIT: CPU: {cpu}%, RAM: {ram}%, Disk: {disk}%, Sandbox: {sandbox_size:.2f}MB (Growth: {growth_mb:.2f}MB)")
    
    # 4. Analyze thresholds and trigger alerts
    if cpu > config.cpu_alert_threshold:
        msg = f"CPU usage is high at {cpu}% (threshold: {config.cpu_alert_threshold}%)"
        sentinel_db.log_alert("CPU", cpu, config.cpu_alert_threshold, "WARNING", msg)
        logging.warning(msg)
        
    if ram > config.ram_alert_threshold:
        msg = f"RAM usage is high at {ram}% (threshold: {config.ram_alert_threshold}%)"
        sentinel_db.log_alert("RAM", ram, config.ram_alert_threshold, "WARNING", msg)
        logging.warning(msg)
        
    if disk > config.disk_alert_threshold:
        msg = f"Disk usage is high at {disk}% (threshold: {config.disk_alert_threshold}%)"
        sentinel_db.log_alert("DISK", disk, config.disk_alert_threshold, "ALERT", msg)
        logging.warning(msg)
        
    if growth_mb > config.dir_growth_threshold_mb:
        msg = f"Sandbox directory grew by {growth_mb:.2f}MB in the last interval (threshold: {config.dir_growth_threshold_mb}MB)"
        sentinel_db.log_alert("DIR_GROWTH", growth_mb, config.dir_growth_threshold_mb, "ALERT", msg)
        logging.warning(msg)

# =============================================================================
# 2. Smart Workspace Organizer Logic
# =============================================================================
async def process_file(file_path: str):
    """Categorizes and organizes a single file using multimodal AI."""
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        return

    file_name = os.path.basename(file_path)
    
    # Ignore hidden/temporary files
    if file_name.startswith(".") or file_name.endswith(".tmp") or file_name.endswith(".part"):
        return

    logging.info(f"ORGANIZER: Processing new file: {file_name}")
    
    try:
        # Load multimodal or text contents
        inputs = []
        ext = os.path.splitext(file_name)[1].lower()
        
        # Build contextual query
        prompt = (
            f"Analyze this file. Name: '{file_name}', Size: {os.path.getsize(file_path)} bytes. "
            "Determine the category folder name: Code, Documents, Images, Invoices, Archives, or Miscellaneous. "
            "Respond strictly with the category and a concise, user-friendly 1-sentence reasoning."
        )
        inputs.append(prompt)

        # Append multimodal data if applicable
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            try:
                inputs.append(Image.from_file(file_path))
            except Exception as e:
                logging.warning(f"Could not load image {file_name} multimodally: {e}")
        elif ext == ".pdf":
            try:
                inputs.append(Document.from_file(file_path))
            except Exception as e:
                logging.warning(f"Could not load PDF {file_name} multimodally: {e}")
        elif ext in [".txt", ".py", ".js", ".json", ".html", ".css", ".md", ".sh"]:
            try:
                with open(file_path, "r", errors="ignore") as f:
                    content = f.read(2000)
                inputs.append(f"\n--- File Snippet Content ---\n{content}\n----------------------------")
            except Exception as e:
                logging.warning(f"Could not read text from {file_name}: {e}")

        # Setup Agent for structured output
        agent_config = LocalAgentConfig(
            system_instructions="You are Proactive System Sentinel's organization expert. Categorize files with extreme precision.",
            response_schema=FileCategory
        )
        
        async with Agent(agent_config) as agent:
            response = await agent.chat(inputs)
            res = await response.structured_output()
            
        if not res or "category" not in res:
            raise ValueError("Failed to get a valid categorization schema from agent.")

        category = res["category"].strip().title()
        reasoning = res.get("reasoning", "Organized by Sentinel.")
        
        # Valid categories fallback to Miscellaneous
        valid_cats = ["Code", "Documents", "Images", "Invoices", "Archives", "Miscellaneous"]
        if category not in valid_cats:
            category = "Miscellaneous"
            
        config = sentinel_config.load_config()
        dest_dir = os.path.join(config.sandbox_dir, category)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, file_name)
        
        # Handle filename collisions
        base, extension = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{extension}")
            counter += 1
            
        # Move the file
        shutil.move(file_path, dest_path)
        
        # Log to Database
        sentinel_db.log_file_op(file_name, file_path, dest_path, category, reasoning, "SUCCESS")
        logging.info(f"ORGANIZER: Organized '{file_name}' -> '{category}/'. Reason: {reasoning}")
        
    except Exception as e:
        logging.error(f"ORGANIZER: Error organizing '{file_name}': {e}")
        sentinel_db.log_file_op(file_name, file_path, "", "Error", str(e), "ERROR")

# =============================================================================
# 3. File Change Trigger
# =============================================================================
async def handle_file_change(ctx: TriggerContext, changes):
    """Callback triggered by watchfiles on directory changes."""
    config = sentinel_config.load_config()
    for change in changes:
        # Check change kind (watchfiles tuples represent change type: 1=added, 2=modified, 3=deleted)
        # Or change object has change[0] as Change Enum/int and change[1] as filepath string.
        # Let's support both tuple indexing and attribute access.
        try:
            kind = change[0]
            path = change[1]
        except (TypeError, IndexError):
            kind = getattr(change, "kind", None)
            path = getattr(change, "path", None)
            
        # We represent Added as 1 (or 'added' or Change.added)
        # Let's check if the path is directly inside the sandbox_dir root.
        # If it's a child folder, we skip to avoid feedback loops!
        if path and (str(kind) == "1" or "added" in str(kind).lower()):
            if os.path.dirname(os.path.abspath(path)) == os.path.abspath(config.sandbox_dir):
                # Run the process in an async task to avoid blocking the trigger
                asyncio.create_task(process_file(path))

# =============================================================================
# Manual Scanning Utility (Triggered on-demand by CLI)
# =============================================================================
async def trigger_manual_scan():
    """Immediately scans and organizes all files in the sandbox root directory."""
    config = sentinel_config.load_config()
    os.makedirs(config.sandbox_dir, exist_ok=True)
    files = [
        os.path.join(config.sandbox_dir, f)
        for f in os.listdir(config.sandbox_dir)
        if os.path.isfile(os.path.join(config.sandbox_dir, f))
    ]
    
    if not files:
        logging.info("ORGANIZER: Manual scan completed. No files to organize.")
        return 0
        
    count = 0
    for f in files:
        file_name = os.path.basename(f)
        if not file_name.startswith(".") and not file_name.endswith(".tmp") and not file_name.endswith(".part"):
            await process_file(f)
            count += 1
            
    return count

# =============================================================================
# Main Background Agent Execution
# =============================================================================
async def main():
    config = sentinel_config.load_config()
    os.makedirs(config.sandbox_dir, exist_ok=True)
    
    # Initialize DB
    sentinel_db.init_db()
    
    # Create triggers
    timer_trigger = every(config.audit_interval, audit_system)
    file_trigger = on_file_change(config.sandbox_dir, handle_file_change)
    
    logging.info(f"SENTINEL: Starting background agent. Monitoring: {config.sandbox_dir}")
    logging.info(f"SENTINEL: System audit interval: {config.audit_interval}s")
    
    agent_config = LocalAgentConfig(
        system_instructions="You are Proactive System Sentinel. Monitor, analyze and organize user environment.",
        triggers=[timer_trigger, file_trigger]
    )
    
    # Run agent loop
    async with Agent(agent_config) as agent:
        logging.info("SENTINEL: Agent initialized and triggers active. Running indefinitely...")
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("SENTINEL: Background agent stopped by user.")
