"""Kubeadm functions module"""
CNI_PLUGINS_VERSION="v1.1.1"

import logging

class Kubeadm:
    def __init__(self, helper):
        self.hp = helper
        self.config = self.get_config()

    def install(self, k8s_version):
        logging.debug('Installing kubeadm')


    def get_config(self):
        return self.hp.get_config()

    def remote_command(self, cmd):
        return self.hp.remote_command(cmd)
