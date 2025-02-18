#!/usr/bin/env python

import os
import subprocess
import shlex
import glob
import argparse

def flirt_reg(moving, fixed, mat_file, out_file, n_threads=8, dof=6):
    """
    Perform registration using FSL's FLIRT.
    
    Parameters:
        moving (str): Path to the moving image.
        fixed (str): Path to the fixed image.
        mat_file (str): Path to save the transformation matrix.
        out_file (str): Path to save the registered (warped) moving image.
        n_threads (int): Number of threads (FLIRT generally ignores this, but kept for consistency).
        dof (int): Degrees of freedom for registration (e.g. 3 for translation-only, 6 for rigid-body).
    """
    # Compute the transformation matrix.
    reg_cmd = f"flirt -in {moving} -ref {fixed} -omat {mat_file} -dof {dof}"
    print("Running FLIRT registration command:")
    print(reg_cmd)
    subprocess.run(shlex.split(reg_cmd), check=True)
    
    # Apply the transformation to obtain the registered moving template.
    apply_cmd = f"flirt -in {moving} -ref {fixed} -applyxfm -init {mat_file} -out {out_file}"
    print("Applying transformation to moving template:")
    print(apply_cmd)
    subprocess.run(shlex.split(apply_cmd), check=True)

def apply_warp_mask(fixed, mat_file, mask, out_mask):
    """
    Warp a mask image into the fixed template space using FLIRT with nearest neighbour interpolation.
    
    Parameters:
        fixed (str): Path to the fixed image (reference space).
        mat_file (str): Transformation matrix file.
        mask (str): Path to the mask (in moving space).
        out_mask (str): Path for the output warped mask.
    """
    # Use nearest neighbour interpolation for label images.
    cmd = f"flirt -in {mask} -ref {fixed} -applyxfm -init {mat_file} -out {out_mask} -interp nearestneighbour"
    print("Warping mask with command:")
    print(cmd)
    subprocess.run(shlex.split(cmd), check=True)

def main():
    parser = argparse.ArgumentParser(
        description="Co-register a moving template to a fixed template using FLIRT and warp lesion masks to the fixed space."
    )
    parser.add_argument(
        "--moving_template", default="CT_template_1mm.nii.gz",
        help="Path to the moving template (e.g. CT_template_1mm_not_registered.nii.gz)"
    )
    parser.add_argument(
        "--fixed_template1", default="MNI152_T1_1mm.nii.gz",
        help="Path to the fixed template (e.g. MNI152_T1_1mm.nii.gz)"
    )
    parser.add_argument(
        "--fixed_template2", default="MNI152b_05mm.nii.gz",
        help="Path to the fixed template (e.g. MNI152_T1_1mm.nii.gz)"
    )
    parser.add_argument(
        "--lesions", required=True,
        help="Path to the folder containing lesion mask files (*.nii.gz) to warp."
    )
    parser.add_argument(
        "--binary_mask", default="threshZresults_testcentral_fever_binarized.nii.gz",
        help="(Optional) Path to a binary mask (e.g. threshZresults_testcentral_fever_binarized.nii.gz) corresponding to the moving template to warp."
    )
    parser.add_argument(
        "--threads", type=int, default=1,
        help="Number of threads to use (default: 1; FLIRT typically ignores this)"
    )

    args = parser.parse_args()

    moving_template = args.moving_template
    fixed_template1 = args.fixed_template1
    fixed_template2 = args.fixed_template2

    lesions_folder = args.lesions
    dof = 6
    n_threads = args.threads

    # Define filenames for the transformation matrix and the registered template.
    mat_file1 = "template_to_mni_affine_template1.mat"
    registered_template1 = moving_template.replace(".nii.gz", "_space-MNI152T1w1mm.nii.gz")

    mat_file2 = "template_to_mni_affine_template2.mat"
    registered_template2 = moving_template.replace(".nii.gz", "_space-MNI152bT1w0x5mm.nii.gz")

    print("==========================================")
    print("Step 1a: Registering moving template to fixed template using FLIRT")
    print("==========================================")
    print(f"Moving Template: {moving_template}")
    print(f"Fixed Template:  {fixed_template1}")
    print(f"Degrees of Freedom: {dof}")
    flirt_reg(moving_template, fixed_template1, mat_file1, registered_template1, n_threads, dof)
    print("Template registration completed.\n")

    # Process all lesion masks in the specified folder.
    print("==========================================")
    print("Step 2a: Warping lesion masks to fixed template1 space using FLIRT")
    print("==========================================")
    mask_files = glob.glob(os.path.join(lesions_folder, "*.nii.gz"))
    if not mask_files:
        print(f"No .nii.gz files found in folder: {lesions_folder}")
    else:
        for mask in mask_files:
            warped_mask = mask.replace(".nii.gz", "_space-MNI152T1w1mm.nii.gz")
            print(f"\nWarping lesion mask: {mask}")
            apply_warp_mask(fixed_template1, mat_file1, mask, warped_mask)
            print(f"Warped lesion mask saved to: {warped_mask}")

    
    print("==========================================")
    print("Step 3: Registering moving template to fixed template using FLIRT")
    print("==========================================")
    print(f"Moving Template: {moving_template}")
    print(f"Fixed Template:  {fixed_template2}")
    print(f"Degrees of Freedom: {dof}")
    flirt_reg(moving_template, fixed_template2, mat_file2, registered_template2, n_threads, dof)
    print("Template registration completed.\n")

    # Warp the binary mask if provided.
    if args.binary_mask:
        print("==========================================")
        print("Step 4a: Warping binary mask to fixed template space using FLIRT")
        print("==========================================")
        binary_mask = args.binary_mask
        warped_binary_mask = binary_mask.replace(".nii.gz", "_space-MNI152T1w1mm.nii.gz")
        print(f"Warping binary mask: {binary_mask}")
        apply_warp_mask(fixed_template1, mat_file1, binary_mask, warped_binary_mask)
        print(f"Warped binary mask saved to: {warped_binary_mask}")

        print("==========================================")
        print("Step 4b: Warping binary mask to fixed template space using FLIRT")
        print("==========================================")
        binary_mask = args.binary_mask
        warped_binary_mask = binary_mask.replace(".nii.gz", "_space-MNI152bT1w0x5mm.nii.gz")
        print(f"Warping binary mask: {binary_mask}")
        apply_warp_mask(fixed_template2, mat_file2, binary_mask, warped_binary_mask)
        print(f"Warped binary mask saved to: {warped_binary_mask}")


    print("\nAll registrations and warpings have been completed successfully.")



if __name__ == "__main__":
    main()
