
from steuermann import nodes

yes_list = (
    ( 'a:b/c', 'a:b/c' ),
    ( 'a:b/*', 'a:b/c' ),
    ( 'a:*/c', 'a:b/c' ),
    ( 'a:*/*', 'a:b/c' ),
    ( '*:b/c', 'a:b/c' ),
    ( '*:b/*', 'a:b/c' ),
    ( '*:*/c', 'a:b/c' ),
    ( '*:*/*', 'a:b/c' ),

    ( '[a-z]:*/*', 'a:b/c' ),

    ( 'a?:*/*', 'ax:b/c' ),
    ( 'a?:*/*', 'ay:b/c' ),

    ( '*:*/*', 'xasdadsf:agasdgg/asdgasdg' ),
    )

no_list = (
    ( '[A-Z]:*/*', 'a:b/c' ),
    ( 'a?:*/*', 'a:b/c' ),
    ( 'a:b/*', 'a:x/y' ),
    ( '*:c/*', 'a:b/y' ),
    ( '*:b/y', 'a:b/c' ),
    ( 'a:b/y', 'a:b/c' ),
    )

def test_wildcard_name() :
    def yes( a, b ) :
        assert nodes.wildcard_name( a, b )

    def no( a, b ) :
        assert not nodes.wildcard_name( a, b )

    for x in yes_list :
        yield yes, x[0], x[1]

    for x in no_list :
        yield no, x[0], x[1]

