'''
run processes asynchronously on various machines, with a callback
on process exit.
'''

# to do someday:
#
# This feature should really be broken into 3 parts:
#  - remotely execute on another machine
#  - track concurrent execution
#  - reserve resource usage
#
# To start a process, ask for a resource reservation.  (Currently, the
# only resource we track is CPUs.)  If we don't get a reservation, we
# don't run right away.
#
# If we do, use the remote exec to run the process on the target machine.
# This is the part that knows hosts.ini.  (We also use hosts.ini to declare
# resource availability.)
#
# When the process finishes, release the resource reservation.
#

import subprocess
import time
import datetime
import os
import os.path
import traceback
import sys
import errno
import ConfigParser
import re

def config_yes_no(d,which) :
    if not which in d :
        return False
    s = d[which]
    return s.strip()[0].lower() in ( 'y', 't', '1' )

debug=1

##### 

class struct :
    pass


#####

class run_exception(Exception) :
    pass

class runner(object): 

    # dict of all current running processes, indexed by node name
    all_procs = None

    # index of nodes
    node_index = None

    # 
    host_info_cache = None

    # dict of how many commands we have running for that machine
    howmany = None

    #####
    #

    def __init__( self, nodes, hosts_ini ) :
        self.all_procs = { }
        self.node_index = nodes
        self.load_host_info(filename = hosts_ini)
        self.host_info_cache = { }
        self.resources = {}
        self.resources_avail = {}


    #####
    # start a process

    def run( self, node, run_name, logfile_name, no_run = False ):
        '''
            run a process
        
            return is:
                D - host disabled
                M - not run; resource limit
                R - running
        '''

        try :

            try :
                args = self.get_host_info(node.host)
            except Exception, e :
                log_traceback()
                print "ERROR: do not know how to run on %s"%node.host
                print e
                raise

            if ( config_yes_no(args,'disable') ) :
                return 'D'

            # track resources
            if node.host not in self.resources.keys():
                self.resources[node.host] = {}
                self.resources_avail[node.host] = {}

            for key, val in args.items():
                if key.startswith('res_'):
                    key = key.lstrip('res_')
                    self.resources[node.host][key] = int(val)
                    if key not in self.resources_avail[node.host].keys():
                        self.resources_avail[node.host][key] = int(val)

            # check if enough resources on host and return if not
            enough = True
            for res, amount in node.resources.items():
                if res in self.resources[node.host].keys():
                    avail = self.resources_avail[node.host][res]
                    if amount > avail:
                        enough = False
                        break
            if not enough:
                return 'M'

            # allocate host resources
            for res, amount in node.resources.items():
                if res in self.resources[node.host].keys():
                    self.resources_avail[node.host][res] -= amount


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
                cmd=node.cmd,
                node=node.name,
                w_node=node.name.replace("/","_").replace(":","_"),
                runname=run_name,
                )

            print
            print 'script = %s' %args['script'] 
            print


            # also stick everything from env into args (if not already defined)
            for k, v in os.environ.items():
                if k not in args.keys():
                    args[k] = v

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

            try :
                os.makedirs( os.path.dirname(logfile_name) )
            except OSError, e :
                if e.errno == errno.EEXIST :
                    pass
                else :
                    raise

            # open the log file, write initial notes
            logfile=open(logfile_name,"w")
            logfile.write('%s %s\n'%(datetime.datetime.now(),run))
            logfile.flush()

            # debug - just say the name of the node we would run

            if ( no_run ) :
                run = [ 'echo', 'disable run - node=', node.name ]
            
            # start running the process
            if debug :
                print "RUN",run
            p = subprocess.Popen(
                args=run,
                stdout=logfile,
                stderr=subprocess.STDOUT,
                shell=False, close_fds=True
            )

            # remember the popen object for the process; remember the open log file
            n = struct()
            n.proc = p
            n.logfile = logfile
            n.logfile_name = logfile_name

            # remember the process is running
            self.all_procs[node.name] = n

            return 'R'

        except Exception, e :
            log_traceback()
            txt= "ERROR RUNNING %s"%node.name
            raise run_exception(txt)

    #####
    # callback when a node finishes

    def finish( self, node_name, status):

        node = self.node_index[node_name]

        args = self.get_host_info(node.host)


        # de-allocate host resources
        for res, amount in node.resources.items():
            if res in self.resources[node.host].keys():
                self.resources_avail[node.host][res] += amount

        if debug :
            hostname = args['hostname']
            print "finish %s %s %d"%(hostname,node_name,n)

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
        try :
            for name, value in cfg.items(section) :
                if value.startswith('[') :
                    # it is a list
                    d[name] = eval(value)
                elif name.endswith('$') :
                    # this is ugly, but we'll do it for now
                    x = value.split('$')
                    x = x[0] + os.environ[x[1]]
                    d[name[:-1]] = x
                else :
                    # everything else is plain text
                    d[name] = value
            return d
        except ConfigParser.NoSectionError :
            print "No config section in hosts.ini: %s"%section
            return { }


    def load_host_info( self, filename ) : 

        if os.path.exists(filename):
            pass
            # print 'READING HOST INFO FROM %s' %filename
        else:
            print 'ERROR - %s does not exist' %filename
            sys.exit(1)

        # read the config file
        self.cfg = ConfigParser.RawConfigParser()
        self.cfg.read(filename)


    def get_host_info(self, host) :
        if not host in self.host_info_cache :
            d = self._host_get_names(self.cfg, host)

            if 'like' in d :
                # get the dict of what this entry is like, copy it,
                # and update it with the values for this entry
                d1 = self.get_host_info(d['like'])
                d1 = d1.copy()
                d1.update(d)
                d = d1
                del d['like']

            # default hostname is the name from the section header
            if not 'hostname' in d :
                d['hostname'] = host

            self.host_info_cache[host] = d

        return self.host_info_cache[host]
    #####

# The traceback interface is awkward in python; here is something I copied from pyetc:

def log_traceback() :
    # You would think that the python traceback module contains
    # something useful to do this, but it always returns multi-line
    # strings.  I want each line of output logged separately so the log
    # file remains easy to process, so I reverse engineered this out of
    # the logging module.
    print "LOG TRACEBACK:"
    try:
        etype, value, tb = sys.exc_info()
        tbex = traceback.extract_tb( tb )
        print tbex
        for filename, lineno, name, line in tbex :
            print '%s:%d, in %s'%(filename,lineno,name)
            if line:
                print '    %s'%line.strip()

        for x in  traceback.format_exception_only( etype, value ) :
            print ": %s",x

        print "---"

    finally:
        # If you don't clear these guys, you can make loops that
        # the garbage collector has to work hard to eliminate.
        etype = value = tb = None

