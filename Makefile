build_docs:
	python docs/backdoc.py --source docs/index.md --title "Django proxy storage documentation" > docs/index.html
	python docs/post_process_docs.py

watch_docs:
	make build_docs
	watchmedo shell-command -p "*.md" -R -c "make build_docs" docs/

prepare_for_tests:
	- test "${TRAVIS}" != "true" && make prepare_infra_for_tests
	pip install tox

prepare_infra_for_tests:
	apt-get install -y python-pip
	apt-get install -y mongodb-server
	make install_python3

install_python3:
	apt-get update
	apt-get install -y python-software-properties
	add-apt-repository -y ppa:fkrull/deadsnakes
	apt-get install -y python3.4