from scapy.all import ARP, Ether, srp

def network_scan(target_ip):
    print(f"Scanning network: {target_ip}...\n")

    arp = ARP(pdst=target_ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=2, verbose=0)[0]

    devices = []
    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})

    print("Available devices in the network:")
    print("IP" + " "*18 + "MAC")
    print("-"*40)
    for device in devices:
        print(f"{device['ip']:20} {device['mac']}")

if __name__ == "__main__":
    target_ip_range = "192.168.1.0/24"
    network_scan(target_ip_range)
