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
    all_procs = { }

    # index of nodes
    node_index = { }

    # info about hosts we can run on
    host_info = { }

    # dir where we write our logs
    logdir = ''

    #####
    #

    def __init__( self, nodes, logdir ) :
        self.node_index = nodes
        self.load_host_info()
        self.logdir = logdir

    #####
    # start a process

    def run( self, node, run_name ):
        if debug :
            print "run",node.name
        node.running = 1
        if debug :
            print "....%s:%s/%s\n"%(node.host, node.table, node.cmd)

        try :
            args = self.host_info[node.host]
        except :
            print "ERROR: do not know how to run on %s"%node.host
            raise

        run = args['run']

        args = args.copy()
        args.update( 
            script=node.script,
            host=node.host,
            table=node.table,
            cmd=node.cmd
            )

        if debug :
            print "ARGS"
            for x in sorted([x for x in args]) :
                print '%s=%s'%(x,args[x])

        run = [ x % args for x in run ]

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

    #####
    # callback when a node finishes

    def finish( self, node_name, status):
        # note the termination of the process at the end of the log file
        logfile  = self.all_procs[node_name].logfile
        logfile.seek(0,2)   # end of file
        logfile.write('\n%s exit=%s\n'%(datetime.datetime.now(),status))
        logfile.close()

        # note the completion of the command
        node = self.node_index[node_name]
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


    def _host_get_names( self, cfg, section, d ) :
        # pick all the variables out of this section
        for name, value in cfg.items(section) :
            if name == 'run' :
                # run is a list
                d[name] = eval(value)
            else :
                # everything else is plain text
                d[name] = value

    def load_host_info( self, filename=None ) : 
        self.host_info = { }

        # read the config file
        if filename is None :
            filename = os.path.dirname(__file__) + '/hosts.ini'
        cfg = ConfigParser.RawConfigParser()
        cfg.read(filename)

	    # this dict holds the set of values that are defined as
	    # applying to all hosts
        all_dict = { }
        self._host_get_names(cfg, 'ALL', all_dict)

        # for all the sections (except ALL) get the names from that section
        for x in cfg.sections() :
            if x == 'ALL' :
                continue

            # start with a dict that contains what is in ALL
            d = all_dict.copy()

            # get what there is to know about host x
            self._host_get_names(cfg, x, d)

            # if it is like some other host, start over using ALL, then
            # the LIKE host, then our own information
            if 'like' in d :
                like = d['like']
                d = all_dict.copy()
                self._host_get_names(cfg, like, d)
                self._host_get_names(cfg, x, d)
                del d['like']

            print x,d
            self.host_info[x] = d

        del cfg

    #####
