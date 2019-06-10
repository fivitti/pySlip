install: clean
	clear; python setup.py build; python setup.py install

release: #clean
	@echo "**********************************************"
	@echo "* read ~/installs/pypi.txt before doing this *"
	@echo "**********************************************"
	@read ignore
#	test -n "$(git status | grep \"modified:\")"; echo "There are modified files."; exit 1
#	test -n "$(git status | grep \"Your branch is ahead of\")"; echo "There are uncommitted files."; exit 2
	@$(eval OUTPUT := $(shell git status | grep "modified:"))
	@echo "OUTPUT=$(OUTPUT)"
ifneq ($(OUTPUT), )
	echo "There are modified files."
	exit 1
endif
	@$(eval OUTPUT := $(shell git status | grep "Your branch is ahead of"))
	@echo "OUTPUT=$(OUTPUT)"
ifneq ("$(OUTPUT)", "")
	echo "There are uncommitted files."
	exit 2
endif

#	$(eval RELNUM := $(shell ./bump_release))
#	cp PyPi_README.rst README.rst
#	python3 setup.py sdist bdist_wheel
#	git tag $(RELNUM) -m "$(RELNUM) release"
#	git push --tags origin master
#	rm -Rf build dist pyslip.egg-info
#	python3 setup.py sdist bdist_wheel
#	-twine upload dist/*
#	cp github_README.rst README.rst

clean:
	rm -Rf build dist pySlipQt.egg-info/
