import nibabel as nib
import numpy as np
from scipy.ndimage import label
import pandas as pd
import xml.etree.ElementTree as ET

import xml.etree.ElementTree as ET

def clean_label(label_name):
    """
    Clean up the label name by replacing known wildcard patterns.
    If the label is exactly '*.*.*.*.', label it as 'Background'.
    Otherwise, remove any occurrences of '*.' or '.*'.
    """
    if label_name.strip() == "*.*.*.*.":
        return "Background"
    # Remove wildcard patterns if present
    cleaned = label_name.replace("*.", "").replace(".*", "").replace("*", "")
    return cleaned.strip()

def load_brainstem_labels():

    atlas_labels = list(range(0, 24))
    atlas_labels_names = {
            0: "Not_in_Atlas",
            1: "CSTL_Atlas",
            2: "CSTR_Atlas",
            3: "FPTL_Atlas",
            4: "FPTR_Atlas",
            5: "ICPMCL_Atlas",
            6: "ICPMCR_Atlas",
            7: "ICPVCL_Atlas",
            8: "ICPVCR_Atlas",
            9: "LLL_Atlas",
            10: "LLR_Atlas",
            11: "MCP_Atlas",
            12: "MLL_Atlas",
            13: "MLR_Atlas",
            14: "POTPTL_Atlas",
            15: "POTPTR_Atlas",
            16: "SCPCRL_Atlas",
            17: "SCPCRR_Atlas",
            18: "SCPCTL_Atlas",
            19: "SCPCTR_Atlas",
            20: "SCPSCL_Atlas",
            21: "SCPSCR_Atlas",
            22: "STTL_Atlas",
            23: "STTR_Atlas"
        }

    return atlas_labels, atlas_labels_names


def load_tailrach_atlas_labels(csv_file="tailrach_atlas_labels.csv"):
    """
    Reads atlas labels from a CSV file with the following structure:
    
        "Index","Description"
        0,"Unknown/Background"
        1,"Left CerebellumPosterior LobeInferior Semi-Lunar LobuleGray Matter"
        ...
    
    Returns:
      1) A list of label IDs (atlas_labels).
      2) A dictionary mapping label ID -> description (atlas_labels_names).
    """
    # Read the CSV into a pandas DataFrame
    df = pd.read_csv(csv_file)
    
    # Create a list of label IDs using the 'Index' column
    atlas_labels = df['Index'].tolist()
    
    # Create a dictionary mapping label ID to its corresponding description
    atlas_labels_names = {}
    for _, row in df.iterrows():
        label_id = row['Index']
        description = row['Description']
        atlas_labels_names[label_id] = description
    
    return atlas_labels, atlas_labels_names

    

def load_neudorfer_atlas_labels(csv_file='neudorfer_atlas_labels.csv'):
    """
    Reads the Neudorfer atlas labels from a CSV file and creates:
      1) A list of label IDs (atlas_labels).
      2) A dictionary mapping label ID -> label name/abbreviation (atlas_labels_names).
    """
    # Read the CSV into a pandas DataFrame
    df = pd.read_csv(csv_file)
    
    # Create a list of label IDs
    atlas_labels = df['Label'].tolist()
    
    # Create a dictionary:
    #   key:   label ID (integer)
    #   value: for example, "Hemisphere_Abbreviation" or any other string composition
    atlas_labels_names = {}
    for _, row in df.iterrows():
        label_id = row['Label']
        
        # Pick how you want to construct the label’s name:
        # Option A: Just the abbreviation
        # name_str = row['Abbreviation']
        
        # Option B: Hemisphere + "_" + Abbreviation
        # name_str = f"{row['Hemisphere']}_{row['Abbreviation']}"
        
        # Option C: Hemisphere + "_" + Name
        # name_str = f"{row['Hemisphere']}_{row['Name']}"

        # Option D: Combine hemisphere, abbreviation, and name
        name_str = f"{row['Hemisphere']}_{row['Abbreviation']}_{row['Name']}"
        
        atlas_labels_names[label_id] = name_str
    
    return atlas_labels, atlas_labels_names


def compute_stats_atlas(lesion_mask_path, warped_atlas_mask_path, output_file, atlas_type='neudorfer'):
    """
    Compute statistics for the from a lesion mask and save the results to a CSV file.

    Parameters:
    mask_file (str): Path to the input mask file in NIfTI format for the smatt_atlas.
    output_file (str): Path to the output CSV file where results for the smatt_atlas will be saved.
    """
    # Load the mask file
    lesion_mask = nib.load(lesion_mask_path)
    lesion_mask_data = lesion_mask.get_fdata().astype(np.uint8)

    warped_atlas_mask = nib.load(warped_atlas_mask_path)
    warped_atlas_mask_data = warped_atlas_mask.get_fdata().astype(np.uint8)

    # Voxel dimensions to calculate volume
    voxel_dims = lesion_mask.header.get_zooms()

    atlas_labels = []
    atlas_labels_names = []

    if atlas_type == "neudorfer":
        atlas_labels, atlas_labels_names = load_neudorfer_atlas_labels()
       
    elif atlas_type == "tailrach":
        atlas_labels, atlas_labels_names = load_tailrach_atlas_labels()

    elif atlas_type == "brainstem":
        atlas_labels, atlas_labels_names = load_brainstem_labels()

    else:
        raise Exception("Something went wrong!")
    
    results = []

    for region_id, region_name  in zip(atlas_labels, [atlas_labels_names[label] for label in atlas_labels]):

        # mask out all lesions except the lesions residing in the current atlas label
        current_atlas_mask = np.zeros_like(warped_atlas_mask_data)
        current_atlas_mask[warped_atlas_mask_data==region_id] = 1
        current_lesion_mask = lesion_mask_data * current_atlas_mask

        # Calculate lesion volume in the entire atlas area
        lesion_voxel_count = np.count_nonzero(current_lesion_mask)
        lesion_volume = lesion_voxel_count * np.prod(voxel_dims)

        # Normalize by the volume of the original region
        region_voxel_count = np.count_nonzero(current_atlas_mask)
        region_volume = region_voxel_count * np.prod(voxel_dims)
        
        if region_volume > 0:
            normalized_lesion_volume = lesion_volume / region_volume
        else:
            normalized_lesion_volume = 0

        # Store results
        results.append({
            'atlas_label': region_name,
            'n_label_voxels': region_voxel_count,
            'label_volume [mm³]': region_volume,
            'n_lesion_voxels': lesion_voxel_count,
            'lesion_volume [mm³]': lesion_volume,
            'lesion_volume [percent]': 100* normalized_lesion_volume
        })

    df = pd.DataFrame(results)   
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
   
    compute_stats_atlas(lesion_mask_path="registration/threshZresults_testcentral_fever_binarized_space-MNI152T1w1mm.nii.gz", 
                        warped_atlas_mask_path="Talairach-labels-1mm.nii.gz", 
                        output_file="regions_in_tailrach.csv", atlas_type='tailrach')
    
    compute_stats_atlas(lesion_mask_path="registration/threshZresults_testcentral_fever_binarized_space-MNI152bT1w0x5mm.nii.gz", 
                        warped_atlas_mask_path="neudorfer_atlas_labels_0.5mm.nii.gz", 
                        output_file="regions_in_neudorfer.csv", atlas_type='neudorfer')
    
    compute_stats_atlas(lesion_mask_path="registration/threshZresults_testcentral_fever_binarized_space-MNI152bT1w0x5mm.nii.gz", 
                        warped_atlas_mask_path="brainstem_atlas_combined_threshold_2e-02.nii.gz", 
                        output_file="regions_in_brainstem.csv", atlas_type='brainstem')


