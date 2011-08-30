'''
prototype of report

'''
import subprocess
import time
import sys

try :
    import CStringIO as StringIO
except ImportError :
    import StringIO as StringIO

#####

def c_d_fn(x,depth) :
    if x.depth  >= depth :
        return
    x.depth = depth
    depth = depth + 1
    for y in x.children :
        c_d_fn(y,depth)
    

def compute_depths(nodes) :
    for x in nodes :
        x = nodes[x]
        x.depth = 0
        x.in_recurse = 0
        x.parents = [ ]
        x.children = [ ]
    for x in nodes :
        x = nodes[x]
        for y in x.precursors :
            if not x in y.children :
                y.children.append(x)
    for x in nodes :
        c_d_fn(nodes[x],1)
        
#####

def compute_table(nodes) :
    # find the depths
    compute_depths(nodes)

    # sort the nodes by depth
    l = [ x.split(':') for x in nodes ]
    l = [ [ x[0] ] + x[1].split('/') for x in l ]
    l = [ [ x[1], x[2], x[0] ] for x in l ]
    l = sorted(l)

    # table_content is a list of nodes in each table
    table_content = { }

    # table_hosts is a list of hosts in each table
    table_hosts = { }

    # table_depth is how deep the deepest row of each table is
    table_depth = { }

    for x in nodes  :
        host, table = x.split(':')
        table, cmd = table.split('/')

        table_content[table] = table_content.get(table,[]) + [ x ]

        table_hosts  [table] = table_hosts  .get(table,[]) + [ host ]

        if table_depth.get(table,0) < nodes[x].depth :
            table_depth[table] = nodes[x].depth

    for x in table_hosts :
        table_hosts[x] = list(set(table_hosts[x]))

    return table_content, table_hosts, table_depth

#####

# html of one table

def html_table(nodes, table, host_list ) :
    s=StringIO.StringIO()

    # this is all the nodes in this table
    pat = ':%s/' % table
    l = [ x for x in nodes if pat in x ]

    # d[x] is the max depth of command x
    d = { }
    for x in l :
        depth = nodes[x].depth
        x = x.split('/')[1]
        if d.get(x,0) < depth :
            d[x] = depth

    # this is the order of the rows of the table
    cmd_order = sorted( [ (d[x], x) for x in d ] )

    # this is the table
    s.write( "<table border=1>" )

    # heading
    s.write( "<tr> <td>&nbsp;</td> " )
    for host in host_list :
        s.write( "<th>%s</th>" % host )
    s.write( "</tr>\n" )

    # loop over the commands in the order they appear
    for depth, cmd in cmd_order :
        s.write( "<tr>\n\t<td>%s/%s</td>\n"%(table,cmd) )
        for host in host_list :
            name = host + ':' + table + '/' + cmd
            if name in nodes :
                s.write( "\t<td class=%%(class!%s)s> %%(text!%s)s </td>\n"%(name,name) )
            else :
                s.write( "\t<td class=nothing> . </td>\n" )
        s.write( "</tr>\n" )
    s.write( "</table>" )
    return s.getvalue()

class struct(object): 
    pass

#####

def main() :
    import sqlite3
    db = sqlite3.connect('sr.db')

    c = db.cursor()
    c.execute('select run from runs')
    for (run,) in c :

        all = [ ]
        c1 = db.cursor()
        c1.execute('select host, tablename, cmd, depth, status, start_time, end_time, notes from status where run = ? ',(run,) )
        for x in c1 :
            n = struct()
            n.host, n.tablename, n.cmd, n.depth, n.status, n.start_time, n.ent_time, n.notes = x
            all.append(n)

        print "RUN",run
        for x in all :
            print x.host, x.tablename, x.cmd, x.status

main()
