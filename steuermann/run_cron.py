import os
import sys
import time
import steuermann.config
import steuermann.run
import datetime

# bugs:
# - this is a hideous hack that works around run.py not being designed for this
# - the work directory on the target machine is poorly named
#

class fakenode(object): 
    pass

def main() :

    if len(sys.argv) < 4 :
        print "smcron host name command"
        print "(from ",sys.argv,")"
        sys.exit(1)

    host = sys.argv[1]
    name = sys.argv[2]
    script = ' '.join(sys.argv[3:])

    db = steuermann.config.open_db()

    c = db.cursor()

    start_time = datetime.datetime.now()
    day, tod = str(start_time).split(' ')

    name = name + '--' + tod

    logfile = '%s/%s.%s' % (day, host, name)

    # something to reduce the possibility of a collision to very small - in this case, we assume that 
    # we can't start multiple processes at the same time from the same process number.  i.e. the
    # pid can not wrap in less than 1 clock tick
    decollision = os.getpid()

    c.execute("INSERT INTO sm_crons ( host, name, start_time, logfile, decollision ) VALUES ( ?, ?, ?, ?, ? )",
        ( host, name, str(start_time), logfile, decollision ) )
    db.commit()

    # this is a hideous hack to plug on to an interface that was not designed for this

    node = fakenode()
    node.host = host
    node.name = 'cron.' + name
    node.table = None
    node.cmd = None
    node.script = script
    if host == 'localhost' :
        node.script_type = 'l'  # local
    else :
        node.script_type = 'r'  # remote
    
    runner = steuermann.run.runner( nodes = { node.name : node } )
    runner.run( node=node, run_name='', logfile_name = steuermann.config.logdir + '/cron/' + logfile )

    n = 0.1
    while 1 :
        exited = runner.poll()
        if exited :
            break
        if n < 2.0 :
            n = n * 2.0
        time.sleep(n)
    
    status = exited[1]

    end_time = datetime.datetime.now()
    td = end_time - start_time

    # only 1 decimal place because we don't poll often enough to make more reasonable.
    td = "%.1f" % ( td.microseconds/1e6 + td.seconds + td.days * 24 * 3600 )
    c.execute("UPDATE sm_crons SET end_time = ?, status = ?, duration = ? WHERE host = ? AND name = ? ",
        (str(end_time), status, td, host, name ) )
    db.commit()

