"""Remote installer functions module"""

import paramiko, time, os
from paramiko import AuthenticationException
ENCODING='utf-8'
import logging

outlock = threading.Lock()

class RemoteConnect:
    def __init__(self, host, user, passcode):
        self.host = host
        self.conn_handle = None
        self.username = user
        self.userpass = passcode
        self.__connect()
        self.log = logging.getLogger("k8s-log")

    def __connect(self):
        try:
            self.conn_handle = paramiko.client.SSHClient()
            self.conn_handle.load_system_host_keys()
            self.conn_handle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.conn_handle.connect(self.host, 22, self.username, self.userpass)
        except AuthenticationException as error:
            print('Authentication Failed: Please check your username and password')
        finally:
            print("Connection handle open for " + self.host)
            return self.conn_handle

    def disconnect(self):
        self.conn_handle.close()

    def execute_command(self, command):
        if self.conn_handle == None:
            self.conn_handle == self.__connect()
        stdin, stdout, stderr = self.conn_handle.exec_command(command)
        status = stdout.channel.recv_exit_status()
        if status == 0:
            self.log.debug("Result:", stout.decode(ENCODING))
            return stdout.read()
        else:
            self.log.error("Error:", sterr.decode(ENCODING))
            return -1
