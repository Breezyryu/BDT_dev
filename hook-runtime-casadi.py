import os
import sys

# PyInstaller frozen exe: casadi DLLs are in _internal/casadi/
# but _casadi.pyd is in _internal/ root, so DLL search path must include casadi folder
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
    _casadi_dir = os.path.join(_base, 'casadi')
    if os.path.isdir(_casadi_dir):
        os.add_dll_directory(_casadi_dir)
        os.environ['PATH'] = _casadi_dir + os.pathsep + os.environ.get('PATH', '')
