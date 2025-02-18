#!/usr/bin/env python3
import os
import argparse
import nibabel as nib
import numpy as np
import csv

def compute_lesion_volume(filepath):
    """
    Load a NIfTI mask file and compute the lesion volume.
    
    The function counts nonzero voxels in the mask and multiplies by the voxel volume.
    """
    img = nib.load(filepath)
    data = img.get_fdata()
    # Count nonzero voxels (assuming mask is binary or thresholded)
    num_voxels = np.count_nonzero(data)
    # Get voxel dimensions (first three elements)
    voxel_dims = img.header.get_zooms()[:3]
    voxel_volume = np.prod(voxel_dims)
    # Return lesion volume in the same unit as voxel_dims cubed (usually mm^3)
    return num_voxels * voxel_volume

def main():
    parser = argparse.ArgumentParser(
        description="Calculate lesion volumes for non-warped and warped mask volumes."
    )
    parser.add_argument(
        "--directory",
        type=str,
        required=True,
        help="Directory containing NIfTI mask files (.nii.gz)."
    )
    args = parser.parse_args()

    # Get list of .nii.gz files in the directory
    files = [f for f in os.listdir(args.directory) if f.endswith('.nii.gz')]
    
    # Group files by base name: remove '_warped' if present to create a common key.
    groups = {}
    for f in files:
        if "_warped.nii.gz" in f:
            base = f.replace("_warped.nii.gz", "")
            groups.setdefault(base, {})["warped"] = f
        else:
            base = f.replace(".nii.gz", "")
            groups.setdefault(base, {})["non_warped"] = f

    # Prepare to store results for each case
    results = []
    for base, pair in groups.items():
        row = {"case": base}
        
        # Process non-warped mask if available
        if "non_warped" in pair:
            non_warped_path = os.path.join(args.directory, pair["non_warped"])
            try:
                vol_non = compute_lesion_volume(non_warped_path)
            except Exception as e:
                print(f"Error processing {pair['non_warped']}: {e}")
                vol_non = None
            row["non_warped_volume"] = vol_non
        else:
            row["non_warped_volume"] = None
        
        # Process warped mask if available
        if "warped" in pair:
            warped_path = os.path.join(args.directory, pair["warped"])
            try:
                vol_warped = compute_lesion_volume(warped_path)
            except Exception as e:
                print(f"Error processing {pair['warped']}: {e}")
                vol_warped = None
            row["warped_volume"] = vol_warped
        else:
            row["warped_volume"] = None
        
        # Compute the difference between warped and non-warped volumes
        if row["non_warped_volume"] is not None and row["warped_volume"] is not None:
            vol_diff = row["warped_volume"] - row["non_warped_volume"]
            row["volume_difference"] = vol_diff
            # Calculate percentage difference if non_warped_volume is not zero
            if row["non_warped_volume"] != 0:
                row["percentage_difference"] = (vol_diff / row["non_warped_volume"]) * 100
            else:
                row["percentage_difference"] = None
        else:
            row["volume_difference"] = None
            row["percentage_difference"] = None

        results.append(row)

    # Save results to a CSV file in the specified directory.
    output_csv = os.path.join(args.directory, "lesion_volumes.csv")
    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = [
            "case", 
            "non_warped_volume", 
            "warped_volume", 
            "volume_difference", 
            "percentage_difference"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"Results saved to {output_csv}")

if __name__ == "__main__":
    main()
