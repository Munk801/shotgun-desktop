# Embedded file name: ..\Resources\paths.py
import os
import sys
import urlparse

class NoPipelineConfigEntityError(Exception):
    """ Error raised when the PipelineConfiguration entity is not available. """
    pass


def get_shotgun_app_root():
    """ returns where the shotgun app is installed """
    if sys.platform == 'darwin':
        args = [os.path.dirname(__file__)] + ['..'] * 5
        shotgun_root = os.path.abspath(os.path.join(*args))
    elif sys.platform == 'win32':
        shotgun_root = os.path.abspath(os.path.dirname(sys.prefix))
    elif sys.platform.startswith('linux'):
        shotgun_root = os.path.abspath(os.path.dirname(sys.prefix))
    else:
        raise NotImplementedError('Unsupported platform: %s' % sys.platform)
    return shotgun_root


def get_python_path():
    """ returns the path to the default python interpreter """
    if sys.platform == 'darwin':
        python = os.path.join(sys.prefix, 'bin', 'python')
    elif sys.platform == 'win32':
        python = os.path.join(sys.prefix, 'python.exe')
    elif sys.platform.startswith('linux'):
        python = os.path.join(sys.prefix, 'bin', 'python')
    return python


def get_default_site_config_root(connection):
    """ return the path to the default configuration for the site """
    if sys.platform == 'darwin':
        plat_key = 'mac_path'
    elif sys.platform == 'win32':
        plat_key = 'windows_path'
    elif sys.platform.startswith('linux'):
        plat_key = 'linux_path'
    else:
        raise RuntimeError('unknown platform: %s' % sys.platform)
    fields = ['id',
     'code',
     'windows_path',
     'mac_path',
     'linux_path']
    try:
        pc = connection.find_one('PipelineConfiguration', [['project.Project.name', 'is', 'Template Project'], ['project.Project.layout_project', 'is', None]], fields=fields)
    except Exception:
        pc_schema = connection.schema_entity_read().get('PipelineConfiguration')
        if pc_schema is None:
            raise NoPipelineConfigEntityError()
        raise

    if pc is not None and pc.get(plat_key, ''):
        return (str(pc[plat_key]), pc)
    else:
        if sys.platform == 'darwin':
            pc_root = os.path.expanduser('~/Library/Application Support/Shotgun')
        elif sys.platform == 'win32':
            pc_root = os.path.join(os.environ['APPDATA'], 'Shotgun')
        elif sys.platform.startswith('linux'):
            pc_root = os.path.expanduser('~/.shotgun')
        site = __get_site_from_connection(connection)
        pc_root = os.path.join(pc_root, site, 'site')
        return (str(pc_root), pc)


def __get_site_from_connection(connection):
    """ return the site from the information in the connection """
    site = urlparse.urlparse(connection.base_url)[1].split(':')[0]
    return site