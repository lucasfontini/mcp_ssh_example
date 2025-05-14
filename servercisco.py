from mcp.server.fastmcp import FastMCP
import paramiko
import re
import time
from typing import Optional, List, Dict, Any

mcp = FastMCP("CiscoSSHServer")

CISCO_HOST = "ios-xe-mgmt.cisco.com"  # Replace with your Cisco device IP
CISCO_PORT = 22
CISCO_USERNAME = "admin"  # Replace with your Cisco username
CISCO_PASSWORD = "C1sco12345"  # Replace with your Cisco password
CISCO_ENABLE_PASSWORD = "C1sco12345"  # Enable password, if different
TIMEOUT = 10

def get_ssh_connection():
    """
    Establish and return an SSH connection to the Cisco device.
    
    Returns:
        tuple: (ssh_client, shell) - SSH client and shell instances
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname=CISCO_HOST,
        port=CISCO_PORT,
        username=CISCO_USERNAME,
        password=CISCO_PASSWORD,
        timeout=TIMEOUT,
        look_for_keys=False,
        allow_agent=False
    )
    
    shell = ssh_client.invoke_shell()
    # Wait for the prompt
    time.sleep(1)
    return ssh_client, shell

def execute_command(shell, command: str, wait_time: float = 1) -> str:
    """
    Execute a command on the Cisco device and return the output.
    
    Args:
        shell: The SSH shell
        command: Command to execute
        wait_time: Time to wait for command output
        
    Returns:
        str: Command output
    """
    shell.send(f"{command}\n")
    time.sleep(wait_time)
    
    output = ""
    while shell.recv_ready():
        output += shell.recv(65535).decode('utf-8')
    
    return output

@mcp.tool()
def run_cisco_command(command: str) -> str:
    """
    Execute a single command on a Cisco device via SSH.

    Args:
        command (str): Command to execute (e.g., 'show version').

    Returns:
        str: Command output or error message.
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Send command
        output = execute_command(shell, command)
        
        ssh_client.close()
        return output or "Command executed successfully."
    except Exception as e:
        return f"Failed to execute command: {str(e)}"

@mcp.tool()
def add_cisco_ip(ip_address: str, interface: str) -> str:
    """
    Add an IP address to a Cisco interface.

    Args:
        ip_address (str): IP address with subnet (e.g., '192.168.1.1/24').
        interface (str): Interface name (e.g., 'GigabitEthernet0/0').

    Returns:
        str: Result of the operation.
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Parse IP address
        if '/' in ip_address:
            ip, subnet = ip_address.split('/')
            netmask = subnet_to_netmask(subnet)
        else:
            # Assume it's a standalone IP with netmask format
            ip = ip_address
            netmask = "255.255.255.0"  # Default netmask
        
        # Enter config mode
        execute_command(shell, "configure terminal")
        
        # Configure interface
        execute_command(shell, f"interface {interface}")
        execute_command(shell, f"ip address {ip} {netmask}")
        execute_command(shell, "no shutdown")
        
        # Exit config mode and save
        execute_command(shell, "end")
        output = execute_command(shell, "write memory")
        
        ssh_client.close()
        return f"IP {ip_address} added to interface {interface}. {output}"
    except Exception as e:
        return f"Failed to add IP address: {str(e)}"

def subnet_to_netmask(subnet: str) -> str:
    """
    Convert CIDR subnet (e.g., '24') to netmask (e.g., '255.255.255.0').

    Args:
        subnet (str): CIDR notation (e.g., '24').

    Returns:
        str: Subnet mask (e.g., '255.255.255.0').
    """
    subnet = int(subnet)
    mask = (0xffffffff << (32 - subnet)) & 0xffffffff
    return f"{(mask >> 24) & 255}.{(mask >> 16) & 255}.{(mask >> 8) & 255}.{mask & 255}"

@mcp.tool()
def list_cisco_interfaces() -> List[Dict[str, str]]:
    """
    List all interfaces on the Cisco device with their status.
    
    Returns:
        List[Dict[str, str]]: List of dictionaries containing interface details
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Get interface list
        output = execute_command(shell, "show ip interface brief", wait_time=2)
        
        interfaces = []
        # Parse output - this regex pattern may need adjustment based on actual output format
        pattern = r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)"
        
        for line in output.splitlines():
            match = re.search(pattern, line)
            if match and "Interface" not in line:  # Skip header line
                interface = {
                    "name": match.group(1),
                    "ip_address": match.group(2),
                    "ok": match.group(3),
                    "method": match.group(4),
                    "status": match.group(5),
                    "protocol": match.group(6)
                }
                interfaces.append(interface)
        
        ssh_client.close()
        return interfaces
    except Exception as e:
        return [{"error": f"Failed to list interfaces: {str(e)}"}]

@mcp.tool()
def get_interface_details(interface_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific interface.
    
    Args:
        interface_name (str): Name of the interface (e.g., 'GigabitEthernet0/0')
        
    Returns:
        Dict[str, Any]: Dictionary containing interface details
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Get interface details
        output = execute_command(shell, f"show interfaces {interface_name}", wait_time=2)
        
        # Parse basic info
        details = {
            "name": interface_name,
            "raw_output": output
        }
        
        # Extract key information using regex
        mac_match = re.search(r"Hardware.+address is (\S+)", output)
        if mac_match:
            details["mac_address"] = mac_match.group(1)
            
        mtu_match = re.search(r"MTU (\d+) bytes", output)
        if mtu_match:
            details["mtu"] = int(mtu_match.group(1))
            
        bw_match = re.search(r"BW (\d+) Kbit", output)
        if bw_match:
            details["bandwidth"] = int(bw_match.group(1))
            
        desc_match = re.search(r"Description: (.+)", output)
        if desc_match:
            details["description"] = desc_match.group(1).strip()
            
        # Extract packet statistics
        in_packets_match = re.search(r"(\d+) packets input", output)
        if in_packets_match:
            details["packets_input"] = int(in_packets_match.group(1))
            
        out_packets_match = re.search(r"(\d+) packets output", output)
        if out_packets_match:
            details["packets_output"] = int(out_packets_match.group(1))
        
        ssh_client.close()
        return details
    except Exception as e:
        return {"error": f"Failed to get interface details: {str(e)}"}

@mcp.tool()
def set_interface_description(interface_name: str, description: str) -> str:
    """
    Set a description for a specified interface.
    
    Args:
        interface_name (str): Name of the interface (e.g., 'GigabitEthernet0/0')
        description (str): Description to set for the interface
        
    Returns:
        str: Result of the operation
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Enter config mode
        execute_command(shell, "configure terminal")
        
        # Configure interface description
        execute_command(shell, f"interface {interface_name}")
        execute_command(shell, f"description {description}")
        
        # Exit config mode and save
        execute_command(shell, "end")
        output = execute_command(shell, "write memory")
        
        ssh_client.close()
        return f"Description for interface {interface_name} set to '{description}'. {output}"
    except Exception as e:
        return f"Failed to set interface description: {str(e)}"

@mcp.tool()
def set_interface_status(interface_name: str, status: bool) -> str:
    """
    Enable or disable a specified interface.
    
    Args:
        interface_name (str): Name of the interface (e.g., 'GigabitEthernet0/0')
        status (bool): True to enable, False to disable
        
    Returns:
        str: Result of the operation
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Enter config mode
        execute_command(shell, "configure terminal")
        
        # Configure interface status
        execute_command(shell, f"interface {interface_name}")
        
        if status:
            execute_command(shell, "no shutdown")
            status_text = "enabled"
        else:
            execute_command(shell, "shutdown")
            status_text = "disabled"
        
        # Exit config mode and save
        execute_command(shell, "end")
        output = execute_command(shell, "write memory")
        
        ssh_client.close()
        return f"Interface {interface_name} {status_text}. {output}"
    except Exception as e:
        return f"Failed to set interface status: {str(e)}"

@mcp.tool()
def configure_switchport(interface_name: str, mode: str, vlan: Optional[int] = None) -> str:
    """
    Configure a switchport interface (access or trunk mode).
    
    Args:
        interface_name (str): Name of the interface (e.g., 'GigabitEthernet0/0')
        mode (str): 'access' or 'trunk'
        vlan (Optional[int]): VLAN ID for access mode
        
    Returns:
        str: Result of the operation
    """
    if mode not in ['access', 'trunk']:
        return "Error: Mode must be 'access' or 'trunk'"
    
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Enter config mode
        execute_command(shell, "configure terminal")
        
        # Configure switchport
        execute_command(shell, f"interface {interface_name}")
        execute_command(shell, "switchport")
        execute_command(shell, f"switchport mode {mode}")
        
        if mode == 'access' and vlan is not None:
            execute_command(shell, f"switchport access vlan {vlan}")
        
        # Exit config mode and save
        execute_command(shell, "end")
        output = execute_command(shell, "write memory")
        
        ssh_client.close()
        
        if mode == 'access' and vlan is not None:
            return f"Interface {interface_name} configured as {mode} port with VLAN {vlan}. {output}"
        else:
            return f"Interface {interface_name} configured as {mode} port. {output}"
    except Exception as e:
        return f"Failed to configure switchport: {str(e)}"

@mcp.tool()
def backup_running_config(filename: Optional[str] = None) -> str:
    """
    Backup the running configuration of the Cisco device.
    
    Args:
        filename (Optional[str]): Filename to save the configuration
        
    Returns:
        str: Configuration content or error message
    """
    try:
        ssh_client, shell = get_ssh_connection()
        
        # Get running config
        output = execute_command(shell, "show running-config", wait_time=5)
        
        ssh_client.close()
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(output)
                return f"Configuration saved to {filename}"
            except Exception as e:
                return f"Failed to save configuration to file: {str(e)}\n\n{output}"
        else:
            return output
    except Exception as e:
        return f"Failed to backup configuration: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")