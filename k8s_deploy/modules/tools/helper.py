"""Helper functions module"""

import os
import subprocess
from subprocess import check_output
import logging
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
        self.verbosity = True
        self.log = logging.getLogger("k8s-log")
        self.cmds = []

    def get_config(self):
        with open(self.config_file, "r") as stream:
            try:
                config = yaml.safe_load(stream)
                return config
            except yaml.YAMLError as exc:
                print(exc)
                return exc

    def set_current_node(self, node):
        self.current_node = node

    def get_current_node(self):
        return self.current_node 

    def queue_command(self, cmd):
        self.cmds.append(cmd)

    def run_commands(self):
        for cmd in self.cmds:
            self.remote_command(cmd)
        self.reset_commands()

    def reset_commands(self):
        self.cmds = []

    def remote_command(self, cmd):
        node_category = self.current_node['node_category']
        node_num = self.current_node['node_num']
        node_name = self.config['cluster'][node_category][node_num]['name']
        user = self.config['cluster'][node_category][node_num]['ssh_access']['user']
        hostname = self.config['cluster'][node_category][node_num]['ssh_access']['hostname']
        identity_file = self.config['cluster'][node_category][node_num]['ssh_access']['identityFile']

        self.log.debug(f'Running command: {cmd} on {node_name}')
        cmd_array = ["ssh", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no", "-i", identity_file, f"{user}@{hostname}", cmd]
        out, err = subprocess.Popen(cmd_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
           
        if (out):
            self.log.debug(f"Result: {out.decode(ENCODING)}")
            return out.decode(ENCODING)
        if (err):
            self.log.error(f"Error: {err.decode(ENCODING)}")
            return err.decode(ENCODING)
