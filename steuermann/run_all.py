'''
run everything in a set of command files
 
'''

import time
import sys
import sqlite3

import run

import datetime

import nodes


#####

def main() :
    global xnodes
    # read all the input files
    
    di_nodes = nodes.read_file_list( sys.argv[2:] )

    xnodes = di_nodes.node_index
    run_name = 'arf' + str(datetime.datetime.now())
    db = sqlite3.connect('sr.db')
    register_database(db, run_name, xnodes)

    n = sys.argv[1]
    if n == '-a' :
        run_all(xnodes, run_name, db)
    elif n == '-i' :
        run_interactive( xnodes, run_name, db )
    else :
        print "%s ?"%n


def do_flag( xnodes, name, recursive, fn, verbose ) :
    if verbose :
        verbose = verbose + 1
    if not ':' in name :
        name = '*:' + name
    if ( '*' in name )  or ( '?' in name ) or ( '[' in name ) :
        if verbose :
            print '  '*verbose, "wild",name
        for x in xnodes :
            if nodes.wildcard_name( name, x ) :
                if verbose :
                    print '  '*verbose, "match",x
                do_flag( xnodes, x, recursive, fn, verbose )
    elif name in xnodes :
        if verbose :
            print '  '*verbose, "found",name
        fn(xnodes[name])
        if recursive :
            for y in xnodes[name].predecessors : 
                do_flag( xnodes, y.name, recursive, fn, verbose )
    else :
            if verbose :
                print '  '*verbose, "not in list", name
            raise Exception()

def set_want( node ) :
    node.wanted = 1
    node.skip = 0

def set_skip( node ) :
    node.wanted = 0
    node.skip = 1


def cmd_flagging( l, xnodes, func ) :
    if l[1] == '-r' :
        recursive = 1
        l = l[2:]
    else :
        recursive = 0
        l = l[1:]
    
    for x in l :
        do_flag( xnodes, x, recursive, func, 1 )

helpstr = """
report              show report 
want [-r] node      declare that we want that node
skip [-r] node      skip this node
list -a
list node
start
wait
wr                  report want/skip values
wd                  report depth
"""

def run_interactive( xnodes, run_name, db) :

    runner = run.runner( xnodes )

    for x in xnodes :
        xnodes[x].finished = 0
        xnodes[x].running  = 0
        xnodes[x].wanted   = 0
        xnodes[x].skip     = 0

    keep_running = 0

    while 1 :
        print "action?"
        l = sys.stdin.readline()
        if l == '' :
            break
        l = l.strip()
        l = l.split()
        if len(l) > 0 :
            n = l[0]
        else :
            n = ''

        if n == '?' :
            print helpstr

        elif n == 'report' :
            report( db, run_name )

        elif n == 'wr' :
            report( db, run_name, info_callback_want )

        elif n == 'wd' :
            report( db, run_name, info_callback_depth )

        elif n == 'want' :
            cmd_flagging( l, xnodes, set_want )

        elif n == 'skip' :
            cmd_flagging( l, xnodes, set_skip )

        elif n == 'list' :
            print_all = '-a' in l
            l = sorted ( [ x for x in xnodes ] )
            print "w f s name"
            for x in l :
                print xnodes[x].wanted, xnodes[x].finished, xnodes[x].skip,  x
                if print_all :
                    print "       AFTER", '  '.join([ a.name for a in xnodes[x].predecessors ])

        elif n == 'start' :
            keep_running = 1

        elif n == 'wait' :
            while 1 :
                ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )
                if not keep_running :
                    break
                if not no_sleep :
                    time.sleep(1)
                if keypress() :
                    print "wait interrupted (processes continue)"
                    break
            print "wait finished"

        if keep_running :
            print "run step"
            ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )

            if len(runner.all_procs) == 0 :
                # give it a chance to start another
                ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )

            if not keep_running :
                    print 'all done'

            else :
                if len(runner.all_procs) == 0 :
                    print "no processes running - some prereq not satisfiable"
        


def register_database(db, run, xnodes ) :
    c = db.cursor()
    c.execute('INSERT INTO runs ( run ) VALUES ( ? )', ( run, ) )
    
    c = db.cursor()
    for x in xnodes :
        host, tablename, cmd = nodes.crack_name(x)
        depth = xnodes[x].depth
        c.execute("INSERT INTO status ( run, host, tablename, cmd, depth, status ) VALUES "
            "( ?, ?, ?, ?, ?, 'N' )", ( run, host, tablename, cmd, depth ) )

    db.commit()

def run_all(xnodes, run_name, db) :

    runner = run.runner( xnodes )

    for x in xnodes :
        xnodes[x].finished = 0
        xnodes[x].running  = 0
        xnodes[x].wanted   = 1

    while 1 :
        ( keep_running, no_sleep ) = run_step( runner, xnodes, run_name, db )
        if not keep_running :
            break
        if not no_sleep :
            time.sleep(1)

def run_step( runner, xnodes, run_name, db ) :
    
        # flag to keep running 
        keep_running = 0

        # flag to suppress brief sleep at end of loop
        no_sleep = 0

        # Loop, polling for work to do, or for finishing processes
        print "loop"
        for x_name in xnodes :
            x=xnodes[x_name]

            # skip nodes that we do not need to consider running because

            # - we explicitly ask to skip it; also mark it finished
	        # so that things that come after can run
            if x.skip :
                x.finished = 1
                continue

            # - it is not wanted
            if not x.wanted :
                continue

            # - it is already finished
            if x.finished :
                continue

            # - we are already running it
            if x.running :
                keep_running=1
                continue

            # ok, if we are here, we found a node that we want to run

            # if there is a node we need to run, we need to come back through the loop
            # (bug: are we sure there is not a deadlock caused by mutual dependencies? if that happens, it can never run.)
            keep_running = 1
            
            # count how many of the predecessors are finished
            released = sum( [ xnodes[r].finished for r in x.released ])

            # if the number of predecessors finished is the number
            # of predecessors, we can run this one
            if released == len(x.released) :
                host, table, cmd = nodes.crack_name(x_name)
                print "RUN", x_name

                db.execute("UPDATE status SET start_time = ?, status = 'S' WHERE ( run = ? AND host = ? AND tablename = ? AND cmd = ? )",
                    ( str(datetime.datetime.now()), run_name, host, table, cmd ) )
                db.commit()
                runner.run(x, run_name)

        # if anything has exited, we process it and update the status in the database
        while 1 :
            who_exited = runner.poll() 
            if not who_exited :
                break

            # yes, something exited - no sleep, and keep running
            no_sleep = 1
            keep_running = 1

            # note who and log it
            x_host, x_table, x_cmd = nodes.crack_name(who_exited[0])

            xnodes[who_exited[0]].wanted = 0

            db.execute("UPDATE status SET end_time = ?, status = ?  WHERE ( run = ? AND host = ? AND tablename = ? AND cmd = ? )",
                    ( str(datetime.datetime.now()), who_exited[1], run_name, x_host, x_table, x_cmd ) )


        runner.display_procs()

        return ( keep_running, no_sleep )

#####

ms_windows = 0

if ms_windows :
    import msvcrt
else :
    import select

def keypress() :
    if ms_windows :
        return msvcrt.kbhit()
    else :
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

#####

def info_callback_status( tablename, cmd, host, status ) :
    return status

def info_callback_want( tablename, cmd, host, status ) :
    n = xnodes['%s:%s/%s'%(host,tablename,cmd)]
    s = ''
    if n.skip :
        s = s + 'S'
    if n.wanted :
        s = s + 'W'
    if s == '' :
        s = '-'
    return s

def info_callback_depth( tablename, cmd, host, status ) :
    n = xnodes['%s:%s/%s'%(host,tablename,cmd)]
    return n.depth

def report( db, run_name, info_callback = info_callback_status ) :
    import pandokia.text_table as tt

    c = db.cursor()
    c.execute("select max(depth) as d, tablename from status where run = ? group by tablename order by d asc",(run_name,))
    table_list = [ x for x in c ]
        # table_list contains ( depth, tablename )

    print """
                -- N = not started
                -- S = started, not finished
                -- P = prereq not satisfied, so not attempted
                -- 0-255 = exit code
"""

    for depth, tablename in table_list :
        print "------"
        print tablename
        t = tt.text_table()

        row = 0
        t.define_column('-')    # the command name in column 0

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

        print t.get_trac_wiki()

#####

if __name__ == '__main__' :
    main()
