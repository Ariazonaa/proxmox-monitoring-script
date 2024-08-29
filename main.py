import requests
import json
import logging
from datetime import datetime
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

# Proxmox connection data
PROXMOX_HOST = 'https://xxxx.xxx.xxx'
PROXMOX_TOKEN = 'PVEAPIToken=xxx@pam!xxxxxx=xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxxxxxxxxxx'

# Discord Webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/xxxxxxxxxxxxxxxxxxxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Extended status codes
STATUS_CODES = {
    'running': {
        'title': 'VM Running',
        'description': 'The virtual machine is ready.',
        'color': 0x00FF00  # Green
    },
    'stopped': {
        'title': 'VM Stopped',
        'description': 'The server is being forcibly stopped.',
        'color': 0xFF0000  # Red
    },
    'paused': {
        'title': 'VM Paused',
        'description': 'The VM is currently paused.',
        'color': 0xFFA500  # Orange
    },
    'suspended': {
        'title': 'VM Suspended',
        'description': 'The VM is in a suspended state.',
        'color': 0x808080  # Gray
    },
    'backup': {
        'title': 'Backup in Progress',
        'description': 'Backup is being created.',
        'color': 0x0000FF  # Blue
    },
    'restore': {
        'title': 'Restoring Backup',
        'description': 'Backup is being restored.',
        'color': 0x800080  # Purple
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
            logging.error("401 Unauthorized: Check the API token and permissions.")
        return None

def send_discord_embed(vm):
    status_info = STATUS_CODES.get(vm['status'], STATUS_CODES['unknown'])
    embed = {
        "title": status_info['title'],
        "description": f"Hostname: {vm['name']}\nStatus: {status_info['description']}",
        "color": status_info['color'],
        "timestamp": datetime.utcnow().isoformat()
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
        qemu_vms = get_proxmox_data(f"nodes/{node_name}/qemu")
        if qemu_vms:
            for vm in qemu_vms['data']:
                vm_id = vm['vmid']
                if 9000 <= vm_id < 10000:
                    logging.info(f"VM {vm_id} is ignored.")
                    continue

                vm_status = get_proxmox_data(f"nodes/{node_name}/qemu/{vm_id}/status/current")
                if vm_status:
                    status = vm_status['data'].get('qmpstatus', vm_status['data'].get('status'))
                    lock = vm_status['data'].get('lock')
                    name = vm['name']
                    vm_key = f"{node_name}-{vm_id}"

                    logging.debug(f"VM {vm_id} on node {node_name}: Status {status}, Lock {lock}")

                    # Check if a restore operation is running
                    if status == 'stopped' and lock == 'create':
                        status = 'restore'
                    
                    # Check if a backup is being created
                    if lock == 'backup':
                        status = 'backup'

                    if vm_key not in last_known_status or last_known_status[vm_key] != status:
                        last_known_status[vm_key] = status
                        send_discord_embed({
                            'vmid': vm_id,
                            'name': name,
                            'status': status
                        })
                    else:
                        logging.debug(f"No change for VM {vm_id} on node {node_name}: Status remains {status}")

def main():
    while True:
        try:
            check_vms()
            time.sleep(5)  # Wait 5 seconds until the next check
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
