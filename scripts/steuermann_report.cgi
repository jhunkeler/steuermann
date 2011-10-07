#! python

import cgi
import cgitb
import os
import sys
import re
import datetime
import pandokia.text_table

STEUERMANN_DIR_HERE
sys.path.insert(0, addpath)

import steuermann.config
import steuermann.run_all

cgitb.enable()

form = cgi.FieldStorage(keep_blank_values=1)
cginame = os.getenv("SCRIPT_NAME")

permission_modify=1

html_header='''Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<HTML>
<HEAD>
<TITLE>%(title)s</TITLE>
</HEAD>
<BODY>
'''

html_trailer='''
</BODY>
</HTML>
'''

##########

def sqltime(arg) :
    if arg is None :
        return None

    if '.' in arg :
        x = arg.split('.')
        d = datetime.datetime.strptime(x[0],'%Y-%m-%d %H:%M:%S')
        d = d.replace(microsecond=int((x[1]+'000000')[0:6]))
    else :
        x = time.strptime(arg,'%Y-%m-%d %H:%M:%S')
        d = datetime.datetime(year=x[0], month=x[1], day=x[2],
        hour=x[3], minute=x[4], second=x[5] )
        # not in 2.4:
        # d = datetime.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
    return d


##########

def normalize_run_name(db, name) :
    
    if name == 'daily_latest' :
        c = db.execute("SELECT max(run) FROM sm_runs WHERE run like 'daily_%'")
        run, = c.fetchone()
        return run

    return name

##########
# if no action specified, show the list of runs
#
if 'action' in form :
    action = form['action'].value
else :
    action = 'index'

if action == 'index' :
    print html_header % { 'title' : 'Steuermann' }
    print "<a href=%s?action=runs>runs</a><br>"%cginame
    print "<a href=%s?action=crons>crons</a><br>"%cginame
    print html_trailer
    sys.exit(0)

    
##########
# list the runs

elif action == 'crons' :
    print html_header % { 'title' : 'Steuermann List' }
    db = steuermann.config.open_db()
    c = db.cursor()

    c.execute("SELECT host, name, decollision, start_time, end_time, duration, status FROM sm_crons ORDER BY start_time desc")

    tt = pandokia.text_table.text_table()
    tt.set_html_table_attributes("border=1")
    tt.define_column('host')
    tt.define_column('name')
    tt.define_column('start_time')
    tt.define_column('end_time')
    tt.define_column('duration')
    tt.define_column('status')
    if permission_modify :
        tt.define_column('delete')

    link="%s?action=%s&host=%s&name=%s&decol=%s"
    for host, name, decollision, start_time, end_time, duration, status in c :
        row = tt.get_row_count()
        short_name = name.split('--')[0]
        tt.set_value(row, 'host',       host )
        tt.set_value(row, 'name',       text=short_name, link=link%(cginame,'cronlog',host,name,decollision) )
        tt.set_value(row, 'start_time', start_time)
        if end_time is None :
            end_time = ''
        if end_time.startswith(start_time[0:11]) :
            tt.set_value(row, 'end_time',   end_time[11:])
        else :
            tt.set_value(row, 'end_time',   end_time)
        tt.set_value(row, 'duration',   duration)
        tt.set_value(row, 'status',     status)
        if permission_modify :
            tt.set_value(row, 'delete', 'arf')

    print tt.get_html()
    print html_trailer
    sys.exit(0)

elif action == 'runs' :
    print html_header % { 'title' : 'Steuermann List' }
    print 'sort: '
    for x in ( 'name_asc', 'name_desc', 'time_asc', 'time_desc' ) :
        print "<a href=%s?action=runs&order=%s>%s</a>"%(cginame,x,x)
    print "<br><br>"
    db = steuermann.config.open_db()
    c = db.cursor()
    order='create_time DESC'

    if 'order' in form :
        x = form['order'].value
        if x == 'name_asc' :
            order = 'run ASC'
        elif x == 'name_desc' :
            order = 'run DESC'
        elif x == 'time_asc' :
            order ='create_time ASC'
        elif x == 'time_desc' :
            order ='create_time DESC'

    c.execute('SELECT DISTINCT run, create_time FROM sm_runs ORDER BY %s'%order)
    print "<table>"
    for run, create_time in c :
        print "<tr>"
        print "<td>"
        print "<a href=%s?action=status&run=%s>%s</a>"%(cginame, run, run)
        print "</td><td>"
        if permission_modify :
            print "<a href=%s?action=delete&run=%s>delete</a>"%(cginame, run)
        print "</td>"
        print "</tr>"
    print "</table>"
    print html_trailer
    sys.exit(0)

##########
# status means show the status of a particular run
#
elif action == 'delete' :
    if permission_modify :
        print 'content-type: text/plain\n'
        in_run = form['run'].value
        db = steuermann.config.open_db()
        in_run = normalize_run_name(db,in_run)
        c = db.cursor()
        c1 = db.cursor()
        print "RUN=",in_run
        c.execute("SELECT run FROM sm_runs WHERE run LIKE ?",(in_run,))
        for run, in c :
            print "echo run ",run
            filename = '%s/run/%s'%(steuermann.config.logdir,run)
            print "rm -rf ",filename
        c.execute("DELETE FROM sm_runs WHERE run LIKE ?",(in_run,))
        db.commit()
        sys.exit(0)

##########
# 

elif action == 'status' :
    db = steuermann.config.open_db()
    import steuermann.report
    steuermann.report.cginame = cginame
    print html_header % { 'title' : 'Steuermann Status' }
    print ''
    run = form['run'].value
    run = normalize_run_name(db,run)
    print steuermann.report.report_html( db, run, info_callback=steuermann.report.info_callback_gui )
    print html_trailer
    sys.exit(0)
    

elif action == 'cronlog' :
    print 'content-type: text/plain'
    print ''
    host  = form['host'].value
    name  = form['name'].value
    decol = form['decol'].value
    db = steuermann.config.open_db()
    c = db.cursor()

    c.execute("SELECT host, name, decollision, start_time, end_time, status, logfile FROM sm_crons WHERE host = ? AND name = ? and decollision = ?", (host, name, decol) )
    for host, name, decollision, start_time, end_time, status, logfile in c :
        print "----------"
        print "%s: %s\n"%(host,name)
        print "decol=%s"%decollision
        print start_time
        print end_time
        print "status=",status
        print "----------"
        f=open( steuermann.config.logdir + '/cron/' + logfile,"r")
        sys.stdout.write(f.read())
        f.close()
    sys.exit(0)

##########
# log means show the result of a particular node from a run
#
elif action == 'log' :
    print 'content-type: text/plain'
    print ''

    # crack apart the parameter run/host:table/cmd
    name = re.match('(.*)/(.*):(.*)/(.*)', form['name'].value)
    run = name.group(1)
    host = name.group(2)
    table = name.group(3)
    cmd = name.group(4)


    db = steuermann.config.open_db()
    c = db.cursor()
    c.execute("SELECT status, start_time, end_time, notes FROM sm_status WHERE run = ? AND host = ? AND tablename = ? AND cmd = ?",(
            run, host, table, cmd ) )
    x = c.fetchone()
    if x is None :
        print "No such record in database",run,host,table,cmd
        sys.exit(0)

    status, start_time, end_time, notes = x

    print "%s %s:%s/%s"%(run, host, table, cmd)
    print "status: %s"%status
    print ""
    print "start: %s"%start_time
    print "end  : %s"%end_time
    start_time = sqltime(start_time)
    end_time = sqltime(end_time)
    if isinstance(end_time,datetime.datetime) and isinstance(end_time,datetime.datetime) :
        print "dur  : %s"%(end_time-start_time)

    if not notes is None :
        print "notes:"
        for x in [ '    ' + x for x in notes.split('\n') ] :
            print x
    print ""
    loglist = [ steuermann.run_all.make_log_file_name( run, host, table, cmd),
        # compat mode until we delete the old files
        '%s/%s/%s:%s.%s.log'%(steuermann.config.logdir,run,host,table,cmd),
        # more compat mode
        '%s/run/%s/%s:%s.%s.log'%(steuermann.config.logdir,run,host,table,cmd),
        ]

    for filename in loglist :
        try :
            f=open(filename,'r')
            break
        except IOError:
            f = None
        
    if f :
        print "--------------------"
        while 1 :
            x = f.read(65536)
            if x == '' :
                break
            sys.stdout.write(x)
    else :
        print "No log file found.  tried "
        print loglist

    sys.exit(0)

##########
# info means show information about the system
#
elif action == 'info' :
    print html_header % { 'title': 'Steuermann Info' }
    print 'db credentials: ',steuermann.config.db_creds,'<br>'
    print 'logdir: ',steuermann.config.logdir,'<br>'
    db = steuermann.config.open_db()
    cur = db.cursor()
    cur.execute("select count(*) from sm_status")
    l = cur.fetchone()
    print "database records: %s\n"%l[0],'<br>'
    cur.execute("select count(*) from sm_runs")
    l = cur.fetchone()
    print "runs: %s\n"%l[0],'<br>'
    print html_trailer
    sys.exit(0)

##########

print html_header
print ''
print 'no recognized action?'
print html_trailer
