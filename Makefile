all: 	steuermann/specfile.py sr.db

steuermann/specfile.py: steuermann/specfile.exy
	exyapps steuermann/specfile.exy

sr.db:	steuermann/db.sql
	rm -f sr.db
	sqlite3 sr.db < steuermann/db.sql

clean:
	rm -f sr.db
	rm -f steuermann/specfile.py

