"""Helper functions module"""

import os
import subprocess
from subprocess import check_output
import yaml
ENCODING='utf-8'

class Helper:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.get_config()
        current_node = {
            'node_category': 'controlplanes',
            'node_num': 0
        }
        self.current_node = current_node

    def get_config(self):
        with open(self.config_file, "r") as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        return config

    def set_current_node(self, node):
        self.current_node = node

    def get_current_node(self):
        return self.current_node 

    def remote_command(self, cmd):
        node_category = self.current_node['node_category']
        node_num = self.current_node['node_num']
        node_name = self.config['cluster'][node_category][node_num]['name']
        user = self.config['cluster'][node_category][node_num]['ssh_access']['user']
        hostname = self.config['cluster'][node_category][node_num]['ssh_access']['hostname']
        identity_file = self.config['cluster'][node_category][node_num]['ssh_access']['identityFile']
        print('Running command: "%s" on %s' % (cmd, node_name))

        out, err = subprocess.Popen(["ssh", "-o", "IdentitiesOnly=yes", "-i", identity_file, f"{user}@{hostname}", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if (out):
            print("Result:", out.decode(ENCODING))
            return out.decode(ENCODING)
        if (err):
            print("Error:", err.decode(ENCODING))
