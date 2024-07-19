"""Command line interface wrapper around the PumpProbe conversion function."""

import pathlib

import click
from pydantic import FilePath, DirectoryPath

from .convert_session import pump_probe_to_nwb


@click.command(name="pump_probe_to_nwb")
@click.option(
    "--base_folder_path",
    help="""
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
""",
    required=True,
    type=click.Path(writable=False),
)
@click.option(
    "--subject_info_file_path",
    help="The path to the subject log YAML file.",
    required=True,
    type=click.Path(writable=False),
)
@click.option(
    "--subject_id",
    help="ID of the subject in the YAML file - must be an integer, not a string.",
    required=True,
    type=int,
)
@click.option(
    "--nwb_output_folder_path",
    help="The folder path to save the NWB files to.",
    required=True,
    type=click.Path(writable=True),
)
@click.option(
    "--testing",
    help="Whether or not to 'test' the conversion process by limiting the amount of data written to the NWB file.",
    required=True,
    is_flag=True,
)
def _pump_probe_to_nwb_cli(
    *, subject_info_file_path: FilePath, subject_id: int, nwb_output_folder_path: DirectoryPath
) -> None:
    subject_info_file_path = pathlib.Path(subject_info_file_path)
    nwb_output_folder_path = pathlib.Path(nwb_output_folder_path)

    pump_probe_to_nwb(
        subject_info_file_path=subject_info_file_path,
        subject_id=subject_id,
        nwb_output_folder_path=nwb_output_folder_path,
    )
