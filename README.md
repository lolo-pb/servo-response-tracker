# Marker angle tracker

Simple Python script to track the angle between two points from a video, 
Use colored markers on a leg and anlalyze response.

<img width="745" height="277" alt="image" src="https://github.com/user-attachments/assets/2fda5488-d515-4fd8-866a-0dbc6813e229" />
<img width="448" height="502" alt="image" src="https://github.com/user-attachments/assets/ef6c0cea-a454-42ae-90ba-bd40bb935538" />


Processes every supported video in a folder, tracks a solid pink dot and a
solid cyan dot, and measures their relative angle once per frame. The first
frame containing both markers is 0 degrees; later values are continuously
unwrapped so crossing +/-180 degrees does not create a false jump.

For each source video, the tracker writes to an output subfolder:

    videos/
        test.mp4
        output/
            test-angles.csv
            test-overlay.mp4

The CSV contains the frame number, timestamp, relative angle, and marker
detection status. A missing marker produces a blank angle for that frame.

The overlay video contains the detected markers, a solid line between them,
the relative angle, and a yellow dotted reference line. The reference line is
anchored at the current cyan marker, follows the initial line back toward the
pink side, and has the same length as the current marker-to-marker line.

## Run on Windows

Run this in PowerShell from this directory:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python tracker.py "C:\path\to\videos"

Supported input extensions are .mp4, .avi, .mov, and .mkv. If the folder
argument is omitted, the tracker uses a videos folder beside tracker.py,
creating it if necessary.

Existing outputs are skipped. To intentionally replace them:

    python tracker.py "C:\path\to\videos" --overwrite

## Tuning

MARKERS contains the HSV ranges for pink and cyan. MIN_BLOB_AREA ignores small
coloured specks. Change these constants if lighting, compression, camera
distance, or marker size causes missed or false detections.
