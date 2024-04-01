import json
import pathlib

import neuroconv
import pandas
import pynwb
from pydantic import DirectoryPath


class ExtraOphysMetadataInterface(neuroconv.BaseDataInterface):
    """A custom interface for adding extra table metadata for the ophys rig."""

    def __init__(self, *, folder_path: DirectoryPath) -> None:
        """
        A custom interface for adding extra table metadata for the ophys rig.

        Parameters
        ----------
        folder_path : DirectoryPath
            Path to the raw pumpprobe folder.
        """
        folder_path = pathlib.Path(folder_path)

        super().__init__(folder_path=folder_path)

        self.z_scan_file_path = folder_path / "zScan.json"
        with open(file=self.z_scan_file_path, mode="r") as fp:
            self.z_scan = json.load(fp=fp)

        self.sync_table_file_path = folder_path / "other-frameSynchronous.txt"
        self.sync_table = pandas.read_table(filepath_or_buffer=self.sync_table_file_path, index_col=False)

    def get_metadata(self) -> dict:
        metadata = super().get_metadata("OnePhotonSeries")

        # Hardcoded in https://github.com/leiferlab/wormdatamodel/blob/282e780bc3c473791cc8d3b3fe9a18cee3c70e62/wormdatamodel/data/recording.py#L29
        um_per_pixel = 0.42

        volume_height_units = self.z_scan["volumeHeightUnits"]
        assert self.z_scan["volumeHeightUnits"] == "um", (
            f"Found an occurence of field 'volumeHeightUnits' in file '{self.z_scan_file_path}' that is not "
            f"'um' (value is '{volume_height_units}' instead)."
        )
        um_per_depth = self.z_scan["volumeHeight"]  # TODO: Should it be this or V/um?

        metadata["Ophys"]["grid_spacing"] = (um_per_pixel, um_per_pixel, um_per_depth)

    def add_to_nwbfile(self, nwbfile: pynwb.NWBFile):
        # zScan contents

        # Mapping from source names to NWB style (verbose snake case)
        # Some fields are excluded here because they are a part of core metadata
        z_scan_to_nwb_names = {
            "latencyShiftPermutation": "latency_shift_permutation",
            "etlCalibrationMindpt": "etl_calibration_min_depth",
            "etlCalibrationMaxdpt": "etl_calibration_max_depth",
            "piezoEtlClockLock": "piezo_etl_clock_lock",
            "etl dpt/um": "etl_depth_per_micrometer",
            "etlVMin": "etl_vmin",
            "etlVMax": "etl_vmax",
            "waveType": "waveform_type",
            "waveform": "waveform",
        }
        volume_scanning_column_descriptions = {
            "latency_shift_permutation": "",
            "etl_calibration_min_depth": "",
            "etl_calibration_max_depth": "",
            "piezo_etl_clock_lock": "",
            "etl_depth_per_micrometer": "",
            "etl_vmin": "",
            "etl_vmax": "",
            "waveform_type": "The generic shape of the waveform.",
            "waveform": "The full signature of the waveform",  # TODO, what units?
        }

        volume_scanning_table = pynwb.file.DynamicTable(
            name="VolumeScanningDetails", description="Custom parameterizations of the volume scanning device."
        )
        for name, description in volume_scanning_column_descriptions.items():
            volume_scanning_table.add_column(name=name, description=description)
        table_values = {
            z_scan_to_nwb_names[key]: value for key, value in self.z_scan.items() if key in z_scan_to_nwb_names
        }
        volume_scanning_table.add_row(**table_values)

        # Volume scanning direction
        # TODO: what does this mean? up vs. down?
        # TODO: could include as a simple TimeSeries with same timestamps as volumetric photon series but values 1, -1

        # Extra frameSynchronous information
        frame_sync_to_nwb_names = {
            "Piezo position (V)": "piezo_position_in_volume",
            "Piezo direction (+-1)": "piezo_direction",
            "Ludl X": "ludl_x",
            "Ludl Y": "ludl_y",
        }
        frame_sync_scanning_column_descriptions = {
            "piezo_position_in_volume": "",
            "piezo_direction": "",
            "ludl_x": "",
            "ludl_y": "",
        }

        # TODO: unpack frameSync content, likely as several TimeSeries with same timestamps as volumetric photon series
        # Wil require some reshaping into the volumes since these are flattened frames

        # volume_scanning_table = pynwb.file.DynamicTable(
        #     name="Piezo", description="Custom parameterizations of the volume scanning device."
        # )
        # for name, description in volume_scanning_column_descriptions.items():
        #     volume_scanning_table.add_column(name=name, description=description)
        # table_values = {
        #     z_scan_to_nwb_names[key]: value for key, value in self.z_scan.items() if key in z_scan_to_nwb_names
        # }
        # volume_scanning_table.add_row(**table_values)
