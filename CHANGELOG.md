# Changelog

<!--next-version-placeholder-->

## v0.4.2 (2026-07-17)

### Bug Fixes

- Correct psr version_toml, changelog marker, and move build off container
  ([`7846f64`](https://github.com/istvankleijn/pitchmark/commit/7846f64bc94e914ade9bd92b631b0d4be21750a6))

> **Note:** `v0.4.0` and `v0.4.1` were cut while migrating the release pipeline
> from python-semantic-release v7 to v10, and the version-bump step was broken
> for both (fixed by the commit above) — `pyproject.toml` stayed pinned at
> `0.4.0a0` in both tags. As a result, only a `0.4.0a0` prerelease ever reached
> PyPI; no `0.4.0` or `0.4.1` package exists there. `v0.4.2` is the first
> release after `v0.3.1` with a working build and a correctly stamped version.


## v0.4.1 (2026-07-17)

### Bug Fixes

- Pin Python 3.10 in the TestPyPI install-verification step
  ([`cd613fa`](https://github.com/istvankleijn/pitchmark/commit/cd613fa17234cec52fdfa626a8d22f8c0933b0bc))


## v0.4.0 (2026-07-17)

### Features

- Simulate ball rolling on green surface
  ([`b5eec1b`](https://github.com/istvankleijn/pitchmark/commit/b5eec1bb15299d19f621f7c7ec1783ff6ae7d5a0))

### Bug Fixes

- Measure elevation in yards
  ([`3da7500`](https://github.com/istvankleijn/pitchmark/commit/3da7500459553b5a1d83a3dfacf259b91483f029))
- Install uv inside the semantic-release Docker action for build_command
  ([`5e27c65`](https://github.com/istvankleijn/pitchmark/commit/5e27c659612d2f5660a2c8c05d60ee4011ff9ac8))


## v0.3.1 (2023-03-21)
### Fix
* Convert slope grade correctly to percentage ([`c70c5d8`](https://github.com/istvankleijn/pitchmark/commit/c70c5d8840913e9cee0d34912799e7da5a308740))

## v0.3.0 (2023-03-21)
### Feature
* Represent hole ground surfaces as smoothened 3D triangle meshes ([`cfe1c8b`](https://github.com/istvankleijn/pitchmark/commit/cfe1c8b80e78335269b4bf081663f01e82254784))
* Clip and filter LAS/LAZ files ([`5588d06`](https://github.com/istvankleijn/pitchmark/commit/5588d06e4b43bd2dff5b2e9aa0056b4267de8e1a))

### Fix
* Correct calculation of slope in triangle geodataframe ([`a683663`](https://github.com/istvankleijn/pitchmark/commit/a683663f095d9dff335724165652f74e1fc9b0be))

### Documentation
* Markdown badges for PyPI and Codecov ([`118e4d4`](https://github.com/istvankleijn/pitchmark/commit/118e4d4b9ae15cffbd3f7b95e64120ebeb62b077))
* Add badges for PyPI and Codecov ([`300d3ad`](https://github.com/istvankleijn/pitchmark/commit/300d3ad643208bf9f795fc1fb5e33bc69db1e96b))

## v0.2.0 (2023-02-27)
### Feature
* Trim course features to those in play ([`593e91d`](https://github.com/istvankleijn/pitchmark/commit/593e91d5d90e592226244c05cce64502a764e2d5))
* Chart holes in local projection ([`869c62d`](https://github.com/istvankleijn/pitchmark/commit/869c62d1690c7d5707d96c7a0d3f53aed9064e70))
* Chart courses using altair ([`ca58fc4`](https://github.com/istvankleijn/pitchmark/commit/ca58fc4e8a695a22bef629250d2a68bd3c053dec))
* **Course:** Add geodataframe representation ([`96a2790`](https://github.com/istvankleijn/pitchmark/commit/96a2790eddabdce55075967a1eb3b199b84f6250))

## v0.1.0 (2023-02-13)
### Feature
* Construct a golf course representation from an OpenStreetMap XML file ([`0093667`](https://github.com/istvankleijn/pitchmark/commit/009366709be89e3144506d12ebb8fcf2c46dbcf4))

## v0.0.1 (25/01/2023)

- First release of `pitchmark`!
