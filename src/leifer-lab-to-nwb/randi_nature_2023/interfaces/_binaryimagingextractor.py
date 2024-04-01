from typing import Tuple, Literal, Union, Iterable

import numpy
from pydantic import FilePath
from roiextractors import ImagingExtractor


# TODO: propagate to ROIExtractors
class BinaryImagingExtractor(ImagingExtractor):
    """A generic class for reading binary imaging data."""

    def __init__(
        self,
        *,
        file_path: FilePath,
        dtype: str,
        shape: Tuple[int, int, int],
        starting_time: Union[float, None] = None,
        sampling_frequency: Union[float, None] = None,
        timestamps: Union[Iterable[float], None] = None,
        offset: int = 0,
        order: Literal["C", "F"] = "C",
    ) -> None:
        if sampling_frequency is None and timestamps is None:
            raise ValueError("At least one of `sampling_frequency` or `timestamps` must be specified.")
        if sampling_frequency is not None and starting_time is None:
            raise ValueError("Since `sampling_frequency` was specified, please also specify the `starting_time`.")

        super().__init__(
            file_path=file_path,
            dtype=dtype,
            shape=shape,
            starting_time=starting_time,
            sampling_frequency=sampling_frequency,
            timestamps=timestamps,
            offset=offset,
            order=order,
        )
        self._memmap = numpy.memmap(filename=file_path, dtype=dtype, shape=shape, offset=offset, order=order, mode="r")

    def get_image_size(self) -> Tuple[int, int]:
        return self._kwargs["shape"][1:]

    def get_num_frames(self) -> int:
        return self._kwargs["shape"][0]

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
