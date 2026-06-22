use numpy::PyReadonlyArray4;
use pyo3::prelude::*;

/// Compute slice-based temporal SNR with BOLDQC-style masking.
///
/// For each call, a fresh mask is computed from the temporal mean image
/// (voxels with mean <= threshold are excluded). Then for each slice:
///   1. Compute the spatial mean of unmasked voxels at each time point
///   2. SNR of that time series = mean / stdev (ddof=1)
///
/// The final result is a weighted average across slices:
///   sum(slice_snr * slice_voxel_count) / total_voxel_count
///
/// Args:
///     data: 4D numpy array with shape (x, y, z, t) and dtype float64
///     mask_threshold: intensity threshold; voxels with temporal mean <= this are masked
///
/// Returns:
///     SNR scalar (f64), or NaN if fewer than 2 time points or all voxels masked
#[pyfunction]
fn compute_snr<'py>(
    py: Python<'py>,
    data: PyReadonlyArray4<'py, f64>,
    mask_threshold: f64,
) -> PyResult<f64> {
    let array = data.as_array();
    let shape = array.shape();
    let (dim_x, dim_y, dim_z, dim_t) = (shape[0], shape[1], shape[2], shape[3]);

    if dim_t < 2 {
        return Ok(f64::NAN);
    }

    let result = py.detach(|| {
        let mut total_weighted_snr: f64 = 0.0;
        let mut total_voxel_count: u64 = 0;

        for z in 0..dim_z {
            // First pass: compute temporal mean per voxel to build the mask,
            // and count unmasked voxels in this slice
            let mut mask = vec![false; dim_x * dim_y];
            let mut slice_voxel_count: u64 = 0;

            for x in 0..dim_x {
                for y in 0..dim_y {
                    let mut sum = 0.0_f64;
                    for t in 0..dim_t {
                        sum += array[[x, y, z, t]];
                    }
                    let voxel_mean = sum / dim_t as f64;

                    if voxel_mean <= mask_threshold
                        || voxel_mean.is_nan()
                        || voxel_mean.is_infinite()
                    {
                        mask[x * dim_y + y] = true;
                    } else {
                        slice_voxel_count += 1;
                    }
                }
            }

            if slice_voxel_count == 0 {
                continue;
            }

            // Second pass: for each time point, compute the spatial mean
            // of unmasked voxels in this slice
            let mut spatial_means = vec![0.0_f64; dim_t];

            for t in 0..dim_t {
                let mut sum = 0.0_f64;
                for x in 0..dim_x {
                    for y in 0..dim_y {
                        if !mask[x * dim_y + y] {
                            sum += array[[x, y, z, t]];
                        }
                    }
                }
                spatial_means[t] = sum / slice_voxel_count as f64;
            }

            // Compute SNR of the spatial-means time series: mean / stdev(ddof=1)
            let series_mean: f64 =
                spatial_means.iter().sum::<f64>() / dim_t as f64;

            let sq_diff_sum: f64 = spatial_means
                .iter()
                .map(|&v| {
                    let diff = v - series_mean;
                    diff * diff
                })
                .sum();
            let series_stdev = (sq_diff_sum / (dim_t - 1) as f64).sqrt();

            let slice_snr = if series_stdev == 0.0
                || series_stdev.is_nan()
                || series_stdev.is_infinite()
            {
                0.0
            } else {
                let snr = series_mean / series_stdev;
                if snr.is_nan() || snr.is_infinite() {
                    0.0
                } else {
                    snr
                }
            };

            total_weighted_snr += slice_snr * slice_voxel_count as f64;
            total_voxel_count += slice_voxel_count;
        }

        if total_voxel_count == 0 {
            f64::NAN
        } else {
            total_weighted_snr / total_voxel_count as f64
        }
    });

    Ok(result)
}

#[pymodule]
fn scanbuddy_snr(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_snr, m)?)?;
    Ok(())
}
