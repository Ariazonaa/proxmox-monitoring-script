
# Proxmox Monitoring Script

This Python script monitors the status of virtual machines (VMs) on a Proxmox server and sends notifications to a Discord channel whenever a VM's status changes. Please note that some features might not work as expected, as the script is still under development.

## Features

- **Proxmox Integration**: Communicates with a Proxmox server to retrieve the current status of VMs.
- **Discord Notifications**: Sends detailed notifications to a Discord channel to inform about status changes.
- **Advanced Status Monitoring**: Supports various VM statuses such as "running," "stopped," "paused," "suspended," "backup," and "restore."
- **Logging**: Logs all activities and errors in a log file for easy troubleshooting.

## Requirements

- Python 3.x
- `requests` library

## Installation

Install the required Python packages:
   ```bash
   pip install requests
   ```

## Configuration

- **Proxmox Connection Data**: Update the `PROXMOX_HOST` and `PROXMOX_TOKEN` variables with your Proxmox server connection details.
- **Discord Webhook URL**: Set the `WEBHOOK_URL` variable to your Discord webhook URL.

## Usage

Run the script with:

```bash
python main.py
```

The script will run continuously and check the status of the VMs at regular intervals.

## License

This project is licensed under the GNU General Public License (GPL). This means you are free to use, modify, and distribute the source code, as long as all derived works are also published under the GPL. For more information, see the `LICENSE` file.

## Security Notes

- Ensure that your Proxmox API token has the necessary permissions and is kept secure.
- Make sure the connection to your Proxmox server is secure, especially if you use `verify=False` in requests.

## Note

This project is still in development, and some features may not work as expected. I am continuously working to improve the script and welcome feedback and suggestions.

