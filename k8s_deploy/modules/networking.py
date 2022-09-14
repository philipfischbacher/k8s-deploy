"""Networking functions module"""

NETWORK_PLUGINS = [
    'flannel',
    'calico'
]

class Networking:
    def __init__(self, helper):
        self.hp = helper
        self.config = self.get_config()
        print('Config:', self.config)
        print('Network Plugin Name:', self.config['network']['cni_plugin']['name'])
        self.cni_plugin = self.config['network']['cni_plugin']['name']

    def install_cni_plugin(self):
        if self.check_cni_plugin():

            match self.cni_plugin:
                case 'flannel':
                    self.install_flannel()
                case _:
                    print('Network Plugin is not defined.')

        else:
            print('Sorry, cannot install the %s network plugin.' % self.cni_plugin)
            print('Please choose from the following network plugins:')
            for plugin in NETWORK_PLUGINS:
                print(plugin)

    def check_cni_plugin(self):
        print('CNI Plugin:', self.cni_plugin)
        print('Available CNI Plugins:', self.cni_plugin)
        if self.cni_plugin in NETWORK_PLUGINS:
            return True
        else:
            return False

    def network_prerequisites(self):
        print('Forwarding IPv4 and letting iptables see bridged traffic')
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
        print('sysctl params required by setup, params persist across reboots')
        cmd="""
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
"""
        self.remote_command(cmd)

        print('Apply sysctl params without reboot')
        cmd = "sudo sysctl --system"
        self.remote_command(cmd)

    def install_flannel(self):
        print('Install flannel network plugin')
        cmd = "kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml"
        self.remote_command(cmd)

    def install_calico(self):
        print('Install calico network plugin')
        cmd = "kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/tigera-operator.yaml"
        self.remote_command(cmd)
        cmd = "kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.1/manifests/custom-resources.yaml"
        self.remote_command(cmd)


    def get_config(self):
        return self.hp.get_config()

    def remote_command(self, cmd):
        self.hp.remote_command(cmd)
