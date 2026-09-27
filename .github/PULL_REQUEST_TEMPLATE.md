<!-- PR titles follow Conventional Commits (e.g. `feat: add ... dataset`); CI checks this. -->

Please see [CONTRIBUTING.md](https://github.com/vega/vega-datasets/blob/main/CONTRIBUTING.md), and:
- [ ] Document new or changed datasets in `_data/datapackage_additions.toml` (description, sources, license).
- [ ] Run `npm run build`; commit `datapackage.json` only if it changed beyond the timestamp.
- [ ] Run the checks in CONTRIBUTING (`ruff`, `taplo`, `pytest`).
