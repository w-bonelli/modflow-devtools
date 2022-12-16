### Version 0.0.6

#### New features

* [feat(build)](https://github.com/modflowpy/flopy/commit/3108c380f29424bcdd1643479f66e849f7f762eb): Restore meson_build function (#15). Committed by w-bonelli on 2022-11-14.

#### Bug fixes

* [fix](https://github.com/modflowpy/flopy/commit/933c79741b0e6a6db7c827414ebf635e62445772): Changes to support running of existing tests (#6). Committed by mjreno on 2022-07-20.
* [fix(ci)](https://github.com/modflowpy/flopy/commit/0bb31907200be32bf2a045d54131f0a1dbd0ae2f): Don't build/test examples on python 3.7 (xmipy requires 3.8+) (#10). Committed by w-bonelli on 2022-11-08.
* [fix(tests)](https://github.com/modflowpy/flopy/commit/3c63aaae581d335b1111b8dd2b929004b3281980): Mark test_download_and_unzip flaky (#11). Committed by w-bonelli on 2022-11-08.
* [fix(fixtures)](https://github.com/modflowpy/flopy/commit/1e5fabdeb6d431f960316b049d68c4919650888c): Fix model-loading fixtures and utilities (#12). Committed by w-bonelli on 2022-11-11.
* [fix(misc)](https://github.com/modflowpy/flopy/commit/80b8d1e1549676debda09383f75db50f5f11417a): Fix multiple issues (#16). Committed by w-bonelli on 2022-11-19.
* [fix(auth)](https://github.com/modflowpy/flopy/commit/89db96ff5fb6e080c189f3a3e348ddf2ded21212): Fix GH API auth token in download_and_unzip (#17). Committed by w-bonelli on 2022-11-19.
* [fix(download)](https://github.com/modflowpy/flopy/commit/58dff9f6c1245b22e3dc10411862d6eacea42e94): Use 'wb' instead of 'ab' mode when writing downloaded files, add retries (#20). Committed by w-bonelli on 2022-12-01.

#### Refactoring

* [refactor](https://github.com/modflowpy/flopy/commit/5aff3427351a0bbe38927d81dad42dd5374b67be): Updates to support modflow6 autotest and remove data path. Committed by mjreno on 2022-08-05.
* [refactor](https://github.com/modflowpy/flopy/commit/e9e14f959e2a2ea016114c2dbfc35555b81459aa): Updates to support modflow6 autotest and remove data path. Committed by mjreno on 2022-08-05.
* [refactor(ci)](https://github.com/modflowpy/flopy/commit/eefb659bb04df6aa18432165850a512285812d15): Create release and publish to PyPI when tags pushed (#14). Committed by w-bonelli on 2022-11-14.
* [refactor(misc)](https://github.com/modflowpy/flopy/commit/1672733df1c17b802f1ade7d28db7bdb90496714): Refactor gh api & other http utilities (#18). Committed by w-bonelli on 2022-11-26.
* [refactor](https://github.com/modflowpy/flopy/commit/bb8fa593cd21f2c0e8e9f3a6c2125fc22d5d9858): Remove mf6 file parsing fns (moved to flopy) (#19). Committed by w-bonelli on 2022-11-28.

