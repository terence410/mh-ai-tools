from injector import Module, singleton, inject
from controllers.face_controller import FaceController
from ui.main_window import MainWindow
from typing import Dict, Type
import importlib

class DynamicAppModule(Module):
    def __init__(self, config: Dict[str, str]):
        self.config = config
        super().__init__()

    def configure(self, binder):
        for interface, implementation in self.config.items():
            module_path, class_name = implementation.rsplit('.', 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            binder.bind(interface, to=cls)


