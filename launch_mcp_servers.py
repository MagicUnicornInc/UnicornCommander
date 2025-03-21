#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import time
import signal
import threading
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCP-Launcher")

# MCP Server configuration
MCP_SERVERS = {
    "coordinator": {
        "name": "MCP Central Coordinator",
        "port": 8760,
        "cmd": ["node", "coordinator.js"],
        "dir": "~/GIT-Projects/MCP-Servers",
        "priority": 1  # Start first
    },
    "kde": {
        "name": "KDE MCP Server",
        "port": 8765,
        "cmd": ["node", "server.js"],
        "dir": "~/GIT-Projects/MCP-Servers",
        "priority": 2  # Start after coordinator
    },
    "code": {
        "name": "Code Execution MCP Server",
        "port": 8766,
        "cmd": ["node", "server.js"],
        "dir": "~/GIT-Projects/MCP-Servers/code",
        "priority": 3
    },
    "data": {
        "name": "Data Processing MCP Server",
        "port": 8767,
        "cmd": ["node", "server.js"],
        "dir": "~/GIT-Projects/MCP-Servers/data",
        "priority": 3
    },
    "network": {
        "name": "Network Operations MCP Server",
        "port": 8768,
        "cmd": ["node", "server.js"],
        "dir": "~/GIT-Projects/MCP-Servers/network",
        "priority": 3
    }
}

# Global process tracking
processes = {}
stop_event = threading.Event()

def expand_path(path):
    """Expand ~ to home directory"""
    return os.path.expanduser(path)

def is_port_available(port):
    """Check if a port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except:
        return False
    finally:
        sock.close()

def start_server(server_id):
    """Start a specific MCP server"""
    if server_id not in MCP_SERVERS:
        logger.error(f"Unknown server: {server_id}")
        return False
    
    server = MCP_SERVERS[server_id]
    
    # Check if port is available
    if not is_port_available(server["port"]):
        logger.warning(f"Port {server['port']} is already in use. {server['name']} may already be running.")
        return False
    
    try:
        # Create full command with working directory
        cmd = server["cmd"]
        working_dir = expand_path(server["dir"])
        
        # Start the process
        logger.info(f"Starting {server['name']} on port {server['port']}...")
        proc = subprocess.Popen(
            cmd,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store the process
        processes[server_id] = proc
        
        # Start log monitoring thread
        threading.Thread(
            target=monitor_logs,
            args=(server_id, proc),
            daemon=True
        ).start()
        
        # Wait a little to see if it starts successfully
        time.sleep(2)
        if proc.poll() is not None:
            logger.error(f"Failed to start {server['name']}: process exited immediately")
            return False
        
        logger.info(f"{server['name']} started successfully (PID: {proc.pid})")
        return True
        
    except Exception as e:
        logger.error(f"Error starting {server['name']}: {str(e)}")
        return False

def monitor_logs(server_id, proc):
    """Monitor and log stdout/stderr from a server process"""
    server = MCP_SERVERS[server_id]
    
    while not stop_event.is_set() and proc.poll() is None:
        # Read stdout
        stdout_line = proc.stdout.readline()
        if stdout_line:
            logger.info(f"[{server['name']}] {stdout_line.strip()}")
        
        # Read stderr
        stderr_line = proc.stderr.readline()
        if stderr_line:
            logger.error(f"[{server['name']}] {stderr_line.strip()}")
    
    # Process finished
    if proc.poll() is not None and not stop_event.is_set():
        logger.warning(f"{server['name']} has stopped unexpectedly (exit code: {proc.returncode})")

def start_all_servers():
    """Start all MCP servers in priority order"""
    # Sort servers by priority
    sorted_servers = sorted(MCP_SERVERS.items(), key=lambda x: x[1]["priority"])
    
    for server_id, _ in sorted_servers:
        if not start_server(server_id):
            logger.warning(f"Failed to start {server_id} server, but continuing with others...")
            
        # Pause between server starts
        time.sleep(3)

def stop_server(server_id):
    """Stop a specific MCP server"""
    if server_id not in processes:
        logger.warning(f"Server {server_id} is not running or not managed by this launcher")
        return
    
    proc = processes[server_id]
    
    # Try to terminate gracefully
    logger.info(f"Stopping {MCP_SERVERS[server_id]['name']}...")
    proc.terminate()
    
    # Wait for process to terminate
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # Force kill if it doesn't terminate in time
        logger.warning(f"{MCP_SERVERS[server_id]['name']} did not terminate gracefully, killing it...")
        proc.kill()
    
    logger.info(f"{MCP_SERVERS[server_id]['name']} stopped")
    del processes[server_id]

def stop_all_servers():
    """Stop all running MCP servers"""
    # Set stop event to notify log monitors
    stop_event.set()
    
    # Sort servers by reverse priority (shutdown in reverse order of startup)
    server_ids = sorted(
        processes.keys(),
        key=lambda x: MCP_SERVERS[x]["priority"],
        reverse=True
    )
    
    for server_id in server_ids:
        stop_server(server_id)

def status():
    """Show status of all MCP servers"""
    running = 0
    for server_id, server in MCP_SERVERS.items():
        if server_id in processes and processes[server_id].poll() is None:
            status_str = f"RUNNING (PID: {processes[server_id].pid})"
            running += 1
        else:
            status_str = "STOPPED"
        
        logger.info(f"{server['name']} - Port {server['port']} - {status_str}")
    
    return running

def handle_signal(signum, frame):
    """Signal handler for graceful shutdown"""
    logger.info("Received shutdown signal, stopping all servers...")
    stop_all_servers()
    sys.exit(0)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MCP Servers Launcher")
    
    # Main commands
    cmd_group = parser.add_mutually_exclusive_group(required=True)
    cmd_group.add_argument("--start", action="store_true", help="Start MCP servers")
    cmd_group.add_argument("--stop", action="store_true", help="Stop MCP servers")
    cmd_group.add_argument("--restart", action="store_true", help="Restart MCP servers")
    cmd_group.add_argument("--status", action="store_true", help="Show MCP servers status")
    
    # Server selection (optional)
    parser.add_argument("--server", help="Specific server ID to manage (default: all servers)")
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        if args.server and args.server not in MCP_SERVERS:
            logger.error(f"Unknown server ID: {args.server}")
            return 1
        
        server_ids = [args.server] if args.server else None
        
        if args.start:
            if server_ids:
                for server_id in server_ids:
                    start_server(server_id)
            else:
                start_all_servers()
            
            # Show status after starting
            time.sleep(1)
            running = status()
            if running == 0:
                logger.error("No servers were started successfully")
                return 1
            
        elif args.stop:
            if server_ids:
                for server_id in server_ids:
                    stop_server(server_id)
            else:
                stop_all_servers()
            
        elif args.restart:
            if server_ids:
                for server_id in server_ids:
                    if server_id in processes:
                        stop_server(server_id)
                    start_server(server_id)
            else:
                stop_all_servers()
                time.sleep(2)
                start_all_servers()
            
            # Show status after restarting
            time.sleep(1)
            running = status()
            if running == 0:
                logger.error("No servers were restarted successfully")
                return 1
            
        elif args.status:
            status()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())