from synapse.logger import logger
from synapse.resources.resources import ResourcesController
from synapse.synapse_exceptions import ResourceException


@logger
class HostsController(ResourcesController):
    '''Resource exposing hosts informations.'''

    __resource__ = "hosts"

    def read(self, res_id=None, attributes=None):
        if 'hostname' in attributes:
            self.status['hostname'] = self.module.get_hostname()

        if 'mac' in attributes or 'mac_addresses' in attributes:
            self.status['mac_addresses'] = self.module.get_mac_addresses()

        if 'memtotal' in attributes:
            self.status['memtotal'] = self.module.get_memtotal()

        if 'ip' in attributes:
            self.status['ip'] = self.module.get_ip_addresses()

        if 'uptime' in attributes:
            self.status['uptime'] = self.module.get_uptime()

        if 'platform' in attributes:
            self.status['platform'] = self.module.get_platform()

        return self.status

    def monitor(self):
        """Sends hosts infos regularly."""

        attrs = ("ip", "hostname", "memtotal", "uptime")
        try:
            with self._lock:
                task = self.read(attributes=attrs)
        except ResourceException:
            pass

        if task:
            self._publish_status('', task)
