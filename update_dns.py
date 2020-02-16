import click
from google.cloud import dns
import copy
import time
import socket
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

@click.command()
@click.option('--ip', help='ip of the host.')
@click.option('--name', help='nome of host')
def update(ip, name):
    if ip.startswith('eth'):
        ip = get_ip_address(ip)

    client = dns.Client.from_service_account_json('auth.json')
    zones = client.list_zones()
    for zone in zones:
        for record in zone.list_resource_record_sets():
            if record.record_type == "A" and record.name == name:
                if record.rrdatas[0] == ip:
                    print("no change needed")
                    return
                changed_record =zone.resource_record_set(
                    record.name, record.record_type, record.ttl, [ip,])
                changes = zone.changes()
                changes.add_record_set(changed_record)
                changes.delete_record_set(record)
                changes.create()
                while changes.status != 'done':
                    print('Waiting for changes to complete')
                    time.sleep(1)
                    changes.reload()

if __name__ == '__main__':
    update()