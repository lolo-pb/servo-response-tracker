# Project notes

This is a deliberately small OpenCV webcam prototype.

```
USB webcam frame
  -> HSV colour masks for pink and cyan
  -> largest valid blob centroid for each marker
  -> line and signed two-point angle in the preview
```

`tracker.py` is the only application file. Run it with native Windows Python
for straightforward webcam access; WSL is fine for editing.

Potential future addition: track three markers and calculate the joint angle at
the middle marker.
