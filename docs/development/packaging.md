# Packaging and deployment

## Packaging

This plugin is using the [qgis-plugin-ci](https://github.com/opengisch/qgis-plugin-ci/) tool to perform packaging operations.  
Under the hood, the package command is performing a `git archive` run based on `CHANGELOG.md`.

Use it like so:

```bash
# package a specific version
uvx --with-requirements requirements/packaging.txt qgis-plugin-ci package 1.3.1
# package latest version
uvx --with-requirements requirements/packaging.txt qgis-plugin-ci package latest
```

## Release a version

Through git workflow:

1. Add the new version to the `CHANGELOG.md`
2. Optionally change the version number in `metadata.txt`
3. Apply a git tag with the relevant version: `git tag -a X.y.z {git commit hash} -m "This version rocks!"`
4. Push tag to main branch: `git push origin X.y.z`
