"""Networking functions module"""

from helper as Hp

def install_networking():
    print('Setup Networking')
    print('Forwarding IPv4 and letting iptables see bridged traffic')
    cmd="""
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl params required by setup, params persist across reboots
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
"""

def getConfig(section, key):
    return Hp.getConfig(section, key)

def remote_command(cmd):
    Hp.remote_command(cmd)

