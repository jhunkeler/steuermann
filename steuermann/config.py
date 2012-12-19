db_creds = 'steuermann.db'

def open_db() :
    import sqlite3
    return sqlite3.connect(db_creds)

logdir = 'logs'
host_logs = 'host_logs'
