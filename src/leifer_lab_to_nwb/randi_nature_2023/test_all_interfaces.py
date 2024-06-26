"""Main conversion script for a single session of data for the Randi et al. Nature 2023 paper."""

import datetime
import pathlib

import pandas
import pynwb
from dateutil import tz

from leifer_lab_to_nwb.randi_nature_2023 import RandiNature2023Converter
from leifer_lab_to_nwb.randi_nature_2023.interfaces import (
    ExtraOphysMetadataInterface,
    NeuroPALImagingInterface,
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

NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

# Parse session start time from the pumpprobe path
session_string = PUMPPROBE_FOLDER_PATH.stem.removeprefix("pumpprobe_")
session_start_time = datetime.datetime.strptime(session_string, "%Y%m%d_%H%M%S")
session_start_time = session_start_time.replace(tzinfo=tz.gettz("US/Eastern"))

interfaces_classes_to_test = {
    "PumpProbeImagingInterfaceGreen": {
        "class": PumpProbeImagingInterface,
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Green"},
        "conversion_options": {"stub_test": True},
    },
    "PumpProbeImagingInterfaceRed": {
        "class": PumpProbeImagingInterface,
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Red"},
        "conversion_options": {"stub_test": True},
    },
    "NeuroPALImagingInterface": {
        "class": NeuroPALImagingInterface,
        "source_data": {"multicolor_folder_path": MULTICOLOR_FOLDER_PATH},
        "conversion_options": {"stub_test": True},
    },
    "PumpProbeSegmentationInterface": {
        "class": PumpProbeSegmentationInterface,
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Green"},
    },
    "PumpProbeSegmentationInterface": {
        "class": PumpProbeSegmentationInterface,
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH, "channel_name": "Red"},
    },
    # NeuroPALSegmentationInterface: {"folder_path": MULTICOLOR_FOLDER_PATH},
    "OptogeneticStimulationInterface": {
        "class": OptogeneticStimulationInterface,
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH},
    },
    "ExtraOphysMetadataInterface": {
        "class": ExtraOphysMetadataInterface,
        "source_data": {"pumpprobe_folder_path": PUMPPROBE_FOLDER_PATH},
    },
}


for test_case_name, interface_options in interfaces_classes_to_test.items():
    nwbfile_path = NWB_OUTPUT_FOLDER_PATH / f"test_{test_case_name}.nwb"

    data_interfaces = list()

    # Special case of the OptogeneticStimulationInterface; requires the PumpProbeSegmentationInterface to be added first
    if test_case_name == "OptogeneticStimulationInterface":
        pump_probe_segmentation_interface = PumpProbeSegmentationInterface(
            pumpprobe_folder_path=PUMPPROBE_FOLDER_PATH, channel_name="Green"
        )
        data_interfaces.append(pump_probe_segmentation_interface)

    InterfaceClassToTest = interface_options["class"]
    interface = InterfaceClassToTest(**interface_options["source_data"])
    data_interfaces.append(interface)

    # Initialize converter
    converter = RandiNature2023Converter(data_interfaces=data_interfaces)

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
        conversion_options = {InterfaceClassToTest.__name__: interface_options["conversion_options"]}
    else:
        conversion_options = None
    converter.run_conversion(
        nwbfile_path=nwbfile_path, metadata=metadata, conversion_options=conversion_options, overwrite=True
    )

    # Test roundtrip to make sure PyNWB can read the file back
    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
        read_nwbfile = io.read()
