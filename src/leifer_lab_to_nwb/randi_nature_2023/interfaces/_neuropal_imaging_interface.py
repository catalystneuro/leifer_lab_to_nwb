import json
import pathlib
import shutil
from typing import Literal

import ndx_microscopy
import neuroconv
import numpy
import pandas
import pynwb
from pydantic import DirectoryPath


class NeuroPALImagingInterface(neuroconv.basedatainterface.BaseDataInterface):
    """Custom interface for automatically setting metadata and conversion options for this experiment."""

    def __init__(self, *, multicolor_folder_path: DirectoryPath) -> None:
        """
        A custom interface for the raw volumetric PumpProbe data.

        Parameters
        ----------
        multicolor_folder_path : directory
            Path to the multicolor folder.
        """
        super().__init__(multicolor_folder_path=multicolor_folder_path)
        multicolor_folder_path = pathlib.Path(multicolor_folder_path)

        # If the device setup is ever changed, these may need to be exposed as keyword arguments
        dtype = numpy.dtype("uint16")
        frame_shape = (2048, 2048)
        number_of_channels = 4
        number_of_depths = 26

        # This file always has a few bytes on the end that make it not automatically reshapable as expected
        # No clue where it comes from but they ignore those bytes even in their own processing code
        dat_file_path = multicolor_folder_path / "frames-2048x2048.dat"
        unshaped_data = numpy.memmap(filename=dat_file_path, dtype=dtype, mode="r")
        clipped_data = unshaped_data[: number_of_channels * number_of_depths * frame_shape[0] * frame_shape[1]]

        # The reshape here still preserves the memory map
        self.data_shape = (number_of_depths, number_of_channels, frame_shape[0], frame_shape[1])
        shaped_data = clipped_data.reshape(self.data_shape)

        self.data = shaped_data

        brains_file_path = multicolor_folder_path / "brains.json"
        with open(brains_file_path, "r") as io:
            self.brains_info = json.load(fp=io)

        # Some basic homogeneity checks
        assert len(self.brains_info["nInVolume"]) == 1, "Only one labeling is supported."
        assert (
            len(self.brains_info["nInVolume"]) == len(self.brains_info["zOfFrame"])
            and len(self.brains_info["zOfFrame"]) == len(self.brains_info["labels"])
            and len(self.brains_info["labels"]) == len(self.brains_info["labels_confidences"])
            and len(self.brains_info["labels_confidences"]) == len(self.brains_info["labels_comments"])
        ), "Mismatch in JSON substructure lengths."
        assert (
            self.brains_info["nInVolume"][0] == len(self.brains_info["labels"][0])
            and self.brains_info["nInVolume"][0] == len(self.brains_info["labels_confidences"][0])
            and self.brains_info["nInVolume"][0] == len(self.brains_info["labels_comments"][0])
        ), "Length of contents does not match number of ROIs."

        # Additional homogeneity check for imaging compatability
        json_depth_length = len(self.brains_info["zOfFrame"][0])
        assert (
            json_depth_length == number_of_depths
        ), f"Mismatch between length of 'zOfFrame' ({json_depth_length}) and number of depths ({number_of_depths})."

    def add_to_nwbfile(
        self,
        *,
        nwbfile: pynwb.NWBFile,
        metadata: dict | None = None,
        stub_test: bool = False,
        stub_depths: int = 3,
    ) -> None:
        # TODO: enhance all metadata
        if "Microscope" not in nwbfile.devices:
            microscope = ndx_microscopy.Microscope(name="Microscope")
            nwbfile.add_device(devices=microscope)
        else:
            microscope = nwbfile.devices["Microscope"]

        if "LightSource" not in nwbfile.devices:
            light_source = ndx_microscopy.MicroscopyLightSource(name="LightSource")
            nwbfile.add_device(devices=light_source)
        else:
            light_source = nwbfile.devices["LightSource"]

        if "NeuroPALImagingSpace" not in nwbfile.lab_meta_data:
            imaging_space = ndx_microscopy.VolumetricImagingSpace(
                name="NeuroPALImagingSpace", description="", microscope=microscope
            )
            nwbfile.add_lab_meta_data(lab_meta_data=imaging_space)
        else:
            imaging_space = nwbfile.lab_meta_data["PlanarImagingSpace"]

        # TODO: confirm the order of the channels in the data
        neuropal_channel_names = ["mtagBFP2", "CyOFP1.5", "tagRFP-T", "mNeptune2.5"]
        optical_channels = list()
        light_sources = list()
        for channel_name in neuropal_channel_names:
            light_source = ndx_microscopy.MicroscopyLightSource(name=f"{channel_name}LightSource")
            nwbfile.add_device(devices=light_source)
            light_sources.append(light_source)

            optical_channel = ndx_microscopy.MicroscopyOpticalChannel(
                name=f"{channel_name}Filter", description="", indicator=channel_name
            )
            nwbfile.add_lab_meta_data(lab_meta_data=optical_channel)
            optical_channels.append(optical_channel)

        # Not exposing chunking/buffering control here for simplicity; note that a single frame is about 8 MB
        chunk_shape = (1, 1, self.data_shape[-2], self.data_shape[-1])

        # Best we can do is limit the number of depths that are written by stub
        imaging_data = self.data if not stub_test else self.data[:stub_depths, :, :, :]
        data_iterator = neuroconv.tools.hdmf.SliceableDataChunkIterator(data=imaging_data, chunk_shape=chunk_shape)

        depth_per_frame_in_um = self.brains_info["zOfFrame"][0]

        multi_channel_microscopy_volume = ndx_microscopy.VariableDepthMultiChannelMicroscopyVolume(
            name="NeuroPALImaging",
            description="",
            microscope=microscope,
            light_sources=light_sources[0],  # TODO
            imaging_space=imaging_space,
            optical_channels=optical_channels[0],  # TODO
            data=data_iterator,
            depth_per_frame_in_um=depth_per_frame_in_um,
            unit="n.a.",
        )
        nwbfile.add_acquisition(multi_channel_microscopy_volume)
