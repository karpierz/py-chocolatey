Changelog
=========

0.9.0 (2025-09-19)
------------------
- Making and mark the package typed.
- Add license() command. Available since Chocolatey v2.5.0
- Add support() command. Available since Chocolatey v2.5.0
- Fix an error in export(): was include_version -> include_version_numbers.
- Remove all_versions option from installed(). Dropped in Chocolatey v2.0.0
- | The ignore_pinned option is now supported in installed(). Available since
  | Chocolatey v2.5.0
- Setup (dependencies) update and fixes.

0.8.3 (2025-09-01)
------------------
- Upgrade chocolatey installer for chocolatey.2.5.1.nupkg
- Setup (dependencies) update.

0.8.2 (2025-05-15)
------------------
- The distribution is now created using 'build' instead of 'setuptools'.
- Setup (dependencies) update (due to regressions in tox and setuptools).

0.8.1 (2025-05-04)
------------------
- Setup (dependencies) update.

0.8.0 (2025-04-28)
------------------
- Add support for Python 3.14
- Drop support for Python 3.9 (due to compatibility issues).
- Update readthedocs's python to version 3.13
- Update tox's base_python to version 3.13
- Setup (dependencies) update.

0.7.1 (2025-03-20)
------------------
- Upgrade chocolatey installer for chocolatey.2.4.3.nupkg
- Add support for PyPy 3.11
- Drop support for PyPy 3.9
- Setup (dependencies) update.

0.7.0 (2025-02-01)
------------------
- Bugfix for feature_get().
- Bugfix for config_set().
- Bugfix for search().
- Bugfix for template_info().
- Copyright year update.
- | Remove 'unpackself' command - because deprecate, see:
  | https://github.com/chocolatey/choco/issues/3426
- Upgrade chocolatey installer for chocolatey.2.4.2.nupkg
- More unittests.
- 100% code linting.
- 100% code coverage.
- Setup (dependencies) update.

0.6.1 (2024-12-13)
------------------
- Source distribution (\*.tar.gz now) is compliant with PEP-0625.
- Setup (dependencies) update.

0.6.0 (2024-12-10)
------------------
- Upgrade chocolatey installer for chocolatey.2.4.1.nupkg
- More unittests.
- Tox configuration is now in native (toml) format.
- Setup (dependencies) update.

0.5.0 (2024-10-30)
------------------
- Add support for Python 3.13
- Drop support for Python 3.8
- Setup (dependencies) update.

0.4.1 (2024-06-20)
------------------
- Upgrade chocolatey installer for chocolatey.2.3.0.nupkg
- Setup (dependencies) update.

0.4.0 (2024-01-26)
------------------
- Setup update (now based on tox >= 4.0).
- Add support for Python 3.12
- Add support for PyPy 3.9 and 3.10
- Copyright year update.
- Cleanup.

0.3.1 (2023-11-24)
------------------
- Fix for info(). Now works for local_only=True.
- Setup cleanup.

0.3.0 (2023-11-22)
------------------
- Drop support for Python 3.7.
- Setup (dependencies) update.

0.2.2 (2023-10-27)
------------------
- Added --yes option as default for push().

0.2.1 (2023-10-13)
------------------
- Fix for setup.

0.2.0 (2023-10-12)
------------------
- Added Chocolatey.setup() for install chocolatey.

0.1.2 (2023-10-11)
------------------
- Fixes for many functions that failed when the source was set.

0.1.1 (2023-10-11)
------------------
- Added missing source_add().
- Fixes for source(s). Now works on unelevated mode.

0.1.0 (2023-10-09)
------------------
- Added support for non-elevated mode.
- Added (mostly raw) unittests.
- First working release.

0.0.2 (2023-10-05)
------------------
- Small fix for run().

0.0.1 (2023-07-13)
------------------
- Initial commit.

0.0.0 (2023-07-07)
------------------
- Initial commit.
