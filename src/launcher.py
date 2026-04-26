import os
import sys
import subprocess
import re
import yaml
import questionary
from init_config import detect_lan_ip, _load_existing, CONFIG_PATH

def get_tailscale_ip():
    """Attempt to detect Tailscale IP (100.x.x.x) across platforms."""
    try:
        # Check platform
        if sys.platform == "win32":
            output = subprocess.check_output(["ipconfig"], text=True)
        else:
            output = subprocess.check_output(["ifconfig"], text=True)
            
        match = re.search(r"\b(100\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", output)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None

def configure_network():
    """Handles network configuration for host.yaml."""
    choice = questionary.select(
        "How would you like to configure the network?",
        choices=[
            "Auto-detect LAN IP",
            "Auto-detect Tailscale IP",
            "Manual Input",
            "Back"
        ]
    ).ask()
    
    if choice == "Back" or choice is None:
        return
        
    host = None
    if choice == "Auto-detect LAN IP":
        try:
            host = detect_lan_ip()
            print(f"[+] Detected LAN IP: {host}")
        except Exception as e:
            print(f"[-] Could not auto-detect LAN IP: {e}")
            return
            
    elif choice == "Auto-detect Tailscale IP":
        host = get_tailscale_ip()
        if host:
            print(f"[+] Detected Tailscale IP: {host}")
        else:
            print("[-] Could not find a Tailscale IP (100.x.x.x).")
            return
            
    elif choice == "Manual Input":
        host = questionary.text("Enter IP address:").ask()
        if not host:
            return
            
    port_str = questionary.text("Enter port (default 12345):", default="12345").ask()
    if not port_str:
        return
    try:
        port = int(port_str)
    except ValueError:
        print("[-] Invalid port number.")
        return
        
    profile_name = questionary.text("Enter profile name (default 'self'):", default="self").ask()
    if not profile_name:
        return
        
    # Update config/host.yaml
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = _load_existing(CONFIG_PATH)
    
    existed = profile_name in data["server_list"]
    data["server_list"][profile_name] = {"host": host, "port": port}
    
    CONFIG_PATH.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )
    verb = "Updated" if existed else "Added"
    print(f"[+] {verb} profile '{profile_name}' -> {host}:{port}")

def select_profile():
    """Helper to select a profile from config/host.yaml."""
    if not CONFIG_PATH.exists():
        print("[-] Config file not found. Please Configure Network first.")
        return None
        
    data = _load_existing(CONFIG_PATH)
    profiles = list(data.get("server_list", {}).keys())
    
    if not profiles:
        print("[-] No profiles found in config. Please Configure Network first.")
        return None
        
    return questionary.select("Select profile:", choices=profiles).ask()

def run_client():
    sid = questionary.text("Enter Student ID:").ask()
    if not sid:
        return
        
    auto_play = questionary.confirm("Play automatically?", default=False).ask()
    
    profile = select_profile()
    if not profile:
        return
        
    cmd = [sys.executable, "src/client.py", "--profile", profile, "--student-id", sid]
    if auto_play:
        cmd.append("--auto")
        
    subprocess.run(cmd)

def run_server_single():
    profile = select_profile()
    if not profile:
        return
    subprocess.run([sys.executable, "src/server.py", "--profile", profile])

def run_server_multi():
    profile = select_profile()
    if not profile:
        return
    subprocess.run([sys.executable, "src/server_multiuser.py", "--profile", profile])

def main():
    while True:
        choice = questionary.select(
            "Socket Programming HW - Main Menu",
            choices=[
                "Start Client (Play Game)",
                "Start Server (Single-player)",
                "Start Server (Multi-player)",
                "Configure Network",
                "Exit"
            ]
        ).ask()
        
        if choice == "Start Client (Play Game)":
            run_client()
        elif choice == "Start Server (Single-player)":
            run_server_single()
        elif choice == "Start Server (Multi-player)":
            run_server_multi()
        elif choice == "Configure Network":
            configure_network()
        elif choice == "Exit" or choice is None:
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
