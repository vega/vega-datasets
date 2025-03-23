# Changelog

# [3.0.0](https://github.com/vega/vega-datasets/compare/v2.11.0...v3.0.0) (2025-03-23)


### Bug Fixes

* Change default `.arrow` compression to `"uncompressed"` ([#656](https://github.com/vega/vega-datasets/issues/656)) ([7c2e67f](https://github.com/vega/vega-datasets/commit/7c2e67f6e7ba69b00e7cb1473503518942385d11))
* fix `CRLF`-inflated `Resource.bytes` size ([#653](https://github.com/vega/vega-datasets/issues/653)) ([2f1c39f](https://github.com/vega/vega-datasets/commit/2f1c39feab287a02e840a14adce14e47e1aa16ec))
* fix example data in us-state-capitals.json, move ND Capital to correct location ([06cd734](https://github.com/vega/vega-datasets/commit/06cd734e788efe0d0461d539012639aaf0f73bf2))
* guarantee unique resource names in `datapackage.json` ([#640](https://github.com/vega/vega-datasets/issues/640)) ([ca792c8](https://github.com/vega/vega-datasets/commit/ca792c8a973ff0ec75f54d4228a10164c70f82cb))
* use current branch for `Resource.hash` ([#669](https://github.com/vega/vega-datasets/issues/669)) ([16a0c65](https://github.com/vega/vega-datasets/commit/16a0c650c4320abaf82743545ada37f1400ccf07))


### Features

* add generation script for us-state-capitals.json ([#668](https://github.com/vega/vega-datasets/issues/668)) ([dd43f29](https://github.com/vega/vega-datasets/commit/dd43f29f288d45d0f4e0a2f9d211bb6e41c99890))
* add parquet files to index and datapackage.json to export ([#632](https://github.com/vega/vega-datasets/issues/632)) ([719c388](https://github.com/vega/vega-datasets/commit/719c388cc844392cda24517e4e0cda976b1d8519))
* Add Species Habitat Dataset for Faceted Map Examples ([#684](https://github.com/vega/vega-datasets/issues/684)) ([7732f91](https://github.com/vega/vega-datasets/commit/7732f91009512799d0e476df7044c15b0fac8a9d)), closes [/github.com/vega/vega-datasets/pull/684/files#r1973999830](https://github.com//github.com/vega/vega-datasets/pull/684/files/issues/r1973999830) [/docs.astral.sh/ruff/rules/#flake8](https://github.com//docs.astral.sh/ruff/rules//issues/flake8)
* adds `Resource.hash` in `datapackage.json` ([#665](https://github.com/vega/vega-datasets/issues/665)) ([9176bda](https://github.com/vega/vega-datasets/commit/9176bdab04ffcebc75bb9bf07cfcbc754dd8db00))
* adds generation script for income.json ([#672](https://github.com/vega/vega-datasets/issues/672)) ([40620d6](https://github.com/vega/vega-datasets/commit/40620d61fd3df815f21d9685ef7a47edc11f8986)), closes [#653](https://github.com/vega/vega-datasets/issues/653) [#671](https://github.com/vega/vega-datasets/issues/671)
* Correct and document `crimea.json` ([#648](https://github.com/vega/vega-datasets/issues/648)) ([369b462](https://github.com/vega/vega-datasets/commit/369b462f7505e4ef3454668793e001e3620861ff))
* generate `frictionless` data package metadata ([#631](https://github.com/vega/vega-datasets/issues/631)) ([3987d4e](https://github.com/vega/vega-datasets/commit/3987d4e896432778407cb128d629b1cecefd0742)), closes [#629](https://github.com/vega/vega-datasets/issues/629) [/github.com/vega/vega-datasets/pull/631#issuecomment-2503760452](https://github.com//github.com/vega/vega-datasets/pull/631/issues/issuecomment-2503760452) [/github.com/vega/vega-datasets/pull/631#pullrequestreview-2465311789](https://github.com//github.com/vega/vega-datasets/pull/631/issues/pullrequestreview-2465311789) [/github.com/vega/vega-datasets/pull/631#issuecomment-2504151082](https://github.com//github.com/vega/vega-datasets/pull/631/issues/issuecomment-2504151082) [/github.com/vega/vega-datasets/pull/631#issuecomment-2503825716](https://github.com//github.com/vega/vega-datasets/pull/631/issues/issuecomment-2503825716) [/github.com/vega/vega-datasets/pull/631#issuecomment-2504182615](https://github.com//github.com/vega/vega-datasets/pull/631/issues/issuecomment-2504182615) [/github.com/vega/vega-datasets/pull/631#issuecomment-2503825716](https://github.com//github.com/vega/vega-datasets/pull/631/issues/issuecomment-2503825716)
* Improve `flights.*` dataset reproducibility ([#645](https://github.com/vega/vega-datasets/issues/645)) ([a88ff4c](https://github.com/vega/vega-datasets/commit/a88ff4c094e0eb4a88ad4f9793d33498bd39225d))
* replace `SOURCES.md` with `datapackage.md` ([#643](https://github.com/vega/vega-datasets/issues/643)) ([5eaa256](https://github.com/vega/vega-datasets/commit/5eaa256486deec59f3c4441d0abb568688ff5a81))
* Use a datetime column in `flights-3m.parquet` ([#642](https://github.com/vega/vega-datasets/issues/642)) ([0c5dc68](https://github.com/vega/vega-datasets/commit/0c5dc68c6bc19cf2c864909ecb06a624d788cec0))

# [2.11.0](https://github.com/vega/vega-datasets/compare/v2.10.0...v2.11.0) (2024-11-16)


### Bug Fixes

* replace data/flights-3m.csv with data/flights-3m.parquet ([#628](https://github.com/vega/vega-datasets/issues/628)) ([12644bf](https://github.com/vega/vega-datasets/commit/12644bfc150902035501637bbdc39f9393630b79))

# [2.10.0](https://github.com/vega/vega-datasets/compare/v2.9.0...v2.10.0) (2024-11-11)


### Bug Fixes

* correct timestamp calculations in flight datasets & add generation script ([#626](https://github.com/vega/vega-datasets/issues/626)) ([f617597](https://github.com/vega/vega-datasets/commit/f61759719966cec696e643318ad13c52fa1c0801))

# [2.9.0](https://github.com/vega/vega-datasets/compare/v2.8.1...v2.9.0) (2024-09-06)


### Features

*  correct monarchs.json and add source information ([#596](https://github.com/vega/vega-datasets/issues/596)) ([2f62800](https://github.com/vega/vega-datasets/commit/2f6280027feed79574fb978a3b7007ea40485826))
* update gapminder.json and add source information ([#580](https://github.com/vega/vega-datasets/issues/580)) ([76feaab](https://github.com/vega/vega-datasets/commit/76feaab74a7f5f2bee8ede28ddcf865241681e64))

## [2.8.1](https://github.com/vega/vega-datasets/compare/v2.8.0...v2.8.1) (2024-03-06)


### Bug Fixes

* write missing arrow footer ([1d17d58](https://github.com/vega/vega-datasets/commit/1d17d588cb9b165fe419b6ed1f4814fc926fc6e5)), closes [#545](https://github.com/vega/vega-datasets/issues/545)

# [2.8.0](https://github.com/vega/vega-datasets/compare/v2.7.0...v2.8.0) (2024-01-19)


### Bug Fixes

* add missing babel plugins ([bca14bb](https://github.com/vega/vega-datasets/commit/bca14bbc5336d975253288fbaa27f374b4d1838b))
* correct browserlists for module and smaller builds ([e1f1f0b](https://github.com/vega/vega-datasets/commit/e1f1f0b87e538122b61a0cc7c97351ad5830a563))


### Features

* data file for Vega Warming Stripes ([#530](https://github.com/vega/vega-datasets/issues/530)) ([cfe9e5d](https://github.com/vega/vega-datasets/commit/cfe9e5d0a61be27eda0b803074a3a7722004b6e3))
* update es versions ([#441](https://github.com/vega/vega-datasets/issues/441)) ([415952c](https://github.com/vega/vega-datasets/commit/415952cd98d7afe4bb959e382e4b9d5e21082cbb))

# [2.7.0](https://github.com/vega/vega-datasets/compare/v2.5.4...v2.7.0) (2023-03-13)


### Features

* add continents to gapminder-health-income dataset ([1476696](https://github.com/vega/vega-datasets/commit/1476696d85540e3801c2bf1eb483157b560a1297))

## <small>2.5.4 (2023-02-13)</small>

* ci: no releases ([7566172](https://github.com/vega/vega-datasets/commit/7566172))
* ci: test on main ([ca722ab](https://github.com/vega/vega-datasets/commit/ca722ab))
* chore: remove auto and use release-it instead ([e28c69b](https://github.com/vega/vega-datasets/commit/e28c69b))
* chore: switch to esm rollup, update deps, fix style of changelog ([d15549f](https://github.com/vega/vega-datasets/commit/d15549f))
* chore: upgrade deps ([b07a963](https://github.com/vega/vega-datasets/commit/b07a963))
* chore(deps-dev): bump @babel/core from 7.19.3 to 7.19.6 (#397) ([5e1db00](https://github.com/vega/vega-datasets/commit/5e1db00)), closes [#397](https://github.com/vega/vega-datasets/issues/397)
* chore(deps-dev): bump @babel/core from 7.19.6 to 7.20.5 (#403) ([f1d5945](https://github.com/vega/vega-datasets/commit/f1d5945)), closes [#403](https://github.com/vega/vega-datasets/issues/403)
* chore(deps-dev): bump @babel/core from 7.20.5 to 7.20.7 (#413) ([d99a2d0](https://github.com/vega/vega-datasets/commit/d99a2d0)), closes [#413](https://github.com/vega/vega-datasets/issues/413)
* chore(deps-dev): bump @babel/core from 7.20.7 to 7.20.12 (#419) ([3e4d7be](https://github.com/vega/vega-datasets/commit/3e4d7be)), closes [#419](https://github.com/vega/vega-datasets/issues/419)
* chore(deps-dev): bump @babel/plugin-transform-runtime (#402) ([934b54d](https://github.com/vega/vega-datasets/commit/934b54d)), closes [#402](https://github.com/vega/vega-datasets/issues/402)
* chore(deps-dev): bump @babel/preset-env from 7.19.3 to 7.19.4 (#400) ([98bad58](https://github.com/vega/vega-datasets/commit/98bad58)), closes [#400](https://github.com/vega/vega-datasets/issues/400)
* chore(deps-dev): bump @babel/preset-env from 7.19.4 to 7.20.2 (#405) ([c4d46a2](https://github.com/vega/vega-datasets/commit/c4d46a2)), closes [#405](https://github.com/vega/vega-datasets/issues/405)
* chore(deps-dev): bump @babel/runtime from 7.19.0 to 7.20.1 (#401) ([a1b206d](https://github.com/vega/vega-datasets/commit/a1b206d)), closes [#401](https://github.com/vega/vega-datasets/issues/401)
* chore(deps-dev): bump @babel/runtime from 7.20.1 to 7.20.6 (#406) ([a0d7294](https://github.com/vega/vega-datasets/commit/a0d7294)), closes [#406](https://github.com/vega/vega-datasets/issues/406)
* chore(deps-dev): bump @babel/runtime from 7.20.6 to 7.20.7 (#411) ([31b3851](https://github.com/vega/vega-datasets/commit/31b3851)), closes [#411](https://github.com/vega/vega-datasets/issues/411)
* chore(deps-dev): bump @babel/runtime from 7.20.7 to 7.20.13 (#421) ([45cda33](https://github.com/vega/vega-datasets/commit/45cda33)), closes [#421](https://github.com/vega/vega-datasets/issues/421)
* chore(deps-dev): bump @rollup/plugin-json from 4.1.0 to 5.0.1 (#398) ([6cb8333](https://github.com/vega/vega-datasets/commit/6cb8333)), closes [#398](https://github.com/vega/vega-datasets/issues/398)
* chore(deps-dev): bump @rollup/plugin-json from 5.0.1 to 5.0.2 (#408) ([d8e651e](https://github.com/vega/vega-datasets/commit/d8e651e)), closes [#408](https://github.com/vega/vega-datasets/issues/408)
* chore(deps-dev): bump @rollup/plugin-json from 5.0.2 to 6.0.0 (#414) ([01bcdd6](https://github.com/vega/vega-datasets/commit/01bcdd6)), closes [#414](https://github.com/vega/vega-datasets/issues/414)
* chore(deps-dev): bump @rollup/plugin-node-resolve from 14.1.0 to 15.0.1 ([ed2c9d1](https://github.com/vega/vega-datasets/commit/ed2c9d1))
* chore(deps-dev): bump @types/d3-dsv from 3.0.0 to 3.0.1 (#410) ([4f15a6a](https://github.com/vega/vega-datasets/commit/4f15a6a)), closes [#410](https://github.com/vega/vega-datasets/issues/410)
* chore(deps-dev): bump rollup-plugin-ts from 3.0.2 to 3.2.0 (#418) ([25620f7](https://github.com/vega/vega-datasets/commit/25620f7)), closes [#418](https://github.com/vega/vega-datasets/issues/418)
* chore(deps-dev): bump terser from 5.15.1 to 5.16.0 (#407) ([7700f40](https://github.com/vega/vega-datasets/commit/7700f40)), closes [#407](https://github.com/vega/vega-datasets/issues/407)
* chore(deps-dev): bump terser from 5.16.0 to 5.16.1 (#409) ([f1775b8](https://github.com/vega/vega-datasets/commit/f1775b8)), closes [#409](https://github.com/vega/vega-datasets/issues/409)
* chore(deps-dev): bump terser from 5.16.1 to 5.16.2 (#420) ([164b546](https://github.com/vega/vega-datasets/commit/164b546)), closes [#420](https://github.com/vega/vega-datasets/issues/420)
* chore(deps-dev): bump typescript from 4.8.4 to 4.9.3 (#404) ([43e0e34](https://github.com/vega/vega-datasets/commit/43e0e34)), closes [#404](https://github.com/vega/vega-datasets/issues/404)
* chore(deps-dev): bump typescript from 4.9.3 to 4.9.4 (#412) ([8f4b829](https://github.com/vega/vega-datasets/commit/8f4b829)), closes [#412](https://github.com/vega/vega-datasets/issues/412)
* chore(deps-dev): bump typescript from 4.9.4 to 4.9.5 (#417) ([6b776f4](https://github.com/vega/vega-datasets/commit/6b776f4)), closes [#417](https://github.com/vega/vega-datasets/issues/417)
* chore(deps): bump json5 from 2.2.1 to 2.2.3 (#415) ([32fe2e7](https://github.com/vega/vega-datasets/commit/32fe2e7)), closes [#415](https://github.com/vega/vega-datasets/issues/415)
* chore(deps): bump ua-parser-js from 1.0.2 to 1.0.33 (#416) ([c91a047](https://github.com/vega/vega-datasets/commit/c91a047)), closes [#416](https://github.com/vega/vega-datasets/issues/416)

### v2.5.3 (Sun Oct 09 2022)

#### 🐛 Bug Fix

- fix: add resolve to include d3 dependency [#395](https://github.com/vega/vega-datasets/pull/395) ([@domoritz](https://github.com/domoritz))

#### Authors: 1

- Dominik Moritz ([@domoritz](https://github.com/domoritz))

---

### v2.5.2 (Sun Oct 09 2022)

#### 🐛 Bug Fix

- fix: switch back to UMD bundles [#393](https://github.com/vega/vega-datasets/pull/393) ([@domoritz](https://github.com/domoritz))

#### Authors: 1

- Dominik Moritz ([@domoritz](https://github.com/domoritz))

---

### v2.5.1 (Sat Oct 01 2022)

#### 🐛 Bug Fix


#### Authors: 1

- Dominik Moritz ([@domoritz](https://github.com/domoritz))

---

### v2.5.0 (Fri Sep 30 2022)

#### 🚀 Enhancement


#### 🐛 Bug Fix

- feat: refactor builds and include sourcemaps and ts support [#388](https://github.com/vega/vega-datasets/pull/388) ([@domoritz](https://github.com/domoritz))
- chore: simplify token setup, update deps [#384](https://github.com/vega/vega-datasets/pull/384) ([@domoritz](https://github.com/domoritz))

#### 🔩 Dependency Updates

- chore(deps-dev): bump terser from 5.14.2 to 5.15.0 [#385](https://github.com/vega/vega-datasets/pull/385) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.77.3 to 2.79.0 [#386](https://github.com/vega/vega-datasets/pull/386) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.7.4 to 4.8.2 [#387](https://github.com/vega/vega-datasets/pull/387) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.37.1 to 10.37.4 [#380](https://github.com/vega/vega-datasets/pull/380) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.37.1 to 10.37.4 [#381](https://github.com/vega/vega-datasets/pull/381) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.37.1 to 10.37.4 [#382](https://github.com/vega/vega-datasets/pull/382) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.76.0 to 2.77.2 [#383](https://github.com/vega/vega-datasets/pull/383) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.14.1 to 5.14.2 [#379](https://github.com/vega/vega-datasets/pull/379) ([@dependabot[bot]](https://github.com/dependabot[bot]))

#### Authors: 2

- [@dependabot[bot]](https://github.com/dependabot[bot])
- Dominik Moritz ([@domoritz](https://github.com/domoritz))

---

### v2.4.0 (Thu Jul 14 2022)

:tada: This release contains work from new contributors! :tada:

Thanks for all your work!

:heart: Cameron Yick ([@hydrosquall](https://github.com/hydrosquall))

:heart: null[@PBI-David](https://github.com/PBI-David)

#### 🚀 Enhancement

- feat: add Platformer Example Dataset [#376](https://github.com/vega/vega-datasets/pull/376) ([@PBI-David](https://github.com/PBI-David) [@domoritz](https://github.com/domoritz))

#### 🐛 Bug Fix

- chore: set up auto for versioning/release management [#312](https://github.com/vega/vega-datasets/pull/312) ([@hydrosquall](https://github.com/hydrosquall))
- Split Multi-Variable Declarations [#271](https://github.com/vega/vega-datasets/pull/271) ([@p42-ai[bot]](https://github.com/p42-ai[bot]))
- Use Template Literals [#270](https://github.com/vega/vega-datasets/pull/270) ([@p42-ai[bot]](https://github.com/p42-ai[bot]))
- Use Template Literals [#267](https://github.com/vega/vega-datasets/pull/267) (p42@p42.ai [@domoritz](https://github.com/domoritz) [@p42-ai[bot]](https://github.com/p42-ai[bot]))

#### 🔩 Dependency Updates

- chore(deps-dev): bump rollup from 2.75.5 to 2.75.7 [#373](https://github.com/vega/vega-datasets/pull/373) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.14.0 to 5.14.1 [#374](https://github.com/vega/vega-datasets/pull/374) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.7.2 to 4.7.4 [#375](https://github.com/vega/vega-datasets/pull/375) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.13.1 to 5.14.0 [#366](https://github.com/vega/vega-datasets/pull/366) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @rollup/plugin-node-resolve from 13.2.1 to 13.3.0 [#367](https://github.com/vega/vega-datasets/pull/367) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.36.5 to 10.37.1 [#368](https://github.com/vega/vega-datasets/pull/368) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.36.5 to 10.37.1 [#369](https://github.com/vega/vega-datasets/pull/369) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.71.1 to 2.75.5 [#370](https://github.com/vega/vega-datasets/pull/370) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.6.4 to 4.7.2 [#371](https://github.com/vega/vega-datasets/pull/371) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.36.5 to 10.37.1 [#372](https://github.com/vega/vega-datasets/pull/372) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.12.1 to 5.13.1 [#362](https://github.com/vega/vega-datasets/pull/362) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.70.1 to 2.71.1 [#363](https://github.com/vega/vega-datasets/pull/363) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.6.3 to 4.6.4 [#364](https://github.com/vega/vega-datasets/pull/364) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @rollup/plugin-node-resolve from 13.1.3 to 13.2.1 [#365](https://github.com/vega/vega-datasets/pull/365) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump node-fetch from 2.6.1 to 2.6.7 [#361](https://github.com/vega/vega-datasets/pull/361) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.6.2 to 4.6.3 [#355](https://github.com/vega/vega-datasets/pull/355) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.68.0 to 2.70.1 [#356](https://github.com/vega/vega-datasets/pull/356) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.32.6 to 10.36.5 [#357](https://github.com/vega/vega-datasets/pull/357) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.32.6 to 10.36.5 [#358](https://github.com/vega/vega-datasets/pull/358) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.32.6 to 10.36.5 [#359](https://github.com/vega/vega-datasets/pull/359) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.12.0 to 5.12.1 [#360](https://github.com/vega/vega-datasets/pull/360) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump minimist from 1.2.5 to 1.2.6 [#354](https://github.com/vega/vega-datasets/pull/354) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump actions/setup-node from 2.5.1 to 3 [#349](https://github.com/vega/vega-datasets/pull/349) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump actions/checkout from 2 to 3 [#350](https://github.com/vega/vega-datasets/pull/350) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.5.5 to 4.6.2 [#351](https://github.com/vega/vega-datasets/pull/351) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.10.0 to 5.12.0 [#352](https://github.com/vega/vega-datasets/pull/352) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.67.0 to 2.68.0 [#353](https://github.com/vega/vega-datasets/pull/353) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.32.5 to 10.32.6 [#342](https://github.com/vega/vega-datasets/pull/342) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.32.5 to 10.32.6 [#343](https://github.com/vega/vega-datasets/pull/343) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.32.5 to 10.32.6 [#346](https://github.com/vega/vega-datasets/pull/346) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.62.0 to 2.67.0 [#344](https://github.com/vega/vega-datasets/pull/344) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.5.4 to 4.5.5 [#345](https://github.com/vega/vega-datasets/pull/345) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @rollup/plugin-node-resolve from 13.1.2 to 13.1.3 [#347](https://github.com/vega/vega-datasets/pull/347) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.32.3 to 10.32.5 [#336](https://github.com/vega/vega-datasets/pull/336) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.32.3 to 10.32.5 [#338](https://github.com/vega/vega-datasets/pull/338) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.32.3 to 10.32.5 [#340](https://github.com/vega/vega-datasets/pull/340) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.5.2 to 4.5.4 [#337](https://github.com/vega/vega-datasets/pull/337) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @rollup/plugin-node-resolve from 13.0.6 to 13.1.2 [#339](https://github.com/vega/vega-datasets/pull/339) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.60.2 to 2.62.0 [#341](https://github.com/vega/vega-datasets/pull/341) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump actions/setup-node from 2.5.0 to 2.5.1 [#335](https://github.com/vega/vega-datasets/pull/335) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump actions/setup-node from 2.4.1 to 2.5.0 [#328](https://github.com/vega/vega-datasets/pull/328) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.32.2 to 10.32.3 [#329](https://github.com/vega/vega-datasets/pull/329) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.59.0 to 2.60.2 [#330](https://github.com/vega/vega-datasets/pull/330) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.4.4 to 4.5.2 [#331](https://github.com/vega/vega-datasets/pull/331) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.32.2 to 10.32.3 [#332](https://github.com/vega/vega-datasets/pull/332) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.32.2 to 10.32.3 [#333](https://github.com/vega/vega-datasets/pull/333) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.9.0 to 5.10.0 [#334](https://github.com/vega/vega-datasets/pull/334) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @rollup/plugin-node-resolve from 13.0.5 to 13.0.6 [#322](https://github.com/vega/vega-datasets/pull/322) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.58.0 to 2.59.0 [#323](https://github.com/vega/vega-datasets/pull/323) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.4.3 to 4.4.4 [#324](https://github.com/vega/vega-datasets/pull/324) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.32.1 to 10.32.2 [#325](https://github.com/vega/vega-datasets/pull/325) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.32.1 to 10.32.2 [#326](https://github.com/vega/vega-datasets/pull/326) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.32.1 to 10.32.2 [#327](https://github.com/vega/vega-datasets/pull/327) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.57.0 to 2.58.0 [#318](https://github.com/vega/vega-datasets/pull/318) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/first-time-contributor from 10.32.0 to 10.32.1 [#319](https://github.com/vega/vega-datasets/pull/319) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @auto-it/conventional-commits from 10.32.0 to 10.32.1 [#320](https://github.com/vega/vega-datasets/pull/320) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump auto from 10.32.0 to 10.32.1 [#321](https://github.com/vega/vega-datasets/pull/321) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump typescript from 4.4.2 to 4.4.3 [#315](https://github.com/vega/vega-datasets/pull/315) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump terser from 5.7.2 to 5.9.0 [#314](https://github.com/vega/vega-datasets/pull/314) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump rollup from 2.56.3 to 2.57.0 [#316](https://github.com/vega/vega-datasets/pull/316) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps-dev): bump @rollup/plugin-node-resolve from 13.0.4 to 13.0.5 [#317](https://github.com/vega/vega-datasets/pull/317) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump actions/setup-node from 2.4.0 to 2.4.1 [#313](https://github.com/vega/vega-datasets/pull/313) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- chore(deps): bump actions/setup-node from v1 to v2.1.5 [#290](https://github.com/vega/vega-datasets/pull/290) ([@dependabot[bot]](https://github.com/dependabot[bot]))
- ci: upgrade to GitHub-native Dependabot [#289](https://github.com/vega/vega-datasets/pull/289) ([@dependabot-preview[bot]](https://github.com/dependabot-preview[bot]) [@domoritz](https://github.com/domoritz))

#### Authors: 8

- [@dependabot-preview[bot]](https://github.com/dependabot-preview[bot])
- [@dependabot[bot]](https://github.com/dependabot[bot])
- [@p42-ai[bot]](https://github.com/p42-ai[bot])
- [@PBI-David](https://github.com/PBI-David)
- Cameron Yick ([@hydrosquall](https://github.com/hydrosquall))
- Dominik Moritz ([@domoritz](https://github.com/domoritz))
- Jeffrey Heer ([@jheer](https://github.com/jheer))
- P42 (p42@p42.ai)

---

### Version 2.4

- Add `platformer-terrain.json`.

### Version 2.2

- Add `sp500-2000.csv`.

### Version 2.1

- Add `version` property to js module.

### Version 2.0

- Add `football.json`. Thanks to @eitanlees!
- Add `penguins.json`.
- Add `seattle-weather-hourly-normals.csv`.
- Update `weather.csv` and `seattle-weather.csv` with better encoded weather condition, indicating more rain. Thanks to @visnup!
- Update co2-concentration data and add seasonally adjusted CO2 field.
- Switch to ISO 8601 dates in `seattle-weather.csv`.
- Rename `weball26.json` to `political-contributions.json`.
- Convert `birdstrikes.json` to `birdstrikes.csv` and use ISO 8601 dates.
- Convert `movies.json` to use column names with spaces and use ISO 8601 dates.
- Remove `climate.json`.
- Replace `seattle-temps.csv` with more general `seattle-weather-hourly-normals.csv`.
- Remove `sf-temps.csv`.
- Remove `graticule.json`. Use graticule generator instead.
- Remove `points.json`.
- Remove `iris.json`. Use `penguins.json` instead.

### Version 1.31

- Strip BOM from `windvectors.csv`.

### Version 1.30

- Update `seattle-temps` with better sourced data.
- Update `sf-temps` with better sourced data.

### Version 1.29

- Add `ohlc.json`. Thanks to @eitanlees!

### Version 1.28

- Add `annual-precip.json`. Thanks to @mattijn!

### Version 1.27

- Add `volcano.json`.

### Version 1.26

- Add `uniform-2d.json`.

### Version 1.22

- Add `windvectors.csv`. Thanks to @jwoLondon!

### Version 1.20

- Add `us-unemployment.csv`. Thanks to @palewire!

### Version 1.19

- Remove time in `weather.csv`.

### Version 1.18

- Fix typo in city name in `us-state-capitals.json`

### Version 1.17

- Made data consistent with respect to origin by making them originated from a Unix platform.

### Version 1.16

- Add `co2-concentration.csv`.

### Version 1.15

- Add `earthquakes.json`.

### Version 1.14

- Add `graticule.json`, London borough boundaries, borough centroids and tube (metro) rail lines.

### Version 1.13

- Add `disasters.csv` with disaster type, year and deaths.

### Version 1.12

- Add 0 padding in zipcode dataset.

### Version 1.11

- Add U district cuisine data

### Version 1.10

- Add weather data for Seattle and New York.

### Version 1.9

- Add income, zipcodes, lookup data, and a dataset with three independent geo variables.

### Version 1.8

- Remove all tabs in `github.csv` to prevent incorrect field name parsing.

### Version 1.7

* Dates in `movies.json` are all recognized as date types by datalib.
* Dates in `crimea.json` are now in ISO format (YYYY-MM-DD).

### Version 1.6

* Fix `cars.json` date format.

### Version 1.5

* Add [Gapminder Health v.s. Income](data/gapminder-health-income.csv) dataset.
* Add generated Github contributions data for punch card visualization.

### Version 1.4

* Add Anscombe's Quartet dataset.

### Version 1.3

* Change date format in weather data so that it can be parsed in all browsers. Apparently YYYY/MM/DD is fine. Can also omit hours now.

### Version 1.2

* Decode origins in cars dataset.
* Add Unemployment Across Industries in US.

### Version 1.1.1

* Fixed the date parsing on the CrossFilter datasets -- an older version of the data was copied over on initial import. A script is now available via `npm run flights N` to re-sample `N` records from the original `flights-3m.csv` dataset.

### Version 1.1

* Add `seattle-weather` dataset. Transformed with https://gist.github.com/domoritz/acb8c13d5dadeb19636c.

### Version 1.0, October 8, 2015

* Initial import from Vega and Vega-Lite.
* Change field names in `cars.json` to be more descriptive (`hp` to `Horsepower`).
