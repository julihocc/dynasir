# Release Checklist (vNext)

Use this checklist to cut the next release quickly and safely.

## 1) Prepare version bump
- Decide new version: e.g., 0.11.2
- Update:
  - `pyproject.toml`: `version = "<new>"`
  - `src/dynasir/__init__.py`: `__version__ = "<new>"`
  - `CHANGELOG.md`: add section for `<new>`

Commands:
```
# Edit files
$ sed -i 's/^version = ".*"/version = "<new>"/' pyproject.toml
$ sed -i 's/^__version__ = ".*"/__version__ = "<new>"/' src/dynasir/__init__.py

# Validate formatting & tests
$ pre-commit run --all-files || true
$ pytest -m "not slow"
$ pytest -n auto
```

## 2) Commit and push to main
```
$ git add pyproject.toml src/dynasir/__init__.py CHANGELOG.md
$ git commit -m "chore: bump version to <new>"
$ git push origin main
```

## 3) Tag the release
```
$ git pull --tags
$ git tag -a v<new> -m "Release v<new>"
$ git push origin v<new>
```

## 4) Trigger release workflow
- GitHub Actions: `release.yml`
- Trusted publishing: environment `pypi`

Commands:
```
# Requires a token with `workflow` scope configured for gh
$ GH_TOKEN=$(grep 'oauth_token:' ~/.config/gh/hosts.yml | head -1 | awk '{print $2}') \
  gh workflow run release.yml -R julihocc/dynasir -r v<new> -f version=<new>
```

## 5) Verify outputs
```
# GitHub Release
$ gh release view v<new> -R julihocc/dynasir

# PyPI
$ curl -s https://pypi.org/pypi/dynasir/json | jq -r '.info.version'

# Install verification in clean venv
$ python3 -m venv .venv_release_check && source .venv_release_check/bin/activate
$ pip install -U pip && pip install dynasir==<new>
$ python -c "import dynasir; print(dynasir.__version__)"
$ deactivate && rm -rf .venv_release_check
```

## 6) Announce
- Draft announcement based on `ANNOUNCEMENT_v<new>.md` (create from v0.11.1 as template)
- Share links to GitHub Release, PyPI, and key notebook demos

Notes:
- CI must be green before triggering release
- Artifact actions should use `v4` (upload/download)
- `release.yml` calls `ci.yml` via `workflow_call`