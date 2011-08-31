import distutils.core

f=open('steuermann/__init__.py','r')
for x in f :
    if x.startswith('__version__') :
        version = x.split("'")[1]
        break
f.close()

print version 

command_list = [ 'smc', 'steuermann_report.cgi' ]
use_usr_bin_env = [ ]
dir_set = 'addpath = "%s"\n'

args = {
    'version' :         "2.0dev",
    'description' :     "Steuermann Continuous Integration Control System",
    'author' :          "Mark Sienkiewicz",
    'scripts' :         ['scripts/smc', 'scripts/steuermann_report.cgi'],
    'package_dir' :     { 'steuermann' : 'steuermann', },
    'url' :             'https://svn.stsci.edu/trac/ssb/etal/wiki/Steuermann',
    'license':          'BSD',
    'packages':         [ 'steuermann' ],
    'package_data':     { 'steuermann' : [ '*.sql', '*.ini', ], }
}

d = distutils.core.setup(
    **args
)


def fix_script(name) :
    fname = script_dir + "/" + name

    f=open(fname,"r")
    l = f.readlines()
    if name in use_usr_bin_env :
        l[0] = '#!/usr/bin/env python\n'
    for count, line in enumerate(l) :
        if line.startswith("STEUERMANN_DIR_HERE") :
            l[count] = dir_set % lib_dir
    f.close()

    f=open(fname,"w")
    f.writelines(l)
    f.close()

if 'install' in d.command_obj :
    # they did an install
    script_dir = d.command_obj['install'].install_scripts
    lib_dir    = d.command_obj['install'].install_lib
    print 'scripts went to', script_dir
    print 'python  went to', lib_dir
    for x in command_list :
        fix_script(x)
    print 'set path = ( %s $path )' % script_dir
    print 'setenv PYTHONPATH  %s:$PYTHONPATH' % lib_dir
else :
    print "no install"

