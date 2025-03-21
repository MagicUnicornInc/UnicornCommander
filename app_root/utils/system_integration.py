#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import logging
import time
from PyQt6.QtCore import QStandardPaths, QSettings, QProcess
from PyQt6.QtWidgets import QApplication

# KF6 imports
try:
    from PyKF6.KNotifications import KNotification
    from PyKF6.KService import KService
    from PyKF6.KConfigCore import KConfig, KConfigGroup
    from PyKF6.KSVG import KSvg
    KF_AVAILABLE = True
except ImportError:
    KF_AVAILABLE = False


def setup_autostart(enable=True):
    """Set up or remove autostart entry for the application"""
    # Get autostart directory
    autostart_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericConfigLocation)
    autostart_dir = os.path.join(autostart_dir, "autostart")
    
    # Ensure autostart directory exists
    os.makedirs(autostart_dir, exist_ok=True)
    
    # Desktop file path
    desktop_file = os.path.join(autostart_dir, "kde-ai-interface.desktop")
    
    if KF_AVAILABLE:
        if enable:
            # Create KService and save it to autostart
            config = KConfig(desktop_file, KConfig.SimpleConfig)
            group = KConfigGroup(config, "Desktop Entry")
            
            group.writeEntry("Type", "Application")
            group.writeEntry("Name", "KDE AI Interface")
            group.writeEntry("Comment", "AI assistant for KDE Plasma")
            group.writeEntry("Exec", get_executable_path())
            group.writeEntry("Icon", "system-search")
            group.writeEntry("X-KDE-autostart-after", "panel")
            group.writeEntry("X-KDE-StartupNotify", "false")
            group.writeEntry("X-DBUS-StartupType", "Unique")
            group.writeEntry("X-KDE-UniqueApplet", "true")
            group.writeEntry("NoDisplay", "false")
            
            config.sync()
            
            return True
        else:
            # Remove autostart desktop file if it exists
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            return False
    else:
        # Fallback for non-KF6 environment
        if enable:
            # Create autostart desktop file
            with open(desktop_file, 'w') as f:
                f.write("""[Desktop Entry]
Type=Application
Name=KDE AI Interface
Comment=AI assistant for KDE Plasma
Exec={exec_path}
Icon=system-search
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
X-KDE-StartupNotify=false
X-DBUS-StartupType=Unique
X-KDE-UniqueApplet=true
NoDisplay=false
""".format(exec_path=get_executable_path()))
            
            return True
        else:
            # Remove autostart desktop file if it exists
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            return False


def get_executable_path():
    """Get the path to the application executable"""
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return sys.executable
    else:
        # Get the absolute path of the main script
        return os.path.abspath(sys.argv[0])


def get_kde_version():
    """Get the KDE Plasma version"""
    if KF_AVAILABLE:
        try:
            # Try to get KDE version using kf6-config
            output = subprocess.check_output(
                ["kf6-config", "--version"], 
                universal_newlines=True
            )
            
            # Parse output to find Plasma version
            for line in output.splitlines():
                if "Plasma" in line:
                    return line.split(":")[-1].strip()
            
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
    else:
        try:
            # Try to get KDE version using kf5-config as fallback
            output = subprocess.check_output(
                ["kf5-config", "--version"], 
                universal_newlines=True
            )
            
            # Parse output to find Plasma version
            for line in output.splitlines():
                if "Plasma" in line:
                    return line.split(":")[-1].strip()
            
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None


def apply_kde_theme(widget, force_dark=False):
    """Apply KDE theme to a widget"""
    # Get application instance
    app = QApplication.instance()
    
    if KF_AVAILABLE:
        if force_dark:
            # Force dark mode using KDE's color scheme
            import qdarkstyle
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        else:
            # Use system palette (follows KDE settings)
            app.setStyleSheet("")
    else:
        if force_dark:
            # Force dark palette
            app.setStyle("Breeze")
            
            # Use Breeze Dark palette
            import qdarkstyle
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        else:
            # Use system palette (follows KDE settings)
            app.setStyleSheet("")


def notify(title, message, icon="dialog-information"):
    """Show a system notification"""
    if KF_AVAILABLE:
        # Use KNotification for KDE-integrated notifications
        notification = KNotification("notification")
        notification.setTitle(title)
        notification.setText(message)
        notification.setIconName(icon)
        notification.sendEvent()
        return True
    else:
        # Since we don't have DBus, use the generic notification
        try:
            subprocess.call(["notify-send", title, message])
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print(f"Notification: {title} - {message}")
            return False


# MCP Server management
class MCPServerManager:
    """Manager for MCP Servers"""
    
    def __init__(self, script_path=None):
        """Initialize the MCP Server Manager
        
        Args:
            script_path: Path to the MCP server launcher script
        """
        self.logger = logging.getLogger("MCPServerManager")
        
        # Use provided script path or search for it
        if script_path:
            self.script_path = script_path
        else:
            # Determine script path based on the application path
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.script_path = os.path.join(app_dir, "launch_mcp_servers.py")
        
        # Check if script exists
        if not os.path.exists(self.script_path):
            self.logger.warning(f"MCP server launcher script not found at {self.script_path}")
            self.available = False
        else:
            self.available = True
            
        # Process tracking
        self.process = None
        self._status_thread = None
        self._stop_event = threading.Event()
        
    def start_servers(self):
        """Start all MCP servers"""
        if not self.available:
            self.logger.error("MCP servers cannot be started: launcher script not available")
            return False
            
        try:
            # Start the servers using the script
            self.logger.info("Starting MCP servers...")
            
            # Use QProcess for better integration with Qt
            if self.process is None:
                self.process = QProcess()
                self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
                self.process.readyReadStandardOutput.connect(self._read_output)
                self.process.finished.connect(self._process_finished)
            
            # Start the script with --start argument
            self.process.start(sys.executable, [self.script_path, "--start"])
            
            # Wait a bit to see if it starts successfully
            if not self.process.waitForStarted(3000):  # Wait for 3 seconds
                self.logger.error("Failed to start MCP servers")
                return False
                
            self.logger.info("MCP servers starting...")
            
            # Start status monitoring thread
            self._stop_event.clear()
            if not self._status_thread or not self._status_thread.is_alive():
                self._status_thread = threading.Thread(
                    target=self._monitor_status,
                    daemon=True
                )
                self._status_thread.start()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting MCP servers: {str(e)}")
            return False
    
    def stop_servers(self):
        """Stop all MCP servers"""
        if not self.available:
            self.logger.error("MCP servers cannot be stopped: launcher script not available")
            return False
            
        try:
            # Stop status monitoring
            self._stop_event.set()
            
            # Stop the servers using the script
            self.logger.info("Stopping MCP servers...")
            
            # Use subprocess for stopping since we don't need to monitor it
            result = subprocess.run(
                [sys.executable, self.script_path, "--stop"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to stop MCP servers: {result.stderr}")
                return False
                
            self.logger.info("MCP servers stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping MCP servers: {str(e)}")
            return False
    
    def restart_servers(self):
        """Restart all MCP servers"""
        if not self.available:
            self.logger.error("MCP servers cannot be restarted: launcher script not available")
            return False
            
        try:
            # First stop the status monitoring
            self._stop_event.set()
            
            # Use subprocess for restarting
            self.logger.info("Restarting MCP servers...")
            result = subprocess.run(
                [sys.executable, self.script_path, "--restart"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to restart MCP servers: {result.stderr}")
                return False
            
            # Start status monitoring thread again
            self._stop_event.clear()
            if not self._status_thread or not self._status_thread.is_alive():
                self._status_thread = threading.Thread(
                    target=self._monitor_status,
                    daemon=True
                )
                self._status_thread.start()
                
            self.logger.info("MCP servers restarted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting MCP servers: {str(e)}")
            return False
    
    def get_status(self):
        """Get status of all MCP servers"""
        if not self.available:
            return {"status": "unavailable", "servers": {}}
            
        try:
            # Get status using the script
            result = subprocess.run(
                [sys.executable, self.script_path, "--status"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Failed to get MCP servers status: {result.stderr}")
                return {"status": "error", "servers": {}}
            
            # Parse the output to get status
            output = result.stdout
            servers = {}
            overall_status = "stopped"
            
            for line in output.splitlines():
                if " - Port " in line and " - " in line.split(" - Port ")[1]:
                    parts = line.split(" - ")
                    name = parts[0].strip()
                    port = parts[1].replace("Port ", "").strip()
                    status = parts[2].strip()
                    
                    server_id = self._get_server_id_from_name(name)
                    if server_id:
                        servers[server_id] = {
                            "name": name,
                            "port": port,
                            "status": "running" if "RUNNING" in status else "stopped"
                        }
                        
                        # If any server is running, consider the overall status as running
                        if "RUNNING" in status:
                            overall_status = "running"
            
            return {
                "status": overall_status,
                "servers": servers
            }
            
        except Exception as e:
            self.logger.error(f"Error getting MCP servers status: {str(e)}")
            return {"status": "error", "servers": {}}
    
    def _get_server_id_from_name(self, name):
        """Convert a server name to its ID"""
        # Simple mapping table
        mapping = {
            "MCP Central Coordinator": "coordinator",
            "KDE MCP Server": "kde",
            "Code Execution MCP Server": "code",
            "Data Processing MCP Server": "data",
            "Network Operations MCP Server": "network"
        }
        
        for server_name, server_id in mapping.items():
            if server_name in name:
                return server_id
                
        return None
    
    def _read_output(self):
        """Read and log output from the MCP server process"""
        if self.process:
            output = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
            for line in output.splitlines():
                if line.strip():
                    self.logger.info(f"MCP: {line.strip()}")
    
    def _process_finished(self, exit_code, exit_status):
        """Handle MCP server process finishing"""
        if exit_code != 0:
            self.logger.warning(f"MCP server process exited with code {exit_code}")
        else:
            self.logger.info("MCP server process completed successfully")
    
    def _monitor_status(self):
        """Monitor MCP servers status periodically"""
        while not self._stop_event.is_set():
            try:
                # Get and log status
                status = self.get_status()
                self.logger.debug(f"MCP servers status: {status['status']}")
                
                # Check if all expected servers are running
                expected_servers = ["coordinator", "kde", "code", "data", "network"]
                running_servers = [
                    server_id for server_id, info in status["servers"].items()
                    if info["status"] == "running"
                ]
                
                if status["status"] == "running" and len(running_servers) < len(expected_servers):
                    # Some servers are not running
                    missing = set(expected_servers) - set(running_servers)
                    self.logger.warning(f"Some MCP servers are not running: {', '.join(missing)}")
                    
            except Exception as e:
                self.logger.error(f"Error in status monitoring: {str(e)}")
                
            # Sleep before next check
            for _ in range(30):  # Check every 30 seconds
                if self._stop_event.is_set():
                    break
                time.sleep(1)