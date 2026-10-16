ROOT ?= wiki
LINT_FLAGS ?=

.PHONY: build lint stage1 stage2 serve test test-site clean

# Wiki pages are in wiki/. _stage1/ and _site/ live in Docker volumes (never on
# the host); ./blob (git-ignored) is mounted at _site/blob/ by the jekyll service.
build: stage1 stage2

lint:
	docker compose run --rm py uv run --no-sync python lint/lint.py --root $(ROOT) $(LINT_FLAGS)

stage1:
	docker compose run --rm py sh -c "uv run --no-sync python lint/lint.py --root $(ROOT) $(LINT_FLAGS) && find _stage1 -mindepth 1 -delete && uv run --no-sync python build/bulid.py compile --root $(ROOT) --out _stage1"

stage2:
	mkdir -p blob
	docker compose run --rm --no-deps jekyll sh -c "bundle install && bundle exec jekyll build --source . --destination ../_site"

serve: stage1
	mkdir -p blob
	docker compose up

test:
	python3 -m unittest discover -s tests

test-site:
	$(MAKE) build ROOT=tests/fixtures/wiki LINT_FLAGS=--warn-only
	docker compose run --rm py uv run --no-sync python tests/check_site.py _site

clean:
	docker compose down --remove-orphans
	docker volume rm -f agent-wiki_stage1 agent-wiki_site
	rmdir _site _stage1 2>/dev/null || true
