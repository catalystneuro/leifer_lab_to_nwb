"""
Main conversion script for a single session of processed data (no raw imaging) for the Randi et al. Nature 2023 paper.
"""

import pathlib


from leifer_lab_to_nwb.randi_nature_2023 import pump_probe_to_nwb

# TESTING=True creates 'preview' files that truncate all major data blocks; useful for ensuring process runs smoothly
TESTING = True

# TESTING=False performs a full file conversion
# TESTING = False


# Define base folder of source data
# Change these as needed on new systems
BASE_FOLDER_PATH = pathlib.Path("D:/Leifer")
SUBJECT_INFO_FILE_PATH = BASE_FOLDER_PATH / "all_subjects_metadata.yaml"

# The integer ID that maps this subject onto the 'all_subect_metadata.yaml' entry
# For testing, subject ID '26' matches date '20211104' used in Figure 1 of the paper
SUBJECT_ID = 0

OUTPUT_FOLDER_PATH = pathlib.Path("E:/Leifer")
NWB_OUTPUT_FOLDER_PATH = OUTPUT_FOLDER_PATH / "nwbfiles"
NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)


if __name__ == "__main__":
    pump_probe_to_nwb(
        base_folder_path=BASE_FOLDER_PATH,
        subject_info_file_path=SUBJECT_INFO_FILE_PATH,
        subject_id=SUBJECT_ID,
        nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
        raw_or_processed="processed",
        testing=TESTING,
    )
