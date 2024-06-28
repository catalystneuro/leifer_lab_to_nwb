"""
Test each individual interface by performing standalone file creations.

An actual conversion should use the `convert_session.py` or `convert_data.py` scripts.

This just makes debugging easier.
"""

import datetime
import pathlib
import warnings

import pandas
import pynwb
from dateutil import tz
from pynwb.testing.mock.file import mock_NWBFile

from leifer_lab_to_nwb.randi_nature_2023 import RandiNature2023Converter
from leifer_lab_to_nwb.randi_nature_2023.interfaces import (
    ExtraOphysMetadataInterface,
    NeuroPALImagingInterface,
    NeuroPALSegmentationInterface,
    OptogeneticStimulationInterface,
    PumpProbeImagingInterface,
    PumpProbeSegmentationInterface,
)

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

# Suppress false warning
warnings.filterwarnings(action="ignore", message="The linked table for DynamicTableRegion*", category=UserWarning)

NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)
test_folder_path = NWB_OUTPUT_FOLDER_PATH / "test_interfaces"
test_folder_path.mkdir(exist_ok=True)

# Parse session start time from the pumpprobe path
session_string = PUMPPROBE_FOLDER_PATH.stem.removeprefix("pumpprobe_")
session_start_time = datetime.datetime.strptime(session_string, "%Y%m%d_%H%M%S")
session_start_time = session_start_time.replace(tzinfo=tz.gettz("US/Eastern"))

# TODO: might be able to remove these when NeuroConv supports better schema validation
PUMPPROBE_FOLDER_PATH = str(PUMPPROBE_FOLDER_PATH)
MULTICOLOR_FOLDER_PATH = str(MULTICOLOR_FOLDER_PATH)

interfaces_classes_to_test = {
    "PumpProbeImagingInterfaceGreen": {
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Green"},
        "conversion_options": {"stub_test": True},
    },
    "PumpProbeImagingInterfaceRed": {
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Red"},
        "conversion_options": {"stub_test": True},
    },
    "PumpProbeSegmentationInterfaceGreed": {
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Green"},
        "conversion_options": {"stub_test": True},
    },
    "PumpProbeSegmentationInterfaceRed": {
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Red"},
        "conversion_options": {"stub_test": True},
    },
    "NeuroPALImagingInterface": {
        "source_data": {"multicolor_folder_path": MULTICOLOR_FOLDER_PATH},
        "conversion_options": {"stub_test": True},
    },
    "NeuroPALSegmentationInterface": {
        "source_data": {"multicolor_folder_path": MULTICOLOR_FOLDER_PATH},
    },
    "OptogeneticStimulationInterface": {
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH},
    },
    "ExtraOphysMetadataInterface": {
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH},
    },
}


for test_case_name, interface_options in interfaces_classes_to_test.items():
    source_data = {test_case_name: interface_options["source_data"]}
    converter = RandiNature2023Converter(source_data=source_data)

    metadata = converter.get_metadata()

    metadata["NWBFile"]["session_start_time"] = session_start_time
    metadata["Subject"]["subject_id"] = session_start_time.strftime("%y%m%d")

    # TODO: these are placeholders that would be read in from a logbook read+lookup
    metadata["Subject"]["subject_id"] = session_start_time.strftime("%y%m%d")
    metadata["Subject"]["species"] = "C. elegans"
    metadata["Subject"]["sex"] = "XX"
    metadata["Subject"]["age"] = "P1D"
    # metadata["Subject"]["growth_stage_time"] = pandas.Timedelta(hours=2, minutes=30).isoformat()  # TODO: request
    metadata["Subject"]["growth_stage"] = "YA"
    metadata["Subject"]["cultivation_temp"] = 20.0

    if "conversion_options" in interface_options:
        conversion_options = {test_case_name: interface_options["conversion_options"]}
    else:
        conversion_options = None

    in_memory_nwbfile = mock_NWBFile()
    converter.add_to_nwbfile(nwbfile=in_memory_nwbfile, metadata=metadata, conversion_options=conversion_options)

    print("Added to in-memory NWBFile object!")

    nwbfile_path = test_folder_path / f"test_{test_case_name}.nwb"
    converter.run_conversion(
        nwbfile_path=nwbfile_path, metadata=metadata, conversion_options=conversion_options, overwrite=True
    )

    # Test roundtrip to make sure PyNWB can read the file back
    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
        read_nwbfile = io.read()
