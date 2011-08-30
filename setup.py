import distutils.core

f=open('steuermann/__init__.py','r')
for x in f :
    if x.startswith('__version__') :
        version = x.split("'")[1]
        break
f.close()

print version 

args = {
    'version' :         "2.0dev",
    'description' :     "Steuermann Continuous Integration Control System",
    'author' :          "Mark Sienkiewicz",
    'scripts' :         ['scripts/smc'],
    'package_dir' :     { 'steuermann' : 'steuermann', },
    'url' :             'https://svn.stsci.edu/trac/ssb/etal/wiki/Steuermann',
    'license':          'BSD',
    'packages':         [ 'steuermann' ],
    'package_data':     { 'steuermann' : [ '*.sql', '*.ini', ], }
}

d = distutils.core.setup(
    **args
)

