"""Helm setup module"""

HELM_CHARTS = [
    'k8ssandra',
    'reaper'
]

class Helm:
    def __init__(self, helper):
        self.hp = helper
        self.config = self.get_config()
        self.helm_version = self.config['helm']['verion']
        self.helm_charts = self.config['helm'][['charts']

    def install_charts():
        for chart in self.helm_charts:
            print('Install Helm chart: %s', % chart['name'])
            if self.check_charts(chart['name']):
                match chart['name']:
                    case 'k8ssandra':
                        self.install_k8ssandra_chart()
                    case _:
            else:
                print('Sorry, cannot install the %s Helm chart.' % chart['name'])
    
    def install_k8ssandra_chart(self):
        self.k8ssandra_config_file = self.config['helm'][['charts']['k8ssandra']['config_file']
        if self.k8ssandra_config_file:
            cmd = "helm repo add k8ssandra https://helm.k8ssandra.io/stable"
            self.remote_command(cmd)

            cmd = "helm repo add traefik https://helm.traefik.io/traefik"
            self.remote_command(cmd)

            cmd = "helm repo update"
            self.remote_command(cmd)

    def check_chart(self, chart_name):
        if chart_name in HELM_CHARTS:
            return True
        else:
            return False

    def get_config(self):
        return self.hp.get_config()

    def remote_command(self, cmd):
        self.hp.remote_command(cmd)
