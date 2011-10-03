#!/bin/sh

n=3

rm -rf build

p=`which python`

case "$p"
in
/usr/stsci/*) : ;;
*)
	echo why is python set to $p
	echo path = $PATH
	exit 1
	;;
esac

unset PYTHONPATH

there=/ssbwebv1/data2/steuermann/s$n

rm -rf $there

python setup.py -q install --home $there

rm -f /eng/ssb/websites/ssb/steuermann/s$n.cgi

ln -s $there/bin/steuermann_report.cgi /eng/ssb/websites/ssb/steuermann/s$n.cgi

if grep -q s$n.cgi  /eng/ssb/websites/ssb/index.html 
then
	:
else
	id=/eng/ssb/websites/ssb

	sed 's?<\!--STEUERMANN-->?<\!--STEUERMANN--><a href="steuermann/s'$n'.cgi">s'$n'</a> <br> ?' < $id/index.html > tmp 

	cp tmp $id/index.html
	ls -l $id/index.html

fi

chgrp -R ssb $there


