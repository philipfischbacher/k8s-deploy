"""Container Plugin functions module"""
CNI_PLUGINS_VERSION="1.3.0"

import logging

class CNI_Plugin:
    def __init__(self, helper):
        self.hp = helper
        self.config = self.get_config()

    def install(self):
        logging.debug('Installing CNI plugins for Kubeadm')
        cni_plugins_version = get_cni_plugins_version()
        arch="amd64"
        dest="/opt/cni/bin"

        cmd = 'sudo mkdir -p "$dest"'
        self.remote_command(cmd)

        cmd = "curl -L \"https://github.com/containernetworking/plugins/releases/download/v${cni_plugins_version}/cni-plugins-linux-${arch}-v${cni_plugins_version}.tgz\" | sudo tar -C \"$dest\" -xz"
        self.remote_command(cmd)

    def get_cni_plugins_version():
        if self.config['cni']['containernetworking']['version']:
            return self.config['cni']['containernetworking']['version']
        else:
            return CNI_PLUGINS_VERSION

    def create_download_dir():
        DOWNLOAD_DIR="/usr/local/bin"
        cmd = "sudo mkdir -p \"$DOWNLOAD_DIR\""
        self.remote_command(cmd)

    def install_critcl():
        CRICTL_VERSION="v1.25.0"
        ARCH="amd64"
        cmd = curl -L \"https://github.com/kubernetes-sigs/cri-tools/releases/download/${CRICTL_VERSION}/crictl-${CRICTL_VERSION}-linux-${ARCH}.tar.gz\" | sudo tar -C $DOWNLOAD_DIR -xz"
        self.remote_command(cmd)

