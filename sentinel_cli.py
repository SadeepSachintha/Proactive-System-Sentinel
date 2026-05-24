import os
import sys
import time
import asyncio
import psutil
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED, DOUBLE

import sentinel_config
import sentinel_db
import sentinel_daemon

# Import agent manual scan logic
try:
    import sentinel_agent
except ImportError:
    sentinel_agent = None

console = Console()

BANNER = """
 ██████╗ ██████╗  ██████╗  █████╗  ██████╗████████╗██╗██╗   ██╗███████╗
██╔═══██╗██╔══██╗██╔═══██╗██╔══██╗██╔════╝╚══██╔══╝██║██║   ██║██╔════╝
██║   ██║██████╔╝██║   ██║███████║██║        ██║   ██║██║   ██║█████╗  
██║   ██║██╔══██╗██║   ██║██╔══██║██║        ██║   ██║╚██╗ ██╔╝██╔══╝  
╚██████╔╝██║  ██║╚██████╔╝██║  ██║╚██████╗   ██║   ██║ ╚████╔╝ ███████╗
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝  ╚═══╝  ╚══════╝
                     S Y S T E M   S E N T I N E L
"""

def print_banner():
    """Prints the premium gradient ASCII banner."""
    console.print(Align.center(Text(BANNER, style="bold cyan")), justify="center")
    console.print(Align.center(Text("Active Multimodal Monitoring & Workspace Orchestration Agent", style="italic white")), justify="center")
    console.print()

def get_meter_bar(percent: float, width: int = 15) -> str:
    """Generates a stylish visual block progress bar."""
    filled_length = int(round(width * percent / 100))
    bar = "█" * filled_length + "░" * (width - filled_length)
    if percent > 85:
        color = "red"
    elif percent > 60:
        color = "yellow"
    else:
        color = "green"
    return f"[{color}]{bar} {percent:.1f}%[/{color}]"

def show_dashboard():
    """Renders the comprehensive, beautiful dashboard of the Sentinel agent and system resources."""
    config = sentinel_config.load_config()
    
    # Check if API Key is available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY"):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass

    if not api_key:
        api_warning_text = Text()
        api_warning_text.append("⚠️ ATTENTION: GEMINI_API_KEY is not set!\n", style="bold yellow")
        api_warning_text.append("Smart Workspace Organizer and AI features require an API key to function.\n\n", style="white")
        api_warning_text.append("To get an API Key, visit: ", style="dim white")
        api_warning_text.append("https://aistudio.google.com/app/api-keys\n", style="underline cyan")
        api_warning_text.append("Then, create a '.env' file in this project directory containing:\n", style="dim white")
        api_warning_text.append("GEMINI_API_KEY=your_api_key_here", style="bold green")
        
        api_panel = Panel(
            api_warning_text,
            title="[bold yellow]API Credentials Setup Required[/bold yellow]",
            title_align="left",
            border_style="yellow",
            box=ROUNDED
        )
        console.print(api_panel)
        console.print()
    
    # 1. Daemon Status Panel
    running, details = sentinel_daemon.get_daemon_status()
    status_text = Text()
    if running:
        status_text.append("● RUNNING  ", style="bold green")
        status_text.append(f"| {details}", style="dim white")
    else:
        status_text.append("○ INACTIVE ", style="bold red")
        status_text.append("| The background Sentinel daemon is currently stopped.", style="dim white")
        
    daemon_panel = Panel(
        status_text,
        title="[bold]Background Sentinel Daemon Status[/bold]",
        title_align="left",
        border_style="green" if running else "red",
        box=ROUNDED
    )
    
    # 2. Live System Resources Panel
    # CPU, Memory, Disk, Sandbox size
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    sandbox_size = sentinel_agent.get_dir_size_mb(config.sandbox_dir) if sentinel_agent else 0.0
    
    sys_table = Table.grid(expand=True)
    sys_table.add_column(width=20)
    sys_table.add_column()
    
    sys_table.add_row("[bold cyan]CPU Load[/bold cyan]", get_meter_bar(cpu))
    sys_table.add_row("[bold cyan]RAM memory[/bold cyan]", get_meter_bar(mem))
    sys_table.add_row("[bold cyan]Disk Space[/bold cyan]", get_meter_bar(disk))
    sys_table.add_row("[bold cyan]Sandbox Size[/bold cyan]", f"[bold yellow]{sandbox_size:.2f} MB[/bold yellow] (Path: {config.sandbox_dir})")
    
    sys_panel = Panel(
        sys_table,
        title="[bold]Real-time System Environment[/bold]",
        title_align="left",
        border_style="cyan",
        box=ROUNDED
    )
    
    # Render Panels
    console.print(daemon_panel)
    console.print(sys_panel)
    console.print()

def view_logs():
    """Displays detailed logs for File Operations and Resource Alerts."""
    console.clear()
    print_banner()
    
    # Table 1: File Organizer Ops
    console.print("[bold green]📂 Recent Smart Workspace Organizer History[/bold green]")
    ops = sentinel_db.get_file_ops(limit=7)
    if not ops:
        console.print("[dim]No file organization activities logged yet.[/dim]\n")
    else:
        table = Table(box=ROUNDED, border_style="green", expand=True)
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("File Name", style="white", width=25)
        table.add_column("Category", style="bold yellow", width=12)
        table.add_column("Status", style="bold green", width=10)
        table.add_column("AI Reasoning / Error Message", style="dim italic")
        
        for op in ops:
            status_style = "bold green" if op["status"] == "SUCCESS" else "bold red"
            # Format timestamp
            try:
                t = datetime.fromisoformat(op["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                t = op["timestamp"]
            table.add_row(
                t,
                op["file_name"],
                op["category"],
                f"[{status_style}]{op['status']}[/{status_style}]",
                op["reasoning"]
            )
        console.print(table)
        console.print()
        
    # Table 2: System Resource Alerts
    console.print("[bold red]⚠️ Recent System Sentinel Resource Warnings & Alerts[/bold red]")
    alerts = sentinel_db.get_alerts(limit=7)
    if not alerts:
        console.print("[dim]No resource warning alerts triggered yet.[/dim]\n")
    else:
        table = Table(box=ROUNDED, border_style="red", expand=True)
        table.add_column("Timestamp", style="cyan", width=20)
        table.add_column("Metric", style="bold yellow", width=12)
        table.add_column("Value", style="white", width=10)
        table.add_column("Threshold", style="white", width=10)
        table.add_column("Severity", style="bold red", width=12)
        table.add_column("Alert Description", style="dim italic")
        
        for alert in alerts:
            sev_color = "red" if alert["severity"] == "ALERT" else "yellow"
            try:
                t = datetime.fromisoformat(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                t = alert["timestamp"]
            table.add_row(
                t,
                alert["metric"],
                f"{alert['value']:.1f}",
                f"{alert['threshold']:.1f}",
                f"[{sev_color}]{alert['severity']}[/{sev_color}]",
                alert["message"]
            )
        console.print(table)
        console.print()
        
    input("\nPress ENTER to return to Main Menu...")

def run_manual_scan():
    """Triggers an immediate workspace organization task."""
    console.clear()
    print_banner()
    
    if not sentinel_agent:
        console.print("[bold red]Error:[/bold red] Sentinel Agent modules failed to load. Make sure the virtual env is correctly configured.")
        time.sleep(2)
        return
        
    console.print("[bold yellow]📂 Starting Immediate Sandbox Scan & Organize...[/bold yellow]")
    console.print("[dim]Scanning root files in the sandbox directory using multimodal AI...[/dim]\n")
    
    try:
        # Run manual scan synchronously in CLI
        count = asyncio.run(sentinel_agent.trigger_manual_scan())
        if count > 0:
            console.print(f"[bold green]✓ Done![/bold green] Successfully scanned and categorized [bold]{count}[/bold] file(s).")
        else:
            console.print("[yellow]✓ Completed.[/yellow] No new files found in the sandbox root to organize.")
    except Exception as e:
        console.print(f"[bold red]✕ Error during scan:[/bold red] {e}")
        
    input("\nPress ENTER to return to Main Menu...")

def configure_settings():
    """Allows visual settings updates."""
    console.clear()
    print_banner()
    config = sentinel_config.load_config()
    
    console.print("[bold cyan]⚙️ Configure Sentinel Settings[/bold cyan]\n")
    console.print(f"[1] Sandbox Directory  : [yellow]{config.sandbox_dir}[/yellow]")
    console.print(f"[2] Audit Interval     : [yellow]{config.audit_interval} seconds[/yellow]")
    console.print(f"[3] CPU Alert Limit    : [yellow]{config.cpu_alert_threshold}%[/yellow]")
    console.print(f"[4] RAM Alert Limit    : [yellow]{config.ram_alert_threshold}%[/yellow]")
    console.print(f"[5] Disk Alert Limit   : [yellow]{config.disk_alert_threshold}%[/yellow]")
    console.print(f"[6] Growth Alert Limit : [yellow]{config.dir_growth_threshold_mb} MB[/yellow]")
    console.print("[7] Return to Main Menu\n")
    
    choice = input("Select setting to update (1-7): ").strip()
    if choice == "1":
        new_val = input(f"Enter new sandbox directory (default: {config.sandbox_dir}): ").strip()
        if new_val:
            config.sandbox_dir = os.path.abspath(os.path.expanduser(new_val))
            sentinel_config.save_config(config)
            console.print("[bold green]✓ Sandbox Directory updated![/bold green]")
    elif choice == "2":
        new_val = input(f"Enter audit interval in seconds (current: {config.audit_interval}): ").strip()
        if new_val.isdigit():
            config.audit_interval = int(new_val)
            sentinel_config.save_config(config)
            console.print("[bold green]✓ Audit interval updated![/bold green]")
    elif choice == "3":
        new_val = input(f"Enter CPU threshold percentage (current: {config.cpu_alert_threshold}%): ").strip()
        try:
            config.cpu_alert_threshold = float(new_val)
            sentinel_config.save_config(config)
            console.print("[bold green]✓ CPU alert limit updated![/bold green]")
        except ValueError:
            pass
    elif choice == "4":
        new_val = input(f"Enter RAM threshold percentage (current: {config.ram_alert_threshold}%): ").strip()
        try:
            config.ram_alert_threshold = float(new_val)
            sentinel_config.save_config(config)
            console.print("[bold green]✓ RAM alert limit updated![/bold green]")
        except ValueError:
            pass
    elif choice == "5":
        new_val = input(f"Enter Disk threshold percentage (current: {config.disk_alert_threshold}%): ").strip()
        try:
            config.disk_alert_threshold = float(new_val)
            sentinel_config.save_config(config)
            console.print("[bold green]✓ Disk alert limit updated![/bold green]")
        except ValueError:
            pass
    elif choice == "6":
        new_val = input(f"Enter Directory Growth threshold limit in MB (current: {config.dir_growth_threshold_mb} MB): ").strip()
        try:
            config.dir_growth_threshold_mb = float(new_val)
            sentinel_config.save_config(config)
            console.print("[bold green]✓ Growth alert limit updated![/bold green]")
        except ValueError:
            pass
    else:
        return

    # Check if daemon is active and notify user
    running, _ = sentinel_daemon.get_daemon_status()
    if running:
        console.print("\n[yellow]Note: Since the Sentinel daemon is running, you must restart it for settings to take effect![/yellow]")
    
    time.sleep(1.5)

def manage_daemon():
    """Menu option for daemon control actions."""
    console.clear()
    print_banner()
    
    running, details = sentinel_daemon.get_daemon_status()
    console.print("[bold green]🔄 Background Daemon Service Management[/bold green]\n")
    if running:
        console.print(f"Current state: [bold green]● RUNNING[/bold green]")
        console.print(f"Details: {details}\n")
        console.print("[1] Stop background daemon")
        console.print("[2] Restart background daemon")
    else:
        console.print(f"Current state: [bold red]○ INACTIVE[/bold red]\n")
        console.print("[1] Start background daemon")
        
    console.print("[3] Return to Main Menu\n")
    
    choice = input("Select command option: ").strip()
    if running:
        if choice == "1":
            console.print("[yellow]Stopping Sentinel daemon...[/yellow]")
            success, msg = sentinel_daemon.stop_daemon()
            if success:
                console.print(f"[bold green]✓ {msg}[/bold green]")
            else:
                console.print(f"[bold red]✕ {msg}[/bold red]")
        elif choice == "2":
            console.print("[yellow]Restarting Sentinel daemon...[/yellow]")
            sentinel_daemon.stop_daemon()
            success, msg = sentinel_daemon.start_daemon()
            if success:
                console.print(f"[bold green]✓ {msg}[/bold green]")
            else:
                console.print(f"[bold red]✕ {msg}[/bold red]")
    else:
        if choice == "1":
            console.print("[yellow]Starting Sentinel daemon...[/yellow]")
            success, msg = sentinel_daemon.start_daemon()
            if success:
                console.print(f"[bold green]✓ {msg}[/bold green]")
            else:
                console.print(f"[bold red]✕ {msg}[/bold red]")
                
    time.sleep(2)

def main_loop():
    """Main interactive execution loop."""
    sentinel_db.init_db()
    
    while True:
        console.clear()
        print_banner()
        show_dashboard()
        
        console.print("[bold yellow]Menu Options:[/bold yellow]")
        console.print("  [bold green]1.[/bold green] 📂 Smart Workspace Organizer (Trigger Immediate Scan)")
        console.print("  [bold green]2.[/bold green] 📊 View File Organization History & System Alert Logs")
        console.print("  [bold green]3.[/bold green] ⚙️ Configure Sentinel Thresholds & Sandbox Path")
        console.print("  [bold green]4.[/bold green] 🔄 Manage Background Daemon (Start/Stop/Restart)")
        console.print("  [bold green]5.[/bold green] 🛑 Exit System Sentinel CLI")
        console.print()
        
        choice = input("Enter choice (1-5): ").strip()
        if choice == "1":
            run_manual_scan()
        elif choice == "2":
            view_logs()
        elif choice == "3":
            configure_settings()
        elif choice == "4":
            manage_daemon()
        elif choice == "5":
            console.print("\n[bold cyan]Goodbye![/bold cyan]")
            break
        else:
            console.print("[bold red]Invalid option. Please choose 1-5.[/bold red]")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Sentinel CLI closed.[/bold cyan]")
