import copy
from typing import Union

import ndx_subjects
import neuroconv
import pynwb
from pydantic import FilePath

from leifer_lab_to_nwb.randi_nature_2023.interfaces import (
    NeuroPALImagingInterface,
    NeuroPALSegmentationInterface,
    OptogeneticStimulationInterface,
    PumpProbeImagingInterface,
    PumpProbeSegmentationInterface,
)


class RandiNature2023Converter(neuroconv.NWBConverter):
    data_interface_classes = {
        "PumpProbeImagingInterfaceGreen": PumpProbeImagingInterface,
        "PumpProbeImagingInterfaceRed": PumpProbeImagingInterface,
        "PumpProbeSegmentationInterfaceGreed": PumpProbeSegmentationInterface,
        "PumpProbeSegmentationInterfaceRed": PumpProbeSegmentationInterface,
        "NeuroPALImagingInterface": NeuroPALImagingInterface,
        "NeuroPALSegmentationInterface": NeuroPALSegmentationInterface,
        "OptogeneticStimulationInterface": OptogeneticStimulationInterface,
    }

    def get_metadata_schema(self) -> dict:
        base_metadata_schema = super().get_metadata_schema()

        # Suppress special Subject field validations
        metadata_schema = copy.deepcopy(base_metadata_schema)
        metadata_schema["properties"].pop("Subject")

        return metadata_schema

    def run_conversion(
        self,
        nwbfile_path: FilePath | None = None,
        nwbfile: pynwb.NWBFile | None = None,
        metadata: dict | None = None,
        overwrite: bool = False,
        conversion_options: dict | None = None,
    ) -> pynwb.NWBFile:
        if metadata is None:
            metadata = self.get_metadata()
        self.validate_metadata(metadata=metadata)

        metadata_copy = dict(metadata)
        subject_metadata = metadata_copy.pop("Subject")  # Must remove from base metadata
        subject = ndx_subjects.CElegansSubject(**subject_metadata)

        conversion_options = conversion_options or dict()
        self.validate_conversion_options(conversion_options=conversion_options)

        with neuroconv.tools.nwb_helpers.make_or_load_nwbfile(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata_copy,
            overwrite=overwrite,
            verbose=self.verbose,
        ) as nwbfile_out:
            nwbfile_out.subject = subject
            for interface_name, data_interface in self.data_interface_objects.items():
                data_interface.add_to_nwbfile(
                    nwbfile=nwbfile_out, metadata=metadata_copy, **conversion_options.get(interface_name, dict())
                )

        return nwbfile_out
