import pathlib
from typing import Union

import ndx_microscopy
import ndx_patterned_ogen
import neuroconv
import numpy
import pandas
import pynwb


class OptogeneticStimulationInterface(neuroconv.BaseDataInterface):

    def __init__(self, *, pumpprobe_folder_path: str | pathlib.Path):
        """
        A custom interface for the two photon optogenetic stimulation data.

        Parameters
        ----------
        pumpprobe_folder_path : DirectoryPath
            Path to the raw pumpprobe folder.
        """
        pumpprobe_folder_path = pathlib.Path(pumpprobe_folder_path)

        optogenetic_stimulus_file_path = pumpprobe_folder_path / "pharosTriggers.txt"
        self.optogenetic_stimulus_table = pandas.read_table(
            filepath_or_buffer=optogenetic_stimulus_file_path, index_col=False
        )

        timestamps_file_path = pumpprobe_folder_path / "framesDetails.txt"
        self.timestamps_table = pandas.read_table(filepath_or_buffer=timestamps_file_path, index_col=False)
        self.timestamps = numpy.array(self.timestamps_table["Timestamp"])

    def add_to_nwbfile(
        self,
        *,
        nwbfile: pynwb.NWBFile,
        metadata: Union[dict, None] = None,
    ) -> None:
        if "Microscope" not in nwbfile.devices:
            microscope = ndx_microscopy.Microscope(name="Microscope")
            nwbfile.add_device(devices=microscope)
        else:
            microscope = nwbfile.devices["Microscope"]

        light_source = ndx_patterned_ogen.LightSource(
            name="AmplifiedLaser",
            description=(
                "For two-photon optogenetic targeting, we used an optical parametric amplifier "
                "(OPA; Light Conversion ORPHEUS) pumped by a femtosecond amplified laser (Light Conversion PHAROS)."
            ),
            model="ORPHEUS amplifier and PHAROS laser",
            manufacturer="Light Conversion",
            stimulation_wavelength_in_nm=850.0,
            filter_description="Short pass at 1040 nm",
            peak_power_in_W=1.2 / 1e3,  # Hardcoded from the paper
            pulse_rate_in_Hz=500e3,  # Hardcoded from the paper
        )
        nwbfile.add_device(light_source)

        site = ndx_patterned_ogen.PatternedOptogeneticStimulusSite(
            name="PatternedOptogeneticStimulusSite",
            description="Scanning",  # TODO
            excitation_lambda=850.0,  # nm
            effector="GUR-3/PRDX-2",
            location="whole brain",
            device=microscope,
            light_source=light_source,
        )
        nwbfile.add_ogen_site(site)

        temporal_focusing = ndx_patterned_ogen.TemporalFocusing(
            name="TemporalFocusing",
            description=(
                "We used temporal focusing to spatially restrict the size of the two-photon excitation spot along the "
                "microscope axis. A motorized iris was used to set its lateral size. For temporal focusing, the "
                "first-order diffraction from a reflective grating, oriented orthogonally to the microscope axis, "
                "was collected and travelled through the motorized iris, placed on a plane conjugate to the grating."
                "To arbitrarily position the two-photon excitation spot in the sample volume, the beam then travelled "
                "through an electrically tunable lens (Optotune EL-16-40-TC, on a plane conjugate to the objective), "
                "to set its position along the microscope axis, and finally was reflected by two galvo-mirrors to set "
                "its lateral position. The pulsed beam was then combined with the imaging light path by a dichroic "
                "mirror immediately before entering the back of the objective."
            ),
            # Calculated manually from the 'source data' of Supplementary Figure 2a
            # https://www.nature.com/articles/s41586-023-06683-4#MOESM10
            lateral_point_spread_function_in_um="(-0.245, 0.059) ± (0.396, 0.264)",
            axial_point_spread_function_in_um="0.444 ± 0.536",
        )
        nwbfile.add_lab_meta_data(temporal_focusing)

        # Assume all targets are unique; if retargeting of the same location is ever enabled, it would be nice
        # to refactor this to make proper reuse of target locations.
        optical_channel = pynwb.ophys.OpticalChannel(  # TODO: I really wish I didn't need this...
            name="DummyOpticalChannel",
            description="A dummy optical channel for ndx-patterned-ogen metadata.",
            emission_lambda=numpy.nan,
        )
        imaging_plane = nwbfile.create_imaging_plane(
            name="TargetImagingPlane",
            description="The targeted plane.",
            indicator="",
            location="whole brain",
            excitation_lambda=numpy.nan,
            device=microscope,
            optical_channel=optical_channel,
        )
        targeted_plane_segmentation = pynwb.ophys.PlaneSegmentation(
            name="TargetPlaneSegmentation",
            description="Table for storing the target centroids, defined by a one-voxel mask.",
            imaging_plane=imaging_plane,
        )
        targeted_plane_segmentation.add_column(name="depth_in_um", description="Targeted depth in micrometers.")
        for target_x_index, target_y_index, depth_in_um in zip(
            self.optogenetic_stimulus_table["optogTargetX"],
            self.optogenetic_stimulus_table["optogTargetY"],
            self.optogenetic_stimulus_table["optogTargetZ"],
        ):
            targeted_plane_segmentation.add_roi(
                pixel_mask=[(int(target_x_index), int(target_y_index), 1.0)], depth_in_um=depth_in_um
            )

        image_segmentation = pynwb.ophys.ImageSegmentation(name="TargetedImageSegmentation")
        image_segmentation.add_plane_segmentation(targeted_plane_segmentation)

        ophys_module = neuroconv.tools.nwb_helpers.get_module(nwbfile=nwbfile, name="ophys")
        ophys_module.add(image_segmentation)

        # Hardcoded duration from the methods section of paper
        # TODO: may have to adjust this for unc-31 mutant strain subjects
        stimulus_duration_in_s = 500.0 / 1e3
        stimulus_start_times_in_s = self.timestamps[
            self.optogenetic_stimulus_table["frameCount"] - self.timestamps_table["frameCount"][0]
        ]
        stimulus_table = ndx_patterned_ogen.PatternedOptogeneticStimulusTable(
            name="OptogeneticStimulusTable",
            description=(
                "Every 30 seconds, a random neuron was selected among the neurons found in the current volumetric "
                "image, on the basis of only its tagRFP-T signal. After galvo-mirrors and the tunable lens set the "
                "position of the two-photon spot on that neuron, a 500-ms (300-ms for the unc-31-mutant strain) "
                "train of light pulses was used to optogenetically stimulate that neuron. The duration of stimulus "
                "illumination for the unc-31-mutant strain was selected to elicit calcium transients in stimulated "
                "neurons with a distribution of amplitudes such that the maximum amplitude was similar to those in "
                "WT-background animals. The output of the laser was controlled through the external interface to its "
                "built-in pulse picker, and the power of the laser at the sample was 1.2mW at 500kHz. Neuron "
                "identities were assigned to stimulated neurons after the completion of experiments using NeuroPAL."
            ),
        )
        for index, start_time_in_s in enumerate(stimulus_start_times_in_s):
            targeted_roi_reference = targeted_plane_segmentation.create_roi_table_region(
                name="targeted_rois", description="The targeted ROI.", region=[index]
            )
            # TODO: create a container of targets so they don't all get dumped to outer level of general
            stimulus_target = ndx_patterned_ogen.OptogeneticStimulusTarget(
                name=f"OptogeneticStimulusTarget{index}", targeted_rois=targeted_roi_reference
            )
            nwbfile.add_lab_meta_data(stimulus_target)

            stimulus_table.add_interval(
                start_time=start_time_in_s,
                stop_time=start_time_in_s + stimulus_duration_in_s,
                targets=stimulus_target,
                stimulus_pattern=temporal_focusing,
                stimulus_site=site,
                power=1.2 / 1e3,  # Hardcoded from the paper; TODO: should be 'power_in_W'
            )
        nwbfile.add_time_intervals(stimulus_table)
