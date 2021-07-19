Planetary Science Sample Data
=============================

This directory contains sample Mars rover image files and results from
running the CIF novelty algorithm simulator.  There are two ways to
analyze this data:

1) Use the Planetary Data System (PDS) image products (.IMG + .LBL
files).  Each image contains one or more targets (e.g., rocks, soil
patches), which are specified in an accompanying .json file.  The unit
of analysis for novelty detection is the image created by a bounding
box around each target.

See `pds/README.md` for how to proceed.

2) Use pre-cropped per-target images (.png files).

See `png/README.md` for how to proceed.

---
Contact: Kiri Wagstaff, kiri.wagstaff@jpl.nasa.gov

