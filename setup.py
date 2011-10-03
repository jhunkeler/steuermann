import distutils.core

long_desc = '''
Steuermann is a control system for continuous integration.  You write
one or more config files defining processes to run on various computers
along with dependencies.  

For example, you can declare that task A runs on computer X, but only
after task B runs (to completion) on computer Y.

You can invoke steuermann in automatic mode to run all the processes in
the necessary order.  This is the way to perform automatic builds/tests.

You can invoke steuermann manually to select a subset of processes
to execute.  This is a way to repeat steps without running everything
again, for example to repeat a failed portion of an automatic build/test
sequence.

'''

classifiers = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2',
    'Topic :: Software Development :: Build Tools',
    'Topic :: System :: Distributed Computing',
    ]

# 
f=open('steuermann/__init__.py','r')
for x in f :
    if x.startswith('__version__') :
        version = x.split("'")[1]
        break
f.close()

#
command_list = [ 'smc', 'smcron', 'steuermann_report.cgi' ]
use_usr_bin_env = [ ]
dir_set = 'addpath = "%s"\n'

args = {
    'name':             'steuermann',
    'version' :         version,
    'description' :     "Steuermann Continuous Integration Control System",
    'long_description': long_desc,
    'author' :          "Mark Sienkiewicz",
    'author_email' :    "help@stsci.edu",
    'url' :             'https://svn.stsci.edu/trac/ssb/etal/wiki/Steuermann',
    'scripts' :         ['scripts/' + x for x in command_list ],
    'package_dir' :     { 'steuermann' : 'steuermann', },
    'license':          'BSD',
    'packages':         [ 'steuermann' ],
    'package_data':     { 'steuermann' : [ '*.sql', '*.ini', ], },
    'classifiers':      classifiers,
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

