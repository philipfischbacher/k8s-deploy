"""
CLI tool for deploying Kubernetes
Main Module
"""
import argparse
import logging

#from k8s_deploy.modules.helper import Helper
from k8s_deploy.modules.k8s import K8S_Cluster as Cluster

def main():
    """Main Function to install Kubernetes remotely
    from the command line.
    """

    parser = parser_init()
    args = parser.parse_args()

    if args.config_file:
        config_file = args.config_file

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    try:
        cluster = Cluster(config_file)
        cluster.install_cluster()
    except ValueError as e:
        print('Error:', e)

#def install_cluster(cluster_name):
    #k8s.install_cluster(cluster_name)

def parser_init():
    """Function to define the variables for parsing the cli arguments"""

    parser = argparse.ArgumentParser(
        prog='Kubernetes Remote Install',
        description="""A Python command line tool that remotely installs Kubernetes.""",
        epilog='I hope you enjoy using this.'
    )

    parser.add_argument(
        'config_file',
        metavar='CONFIG_FILE',
        type=str,
        help="""config yaml file"""
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action="store_true",
        help='Increase verbose output.'
    )

    return parser


if __name__ == '__main__':
    main()
