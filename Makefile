ROOT ?= .
OUT ?= _stage1
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

.PHONY: site stage1 stage2 test-site clean

site: stage1 stage2

stage1:
	docker compose run --rm --user $(HOST_UID):$(HOST_GID) -e HOME=/tmp -e UV_CACHE_DIR=/tmp/uv py uv run --no-sync python wikic/wikic.py compile --root $(ROOT) --out $(OUT)

stage2:
	docker compose run --rm -e HOST_UID=$(HOST_UID) -e HOST_GID=$(HOST_GID) jekyll sh -c "bundle install && bundle exec jekyll build --source $(OUT) --destination _site; rc=\$$?; chown -R \$$HOST_UID:\$$HOST_GID _site $(OUT); exit \$$rc"


clean:
	rm -rf _stage1 _site

test-site:
	$(MAKE) site ROOT=tests/fixtures/wiki OUT=_stage1
	python3 tests/check_site.py _site

.PHONY: test-blob

test-blob:
	docker compose up -d --wait blob
	docker compose run --rm --user $(HOST_UID):$(HOST_GID) -e HOME=/tmp -e UV_CACHE_DIR=/tmp/uv -e BLOB_E2E=1 -e BLOB_BASE=http://blob:9000/wiki py uv run --no-sync python -m unittest tests.test_blob_http -v; rc=$$?; docker compose stop blob; exit $$rc
