import pathlib
import importlib.util as ilu


def load_module(file_path, module_name=None):
    module_name = module_name or pathlib.Path(file_path).stem
    spec = ilu.spec_from_file_location(module_name, file_path)
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



