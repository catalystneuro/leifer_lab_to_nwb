"""Main conversion script for the entire dataset for the Randi et al. Nature 2023 paper."""

import datetime
import pathlib
import warnings

import dateutil.tz
import ndx_subjects
import pandas
import pynwb
import tqdm
import yaml

from leifer_lab_to_nwb.randi_nature_2023 import convert_session

# STUB_TEST=True creates 'preview' files that truncate all major data blocks; useful for ensuring process runs smoothly
# STUB_TEST=False performs a full file conversion
STUB_TEST = True
# STUB_TEST = False

SKIP_EXISTING = True

# Define base folder of source data
# Change these as needed on new systems
SOURCE_FOLDER_PATH = pathlib.Path("D:/Leifer")
SESSION_FOLDER_PATH = SOURCE_FOLDER_PATH / "20211104"
LOGBOOK_FILE_PATH = SOURCE_FOLDER_PATH / "all_subjects_metadata.yaml"

PUMPPROBE_FOLDER_PATH = SESSION_FOLDER_PATH / "pumpprobe_20211104_163944"
MULTICOLOR_FOLDER_PATH = SESSION_FOLDER_PATH / "multicolorworm_20211104_162630"

OUTPUT_FOLDER_PATH = pathlib.Path("E:/Leifer")
NWB_OUTPUT_FOLDER_PATH = OUTPUT_FOLDER_PATH / "nwbfiles"

# *************************************************************************
# Everything below this line is automated and should not need to be changed
# *************************************************************************

NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

with open(file=LOGBOOK_FILE_PATH, mode="r") as f:
    all_subject_info = yaml.safe_load(f)

raw_or_processed = "processed"
for subject_info in tqdm.tqdm(
    iterable=all_subject_info.values(),
    total=len(all_subject_info),
    desc="Converting processed sessions",
    unit="session",
    position=0,
    leave=True,
    mininterval=5.0,
    smoothing=0,
):
    session_folder_path = SOURCE_FOLDER_PATH / str(subject_info["date"])
    pumpprobe_folder_path = session_folder_path / subject_info["pump_probe_folder"]
    multicolor_folder_path = session_folder_path / subject_info["multicolor_folder"]

    convert_session(
        pumpprobe_folder_path=pumpprobe_folder_path,
        multicolor_folder_path=multicolor_folder_path,
        nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
        raw_or_processed=raw_or_processed,
        subject_info=subject_info,
        stub_test=STUB_TEST,
        skip_existing=SKIP_EXISTING,
    )

print("\n\nProcessed sessions are converted!\n\n")

raw_or_processed = "raw"
for subject_info in tqdm.tqdm(
    iterable=all_subject_info.values(),
    total=len(all_subject_info),
    desc="Converting processed sessions",
    unit="session",
    position=0,
    leave=True,
    mininterval=5.0,
    smoothing=0,
):
    session_folder_path = SOURCE_FOLDER_PATH / subject_info["date"]
    pumpprobe_folder_path = session_folder_path / subject_info["pump_probe_folder"]
    multicolor_folder_path = session_folder_path / subject_info["multicolor_folder"]

    convert_session(
        pumpprobe_folder_path=pumpprobe_folder_path,
        multicolor_folder_path=multicolor_folder_path,
        nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
        raw_or_processed=raw_or_processed,
        subject_info=subject_info,
        stub_test=STUB_TEST,
        skip_existing=SKIP_EXISTING,
    )

print("\n\nRaw sessions are converted!\n\n")
