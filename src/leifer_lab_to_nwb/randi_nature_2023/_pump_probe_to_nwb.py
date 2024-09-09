"""Main code definition for the conversion of a full session (including NeuroPAL)."""

import datetime
import warnings
import typing

import yaml
import dateutil.tz
import pydantic

from ._randi_nature_2023_converter import RandiNature2023Converter


@pydantic.validate_call
def pump_probe_to_nwb(
    *,
    base_folder_path: pydantic.DirectoryPath,
    subject_info_file_path: pydantic.FilePath,
    subject_id: int,
    nwb_output_folder_path: pydantic.DirectoryPath,
    raw_or_processed: typing.Literal["raw", "processed"],
    testing: bool = False,
    skip_existing: bool = True,
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

        Note that files produced in this way will not save in the `nwb_output_folder_path`, but rather in a folder
        adjacent to it marked as `nwb_testing`.
    """
    with open(file=subject_info_file_path, mode="r") as stream:
        all_subject_info = yaml.safe_load(stream=stream)
    subject_info = all_subject_info[subject_id]

    session_folder_path = base_folder_path / str(subject_info["date"])
    pump_probe_folder_path = session_folder_path / subject_info["pump_probe_folder"]
    multicolor_folder_path = session_folder_path / subject_info["multicolor_folder"]

    if pump_probe_folder_path.exists() is False:
        message = f"Could not find source data at '{pump_probe_folder_path}' - skipping!"
        warnings.warn(message=message, stacklevel=3)
        return None

    # Parse session start time from the pumpprobe path
    session_string = pump_probe_folder_path.stem.removeprefix("pumpprobe_")
    session_start_time = datetime.datetime.strptime(session_string, "%Y%m%d_%H%M%S")
    session_start_time = session_start_time.replace(tzinfo=dateutil.tz.gettz("US/Eastern"))

    subject_id_from_start_time = session_start_time.strftime("%y%m%d")
    subject_id = str(subject_info.get("subject_id", subject_id_from_start_time))

    session_type = "imaging" if raw_or_processed == "raw" else "segmentation"
    if testing is True:
        stub_folder_path = nwb_output_folder_path / "stubs"
        stub_folder_path.mkdir(exist_ok=True)
        nwbfile_path = stub_folder_path / f"{session_string}_stub_{session_type}.nwb"
    else:
        # Name and nest the file in a DANDI compliant way
        subject_folder_path = nwb_output_folder_path / f"sub-{subject_id}"
        subject_folder_path.mkdir(exist_ok=True)
        dandi_session_string = session_string.replace("_", "-")
        dandi_filename = f"sub-{subject_id}_ses-{dandi_session_string}_desc-{session_type}_ophys+ogen.nwb"
        nwbfile_path = subject_folder_path / dandi_filename

    if skip_existing is True and nwbfile_path.exists():
        print(f"File at '{nwbfile_path}' exists - skipping!")
        return None

    if raw_or_processed == "raw":
        source_data = {
            "PumpProbeImagingInterfaceGreen": {
                "pump_probe_folder_path": pump_probe_folder_path,
                "channel_name": "Green",
            },
            "PumpProbeImagingInterfaceRed": {"pump_probe_folder_path": pump_probe_folder_path, "channel_name": "Red"},
            "NeuroPALImagingInterface": {"multicolor_folder_path": multicolor_folder_path},
        }
        conversion_options = {
            "PumpProbeImagingInterfaceGreen": {"stub_test": testing},
            "PumpProbeImagingInterfaceRed": {"stub_test": testing},
            "NeuroPALImagingInterface": {"stub_test": testing},
        }
    elif raw_or_processed == "processed":
        source_data = {
            "PumpProbeSegmentationInterfaceGreed": {
                "pump_probe_folder_path": pump_probe_folder_path,
                "channel_name": "Green",
            },
            "PumpProbeSegmentationInterfaceRed": {
                "pump_probe_folder_path": pump_probe_folder_path,
                "channel_name": "Red",
            },
            "NeuroPALSegmentationInterface": {"multicolor_folder_path": multicolor_folder_path},
            "OptogeneticStimulationInterface": {"pump_probe_folder_path": pump_probe_folder_path},
        }
        conversion_options = {
            "PumpProbeSegmentationInterfaceGreed": {"stub_test": testing},
            "PumpProbeSegmentationInterfaceRed": {"stub_test": testing},
        }

    converter = RandiNature2023Converter(source_data=source_data, verbose=False)

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

    metadata["Subject"]["subject_id"] = subject_id

    subject_description = ""
    if growth_stage_comments := subject_info.get("growth_stage_comments", "none") != "none":
        subject_description += f"Growth stage comments: {growth_stage_comments}\n"
    if other_comments := subject_info.get("other_comments", "none") != "none":
        subject_description += f"Other comments: {other_comments}\n"
    if subject_description != "":
        metadata["Subject"]["description"] = subject_description

    metadata["Subject"]["species"] = "Caenorhabditis elegans"
    metadata["Subject"]["age"] = "P1D"  # Could use 'days_on_dex' from the subject info file, but is it ever not 1?
    metadata["Subject"]["sex"] = "O"
    metadata["Subject"]["c_elegans_sex"] = "XX" if subject_info.get("sex", "H") == "H" else "XO"
    metadata["Subject"]["strain"] = subject_info.get("public_strain", "AKS471.2.d")
    metadata["Subject"]["genotype"] = "WT"
    metadata["Subject"]["growth_stage"] = subject_info.get("growth_stage", "L4")
    metadata["Subject"]["cultivation_temp"] = 20.0

    # Suppress false warning
    warnings.filterwarnings(action="ignore", message="The linked table for DynamicTableRegion*", category=UserWarning)

    converter.run_conversion(
        nwbfile_path=nwbfile_path, metadata=metadata, overwrite=True, conversion_options=conversion_options
    )

    return None
