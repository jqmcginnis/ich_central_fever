#!/usr/bin/env python3
import argparse
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from nibabel.affines import apply_affine

def load_nifti(filepath):
    """Load a NIfTI file and return the image data."""
    img = nib.load(filepath)
    return img.get_fdata()

def extract_slice(data, orientation, slice_index):
    """
    Extract a 2D slice from a 3D volume based on the orientation.
    Orientation choices:
      - sagittal: slice along the first dimension (x-axis)
      - coronal: slice along the second dimension (y-axis)
      - axial: slice along the third dimension (z-axis)
    """
    if orientation == 'sagittal':
        slice_data = data[slice_index, :, :]
    elif orientation == 'coronal':
        slice_data = data[:, slice_index, :]
    elif orientation == 'axial':
        slice_data = data[:, :, slice_index]
    else:
        raise ValueError("Orientation must be 'sagittal', 'coronal', or 'axial'.")
    return slice_data

def plot_slice(ax, template_slice, mask_slice, orientation, slice_index, affine):
    """
    Plot a single slice in the provided axis.
    The template is plotted in grayscale, and only non-zero mask voxels are overlaid in red.
    """
    # Display the template slice in grayscale.,
    ax.imshow(np.rot90(template_slice), cmap='gray')
    
    # Mask zero voxels in mask_slice, so only non-zero values appear.
    masked_overlay = np.ma.masked_where(mask_slice == 0, mask_slice)
    
    # Create a binary colormap so that any non-masked voxel appears red.
    red_cmap = colors.ListedColormap(['red'])
    
    # Overlay the mask slice (using no interpolation to preserve pixel boundaries)
    ax.imshow(np.rot90(masked_overlay), cmap=red_cmap, interpolation='none')
    
    if orientation == "axial":
        coords = apply_affine(affine, [0, 0, slice_index])
        ax.set_title(f'z =  {int(coords[2],)}', fontsize=12)
    elif orientation == "sagittal":
        coords = apply_affine(affine, [slice_index, 0, 0])
        ax.set_title(f'x =  {int(coords[0])}', fontsize=12)
    else:
        coords = apply_affine(affine, [0, slice_index, 0])
        ax.set_title(f'y =  {int(coords[1])}', fontsize=12)

    print(affine)
    print(coords)
    ax.axis('off')

def main():
    parser = argparse.ArgumentParser(
        description="Generate a single figure with multiple axial and sagittal slices overlaid with a mask."
    )
    parser.add_argument('--template', required=True, help="Path to the MNI template NIfTI file.")
    parser.add_argument('--mask', required=True, help="Path to the mask NIfTI file.")
    parser.add_argument('--output', default="VLSM.png", help="Output filename for the snapshot.")
    args = parser.parse_args()

    # Load template and mask data.
    template_data = load_nifti(args.template)
    mask_data = load_nifti(args.mask)
    affine = nib.load(args.template).affine

    # Define slice indices for each orientation.
    axial_indices = [62, 63, 67, 68]
    sagittal_indices = [93, 94, 95, 96]

    # Create a figure with 2 rows and 4 columns.
    fig, axes = plt.subplots(2, 4, figsize=(12, 8))
    
    # Plot axial slices in the first row.
    for idx, slice_index in enumerate(axial_indices):
        template_slice = extract_slice(template_data, 'axial', slice_index)
        mask_slice = extract_slice(mask_data, 'axial', slice_index)
        plot_slice(axes[0, idx], template_slice, mask_slice, 'axial', slice_index, affine)

    # Plot sagittal slices in the second row.
    for idx, slice_index in enumerate(sagittal_indices):
        template_slice = extract_slice(template_data, 'sagittal', slice_index)
        mask_slice = extract_slice(mask_data, 'sagittal', slice_index)
        plot_slice(axes[1, idx], template_slice, mask_slice, 'sagittal', slice_index, affine)

    # Set a global title for the figure.
    fig.suptitle("Results of VLSM Analysis", fontsize=16)
    plt.tight_layout()
    plt.savefig(args.output, dpi=300)
    plt.close()
    print(f"Combined snapshot saved to: {args.output}")

if __name__ == '__main__':
    main()
