For EEG visualization project, set the working directory to ~/Library/CloudStorage/Box-Box/EEG Research - Shared Drive/Scripts/eeg_viz

## Instructions for running

1. Run python codes under a proper virtual environment. (e.g., pyllm)
2. Install necessary packages:
pip install pyyaml pandas openpyxl

3. Enter working directory for codes: eeg_viz, 
python main.py  # desktop GUI — two patients side by side
python web_server.py # web GUI  — open http://127.0.0.1:8000

## Code Structure

config.yaml ─► config.py
                   │
        ┌──────────┴───────────┐
   data_manager.py          colors.py        ← core (no UI, no web)
        │   (pandas)        (pure RGB/hex)
        ├──────────┬───────────┤
   ElectrodeMap   backend.py (EEGBackend)     ← backend.py = Qt-free, JSON-only
   gui.py         │
   (PyQt desktop) web_server.py ─► web/index.html   ← browser front-end
   

## Task Instructions
create a config.yaml file to contain all possible running parameters such as directory path for raw EEG data, csv or excel files for visualization, etc. main.py reads the config parameters and pass to other modules when needed

Task 1: modify the current python script main.py so it contains a variable for setting the directory path for all needed data files for visualization purpose.

Task 2: add a little triangle at the 90 degree direction and on top of the outside big circle to indicate a nose, put two small half circles at the both sides of the outside circle to indicate the positions of two ears

Task 3: extend the functionality of the GUI interface. write python functions or modules so that they can later work at back-end, and called by front-end web browser based GUI.

Add function to display two patients' EEG side by side, the two patients can be picked from the drop-down manual.

Task 4: generate a plot similar to the image front_central_delta_left_vs_right.png in ./image_sample directory for AA and AA-post based on data in coherence.xlsx, use the row with label CONTROL_AVG as the control value. Put the plot in a new choice tab in the GUI.

Added "- name: "Left Temporal-Central"
pairs: ["C3-T3", "C3-T5", "CZ-T3", "CZ-T5"]
- name: "Right Temporal-Central"
pairs: ["C4-T4", "C4-T6", "CZ-T4", "CZ-T6"]" to config.yaml, display plots for these two groups in the GUI

Make the legend of the plot to be the label of chosen data in the drop-down box, instead of a fixed legend of "Non-ADA Control", make the other legends dynamically consistent with the data plotted.  Also, use color green for Post-ETS, color red for Pre-ETS.
