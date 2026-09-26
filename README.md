# Marker angle tracker

Tracks a solid pink dot and a solid cyan dot from a USB webcam. It shows each
dot's coloured-pixel centroid and the signed angle from the pink dot to the
cyan dot. Image-right is `0°`; counter-clockwise is positive.

## Run on Windows

Run this in PowerShell from the project directory, not inside WSL, so Windows
has direct access to the webcam:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tracker.py
```

Press `q` in the preview window to stop. If the USB webcam is not camera `0`,
change `CAMERA_INDEX` near the top of `tracker.py`.

## Tuning

`MARKERS` contains the HSV ranges for pink and cyan. `MIN_BLOB_AREA` ignores
small coloured specks; begin with its default of 200 pixels and increase it if
reflections are selected instead of the marker.
