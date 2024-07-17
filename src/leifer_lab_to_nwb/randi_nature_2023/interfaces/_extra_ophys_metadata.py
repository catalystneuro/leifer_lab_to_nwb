import json
import pathlib

import neuroconv
import pandas
import pynwb


class ExtraOphysMetadataInterface(neuroconv.BaseDataInterface):

    def __init__(self, *, pumpprobe_folder_path: str | pathlib.Path) -> None:
        """
        A custom interface for adding extra table metadata for the ophys rig.

        Parameters
        ----------
        pumpprobe_folder_path : DirectoryPath
            Path to the raw pumpprobe folder.
        """
        pumpprobe_folder_path = pathlib.Path(pumpprobe_folder_path)

        z_scan_file_path = pumpprobe_folder_path / "zScan.json"
        with open(file=z_scan_file_path, mode="r") as fp:
            self.z_scan = json.load(fp=fp)

        sync_table_file_path = pumpprobe_folder_path / "other-frameSynchronous.txt"
        self.sync_table = pandas.read_table(filepath_or_buffer=sync_table_file_path, index_col=False)

    def add_to_nwbfile(self, nwbfile: pynwb.NWBFile, metadata: dict):
        # Plane depths
        # volt_per_um = 0.125  # Hardcoded value by the lab
        # depth_in_um_per_pixel = 0.42  # Hardcoded value by the lab

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
            name="VolumeScanningConfiguration", description="Custom parameterizations of the volume scanning device."
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
        # frame_sync_to_nwb_names = {
        #     "Piezo position (V)": "piezo_position_in_volume",
        #     "Piezo direction (+-1)": "piezo_direction",
        #     "Ludl X": "ludl_x",
        #     "Ludl Y": "ludl_y",
        # }
        # frame_sync_scanning_column_descriptions = {
        #     "piezo_position_in_volume": "",
        #     "piezo_direction": "",
        #     "ludl_x": "",
        #     "ludl_y": "",
        # }

        # TODO: unpack frameSync content, likely as several TimeSeries with same timestamps as volumetric photon series
        # Will require some reshaping into the volumes since these are flattened frames

        # volume_scanning_table = pynwb.file.DynamicTable(
        #     name="Piezo", description="Custom parameterizations of the volume scanning device."
        # )
        # for name, description in volume_scanning_column_descriptions.items():
        #     volume_scanning_table.add_column(name=name, description=description)
        # table_values = {
        #     z_scan_to_nwb_names[key]: value for key, value in self.z_scan.items() if key in z_scan_to_nwb_names
        # }
        # volume_scanning_table.add_row(**table_values)
