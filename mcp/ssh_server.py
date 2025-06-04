from fastmcp import FastMCP
import os 
import paramiko
from dotenv import load_dotenv

load_dotenv()



servidor_mcp = FastMCP('mcp-ssh')
@servidor_mcp.tool()

async def run_command(command: str) -> str:
    """Executes a command on device via SSH.

    Args:
        command (str): The command to execute on  device 

    Returns:
        str: The command output, error message, or success message.
    """

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname="sandbox-iosxr-1.cisco.com",
        port=22,
        username="admin",
        password="C1sco12345"
    )

    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8')
    print(output)
    error = stderr.read().decode('utf-8')
    ssh_client.close()
    return error if error else output or "Command executed successfully."




if __name__ == "__main__":
   servidor_mcp.run(transport='sse', port=8000)