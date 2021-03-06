import os
import sys
import uuid
import platform
import ConfigParser

from distutils import sysconfig


class Config(object):

    TRUE_ANSWERS = (1, "y", "yes", "True", "true", True, "on")

    def __init__(self, name='synapse', devel=False, windows=False):

        self.paths = {
            'pid': os.path.join('/var/run', name + '.pid'),
            'config_path': os.path.join('/etc', name),
            'conf': os.path.join('/etc', name, name + '.conf'),
            'permissions': os.path.join('/etc', name, 'permissions.conf'),
            'persistence': os.path.join('/var/lib', name, 'persistence'),
            'logger_conf': os.path.join('/etc', name, 'logger.conf'),
            'cacert': os.path.join('/etc', name, 'ssl/certs/cacert.pem'),
            'cert': os.path.join('/etc', name, 'ssl/certs/cert.pem'),
            'csr': os.path.join('/etc', name, 'ssl/csr/csr.pem'),
            'key': os.path.join('/etc', name, 'ssl/private/key.pem'),
            'log': os.path.join('/var/log', name, 'messages.log'),
            'plugins': os.path.join('/var/lib', name, 'plugins'),
            }

        if devel:
            curdir = os.path.dirname(os.path.abspath(__file__))
            rootdir = os.path.dirname(curdir)
            for key, value in self.paths.iteritems():
                newvalue = os.path.join(rootdir, 'devel', value[1:])
                self.paths.update({key: newvalue})

        elif windows:
            prefix = os.path.dirname(sysconfig.PREFIX)
            full_prefix = os.path.join(prefix, 'synapse-agent')
            for key, value in self.paths.iteritems():
                newval = value.replace('/', '\\')[1:]
                self.paths[key] = os.path.join(full_prefix, newval)

        self.conf = self.load_config('conf')

        self.rabbitmq = self.set_rabbitmq_config()
        self.monitor = self.set_monitor_config()
        self.resourcefile = self.set_resourcefile_config()
        self.controller = self.set_controller_config()
        self.log = self.set_logger_config()

        self.sections = [('rabbitmq', self.rabbitmq),
                         ('monitor', self.monitor),
                         ('resourcefile', self.resourcefile),
                         ('controller', self.controller),
                         ('log', self.log)]

    def add_section(self, name, section):
        setattr(self, name, section)
        self.sections.append((name, section))

    def set_rabbitmq_config(self):
        conf = {
            'use_ssl': False,
            'fail_if_no_peer_cert': True,
            'ssl_auth': False,
            'cacertfile': self.paths['cacert'],
            'csrfile': self.paths['csr'],
            'certfile': self.paths['cert'],
            'keyfile': self.paths['key'],
            'host': 'localhost',
            'vhost': '/',
            'port': '5672',
            'ssl_port': '5671',
            'username': 'guest',
            'password': 'guest',
            'uuid': '',
            'exchange': 'amq.fanout',
            'status_exchange': 'inbox',
            'status_routing_key': '',
            'compliance_routing_key': '',
            'retry_timeout': 5,
            'heartbeat': '30'
            }

        conf.update(self.conf.get('rabbitmq', {}))

        conf['use_ssl'] = self.sanitize_true_false(conf['use_ssl'])
        conf['fail_if_no_peer_cert'] = \
                self.sanitize_true_false(conf['fail_if_no_peer_cert'])
        conf['ssl_auth'] = self.sanitize_true_false(conf['ssl_auth'])
        conf['port'] = self.sanitize_int(conf['port'])
        conf['ssl_port'] = self.sanitize_int(conf['ssl_port'])
        conf['retry_timeout'] = self.sanitize_int(conf['retry_timeout'])
        conf['heartbeat'] = self.sanitize_int(conf['heartbeat'])
        if not conf['uuid']:
            conf['uuid'] = str(uuid.uuid4())

        return conf

    def set_monitor_config(self):

        conf = {
                'enable_compliance': False,
                'default_interval': '30',
                'alert_interval': '3600',
                'publish_status': False
                }

        conf.update(self.conf.get('monitor', {}))

        conf['default_interval'] = self.sanitize_int(conf['default_interval'])
        conf['alert_interval'] = self.sanitize_int(conf['alert_interval'])
        conf['publish_status'] = \
                self.sanitize_true_false(conf['publish_status'])
        conf['enable_compliance'] = \
                self.sanitize_true_false(conf['enable_compliance'])

        return conf

    def set_resourcefile_config(self):

        conf = {
            'url': 'http://localhost/setup.json',
            'path': '/tmp/setup.json',
            'timeout': 10
            }

        conf.update(self.conf.get('resourcefile', {}))

        conf['timeout'] = self.sanitize_int(conf['timeout'])

        return conf

    def set_controller_config(self):
        conf = {
            'ignored_resources': '',
            'persistence_path': self.paths['persistence'],
            'custom_plugins': self.paths['plugins'],
            'permissions_path': self.paths['permissions'],
            'distribution_name': self.get_platform()[0],
            'distribution_version': self.get_platform()[1],
            }

        conf.update(self.conf.get('controller', {}))

        return conf

    def set_logger_config(self):
        conf = {
            'level': 'INFO',
            'logger_conf': self.paths['logger_conf'],
            'path': self.paths['log']
            }

        conf.update(self.conf.get('logger', {}))

        return conf

    def load_config(self, name):
        fp = self.paths[name]

        conf = {}
        config = ConfigParser.SafeConfigParser()
        config.read(fp)
        for section in config.sections():
            conf[section] = dict(config.items(section))

        return conf

    def get_platform(self):
        dist = ('linux', '0')
        if platform.system().lower() == 'linux':
            dist = platform.linux_distribution()
        elif platform.system().lower() == 'windows':
            dist = ('windows', platform.win32_ver()[0])
        return (self._format_string(dist[0]), self._format_string(dist[1]))

    def _format_string(self, s):
        '''This method replaces dots and spaces with underscores.'''
        _s = '_'.join([x for x in s.lower().split(' ')])
        return ''.join([x for x in _s.replace('.', '_')])

    def update_conf(self, conf, kwargs):
        for key in kwargs:
            conf[key] = kwargs[key]

    def sanitize_true_false(self, option):
        if isinstance(option, basestring):
            return option.lower() in self.TRUE_ANSWERS
        return option

    def sanitize_int(self, option):
        try:
            return int(option)
        except ValueError:
            raise Exception("'%s' must be an integer" % option)

    def dump_config_file(self, to_file=True, *args):
        filecontent = ''

        if to_file:
            msg = "# This file is auto-generated. Edit at your own risks.\n"
            filecontent = '#' * len(msg) + '\n'
            filecontent += msg
            filecontent += '#' * len(msg) + '\n'

        filecontent += '\n'
        for section in self.sections:
            filecontent += "[%s]\n" % section[0]
            for option, value in section[1].iteritems():
                filecontent += "{0} = {1}\n".format(option, value)
            filecontent += '\n'

        if to_file:
            with open(self.paths['conf'], 'w') as fd:
                fd.write(filecontent)

        return filecontent


devel = os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'devel'))
windows = platform.system().lower() == 'windows'
try:
    config = Config(name='synapse-agent', devel=devel, windows=windows)
except Exception as err:
    sys.exit('Error in config module: %s' % err)
