"""Kubernetes functions module"""

import logging
import subprocess
import time
from k8s_deploy.modules.tools.helper import Helper 
from k8s_deploy.modules.container_runtime import ContainerRuntime
#from k8s_deploy.modules.k8s.kubeadm import Kubeadm
#from k8s_deploy.modules.k8s.kubelet import Kubelet
#from k8s_deploy.modules.k8s.kubectl import Kubectl
from k8s_deploy.modules.networking import Networking

K8S_LATEST_VERSION_URL='https://dl.k8s.io/release/stable.txt'
KUBELET_RELEASE_VERSION="v0.16.2"
ARCH="amd64"
ENCODING='utf-8'


class Cluster:
    def __init__(self, config_file):
        self.log = logging.getLogger("k8s-log")
        self.hp = Helper(config_file)
        self.config = self.get_config()
        #self.kubeadm = Kubeadm(self.hp)
        #self.kubelet = Kubelet(self.hp)
        #self.kubectl = Kubectl(self.hp)
        self.network = Networking(self.hp)
        self.crt = ContainerRuntime(self.hp)

    def test(self):
        download_dir="~"
        k8s_version = self.get_k8s_version()
        cmd = f"sudo curl -L https://dl.k8s.io/release/{k8s_version}/bin/linux/{ARCH}/kubelet -o {download_dir}/kubelet"
        self.remote_command(cmd)

    def install_cluster(self):
        print("Dummy command to ssh for the first time and establish host authenticity with each node")
        host_response = input("You will need to enter 'yes' if it is the first time connecting: ")
        if host_response == "yes":
            self.establish_host_authenticity()

        self.log.info(f'Installing Cluster with Kubernetes version: {self.get_k8s_version(True)}')
        self.set_current_node_to_controlplane()

        self.log.info('Create controlplane')
        num = 0
        self.init_controlplane(num)


        num_workers = len(self.config['cluster']['workers'])
        logging.debug('Number of worker nodes', num_workers)
        for node_num in range(0, num_workers):
            self.log.info(f"Create worker node: {self.config['cluster']['workers'][node_num]['name']}")
            self.init_worker_node(node_num)

        self.log.info(f'Finished creating cluster with Kubernetes version: {self.get_k8s_version(True)}')

        self.log.info('Adding extras')
        
        self.set_current_node_to_controlplane()
        self.create_alias("k=kubectl")
        self.log.info('Install CNI plugin')
        self.network.install_cni_plugin()

    def set_current_node_to_controlplane(self):
        current_node = {
            'node_category': 'controlplanes',
            'node_num': 0
        }
        self.set_current_node(current_node)

    def set_current_node(self, node):
        self.hp.set_current_node(node)

    def get_current_node(self):
        return self.hp.get_current_node()
        
    def prepare_environment(self):
        self.log.debug('Preparing environment for Kubernetes')
        
        self.apt_update()
        self.disable_swap()
        self.install_dependency_packages()
        self.apt_update()

    def network_prerequisites(self):
        self.log.debug('Networking Prerequisites')
        self.network.network_prerequisites()

    def install_cni_plugin(self):
        self.network.install_cni_plugin()
        
    def setup_container_runtime(self):
        self.log.debug('Setup Container Runtime')
        self.crt.setup_container_runtime()

    def init_controlplane(self, node_num):
        current_node = {
            'node_category': 'controlplanes',
            'node_num': node_num
        }
        self.network_prerequisites()
        self.init_node()

        pod_network_cidr = self.config['network']['pod_network_cidr']
        endpoint = self.config['cluster']['controlplanes'][node_num]['endpoints']['ip']['internal']
        node_name = self.config['cluster']['controlplanes'][node_num]['name']

        cmd = f"sudo kubeadm init --apiserver-advertise-address={endpoint} --pod-network-cidr={pod_network_cidr} --node-name={node_name}"
        self.remote_command(cmd)

        self.make_kube_config()


    def init_worker_node(self, node_num):
        current_node = {
            'node_category': 'workers',
            'node_num': node_num
        }
        self.log.debug('Current node: {current_node}.')

        self.set_current_node(current_node)

        self.log.debug('Initializing worker node: ' + self.get_node_name())
        self.init_node()

        self.log.info('Joining node to cluster')
        self.join_node()

        self.add_worker_node_role()

    def get_node_name(self):
        node = self.get_current_node()
        return self.config['cluster'][node['node_category']][node['node_num']]['name']

    def establish_host_authenticity(self):
        num_cp = len(self.config['cluster']['controlplanes'])
        num_workers = len(self.config['cluster']['workers'])

        for node_num in range(0, num_cp):
            current_node = {
                'node_category': 'controlplanes',
                'node_num': node_num
            }
            self.set_current_node(current_node)
            cmd = "echo first time ssh"
            print(self.remote_command(cmd))

        for node_num in range(0, num_workers):
            current_node = {
                'node_category': 'workers',
                'node_num': node_num
            }
            self.set_current_node(current_node)
            cmd = "echo first time ssh check"
            self.log.debug(self.remote_command(cmd))

    def init_node(self):
        self.set_hostname(self.get_node_name())

        self.log.info('Setup the container runtime.')
        self.setup_container_runtime()
        
        self.log.info('Prepare the environment')
        self.prepare_environment()

        self.log.info('Setup networking prerequisites')
        self.network_prerequisites()

        self.log.info('Install the Kubernetes components.')
        self.install_k8s_components()


    def set_hostname(self, name):
        self.log.debug(f'Set the hostname to: {name}')
        self.queue_command(f'sudo hostnamectl set-hostname {name}')
        self.run_commands()

    def get_node_details(self, node_category, node_num):
        node = self.config['cluster'][node_category][node_num]
        node_details = {
            'name': node['name'],
            'internal_ip': node['endpoints']['ip']['internal'],
            'external_ip': node['endpoints']['ip']['external'],
            'private_hostname': node['endpoints']['hostname']['internal'],
            'public_hostname': node['endpoints']['hostname']['external']
        }
        return node_details


    def make_kube_config(self):
        self.log.debug("Check if the original kube config file exists.")
        result = self.remote_command("test -e $HOME/.kube && echo 1 || echo 0")

        if result:
            self.log.debug("Remove the original kube config file to avoid the installation from hanging")
            self.queue_command("sudo rm -r  $HOME/.kube")
        
        self.queue_command("mkdir -p $HOME/.kube")
        self.queue_command("sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config")
        self.queue_command("sudo chown $(id -u):$(id -g) $HOME/.kube/config")
        self.run_commands()

    def get_join_command(self):
        current_node = self.get_current_node()
        self.set_current_node_to_controlplane()
        self.log.debug('Get join command from controlplane')
        response = self.remote_command("sudo kubeadm token create --print-join-command")
        self.set_current_node(current_node)
        self.log.debug(f'Get join command response: {response}')
        self.config['join_command'] = response.rstrip()
        return response.rstrip()

    def join_node(self):
        self.log.debug('Run the join command to join the node to cluster')
        node_name = self.get_node_name()
        self.config['join_command'] = self.get_join_command()
        self.log.debug("Reset the node")
        self.queue_command("sudo kubeadm reset -f")
        self.queue_command(f"sudo {self.config['join_command']} --node-name {node_name}")
        self.run_commands()

    def add_worker_node_role(self):
        self.log.debug('Label the worker node')
        current_node = self.get_current_node()
        node_name = self.get_node_name()
        
        self.set_current_node_to_controlplane()
        self.queue_command(f"kubectl label node {node_name} node-role.kubernetes.io/worker=worker")
        self.run_commands()

        self.set_current_node(current_node)

    def add_node_name(self, ip, node_name):
        self.queue_command(f'sudo echo "{ip} {node_name}" >> /etc/hosts')
        self.run_commands()

    def install_k8s_components(self):
        self.log.debug('Installing Kubernetes Components')
        download_dir="/usr/local/bin"
        self.install_kubelet(download_dir)
        self.install_kubectl(download_dir)
        self.install_kubeadm(download_dir)


    def get_k8s_version(self, clean=False):
        k8s_version = self.config['cluster']['k8s_version']
        if k8s_version == 'latest':
            if clean:
                return self.get_k8s_latest_version()[1:]
            else:
                return self.get_k8s_latest_version()
        else:
            if clean:
                return k8s_version
            else:
                return f'v{k8s_version}'

    def get_k8s_latest_version(self):
        cmd = subprocess.run(["curl", "-Ls", K8S_LATEST_VERSION_URL], capture_output=True)
        return cmd.stdout.decode(ENCODING)

    def apt_update(self):
        self.log.debug('Update packages index')
        self.queue_command("sudo apt-get update")
        self.run_commands()

    def install_dependency_packages(self):
        self.log.debug('Install dependency packages')
        self.queue_command("sudo apt-get install -y apt-transport-https ca-certificates curl socat conntrack")
        self.run_commands()

    def disable_swap(self):
        self.log.debug('Disabling Swap')
        self.queue_command("sudo swapoff -a")
        self.run_commands()

    def install_kubeadm(self, download_dir):
        k8s_version = self.get_k8s_version()
        CRICTL_VERSION="v1.28.0"
        self.queue_command(f'sudo mkdir -p {download_dir}')
        self.queue_command(f'curl -L "https://github.com/kubernetes-sigs/cri-tools/releases/download/{CRICTL_VERSION}/crictl-{CRICTL_VERSION}-linux-{ARCH}.tar.gz" | sudo tar -C {download_dir} -xz')
        self.queue_command(f"sudo curl -L https://dl.k8s.io/release/{k8s_version}/bin/linux/{ARCH}/kubeadm -o {download_dir}/kubeadm")
        self.queue_command(f"sudo chmod +x {download_dir}/kubeadm")
        self.run_commands()


    def install_kubelet(self, download_dir):
        self.log.debug('Installing kubelet')
        k8s_version = self.get_k8s_version()
        self.queue_command(f"sudo curl -L https://dl.k8s.io/release/{k8s_version}/bin/linux/{ARCH}/kubelet -o {download_dir}/kubelet")
        self.queue_command(f"sudo chmod +x {download_dir}/kubelet")
        self.queue_command(f'curl -sSL "https://raw.githubusercontent.com/kubernetes/release/{KUBELET_RELEASE_VERSION}/cmd/krel/templates/latest/kubelet/kubelet.service" | sed "s:/usr/bin:{download_dir}:g" | sudo tee /etc/systemd/system/kubelet.service')
        self.queue_command('sudo mkdir -p /etc/systemd/system/kubelet.service.d')
        self.queue_command(f'curl -sSL "https://raw.githubusercontent.com/kubernetes/release/{KUBELET_RELEASE_VERSION}/cmd/krel/templates/latest/kubeadm/10-kubeadm.conf" | sed "s:/usr/bin:{download_dir}:g" | sudo tee /etc/systemd/system/kubelet.service.d/10-kubeadm.conf')
        self.queue_command("sudo systemctl enable kubelet.service")
        self.run_commands()

    def install_kubectl(self, download_dir):
        self.log.debug('Installing kubectl')
        k8s_version = self.get_k8s_version()
        self.queue_command(f'curl -LO "https://dl.k8s.io/release/{k8s_version}/bin/linux/amd64/kubectl"')
        self.log.debug('Downloading the checksum for kubectl')
        self.queue_command(f'curl -LO "https://dl.k8s.io/release/{k8s_version}/bin/linux/amd64/kubectl.sha256"')
        self.run_commands()
        self.log.debug('Checksum validation for kubectl')
        result = self.remote_command(f'echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check')
        self.log.debug(f'Result: "{result.rstrip()}"')
        if result.rstrip() == "kubectl: OK":
            self.log.debug('Checksum for kubectl is ok.')
            self.queue_command(f"sudo install -o root -g root -m 0755 kubectl {download_dir}/kubectl")
            self.queue_command("chmod +x kubectl && mkdir -p $HOME/local/bin && mv ./kubectl $HOME/local/bin/kubectl")
        else:
            self.log.debug(f'Checksum for kubectl is not ok: "{result}"')
            self.queue_command(f"sudo install -o root -g root -m 0755 kubectl {download_dir}/kubectl")
            self.queue_command("chmod +x kubectl && mkdir -p $HOME/local/bin && mv ./kubectl $HOME/local/bin/kubectl")
        self.run_commands()

    def create_alias(self, alias):
        self.queue_command(f'sudo echo "alias {alias}" >> $HOME/.bashrc')
        self.queue_command(f'source $HOME/.bashrc')
        self.run_commands()

    def get_config(self):
        return self.hp.config

    def remote_command(self, cmd):
        return self.hp.remote_command(cmd)

    def queue_command(self, cmd):
        return self.hp.queue_command(cmd)

    def run_commands(self):
        return self.hp.run_commands()
