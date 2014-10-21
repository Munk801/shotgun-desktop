# Embedded file name: ..\Resources\initialization\shotgun.py
import json
import urllib
import urllib2
import urlparse
from shotgun_api3 import Shotgun
from . import constants

def is_server_valid(connection):
    """ Validate the shotgun server """
    sg_major_ver = connection.server_info['version'][0]
    sg_minor_ver = connection.server_info['version'][1]
    if sg_major_ver < 5 or sg_major_ver == 5 and sg_minor_ver < 1:
        return False
    return True


def get_or_create_script(connection):
    """ Find the Toolkit script in Shotgun or create it if it does not exist """
    script = connection.find_one('ApiUser', [['firstname', 'is', 'Toolkit']], fields=['firstname', 'salted_password'])
    if script is not None:
        return script
    else:
        permission_rule_set = connection.find_one('PermissionRuleSet', [['entity_type', 'is', 'ApiUser'], ['code', 'is', 'api_admin']])
        data = {'description': 'Shotgun Toolkit API Access',
         'email': 'toolkitsupport@shotgunsoftware.com',
         'firstname': 'Toolkit',
         'lastname': '1.0',
         'generate_event_log_entries': True}
        if permission_rule_set is not None:
            data['permission_rule_set'] = permission_rule_set
        script = connection.create('ApiUser', data)
        script = connection.find_one('ApiUser', [['id', 'is', script['id']]], fields=['firstname', 'salted_password'])
        return script


def get_app_store_credentials(connection):
    """ Return the validated script for this site to connect to the app store """
    script, key = __get_app_store_key(connection)
    proxy_server = connection.config.proxy_server
    proxy = None
    if proxy_server is not None:
        proxy_port = connection.config.proxy_port
        proxy_user = connection.config.proxy_user
        proxy_pass = connection.config.proxy_pass
        if proxy_user is not None:
            proxy = '%s:%s@%s:%s' % (proxy_user,
             proxy_pass,
             proxy_server,
             proxy_port)
        else:
            proxy = '%s:%s' % (proxy_server, proxy_port)
    try:
        sg_app_store = Shotgun(constants.SGTK_APP_STORE, script, key, http_proxy=proxy)
        app_store_script = sg_app_store.find_one('ApiUser', [['firstname', 'is', script]], fields=['type',
         'firstname',
         'id',
         'salted_password'])
    except Exception:
        return

    return app_store_script


def __get_app_store_key(connection):
    """ Return the script for this site to connect to the app store """
    toolkit_script = get_or_create_script(connection)
    proxy_user = connection.config.proxy_user
    proxy_pass = connection.config.proxy_pass
    proxy_server = connection.config.proxy_server
    proxy_port = connection.config.proxy_port
    if proxy_server is not None:
        scheme, _, _, _, _ = urlparse.urlsplit(connection.base_url)
        if proxy_user and proxy_pass:
            auth_string = '%s:%s@' % (proxy_user, proxy_pass)
        else:
            auth_string = ''
        proxy_addr = 'http://%s%s:%d' % (auth_string, proxy_server, proxy_port)
        proxy_handler = urllib2.ProxyHandler({scheme: proxy_addr})
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)
    post_data = {'script_name': toolkit_script['firstname'],
     'script_key': toolkit_script['salted_password']}
    response = urllib2.urlopen('%s/api3/sgtk_install_script' % connection.base_url, urllib.urlencode(post_data))
    html = response.read()
    data = json.loads(html)
    return (data['script_name'], data['script_key'])