ROOT ?= pages

.PHONY: site stage1 stage2 serve test test-site clean

# Wiki pages are in pages/. _stage1/ and _site/ live in Docker volumes (never on
# the host); ./blob (git-ignored) is mounted at _site/blob/ by the jekyll service.
site: stage1 stage2

stage1:
	docker compose run --rm py sh -c "find _stage1 -mindepth 1 -delete; uv run --no-sync python wikic/wikic.py compile --root $(ROOT) --out _stage1"

stage2:
	mkdir -p blob
	docker compose run --rm jekyll

serve:
	mkdir -p blob
	docker compose run --rm --service-ports jekyll sh -c "bundle install && bundle exec jekyll serve --source . --destination ../_site --host 0.0.0.0 --port 4000 --skip-initial-build --no-watch"

test:
	python3 -m unittest discover -s tests

test-site:
	$(MAKE) site ROOT=tests/fixtures/wiki
	docker compose run --rm py uv run --no-sync python tests/check_site.py _site

clean:
	docker compose down --remove-orphans
	docker volume rm -f agent-wiki_stage1 agent-wiki_site
	rmdir _site _stage1 2>/dev/null || true
