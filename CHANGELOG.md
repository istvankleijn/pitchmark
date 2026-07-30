# Changelog

<!--next-version-placeholder-->

## v0.5.0 (2026-07-30)

### Bug Fixes

- Bump stale transitive deps breaking Python 3.12 on Linux CI
  ([`84a623d`](https://github.com/istvankleijn/pitchmark/commit/84a623d1ea49b911a13232e6153eeb7ea8fb8f83))

### Build System

- Bump altair 4.2.2 -> 6.2.2
  ([`bf8f3bf`](https://github.com/istvankleijn/pitchmark/commit/bf8f3bf4700e84de21b0641acc202864ee706ea1))

- Bump laspy 2.4.1 -> 2.7.0
  ([`ce01445`](https://github.com/istvankleijn/pitchmark/commit/ce01445ab13f564e9a22cb06f6d1cc98a115d9e2))

- Bump myst-nb, sphinx-autoapi, sphinx-rtd-theme to current majors
  ([`6294bf2`](https://github.com/istvankleijn/pitchmark/commit/6294bf2719a4f992ccdfd4224bf10b56a9a12670))

- Bump open3d 0.16.0 -> 0.19.0
  ([`8ca3963`](https://github.com/istvankleijn/pitchmark/commit/8ca396321249966333b2237a551d5dd142de3b73))

- Bump osmium 3.6.0 -> 4.3.1
  ([`021070c`](https://github.com/istvankleijn/pitchmark/commit/021070c0d9ef39a9d385968999de0192ebe43761))

- Bump pandas, numpy, geopandas, and shapely
  ([`cd230cd`](https://github.com/istvankleijn/pitchmark/commit/cd230cd5582d012114d902b3beb2559fbba8c7ab))

- Bump pytest 7.3.1 -> 9.1.1, pytest-cov 4.0.0 -> 7.1.0
  ([`52248bb`](https://github.com/istvankleijn/pitchmark/commit/52248bba0f6c3f5c83d2a82c23df0488f9f0defd))

- Replace laszip backend with lazrs
  ([`8f7bc75`](https://github.com/istvankleijn/pitchmark/commit/8f7bc7523a86ebb2ee196e7a8c4d31d952e707a2))

### Chores

- Sync uv.lock for v0.4.2
  ([`cd2f4e2`](https://github.com/istvankleijn/pitchmark/commit/cd2f4e2f1f448802c046cf4bf16da750a8d5b9f6))

### Continuous Integration

- Run lint, format check, docs build, and coverage only on 3.12
  ([`88eaf19`](https://github.com/istvankleijn/pitchmark/commit/88eaf19da35e6d22bf6c1bc043ee2fdf22630605))

- Test against Python 3.10-3.12 in CI matrix
  ([`5d2ba8a`](https://github.com/istvankleijn/pitchmark/commit/5d2ba8a2513432ff0fd130aa665854a327ce4db3))

- Wire Codecov upload token and fail loudly on upload errors
  ([`1f6a166`](https://github.com/istvankleijn/pitchmark/commit/1f6a1669ebe7619c7bf3221e1a9360c1fe2bf3a8))

### Documentation

- Backfill missing v0.4.0/v0.4.1 changelog entries
  ([`9a43004`](https://github.com/istvankleijn/pitchmark/commit/9a43004f56230fa4170c22666dedafede516d78a))

- Fix Codecov badge branch reference
  ([`de07c0e`](https://github.com/istvankleijn/pitchmark/commit/de07c0e511b39a8c3ceab11b28b217abdec192e4))

- Update stale 2023 copyright year to 2023-2026
  ([`1bc0604`](https://github.com/istvankleijn/pitchmark/commit/1bc0604b795985fc8fb948453926ce3387d13bda))

### Features

- Support Python 3.12
  ([`b47798d`](https://github.com/istvankleijn/pitchmark/commit/b47798d70107407f2af227a3eec6186751eedba2))

### Refactoring

- Replace deprecated GeoSeries.unary_union with union_all()
  ([`8991d7e`](https://github.com/istvankleijn/pitchmark/commit/8991d7eff25cc45b04127cbd0b39299d49fb5728))

### Testing

- Cover clip_to_geoseries with synthetic LAS data
  ([`81c061b`](https://github.com/istvankleijn/pitchmark/commit/81c061b739136659bcf7c901e515c27a48a4360a))

- Cover GolfHandler.add_feature's unsupported geom_type guard
  ([`0ef8414`](https://github.com/istvankleijn/pitchmark/commit/0ef84146acb0006932e023d2067427956116ce26))

- Cover simplify_close_vertices, simplified_mesh, and gdf_from_mesh
  ([`2a85719`](https://github.com/istvankleijn/pitchmark/commit/2a85719a97f0caa76c0de70aa0d84ead037771f6))

- Update chart assertions for altair 6's schema changes
  ([`30c59d3`](https://github.com/istvankleijn/pitchmark/commit/30c59d3da424f7b14fb5847f2568e502c8d72404))

- Verify simplify_close_vertices distance threshold behavior
  ([`1195a91`](https://github.com/istvankleijn/pitchmark/commit/1195a9157deabd466a94424cd2aa461aba0f6c57))


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
