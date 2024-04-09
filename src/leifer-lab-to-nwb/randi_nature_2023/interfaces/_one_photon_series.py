import pathlib
from typing import Union

import numpy
import pandas
from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import (
    BaseImagingExtractorInterface,
)
from pydantic import DirectoryPath
from pynwb import NWBFile


class OnePhotonSeriesInterface(BaseImagingExtractorInterface):
    """Custom interface for automatically setting metadata and conversion options for this experiment."""

    ExtractorModuleName = "leifer_lab_to_nwb.randi_nature_2023.interfaces.binaryimagingextractor"  # TODO: propagate
    ExtractorName = "BinaryImagingExtractor"

    def __init__(self, *, folder_path: DirectoryPath):
        """
        A custom interface for the raw volumetric pumpprobe data.

        Parameters
        ----------
        folder_path : DirectoryPath
            Path to the raw pumpprobe folder.
        """
        folder_path = pathlib.Path(folder_path)
        dat_file_path = next(folder_path.glob("*.dat"))
        assert (
            "U16" in dat_file_path.stem
        ), "Raw .dat file '{dat_file_path}' does not indicate uint16 dtype in filename."
        dtype = numpy.dtype("uint16")
        frame_shape = tuple(int(value) for value in dat_file_path.stem.split("_")[-1].split("x"))

        timestamps_file_path = folder_path / "framesDetails.txt"
        timestamps_table = pandas.read_table(filepath_or_buffer=timestamps_file_path, index_col=False)
        number_of_frames = timestamps_table.shape[0]
        timestamps = numpy.array(timestamps_table["Timestamp"])

        volume_partitions_file_path = folder_path / "other-volumeMetadataUtilities.txt"
        volume_partitions_table = pandas.read_table(filepath_or_buffer=volume_partitions_file_path, index_col=False)
        number_of_depths = volume_partitions_table.shape[0]

        shape = (number_of_frames, frame_shape[0], frame_shape[1], number_of_depths)

        super.__init__(file_path=dat_file_path, dtype=dtype, shape=shape, timestamps=timestamps)

    def get_metadata(self) -> dict:
        return super().get_metadata(photon_series_type="OnePhotonSeries")

    def get_metadata_schema(self) -> dict:
        return super().get_metadata(photon_series_type="OnePhotonSeries")

    def add_to_nwbfile(
        self,
        *,
        nwbfile: NWBFile,
        metadata: Union[dict, None] = None,
        photon_series_index: int = 0,
        stub_test: bool = False,
        stub_frames: int = 100,
    ) -> None:
        super().add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            photon_series_index=photon_series_index,
            stub_test=stub_test,
            stub_frames=stub_frames,
            photon_series_type="OnePhotonSeries",
            parent_container="acquisition",
        )
