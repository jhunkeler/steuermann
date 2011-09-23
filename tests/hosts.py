import steuermann.run as run

r = run.runner(0,0)

def test_1() :
    print "SECTIONS",r.cfg.sections()

def test_2() :
    print r.get_host_info('rhe4-32')

def test_3() :
    print r.get_host_info('leopard')


print "XXXXXXXXXX"
test_1()
print "XXXXXXXXXX"
test_2()
print "XXXXXXXXXX"
test_3()
print "XXXXXXXXXX"
