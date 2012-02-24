#
# steuermann remote execution daemon - use this when you can't use
# something better (like ssh) to get your commands running in the
# other machine.
#
# Copyright 2012 Association of Universities for Research in Astronomy (AURA) 
#

import os
import time
import CGIHTTPServer
import BaseHTTPServer
import SocketServer
import platform
import subprocess
import urllib
import urlparse

os.chdir('/')
print os.getcwd()

#####
#

valid_client_ip = ( 
    '130.167.180.22',       # arzach
    '130.167.180.4',        # ssb
    '130.167.237.185',      # banana
    '130.167.237.55',       # vxp-dukat
    )

#####
#
# This uses the python stock http server.  Here is a request handler
# that services GET requests by executing the command passed in.
# All other requests are invalid.

password = "pass"
 
class my_handler( CGIHTTPServer.CGIHTTPRequestHandler ) :

    def __init__(self, request, client_address, server) :
        # init the superclass
        CGIHTTPServer.CGIHTTPRequestHandler.__init__(self, request, client_address, server)

    def reject_client(self) :
        print self.client_address
        if not ( self.client_address[0] in valid_client_ip ) :
            self.bad_client('a')
            return 1

        if self.path.startswith('/' + password + '/' ) :
            self.path = self.path[len(password)+2:]
        else :
            self.bad_client('p')
            return 1

        return 0

    def do_GET(self) :
        # GET /password/command...
        #   run the command

        if self.reject_client() :
            return

        path = self.path

        print "GET",path
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Hello world: %s\n"%path)
        self.wfile.flush()

    def bad_client(self, why) :
        self.send_response(500)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("bad client: %s\n"%why)
        self.wfile.flush()
        return

    def do_INVALID(self) :
        self.send_response(500)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("error\n")
        self.wfile.flush()
        return

    def do_POST(self) :
        # POST password=pass&name=filename&data=filedata
        #   upload data to a file

        if self.reject_client() :
            return

        print self.path


        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        d = urlparse.parse_qs(data)

        for x in sorted([ x for x in d]) :
            print x,d[x]

        if d['password'][0] != password :
            self.bad_client('p')
            return

        dirname = d['dirname'][0]
        print "CD",dirname
        os.chdir(dirname)

        if self.path == 'upload' :

            filename = d['filename'][0]

            mode = 'wb'
            if 'mode' in d :
                t = d['mode'][0]
                if t == 't' or t == 'text' :
                    mode = 'w'
                elif t == 'b' or t == 'binary' :
                    mode = 'wb'
                else :
                    return self.bad_client('mode')

            f = open(filename,'wb')
            f.write(d['data'][0])
            f.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("uploaded %s\n"%filename)
            self.wfile.flush()

        elif self.path == 'run' :
            cmd = d['cmd'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("Hello world: %s\n"%cmd)
            run_child(cmd, self.wfile)
            self.wfile.write("done\n")
            self.wfile.flush()
        else :
            return self.bad_client('c')


    def do_HEAD(self) :
        self.do_invalid()


class MultiThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

####

windows = platform.system() == 'Windows'

def run_child(path, wfile) :
    env = os.environ
    cmd = urllib.unquote_plus(path)
    print "COMMAND",cmd

    # bug: implement timeouts
    if windows :
        status = subprocess_windows( cmd, wfile, env )
    else :
        status = subprocess_unix( cmd, wfile, env )

    # subprocess gives you weird status values
    if status > 0 :
        t_status="exit %d"%(status >> 8)
        if status != 0 :
            return_status = 1
    else :
        return_status = 1
        t_status="signal %d" % ( - status )
        # subprocess does not tell you if there was a core
        # dump, but there is nothing we can do about it.

    print "COMMAND EXIT:",status,t_status


def subprocess_windows(cmd, wfile, env ) :
    # You might think that subprocess.Popen() would be portable,
    # but you would be wrong.
    #
    # On Windows, sockets are NOT file descriptors.  Since we are in a web server, wfile here is a socket.

    # print wfile.fileno()
    # import msvcrt
    # print msvcrt.get_osfhandle(wfile.fileno())
    p = subprocess.Popen( cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, env = env, creationflags = subprocess.CREATE_NEW_PROCESS_GROUP )
    while 1 :
        n = p.stdout.read(256)
        if n == '' :
            break
        wfile.write(n)
    return p.wait()

def subprocess_unix( cmd, wfile, env ) :
    p = subprocess.Popen( cmd, stdout=wfile, stderr=wfile, shell=True, env = env, preexec_fn=os.setpgrp )
    return p.wait()

#####


def run( args = [ ] ) :
    # you could parse args here if you wanted to.  I don't care to spend
    # the time.  This is just here for people who can't (or don't want to)
    # install a full featured web server just to try things out.
    if len(args) > 0 :
        ip = args[0]
    else :
        ip = platform.node()

    port = 7070

    print "http://%s:%s/"%(str(ip),str(port))

    httpd = MultiThreadedHTTPServer( (ip, port) , my_handler)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    while 1 :
        httpd.handle_request()

if __name__ == '__main__' :
    run()


##
# in case we need to kill child processes:
# http://code.activestate.com/recipes/347462-terminating-a-subprocess-on-windows/


