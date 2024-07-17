# leifer-lab-to-nwb

Conversion scripts and command line utilities for converting data from the Leifer lab PumpProbe system to NeurodataWithoutBorders (NWB) format.

Includes the publication Neural signal propagation atlas of Caenorhabditis elegans (Nature, 2023).



## Recommendation: Use from a clean, standalone environment

For maximum reliability and stability, it is recommended to use this software in its own conda environment to avoid conflicts with other packages installed on the same system.

Begin by installing [Anaconda](https://www.anaconda.com/download#), then create a new environment by running:

```bash
conda create --name <name of environment> --no-default-packages --no-cache-dir
```

where you may choose whatever convention you prefer for setting environment names. I like to tag the name with the date of creation for easy reference, such as `leifer_lab_to_nwb_created_7_17_2024`.

You can then activate the isolated environment with:

```bash
conda activate <name of environment>
```

For the time being you will need to install `git` using:

```bash
conda install git
```

though I may eventually be able to remove this necessity.



## Installation

In the isolated environment, install this package by calling:

```bash
git clone https://github.com/catalystneuro/leifer-lab-to-nwb
cd leifer-lab-to-nwb
pip install -e .
```

Then to install the specific set of dependencies for a particular conversion, such as `randi_nature_2023`:

```bash
pip install --requirement src/leifer_lab_to_nwb/randi_nature_2023/requirements.txt
```



## Usage: convert a single session of your experiment

TODO
