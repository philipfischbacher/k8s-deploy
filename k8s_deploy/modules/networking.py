"""Networking functions module"""
import logging

NETWORK_PLUGINS = [
    'flannel',
    'calico'
]
ARCH="amd64"

class Networking:
    def __init__(self, helper):
        self.log = logging.getLogger("k8s-log")
        self.hp = helper
        self.config = self.get_config()
        self.cni_plugin = self.config['network']['cni_plugin']['name']

    def install_cni_plugin(self):
        print('Network Plugin Name:', self.config['network']['cni_plugin']['name'])
        if self.check_cni_plugin():
            if self.cni_plugin == 'flannel':
                self.install_flannel()
            else:
                self.log.warning('Network Plugin is not defined.')

        else:
            available_plugins = ','.join(NETWORK_PLUGINS)
            self.log.error(f'Sorry, cannot install the {self.cni_plugin} network plugin. Please choose from the following network plugins: {available_plugins}')

    def check_cni_plugin(self):
        self.log.debug(f'CNI Plugin: {self.cni_plugin}')
        if self.cni_plugin in NETWORK_PLUGINS:
            return True
        else:
            return False

    def network_prerequisites(self):
        self.log.info('Forwarding IPv4 and letting iptables see bridged traffic')
        cmd="""
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
"""
        self.remote_command(cmd)
        cmd = "sudo modprobe overlay"
        self.remote_command(cmd)
        cmd = "sudo modprobe br_netfilter"
        self.remote_command(cmd)
        self.log.info('sysctl params required by setup, params persist across reboots')
        cmd="""
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
"""
        self.remote_command(cmd)

        self.log.info('Apply sysctl params without reboot')
        cmd = "sudo sysctl --system"
        self.remote_command(cmd)
        self.log.info('Install Loopback plugin.')
        self.install_loopback()

    def install_flannel(self):
        self.log.info('Install flannel network plugin')
        cmd = "kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml"
        self.remote_command(cmd)

    def install_calico(self):
        print('Install calico network plugin')
        cmd = "kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/tigera-operator.yaml"
        self.remote_command(cmd)
        cmd = "kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/custom-resources.yaml"
        self.remote_command(cmd)

    def install_loopback(self):
        version = 'v0.9.1'
        cmd = f'sudo wget -O cni-plugins.tar.gz https://github.com/containernetworking/plugins/releases/download/{version}/cni-plugins-linux-{ARCH}-{version}.tgz'
        self.remote_command(cmd)
        cmd = 'sudo mkdir -p /opt/cni/bin && sudo tar -C /opt/cni/bin -xzf cni-plugins.tar.gz'
        self.remote_command(cmd)

    def get_config(self):
        return self.hp.get_config()

    def remote_command(self, cmd):
        self.hp.remote_command(cmd)
