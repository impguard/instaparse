test = nosetests --stop

.PHONY: check, checkpython, checkjava, clean

all:
	@python src/compile/compile.py -s src -i compile/importFile -f compile/fileOrder out.py

check:
	@$(test)

checkpython:
	@$(test) test/pygen_test.py

checkjava:
	@$(test) test/javagen_test.py

clean:
	@rm -rf test/*.pyc src/*.pyc test_tmp out.py

