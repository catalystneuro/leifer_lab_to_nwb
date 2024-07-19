# leifer-lab-to-nwb

Conversion scripts and command line utilities for converting data from the Leifer lab PumpProbe system to NeurodataWithoutBorders (NWB) format.

Includes the publication Neural signal propagation atlas of Caenorhabditis elegans (Nature, 2023).



## Recommendation: Use from a clean, standalone environment

For maximum reliability and stability, it is recommended to use this software in its own conda environment to avoid conflicts with other packages installed on the same system.

Begin by installing [Anaconda](https://www.anaconda.com/download#), then create a new environment by running:

```bash
conda create --name <name of environment> --no-default-packages
```

where you may choose whatever convention you prefer for setting environment names. I like to tag the name with the date of creation for easy reference, such as `leifer_lab_to_nwb_created_7_17_2024`.

You can then activate the isolated environment with:

```bash
conda activate <name of environment>
```

You may also need to install `git` and `pip` using:

```bash
conda install git pip --yes
```



## Installation

In the isolated environment, install this package by calling:

```bash
git clone https://github.com/catalystneuro/leifer_lab_to_nwb
```

then navigate into the `leifer_lab_to_nwb` directory and call:

```bash
pip install .
```

Then to install the specific set of dependencies for a particular conversion, such as `randi_nature_2023`:

```bash
pip install .[randi_nature_2023]
```



## Usage: convert a single session of your experiment

### Command line interface

To use the command line interface, simply copy and paste the following, then adjust to your local paths, subject ID:

```bash
pump_probe_to_nwb --base_folder_path D:/Leifer --subject_info_file_path D:/Leifer/all_subjects_metadata.yaml --subject_id 26 --nwb_output_folder_path D:/Leifer/nwbfiles
```

This will write the full NWB file, but if you just want to do a quick test you can add the `--testing` flag to the end. I recommend doing this, but keeping the resulting files in a separate 'throw-away' directory, such as:

```bash
pump_probe_to_nwb --subject_info_file_path D:/Leifer/all_subjects_metadata.yaml --subject_id 26 --nwb_output_folder_path D:/Leifer/nwbfiles --testing
```

though you should note that files produced in this way will not save in the `nwb_output_folder_path`, but rather in a folder adjacent to it marked as `nwb_testing`.

If you ever have any question about how to use the command line interface, you can invoke:

```bash
pump_probe_to_nwb --help
```

to quickly reference the various options.

### Python script

Alternatively, you can also run the conversion directly via a Python script - just search for the [`convert_session.py`](https://github.com/catalystneuro/leifer_lab_to_nwb/blob/main/src/leifer_lab_to_nwb/randi_nature_2023/convert_session.py) file in your local copy of the repository, and follow instructions at the top of the file to adjust the parameters.



## Upload to DANDI

To upload to the [DANDI Archive](https://dandiarchive.org/), again create and use an isolated environment, such as:

```bash
conda create --name dandi_upload_created_7_17_2024 --no-default-packages
```
```bash
conda activate dandi_upload_created_7_17_2024
```
```bash
pip install .[dandi]
```

This, in particular, will have to be updated periodically to keep the version requirements within ranges expected by their server (the recommendation being to create a new environment each time; you can cleanup older or unused environments using `conda env remove --name < name of old environment to remove >`).

First, navigate to the directory containing the NWB output folder specified above. If you have not already downloaded a local partial copy of the dandiset you wish to upload to, then start by calling:

```bash
dandi download DANDI:< dandiset ID >  --download dandiset.yaml
```

For example, for the dandiset https://dandiarchive.org/dandiset/001075, you would call

```bash
dandi download DANDI:001075  --download dandiset.yaml
```

Next, navigate into the directory created and call:

```bash
dandi organize ../<NWB output folder>
```

validate the files using:

```bash
dandi validate .
```

and if there are any invalidations, raise an issue on this repository. Then to upload, call:

```bash
dandi upload
```

and double-check the DANDI website to ensure the files show up after the upload bar reaches completion.
