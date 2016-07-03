import pygraphviz as gv
import sys, os
import nodes


'''
This script produces a DOT file of the nodes in one or more *.sm files

Requires graphviz and pygraphviz
'''


if len(sys.argv) < 2:
    print('ERROR - missing argument(s)')
    sys.exit(1)

sm_files = sys.argv[1:]

# get a command-tree of the *.sm files
tree = nodes.read_file_list(sm_files)

# do some things to get a list of only direct predecessors
N = []
for node in tree.node_index.values():
    node.parents = [p.name for p in node.predecessors]
    N.append(node)

hosts = []
for node in N:
    if node.host not in hosts:
        hosts.append(node.host)

extras = {}
for node in N:
    if node.name not in extras.keys():
        extras[node.name] = []
    for s in node.predecessors:
        for p in s.parents:
            if p in node.parents:
                extras[node.name].append(p)

for k, v in extras.items():
    extras[k] = list(set(v))

for i, node in enumerate(N):
    node.direct_parents = []
    for s in node.predecessors:
        if s.name not in extras[node.name]:
            node.direct_parents.append(s)
    N[i] = node


# these are just some random colors (enough for 13 hosts)
colors = [
    'red',
    'black',
    'purple',
    'lawngreen',
    'tomato',
    'teal',
    'brown',
    'orange',
    'blue',
    'midnightblue',
    'lightseagreen',
    'goldenrod',
    'black'
]

# assign host colors
host_colors = {}
for host in hosts:
    host_colors[host] = colors.pop(0)


# make the graph
graph = gv.AGraph(directed=True)

for node in N:
    graph.add_node(node.name, color = host_colors[node.host])

for node in N:
    for s in node.direct_parents:
        graph.add_edge(s.name, node.name)


# output to $HOME/sm_steps.dot
home = os.environ['HOME']
graph.write(os.path.join(home, 'sm_steps.dot'))

