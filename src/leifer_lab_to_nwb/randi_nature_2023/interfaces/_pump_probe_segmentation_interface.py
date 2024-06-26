import pathlib
from typing import Literal

import numpy
import pandas
from neuroconv.datainterfaces.ophys.basesegmentationextractorinterface import (
    BaseSegmentationExtractorInterface,
)
from pydantic import DirectoryPath
from pynwb import NWBFile


class PumpProbeSegmentationInterface(BaseSegmentationExtractorInterface):
    ExtractorModuleName = "leifer_lab_to_nwb.randi_nature_2023.interfaces._pump_probe_segmentation_extractor"
    ExtractorName = "PumpProbeSegmentationExtractor"

    def __init__(self, *, pumpprobe_folder_path: DirectoryPath, channel_name: Literal["Green", "Red"] | str):
        """
        A custom interface for the raw volumetric pumpprobe data.

        Parameters
        ----------
        pumpprobe_folder_path : DirectoryPath
            Path to the pumpprobe folder.
        """
        pumpprobe_folder_path = pathlib.Path(pumpprobe_folder_path)

        # Other interfaces use CamelCase to refer to the NWB object the channel data will end up as
        # The files on the other hand are all lower case
        lower_channel_name = channel_name.lower()
        pickle_file_path = pumpprobe_folder_path / f"{lower_channel_name}.pickle"

        # TODO: generalize this timestamp extraction to a common utility function
        # From prototyping data, the frameSync seems to start first...
        sync_table_file_path = pumpprobe_folder_path / "other-frameSynchronous.txt"
        sync_table = pandas.read_table(filepath_or_buffer=sync_table_file_path, index_col=False)
        frame_indices = sync_table["Frame index"]

        # ...then the frameDetails has timestamps for a subset of the frame indices
        timestamps_file_path = pumpprobe_folder_path / "framesDetails.txt"
        timestamps_table = pandas.read_table(filepath_or_buffer=timestamps_file_path, index_col=False)
        number_of_frames = timestamps_table.shape[0]

        frame_count_delay = timestamps_table["frameCount"][0] - frame_indices[0]
        frame_count_end = frame_count_delay + number_of_frames

        sync_subtable = sync_table.iloc[frame_count_delay:frame_count_end]

        self.timestamps = numpy.array(timestamps_table["Timestamp"])

        # Hardcoding this for now
        image_shape = (512, 512)
        super().__init__(file_path=pickle_file_path, timestamps=self.timestamps, image_shape=image_shape)

        # Hardcode a special plane segmentation name for this interface
        # self.plane_segmentation_name = "PumpProbeSegmentation"

    # def get_metadata(self) -> dict:
    #     metadata = super().get_metadata()
    #
    #     # Hardcoded value from lab
    #     # This is also an average in a sense - the exact depth is tracked by the Piezo and written
    #     # as a custom DynamicTable in the ExtraOphysMetadataInterface
    #     depth_per_pixel = 0.42
    #
    #     # one_photon_metadata["Ophys"]["grid_spacing"] = (um_per_pixel, um_per_pixel, um_per_pixel)
    #
    #     metadata["Ophys"]["ImageSegmentation"]["plane_segmentations"][0]["name"] = self.plane_segmentation_name
    #
    #     metadata["Ophys"]["Fluorescence"]= {'name': 'Fluorescence', self.plane_segmentation_name: {'raw': {
    #         'name': 'BaselineSignal', 'description': 'Array of raw fluorescence traces.', 'unit': 'n.a.'}}}
    #     metadata["Ophys"]["DfOverF"] = {'name': 'Derivative', self.plane_segmentation_name: {
    #         'dff': {'name': 'DerivativeOfSignal', 'description': 'Array of filtered fluorescence traces; '
    #                                                              'approximately the derivative (unnormalized) of the '
    #                                                              'baseline signal'
    #                                                              '.', 'unit': 'n.a.'}}}
    #
    #     return metadata
    #
    # def get_metadata_schema(self) -> dict:
    #     return super().get_metadata(photon_series_type="OnePhotonSeries")

    # def add_to_nwbfile(
    #     self,
    #     *,
    #     nwbfile: NWBFile,
    #     metadata: dict | None = None,
    #     stub_test: bool = False,
    # ) -> None:
    #     super().add_to_nwbfile(
    #         nwbfile=nwbfile,
    #         metadata=metadata,
    #         stub_test=stub_test,
    #         plane_segmentation_name="PumpProbeSegmentation",
    #     )
