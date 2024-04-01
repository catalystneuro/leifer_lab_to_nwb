import pathlib
import datetime
from dateutil import tz

from neuroconv import ConverterPipe

from leifer_lab_to_nwb.randi_nature_2023.interfaces import (
    OnePhotonSeriesInterface,
    ExtraOphysMetadataInterface,
    OptogeneticStimulationInterface,
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

nwbfile_path = base_folder_path / "nwbfiles" / f"{session_string}.nwb"


# Initialize interfaces
data_interfaces = list()

one_photon_series_interface = OnePhotonSeriesInterface(folder_path=raw_pumpprobe_folder_path)
data_interfaces.append(one_photon_series_interface)

extra_ophys_metadata_interface = ExtraOphysMetadataInterface(folder_path=raw_pumpprobe_folder_path)
data_interfaces.append(extra_ophys_metadata_interface)

optogenetic_stimulation_interface = OptogeneticStimulationInterface(folder_path=raw_pumpprobe_folder_path)
data_interfaces.append(optogenetic_stimulation_interface)

# Initialize converter
converter = ConverterPipe(data_interfaces=data_interfaces)

metadata = converter.get_metadata()

metadata["NWBFile"]["session_start_time"] = session_start_time

converter.run_conversion(nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True)
