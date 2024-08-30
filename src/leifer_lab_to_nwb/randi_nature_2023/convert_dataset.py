"""Main conversion script for the entire dataset for the Randi et al. Nature 2023 paper."""

import pathlib

import tqdm
import yaml

from leifer_lab_to_nwb.randi_nature_2023 import pump_probe_to_nwb

# TESTING=True creates 'preview' files that truncate all major data blocks; useful for ensuring process runs smoothly
TESTING = True

# TESTING=False performs a full file conversion
# TESTING = False

# Define base folder of source data
# Change these as needed on new systems
BASE_FOLDER_PATH = pathlib.Path("D:/Leifer")
SUBJECT_INFO_FILE_PATH = BASE_FOLDER_PATH / "all_subjects_metadata.yaml"

OUTPUT_FOLDER_PATH = pathlib.Path("E:/Leifer")
NWB_OUTPUT_FOLDER_PATH = OUTPUT_FOLDER_PATH / "nwbfiles"
NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)

if __name__ == "__main__":
    with open(file=SUBJECT_INFO_FILE_PATH, mode="r") as stream:
        all_subject_info = yaml.safe_load(stream=stream)

    # Check YAML for integrity
    for subject_key, subject_info in all_subject_info.items():
        if subject_key != subject_info["subject_id"]:
            message = (
                "\n\nMismatch detected between lookup key and subject ID!\n\n"
                f"Lookup key: {subject_key}\nSubject ID: {subject_info['subject_id']}\n\n"
                "Please fix this entry of the subject metadata YAML file."
            )
            raise ValueError(message)

    # Convert all processed sessions
    raw_or_processed = "processed"
    for subject_key, subject_info in tqdm.tqdm(
        iterable=all_subject_info.items(),
        total=len(all_subject_info),
        desc="Converting processed sessions",
        unit="session",
        position=0,
        leave=True,
        mininterval=5.0,
        smoothing=0,
    ):
        pump_probe_to_nwb(
            base_folder_path=BASE_FOLDER_PATH,
            subject_info_file_path=SUBJECT_INFO_FILE_PATH,
            subject_id=subject_key,
            nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
            raw_or_processed="processed",
            testing=TESTING,
        )

    print("\n\nProcessed sessions are converted!\n\n")

    # Convert all raw sessions
    raw_or_processed = "raw"
    for subject_key, subject_info in tqdm.tqdm(
        iterable=all_subject_info.items(),
        total=len(all_subject_info),
        desc="Converting processed sessions",
        unit="session",
        position=0,
        leave=True,
        mininterval=5.0,
        smoothing=0,
    ):
        pump_probe_to_nwb(
            base_folder_path=BASE_FOLDER_PATH,
            subject_info_file_path=SUBJECT_INFO_FILE_PATH,
            subject_id=subject_key,
            nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
            raw_or_processed="raw",
            testing=TESTING,
        )

    print("\n\nRaw sessions are converted!\n\n")
