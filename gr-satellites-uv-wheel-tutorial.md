# Building `gr-satellites` from source with `uv` (modern workflow)

This write-up captures a practical path I validated on Ubuntu 24.04 (March 31, 2026) to build `gr-satellites` from source and produce a wheel using `uv` + standard Unix/C/C++ tooling.

> Scope note: `gr-satellites` is a GNU Radio out-of-tree (OOT) module with heavy C++ and system-library dependencies. `uv` is excellent for Python build orchestration, but it does **not** replace system package management for GNU Radio itself.

## What I tested

- Cloned upstream: `https://github.com/daniestevez/gr-satellites`
- Read upstream source-install docs: `https://gr-satellites.readthedocs.io/en/latest/installation.html`
- Installed system dependencies via `apt` (GNU Radio dev stack + required build libs).
- Confirmed a normal CMake/Ninja build works.
- Added a temporary `pyproject.toml` using `scikit-build-core` and successfully built:
  - `gr_satellites-5.10.0-cp312-cp312-linux_x86_64.whl`

## Why this is a “modernized” path

The official docs describe a classic:

```bash
cmake ..
make
sudo make install
```

Modernizing with `uv` gives you:

- reproducible Python-side build tool resolution,
- no global pip pollution,
- `uv build` as a one-command wheel build entrypoint.

The core C/C++ build still uses CMake/Ninja under the hood (as it should).

---

## 1) Install system prerequisites (Ubuntu/Debian)

`gr-satellites` requires GNU Radio and C/C++ dependencies from the OS.

```bash
sudo apt-get update
sudo apt-get install -y \
  git cmake ninja-build pkg-config \
  gnuradio-dev \
  liborc-0.4-dev \
  libsndfile1-dev \
  libspdlog-dev
```

If you are on non-Debian systems, install equivalent GNU Radio development packages and headers.

### Python ABI gotcha (important)

GNU Radio Python bindings are tied to a specific Python ABI. On Ubuntu 24.04 here, GNU Radio was installed for Python 3.12:

```bash
/usr/bin/python3.12 -c "import gnuradio; print(gnuradio.__file__)"
```

If your `uv` environment uses a different Python than GNU Radio, build/import failures are likely.

---

## 2) Clone `gr-satellites`

```bash
git clone https://github.com/daniestevez/gr-satellites.git
cd gr-satellites
```

Optional (tests/sample data):

```bash
git submodule update --init
```

---

## 3) Sanity-check native build first (recommended)

Before wheel work, verify your toolchain:

```bash
cmake -S . -B build -GNinja
cmake --build build
```

If this fails, fix native/system deps first.

---

## 4) Add a minimal wheel backend (`scikit-build-core`)

`gr-satellites` does not currently ship a `pyproject.toml` wheel config upstream, so create one locally:

```toml
# pyproject.toml
[build-system]
requires = ["scikit-build-core>=0.10"]
build-backend = "scikit_build_core.build"

[project]
name = "gr-satellites"
version = "5.10.0"
description = "GNU Radio satellites OOT module"
requires-python = ">=3.12"

[tool.scikit-build]
cmake.source-dir = "."
wheel.packages = ["python/satellites"]
```

Notes:
- `wheel.packages = ["python/satellites"]` ensures Python package inclusion.
- CMake install rules also place binaries, shared libs, headers, GRC blocks, etc. into the wheel staging area.

---

## 5) Build wheel with `uv`

```bash
uv build --wheel -o dist
```

Expected output includes something like:

```text
Successfully built dist/gr_satellites-5.10.0-cp312-cp312-linux_x86_64.whl
```

This was successful in my run.

---

## 6) Inspect and test the wheel

List contents:

```bash
unzip -l dist/gr_satellites-5.10.0-cp312-cp312-linux_x86_64.whl | head
```

You should see entries like:
- `bin/gr_satellites`
- `lib/libgnuradio-satellites...`
- Python package files under `satellites/...`
- GRC block YAML files under `share/gnuradio/grc/blocks/...`

Install/test in a compatible Python (matching GNU Radio ABI):

```bash
uv venv --python /usr/bin/python3.12 .venv
source .venv/bin/activate
uv pip install dist/gr_satellites-5.10.0-cp312-cp312-linux_x86_64.whl
python -c "import satellites; print('ok', satellites.__file__)"
```

---

## Findings and caveats

1. **System dependencies are still the hard requirement.**
   `uv` modernizes Python/build orchestration, not GNU Radio C++ dependency provisioning.

2. **Python version alignment is critical.**
   Build against the same Python ABI used by GNU Radio packages.

3. **This works today as a local packaging overlay.**
   Upstream currently documents CMake install flow; this wheel approach is a practical extension.

4. **Current output is a platform wheel, not manylinux.**
   This is expected due to native GNU Radio linkage. Distributing broadly would require a stricter packaging strategy.

5. **You may see CMake policy warnings (CMP0148) and syntax warnings from helper scripts.**
   These did not block the build in my test.

---

## Suggested upstream-friendly next step

If you want this workflow to be permanent and CI-friendly, open a PR to `gr-satellites` adding:

- official `pyproject.toml` with `scikit-build-core`,
- documented wheel build section (`uv build --wheel`),
- CI job that builds and smoke-tests Linux wheels against supported GNU Radio/Python combinations.

That would turn this from an experimental local recipe into a repeatable upstream-supported build path.
