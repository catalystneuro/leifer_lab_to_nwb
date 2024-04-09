from typing import Union

import ndx_multichannel_volume
import neuroconv
import pynwb


class RandiNature2023Converter(neuroconv.ConverterPipe):
    def run_conversion(
        self,
        nwbfile_path: Union[str, None] = None,
        nwbfile: Union[pynwb.NWBFile, None] = None,
        metadata: Union[dict, None] = None,
        overwrite: bool = False,
        conversion_options: Union[dict, None] = None,
    ) -> pynwb.NWBFile:
        if metadata is None:
            metadata = self.get_metadata()
        self.validate_metadata(metadata=metadata)

        metadata_copy = dict(metadata)
        subject_metadata = metadata_copy.pop("Subject")  # Must remove from base metadata
        ibl_subject = ndx_multichannel_volume.CElegansSubject(**subject_metadata)

        conversion_options = conversion_options or dict()
        self.validate_conversion_options(conversion_options=conversion_options)

        with neuroconv.tools.nwb_helpers.make_or_load_nwbfile(
            nwbfile_path=nwbfile_path,
            nwbfile=nwbfile,
            metadata=metadata_copy,
            overwrite=overwrite,
            verbose=self.verbose,
        ) as nwbfile_out:
            nwbfile_out.subject = ibl_subject
            for interface_name, data_interface in self.data_interface_objects.items():
                data_interface.add_to_nwbfile(
                    nwbfile=nwbfile_out, metadata=metadata_copy, **conversion_options.get(interface_name, dict())
                )

        return nwbfile_out
