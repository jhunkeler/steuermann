'''
Generate reports from the database
 
'''

import time
import sys
import sqlite3
import pandokia.text_table as text_table
import StringIO


def get_table_list( db, run_name ) :
    c = db.cursor()
    c.execute("select max(depth) as d, tablename from status where run = ? group by tablename order by d asc",(run_name,))
    table_list = [ x for x in c ]
        # table_list contains ( depth, tablename )
    return table_list

def get_table( db, run_name, tablename, info_callback ) :

    t = text_table.text_table()

    row = 0
    t.define_column('-')    # the command name in column 0

    c = db.cursor()
    c.execute("select distinct host from status where tablename = ? and run = ? order by host asc",(tablename, run_name))
    for host, in c :
        t.define_column(host)
        t.set_value(row, host, host)


    c.execute("""select cmd, host, depth, status, start_time, end_time, notes from status
        where tablename = ? and run = ?  order by depth, cmd asc
        """, ( tablename, run_name ) )

    prev_cmd = None
    for x in c :
        cmd, host, depth, status, start_time, end_time, notes = x
        if cmd != prev_cmd :
            row = row + 1
            t.set_value(row, 0, cmd)
            prev_cmd = cmd
        t.set_value( row, host, info_callback( tablename, cmd, host, status ) )

    t.pad()

    return t

def info_callback_status( tablename, cmd, host, status ) :
    return status

def report_text( db, run_name, info_callback = info_callback_status ) :

    s = StringIO.StringIO()

    table_list = get_table_list(db, run_name)

    for depth, tablename in table_list :
        s.write("------\n")
        s.write(tablename)
        s.write('\n')

        t = get_table( db, run_name, tablename, info_callback )

        s.write( t.get_trac_wiki() )

    return s.getvalue()

def report_html( db, run_name, info_callback = info_callback_status, hlevel=1 ) :
    s = StringIO.StringIO()
    s.write('<h%d>%s</h%d>\n'%(hlevel,run_name,hlevel))

    hlevel = hlevel + 1
    
    table_list = get_table_list(db, run_name)

    for depth, tablename in table_list :
        s.write('<h%d>%s</h%d>\n'%(hlevel,tablename,hlevel))
        t = get_table( db, run_name, tablename, info_callback )
        s.write(t.get_html())

    return s.getvalue()

def main() :
    db = sqlite3.connect('sr.db')
    print report_html( db, 'arf2011-08-30 16:52:23.928381' )

if __name__ == '__main__' :
    main()

