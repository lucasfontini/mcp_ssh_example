from mcp.server.fastmcp import FastMCP
import paramiko
import os
from dotenv import load_dotenv
from typing import Optional

# Carrega variáveis do arquivo .env
load_dotenv()

# Inicializa o servidor FastMCP
mcp = FastMCP("MikroTikSSHServer")

# Pega variáveis do .env
MIKROTIK_PORT = int(os.getenv("MIKROTIK_PORT", "22"))
MIKROTIK_USERNAME = os.getenv("MIKROTIK_USERNAME")
MIKROTIK_PASSWORD = os.getenv("MIKROTIK_PASSWORD")

@mcp.tool()
def run_mikrotik_command(command: str, hostname: str) -> str:
    """
    Executa um comando via SSH no MikroTik.
    
    Args:
        command (str): O comando a ser executado.
        hostname (str): O hostname ou IP do MikroTik.
    
    Returns:
        str: Resultado da execução do comando.
    """
    try:
        # Inicializa a conexão SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=hostname,
            port=MIKROTIK_PORT,
            username=MIKROTIK_USERNAME,
            password=MIKROTIK_PASSWORD,
            timeout=10
        )
        
        # Executa o comando
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        # Fecha a conexão SSH
        ssh_client.close()
        
        # Retorna o erro ou o output
        return error if error else output or "Command executed successfully."
    except Exception as e:
        return f"Failed to execute command: {str(e)}"


@mcp.tool()
def add_mikrotik_ip(ip_address: str, interface: str) -> str:
    """
    Adiciona um endereço IP a uma interface do MikroTik.
    
    Args:
        ip_address (str): Endereço IP com a máscara (e.g., '192.168.1.1/24').
        interface (str): Nome da interface (e.g., 'ether1').
    
    Returns:
        str: Resultado da operação.
    """
    command = f"/ip address add address={ip_address} interface={interface}"
    return run_mikrotik_command(command, "192.168.88.1")  # Substitua pelo seu endereço IP do MikroTik


if __name__ == "__main__":
    # Executa o servidor com transporte HTTP streamable
    mcp.run(transport="sse")
