# scanbuddy_snr — Rust SNR Extension for Scanbuddy

## Overview

`scanbuddy_snr` is a Python extension module written in Rust (via PyO3 + maturin) that provides a high-performance SNR calculation for Scanbuddy's real-time fMRI monitoring pipeline. It replaces the pure-Python SNR computation with compiled Rust code while maintaining identical numerical results.

The module is **optional** — Scanbuddy will use it if available, and gracefully fall back to the original Python implementation if the Rust module cannot be imported.

## Background

### The Problem

Scanbuddy monitors fMRI scans in real time, computing signal-to-noise ratio (SNR) as volumes arrive from the scanner. The existing Python implementation works but involves nested loops over slices and volumes with numpy masked arrays, which becomes slow for large 4D datasets.

### Approach: BOLDQC-Style Masking + Scanbuddy Metric

The companion project BOLDQC computes a fresh intensity-based mask from the temporal mean image on every run, which is more robust than Scanbuddy's incremental mask-diffing approach. This module adopts that masking strategy (recompute from scratch every time) while preserving Scanbuddy's actual SNR metric.

**Why not use BOLDQC's per-voxel SNR directly?** BOLDQC computes per-voxel `temporal_mean / temporal_stdev`, which works well on motion-corrected data. But Scanbuddy operates on raw (un-corrected) volumes, where individual voxels have high temporal variance from motion. Scanbuddy's metric — spatially averaging voxels within a slice first, then computing the SNR of that time series — cancels out per-voxel noise through spatial averaging and produces values consistent with what operators expect (~100-150 for typical scans).

## Algorithm

The `compute_snr` function:

1. **Input**: 4D numpy array `(x, y, z, t)` of float64 values, plus a mask threshold
2. **For each slice z**:
   - **Build mask**: Compute the temporal mean for each voxel. Exclude voxels where the mean is <= threshold, NaN, or infinite
   - **Spatial means time series**: For each time point t, compute the mean intensity of all unmasked voxels in that slice
   - **Slice SNR**: `mean(spatial_means) / stdev(spatial_means, ddof=1)`
3. **Weighted average**: `sum(slice_snr * slice_voxel_count) / total_voxel_count`
4. **Edge cases**: Returns NaN if fewer than 2 time points or if all voxels are masked

## Project Structure

```
scanbuddy_snr/
├── Cargo.toml              # Rust dependencies (pyo3, numpy, ndarray)
├── pyproject.toml           # Maturin build configuration
├── build_in_container.sh    # Script to build for the Docker environment
├── src/
│   └── lib.rs              # The Rust implementation
└── target/
    └── wheels/
        ├── *.whl                       # Built wheel files
        └── extracted_313t/
            └── scanbuddy_snr/          # Extracted .so + __init__.py for volume mounting
                ├── __init__.py
                └── scanbuddy_snr.cpython-313t-aarch64-linux-gnu.so
```

## Integration with Scanbuddy

### Python Side (`scanbuddy/proc/snr.py`)

The SNR class conditionally imports the Rust function:

```python
try:
    from scanbuddy_snr import compute_snr as _rust_compute_snr
    _USE_RUST_SNR = True
except (ImportError, AttributeError):
    _USE_RUST_SNR = False
```

The `calc_snr` method dispatches accordingly:

```python
def calc_snr(self, key):
    if _USE_RUST_SNR:
        data = self._fdata_array[:, :, :, :key - 4]
        return _rust_compute_snr(data, self._mask_threshold)
    else:
        return self._calc_snr_python(key)
```

The original Python implementation is preserved as `_calc_snr_python` and all its helper methods (`generate_mask`, `get_mean_slice_intensities`, `find_mask_differences`) remain intact for the fallback path.

### Docker Deployment

Scanbuddy runs in a Docker container based on RockyLinux 8 with free-threaded Python 3.13t (GIL disabled). The Rust extension is volume-mounted into the container's site-packages in `docker-compose-devel.yaml`:

```yaml
volumes:
  - ../../scanbuddy_snr/target/wheels/extracted_313t/scanbuddy_snr:/sw/miniforge/envs/python3.13t/lib/python3.13t/site-packages/scanbuddy_snr
```

### Mask Threshold

The mask threshold is determined from DICOM metadata (bits stored + receive coil) by the existing Python code and passed to the Rust function as a parameter:

| Bits Stored | Receive Coil         | Threshold |
|-------------|----------------------|-----------|
| 12          | Any                  | 150.0     |
| 16          | Head_32              | 1500.0    |
| 16          | Head_64, HeadNeck_64 | 3000.0    |

### When SNR Is Computed

The existing orchestration is unchanged:
- First 5 volumes are skipped (not included in SNR)
- SNR calculation triggers every 4 volumes starting at volume 54 (`key > 53 and key % 4 == 0`)
- If the result is NaN, the mask threshold is decremented and the next call retries
- Results are published via PyPubSub to the `plot_snr` topic for the Dash web UI

## Building

### Prerequisites

- Rust toolchain (`rustup`)
- `maturin` (`pip install maturin`)
- `numpy` in the target Python environment

### Local Development (macOS)

```bash
cd scanbuddy_snr
maturin develop --release
```

This builds and installs the extension into your active Python environment.

### For the Docker Container (RockyLinux 8 / linux/arm64 / Python 3.13t)

The `.so` must be built on a matching platform (glibc 2.28, aarch64, free-threaded CPython 3.13t). Use the provided build script inside a RockyLinux 8 container:

```bash
cd scanbuddy_snr
docker run --rm -v $(pwd):/src -w /src rockylinux:8 bash /src/build_in_container.sh
```

Then extract the wheel:

```bash
rm -rf target/wheels/extracted_313t
unzip -o target/wheels/scanbuddy_snr-*-cp313t-*manylinux_2_28*.whl \
  -d target/wheels/extracted_313t/
```

Restart the Scanbuddy container — it picks up the new `.so` from the volume mount.

### Build Constraints

| Constraint | Reason |
|-----------|--------|
| Must target glibc 2.28 | RockyLinux 8 base image |
| Must target `cp313t` ABI | Free-threaded Python 3.13 (GIL disabled) |
| Must target `aarch64` | ARM-based Docker host |
| Requires PyO3 >= 0.24 | Free-threaded Python support added in 0.23; numpy crate compat requires 0.24 |

## Performance

The Rust implementation releases the Python GIL during computation (`py.allow_threads`), allowing other threads to run concurrently — important since SNR calculation happens on a separate thread from the Dash UI.

Benchmarks on a typical fMRI volume (96x96x72 voxels, 50 time points, ~253 MB):

| Implementation | Time |
|---------------|------|
| Rust          | ~140ms |
| Python        | several seconds |

## Key Design Decisions

1. **Optional dependency**: The `try/except` import pattern means Scanbuddy works identically without the Rust module installed. This avoids breaking existing deployments.

2. **Spatial-mean metric, not per-voxel**: The Rust code computes the same metric as the Python Scanbuddy (spatial average per slice, then temporal SNR of that series), not the per-voxel temporal SNR that BOLDQC uses. On raw un-corrected fMRI data, per-voxel temporal SNR is ~30 while the spatial-mean approach yields ~130 — the latter is what operators are calibrated to.

3. **Fresh mask every call**: Unlike the Python implementation which tracks mask differences between calls and only recomputes affected slices, the Rust version recomputes the entire mask from scratch each time. This is simpler and correct — and fast enough in Rust that the optimization isn't needed.

4. **Volume-mount deployment**: Rather than rebuilding the entire Docker image to include the Rust toolchain, the pre-built `.so` is volume-mounted in. This allows rapid iteration during development.

## Dependencies

### Rust (Cargo.toml)

| Crate    | Version | Purpose |
|----------|---------|---------|
| `pyo3`   | 0.24    | Python extension bindings |
| `numpy`  | 0.24    | Zero-copy numpy array access |
| `ndarray`| 0.16    | N-dimensional array types |

### Python

No additional Python dependencies — the module is self-contained and only requires numpy (already a Scanbuddy dependency).
