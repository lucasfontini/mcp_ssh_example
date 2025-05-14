from mcp.server.fastmcp import FastMCP
import paramiko
from typing import Optional

mcp = FastMCP("MikroTikSSHServer")

MIKROTIK_HOST = "172.23.45.98"
MIKROTIK_PORT = 22
MIKROTIK_USERNAME = "noc"
MIKROTIK_PASSWORD = "ndvl7Rp#"

@mcp.tool()
def run_mikrotik_command(command: str) -> str:
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=MIKROTIK_HOST,
            port=MIKROTIK_PORT,
            username=MIKROTIK_USERNAME,
            password=MIKROTIK_PASSWORD,
            timeout=10
        )
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        ssh_client.close()
        return error if error else output or "Command executed successfully."
    except Exception as e:
        return f"Failed to execute command: {str(e)}"

@mcp.tool()
def add_mikrotik_ip(ip_address: str, interface: str) -> str:
    """
    Add an IP address to a MikroTik interface.
    
    Args:
        ip_address (str): IP address with subnet (e.g., '192.168.1.1/24').
        interface (str): Interface name (e.g., 'ether1').
    
    Returns:
        str: Result of the operation.
    """
    command = f"/ip address add address={ip_address} interface={interface}"
    return run_mikrotik_command(command)

if __name__ == "__main__":
    mcp.run(transport="stdio")