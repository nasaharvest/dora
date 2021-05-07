Planetary Science Sample Data
=============================

This directory contains sample Mars rover image files and results from
running the CIF novelty algorithm simulator.  The unit of analysis for
novelty detection is individual "targets" within each image (e.g.,
rocks, soil patches).  Each image contains one or more targets.

Data
----

The `images/` directory contains images from the Mars Science
Laboratory rover's Navcam instrument, using the directory structure
employed by the mission in its deliveries to the Planetary Data System
archive.  Within `MSLNAV_0XXX/DATA/` there are per-sol directories for
sols 1343, 1347, 1349, and 1371, with one image product per sol.

Experiments
-----------

The `exp/` directory contains the files needed to run a simple
experiment with the CIF simulator as well as the expected results for
comparison:

- `run_sim.sh` : Bash script that runs the simulator and a visualization
  script that displays the selected novel targets on the original
  image.  To run this script, you will first need to update the `sim`
  variable that specifies where to find the CIF simulator code on your
  system. 
  
- `simulator_config_aegis_select.yml` : Simulator config file that
  specifies using targets from sols 1343-1370 as "prior" (not novel)
  targets and ranking targets from sol 1371 as the final output.  It
  also specifies the use of "aegis-select" features to represent each
  target.  These options can be overridden in the call to `simulator.py`
  if desired.
  
- `aegis_executions_sol1343-sol1400.json` : JSON file containing all
  targets from the source images.  This file also contains the AEGIS
  features used to represent each target and their pixel locations
  within their source images.  It is needed by both the simulator and
  the visualization script.

The `results/` directory contains the expected results of running the
`run_sim.sh` script.

Expected output at the command line after changing into the `exp/`
directory and running the Bash script:

```Console
> ./run_sim.sh 
--- Loaded package version information ---
[QUESTION] Output directory /home/wkiri/Research/DORA/git/sample_data/planetary_rover/exp/sol01371 exists. Do you want to delete all files and directories in the out_dir? (y/n)y
[INFO] All files and directories have been deleted.
Loaded known novel targets in 42 sols
Drew 8 candidate targets.
Drew 1 aegis targets.
Drew 1 demud-k-3 targets.
Drew 1 iforest-seed-1234 targets.
Drew 1 pca-k-3 targets.
Drew 1 rx targets.
Drew 2 known-novel targets.
Saved image to sol01371/SOL01371NLB_519216253EDR_F0542784CCAM15900M1-novel.png
```

You can then compare your new output in `exp/sol01731/` to the output
in `results/`.  Note: git is configured to ignore this new output
directory so that it will not be accidentally committed back to the
repository. 

---
Contact: Kiri Wagstaff, kiri.wagstaff@jpl.nasa.gov

