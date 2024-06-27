import pathlib
from typing import Literal

import numpy
import pandas
import pynwb.ophys
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

        self.channel_name = channel_name

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

        # Technically every frame at every depth has a timestamp (and these are in the source MicroscopySeries)
        # But the fluorescence is aggregated per volume (over time) and so the timestamps are averaged over those frames
        timestamps_file_path = pumpprobe_folder_path / "framesDetails.txt"
        timestamps_table = pandas.read_table(filepath_or_buffer=timestamps_file_path, index_col=False)
        timestamps = numpy.array(timestamps_table["Timestamp"])

        averaged_timestamps = numpy.empty(shape=self.signal_info.data[0], dtype=numpy.float64)
        z_of_frame_lengths = [len(entry) for entry in self.brains_info["zOfFrame"]]
        cumulative_sum_of_lengths = numpy.cumsum(z_of_frame_lengths)
        for volume_index, (z_of_frame_length, cumulative_sum) in enumerate(
            zip(z_of_frame_lengths, cumulative_sum_of_lengths)
        ):
            start_frame = cumulative_sum - z_of_frame_length
            end_frame = cumulative_sum
            averaged_timestamps[volume_index] = numpy.mean(timestamps[start_frame:end_frame])

        self.timestamps_per_volume = averaged_timestamps

    def add_to_nwbfile(
        self,
        *,
        nwbfile: NWBFile,
        metadata: dict | None = None,
        stub_test: bool = False,
        stub_frames: int = 70,
    ) -> None:
        # TODO: probably centralize this in a helper function
        if "Microscope" not in nwbfile.devices:
            microscope = ndx_microscopy.Microscope(name="Microscope")
            nwbfile.add_device(devices=microscope)
        else:
            microscope = nwbfile.devices["Microscope"]

        if "PumpProbeImagingSpace" not in nwbfile.lab_meta_data:
            imaging_space = ndx_microscopy.PlanarImagingSpace(
                name="PumpProbeImagingSpace", description="", microscope=microscope
            )
            nwbfile.add_lab_meta_data(lab_meta_data=imaging_space)
        else:
            imaging_space = nwbfile.lab_meta_data["PumpProbeImagingSpace"]

        plane_segmentation = ndx_microscopy.MicroscopyPlaneSegmentation(
            name=f"PumpProbe{self.channel_name}PlaneSegmentation",
            description=(
                "The PumpProbe segmentation of the C. elegans brain. "
                "Only some of these local ROI IDs match the NeuroPAL IDs with cell labels. "
                "Note that the Z-axis of the `voxel_mask` is in reference to the index of that depth in its scan cycle."
            ),
            imaging_space=imaging_space,
        )
        plane_segmentation.add_column(
            name="neuropal_ids",
            description=(
                "The NeuroPAL ROI ID that has been matched to this PumpProbe ID. Blank means the ROI was not matched."
            ),
        )

        # There are coords for each 'nInVolume', but only the ones for the span of the 30th frame are used
        number_of_rois = self.signal_info.data.shape[1]
        labeled_frame_index = 30
        sub_start = sum(self.brains_info["nInVolume"][:labeled_frame_index])
        sub_coordinates = self.brains_info["coordZYX"][sub_start : (sub_start + number_of_rois)]

        number_of_rois = self.brains_info["nInVolume"][labeled_frame_index]
        for pump_probe_roi_id in range(number_of_rois):
            coordinate_info = sub_coordinates[pump_probe_roi_id]
            coordinates = (coordinate_info[2], coordinate_info[1], coordinate_info[0], 1.0)

            plane_segmentation.add_row(
                id=pump_probe_roi_id,
                voxel_mask=[coordinates],  # TODO: add rest of box
                neuropal_ids=self.brains_info["labels"][labeled_frame_index][pump_probe_roi_id].replace(" ", ""),
            )

        # TODO: might prefer to combine plane segmentations over image segmentation objects
        # to reduce clutter
        image_segmentation = ndx_microscopy.MicroscopyImageSegmentation(
            name=f"PumpProbe{self.channel_name}ImageSegmentation", microscopy_plane_segmentations=[plane_segmentation]
        )

        ophys_module = neuroconv.tools.nwb_helpers.get_module(nwbfile=nwbfile, name="ophys")
        ophys_module.add(image_segmentation)

        plane_segmentation_region = pynwb.ophys.DynamicTableRegion(
            name=f"PumpProbe{self.channel_name}PlaneSegmentationRegion",
            description="",
            data=[x for x in range(number_of_rois)],
            table=plane_segmentation,
        )
        roi_response_series = RoiResponseSeries(
            name=f"{self.channel_name}RoiResponseSeries",
            description=(
                f"Average baseline fluorescence for the '{self.channel_name}' optical channel extracted from the raw "
                "imaging and averaged over a volume defined as a complete scan cycle over volumetric depths."
            ),
            data=self.signal_info.data,
            rois=plane_segmentation_region,
            unit="n.a.",
            timestamps=self.timestamps_per_volume,
        )

        fluorescence = Fluorescence(roi_response_series=roi_response_series)
        ophys_module.add(fluorescence)
