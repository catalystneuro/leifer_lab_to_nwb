import pathlib
import json

import yaml

base_path = pathlib.Path("D:/Leifer")

subject_info_file_path = pathlib.Path("D:/Leifer/all_subjects_metadata.yaml")
with open(file=subject_info_file_path, mode="r") as stream:
    all_subject_info = yaml.safe_load(stream=stream)

session_to_box_shape = dict()
for subject_id, session_info in all_subject_info.items():
    sessions = [session_info["multicolor_folder"], session_info["pump_probe_folder"]]
    for session in sessions:
        log_file = base_path / str(session_info["date"]) / session / "analysis.log"

        if not log_file.exists():
            continue

        with open(file=log_file, mode="r") as io:
            lines = io.readlines()

        lines_with_box_size = [line for line in lines if '"box_size":' in line]

        if len(lines_with_box_size) == 0:
            session_to_box_shape.update({session: (1, 3, 3)})  # The hard coded default

        for line in lines_with_box_size:
            shape = tuple(int(x) for x in line.split('"box_size":')[1].split("], ")[0].removeprefix(" [").split(","))

            session_to_box_shape.update({session: shape})

base_path = pathlib.Path("G:/Leifer")

for subject_id, session_info in all_subject_info.items():
    sessions = [session_info["multicolor_folder"], session_info["pump_probe_folder"]]
    for session in sessions:
        log_file = base_path / str(session_info["date"]) / session / "analysis.log"

        if not log_file.exists():
            continue

        with open(file=log_file, mode="r") as io:
            lines = io.readlines()

        lines_with_box_size = [line for line in lines if '"box_size":' in line]

        if len(lines_with_box_size) == 0:
            session_to_box_shape.update({session: (1, 3, 3)})  # The hard coded default

        for line in lines_with_box_size:
            shape = tuple(int(x) for x in line.split('"box_size":')[1].split("], ")[0].removeprefix(" [").split(","))

            session_to_box_shape.update({session: shape})

save_path = pathlib.Path(
    "D:/GitHub/leifer_lab_to_nwb/src/leifer_lab_to_nwb/randi_nature_2023/session_to_box_shape.json"
)
with open(file=save_path, mode="w") as io:
    json.dump(obj=session_to_box_shape, fp=io, indent=2)
