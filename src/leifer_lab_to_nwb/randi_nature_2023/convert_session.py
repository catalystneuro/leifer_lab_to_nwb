"""Main conversion script for a single session of data for the Randi et al. Nature 2023 paper."""

import datetime
import pathlib

import pandas
from dateutil import tz

from leifer_lab_to_nwb.randi_nature_2023 import RandiNature2023Converter
from leifer_lab_to_nwb.randi_nature_2023.interfaces import (
    ExtraOphysMetadataInterface,
    OnePhotonSeriesInterface,
    OptogeneticStimulationInterface,
    SubjectInterface,
)

# Define base folder of source data
base_folder_path = pathlib.Path("E:/Leifer")
session_folder_path = base_folder_path / "Hermaphrodite"

pumpprobe_folder_path = session_folder_path / "pumpprobe_20210830_111646"

# Parse session start time from top path
session_string = pumpprobe_folder_path.stem.removeprefix("pumpprobe_")
session_start_time = datetime.datetime.strptime(session_string, "%Y%m%d_%H%M%S")
session_start_time = session_start_time.replace(tzinfo=tz.gettz("US/Eastern"))

# Define specific paths for interfaces and output
raw_pumpprobe_folder_path = pumpprobe_folder_path / "raw"
raw_data_file_path = raw_pumpprobe_folder_path / "sCMOS_Frames_U16_1024x512.dat"
logbook_file_path = raw_pumpprobe_folder_path.parent / "logbook.txt"

nwbfile_path = base_folder_path / "nwbfiles" / f"{session_string}.nwb"

# Initialize interfaces
data_interfaces = list()

# subject_interface = SubjectInterface(file_path=logbook_file_path, session_id=session_string)

# one_photon_series_interface = OnePhotonSeriesInterface(folder_path=raw_pumpprobe_folder_path)

extra_ophys_metadata_interface = ExtraOphysMetadataInterface(folder_path=raw_pumpprobe_folder_path)

optogenetic_stimulation_interface = OptogeneticStimulationInterface(folder_path=raw_pumpprobe_folder_path)

# Initialize converter
data_interfaces = [
    # subject_interface,  # TODO: pending logbook consistency across sessions (still uploading)
    # one_photon_series_interface,  # TODO: pending extension
    extra_ophys_metadata_interface,
    optogenetic_stimulation_interface,
]
converter = RandiNature2023Converter(data_interfaces=data_interfaces)

metadata = converter.get_metadata()

metadata["NWBFile"]["session_start_time"] = session_start_time

# metadata["Subject"]["subject_id"] = session_start_time.strftime("%y%m%d")  # TODO: hopefully come up with better ID
# metadata["Subject"]["species"] = "C. elegans"
# metadata["Subject"]["sex"] = "XX"  # TODO: pull from global listing by subject
# metadata["Subject"]["age"] = "P1D"  # TODO: request
# metadata["Subject"]["growth_stage_time"] = pandas.Timedelta(hours=2, minutes=30).isoformat()  # TODO: request
# metadata["Subject"]["growth_stage"] = "YA"  # TODO: request
# metadata["Subject"]["cultivation_temp"] = "20."  # TODO: request, schema says in units Celsius

converter.run_conversion(nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True)
