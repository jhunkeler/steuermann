'''
run processes asynchronously on various machines, with a callback
on process exit.
'''

import subprocess
import time
import datetime
import os

import ConfigParser

debug=0

##### 

class struct :
    pass


#####

class runner(object): 

    # dict of all current running processes, indexed by node name
    all_procs = None

    # index of nodes
    node_index = None

    # dir where we write our logs
    logdir = ''

    # 
    host_info_cache = None

    # dict of how many commands we have running for that machine
    howmany = None

    #####
    #

    def __init__( self, nodes, logdir ) :
        self.all_procs = { }
        self.node_index = nodes
        self.load_host_info()
        self.logdir = logdir
        self.host_info_cache = { }
        self.howmany = { }

    #####
    # start a process

    def run( self, node, run_name ):

        try :
            args = self.get_host_info(node.host)
        except :
            print "ERROR: do not know how to run on %s"%node.host
            raise

        if 'maxproc' in args :
            hostname = args['hostname']

            n = int(self.howmany.get(hostname,0))
            if n >= int(args['maxproc']) :
                print "decline to run %s - %d other already running"%(node.name,n)
                return False

            n = n + 1
            self.howmany[hostname] = n
            print "running %s %s %d"%(hostname,node.name, n)
        else :
            print "running %s %s no maxproc"%(hostname, node.name)

        if debug :
            print "run",node.name
        if debug :
            print "....%s:%s/%s\n"%(node.host, node.table, node.cmd)

        node.running = 1

        args = args.copy()
        args.update( 
            script=node.script,
            script_type=node.script_type,
            host=node.host,
            table=node.table,
            cmd=node.cmd
            )

        if debug :
            print "ARGS"
            for x in sorted([x for x in args]) :
                print '%s=%s'%(x,args[x])

        args['script'] = args['script'] % args

        if args['script_type'] == 'r' :
            run = args['run']
        elif  args['script_type'] == 'l' :
            run = args['local']
        else :
            raise Exception()

        t = [ ]
        for x in run :
            # bug: what to do in case of keyerror
            t.append( x % args )

        run = t

        if debug :
            print "RUN",run

        # make sure the log directory is there
        logdir= self.logdir + "/%s"%run_name
        try :
            os.makedirs(logdir)
        except OSError:
            pass

        # create a name for the log file, but do not use / in the name
        logfile_name = "%s/%s.log"%( logdir, node.name.replace('/','.') )

        # open the log file, write initial notes
        logfile=open(logfile_name,"w")
        logfile.write('%s %s\n'%(datetime.datetime.now(),run))
        logfile.flush()
        
        # start running the process
        p = subprocess.Popen(args=run,
            stdout=logfile,
            stderr=subprocess.STDOUT,
            shell=False, close_fds=True)

        # remember the popen object for the process; remember the open log file
        n = struct()
        n.proc = p
        n.logfile = logfile
        n.logfile_name = logfile_name

        # remember the process is running
        self.all_procs[node.name] = n

        return True

    #####
    # callback when a node finishes

    def finish( self, node_name, status):

        node = self.node_index[node_name]

        args = self.get_host_info(node.host)

        if 'maxproc' in args :
            hostname = args['hostname']

            n = int(self.howmany.get(hostname,0))
            n = n - 1

            self.howmany[hostname] = n
            print "finish %s %s %d"%(hostname,node_name,n)
        else :
            print "finish %s %s no maxproc"%(hostname,node_name)

        # note the termination of the process at the end of the log file
        logfile  = self.all_procs[node_name].logfile
        logfile.seek(0,2)   # end of file
        logfile.write('\n%s exit=%s\n'%(datetime.datetime.now(),status))
        logfile.close()

        # note the completion of the command
        if debug :
            print "finish",node.name
        node.running = 0
        node.finished = 1
        node.exit_status = status

    #####

    # poll for exited child processes - this whole thing could could
    # be event driven, but I don't care to work out the details right
    # now.

    def poll( self ) :

        # look at all active processes
        for name in self.all_procs :

            # see if name has finished
            p = self.all_procs[name].proc
            n =  p.poll()
            if n is not None :

                # marke the node finished
                self.finish(name,n)

                #
                status = p.returncode

                # remove it from the list of pending processes
                del self.all_procs[name]

                # Return the identity of the exited process.
                # There may be more, but we will come back and poll again.
                return ( name, status )

        return None

    #####

    def display_procs( self ) :
        # display currently active child processes
        print "procs:"
        for x in sorted(self.all_procs) :
            print "    ",x
        print ""

    #####


    def _host_get_names( self, cfg, section ) :
        d = { }
        # pick all the variables out of this section
        for name, value in cfg.items(section) :
            if value.startswith('[') :
                # it is a list
                d[name] = eval(value)
            else :
                # everything else is plain text
                d[name] = value
        return d

    def load_host_info( self, filename=None ) : 

        # read the config file
        if filename is None :
            filename = os.path.dirname(__file__) + '/hosts.ini'
        self.cfg = ConfigParser.RawConfigParser()
        self.cfg.read(filename)

    def get_host_info(self, host) :
        if debug:
            print "enter get_host_info",host
        if not host in self.host_info_cache :

            d = self._host_get_names(self.cfg, host)
            if debug:
                print "in get_host_info, got names for ",host, d
            if 'like' in d :
                if debug:
                    print "has like", d['like']
                d1 = self.get_host_info(d['like']).copy()
                del d['like']
                d1.update(d)
                self.host_info_cache[host] = d1
            else :
                print "end of chain",host,d
                self.host_info_cache[host] = d

        if debug:
            print "leave get_host_info",host, self.host_info_cache[host]

        return self.host_info_cache[host]
    #####
