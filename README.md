# leifer_lab_to_nwb

Conversion scripts and command line utilities for converting data from the Leifer lab PumpProbe system to NeurodataWithoutBorders (NWB) format.

Includes the publication Neural signal propagation atlas of Caenorhabditis elegans (Nature, 2023).



## Recommendation: Use from a clean, standalone environment

For maximum reliability and stability, it is recommended to use this software in its own conda environment to avoid conflicts with other packages installed on the same system.

Begin by installing [Anaconda](https://www.anaconda.com/download#), then create a new environment.

Be sure to install this environment in a location that has enough disk space by using the `--prefix` flag:

```bash
conda create --prefix < folder path >/leifer_lab_to_nwb_< today's date > --no-default-packages --yes
```

where the `folder path` is a mounted drive with ample space instead of your user's home directory. For example:

```bash
conda create --prefix /mnt/data/leifer_lab_to_nwb_7_25_2024 --no-default-packages --yes
```

I recommend tagging the name of the environment with the date reference to make it easier to tell if the environment might be out of date. I recommend creating a new fresh environment every few months.

You can then confirm the environment was installed by calling:

```bash
conda env list
```

from which you should be able to see the environment that was just created. You can then activate this isolated environment with:

```bash
conda activate < folder path >/leifer_lab_to_nwb_< date reference >
```

For example:

```bash
conda activate /mnt/data/leifer_lab_to_nwb_7_25_2024
```



## Installation

The first time you activate the isolated environment, begin by installing:

```bash
conda install git pip --yes
```

then install the rest of the package by calling:

```bash
git clone https://github.com/catalystneuro/leifer_lab_to_nwb
cd leifer_lab_to_nwb
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

### Command Line Interface (CLI)

If you ever have any questions about how to use the CLI, you can invoke:

```bash
pump_probe_to_nwb --help
```

to quickly reference the various options.

The main way of calling the CLI is to simply copy and paste the following, then adjust to your local paths and subject ID:

```bash
pump_probe_to_nwb \
  --base_folder_path D:/Leifer \
  --subject_info_file_path D:/Leifer/all_subjects_metadata.yaml \
  --subject_id 26 \
  --nwb_output_folder_path D:/Leifer/nwbfiles \
  --testing
```

Note that the `--testing` flag on the end there only writes a small NWB file to 'test' that the pipeline is working correctly.

To perform the full data conversion, simply remove the `--testing` flag:

```bash
pump_probe_to_nwb \
  --base_folder_path D:/Leifer \
  --subject_info_file_path D:/Leifer/all_subjects_metadata.yaml \
  --subject_id 26 \
  --nwb_output_folder_path D:/Leifer/nwbfiles
```



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

First, fetch your DANDI API credential from the top-right corner of the [archive website](https://dandiarchive.org/) (your initials) and set them as an environment variable.

On Windows, you can either set it once in the command line using:

```bash
set DANDI_API_KEY=< paste API key here >
```

or you can save it permanently on the device via the control panel. On UNIX, the command is:

```bash
export DANDI_API_KEY=< paste API key here >
```

Then, navigate to the directory containing the NWB output folder specified during the file conversion. If you have not already downloaded a local partial copy of the dandiset you wish to upload to, then start by calling:

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
