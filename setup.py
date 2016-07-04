import exyapps
import os
import subprocess
import sqlite3
import sys
from setuptools import setup, find_packages, Extension


if os.path.exists('relic'):
    sys.path.insert(1, 'relic')
    import relic.release
else:
    try:
        import relic.release
    except ImportError:
        try:
            subprocess.check_call(['git', 'clone',
                'https://github.com/jhunkeler/relic.git'])
            sys.path.insert(1, 'relic')
            import relic.release
        except subprocess.CalledProcessError as e:
            print(e)
            exit(1)


version = relic.release.get_info()
relic.release.write_template(version, 'steuermann')

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

command_list = [ 'smc', 'smcron', 'steuermann_report.cgi' ]

with open('requirements.txt', 'r') as req:
    install_requires = [ pkg.rstrip() for pkg in req ]

# Create database from template
db_script = open(os.path.join('steuermann', 'db.sql'), 'r').read()
db_output = 'steuermann.db'

if os.path.exists(db_output):
    os.unlink(db_output)

db = sqlite3.connect(db_output)
db.executescript(db_script)

# Generate specfile
exy_specfile = os.path.join('steuermann', 'specfile.exy')
from exyapps import main as exyapps
import exyapps.grammar as g2
exyapps.flags = {}
exyapps.grammar = g2
exyapps.generate(exy_specfile, None, dump=0, **exyapps.flags)

setup(
    name = 'steuermann',
    version = version.pep386,
    description = 'Steuermann Continuous Integration Control System',
    long_description = long_desc,
    author = 'Mark Sienkiewicz',
    author_email = 'help@stsci.edu',
    url = 'https://svn.stsci.edu/trac/ssb/etal/wiki/Steuermann',
    install_requires = install_requires,
    scripts = ['scripts/' + x for x in command_list ],
    packages = find_packages(),
    package_data = {
        '': '*.ini'
    },
    classifiers = classifiers
)

