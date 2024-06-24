"""Main conversion script for a single session of data for the Randi et al. Nature 2023 paper."""

import datetime
import pathlib

import pandas
from dateutil import tz

from leifer_lab_to_nwb.randi_nature_2023 import RandiNature2023Converter
from leifer_lab_to_nwb.randi_nature_2023.interfaces import (
    ExtraOphysMetadataInterface,
    OptogeneticStimulationInterface,
    PumpProbeImagingInterface,
    SubjectInterface,
)

# Define base folder of source data
# Change these as needed on new systems
BASE_FOLDER_PATH = pathlib.Path("E:/Leifer")
SESSION_FOLDER_PATH = BASE_FOLDER_PATH / "Hermaphrodite"
LOGBOOK_FILE_PATH = raw_pumpprobe_folder_path.parent / "logbook.txt"

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

# Define specific paths for interfaces and output
raw_pumpprobe_folder_path = PUMPPROBE_FOLDER_PATH / "raw"
raw_multicolor_folder_path = SESSION_FOLDER_PATH / "multicolor_20210830_111646"

raw_data_file_path = raw_pumpprobe_folder_path / "sCMOS_Frames_U16_1024x512.dat"
LOGBOOK_FILE_PATH = raw_pumpprobe_folder_path.parent / "logbook.txt"

nwbfile_folder_path = BASE_FOLDER_PATH / "nwbfiles"
nwbfile_folder_path.mkdir(exist_ok=True)
nwbfile_path = nwbfile_folder_path / f"{session_string}.nwb"

interfaces_classes_to_test = {
    PumpProbeImagingInterface: {"folder_path": raw_pumpprobe_folder_path},
    CalciumSegmentationInterface: {"folder_path": raw_pumpprobe_folder_path},
    NeuroPALImagingInterface: {"folder_path": raw_multicolor_folder_path},
    OptogeneticStimulationInterface: {"folder_path": raw_pumpprobe_folder_path},
}

# All interfaces must currently be written with the 'ExtraOphysMetadataInterface' first to ensure all
# associated metadata is included
# TODO: might figure a good way to include this automatically via the NWBConverter
for InterfaceClassToTest in interfaces_to_test:
    nwbfile_path = NWB_OUTPUT_FOLDER_PATH / f"test_{InterfaceClassToTest}.nwb"

    extra_ophys_metadata_interface = ExtraOphysMetadataInterface(folder_path=raw_pumpprobe_folder_path)
    data_interfaces.append(extra_ophys_metadata_interface)

    interface = InterfaceClassToTest(folder_path=raw_pumpprobe_folder_path)
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

    converter.run_conversion(nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True)
