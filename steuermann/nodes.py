'''
Stuff related to the tree structure of the command set
'''

import fnmatch
#import exyapps.runtime


#####
#####

class command_tree(object):

    # list of additional files to import after this one; this is just
    # here so we have a place to put it.  It is appended by the parser
    # and consumed by read_file_list()
    import_list = [ ]

    # a dict that maps currently known node names to node objects
    node_index = None

    # This is a list if (before, after) showing names of node orders;
    # the individual nodes do not store this information while the
    # parsing is happening.
    node_order = None

    # call init() once before parsing, then call parse for each file, then call finish()
    def __init__( self ) :
        self.node_index = { }
        self.node_order = [ ]

    def finish( self ) :
        # This links up the nodes according to the (before, after) information
        # in node_order.  before and after are fully qualified node names.
        # We do this at the end so that 
        #  - we can have forward references
        #  - we can use wild cards in our AFTER clauses

        # before is the predecessor, after comes "AFTER before"
        for before, after, required, pos in self.node_order :
            if ( '*' in before ) or ( '?' in before ) or ( '[' in before ) or ( '@' in before ):
                # print "CONNECTING %-50s %-50s"%(before, after)
                for x in self.node_index :
                    if wildcard_name( wild=before, name=x ) :
                        # print "           found",x
                        # yes, the wild card matches this one; connect them
                        # (but don't let a node come before itself because the wild card is too loose)
                        if x != after :
                            self.connect(x, after, required, pos)
            else :
                # print "CONNECTING %-50s %-50s"%(before, after)
                # print "           found",after
                self.connect(before, after, required, pos)

        # Work out the depths of each node.
        # Since we are walking the graph, we also detect dependency loops here.
        compute_depths( self.node_index )
        

    # make the actual connection between nodes
    def connect( self, before, after, required, line ) :

        if not before in self.node_index :
            if required :
                print "error: %s happens after non-existant %s - line %s"%(after,before,line)
            return

        if not after in self.node_index :
            print "error: after node %s does not exist %s"%(after,line)
            return

        # tell the after node that the other one comes first

        self.node_index[after].predecessors.append(self.node_index[before])

        # tell the after node about the before node and note that
        # the before node is not done yet.
        self.node_index[after].released[before] = False


    # create a set of nodes for a particular command - called from within the parser
    def add_command_list( self, table, hostlist, command_list ) :
        for host in set(hostlist) :
            this_table = '%s:%s' % ( host, table )
            for command, script, script_type, after_clause, pos, resources in command_list :
                # this happens once for each CMD clause
                # command is the name of this command
                # script is the script to run
                # after is a list of AFTER clauses
                # pos is where in this file this command was defined

                command = normalize_name( host, table, command )

                if command in self.node_index :
                    # bug: should be error
                    print "# warning: %s already used on line %s"%(command,self.node_index[command].input_line)

                # create the node
                self.node_index[command]=node(command, script, script_type, nice_pos( current_file_name, pos), resources )

                for before_name, required, pos in after_clause :
                    # this happens once for each AFTER clause
                    # before is the name of a predecessor that this one comes after
                    # required is a boolean, whether the predecessor must exist
                    # pos is where in the file the AFTER clause begins

                    before_name = normalize_name( host, table, before_name )

                    # list of ( before, after, required, pos )
                    self.node_order.append( (before_name, command, required, pos) )



#####

# crack open host:table/cmd
def crack_name(name) :
    if ':' in name :
        t = name.split(':')
        host = t[0]
        name = t[1]
    else :
        host = '*'

    if '/' in name :
        t = name.split('/')
        table = t[0]
        cmd = t[1]
    else :
        table = '*'
        cmd = name

    return (host, table, cmd)

#####

def join_name( host, table, cmd ) :
    return '%s:%s/%s'%(host,table,cmd)

#####

def normalize_name( host, table, name ) :

    if not '/' in name :
        name = table + '/' + name

    if name.startswith('.:') :
        name = name[2:]

    if not ':' in name :
        name = host + ':' + name
    # print "## return %s"%name
    return name

#####
#
# this checks whether a particular wildcard pattern matches a particular name
#

_wildcard_cache = ( None, None )

def wildcard_name( wild, name ) :
    global _wildcard_cache

    w_host, w_table, w_cmd = crack_name(wild)

    n_host, n_table, n_cmd = crack_name(name)

    if w_host.startswith('@') :
        # hostgroups are a special case of wild cards.  it matches if the host part of 
        if n_host in get_hostgroup(w_host) :
            return ( fnmatch.fnmatchcase(n_table,w_table) and
                     fnmatch.fnmatchcase(n_cmd,  w_cmd  ) )
        else :
            return False
    else :
        return ( fnmatch.fnmatchcase(n_host, w_host ) and
                 fnmatch.fnmatchcase(n_table,w_table) and
                 fnmatch.fnmatchcase(n_cmd,  w_cmd  ) )


#####


#####

    
# a node object for each command instance that will be run.  The name is
# "host:table/command".  The shell command to execute on the target host
# is "script".
#
# predecessors[] is a list of everything that this node must definitely come after.
#
# released is a dict indexed by each of the "before" nodes; the value is
# true if the before node is finished running.
#
class node(object) :
    def __init__(self, name, script, script_type, input_line, resources) :
        # the fully qualified name of the node
        self.name = name

        # the command script that this node runs
        self.script = script % nodes.saved_conditions
        self.script_type = script_type

        # what "resources" it requires
        self.resources = resources

        # what line of the input file specified this node; this is
        # a string of the form "foo.bar 123"
        self.input_line = input_line

        # crack open host:table/cmd
        self.host, self.table, self.cmd = crack_name(name)

        # this command runs after every node in this list
        self.predecessors = [ ]

        # this is a dict of everything that comes before us
        # The key is the name of the other node.
        # The value is true/false for whether the other node
        # is finished running.
        self.released = { }

        # These flags are 1 or 0 so we can sum() them
        self.finished = 0
        self.running = 0

        #
        self.wanted = 1
        self.skip = 1

#####

# debug - make a string representation of all the nodes

def show_nodes( node_index ) :
    import cStringIO as StringIO
    s = StringIO.StringIO()
    for x in sorted( [ x for x in node_index ] ) :    
        x = node_index[x]

        # show the node name and the command it runs
        s.write( "NODE  %s  %s  %s\n"%(x.name, x.script, x.input_line) )

        # show each node that this one comes After, and show the flag
        # whether the previous node has run yet.
        for y in x.predecessors :
            s.write( "        AFTER %s\n"%y.name )

    return s.getvalue()

#####

def nice_pos( filename, yapps_pos ) :
    # filename is the file name to use
    # yapps_pos is a tuple of (file, line, col) except that file
    # is a file-like object with no traceability to an actual file1
    return "%s:%s col %s"%(filename, yapps_pos[1], yapps_pos[2])

#####


#####
#
# calculating depths of a node tree

def c_d_fn(x,depth) :

    if x.in_recursion :
        print "error: loop detected at",x.name
        return

    # print '>',"  "*depth, depth, x.name

    # if it is already deeper than where we are now, we can (must)
    # prune the tree walk here.
    if x.depth  >= depth :
        return

    if depth > 100 :
        # bug: proxy for somebody wrote a loop
        print "error: depth > 100, node = ",x.name
        return

    x.in_recursion = 1

    # assign the depth
    x.depth = depth

    # make all the successors one deeper
    depth = depth + 1
    for y in x.successors :
        c_d_fn(y,depth)

    # print '<',"  "*depth, depth, x.name
    x.in_recursion = 0

def compute_depths(nodes) :

    # init everything
    for x in nodes :
        x = nodes[x]
        x.depth = 0
        x.successors = [ ]
        x.in_recursion = 0

    # walk the nodes in an arbitrary order; make a list of successors
    for x in nodes :
        x = nodes[x]
        for y in x.predecessors :
            if not x in y.successors :
                y.successors.append(x)

    # recursively walk down the tree assigning depth values, starting
    # with depth=1 for the highest level
    for x in nodes :
        c_d_fn(nodes[x],1)

    #
    for x in nodes :
        x = nodes[x]
        del x.in_recursion


#####

import specfile

current_file_name = None

def read_file_list( file_list ) :

    global current_file_name
    di = command_tree( ) 
    imported = { }
    while len(file_list) > 0 : 

        # print "START",file_list
        # first name off the list
        current_file_name = file_list[0]
        file_list = file_list[1:]
        # print "LIST",file_list

        # see if it imported already
        if current_file_name in imported :
            # print "SKIP",current_file_name
            continue
        imported[current_file_name] = 1

        print "READING ",current_file_name
        # read/parse
        sc = specfile.specfileScanner( open(current_file_name,'r').read() )
        p = specfile.specfile( scanner=sc, data=di )
        
        result = specfile.wrap_error_reporter( p, 'start' )

        # if there were any import statements in the file, add those files to the list
        file_list += di.import_list
        di.import_list = [ ]

    di.finish()
    return di

#####

saved_conditions = { 'True' : True, 'False' : False }

def declare_conditions( text, filename ) :
    # the parameter "text" is the token that begins "CONDITION\n"
    # and ends "\nEND\n", with a block of python code in the middle.
    # 
    # the parameter "filename" is what file we were processing when
    # we saw this set of conditions defined.

    # process the junk off the ends of the text
    text = text.split('\n',1)[1]    # tear off "CONDITION\n"
    text = text.rsplit('\n',2)[0]   # tear off "END\n"

    # if it is indented at all, compensate for the indent so the
    # exec will work
    if text.startswith(' ') or text.startswith('\t') :
        text = 'if 1 :\n' + text

    # exec it into cond first, and then move any entries that are unique
    #   into saved_conditions; this allows us to specify conditions on the
    #   command line and not have them overwritten by the same variable in
    #   a CONDITIONS block
    cond = {}
    exec text in cond
    for k, v in cond.items():
        if k not in saved_conditions:
            saved_conditions[k] = v

    


def check_condition( name, filename ) :

    if name in saved_conditions :
        c = saved_conditions[name]
        if callable(c) :
            ans = c()
        else :
            ans = c
    else :
        ans = False

    return ans
    
#####

hostgroups = { }

def define_hostgroup( name ) :
    if not name in hostgroups :
        hostgroups[name] = set( )

def add_hostgroup( name, host ) :
    if host.startswith('@') :
        new = get_hostgroup(host) 
    else :
        new = [ host ]

    hostgroups[name] |= set( new )

def get_hostgroup( name ) :
    return list( hostgroups[name] )

#####

if __name__=='__main__':
    import sys
    n = read_file_list( sys.argv[1:] )
    print show_nodes(n.node_index)

