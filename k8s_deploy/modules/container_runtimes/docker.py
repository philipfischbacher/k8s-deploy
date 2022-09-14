"""Docker Container setup module"""

class Docker:
    def __init__(self, helper):
        self.hp = helper
        self.config = self.get_config()

    def get_config(self):
        return self.hp.get_config()

    def remote_command(self, cmd):
        self.hp.remote_command(cmd)

    def install(self):
        cmd ="apt-get update"
        self.remote_command(cmd)

        cmd = "apt-get install -y docker.io"
        self.remote_command(cmd)

        cmd = "sudo systemctl enable docker && sudo systemctl daemon-reload && sudo systemctl restart docker"
        self.remote_command(cmd)
        
