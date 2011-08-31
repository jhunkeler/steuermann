#! python

import cgi
import cgitb

cgitb.enable()

form = cgi.FieldStorage(keep_blank_values=1)
cginame = os.getenv("SCRIPT_NAME")

import sqlite3

if not 'action' in form :
    print 'content-type: text/html'
    print ''
    db = sqlite3.connect('db.sr')
    c = db.cursor()
    c.execute('SELECT DISTINCT run FROM status ORDER BY run ASC')
    for run, in c :
        print "<a href=%s?action=report&run=%s>%s</a><br>"%(cginame, run, run)
    return

action = form['action'].value

if action == 'report' :
    import steuermann.report
    print 'content-type: text/html'
    print ''
    run = form['run'].value
    print steuermann.report.report_html( db, run )
    return

print 'content-type: text/html'
print ''
print 'no action?'

