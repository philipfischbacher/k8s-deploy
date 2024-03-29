"""
CLI tool for deploying Kubernetes
Main Module
"""
import argparse
import logging
import sys

LOGGING_FORMAT="%(name)s - %(levelname)s - %(asctime)s %(message)s"

from k8s_deploy.modules.cluster import Cluster

def main():
    """Main Function to install Kubernetes remotely
    from the command line.
    """
    logging.basicConfig(format=LOGGING_FORMAT, datefmt='%y-%b-%d %H:%M:%S')
    log = logging.getLogger("k8s-log")
    parser = parser_init()
    args = parser.parse_args()

    if args.config_file:
        config_file = args.config_file

    if args.verbose:
        logging.info('Set logging level to debug')
        log.setLevel(logging.DEBUG)

    try:
        cluster = Cluster(config_file)
        cluster.install_cluster()
    except ValueError as e:
        log.error('Error:', e)

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
        default=False,
        action="store_true",
        help='Increase verbose output.'
    )

    return parser


if __name__ == '__main__':
    main()
