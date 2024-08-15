#!/usr/bin/python
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Tuple, TypedDict

SETTINGS_SEARCH_BASE_BATH = os.getenv("SETTINGS_SEARCH_BASE_BATH", "~/.local/share/Steam/steamapps/compatdata")
RL_SETTINGS_FILENAME = "TASystemSettings.ini"

class KscreenMonitor(TypedDict):
    output: int
    modes: Dict[int, str]
    selected_mode: int

def patch_settings(screen_width: int, revert: bool = False):
    path = Path(SETTINGS_SEARCH_BASE_BATH)
    
    print(f"Searching for {RL_SETTINGS_FILENAME} in {path}")

    cmd = ["find", str(path), "-name", RL_SETTINGS_FILENAME, "-type", "f"]
    print(cmd)
    ta_system_settings_path = subprocess.check_output(" ".join(cmd), shell=True).decode("utf-8").strip()

    if not ta_system_settings_path:
        raise Exception(f"{RL_SETTINGS_FILENAME} not found")

    print(f"Found {RL_SETTINGS_FILENAME} at {ta_system_settings_path}")

    if revert:
        print(f"Reverting {RL_SETTINGS_FILENAME} to original settings")
        shutil.copy(f"{RL_SETTINGS_FILENAME}.bkp", ta_system_settings_path)
        return

    shutil.copy(ta_system_settings_path, f"{RL_SETTINGS_FILENAME}.bkp")

    with open(ta_system_settings_path, "r") as f:
        settings = f.readlines()

    changed_settings = []

    first_res_x_edited = False
    for i,line in enumerate(settings):
        if f"Fullscreen=True" == line:
            changed_settings.append((i, f"Fullscreen=False\n"))
            continue

        if line.startswith("ResX=") and line != f"ResX={screen_width*2}" and not first_res_x_edited:
            changed_settings.append((i, f"ResX={screen_width*2}\n"))
            first_res_x_edited = True
            continue

        if "Borderless=False" == line:
            changed_settings.append((i, f"Borderless=True\n"))
            continue

    for index, new_settings in changed_settings:
        settings[index] = new_settings

    with open(ta_system_settings_path, "w") as f:
        f.writelines(settings)

def parse_kscreen_doctor_output(output) -> KscreenMonitor:
    modes = {}
    
    # Extract the Output number
    output_number_match = re.search(r"Output:\s*(\d+)", output)
    output_number = output_number_match.group(1) if output_number_match else None
    
    # Find the section that contains the modes
    modes_section = re.search(r"Modes:(.*?)(Geometry|Scale|Rotation)", output, re.DOTALL)
    
    selected_mode = -1
    if modes_section:
        # Extract each mode and resolution using regex
        mode_matches = re.findall(r"(\d+):(\d+x\d+@\d+[\*]?+)", modes_section.group(1))

        # Convert matches to the required format
        for mode, resolution in mode_matches:
            if "*" in resolution:
                selected_mode = int(mode)
            modes[int(mode)] = resolution.replace("*", "")

    return {
        "output": int(output_number),
        "modes": modes,
        "selected_mode": selected_mode
    }


def selected_mode_resolution(monitor: KscreenMonitor) -> Tuple[int, int, int]:
    res, refresh = monitor["modes"][monitor["selected_mode"]].split("@")
    return [int(x) for x in res.split("x")] + [int(refresh)]


def normalize_screen_resolution(revert: bool = False):
    if revert:
        print("Reverting monitors to original modes")
        with open("screen_mode.bkp", "r") as f:
            cmd = ["kscreen-doctor"]
            for line in f:
                screen, mode = line.split(",")
                cmd.append(f"output.{screen.strip()}.mode.{mode.strip()}")
            print(cmd)
            subprocess.run(cmd)
        return

    cmd = ["kscreen-doctor", "--outputs"]
    output = subprocess.check_output(cmd).decode("utf-8").strip()

    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    # Remove ANSI color codes
    output = ansi_escape.sub('', output)

    monitors = output.splitlines()

    if len(monitors) > 2:
        raise Exception("More than 2 monitors found. Please have only two monitors connected.")
    
    if len(monitors) == 0:
        raise Exception("No monitors found. Please have two monitors connected.")

    monitor_1 = parse_kscreen_doctor_output(monitors[0])
    monitor_2 = parse_kscreen_doctor_output(monitors[1])

    with open("screen_mode.bkp", "w") as f:
        for monitor in [monitor_1, monitor_2]:
            f.write(f"{monitor['output']},{monitor['selected_mode']}\n")

    monitor_1_res = selected_mode_resolution(monitor_1)
    monitor_2_res = selected_mode_resolution(monitor_2)
    
    if monitor_1_res[0] == monitor_2_res[0] and monitor_1_res[1] == monitor_2_res[1]:
        return monitor_1_res[0]
    
    # If the monitors have different resolutions, resize the biggest to match the smallest
    min_res = monitor_1_res
    min_res_raw = monitor_1["modes"][monitor_1["selected_mode"]]
    monitor_to_resize = monitor_2
    if monitor_2_res[0] * monitor_2_res[1] < min_res[0] * min_res[1]:
        min_res = monitor_2_res
        min_res_raw = monitor_2["modes"][monitor_2["selected_mode"]]
        monitor_to_resize = monitor_1

    cmd = ["kscreen-doctor", f"output.{monitor_to_resize['output']}.mode.{min_res_raw}"]

    print(cmd)
    subprocess.run(cmd)

    return min_res[0]

def main(revert: bool = False):
    screen_width = normalize_screen_resolution(revert)
    patch_settings(screen_width, revert)


if __name__ == '__main__':
    import sys

    revert = False
    if "--revert" in sys.argv or "-r" in sys.argv:
        revert = True

    main(revert)
