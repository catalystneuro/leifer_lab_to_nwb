import pathlib
import shutil
from typing import Literal

import ndx_microscopy
import neuroconv
import numpy
import pandas
import pynwb

_DEFAULT_CHANNEL_NAMES = ["Green", "Red"]
_DEFAULT_CHANNEL_FRAME_SLICING = {
    "Green": (slice(0, 512), slice(0, 512)),
    "Red": (slice(512, 1024), slice(0, 512)),
}


class PumpProbeImagingInterface(neuroconv.basedatainterface.BaseDataInterface):

    def __init__(
        self,
        *,
        pumpprobe_folder_path: str | pathlib.Path,
        channel_name: Literal[_DEFAULT_CHANNEL_NAMES] | str,
        channel_frame_slicing: tuple[slice, slice] | None = None,
    ) -> None:
        """
        A custom interface for the raw volumetric PumpProbe data.

        Parameters
        ----------
        pumpprobe_folder_path : directory
            Path to the pumpprobe folder.
        channel_name : either of "GreenChannel", "RedChannel" or an arbitrary string
            The name given to the optical channel responsible for collecting this data.
            The two allowed defaults determine other properties automatically; but when specifying an arbitrary string,
            you will need to specify the other information (slicing range, wavelength metadata, etc.) manually.
        channel_frame_slicing : tuple of slices, optional
            If the `channel_name` is not one of the defaults, then then you must specify how to slice the frame
            to extract the data for this channel.

            The default slicing is:
                GreenChannel=(slice(0, 512), slice(0, 512))
                RedChannel=(slice(512, 1024), slice(0, 512))
        """
        super().__init__(
            pumpprobe_folder_path=pumpprobe_folder_path,
            channel_name=channel_name,
            channel_frame_slicing=channel_frame_slicing,
        )
        if channel_name not in _DEFAULT_CHANNEL_NAMES and channel_frame_slicing is None:
            raise ValueError(
                f"A custom `optical_channel_name` was specified ('{channel_name}') and was not one of the "
                f"known defaults ('{_DEFAULT_CHANNEL_NAMES}'), but no frame slicing pattern was passed."
            )

        self.channel_name = channel_name
        self.channel_frame_slicing = channel_frame_slicing or _DEFAULT_CHANNEL_FRAME_SLICING[channel_name]

        pumpprobe_folder_path = pathlib.Path(pumpprobe_folder_path)

        # If the device setup is ever changed, these may need to be exposed as keyword arguments
        dtype = numpy.dtype("uint16")
        frame_shape = (1024, 512)

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

        # This was hardcoded via discussion in
        # https://github.com/catalystneuro/leifer_lab_to_nwb/issues/2
        depth_scanning_piezo_volts_to_um = 1 / 0.125
        self.series_depth_per_frame_in_um = numpy.array(
            sync_subtable["Piezo position (V)"] * depth_scanning_piezo_volts_to_um
        )

        full_shape = (number_of_frames, frame_shape[0], frame_shape[1])

        dat_file_path = pumpprobe_folder_path / "sCMOS_Frames_U16_1024x512.dat"
        self.imaging_data_memory_map = numpy.memmap(filename=dat_file_path, dtype=dtype, mode="r", shape=full_shape)

        # This slicing operation *should* be lazy since it does not usually include fancy indexing
        full_slice = (slice(0, number_of_frames), self.channel_frame_slicing[0], self.channel_frame_slicing[1])
        self.imaging_data_for_channel = self.imaging_data_memory_map[full_slice]

        self.data_shape = (
            number_of_frames,
            full_slice[1].stop - full_slice[1].start,
            full_slice[2].stop - full_slice[2].start,
        )

    def add_to_nwbfile(
        self,
        *,
        nwbfile: pynwb.NWBFile,
        metadata: dict | None = None,
        stub_test: bool = False,
        stub_frames: int = 70,
    ) -> None:
        # TODO: enhance all metadata
        if "Microscope" not in nwbfile.devices:
            microscope = ndx_microscopy.Microscope(name="Microscope")
            nwbfile.add_device(devices=microscope)
        else:
            microscope = nwbfile.devices["Microscope"]

        if "MicroscopyLightSource" not in nwbfile.devices:
            light_source = ndx_microscopy.MicroscopyLightSource(name="MicroscopyLightSource")  # TODO
            nwbfile.add_device(devices=light_source)
        else:
            light_source = nwbfile.devices["MicroscopyLightSource"]

        if "PlanarImagingSpace" not in nwbfile.lab_meta_data:
            imaging_space = ndx_microscopy.PlanarImagingSpace(
                name="PlanarImagingSpace", description="", microscope=microscope
            )
            nwbfile.add_lab_meta_data(lab_meta_data=imaging_space)
        else:
            imaging_space = nwbfile.lab_meta_data["PlanarImagingSpace"]

        optical_channel = ndx_microscopy.MicroscopyOpticalChannel(name=self.channel_name, description="", indicator="")
        nwbfile.add_lab_meta_data(lab_meta_data=optical_channel)

        # Not exposing chunking/buffering control here for simplicity; but this is where they would be passed
        num_frames = self.data_shape[0] if not stub_test else stub_frames
        x = self.data_shape[1]
        y = self.data_shape[2]
        frame_size_bytes = x * y * self.imaging_data_for_channel.dtype.itemsize
        chunk_size_bytes = 10.0 * 1e6  # 10 MB default
        num_frames_per_chunk = int(chunk_size_bytes / frame_size_bytes)
        chunk_shape = (max(min(num_frames_per_chunk, num_frames), 1), x, y)

        imaging_data = self.imaging_data_for_channel if not stub_test else self.imaging_data_for_channel[:stub_frames]
        data_iterator = neuroconv.tools.hdmf.SliceableDataChunkIterator(data=imaging_data, chunk_shape=chunk_shape)

        timestamps = self.timestamps if not stub_test else self.timestamps[:stub_frames]

        variable_depth_microscopy_series = ndx_microscopy.VariableDepthMicroscopySeries(
            name=f"PumpProbeImaging{self.channel_name}",
            description="",  # TODO
            microscope=microscope,
            light_source=light_source,
            imaging_space=imaging_space,
            optical_channel=optical_channel,
            data=data_iterator,
            depth_per_frame_in_um=self.series_depth_per_frame_in_um,
            unit="n.a.",
            timestamps=timestamps,
        )
        nwbfile.add_acquisition(variable_depth_microscopy_series)
