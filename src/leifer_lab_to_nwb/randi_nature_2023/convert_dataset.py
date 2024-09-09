"""Main conversion script for the entire dataset for the Randi et al. Nature 2023 paper."""

import pathlib
import traceback

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
SUBJECT_INFO_FILE_PATH = pathlib.Path("D:/Leifer/all_subjects_metadata.yaml")

OUTPUT_FOLDER_PATH = pathlib.Path("E:/Leifer")
NWB_OUTPUT_FOLDER_PATH = OUTPUT_FOLDER_PATH / "nwbfiles"
ERROR_FOLDER = NWB_OUTPUT_FOLDER_PATH / "errors"
COMPLETED_RAW_FILE_PATH = NWB_OUTPUT_FOLDER_PATH / "completed_raw_sessions.txt"
LIMIT_RAW = 10

if __name__ == "__main__":
    NWB_OUTPUT_FOLDER_PATH.mkdir(exist_ok=True)
    ERROR_FOLDER.mkdir(exist_ok=True)

    with open(file=SUBJECT_INFO_FILE_PATH, mode="r") as stream:
        all_subject_info = yaml.safe_load(stream=stream)

    completed_raw_sessions = []
    if COMPLETED_RAW_FILE_PATH.exists() and TESTING is False:
        with open(file=COMPLETED_RAW_FILE_PATH, mode="r") as io:
            completed_raw_sessions = io.readlines()

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
        try:
            pump_probe_to_nwb(
                base_folder_path=BASE_FOLDER_PATH,
                subject_info_file_path=SUBJECT_INFO_FILE_PATH,
                subject_id=subject_key,
                nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
                raw_or_processed="processed",
                testing=TESTING,
            )
        except Exception as exception:
            error_file_path = ERROR_FOLDER / f"{subject_key}_{raw_or_processed}_testing={TESTING}_error.txt"
            message = (
                f"Error encountered during conversion of processed subject ID '{subject_key}'!\n\n"
                f"{type(exception)}: {str(exception)}\n\n"
                f"{traceback.format_exc()}"
            )
            with open(file=error_file_path, mode="w") as io:
                io.write(message)

    print("\n\nProcessed sessions were converted!\n\n")

    # Convert all raw sessions
    raw_or_processed = "raw"
    raw_counter = 0
    for subject_key, subject_info in tqdm.tqdm(
        iterable=all_subject_info.items(),
        total=len(all_subject_info),
        desc="Converting raw sessions",
        unit="session",
        position=0,
        leave=True,
        mininterval=5.0,
        smoothing=0,
    ):
        try:
            if raw_counter >= LIMIT_RAW:
                break
            if subject_key in completed_raw_sessions:
                continue

            pump_probe_to_nwb(
                base_folder_path=BASE_FOLDER_PATH,
                subject_info_file_path=SUBJECT_INFO_FILE_PATH,
                subject_id=subject_key,
                nwb_output_folder_path=NWB_OUTPUT_FOLDER_PATH,
                raw_or_processed="raw",
                testing=TESTING,
            )

            if TESTING is False:
                raw_counter += 1

                with open(file=COMPLETED_RAW_FILE_PATH, mode="a") as io:
                    io.writeline(f"{subject_key}\n")
        except Exception as exception:
            error_file_path = ERROR_FOLDER / f"{subject_key}_{raw_or_processed}_testing={TESTING}_error.txt"
            message = (
                f"Error encountered during conversion of processed session '{subject_key}'!\n\n"
                f"{type(exception)}: {str(exception)}\n\n"
                f"{traceback.format_exc()}"
            )
            with open(file=error_file_path, mode="w") as io:
                io.write(message)

    print(f"\n\n{raw_counter} more raw sessions were converted!\n\n")
