# Embedded file name: ..\Resources\utils.py
import os
import sys
import stat
import time
import errno
import ctypes
import ctypes.util

def _osx_sudo_start():
    sec = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Security'))
    kAuthorizationFlagInteractionAllowed = 1
    kAuthorizationFlagExtendRights = 2
    auth = ctypes.c_void_p()
    r_auth = ctypes.byref(auth)
    err = sec.AuthorizationCreate(None, None, kAuthorizationFlagExtendRights | kAuthorizationFlagInteractionAllowed, r_auth)
    if err:
        raise OSError(errno.EACCES, 'could not sudo: %d' % err)
    return auth


def _osx_sudo_end(auth):
    sec = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Security'))
    kAuthorizationFlagDefaults = 0
    err = sec.AuthorizationFree(auth, kAuthorizationFlagDefaults)
    if err:
        raise OSError(errno.EACCES, 'could not sudo: %d' % err)


def _osx_sudo_mkdir(auth, path, mode):
    exe = ['/bin/mkdir',
     '-pm',
     oct(mode),
     path]
    _osx_sudo_cmd(auth, exe)


def _osx_sudo_touch(auth, path):
    exe = ['/usr/bin/touch', path]
    _osx_sudo_cmd(auth, exe)


def _osx_sudo_chmod(auth, path, mode):
    exe = ['/bin/chmod', oct(mode), path]
    _osx_sudo_cmd(auth, exe)
    while stat.S_IMODE(os.stat(path).st_mode) != mode:
        time.sleep(0.1)


def _osx_sudo_cmd(auth, exe):
    sec = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Security'))
    kAuthorizationFlagDefaults = 0
    args = (ctypes.c_char_p * len(exe))()
    for i, arg in enumerate(exe[1:]):
        args[i] = arg

    args[len(exe) - 1] = None
    err = sec.AuthorizationExecuteWithPrivileges(auth, exe[0], kAuthorizationFlagDefaults, args, None)
    if err:
        raise OSError(errno.EACCES, 'could not sudo: %d' % err)
    return


def _win32_sudo_start():
    from PySide import QtGui
    QtGui.QMessageBox.critical(None, 'Error with initial setup.', 'Elevated permissions needed to setup Toolkit.\nPlease run again as an Administrator.')
    sys.exit(1)
    return


def _win32_sudo_end(auth):
    raise NotImplementedError


def _win32_sudo_mkdir(auth, path, mode):
    raise NotImplementedError


def _win32_sudo_touch(auth, path):
    raise NotImplementedError


def _win32_sudo_chmod(auth, path, mode):
    raise NotImplementedError


def _win32_sudo_cmd(auth, exe):
    raise NotImplementedError


def _linux_sudo_start():
    from PySide import QtGui
    QtGui.QMessageBox.critical(None, 'Error with initial setup.', 'Elevated permissions needed to setup Toolkit.\nPlease run again as root.')
    sys.exit(1)
    return


def _linux_sudo_end(auth):
    raise NotImplementedError


def _linux_sudo_mkdir(auth, path, mode):
    raise NotImplementedError


def _linux_sudo_touch(auth, path):
    raise NotImplementedError


def _linux_sudo_chmod(auth, path, mode):
    raise NotImplementedError


def _linux_sudo_cmd(auth, exe):
    raise NotImplementedError


if sys.platform == 'darwin':
    sudo_start = _osx_sudo_start
    sudo_mkdir = _osx_sudo_mkdir
    sudo_touch = _osx_sudo_touch
    sudo_chmod = _osx_sudo_chmod
    sudo_end = _osx_sudo_end
elif sys.platform == 'win32':
    sudo_start = _win32_sudo_start
    sudo_mkdir = _win32_sudo_mkdir
    sudo_touch = _win32_sudo_touch
    sudo_chmod = _win32_sudo_chmod
    sudo_end = _win32_sudo_end
elif sys.platform.startswith('linux'):
    sudo_start = _linux_sudo_start
    sudo_mkdir = _linux_sudo_mkdir
    sudo_touch = _linux_sudo_touch
    sudo_chmod = _linux_sudo_chmod
    sudo_end = _linux_sudo_end
else:
    raise RuntimeError('Unknown platform: %s' % sys.platform)