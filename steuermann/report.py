'''
Generate reports from the database
 
'''

import time
import sys
import pandokia.text_table as text_table
import StringIO

# this will be reset by the cgi main program if we are in a real cgi
cginame = 'arf.cgi'

#

def info_callback_status( db, run, tablename, host, cmd ) :
    c = db.cursor()
    c.execute("SELECT status FROM status WHERE run = ? AND host = ? AND tablename = ? AND cmd = ?",(
            run, host, tablename, cmd ) )
    status, = c.fetchone()
    return status

#

def info_callback_gui( db, run, tablename, host, cmd ) :
    c = db.cursor()
    c.execute("SELECT status, start_time, end_time FROM status WHERE run = ? AND host = ? AND tablename = ? AND cmd = ?",(
            run, host, tablename, cmd ) )
    x = c.fetchone()
    if x is None :
        return ''
    status, start_time, end_time = x
    if start_time is None :
        start_time = ''
    if end_time is None :
        end_time = ''

    # t_result = '%s %s %s'%(status, start_time, end_time )
    t_result = status

    if status != '0' and status != 'N' :
        status = '<font color=red>%s</font>'%status

    if status != 'N' and status != 'P' :
        link = "<a href='%s?action=log&name=%s/%s:%s/%s'>*</a>"%(cginame, run, host, tablename, cmd )
    else :
        link = ''

    # h_result = '%s %s %s %s'%(link, status, start_time, end_time)
    h_result = '%s %s'%(link, status )

    return ( t_result, h_result )

# 

def info_callback_debug_table_cell( db, run, tablename, cmd, host ) :
    return '%s %s %s %s' % ( run, host, tablename, cmd )

#

def get_table_list( db, run_name ) :
    c = db.cursor()
    c.execute("select max(depth) as d, tablename from status where run = ? group by tablename order by d asc",(run_name,))
    table_list = [ x for x in c ]
        # table_list contains ( depth, tablename )
    return table_list

def get_table( db, run_name, tablename, info_callback, showdepth=0 ) :

    t = text_table.text_table()
    t.set_html_table_attributes('border=1')

    t.define_column('-',html='&nbsp;',showname='-')    # the command name in column 0

    if showdepth :
        t.define_column('depth')

    c = db.cursor()
    c.execute("select distinct host from status where tablename = ? and run = ? order by host asc",(tablename, run_name))
    for host, in c :
        t.define_column(host)

    c.execute("""select cmd, host, depth, status, start_time, end_time, notes from status
        where tablename = ? and run = ?  order by depth, cmd asc
        """, ( tablename, run_name ) )

    row = -1
    prev_cmd = None
    for x in c :
        cmd, host, depth, status, start_time, end_time, notes = x
        if cmd != prev_cmd :
            row = row + 1
            t.set_value(row, 0, cmd)
            if showdepth :
                t.set_value(row, 'depth', depth)
            prev_cmd = cmd
            
        info = info_callback( db, run_name, tablename, host, cmd )
        if isinstance(info, tuple) :
            t.set_value( row, host, text=info[0], html=info[1] )
        else :
            t.set_value( row, host, info) 

    t.pad()

    return t

#

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

#

def report_html( db, run_name, info_callback = info_callback_status, hlevel=1 ) :
    s = StringIO.StringIO()
    s.write('<h%d>%s</h%d>\n'%(hlevel,run_name,hlevel))

    hlevel = hlevel + 1
    
    table_list = get_table_list(db, run_name)

    for depth, tablename in table_list :
        s.write('<h%d>%s</h%d>\n'%(hlevel,tablename,hlevel))
        t = get_table( db, run_name, tablename, info_callback, showdepth=1 )
        s.write(t.get_html())

    return s.getvalue()

#
def main() :
    import steuermann.config
    db = steuermann.config.open_db()
    print report_html( db, 'arf2011-08-30 16:52:23.928381' )

if __name__ == '__main__' :
    main()

