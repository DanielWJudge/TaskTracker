.PHONY: bump-patch bump-minor bump-major release-patch release-minor release-major

bump-patch:
	./bump_version.py patch

bump-minor:
	./bump_version.py minor

bump-major:
	./bump_version.py major

release-patch: bump-patch tag push
release-minor: bump-minor tag push
release-major: bump-major tag push

tag:
	@echo "Tagging version..."
	@git add src/momentum/__version__.py
	@VERSION=$$(python3 -c 'import momentum.__version__ as v; print(v.__version__)') && \
	 git commit -m "Bump version to $$VERSION" && \
	 git tag v$$VERSION

push:
	@git push && git push --tags
