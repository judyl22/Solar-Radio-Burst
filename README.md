# Solar Radio Burst Analysis

Research notebooks and Python utilities for exploring solar radio bursts in Parker Solar Probe (PSP) and STEREO observations, detecting burst tracks in dynamic spectra, and comparing radio frequency changes with MAVEN particle energy changes.

The repository contains several experimental approaches, including logarithmic frequency interpolation, thresholding, probabilistic Hough line detection, gradient-based track extraction, and curvature analysis. It is organized as a notebook-based research workspace; individual notebooks contain event-specific dates and parameters.

## Repository guide

| Path | Contents |
| --- | --- |
| `detection_helper.py` | PSP FIELDS/RFS loading, frequency interpolation, binary maps, Hough detection, line grouping, and plotting utilities. |
| `helper.py` | Shared utilities, including UTC/Unix time conversion and array operations. |
| `detection_*.ipynb`, `dection_*.ipynb`, `dectection_*.ipynb` | Detection experiments and alternative preprocessing and extraction methods. Filenames retain their original spelling. |
| `dection_prog_new_extract4.ipynb` | Burst extraction experiments using shared helpers and curvature/ACBone routines. |
| `dection_prog_new_extract5_new_curvature.ipynb` | Further gradient, transition-point, grouping, and burst-track extraction experiments. |
| `PJCurvature_demo.ipynb` | Curvature demonstration. |
| `plotting notebooks/` | PSP and STEREO plotting examples and event inspection. |
| `calculation notebooks/` | Drift-rate calculations and event/geometry investigations. |
| `compare_maven/` | PSP/STEREO/MAVEN event tables, comparison scripts, fitting utilities, notebooks, and saved figures. |
| `recordings/` | Event notes and candidate tables in CSV and Apple Numbers formats. |
| `comp_stereo_psp.ipynb` | PSP/STEREO comparison notebook. |
| `freq_change_vs_energy_change.ipynb` | Frequency-change and energy-change exploration. |

## Setup

Create a Python environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab numpy scipy matplotlib pandas python-dateutil pyspedas pytplot-mpl-temp scikit-image scikit-learn adjustText cdflib
jupyter lab
```

These packages cover the shared helpers and main comparison scripts. `pytplot-mpl-temp` provides the `pytplot` import used by the code. There is currently no pinned dependency manifest; some older notebook cells may require dependency or API adjustments.

Open root-level detection notebooks with the repository root as their working directory so that `helper` and `detection_helper` can be imported. For notebooks in subdirectories, check their imports and relative data paths before running cells.

## Detecting bursts in PSP data

Start with `dection_prog_new_extract4.ipynb` for extraction experiments, or `dection_prog_new_extract5_new_curvature.ipynb` for gradient and transition-point methods. Review the selected date range and execute the required cells in order.

The shared preprocessing workflow can also be run in a notebook cell from the repository root:

```python
import matplotlib.pyplot as plt
from detection_helper import (
    return_arr,
    convert_data_log,
    bmap_row_mean_loop_new,
    plot_bmap,
)

# Load PSP Level 3 low- and high-frequency RFS observations.
times, frequencies, power = return_arr("2023-08-19", "2023-08-20")

# Interpolate onto a logarithmically spaced frequency grid.
freq_log, freq_log_exp, power_log = convert_data_log(frequencies, power)

# Threshold each frequency channel and retain sustained enhancements.
binary_map = bmap_row_mean_loop_new(
    times_arr=times,
    full_data=power_log,
    ratio=0.95,
    min_duration=1,  # seconds
)

plot_bmap(times, freq_log_exp, binary_map)
plt.show()
```

`return_arr` loads PSP FIELDS/RFS Level 3 `rfs_lfr` and `rfs_hfr` data through PySPEDAS, using the `V1V2` channel. The returned power array is indexed as `[time, frequency]`; frequencies are in Hz, and `freq_log_exp` contains base-10 logarithms of frequency. Time conversion helpers use Unix seconds and UTC datetimes.

The first load requires network access unless the requested observations are already cached. `return_arr` currently sets `no_update=False` internally. The local `psp_data/` directory is excluded from Git.

For line extraction, explore `all_lines_day` and the notebook-specific gradient routines after constructing the binary map. Thresholds, minimum durations, slices, and grouping tolerances are experiment settings and should be reviewed for each event.

## Comparing PSP, STEREO, and MAVEN events

The comparison workflow uses the tables supplied in `compare_maven/`:

- `stereo_maven_psp_both.csv`: paired STEREO and PSP event columns.
- `maven_descending_full_clean.csv`: MAVEN event times and energy endpoints.
- `radio_burst_analysis.py`: duration, frequency-change, drift-rate, energy-change, date-matching, and fitting functions.
- `run_script.ipynb` and `script.py`: analysis entry points.

Run the script with `compare_maven/` as the working directory:

```bash
cd compare_maven
python script.py
```

The script computes event quantities, merges observations by calendar date, and displays scatter plots and power-law/cubic fits. It writes or overwrites `stereo_added.csv`, `psp_added.csv`, `maven_added.csv`, and `merged.csv` in that directory. It also opens interactive plots and pauses for Enter at several stages.

Radio event tables use `Start time`, `End time`, `High frequency (Hz)`, and `Low frequency (Hz)`. MAVEN tables use `Start Time (UTC)`, `End Time (UTC)`, `Start Energy (keV)`, and `End Energy (keV)`. The radio drift-rate calculation is `(high frequency - low frequency) / duration`, reported in Hz/s.

The script includes hard-coded row exclusions for the supplied dataset. Review these before substituting another event table. Matching by date can produce multiple combinations of events on the same day; inspect the merged results when interpreting comparisons.

## Working with the notebooks

- Check date ranges, local file paths, and manually selected event windows before running a notebook.
- Some cells use interactive plotting backends such as `%matplotlib tk`; select a backend supported by your environment.
- Notebook outputs and saved figures record experiments and may reflect earlier parameter choices. Rerun the relevant cells to reproduce a result with your settings.
- Downloaded spacecraft observations are separate from the included event tables and figures.

## References and acknowledgments

We acknowledge Peijin Zhang's [type3detect](https://github.com/peijin94/type3detect) project for its methods and code for automatic Type III radio burst detection using the Hough transform and active-contour backbone extraction (ACBone).

The upstream repository requests citation of the following paper when using its ideas or code:

Zhang, P. J., Wang, C. B., & Ye, L. (2018). [A type III radio burst automatic analysis system and statistic results for a half solar cycle with Nançay Decameter Array data](https://doi.org/10.1051/0004-6361/201833260). *Astronomy & Astrophysics*, **618**, A165.

```bibtex
@article{zhang2018type,
  author = {Zhang, P. J. and Wang, C. B. and Ye, L.},
  title = {A type III radio burst automatic analysis system and statistic results for a half solar cycle with Nan{\c{c}}ay Decameter Array data},
  journal = {Astronomy & Astrophysics},
  volume = {618},
  pages = {A165},
  year = {2018},
  doi = {10.1051/0004-6361/201833260}
}
```
