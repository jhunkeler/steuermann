import steuermann.run as run

r = run.runner(0,0)

def test_1() :
    print r.cfg.sections()

def test_2() :
    print r.get_host_info('rhe4-32')


test_1()
test_2()
