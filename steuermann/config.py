db_creds = '/ssbwebv1/data2/steuermann/steuermann.db'

def open_db() :
    import sqlite3
    return sqlite3.connect(db_creds)

logdir = '/ssbwebv1/data2/steuermann/logs'
