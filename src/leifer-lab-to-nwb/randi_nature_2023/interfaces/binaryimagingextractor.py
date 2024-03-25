"""Generic class for reading imaging data from a binary file."""

import numpy
from pydantic import FilePath
from roiextractors import ImagingExtractor


# TODO: propagate
class BinaryImagingExtractor(ImagingExtractor):
    """A generic class for reading binary imaging data."""

    def __init__(self, *, file_path: FilePath, dtype: str, shape: Union[], offset: int = 0, order: Literal["C", "F"] = "C") -> None:
        super().__init__(file_path=file_path, dtype=dtype, shape=shape, offset=offset, order=order)
        self._memmap = numpy.memmap(filename=file_path, dtype=dtype, shape=shape, offset=offset, order=order, mode="r")

    @abstractmethod
    def get_image_size(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def get_num_frames(self) -> int:
        pass

    @abstractmethod
    def get_sampling_frequency(self) -> float:
        pass

    @abstractmethod
    def get_channel_names(self) -> list:
        """List of  channels in the recoding.

        Returns
        -------
        channel_names: list
            List of strings of channel names
        """
        pass

    @abstractmethod
    def get_num_channels(self) -> int:
        """Total number of active channels in the recording

        Returns
        -------
        no_of_channels: int
            integer count of number of channels
        """
        pass

    def get_dtype(self) -> str:
        return self._kwargs["dtype"]

    @abstractmethod
    def get_video(
        self, start_frame: Optional[int] = None, end_frame: Optional[int] = None, channel: int = 0
    ) -> np.ndarray:
        pass
