import os
import paramiko
from pathlib import Path
from dotenv import load_dotenv

class RMClient:
    """
    Transport layer for reMarkable. 
    Handles SSH/SFTP connections and basic device control.
    """
    
    BASE_PATH = "/home/root/.local/share/remarkable/xochitl"

    def __init__(self):
        # Locate .env relative to this file (src/ssh_client.py -> ../.env)
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)

        self.ip = os.getenv("RM_IP")
        self.password = os.getenv("RM_PASSWORD")
        
        if not self.ip or not self.password:
            raise ValueError("RM_IP or RM_PASSWORD not found in .env file")

        self.ssh = None
        self.sftp = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Establish SSH and SFTP connections."""
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.ip, username="root", password=self.password, timeout=10)
        self.sftp = self.ssh.open_sftp()

    def close(self):
        """Close connections."""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()

    def execute(self, command):
        """Run a shell command and return (exit_status, stdout, stderr)."""
        stdin, stdout, stderr = self.ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        return exit_status, stdout.read().decode().strip(), stderr.read().decode().strip()

    def upload(self, local_path, remote_filename):
        """Upload a file to the xochitl directory."""
        remote_path = f"{self.BASE_PATH}/{remote_filename}"
        self.sftp.put(local_path, remote_path)

    def download(self, remote_filename, local_path):
        """Download a file from the xochitl directory."""
        remote_path = f"{self.BASE_PATH}/{remote_filename}"
        self.sftp.get(remote_path, local_path)

    def list_dir(self, remote_subfolder=""):
        """List files in the xochitl directory or a subfolder."""
        path = self.BASE_PATH
        if remote_subfolder:
            path = f"{self.BASE_PATH}/{remote_subfolder}"
        try:
            return self.sftp.listdir(path)
        except IOError:
            return []

    def mkdir(self, folder_name):
        """Create a directory in the xochitl storage."""
        self.execute(f"mkdir -p {self.BASE_PATH}/{folder_name}")

    def stop_xochitl(self):
        """Stop the tablet UI."""
        self.execute("systemctl stop xochitl")

    def start_xochitl(self):
        """Start the tablet UI."""
        self.execute("systemctl start xochitl")

    def is_ui_running(self):
        """Check if xochitl is currently active."""
        status, out, err = self.execute("systemctl is-active xochitl")
        return out == "active"
