from __future__ import print_function
import os
import sys

_path = sys.path.copy()

#if not os.path.exists(config_dir):
#    os.makedirs(config_dir, mode=0o700)

try:
    # We don't care if this config does exist, we have further options to test
    config_dir = ''
    if 'STEUERMANN_CONFIG' in os.environ:
        config_dir = os.path.abspath(os.environ['STEUERMANN_CONFIG'])
    user_config = os.path.join(config_dir, 'config.py')
    hosts_config = os.path.join(config_dir, 'hosts.ini')

    sys.path.insert(1, config_dir)
    import config

except ImportError:
    config_dir = os.path.join(os.path.expanduser('~'), '.steuermann', 'default')
    user_config = os.path.join(config_dir, 'config.py')
    hosts_config = os.path.join(config_dir, 'hosts.ini')

    sys.path = _path
    sys.path.insert(1, config_dir)
    try:
        import config
    except ImportError as e:
        print(e)
        print('FATAL: Missing config (i.e. {0})'.format(user_config))
        exit(1)

print("Using: {0}".format(config_dir))
db_creds = config.db_creds


def open_db():
    import sqlite3
    return sqlite3.connect(db_creds)

logdir = config.logdir
host_logs = config.host_logs
