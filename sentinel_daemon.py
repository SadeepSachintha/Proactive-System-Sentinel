import os
import sys
import signal
import subprocess
import psutil
import time

PID_FILE = os.path.expanduser("~/.gemini/antigravity/sentinel_agent.pid")
LOG_FILE = os.path.expanduser("~/.gemini/antigravity/sentinel_agent.log")

def get_running_pid():
    """Reads PID from pid file and verifies if the process is active and running sentinel_agent."""
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Check if process is alive and is actually a Python process running sentinel_agent
        if psutil.pid_exists(pid):
            p = psutil.Process(pid)
            cmd = " ".join(p.cmdline())
            if "sentinel_agent" in cmd:
                return pid
    except Exception:
        pass
    return None

def start_daemon() -> tuple[bool, str]:
    """Starts the sentinel_agent background process."""
    existing_pid = get_running_pid()
    if existing_pid:
        return False, f"Sentinel daemon is already running (PID: {existing_pid})."

    # Find the local python interpreter
    workspace_dir = "/Users/sadeep/Projects/Proactive System Sentinel"
    python_executable = os.path.join(workspace_dir, ".venv/bin/python3")
    agent_script = os.path.join(workspace_dir, "sentinel_agent.py")

    # Start the process in the background, redirecting stdout/stderr to the log file
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log_fd = open(LOG_FILE, "a")

    try:
        # On macOS/Unix, we run using subprocess.Popen with double-fork or detached process group
        proc = subprocess.Popen(
            [python_executable, agent_script],
            stdout=log_fd,
            stderr=log_fd,
            cwd=workspace_dir,
            preexec_fn=os.setsid,  # Run in a new session to detach from current terminal
            close_fds=True
        )
        
        # Write PID file
        with open(PID_FILE, "w") as f:
            f.write(str(proc.pid))
            
        # Wait a brief moment and verify it's still running
        time.sleep(0.5)
        if psutil.pid_exists(proc.pid):
            return True, f"Sentinel daemon started successfully (PID: {proc.pid})."
        else:
            return False, "Sentinel daemon failed to start. Check log file for details."
            
    except Exception as e:
        return False, f"Failed to start daemon: {e}"
    finally:
        log_fd.close()

def stop_daemon() -> tuple[bool, str]:
    """Stops the running sentinel_agent daemon."""
    pid = get_running_pid()
    if not pid:
        # Clean up dangling pid file if it exists
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
        return False, "Sentinel daemon is not running."

    try:
        # Try graceful termination first (SIGTERM)
        os.kill(pid, signal.SIGTERM)
        
        # Wait for termination
        for _ in range(10):
            time.sleep(0.2)
            if not psutil.pid_exists(pid):
                break
        else:
            # Force kill if still alive
            os.kill(pid, signal.SIGKILL)
            
        # Clean up PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            
        return True, f"Sentinel daemon stopped successfully (PID: {pid})."
    except Exception as e:
        return False, f"Error stopping daemon: {e}"

def get_daemon_status() -> tuple[bool, str]:
    """Returns daemon running state and details."""
    pid = get_running_pid()
    if not pid:
        return False, "Inactive"
        
    try:
        p = psutil.Process(pid)
        cpu = p.cpu_percent(interval=0.1)
        mem = p.memory_percent()
        create_time = datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
        return True, f"Active (PID: {pid}) | CPU: {cpu:.1f}% | Mem: {mem:.1f}% | Started: {create_time}"
    except Exception:
        return True, f"Active (PID: {pid})"
