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
conda install git pip
```



## Installation

In the isolated environment, install this package by calling:

```bash
git clone https://github.com/catalystneuro/leifer-lab-to-nwb
cd leifer-lab-to-nwb
pip install .
```

Then to install the specific set of dependencies for a particular conversion, such as `randi_nature_2023`:

```bash
pip install .[randi_nature_2023]
```



## Usage: convert a single session of your experiment

TODO



## Upload to DANDI

To upload to the [DANDI Archive](https://dandiarchive.org/), again create and use an isolated environment, such as:

```bash
conda create --name dandi_upload_created_7_17_2024 --no-default-packages
conda activate dandi_upload_created_7_17_2024

pip install leifer_lab_to_nwb[dandi]
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
