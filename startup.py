# Embedded file name: ..\Resources\startup.py
from __future__ import absolute_import
import os
import sys
import ConfigParser
import logging
import shotgun_desktop.splash
import shotgun_desktop.logging
shotgun_desktop.logging.initialize_logging()
logger = logging.getLogger('tk-desktop.bootstrap')
logger.info('------------------ Desktop Engine Bootstrap ------------------')
from PySide import QtGui
import shotgun_desktop.paths
import shotgun_desktop.version
from shotgun_desktop.turn_on_toolkit import TurnOnToolkit
from shotgun_desktop.initialization import initialize
from shotgun_desktop.ui import resources_rc
framework_python_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'tk-framework-login'))
logger.debug("adding '%s' to sys.path for login framework" % framework_python_dir)
sys.path.insert(0, framework_python_dir)
try:
    from python import ShotgunLogin
except ImportError:
    logger.exception('Could not import tk-framework-login')
    sys.exit(1)

sys.path.pop(0)

def __import_sgtk_from_path(path):
    python_path = os.path.join(path, 'install', 'core', 'python')
    logger.debug('loading sgtk from %s', python_path)
    if python_path not in sys.path:
        sys.path.insert(1, python_path)
    sys.path_importer_cache.clear()
    import sgtk
    return sgtk


def _get_configured_login_manager():
    login = ShotgunLogin.get_instance_for_namespace('tk-desktop')
    if sys.platform == 'darwin':
        login_config = os.path.join(shotgun_desktop.paths.get_shotgun_app_root(), 'Contents', 'Resources', 'config.ini')
    else:
        login_config = os.path.join(shotgun_desktop.paths.get_shotgun_app_root(), 'config.ini')
    if os.path.exists(login_config):
        config = ConfigParser.SafeConfigParser({'default_login': None,
         'default_site': None,
         'http_proxy': None})
        config.read(login_config)
        if config.has_section('Login'):
            default_login = config.get('Login', 'default_login', raw=True)
            default_site = config.get('Login', 'default_site', raw=True)
            http_proxy = config.get('Login', 'http_proxy', raw=True)
            if default_login is not None:
                default_login = os.path.expandvars(default_login)
                login.set_default_login(default_login)
            if default_site is not None:
                default_site = os.path.expandvars(default_site)
                login.set_default_site(default_site)
            if http_proxy is not None:
                http_proxy = os.path.expandvars(http_proxy)
                login.set_http_proxy(http_proxy)
    return login


def _get_default_site_config_root(splash, connection, login):
    while True:
        try:
            default_site_config, _ = shotgun_desktop.paths.get_default_site_config_root(connection)
            break
        except shotgun_desktop.paths.NoPipelineConfigEntityError:
            splash.hide()
            dialog = TurnOnToolkit(connection, login)
            dialog.raise_()
            dialog.activateWindow()
            results = dialog.exec_()
            if results == dialog.Rejected:
                sys.exit(0)
            continue

    return default_site_config


def main():
    try:
        app = QtGui.QApplication(sys.argv)
    except Exception as error:
        logger.exception('Could not create QApp')
        QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error starting Toolkit, please contact support.\n%s' % error)
        sys.exit(1)

    try:
        login = _get_configured_login_manager()
        connection = login.get_connection()
        if not connection:
            logger.info('Login canceled.  Quitting.')
            sys.exit(0)
    except Exception as error:
        logger.exception('Could not get Shotgun connection')
        QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error starting the Toolkit, please contact support.\n%s' % error)
        sys.exit(1)

    splash = shotgun_desktop.splash.Splash()
    splash.show()
    splash.set_message('Looking up site configuration.')
    app.processEvents()
    try:
        default_site_config = _get_default_site_config_root(splash, connection, login)
        splash.show()
    except Exception as error:
        logger.exception('could not get default_site_config')
        QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error starting the Toolkit, please contact support.\n%s' % error)
        splash.hide()
        sys.exit(1)

    toolkit_imported = False
    try:
        if os.path.exists(default_site_config):
            logger.debug("Trying site config from '%s'" % default_site_config)
            sgtk = __import_sgtk_from_path(default_site_config)
            toolkit_imported = True
    except Exception:
        pass

    if not toolkit_imported:
        logger.debug('initial sgtk import failed')
        try:
            app.processEvents()
            splash.set_message('Initializing Toolkit')
            core_path = initialize(splash, connection)
        except Exception as error:
            logger.exception('could not initialize toolkit')
            QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error starting the Toolkit, please contact support.\n%s' % error)
            sys.exit(1)

        try:
            sgtk = __import_sgtk_from_path(core_path)
            if sgtk is None:
                logger.info('Could not access API post initialization.')
                QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Could not access API post initialization, please contact support.')
                sys.exit(0)
            splash.set_message('Setting up default site configuration...')
            sg = sgtk.util.shotgun.create_sg_connection()
            template_project = sg.find_one('Project', [['name', 'is', 'Template Project'], ['layout_project', 'is', None]])
            if template_project is None:
                logger.exception('Template project not found.')
                QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error finding the Template project on your site, please contact support.')
                sys.exit(1)
            default_site_config, _ = shotgun_desktop.paths.get_default_site_config_root(sg)
            if not os.path.exists(default_site_config):
                os.makedirs(default_site_config)
            if sys.platform == 'darwin':
                path_param = 'config_path_mac'
            elif sys.platform == 'win32':
                path_param = 'config_path_win'
            elif sys.platform.startswith('linux'):
                path_param = 'config_path_linux'
            config_uri = os.environ.get('SGTK_SITE_CONFIG_DEBUG_LOCATION', 'tk-config-site')
            params = {'auto_path': True,
             'config_uri': config_uri,
             'project_folder_name': 'site',
             'project_id': template_project['id'],
             path_param: default_site_config}
            setup_project = sgtk.get_command('setup_project')
            setup_project.set_logger(logger)
            setup_project.execute(params)
            sgtk = __import_sgtk_from_path(default_site_config)
            tk = sgtk.sgtk_from_path(default_site_config)
            splash.set_message('Localizing core...')
            localize = tk.get_command('localize')
            localize.set_logger(logger)
            localize.execute({})
        except Exception as error:
            splash.hide()
            logger.exception('Error importing sgtk after initialization')
            QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error starting the Toolkit, please contact support.\n%s' % error)
            sys.exit(1)

    try:
        tk = sgtk.sgtk_from_path(default_site_config)
        if tk.pipeline_configuration.is_auto_path():
            splash.set_message('Getting updates...')
            app.processEvents()
            core_update = tk.get_command('core')
            core_update.set_logger(logger)
            core_update.execute({})
            sgtk = __import_sgtk_from_path(default_site_config)
            tk = sgtk.sgtk_from_path(default_site_config)
            updates = tk.get_command('updates')
            updates.set_logger(logger)
            updates.execute({})
        splash.set_message('Starting desktop engine.')
        app.processEvents()
        ctx = tk.context_empty()
        engine = sgtk.platform.start_engine('tk-desktop', tk, ctx)
        shotgun_desktop.logging.tear_down_logging()
    except Exception as error:
        splash.hide()
        logger.exception('Error starting tk-desktop')
        QtGui.QMessageBox.critical(None, 'Toolkit Error', 'Error starting the Desktop engine, please contact support.\n%s' % error)
        sys.exit(1)

    if 'SGTK_DESKTOP_ORIGINAL_PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = os.environ['SGTK_DESKTOP_ORIGINAL_PYTHONPATH']
    if 'SGTK_DESKTOP_ORIGINAL_PYTHONHOME' in os.environ:
        os.environ['PYTHONHOME'] = os.environ['SGTK_DESKTOP_ORIGINAL_PYTHONHOME']
    try:
        exit_value = engine.run(splash, version=shotgun_desktop.version.DESTKOP_APPLICATION_VERSION)
    except Exception:
        splash.hide()
        logger.exception('Error while running tk-desktop')
        exit_value = -1

    os._exit(exit_value)
    return