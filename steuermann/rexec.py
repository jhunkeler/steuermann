import sys
import urllib
import urllib2
import pandokia.helpers.easyargs as easyargs
import os.path

# http://ss64.com/nt/ - language of cmd.exe


# URLs are
# http://
#   hostname
#   :port
#   /password/
#   directive
#       args
#
# method=GET directive=run/
#       args = url encoded command line
#
# method=POST directive=upload
#       no args
#       post ...

def urlbase( host, password ) :
    if not ':' in host :
        host = host + ':7070'
    url = "http://%s/%s/"%(host,urllib.quote_plus(password))
    return url

def run( host, cmd, password, directory ):
    url = urlbase(host,password) + "run"

    data = urllib.urlencode( { 'password' : password,
        'dirname' : directory,
        'cmd' : cmd
        }
        )
    req = urllib2.Request(url, data)
    try :
        f = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print "HTTP ERROR",e.code
        print e.read()
        return 1
    while 1 :
        s = f.read(2048)
        if s == '' :
            break
        sys.stdout.write(s)
    return 0

def upload( host, filename, password, directory) :
    url = urlbase(host, password) + "upload"

    f = open(filename,"r")

    data = urllib.urlencode( { 'password' : password,
        'dirname' : directory,
        'filename' : os.path.basename(filename),
        'data' : f.read(),
        }
        )
    req = urllib2.Request(url, data)
    try :
        f = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print "HTTP ERROR",e.code
        print e.read()
        return 1
    print f.read()
    f.close()
    return 0

if __name__ == '__main__' :
    opt, args = easyargs.get( { 
        '-p' : '=',     # password
        '-f' : '=',     # password from file
        '-u' : '',      # upload
        '-d' : '=',     # upload destination directory (default .)
        '-h' : '=',     # host name
        } )
    if '-p' in opt :
        password = opt['-p']
    elif '-f' in opt :
        password = open(opt['-f'],'r').readline().strip()

    if not ( '-h' in opt ) :
        print "must give host name with -h"
        sys.exit(2)
    host = opt['-h']
    if '-d' in opt :
        directory = opt['-d']
    else :
        directory = "."

    if opt['-u'] :
        ex = 0
        for x in args :
            print "UPLOAD", x
            ex |= upload(host = host , filename=x, directory=directory, password=password)
        sys.exit(ex)
    else :
        x = run( host=host,
            cmd = ' '.join(args),
            password = password,
            directory = directory
            )
        sys.exit(x)


