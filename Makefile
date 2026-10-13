ROOT ?= .
OUT ?= _stage1

.PHONY: site stage1 stage2 test-site

site: stage1 stage2

stage1:
	docker compose run --rm py uv run --no-sync python wikic/wikic.py compile --root $(ROOT) --out $(OUT)

stage2:
	docker compose run --rm jekyll sh -c "bundle install && bundle exec jekyll build --source $(OUT) --destination _site"

test-site:
	$(MAKE) site ROOT=tests/fixtures/wiki OUT=_stage1
	python3 tests/check_site.py _site

.PHONY: test-blob

test-blob:
	docker compose up -d --wait blob
	BLOB_E2E=1 python3 -m unittest tests.test_blob_http -v; rc=$$?; docker compose stop blob; exit $$rc
