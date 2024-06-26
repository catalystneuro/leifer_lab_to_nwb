import pickle
from typing import Iterable, Literal, Tuple, Union

import numpy
from pydantic import FilePath
from roiextractors import SegmentationExtractor


class PumpProbeSegmentationExtractor(SegmentationExtractor):
    """A very custom segmentation extractor for the .pickle files that correspond to wormdatamodel objects."""

    def __init__(
        self,
        *,
        file_path: FilePath,
        timestamps: Iterable[float],
        image_shape: Tuple[int, int],
    ) -> None:
        super().__init__()
        self._file_path = file_path
        self._times = timestamps
        self._image_shape = image_shape

        self._channel_names = [self._file_path.stem.upper()]

        with open(file=file_path, mode="rb") as file:
            self._all_pickled_info = pickle.load(file=file)

        self._roi_response_raw = self._all_pickled_info.data

        # TODO: this isn't quite true, I don't think it's normalized
        self._roi_response_dff = self._all_pickled_info.derivative

        # TODO
        number_of_rois = self._roi_response_raw.shape[1]
        self._image_masks = numpy.zeros(shape=(self._image_shape[0], self._image_shape[1], number_of_rois), dtype=bool)

    def get_accepted_list(self) -> list:
        return list(range(self._roi_response_raw.shape[1]))

    def get_rejected_list(self) -> list:
        return list()

    def get_image_size(self) -> Tuple[int, int]:
        return self._image_shape

    # TODO: might want to load these from brains file
    def get_roi_ids(self) -> list:
        return super().get_roi_ids()

    def get_channel_names(self) -> list:
        return self._channel_names
