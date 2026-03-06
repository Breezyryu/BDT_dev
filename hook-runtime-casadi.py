import os
import sys

# PyInstaller frozen exe: casadi DLLs are in _internal/casadi/
# but _casadi.pyd is in _internal/ root, so DLL search path must include casadi folder
# 핵심: 시스템 PATH에 같은 이름의 DLL(libstdc++, libgcc 등)이 있으면
# 다른 버전이 먼저 로드되어 "지정된 프로시저를 찾을 수 없습니다" 에러 발생
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
    _casadi_dir = os.path.join(_base, 'casadi')
    if os.path.isdir(_casadi_dir):
        # 1) DLL 검색 경로에 추가
        os.add_dll_directory(_casadi_dir)
        os.add_dll_directory(_base)
        # 2) PATH 맨 앞에 casadi 경로 추가 (우선순위 최상위)
        os.environ['PATH'] = _casadi_dir + os.pathsep + _base + os.pathsep + os.environ.get('PATH', '')
        # 3) 핵심 MinGW 런타임 DLL을 ctypes로 먼저 강제 로드
        import ctypes
        for _dll_name in [
            'libwinpthread-1.dll',
            'libgcc_s_seh-1.dll',
            'libstdc++-6.dll',
            'libgfortran-5.dll',
            'libquadmath-0.dll',
            'libgomp-1.dll',
            'libcasadi.dll',
            'libcasadi-tp-openblas.dll',
        ]:
            _dll_path = os.path.join(_casadi_dir, _dll_name)
            if os.path.isfile(_dll_path):
                try:
                    ctypes.CDLL(_dll_path)
                except OSError:
                    pass
