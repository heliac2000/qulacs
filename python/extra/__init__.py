
try:
  __QULACS_SETUP__
except NameError:
  __QULACS_SETUP__ = False

if not __QULACS_SETUP__:
  from glob import glob
  from os import path
  from sys import modules as sys_modules
  from importlib._bootstrap import _exec
  from importlib.machinery import SourceFileLoader
  from importlib.util import spec_from_file_location, module_from_spec
  from pkg_resources import get_distribution

  # Load a shared library
  def load_dynamic(module, path):
    spec = spec_from_file_location(module, path)
    mod = module_from_spec(spec)
    sys_modules[module] = mod
    spec.loader.exec_module(mod)

  # Load a python code
  def load_source(module, path):
    loader = SourceFileLoader(module, path)
    spec = spec_from_file_location(module, path, loader=loader)
    _exec(spec, sys_modules[module])

  # Load qulacs shared library
  load_dynamic(
    __name__,
    path.join(path.dirname(path.dirname(path.abspath(__file__))),
              open(path.join(
                get_distribution(__name__).egg_info, 'native_libs.txt')
              ).read().strip()))

  # Load extra python codes
  for f in sorted(glob(path.join(path.dirname(path.abspath(__file__)), '*.py'))):
    if f != path.abspath(__file__): # don't load "__init__.py"
      load_source(__name__, f)

  __QULACS_SETUP__ = True
