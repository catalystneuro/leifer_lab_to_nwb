"""Main code definition for the conversion of a full session (including NeuroPAL)."""

import datetime
import pathlib
import warnings

import yaml
from dateutil import tz
from pydantic import FilePath, DirectoryPath

from ._randi_nature_2023_converter import RandiNature2023Converter


def pump_probe_to_nwb(
    *,
    base_folder_path: DirectoryPath,
    subject_info_file_path: FilePath,
    subject_id: int,
    nwb_output_folder_path: DirectoryPath,
    testing: bool = False,
) -> None:
    """
    Convert a single session of pumpprobe (and its corresponding NeuroPAL) data to NWB format.

    Based off of the data structures found in the Randi 2023 dataset.

    Parameters
    ----------
    base_folder_path : pydantic.DirectoryPath
        The base folder in which to search for data referenced by the `subject_info_file_path`.

        Expected to be structured similar to...

        |- < base folder >
        |--- < date >
        |----- multicolorworm_< timestamp >
        |----- pumpprobe_< timestamp >

        For example...

        |- D:/Leifer
        |--- 20211104
        |----- multicolorworm_20211104_162630
        |----- pumpprobe_20211104_163944
    subject_info_file_path : pydantic.FilePath
        The path to the subject log YAML file.
    subject_id : int
        ID of the subject in the YAML file - must be an integer, not a string.
    nwb_output_folder_path : pydantic.DirectoryPath
        The folder path to save the NWB files to.
    testing : bool, default: False
        Whether or not to 'test' the conversion process by limiting the amount of data written to the NWB file.
    """
    subject_info_file_path = pathlib.Path(subject_info_file_path)
    nwb_output_folder_path = pathlib.Path(nwb_output_folder_path)

    with open(file=subject_info_file_path, mode="r") as stream:
        all_subject_info = yaml.load(stream=stream, Loader=yaml.SafeLoader)

    this_subject_info = all_subject_info[subject_id]

    session_folder_path = base_folder_path / str(this_subject_info["date"])
    pump_probe_folder_path = session_folder_path / this_subject_info["pump_probe_folder"]
    multicolor_folder_path = session_folder_path / this_subject_info["multicolor_folder"]

    # Suppress false warning
    warnings.filterwarnings(action="ignore", message="The linked table for DynamicTableRegion*", category=UserWarning)

    nwb_output_folder_path.mkdir(exist_ok=True)

    # Parse session start time from the pumpprobe path
    session_string = pump_probe_folder_path.stem.removeprefix("pumpprobe_")
    session_start_time = datetime.datetime.strptime(session_string, "%Y%m%d_%H%M%S")
    session_start_time = session_start_time.replace(tzinfo=tz.gettz("US/Eastern"))

    # TODO: might be able to remove these when NeuroConv supports better schema validation
    pump_probe_folder_path = str(pump_probe_folder_path)
    multicolor_folder_path = str(multicolor_folder_path)

    source_data = {
        "PumpProbeImagingInterfaceGreen": {"pump_probe_folder_path": pump_probe_folder_path, "channel_name": "Green"},
        "PumpProbeImagingInterfaceRed": {"pump_probe_folder_path": pump_probe_folder_path, "channel_name": "Red"},
        "PumpProbeSegmentationInterfaceGreed": {
            "pump_probe_folder_path": pump_probe_folder_path,
            "channel_name": "Green",
        },
        "PumpProbeSegmentationInterfaceRed": {"pump_probe_folder_path": pump_probe_folder_path, "channel_name": "Red"},
        "NeuroPALImagingInterface": {"multicolor_folder_path": multicolor_folder_path},
        "NeuroPALSegmentationInterface": {"multicolor_folder_path": multicolor_folder_path},
        "OptogeneticStimulationInterface": {"pump_probe_folder_path": pump_probe_folder_path},
        "ExtraOphysMetadataInterface": {"pump_probe_folder_path": pump_probe_folder_path},
    }

    converter = RandiNature2023Converter(source_data=source_data)

    metadata = converter.get_metadata()

    metadata["NWBFile"]["session_start_time"] = session_start_time

    # TODO: these are all placeholders that would be read in from the YAML logbook read+lookup
    metadata["NWBFile"][
        "experiment_description"
    ] = """
    To measure signal propagation, we activated each single neuron, one at a time, through two-photon stimulation,
    while simultaneously recording the calcium activity of the population at cellular resolution using spinning disk
    confocal microscopy. We recorded activity from 113 wild-type (WT)-background animals, each for up to 40min, while
    stimulating a mostly randomly selected sequence of neurons one by one every 30s. We spatially restricted our
    two-photon activation in three dimensions to be the size of a typical C. elegans neuron, to minimize off-target
    activation of neighbouring neurons. Animals were immobilized but awake,and pharyngeal pumping was visible during
    recordings.
    """
    metadata["NWBFile"]["institution"] = "Princeton University"
    metadata["NWBFile"]["lab"] = "Leifer Lab"
    metadata["NWBFile"]["experimenter"] = ["Randi, Francesco"]
    metadata["NWBFile"]["keywords"] = ["C. elegans", "optogenetics", "functional connectivity"]

    assert (
        this_subject_info["subject_id"] == subject_id
    ), "Mismatch in subject ID between key and info value! Please double check the subject metadata YAML file."

    metadata["Subject"]["subject_id"] = str(subject_id)

    lab_sex_mapping = {"H": "XX", "M": "XO"}
    metadata["Subject"]["c_elegans_sex"] = lab_sex_mapping[this_subject_info["sex"]]

    metadata["Subject"]["strain"] = this_subject_info["public_strain"]
    metadata["Subject"]["genotype"] = "WT"
    metadata["Subject"]["age"] = "P1D"
    metadata["Subject"]["growth_stage"] = this_subject_info["growth_stage"]
    metadata["Subject"]["cultivation_temp"] = 20.0

    conversion_options = {
        "PumpProbeImagingInterfaceGreen": {"stub_test": testing},
        "PumpProbeImagingInterfaceRed": {"stub_test": testing},
        "PumpProbeSegmentationInterfaceGreed": {"stub_test": testing},
        "PumpProbeSegmentationInterfaceRed": {"stub_test": testing},
        "NeuroPALImagingInterface": {"stub_test": testing},
    }

    if testing:
        stub_folder_path = nwb_output_folder_path.parent / "stub_nwbfiles"
        stub_folder_path.mkdir(exist_ok=True)
        nwbfile_path = stub_folder_path / f"{session_string}_stub.nwb"
    else:
        # Name and nest the file in a DANDI compliant way
        subject_folder_path = nwb_output_folder_path / f"sub-{subject_id}"
        subject_folder_path.mkdir(exist_ok=True)
        dandi_session_string = session_string.replace("_", "-")
        nwbfile_path = subject_folder_path / f"sub-{subject_id}_ses-{dandi_session_string}.nwb"

    converter.run_conversion(
        nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True, conversion_options=conversion_options
    )
