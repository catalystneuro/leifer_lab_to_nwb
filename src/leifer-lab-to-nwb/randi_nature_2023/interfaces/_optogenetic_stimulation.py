import pathlib
from typing import Union

import numpy
import pandas
import neuroconv
import pynwb
import ndx_patterned_ogen
from pydantic import DirectoryPath


class OptogeneticStimulationInterface(neuroconv.BaseDataInterface):
    """Custom interface for the two photon optogenetic stimulation data."""

    def __init__(self, *, folder_path: DirectoryPath):
        """
        A custom interface for the two photon optogenetic volumetric pumpprobe data.

        Parameters
        ----------
        folder_path : DirectoryPath
            Path to the raw pumpprobe folder.
        """
        folder_path = pathlib.Path(folder_path)

        self.optogenetic_stimulus_file_path = folder_path / "pharosTriggers.txt"
        self.optogenetic_stimulus_table = pandas.read_table(
            filepath_or_buffer=self.optogenetic_stimulus_file_path, index_col=False
        )

        self.timestamps_file_path = folder_path / "framesDetails.txt"
        self.timestamps_table = pandas.read_table(filepath_or_buffer=self.timestamps_file_path, index_col=False)
        self.timestamps = numpy.array(self.timestamps_table["Timestamp"])

    def add_to_nwbfile(
        self,
        *,
        nwbfile: pynwb.NWBFile,
        metadata: Union[dict, None] = None,
        photon_series_index: int = 0,
        stub_test: bool = False,
        stub_frames: int = 100,
    ) -> None:
        assert "Microscope" in nwbfile.devices, (
            "The `Microscope` must be added before this interface! Make sure the call to "
            "`.run_conversion` for this interface occurs after the `OnePhotonSeriesInterface`."
        )
        microscope = nwbfile.devices["Microscope"]

        assert "PlaneSegmentation" in nwbfile.processing["ophys"], (
            "The `PlaneSegmentation` must be added before this interface! Make sure the call to "
            "`.run_conversion` for this interface occurs after the `OnePhotonSeriesInterface`."
        )
        plane_segmentation = nwbfile.processing["ophys"]["PlaneSegmentation"]

        pharos_device = pynwb.Device(name="PHAROSLaser", description="")
        nwbfile.add_device(device=pharos_device)

        light_source = ndx_patterned_ogen.LightSource(
            name="AmplifiedLaser",
            description=(
                "For two-photon optogenetic targeting, we used an optical parametric amplifier "
                "(OPA; Light Conversion ORPHEUS) pumped by a femtosecond amplified laser (Light Conversion PHAROS)."
            ),
            model="ORPHEUS amplifier and PHAROS laser",
            manufacturer="Light Conversion",
            stimulation_wavelength=850.0,  # nm
            filter_description="Short pass at 1040 nm",
            peak_power=1.2 / 1e3,  # Hardcoded from the paper
            # intensity=0.005,  # TODO: issue raised
            pulse_rate=500e3,  # Hardcoded from the paper
        )
        nwbfile.add_device(light_source)

        site = ndx_patterned_ogen.PatternedOptogeneticStimulusSite(
            name="PatternedOptogeneticStimulusSite",
            description="Scanning",
            excitation_lambda=850.0,  # nm
            effector="GUR-3/PRDX-2",
            location="whole-brain",
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
            lateral_point_spread_function="9 um ± 0.7 um",  # TODO
            axial_point_spread_function="32 um ± 1.6 um",  # TODO
        )
        nwbfile.add_lab_meta_data(temporal_focusing)

        # TODO: utilize objective registration
        # for index,
        #     target = OptogeneticStimulusTarget(name=f"Target{index}", targeted_rois=targeted_rois_1)
        #     targets.append(target)
        #     nwbfile.add_lab_meta_data(target)

        # Hardcoded duration from the methods section of paper
        # TODO: may have to adjust this for unc-31 mutant strain subjects
        stimulus_duration_in_s = 500.0 / 1e3
        stimulus_start_times_in_s = self.timestamps[
            self.optogenetic_stimulus_table["frameCount"] - self.timestamps_table["frameCount"][0]
        ]
        stimulus_table = ndx_patterned_ogen.PatternedOptogeneticStimulusTable(
            name="OptogeneticStimulusTable",
            description=(
                "Every 30 seconds, a random neuron was selected among the neurons found in the current volumetric "
                "image, on the basis of only its tagRFP-T signal. After galvo-mirrors and the tunable lens set the "
                "position of the two-photon spot on that neuron, a 500-ms (300-ms for the unc-31-mutant strain) "
                "train of light pulses was used to optogenetically stimulate that neuron. The duration of stimulus "
                "illumination for the unc-31-mutant strain was selected to elicit calcium transients in stimulated "
                "neurons with a distribution of amplitudes such that the maximum amplitude was similar to those in "
                "WT-background animals. The output of the laser was controlled through the external interface to its "
                "built-in pulse picker, and the power of the laser at the sample was 1.2 mW at 500 kHz. Neuron "
                "identities were assigned to stimulated neurons after the completion of experiments using NeuroPAL."
            ),
        )
        for index, start_time_in_s in enumerate(stimulus_start_times_in_s):
            stimulus_table.add_interval(
                start_time=start_time_in_s,
                stop_time=start_time_in_s + stimulus_duration_in_s,
                targets=nwbfile.lab_meta_data[f"Target{index}"],
                stimulus_pattern=temporal_focusing,
                stimulus_site=site,
            )
