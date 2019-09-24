help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

install: ## Install requirements
	@[ -n "${VIRTUAL_ENV}" ] || (echo "ERROR: This should be run from a virtualenv" && exit 1)
	pip install -r requirements.txt

.PHONY: requirements.txt
requirements.txt: ## Regenerate requirements.txt
	pip-compile requirements.in > $@

dev: ## Run dev environment with a watcher
	nodemon -e py -x python main.py

tdd: ## Run tests with a watcher
	CI=1 ptw -- -sx

test: ## Run test suite
	CI=1 pytest --cov

fixtures: tests/fixtures/ad-rss.xml tests/fixtures/article.html

tests/fixtures/ad-rss.xml:
	curl --silent https://www.architecturaldigest.com/feed/rss > $@

tests/fixtures/article.html:
	curl --silent https://www.architecturaldigest.com/story/why-high-gloss-paint-should-be-on-your-radar > $@

tests/fixtures/gallery.html:
	curl --silent https://www.architecturaldigest.com/gallery/dramatic-history-londons-underground > $@
