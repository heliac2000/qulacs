
try:
  __QULACS_SETUP__
except NameError:
  __QULACS_SETUP__ = False

if not __QULACS_SETUP__:
  from pkg_resources import get_distribution
  from os import path
  from glob import glob
  from imp import load_dynamic, load_source

  load_dynamic(
    __name__,
    path.join(path.dirname(path.dirname(path.abspath(__file__))),
              open(path.join(
                get_distribution(__name__).egg_info,
                'native_libs.txt')).read().strip()))

  for f in glob(path.join(path.dirname(path.abspath(__file__)), '*.py')):
    if f != path.abspath(__file__): # don't load "__init__.py"
      load_source(__name__, f)

  __QULACS_SETUP__ = True
