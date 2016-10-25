from abc import abstractmethod, ABCMeta

__author__ = 'schien'


class NodeController(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def update_node(self):
        pass


class BaseController(object):
    __metaclass__ = ABCMeta

    def update(self, api_id=None):
        api_data = self.get_api_data(api_id)
        for node_controller in self.get_node_controllers(api_data):
            node_controller.update_node()
            for device_controller in node_controller.get_device_controllers():
                device_controller.create_measurements()

    @abstractmethod
    def get_api_data(self, api_id=None) -> []:
        pass

    @abstractmethod
    def get_node_controllers(self, api_data) -> [NodeController]:
        pass

    @abstractmethod
    def get_device_controllers(self, node_data) -> []:
        pass
