import json
import pathlib

import ndx_multichannel_volume
import neuroconv
import pandas
import pynwb
from pydantic import FilePath


class SubjectInterface(neuroconv.BaseDataInterface):
    """A custom interface for adding extra subject metadata from the logbook."""

    def __init__(self, *, file_path: FilePath, session_id: str) -> None:
        """
        A custom interface for adding extra subject metadata from the logbook.

        Parameters
        ----------
        file_path : FilePath
            Path to the logbook for this session.
        """
        file_path = pathlib.Path(file_path)

        super().__init__(file_path=file_path, session_id=session_id)

        with open(file=file_path, mode="r") as io:
            self.logbook = io.readlines()

    def add_to_nwbfile(self, nwbfile: pynwb.NWBFile):
        session_id = self.source_data["session_id"]

        logbook_growth_stage_mapping = {
            "L4": "L4",
            "young adult": "YA",
            "L4/ya": "YA",  # TODO: consult them on how to handle this case
        }

        subject_start_line = self.logbook

        subject = ndx_multichannel_volume.CElegansSubject(
            subject_id=session_id,  # Sessions are effectively defined by the subject number on that day
            description="",  # TODO: find something from paper
            species="Caenorhabditis elegans",
            growth_stage=logbook_growth_stage_mapping[growth_stage],
            strain=strain,
        )
        nwbfile.subject = subject
