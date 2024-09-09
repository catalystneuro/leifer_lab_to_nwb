import json
import pathlib
import pickle
import warnings
from typing import Literal

import ndx_microscopy
import neuroconv
import numpy
import pandas
import pydantic
import pynwb

from ._globals import _DEFAULT_CHANNEL_NAMES
from ._box_utils import _calculate_voxel_mask


class PumpProbeSegmentationInterface(neuroconv.basedatainterface.BaseDataInterface):

    def __init__(
        self, *, pump_probe_folder_path: pydantic.DirectoryPath, channel_name: Literal[_DEFAULT_CHANNEL_NAMES]
    ):
        """
        A custom interface for the raw volumetric pumpprobe data.

        Parameters
        ----------
        pump_probe_folder_path : DirectoryPath
            Path to the pumpprobe folder.
        """
        super().__init__(pump_probe_folder_path=pump_probe_folder_path, channel_name=channel_name)
        pump_probe_folder_path = pathlib.Path(pump_probe_folder_path)

        self.channel_name = channel_name

        # Other interfaces use CamelCase to refer to the NWB object the channel data will end up as
        # The files on the other hand are all lower case
        lower_channel_name = channel_name.lower()
        signal_file_path = pump_probe_folder_path / f"{lower_channel_name}.pickle"
        with open(file=signal_file_path, mode="rb") as io:
            self.signal_info = pickle.load(file=io)

        # Ignore ref_index from the mask info since that varies quite a bit (it's the frame index used for labels)
        # And strip extra version attachments
        mask_type_info = {key: self.signal_info.info[key] for key in ["method", "version"]}
        mask_type_info["version"] = mask_type_info["version"].split("-")[0]
        all_expected_mask_type_info = [
            {"method": "box", "version": "v1.0"},  # Seen in earlier; usually .dirty; might still produce similar boxes
            {"method": "box", "version": "1.5"},  # The gold standard example; from the Fig. 1 data
        ]
        assert mask_type_info in all_expected_mask_type_info, (
            "Unimplemented method detected for mask type."
            f"\n\nFull signal info: {json.dumps(obj=self.signal_info.info, indent=2)}"
            "\n\nPlease raise an issue to have the new mask type incorporated."
        )

        # Load the local box shape mapping
        box_shape_file_path = pathlib.Path(__file__).parent.parent / "session_to_box_shape.json"
        with open(file=box_shape_file_path, mode="r") as io:
            box_shape_mapping = json.load(fp=io)
        self.box_shape = box_shape_mapping[pump_probe_folder_path.name]

        # Load general ROI metadata
        brains_file_path = pump_probe_folder_path / "brains.json"
        with open(brains_file_path, "r") as io:
            self.brains_info = json.load(fp=io)

        # Technically every frame at every depth has a timestamp (and these are in the source MicroscopySeries)
        # But the fluorescence is aggregated per volume (over time) and so the timestamps are averaged over those frames
        timestamps_file_path = pump_probe_folder_path / "framesDetails.txt"
        timestamps_table = pandas.read_table(filepath_or_buffer=timestamps_file_path, index_col=False)
        timestamps = numpy.array(timestamps_table["Timestamp"])

        averaged_timestamps = numpy.empty(shape=self.signal_info.data.shape[0], dtype=numpy.float64)
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
        nwbfile: pynwb.NWBFile,
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
                name="PumpProbeImagingSpace",
                description="The variable-depth imaging space scanned by the PumpProbe system.",
                microscope=microscope,
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
        plane_segmentation.add_column(name="centroids", description="The centroids of each ROI.")
        plane_segmentation.add_column(
            name="neuropal_ids",
            description=(
                "The NeuroPAL ROI ID that has been matched to this PumpProbe ID. Blank means the ROI was not matched."
            ),
        )

        # In most sessions, the labeled frame index is fixed to be the 30th frame
        # But there are many others where this is not the case
        labeled_frame_indices = [
            index for index, frame_labels in enumerate(self.brains_info["labels"]) if len(frame_labels) != 0
        ]
        if len(labeled_frame_indices) == 0:
            raise ValueError("No labeled frames found in the 'brains.json' file.")
        if len(labeled_frame_indices) > 1:
            raise ValueError("More than one labeled frame in the 'brains.json' file.")
        labeled_frame_index = labeled_frame_indices[0]

        # Check for possible file mismatches based on recorded metadata
        if self.signal_info.info["ref_index"] != labeled_frame_index:
            message = (
                "Mismatch in the labeled frame index between the signal "
                f"({self.signal_info.info['ref_index']}) and brains ({labeled_frame_index}) files!"
            )
            raise ValueError(message)

        # There are coords for each 'nInVolume', but only the ones for the span of the labeled frames are used
        number_of_rois_from_signal = self.signal_info.data.shape[1]
        number_of_rois_from_brains = self.brains_info["nInVolume"][labeled_frame_index]
        if number_of_rois_from_signal != number_of_rois_from_brains:
            message = (
                "Mismatch in the number of ROIs between the signal "
                f"({number_of_rois_from_signal}) and brains ({number_of_rois_from_brains}) files!"
            )
            raise ValueError(message)
        number_of_rois = number_of_rois_from_signal

        sub_start = sum(self.brains_info["nInVolume"][:labeled_frame_index])
        sub_coordinates = self.brains_info["coordZYX"][sub_start : (sub_start + number_of_rois)]

        mask_type = self.signal_info.info["method"]
        if mask_type == "weightedMask":
            message = (
                "Detected ROI mask type 'weightedMask' - because the associated 'weights' have never been seen "
                "dumped to the 'analysis.log', we cannot reconstruct the proper NWB voxel masks."
                "Only the centroids will be written as the mask coordinates."
            )
            warnings.warn(message=message, stacklevel=3)

        for pump_probe_roi_id in range(number_of_rois):
            centroid_info = sub_coordinates[pump_probe_roi_id]
            centroid = (centroid_info[2], centroid_info[1], centroid_info[0])

            if mask_type == "box" and tuple(self.box_shape) not in ((1, 3, 3), (3, 5, 5), (5, 5, 5)):
                message = f"Box shape {self.box_shape} has not been implemented."
                raise NotImplementedError(message)

            if mask_type == "box":
                voxel_mask = _calculate_voxel_mask(
                    centroid_zyx=centroid_info, box_shape=self.box_shape, method=mask_type
                )
            elif mask_type == "weightedMask":
                voxel_mask = [centroid]

            plane_segmentation.add_row(
                id=pump_probe_roi_id,
                voxel_mask=voxel_mask,
                centroids=[centroid],
                neuropal_ids=self.brains_info["labels"][labeled_frame_index][pump_probe_roi_id].replace(" ", ""),
            )

        image_segmentation = ndx_microscopy.MicroscopySegmentations(
            name=f"PumpProbe{self.channel_name}Segmentations", microscopy_plane_segmentations=[plane_segmentation]
        )

        ophys_module = neuroconv.tools.nwb_helpers.get_module(nwbfile=nwbfile, name="ophys")
        ophys_module.add(image_segmentation)

        plane_segmentation_region = pynwb.ophys.DynamicTableRegion(
            name="table_region",  # Name must be exactly this
            description="",
            data=[x for x in range(number_of_rois)],
            table=plane_segmentation,
        )
        microscopy_response_series = ndx_microscopy.MicroscopyResponseSeries(
            name=f"{self.channel_name}Signal",
            description=(
                f"Average baseline fluorescence for the '{self.channel_name}' optical channel extracted from the raw "
                "imaging and averaged over a volume defined as a complete scan cycle over volumetric depths."
            ),
            data=self.signal_info.data[:stub_frames, :],
            table_region=plane_segmentation_region,
            unit="n.a.",
            timestamps=self.timestamps_per_volume[:stub_frames],
        )

        # TODO: should probably combine all of these into a single container
        container = ndx_microscopy.MicroscopyResponseSeriesContainer(
            name=f"{self.channel_name}Signals", microscopy_response_series=[microscopy_response_series]
        )
        ophys_module.add(container)
