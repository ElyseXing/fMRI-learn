"""Download and inspect one preprocessed ADHD resting-state scan."""

from nilearn import datasets, image


def main():
    dataset = datasets.fetch_adhd(n_subjects=1)
    func_file = dataset.func[0]
    func_img = image.load_img(func_file)

    shape = func_img.shape
    zooms = func_img.header.get_zooms()
    time_unit = func_img.header.get_xyzt_units()[1]

    print(f"Functional image: {func_file}")
    print(f"Dimensions (x, y, z, time): {shape}")
    print(f"Voxel sizes and TR: {zooms}")
    print(f"Spatial unit: {func_img.header.get_xyzt_units()[0]}")
    print(f"Time unit: {time_unit}")
    print(f"Affine to world coordinates:\n{func_img.affine}")

    if len(shape) != 4:
        raise ValueError(f"Expected a 4D functional image, got shape {shape}")

    print("\nThis sample is already spatially preprocessed; do not normalize it again.")


if __name__ == "__main__":
    main()