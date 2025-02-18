import nibabel as nib
import numpy as np
import pandas as pd

# Define the file names
file_MNI = 'threshZresults_testcentral_fever_binarized.nii.gz'
file_std = 'threshZresults_testcentral_fever_binarized_warped.nii.gz'

# Load the images
img_MNI = nib.load(file_MNI)
img_std = nib.load(file_std)

# Extract the data arrays
data_MNI = img_MNI.get_fdata()
data_std = img_std.get_fdata()

# Count the number of non-zero voxels for each image
count_MNI = np.count_nonzero(data_MNI)
count_std = np.count_nonzero(data_std)

# Create a DataFrame with the results
df = pd.DataFrame({
    'File': [file_MNI, file_std],
    'NonZeroVoxelCount': [count_MNI, count_std]
})

print(df)

# Save the DataFrame to a CSV file
df.to_csv('nonzero_voxel_counts.csv', index=False)

print("CSV file with non-zero voxel counts has been saved as 'nonzero_voxel_counts.csv'.")
