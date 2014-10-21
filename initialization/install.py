# Embedded file name: ..\Resources\initialization\install.py
import os
import sys
import uuid
import errno
import shutil
import logging
import tempfile
import traceback
from zipfilehelper import unzip_file
from distutils.version import LooseVersion
from PySide import QtCore
from shotgun_api3 import Shotgun
from .. import utils
from . import constants

class InstallThread(QtCore.QThread):
    stepDone = QtCore.Signal(str)
    stepWarn = QtCore.Signal(str)
    stepError = QtCore.Signal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self._auth = None
        self._logger = logging.getLogger('tk-desktop.initialization.install')
        return

    def set_install_folder(self, folder):
        self._sgtk_folder = folder

    def set_shotgun_info(self, url, script, key, proxy = None):
        self._server_url = url
        self._script_name = script
        self._app_key = key
        self._sg_proxy = proxy

    def set_app_store_info(self, script, key, app_store_current_script_user_entity):
        self._app_store_script = script
        self._app_store_key = key
        self._app_store_current_script_user_entity = app_store_current_script_user_entity

    def set_locations(self, location):
        self._location = location

    def set_executables(self, executables):
        self._executables = executables

    def run(self):
        if os.path.exists(self._sgtk_folder):
            self._logger.info("Install directory already exists: '%s'" % self._sgtk_folder)
            self.stepDone.emit('Install directory already exists')
            return
        else:
            try:
                self.create_structure()
                self.install_core()
            except Exception:
                self._logger.exception()
                error = traceback.format_exc()
                self.stepError.emit(error)
            else:
                self.stepDone.emit('Done')
                self._logger.debug('Done')
            finally:
                if self._auth is not None:
                    utils.sudo_end(self._auth)
                    self._auth = None

            return

    def create_structure(self):
        self._logger.debug('Creating install directory...')
        self.stepDone.emit('Creating install directory...')
        try:
            os.makedirs(self._sgtk_folder, 509)
            elevate = False
        except OSError as e:
            if e.errno != errno.EACCES:
                raise
            elevate = True

        if elevate:
            self._auth = utils.sudo_start()
            touch = lambda path: utils.sudo_touch(self._auth, path)
            mkdir = lambda path, mode: utils.sudo_mkdir(self._auth, path, mode)
            chmod = lambda path, mode: utils.sudo_chmod(self._auth, path, mode)
            mkdir(self._sgtk_folder, 509)
        else:
            mkdir = os.makedirs
            chmod = os.chmod
            touch = lambda path: open(path, 'a').close()
        mkdir(os.path.join(self._sgtk_folder, 'config'), 509)
        mkdir(os.path.join(self._sgtk_folder, 'config', 'core'), 509)
        mkdir(os.path.join(self._sgtk_folder, 'install'), 509)
        mkdir(os.path.join(self._sgtk_folder, 'install', 'core'), 511)
        mkdir(os.path.join(self._sgtk_folder, 'install', 'core.backup'), 511)
        mkdir(os.path.join(self._sgtk_folder, 'install', 'engines'), 511)
        mkdir(os.path.join(self._sgtk_folder, 'install', 'apps'), 511)
        mkdir(os.path.join(self._sgtk_folder, 'install', 'frameworks'), 511)
        self.stepDone.emit('Creating configuration files...')
        self._logger.debug('Creating configuration files...')
        sg_config_location = os.path.join(self._sgtk_folder, 'config', 'core', 'shotgun.yml')
        touch(sg_config_location)
        chmod(sg_config_location, 511)
        fh = open(sg_config_location, 'wt')
        fh.write('# Shotgun Pipeline Toolkit configuration file\n')
        fh.write('# this file was automatically created\n')
        fh.write('\n')
        fh.write('host: %s\n' % self._server_url)
        fh.write('api_script: %s\n' % self._script_name)
        fh.write('api_key: %s\n' % self._app_key)
        if self._sg_proxy is None:
            fh.write('http_proxy: null\n')
        else:
            fh.write('http_proxy: %s\n' % self._sg_proxy)
        fh.write('\n')
        fh.write('# End of file.\n')
        fh.close()
        sg_config_location = os.path.join(self._sgtk_folder, 'config', 'core', 'app_store.yml')
        touch(sg_config_location)
        chmod(sg_config_location, 511)
        fh = open(sg_config_location, 'wt')
        fh.write('# Shotgun Pipeline Toolkit configuration file\n')
        fh.write('# this file was automatically created\n')
        fh.write('\n')
        fh.write('host: %s\n' % constants.SGTK_APP_STORE)
        fh.write('api_script: %s\n' % self._app_store_script)
        fh.write('api_key: %s\n' % self._app_store_key)
        if self._sg_proxy is None:
            fh.write('http_proxy: null\n')
        else:
            fh.write('http_proxy: %s\n' % self._sg_proxy)
        fh.write('\n')
        fh.write('# End of file.\n')
        fh.close()
        sg_code_location = os.path.join(self._sgtk_folder, 'config', 'core', 'install_location.yml')
        touch(sg_code_location)
        chmod(sg_code_location, 511)
        fh = open(sg_code_location, 'wt')
        fh.write('# Shotgun Pipeline Toolkit configuration file\n')
        fh.write('# This file was automatically created\n')
        fh.write('\n')
        fh.write('# This file stores the location on disk where this\n')
        fh.write('# configuration is located. It is needed to ensure\n')
        fh.write('# that deployment works correctly on all os platforms.\n')
        fh.write('\n')
        for curr_platform, path in self._location.items():
            fh.write("%s: '%s'\n" % (curr_platform, path))

        fh.write('\n')
        fh.write('# End of file.\n')
        fh.close()
        for x in self._executables:
            sg_config_location = os.path.join(self._sgtk_folder, 'config', 'core', 'interpreter_%s.cfg' % x)
            touch(sg_config_location)
            chmod(sg_config_location, 511)
            fh = open(sg_config_location, 'wt')
            fh.write(self._executables[x])
            fh.close()

        return

    def install_core(self):
        sg_studio = Shotgun(self._server_url, self._script_name, self._app_key, http_proxy=self._sg_proxy)
        sg_studio_version = '.'.join([ str(x) for x in sg_studio.server_info['version'] ])
        sg_app_store = Shotgun(constants.SGTK_APP_STORE, self._app_store_script, self._app_store_key, http_proxy=self._sg_proxy)
        latest_core, core_path = self._download_core(sg_studio_version, sg_app_store, self._server_url, self._app_store_current_script_user_entity)
        self.stepDone.emit('Now installing Shotgun Pipeline Toolkit Core')
        self._logger.debug('Now installing Shotgun Pipeline Toolkit Core')
        sys.path.insert(0, core_path)
        try:

            class EmitLogger(object):

                def __init__(self, host, debug = False):
                    self.host = host
                    self._debug = debug

                def debug(self, msg):
                    if self._debug:
                        self.host.stepDone.emit(msg)

                def info(self, msg):
                    self.host.stepDone.emit(msg)

                def warning(self, msg):
                    self.host.stepWarn.emit(msg)

                def error(self, msg):
                    self.host.stepError.emit(msg)

            import _core_upgrader
            sgtk_install_folder = os.path.join(self._sgtk_folder, 'install')
            _core_upgrader.upgrade_tank(sgtk_install_folder, EmitLogger(self, debug=False))
        except Exception as e:
            self._logger.exception('Could not run upgrade script! Error reported: %s' % e)
            self.stepError.emit('Could not run upgrade script! Error reported: %s' % e)
            return

        self.stepDone.emit('Installing binary wrapper scripts...')
        self._logger.debug('Installing binary wrapper scripts...')
        src_dir = os.path.join(self._sgtk_folder, 'install', 'core', 'setup', 'root_binaries')
        if not os.path.exists(src_dir):
            self.stepError.emit('Looks like you are trying to download an old version of the Shotgun Pipeline Toolkit!')
            self._logger.error('Looks like you are trying to download an old version of the Shotgun Pipeline Toolkit!')
            return
        else:
            if self._auth is not None:
                utils.sudo_chmod(self._auth, self._sgtk_folder, 511)
            for file_name in os.listdir(src_dir):
                src_file = os.path.join(src_dir, file_name)
                tgt_file = os.path.join(self._sgtk_folder, file_name)
                shutil.copy(src_file, tgt_file)
                os.chmod(tgt_file, 509)

            if self._auth is not None:
                utils.sudo_chmod(self._auth, self._sgtk_folder, 509)
            data = {}
            data['description'] = '%s: Sgtk was activated' % self._server_url
            data['event_type'] = 'TankAppStore_Activation_Complete'
            data['entity'] = latest_core
            data['user'] = self._app_store_current_script_user_entity
            data['project'] = constants.SGTK_APP_STORE_DUMMY_PROJECT
            sg_app_store.create('EventLogEntry', data)
            return

    def _download_core(self, sg_studio_version, sg_app_store, studio_url, app_store_current_script_user_entity):
        """
        Downloads the latest core from the app store.
        Returns a path to the unpacked code in a tmp location
        """
        self.stepDone.emit('Finding the latest version of the Core API...')
        self._logger.debug('Finding the latest version of the Core API...')
        latest_core = sg_app_store.find_one(constants.SGTK_CORE_VERSION_ENTITY, filters=[['sg_status_list', 'is_not', 'rev'], ['sg_status_list', 'is_not', 'bad']], fields=['sg_min_shotgun_version', 'code', constants.SGTK_CODE_PAYLOAD_FIELD], order=[{'field_name': 'created_at',
          'direction': 'desc'}])
        if latest_core is None:
            raise Exception('Cannot find a version of the core system to download!Please contact support!')
        min_sg_version = latest_core['sg_min_shotgun_version']
        if min_sg_version:
            if min_sg_version.startswith('v'):
                min_sg_version = min_sg_version[1:]
            if LooseVersion(min_sg_version) > LooseVersion(sg_studio_version):
                raise Exception('Your shotgun installation is version %s but the Sgtk Core (%s) requires version %s. Please contact support.' % (sg_studio_version, latest_core['code'], min_sg_version))
        if 'SGTK_CORE_DEBUG_LOCATION' in os.environ:
            self.stepDone.emit("Using debug core from '%s'" % os.environ['SGTK_CORE_DEBUG_LOCATION'])
            self._logger.debug("Using debug core from '%s'" % os.environ['SGTK_CORE_DEBUG_LOCATION'])
            return (latest_core, os.environ['SGTK_CORE_DEBUG_LOCATION'])
        else:
            if latest_core[constants.SGTK_CODE_PAYLOAD_FIELD] is None:
                raise Exception('Cannot find an Sgtk binary bundle for %s. Please contact support' % latest_core['code'])
            self.stepDone.emit('Downloading Toolkit Core API %s from the App Store...' % latest_core['code'])
            self._logger.debug('Downloading Toolkit Core API %s from the App Store...' % latest_core['code'])
            zip_tmp = os.path.join(tempfile.gettempdir(), '%s_sgtk_core.zip' % uuid.uuid4().hex)
            extract_tmp = os.path.join(tempfile.gettempdir(), '%s_sgtk_unzip' % uuid.uuid4().hex)
            try:
                attachment_id = int(latest_core[constants.SGTK_CODE_PAYLOAD_FIELD]['url'].split('/')[-1])
            except:
                raise Exception('Could not extract attachment id from data %s' % latest_core)

            bundle_content = sg_app_store.download_attachment(attachment_id)
            fh = open(zip_tmp, 'wb')
            fh.write(bundle_content)
            fh.close()
            self.stepDone.emit('Download complete, now extracting content...')
            self._logger.debug('Download complete, now extracting content...')
            unzip_file(zip_tmp, extract_tmp)
            data = {}
            data['description'] = '%s: Core API was downloaded' % studio_url
            data['event_type'] = 'TankAppStore_CoreApi_Download'
            data['entity'] = latest_core
            data['user'] = app_store_current_script_user_entity
            data['project'] = constants.SGTK_APP_STORE_DUMMY_PROJECT
            data['attribute_name'] = constants.SGTK_CODE_PAYLOAD_FIELD
            sg_app_store.create('EventLogEntry', data)
            return (latest_core, extract_tmp)