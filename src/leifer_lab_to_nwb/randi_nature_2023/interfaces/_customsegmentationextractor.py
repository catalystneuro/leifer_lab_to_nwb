import pickle
from typing import Iterable, Literal, Tuple, Union

import numpy
from pydantic import FilePath
from roiextractors import SegmentationExtractor


class CustomSegmentationExtractor(SegmentationExtractor):
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

        with open(file=file_path, mode="rb") as file:
            self._signal = pickle.load(file=file)

        self.roi_response_raw = self._signal.data
        self._image_mask

    def get_accepted_list(self) -> list:
        return list(range(self.roi_response_raw.shape[1]))

    def get_rejected_list(self) -> list:
        return list()

    def get_image_size(self) -> Tuple[int, int]:
        return self._image_size

    def get_sampling_frequency(self) -> float:
        if self._kwargs["sampling_frequency"] is None:
            raise ValueError(
                "This ImagingExtractor does not have a constant sampling frequency! Use `get_timestamps` instead."
            )

        return self._kwargs["sampling_frequency"]

    def get_timestamps(self) -> Iterable[float]:
        if self._kwargs["timestamps"] is None:
            raise ValueError(
                "This ImagingExtractor does not have timestamps set! Use `get_sampling_frequency` instead."
            )

        return self._kwargs["timestamps"]

    def get_channel_names(self) -> list:
        raise NotImplementedError

    def get_num_channels(self) -> int:
        return 1

    def get_dtype(self) -> str:
        return self._kwargs["dtype"]

    def get_video(
        self, start_frame: Union[int, None] = None, end_frame: Union[int, None] = None, channel: int = 0
    ) -> numpy.ndarray:
        return self._memmap[start_frame:end_frame, ...]
