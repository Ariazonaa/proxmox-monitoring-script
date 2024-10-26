import requests
import json
import logging
from datetime import datetime, timedelta
import time
import urllib3

# Disable warnings for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='proxmox_monitor.log',
                    filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(console)

# Proxmox connection details
PROXMOX_HOST = 'https://proxmox.example.com'
PROXMOX_TOKEN = 'PVEAPIToken=YOUR_PROXMOX_TOKEN'

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# Enhanced status codes
STATUS_CODES = {
    'running': {
        'title': '🟢 Virtual Machine Running',
        'description': 'The virtual machine is in an operational state.',
        'color': 0x00FF00  # Green
    },
    'stopped': {
        'title': '🔴 Virtual Machine Stopped',
        'description': 'The virtual machine has been forcibly stopped.',
        'color': 0xFF0000  # Red
    },
    'paused': {
        'title': '🟠 Virtual Machine Paused',
        'description': 'The operation of the virtual machine is temporarily suspended.',
        'color': 0xFFA500  # Orange
    },
    'suspended': {
        'title': '⚪ Virtual Machine Suspended',
        'description': 'The virtual machine is in a suspended state.',
        'color': 0x808080  # Gray
    },
    'starting': {
        'title': '🔵 Virtual Machine Starting',
        'description': 'The virtual machine is currently being initialized.',
        'color': 0x00FFFF  # Cyan
    },
    'stopping': {
        'title': '🔴 Virtual Machine Stopping',
        'description': 'The virtual machine is being properly shut down.',
        'color': 0x800000  # Dark Red
    },
    'shutdown': {
        'title': '🟡 Virtual Machine Shutting Down',
        'description': 'The virtual machine is undergoing a shutdown process.',
        'color': 0xFFFF00  # Yellow
    },
    'migrating': {
        'title': '🔷 Virtual Machine Migrating',
        'description': 'The virtual machine is being migrated to another host.',
        'color': 0x800080  # Purple
    },
    'unknown': {
        'title': '⚫ Unknown Status',
        'description': 'The current status of the virtual machine is unknown.',
        'color': 0x000000  # Black
    },
    'error': {
        'title': '❌ Error State',
        'description': 'An unexpected error has occurred.',
        'color': 0xFF00FF  # Magenta
    },
    'locked': {
        'title': '🔒 Virtual Machine Locked',
        'description': 'The virtual machine is currently locked for operations.',
        'color': 0x808000  # Olive
    },
    'backup': {
        'title': '🔵 Backup in Progress',
        'description': 'A backup of the virtual machine is being created.',
        'color': 0x0000FF  # Blue
    },
    'restore': {
        'title': '🔷 Restore in Progress',
        'description': 'A backup is being restored to the virtual machine.',
        'color': 0x8A2BE2  # Blue Violet
    },
    'snapshot': {
        'title': '📸 Snapshot in Progress',
        'description': 'A snapshot of the virtual machine is being created.',
        'color': 0xADD8E6  # Light Blue
    },
    'clone': {
        'title': '🌀 Virtual Machine Cloning',
        'description': 'The virtual machine is being cloned.',
        'color': 0x008080  # Teal
    },
    'rollback': {
        'title': '↺ Rollback in Progress',
        'description': 'The virtual machine is being reverted to a previous state.',
        'color': 0xFF4500  # Orange Red
    },
    'provisioning': {
        'title': '🛠️ Provisioning in Progress',
        'description': 'The virtual machine is being provisioned.',
        'color': 0x7FFF00  # Spring Green
    }
}

# Dictionary to store the last known status of each VM
last_known_status = {}

def get_proxmox_data(endpoint):
    url = f"{PROXMOX_HOST}/api2/json/{endpoint}"
    headers = {"Authorization": PROXMOX_TOKEN}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        logging.debug(f"Response from {url}: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving data from {url}: {e}")
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
            logging.error("401 Unauthorized: Please check the API token and permissions.")
        return None

def format_uptime(seconds):
    delta = timedelta(seconds=seconds)
    days = delta.days
    years, days = divmod(days, 365)
    weeks, days = divmod(days, 7)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return (
        f"{years} years, {weeks} weeks, {days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        if years > 0 else
        f"{weeks} weeks, {days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        if weeks > 0 else
        f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        if days > 0 else
        f"{hours} hours, {minutes} minutes, {seconds} seconds"
        if hours > 0 else
        f"{minutes} minutes, {seconds} seconds"
        if minutes > 0 else
        f"{seconds} seconds"
    )

def send_discord_embed(vm, node_info):
    status_info = STATUS_CODES.get(vm['status'], STATUS_CODES['unknown'])
    embed = {
        "title": f"{status_info['title']} - {vm['name']}",
        "description": (
            f"**💻 VM Name:** {vm['name']}\n"
            f"**🆔 VM ID:** {vm['vmid']}\n"
            f"**📍 Node:** {vm['node']}\n"
            f"**⚙️ Status:** {status_info['description']}\n\n"
            f"**📊 Resource Usage (VM):**\n"
            f"- **🧠 CPU Usage:** {vm['cpu']}%\n"
            f"- **💿 Memory Usage:** {vm['mem']} MB/{vm['maxmem']} MB ({(vm['mem'] / vm['maxmem']) * 100:.2f}%)\n"
            f"- **⏱️ Uptime:** {format_uptime(vm['uptime'])}\n\n"
            f"**💄 Node Information:**\n"
            f"- **💽 Memory Usage (Node):** {node_info['used_memory']} MB/{node_info['total_memory']} MB ({(node_info['used_memory'] / node_info['total_memory']) * 100:.2f}%)"
        ),
        "thumbnail": {
            "url": "https://cdn.discordapp.com/emojis/1273407068186873977.gif?size=44&quality=lossless"
        },
        "color": status_info['color'],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "Powered by Ariazonaa",
            "icon_url": "https://www.svgrepo.com/show/331666/virtual-machine.svg"
        }
    }
    
    data = {
        "embeds": [embed]
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        response.raise_for_status()
        logging.info(f"Discord message for VM {vm['vmid']} sent successfully, status code {response.status_code}.")
    except requests.exceptions.RequestException as error:
        logging.error(f"Error sending Discord message for VM {vm['vmid']}: {error}")

def check_vms():
    nodes = get_proxmox_data("nodes")
    if not nodes:
        logging.error("Could not retrieve nodes.")
        return

    for node in nodes['data']:
        node_name = node['node']
        node_status = get_proxmox_data(f"nodes/{node_name}/status")
        if not node_status:
            logging.error(f"Could not retrieve status for node {node_name}.")
            continue
        
        node_cpu_usage = round(node_status['data'].get('cpu', 0) * 100, 2)
        node_used_memory = node_status['data'].get('memory', {}).get('used', 0) // (1024 * 1024)  # Convert to MB
        node_total_memory = node_status['data'].get('memory', {}).get('total', 1) // (1024 * 1024)  # Convert to MB

        qemu_vms = get_proxmox_data(f"nodes/{node_name}/qemu")
        if qemu_vms:
            for vm in qemu_vms['data']:
                vm_id = vm['vmid']
                if 9000 <= vm_id < 10000:
                    logging.info(f"VM {vm_id} is being ignored.")
                    continue

                vm_status = get_proxmox_data(f"nodes/{node_name}/qemu/{vm_id}/status/current")
                if vm_status:
                    status = vm_status['data'].get('qmpstatus', vm_status['data'].get('status'))
                    lock = vm_status['data'].get('lock')
                    name = vm['name']
                    vm_key = f"{node_name}-{vm_id}"

                    cpu_usage = round(vm_status['data'].get('cpu', 0) * 100, 2)
                    memory_usage = vm_status['data'].get('mem', 0)
                    max_memory = vm_status['data'].get('maxmem', 1)
                    uptime = vm_status['data'].get('uptime', 0)

                    logging.debug(f"VM {vm_id} on node {node_name}: Status {status}, Lock {lock}")

                    if lock:
                        if lock == 'backup':
                            status = 'backup'
                        elif lock == 'snapshot':
                            status = 'snapshot'
                        elif lock == 'clone':
                            status = 'clone'
                        elif lock == 'migrate':
                            status = 'migrating'
                        elif lock == 'rollback':
                            status = 'rollback'
                        elif lock == 'suspend':
                            status = 'suspended'
                        elif lock == 'create':
                            status = 'restore'
                        else:
                            status = 'locked'

                    if vm_key not in last_known_status or last_known_status[vm_key] != status:
                        last_known_status[vm_key] = status
                        send_discord_embed({
                            'vmid': vm_id,
                            'name': name,
                            'status': status,
                            'node': node_name,
                            'cpu': cpu_usage,
                            'mem': memory_usage // (1024 * 1024),  # Convert to MB
                            'maxmem': max_memory // (1024 * 1024),  # Convert to MB
                            'uptime': uptime
                        }, {
                            'cpu': node_cpu_usage,
                            'used_memory': node_used_memory,
                            'total_memory': node_total_memory
                        })
                    else:
                        logging.debug(f"No change for VM {vm_id} on node {node_name}: Status remains {status}")

def main():
    while True:
        try:
            check_vms()
            time.sleep(5)  # Wait 5 seconds before the next check
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
