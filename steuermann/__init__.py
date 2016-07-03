from .version import *

allowed_flags = {
    '--all' : '-a'      ,
    '-a'    : ''        ,   # run all nodes non-interactively
    '-r'    : '='       ,   # give run name
    '-n'    : ''        ,   # do not actually execute any processes
    '-h'    : '='       ,   # give hosts (*.ini) file
}

