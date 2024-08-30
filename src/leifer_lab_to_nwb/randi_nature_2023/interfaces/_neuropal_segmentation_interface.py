import json
import pathlib

import ndx_microscopy
import neuroconv
import pynwb
from neuroconv.basedatainterface import BaseDataInterface


class NeuroPALSegmentationInterface(BaseDataInterface):

    def __init__(self, *, multicolor_folder_path: str | pathlib.Path):
        """
        A custom interface for the raw volumetric NeuroPAL data.

        Parameters
        ----------
        multicolor_folder_path : DirectoryPath
            Path to the multicolor folder.
        """
        super().__init__(multicolor_folder_path=multicolor_folder_path)
        multicolor_folder_path = pathlib.Path(multicolor_folder_path)

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

    def add_to_nwbfile(
        self,
        *,
        nwbfile: pynwb.NWBFile,
        metadata: dict | None = None,
    ) -> None:
        # TODO: probably centralize this in a helper function
        if "Microscope" not in nwbfile.devices:
            microscope = ndx_microscopy.Microscope(name="Microscope")
            nwbfile.add_device(devices=microscope)
        else:
            microscope = nwbfile.devices["Microscope"]

        if "NeuroPALImagingSpace" not in nwbfile.lab_meta_data:
            imaging_space = ndx_microscopy.VolumetricImagingSpace(
                name="NeuroPALImagingSpace", description="", microscope=microscope
            )
            nwbfile.add_lab_meta_data(lab_meta_data=imaging_space)
        else:
            imaging_space = nwbfile.lab_meta_data["NeuroPALImagingSpace"]

        plane_segmentation = ndx_microscopy.MicroscopyPlaneSegmentation(
            name="NeuroPALPlaneSegmentation",
            description="The NeuroPAL segmentation of the C. elegans brain with cell labels.",
            imaging_space=imaging_space,
        )
        plane_segmentation.add_column(
            name="labels",
            description="The C. elegans cell names labeled from the NeuroPAL imaging.",
        )
        plane_segmentation.add_column(
            name="labels_confidences",
            description="The C. elegans cell names labeled from the NeuroPAL imaging.",
        )
        plane_segmentation.add_column(
            name="labels_comments",
            description="Various comments about the cell label classification process.",
        )

        number_of_rois = self.brains_info["nInVolume"][0]
        for neuropal_roi_id in range(number_of_rois):
            coordinate_info = self.brains_info["coordZYX"][neuropal_roi_id]
            coordinates = (coordinate_info[2], coordinate_info[1], coordinate_info[0], 1.0)

            plane_segmentation.add_row(
                id=neuropal_roi_id,
                voxel_mask=[coordinates],
                labels=self.brains_info["labels"][0][neuropal_roi_id],
                labels_confidences=self.brains_info["labels_confidences"][0][neuropal_roi_id],
                labels_comments=self.brains_info["labels_comments"][0][neuropal_roi_id],
            )

        image_segmentation = ndx_microscopy.MicroscopySegmentations(
            name="NeuroPALSegmentations", microscopy_plane_segmentations=[plane_segmentation]
        )

        ophys_module = neuroconv.tools.nwb_helpers.get_module(nwbfile=nwbfile, name="ophys")
        ophys_module.add(image_segmentation)
