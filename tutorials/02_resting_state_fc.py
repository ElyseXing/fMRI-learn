"""Extract ROI signals and compute a single-subject resting-state FC matrix."""

from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from nilearn import datasets, image, plotting
from nilearn.maskers import NiftiLabelsMasker


HIGH_PASS = 0.01
LOW_PASS = 0.1
CONFOUND_CANDIDATES = {
    "x", "y", "z", "transx", "transy", "transz",
    "motionx", "motiony", "motionz",
    "rotx", "roty", "rotz", "rotationx", "rotationy", "rotationz",
    "motionpitch", "motionroll", "motionyaw", "whitematter", "wm", "csf",
}
OUTPUT_DIR = Path("outputs")


def normalize_column_name(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def main():
    dataset = datasets.fetch_adhd(n_subjects=1)
    func_file = dataset.func[0]
    confounds_file = dataset.confounds[0]
    func_img = image.load_img(func_file)

    tr = float(func_img.header.get_zooms()[3])
    nyquist = 1 / (2 * tr)
    if not (0 < HIGH_PASS < LOW_PASS < nyquist):
        raise ValueError(
            f"Require 0 < high-pass < low-pass < Nyquist ({nyquist:.4f} Hz); "
            f"got {HIGH_PASS} and {LOW_PASS} Hz. Check the header TR ({tr} s)."
        )

    confounds = pd.read_csv(confounds_file, sep=None, engine="python")
    selected_columns = [
        column
        for column in confounds.columns
        if normalize_column_name(column) in CONFOUND_CANDIDATES
    ]
    if not selected_columns:
        raise ValueError(
            "No familiar motion/WM/CSF confounds were found. "
            f"Available columns: {list(confounds.columns)}"
        )
    confounds = confounds[selected_columns].fillna(0)

    atlas = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-2mm")
    masker = NiftiLabelsMasker(
        labels_img=atlas.maps,
        standardize="zscore_sample",
        standardize_confounds=True,
        detrend=True,
        low_pass=LOW_PASS,
        high_pass=HIGH_PASS,
        t_r=tr,
        verbose=1,
    )
    signals = masker.fit_transform(func_img, confounds=confounds)
    connectivity = np.corrcoef(signals, rowvar=False)

    roi_names = [str(label) for label in atlas.labels[1:]]
    if len(roi_names) != connectivity.shape[0]:
        roi_names = [f"ROI_{index + 1:02d}" for index in range(connectivity.shape[0])]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix = pd.DataFrame(connectivity, index=roi_names, columns=roi_names)
    matrix.to_csv(OUTPUT_DIR / "connectivity_matrix.csv")

    fig, ax = plt.subplots(figsize=(11, 9), constrained_layout=True)
    display = plotting.plot_matrix(
        connectivity,
        labels=roi_names,
        axes=ax,
        vmin=-1,
        vmax=1,
        colorbar=True,
        title="Resting-state ROI connectivity (Pearson r)",
    )
    display.figure.savefig(OUTPUT_DIR / "connectivity_matrix.png", dpi=160)
    plt.close(display.figure)

    print(f"Functional image: {func_file}")
    print(f"TR: {tr:g} s; time points: {signals.shape[0]}; ROIs: {signals.shape[1]}")
    print(f"Confounds used: {selected_columns}")
    print(f"Temporal filter: {HIGH_PASS:g}–{LOW_PASS:g} Hz")
    print(f"Saved matrix and plot in {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()