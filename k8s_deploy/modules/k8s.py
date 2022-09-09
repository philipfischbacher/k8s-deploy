"""Kubernetes functions module"""

import subprocess
import time
from k8s_deploy.modules.helper import Helper 
from k8s_deploy.modules.container_runtime import ContainerRuntime

K8S_LATEST_VERSION_URL='https://dl.k8s.io/release/stable.txt'
ENCODING='utf-8'


class K8S_Cluster:
    def __init__(self, config_file):
        self.hp = Helper(config_file)
        self.config = self.get_config()

    def install_cluster(self):
        k8s_version = self.get_k8s_version()
        print('Installing Cluster with Kubernetes version: ' + k8s_version)
        self.set_current_node_to_controlplane()

        print('Create controlplane')
        num = 0
        self.init_controlplane(num)

        workers = len(self.config['cluster']['workers'])
        print('Number of worker nodes', workers)
        for node_num in range(0, workers):
            if node_num == 0:
                print('Create worker node:', self.config['cluster']['workers'][node_num]['name'])
                self.init_worker_node(node_num)

        print('Finished creating cluster with Kubernetes version: ' + k8s_version)

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
        print('Update packages index')
        self.apt_update()

        print('Disabling Swap')
        self.disable_swap()

        print('Install dependency packages')
        self.install_dependency_packages()
        self.add_google_cloud_pub_key()

        print('Networking Prerequisites')
        self.networking_prerequisites()

        print('Update packages index')
        self.apt_update()

    def networking_prerequisites(self):
        print('Forwarding IPv4 and letting iptables see bridged traffic')
        cmd="""
cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF
        """
        self.remote_command(cmd)

        cmd = "sudo modprobe overlay"
        self.remote_command(cmd)
        
        cmd = "sudo modprobe br_netfilter"
        self.remote_command(cmd)

        cmd="""
cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF
            """
        self.remote_command(cmd)

        cmd = "sudo sysctl --system"
        self.remote_command(cmd)

        
    def setup_container_runtime(self):
        crt = ContainerRuntime(self.hp)
        crt.setup_container_runtime()

    def init_controlplane(self, node_num):
        
        self.init_node('controlplanes', node_num)

        pod_network_cidr = self.config['network']['pod_network_cidr']
        endpoint = self.config['cluster']['controlplanes'][node_num]['endpoints']['ip']['internal']
        node_name = self.config['cluster']['controlplanes'][node_num]['name']

        cmd = f"sudo kubeadm init --apiserver-advertise-address={endpoint} --pod-network-cidr={pod_network_cidr} --node-name={node_name}"
        self.remote_command(cmd)

        self.make_kube_config()

    def init_worker_node(self, node_num):
        node_name = self.config['cluster']['workers'][node_num]['name']
        print('Initializing worker node: ' + node_name)
        self.init_node('workers', node_num)

        #internal_ip = self.config['cluster']['workers'][node_num]['endpoints']['ip']['internal']
        node_name = self.config['cluster']['workers'][node_num]['name']
        print('Joining node to cluster')
        self.join_worker_node(node_name)

        self.add_worker_node_role(node_name)

    def init_node(self, category, node_num):
        #print(self.get_node_details(category, node_num))
        current_node = {
            'node_category': category,
            'node_num': node_num
        }
        self.set_current_node(current_node)

        print('Setup Container Runtime')
        self.setup_container_runtime()
        
        print('Preparing environment for Kubernetes')
        self.prepare_environment()

        print('Setup networking prerequisites')
        self.networking_prerequisites()

        print('Installing Kubernetes Components')
        self.install_k8s_components()



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
        cmd = "mkdir -p $HOME/.kube"
        self.remote_command(cmd)

        cmd = "sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config"
        self.remote_command(cmd)

        cmd = "sudo chown $(id -u):$(id -g) $HOME/.kube/config"
        result = self.remote_command(cmd)



    def config_join_command(self):
        current_node = self.get_current_node()
        self.set_current_node_to_controlplane()
        print('Get join command from controlplane')
        cmd = "sudo kubeadm token create --print-join-command"
        self.config['join_command'] = "sudo " + self.remote_command(cmd).rstrip()
        self.set_current_node(current_node)

    def join_worker_node(self, node_name):
        print('Run the join command to join the node to cluster')
        self.config_join_command()
        cmd = self.config['join_command'] + f" --node-name {node_name}"
        print("Display full join command:", cmd)
        self.remote_command(cmd)
        time.sleep(30)

    def add_worker_node_role(self, node_name):
        print ('Label the worker node')
        current_node = self.get_current_node()
        self.set_current_node_to_controlplane()
        
        cmd = f"kubectl label node {node_name} node-role.kubernetes.io/worker=worker"
        self.remote_command(cmd)

        self.set_current_node(current_node)

    def add_node_name(self, ip, node_name):
        cmd = f"sudo echo \"{ip}  {node_name}\" >> /etc/hosts"
        self.remote_command(cmd)

    def install_k8s_components(self):
        print('Installing kubeadm')
        self.install_kubeadm()

        print('Installing kubelet')
        self.install_kubelet()

        print('Installing kubectl')
        self.install_kubectl()


    def get_k8s_version(self):
        k8s_version = self.config['cluster']['k8s_version']
        if k8s_version == 'latest':
            return self.get_k8s_latest_version()[1:]
        else:
            return k8s_version
            

    def get_k8s_latest_version(self):
        cmd = subprocess.run(["curl", "-Ls", K8S_LATEST_VERSION_URL], capture_output=True)
        return cmd.stdout.decode(ENCODING)

    def apt_update(self):
        cmd = "sudo apt-get update"
        self.remote_command(cmd)

    def install_dependency_packages(self):
        cmd = "sudo apt-get install -y apt-transport-https ca-certificates curl"
        self.remote_command(cmd)

    def add_google_cloud_pub_key(self):
        print('Download and add the Google Cloud public signing key')
        cmd = "sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg"
        self.remote_command(cmd)

        print('Add the Kubernetes apt repo')
        cmd = 'echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list'
        self.remote_command(cmd)

    def disable_swap(self):
        cmd = "sudo swapoff -a"
        self.remote_command(cmd)

    def install_kubeadm(self):
        k8s_version = self.get_k8s_version()
        cmd = f"sudo apt-get install -y kubeadm={k8s_version}-00"
        self.remote_command(cmd)

    def install_kubelet(self):
        k8s_version = self.get_k8s_version()
        cmd = f"sudo apt-get install -y kubelet={k8s_version}-00"
        self.remote_command(cmd)

    def install_kubectl(self):
        k8s_version = self.get_k8s_version()
        cmd = f"sudo apt-get install -y kubectl={k8s_version}-00"
        self.remote_command(cmd)

    def pin_kubeadm(self):
        print('Pin kubeadm')
        cmd="sudo apt-mark hold kubeadm"
        self.remote_command(cmd)

    def pin_kubelet(self):
        print('Pin kubelet')
        cmd="sudo apt-mark hold kubelet"
        self.remote_command(cmd)

    def pin_kubectl(self):
        print('Pin kubeadm')
        cmd="sudo apt-mark hold kubectl"
        self.remote_command(cmd)

    def get_config(self):
        return self.hp.config

    def remote_command(self, cmd):
        return self.hp.remote_command(cmd)
