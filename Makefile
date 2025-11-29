help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"

install: ## Install requirements
	uv sync --all-extras

dev: ## Run dev environment with a watcher
	nodemon -e py -x python main.py

lint: ## Run linter
	ruff check .
	ruff format --check .
	mypy .

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

docker/build:
	docker build --tag crccheck/refeed .

docker/run:
	docker run -i -t --rm -p 8080:8080 crccheck/refeed

docker/push: ## Build and push production Docker artifact
	docker buildx build --platform linux/amd64 --tag crccheck/refeed --push .
