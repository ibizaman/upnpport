"""
Maintains port forwarding in UPnP compatible routers.
"""

import argparse
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from time import sleep

import yaml


DEFAULT_CONFIG_FILES = [
    Path(p)
    for p in ["/etc/upnpport/upnpport.yaml",
              Path.home() / ".config/upnpport/upnpport.yaml",
              "./config/upnpport.yaml"]]


class Config:
    def __init__(self, config_file):
        self._rules = {}

        self.parse_rules(config_file)

    def __iter__(self):
        for (port, protocol), rest in self._rules.items():
            rule = {
                'port': port,
                'protocol': protocol,
            }
            if port != rest['external_port']:
                rule['external_port'] = rest['external_port']
            yield rule

    def rules(self):
        return list(self)

    def add(self, port, external_port=None, protocol='tcp'):
        external_port = external_port or port
        self._rules[(port, protocol)] = {'external_port': external_port}

    def remove(self, port, external_port=None, protocol='tcp'):
        external_port = external_port or port
        del self._rules[(port, protocol)]

    def parse_rules(self, config_file):
        self._rules = {}

        try:
            with config_file.open() as f:
                config = yaml.load(f.read())
                if not config:
                    return

                for rule in config:
                    self.add(rule['port'], rule.get('external_port'), rule['protocol'])
        except FileNotFoundError:
            pass

    def dump_rules(self, config_file):
        with config_file.open('w') as f:
            f.write(yaml.dump(self.rules(), default_flow_style=False))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.set_defaults(func=None)
    command_parser = parser.add_subparsers()

    parser_conf = command_parser.add_parser('configure', help='Modify configuration file.')
    parser_conf.set_defaults(command='configure')
    parser_conf.set_defaults(func=configure)
    parser_conf.add_argument(
        'config_file',
        type=Path,
        help='Location of the config file to modify.'
    )
    conf_action_parser = parser_conf.add_subparsers()

    parser_conf_add = conf_action_parser.add_parser('add', help='Add or replace port forwarding rule.')
    parser_conf_add.set_defaults(action='add')
    parser_conf_add.add_argument(
        'port',
        type=int)
    parser_conf_add.add_argument(
        '--protocol',
        choices=['tcp', 'udp'],
        default='tcp')
    parser_conf_add.add_argument(
        '--external_port',
        type=int)

    parser_conf_del = conf_action_parser.add_parser('del', help='Remove port forwarding rule.')
    parser_conf_del.set_defaults(action='del')
    parser_conf_del.add_argument(
        'port',
        type=int)
    parser_conf_del.add_argument(
        '--protocol',
        choices=['tcp', 'udp'],
        default='tcp')
    parser_conf_del.add_argument(
        '--external_port',
        type=int)

    parser_run = command_parser.add_parser('run', help='Run script.')
    parser_run.set_defaults(command='run')
    parser_run.set_defaults(func=run)
    parser_run.add_argument(
        '--config_files',
        type=lambda v: [Path(p) for p in v.split(',')],
        default=','.join(str(p) for p in DEFAULT_CONFIG_FILES),
        help="Location of config files, last one found takes precendence, defaults to {}.".format(
            ', '.join(str(p) for p in DEFAULT_CONFIG_FILES)))

    args = vars(parser.parse_args())
    if args['func']:
        args['func'](**args)


def configure(config_file, action, port, protocol='tcp', external_port=None, **_kwargs):
    config = Config(config_file)

    if action == 'add':
        config.add(port, external_port, protocol)
    elif action == 'del':
        config.remove(port, external_port, protocol)

    config.dump_rules(config_file)


def run(config_files, **_kwargs):
    config = Config(find_config(config_files))

    def sigusr1_handler(_signum, _stack):
        config.parse_rules(find_config(config_files))
        print('Reloaded configuration file.')
        
    signal.signal(signal.SIGUSR1, sigusr1_handler)

    while True:
        try:
            open_ports(config)
            print('Sleeping for 5 minutes.')
            sleep(300)
        except KeyboardInterrupt:
            return


def find_config(config_files):
    for config_file in reversed(config_files):
        if config_file.is_file():
            return config_file

    raise RuntimeError("No configuration found on given paths.")


def open_ports(rules):
    existing_rules = get_existing_rules()

    for rule in rules:
        if rule in existing_rules:
            print('skipping rule', format(rule))
            continue

        print('enforcing rule', format(rule))
        command = ['upnpc', '-r', str(rule['port'])]
        if 'external_port' in rule:
            command += [str(rule['external_port'])]
        command += [rule['protocol']]
        call(*command)


def get_existing_rules():
    command = ['upnpc', '-l']
    output = call(*command).decode('utf-8').split('\n')
    rules_str = keep_lines(output, r'.*\d->')
    rules = []
    for rule_str in rules_str:
        rule_str_split = re.split(r'\s+|->|:', rule_str)
        if rule_str_split[0] == '':
            del rule_str_split[0]
        rule = {'port': int(rule_str_split[4]), 'protocol': rule_str_split[1].lower()}
        if int(rule_str_split[2]) != rule['port']:
            rule['external_port'] = int(rule_str_split[2])
        rules.append(rule)
    return rules


def call(*args):
    try:
        return subprocess.Popen(args, stdout=subprocess.PIPE).stdout.read()
    except FileNotFoundError:
        raise RuntimeError('Could not find upnpc executable, is miniupnpc installed?')


def keep_lines(lines, regex):
    for line in lines:
        if re.match(regex, line):
            yield line


def format(rule):
    return str(rule['port']) + '->' \
        + str(rule.get('external_port', rule['port'])) \
        + ' ' + rule['protocol']


if __name__ == '__main__':
    main()
