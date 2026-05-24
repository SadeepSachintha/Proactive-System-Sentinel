# Proactive System Sentinel 🛡️

A command-line and system-level automation agent that runs in the background to monitor, analyze, and assist you with your files and system resources using the **Google Antigravity (AGY) SDK** and Gemini's multimodal reasoning.

---

## 🌟 Key Features

1. **📂 Smart Workspace Organizer**:
   Automatically monitors your designated sandbox directory. When new files (such as source code, plain documents, image screenshots, PDF invoices, or archives) are added, the Sentinel uses Gemini's multimodal AI capabilities to analyze the content, categorize them, and move them into sorted category subfolders (`Code`, `Documents`, `Invoices`, `Images`, `Archives`, or `Miscellaneous`) while logging the exact reasoning behind its choice.

2. **📊 System Status & File Auditing**:
   Runs background audits periodically (configured to every 60 seconds). It logs metrics for CPU, memory, and disk usage into a persistent SQLite database. If resource usage crosses thresholds or if files grow too rapidly in size, it generates natural language warnings and alerts.

3. **🔄 Interactive CLI Dashboard**:
   A gorgeous console client styled with the `rich` library. Features visual progress bars for system loads, background daemon process tags (live PID, uptime, memory indicators), setting controllers, history visualizers, and direct controls to start, stop, or restart the background Sentinel daemon process.

---

## 📂 Project Structure

```
/Users/sadeep/Projects/Proactive System Sentinel/
├── .venv/                         # Local Python virtual environment
├── sentinel_config.py             # Settings manager (Pydantic schema validation)
├── sentinel_db.py                 # SQLite database engine (audit history, file ops logs)
├── sentinel_agent.py              # AGY Agent loop, system audit and organizer triggers
├── sentinel_daemon.py             # Detached background process lifecycle controller
├── sentinel_cli.py                # Beautiful interactive terminal console dashboard
├── .gitignore                     # Git filter for venvs, credentials, and local databases
├── .env.example                   # Environment credentials template
└── test_sentinel.py               # Automated verification test suite
```

---

## ⚙️ Installation & Setup

### 1. Configure Credentials
Copy the credentials template to a `.env` file and insert your Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/api-keys):
```bash
cp .env.example .env
# Open '.env' and fill in: GEMINI_API_KEY=your_api_key
```

### 2. Verify Your Setup
Run the automated mock verification suite to test database initialization, schema validation, and file organization logic:
```bash
.venv/bin/python3 test_sentinel.py
```

### 3. Launch the Interactive CLI Dashboard
To monitor system health, start/stop the background daemon, or view audit logs, launch the console interface:
```bash
.venv/bin/python3 sentinel_cli.py
```

---

## 🛠️ SQLite Log Databases

The Sentinel uses a local SQLite database (`sentinel_db.sqlite`) containing three primary tables:
- **`file_ops`**: Records file movements: source, destination, status, and Gemini's detailed categorization reasoning.
- **`alerts`**: Logs historical resource usage alerts, warnings, and anomaly details.
- **`metrics`**: Archives logs of CPU, memory, disk, and directory sizes.

---

## 📝 CLI Menu Operations
- **`1.` Smart Workspace Organizer**: Instantly scans the sandbox root directory and triggers immediate categorization on all root files.
- **`2.` View History & Alerts**: Lists tabular views of recent file organization operations and resource warning tables.
- **`3.` Configure Sentinel**: Provides setting updates (e.g. adjust monitored sandbox path, alert limits, audit interval durations).
- **`4.` Manage Background Daemon**: Detaches and launches `sentinel_agent.py` in the background (or terminates active processes gracefully).
- **`5.` Exit**: Closes the dashboard.
