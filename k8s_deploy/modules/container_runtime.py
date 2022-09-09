"""Container Runtime setup module"""


class ContainerRuntime:
    def __init__(self, helper):
        self.hp = helper
        self.config = self.get_config()
        self.container_runtime = self.config['container_runtime']['name']

    def setup_container_runtime(self):
        if self.container_runtime == 'containerd':
            self.install_containerd_tarball()
        else:
            print('Sorry, this container runtime is not available with this script.')
            #self.install_docker()

    def install_docker(self):
        print('Sorry, can\'t install docker yet.')
        
    def install_containerd(self):
        cmd = "sudo apt-get update"
        self.remote_command(cmd)

        cmd = "sudo apt-get -y install containerd"
        self.remote_command(cmd)

        self.configure_containerd()

        #cmd = "sudo mkdir -p /etc/containerd"
        #self.remote_command(cmd)

        #cmd = "containerd config default | sudo tee /etc/containerd/config.toml"
        #self.remote_command(cmd)

        #cmd = "sudo systemctl restart containerd"
        #self.remote_command(cmd)

    def install_containerd_tarball(self):
        print('Download containerd')
        containerd_version = self.config['container_runtime']['versions']['containerd']
        runc_version = self.config['container_runtime']['versions']['runc']

        cmd = f"curl -Ls https://github.com/containerd/containerd/releases/download/v{containerd_version}/containerd-{containerd_version}-linux-amd64.tar.gz --output containerd.tar.gz"
        self.remote_command(cmd)

        print('Unzip containerd')
        cmd = "sudo tar Cxzvf /usr/local ~/containerd.tar.gz"
        self.remote_command(cmd)
        
        print('Create the /usr/local/lib/systemd/system directory for the containerd service')
        cmd = "sudo mkdir /usr/local/lib/systemd/system/ -p"
        self.remote_command(cmd)

        cmd = "curl -Ls https://raw.githubusercontent.com/containerd/containerd/main/containerd.service > ~/containerd.service"
        self.remote_command(cmd)

        cmd = "sudo mv ~/containerd.service /usr/local/lib/systemd/system/containerd.service"
        self.remote_command(cmd)

        cmd = "sudo systemctl daemon-reload"
        self.remote_command(cmd)

        cmd = "sudo systemctl enable --now containerd"
        self.remote_command(cmd)

        cmd = f"curl -Ls https://github.com/opencontainers/runc/releases/download/v{runc_version}/runc.amd64 --output runc.amd64"
        self.remote_command(cmd)

        cmd = "sudo install -m 755 runc.amd64 /usr/local/sbin/runc"
        self.remote_command(cmd)

        self.configure_containerd()
        
    def configure_containerd(self):
        print('Setup containerd config.toml file')
        cmd = "sudo mkdir -p /etc/containerd"
        self.remote_command(cmd)

        cmd = "containerd config default | sudo tee /etc/containerd/config.toml"
        self.remote_command(cmd)

        cmd = "sudo systemctl restart containerd"
        self.remote_command(cmd)

    def get_config(self):
        return self.hp.get_config()

    def remote_command(self, cmd):
        self.hp.remote_command(cmd)
