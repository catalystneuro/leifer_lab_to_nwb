import pathlib
from typing import Literal

import numpy
import pandas
from neuroconv.basedatainterface import BaseDataInterface
from pynwb import NWBFile


class PumpProbeSegmentationInterface(BaseDataInterface):

    def __init__(self, *, pumpprobe_folder_path: str | pathlib.Path, channel_name: Literal["Green", "Red"] | str):
        """
        A custom interface for the raw volumetric pumpprobe data.

        Parameters
        ----------
        pumpprobe_folder_path : DirectoryPath
            Path to the pumpprobe folder.
        """
        super().__init__(pumpprobe_folder_path=pumpprobe_folder_path, channel_name=channel_name)
        pumpprobe_folder_path = pathlib.Path(pumpprobe_folder_path)

        # Other interfaces use CamelCase to refer to the NWB object the channel data will end up as
        # The files on the other hand are all lower case
        lower_channel_name = channel_name.lower()
        signal_file_path = pumpprobe_folder_path / f"{lower_channel_name}.pickle"
        with open(file=signal_file_path, mode="rb") as io:
            self.signal_info = pickle.load(file=io)
        assert (
            self.signal_info["info"]["method"] == "box"
            and self.signal_info["info"]["ref_index"] == "30"
            and self.signal_info["info"]["version"] == "1.5"
        ), "Unimplemented method detected for mask type."

        brains_file_path = pumpprobe_folder_path / "brains.json"
        with open(brains_file_path, "r") as io:
            self.brains_info = json.load(fp=io)

        # Reshape coordinates to match more directly
        reshaped_xyz_coordinates = []
        counter = 0
        for number_of_rois_in_volume in self.brains_info["nInVolume"]:
            xyz_coordinates_per_volume = []
            for volume_index in range(number_of_rois_in_volume):
                xyz_coordinates_per_volume.append(
                    (
                        self.brains_info["coordZYX"][counter + volume_index][2],
                        self.brains_info["coordZYX"][counter + volume_index][1],
                        self.brains_info["coordZYX"][counter + volume_index][0],
                    )
                )

            reshaped_xyz_coordinates.append(xyz_coordinates_per_volume)
            counter += number_of_rois_in_volume

        # ...then the frameDetails has timestamps for a subset of the frame indices
        timestamps_file_path = pumpprobe_folder_path / "framesDetails.txt"
        timestamps_table = pandas.read_table(filepath_or_buffer=timestamps_file_path, index_col=False)

        self.timestamps = numpy.array(timestamps_table["Timestamp"])

        # Hardcoding this for now
        # image_shape = (512, 512)

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

    def add_to_nwbfile(
        self,
        *,
        nwbfile: NWBFile,
        metadata: dict | None = None,
        stub_test: bool = False,
        stub_frames: int = 70,
    ) -> None:
        pass
