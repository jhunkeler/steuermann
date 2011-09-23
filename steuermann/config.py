def open_db() :
    import sqlite3
    return sqlite3.connect('/ssbwebv1/data2/steuermann/steuermann.db')

logdir = '/ssbwebv1/data2/steuermann/logs'
