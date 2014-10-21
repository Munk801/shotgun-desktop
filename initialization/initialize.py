# Embedded file name: ..\Resources\initialization\initialize.py
import os
import sys
import logging
import tempfile
from . import install
from . import shotgun
from .. import paths

def initialize(splash, connection):
    """ initialize toolkit for this computer for a single site """
    logger = logging.getLogger('tk-desktop.initialization')
    if not shotgun.is_server_valid(connection):
        raise RuntimeError('Shotgun server is not valid')
    temp_dir = tempfile.mkdtemp(prefix='tk-desktop')
    temp_site_root = os.path.join(temp_dir, 'site')
    logger.debug('temp site install: %s', temp_site_root)
    splash.show()
    splash.set_message('Getting site details...')
    toolkit_script = shotgun.get_or_create_script(connection)
    if toolkit_script is None:
        raise RuntimeError('did not get toolkit script')
    app_store_script = shotgun.get_app_store_credentials(connection)
    if app_store_script is None:
        raise RuntimeError('did not get app store script')
    if sys.platform == 'darwin':
        current_plat_name = 'Darwin'
    elif sys.platform == 'win32':
        current_plat_name = 'Windows'
    elif sys.platform.startswith('linux'):
        current_plat_name = 'Linux'
    else:
        raise RuntimeError('unknown platform: %s' % sys.platform)
    locations = {'Darwin': '',
     'Windows': '',
     'Linux': ''}
    locations[current_plat_name] = temp_site_root
    executables = {'Darwin': '',
     'Windows': '',
     'Linux': ''}
    executables[current_plat_name] = paths.get_python_path()
    splash.details = 'Installing Toolkit core...'
    installer = install.InstallThread()
    installer.set_install_folder(temp_site_root)
    installer.set_shotgun_info(connection.base_url, toolkit_script['firstname'], toolkit_script['salted_password'])
    installer.set_app_store_info(app_store_script['firstname'], app_store_script['salted_password'], app_store_script)
    installer.set_locations(locations)
    installer.set_executables(executables)
    logger.debug('starting installer')
    installer.start()
    installer.wait()
    return temp_site_root