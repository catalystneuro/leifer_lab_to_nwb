"""
Main conversion script for a single session of processed data (no raw imaging) for the Randi et al. Nature 2023 paper.
"""

import pathlib


from leifer_lab_to_nwb.randi_nature_2023 import convert_session

# STUB_TEST=True creates 'preview' files that truncate all major data blocks; useful for ensuring process runs smoothly
# STUB_TEST=False performs a full file conversion
# STUB_TEST = True
STUB_TEST = False

# Define base folder of source data
# Change these as needed on new systems
SOURCE_FOLDER_PATH = pathlib.Path("D:/Leifer")
SESSION_FOLDER_PATH = SOURCE_FOLDER_PATH / "20211104"

PUMP_PROBE_FOLDER_PATH = SESSION_FOLDER_PATH / "pumpprobe_20211104_163944"
MULTICOLOR_FOLDER_PATH = SESSION_FOLDER_PATH / "multicolorworm_20211104_162630"

OUTPUT_FOLDER_PATH = pathlib.Path("E:/Leifer")
NWB_OUTPUT_FOLDER_PATH = OUTPUT_FOLDER_PATH / "nwbfiles"

# *************************************************************************
# Everything below this line is automated and should not need to be changed
# *************************************************************************

NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

convert_session(
    pump_probe_folder_path=PUMP_PROBE_FOLDER_PATH,
    multicolor_folder_path=MULTICOLOR_FOLDER_PATH,
    nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
    raw_or_processed="processed",
    stub_test=STUB_TEST,
)
