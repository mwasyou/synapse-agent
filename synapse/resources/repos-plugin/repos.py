from synapse.synapse_exceptions import ResourceException
from synapse.resources.resources import ResourcesController
from synapse.logger import logger


@logger
class ReposController(ResourcesController):

    __resource__ = "repos"

    def read(self, res_id=None, attributes={}):
        details = attributes.get('details')
        return self.module.get_repos(res_id, details=details)

    def create(self, res_id=None, attributes={}):
        self.check_mandatory(res_id)
        baseurl = attributes.get('baseurl')
        monitor = attributes.get('monitor')
        self.comply(name=res_id, baseurl=baseurl, present=True,
                    monitor=monitor)
        self.module.create_repo(res_id, attributes)
        return self.module.get_repos(res_id)

    def update(self, res_id=None, attributes=None):
        return self.create(res_id=res_id, attributes=attributes)

    def delete(self, res_id=None, attributes=None):
        self.check_mandatory(res_id)
        self.comply(monitor=False)
        self.module.delete_repo(res_id, attributes)

        return self.module.get_repos(res_id)

    def monitor(self):
        try:
            res = getattr(self.persister, "repos")
        except AttributeError:
            return

        for state in res:
            error = False
            res_id = state["resource_id"]
            res_status = state["status"]
            with self._lock:
                try:
                    self.response = self.read(res_id=res_id)
                except ResourceException as err:
                    self.logger.error(err)

            for key in res_status.keys():
                if self.response.get(key) != res_status[key]:
                    error = True
                    break
            if error:
                self._publish(res_id, state, self.response)
