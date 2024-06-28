"""Main conversion script for a single session of data for the Randi et al. Nature 2023 paper."""

import datetime
import pathlib

import pandas
import pynwb
from dateutil import tz

from leifer_lab_to_nwb.randi_nature_2023 import RandiNature2023Converter

# STUB_TEST=True creates 'preview' files that truncate all major data blocks; useful for ensuring process runs smoothly
# STUB_TEST=False performs a full file conversion
STUB_TEST = True


# Define base folder of source data
# Change these as needed on new systems
BASE_FOLDER_PATH = pathlib.Path("D:/Leifer")
SESSION_FOLDER_PATH = BASE_FOLDER_PATH / "20211104"
# LOGBOOK_FILE_PATH = SESSION_FOLDER_PATH / "logbook.txt"

PUMPPROBE_FOLDER_PATH = SESSION_FOLDER_PATH / "pumpprobe_20211104_163944"
MULTICOLOR_FOLDER_PATH = SESSION_FOLDER_PATH / "multicolorworm_20211104_162630"

NWB_OUTPUT_FOLDER_PATH = BASE_FOLDER_PATH / "nwbfiles"

# *************************************************************************
# Everything below this line is automated and should not need to be changed
# *************************************************************************

NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

# Parse session start time from the pumpprobe path
session_string = PUMPPROBE_FOLDER_PATH.stem.removeprefix("pumpprobe_")
session_start_time = datetime.datetime.strptime(session_string, "%Y%m%d_%H%M%S")
session_start_time = session_start_time.replace(tzinfo=tz.gettz("US/Eastern"))

# TODO: might be able to remove these when NeuroConv supports better schema validation
PUMPPROBE_FOLDER_PATH = str(PUMPPROBE_FOLDER_PATH)
MULTICOLOR_FOLDER_PATH = str(MULTICOLOR_FOLDER_PATH)

# Initialize interfaces
data_interfaces = list()

source_data = {
    "PumpProbeImagingInterfaceGreen": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Green"},
    "PumpProbeImagingInterfaceRed": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Red"},
    "PumpProbeSegmentationInterfaceGreed": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Green"},
    "PumpProbeSegmentationInterfaceRed": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Red"},
    "NeuroPALImagingInterface": {"multicolor_folder_path": MULTICOLOR_FOLDER_PATH},
    "NeuroPALSegmentationInterface": {"multicolor_folder_path": MULTICOLOR_FOLDER_PATH},
    "OptogeneticStimulationInterface": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH},
    "ExtraOphysMetadataInterface": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH},
}

# Initialize converter
converter = RandiNature2023Converter(source_data=source_data)

metadata = converter.get_metadata()

metadata["NWBFile"]["session_start_time"] = session_start_time

# TODO: these are placeholders that would be read in from a logbook read+lookup
subject_id = session_start_time.strftime("%y%m%d")
metadata["Subject"]["subject_id"] = subject_id
metadata["Subject"]["species"] = "C. elegans"
metadata["Subject"]["sex"] = "XX"
metadata["Subject"]["age"] = "P1D"
# metadata["Subject"]["growth_stage_time"] = pandas.Timedelta(hours=2, minutes=30).isoformat()  # TODO: request
metadata["Subject"]["growth_stage"] = "YA"
metadata["Subject"]["cultivation_temp"] = 20.0

conversion_options = {
    "PumpProbeImagingInterfaceGreen": {"stub_test": STUB_TEST},
    "PumpProbeImagingInterfaceRed": {"stub_test": STUB_TEST},
    "PumpProbeSegmentationInterfaceGreed": {"stub_test": STUB_TEST},
    "PumpProbeSegmentationInterfaceRed": {"stub_test": STUB_TEST},
    "NeuroPALImagingInterface": {"stub_test": STUB_TEST},
}

nwbfile_path = NWB_OUTPUT_FOLDER_PATH / f"sub-{subject_id}_ses-{session_string}.nwb"
converter.run_conversion(
    nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True, conversion_options=conversion_options
)
