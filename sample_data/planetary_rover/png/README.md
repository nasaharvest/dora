Planetary Science Sample Data (PNG format)
==========================================

This directory contains sample Mars rover image files (.png).

Data
----

The `images/` directory contains several .png files, with one target
(e.g., rock, soil patch) contained in each.  Each original PDS image
product contains one or more targets.  The .png files were created
using a bounding box around each target.

The naming convention specifies the mission date (sol) on which the
source image was acquired, the instrument used to collect the image,
an identifier string, and the target index within the image.

Example:

SOL01343NLB_516721703EDR_F0540992CCAM15900M1-112.png

The source image was taken on sol 1343 by the Navcam Left camera, and
it is target number 112 within that image.

The data set consists of targets from a single source Navcam image
product from each of the following sols:  1343, 1347, 1349, and 1371.

Experiments
-----------

DORA requires the specification of which images to "fit" (train) and
which images to "score" (rank).

The `exp/` directory contains the files needed to run a simple
experiment with DORA as well as the expected results for comparison:

- `run_dora.sh` : Bash script that runs DORA using navcam.config .
  
- `navcam.config` : DORA config file that specifies using images from
  sols 1343-1349 (in `images-fit/`) to train each algorithm and images
  from sol 1371 (in `images-score/`) to be ranked.  It also specifies
  which algorithms to run and the feature representation (raw pixels). 

The `results/` directory contains the expected results of running the
`run_dora.sh` script.

Expected output at the command line after changing into the `exp/`
directory and running the Bash script:

```Console
> cd exp
> ./run_dora.sh
```

Information about the run is available in the generated log file,
`dora.log`:

```Console
> cat dora.log 
[2021-07-16 11:20:03]: Configuration file: /home/wkiri/Research/DORA/git/sample_data/planetary_rover/png/exp/navcam.config
[2021-07-16 11:20:03]: data_type: image               
[2021-07-16 11:20:03]: data_to_fit: ../images-fit       
[2021-07-16 11:20:03]: data_to_score: ../images-score     
[2021-07-16 11:20:03]: zscore_normalization: 0                   
[2021-07-16 11:20:03]: features: {'flattened_pixel_values': {'width': 64, 'height': 64}}
[2021-07-16 11:20:03]: outlier_detection: {'demud': {'k': 5}, 'iforest': {}, 'negative_sampling': {'percent_increase': 20}, 'pca': {'k': 5}}
[2021-07-16 11:20:03]: results: {'save_scores': {}}
[2021-07-16 11:20:03]: Use data loader: image
[2021-07-16 11:20:04]: Created sub directory for outlier detection algorithm iforest at /home/wkiri/Research/DORA/git/sample_data/planetary_rover/png/exp/results/iforest
[2021-07-16 11:20:22]: Created sub directory for outlier detection
algorithm negative_sampling at
/home/wkiri/Research/DORA/git/sample_data/planetary_rover/png/exp/results/negative_sampling-percent_increase=20
```

You can then compare your new output in `results/` to the output
in `../results/`.

```Console
> diff -r ../results/ results
```

Note: git is configured to ignore this new output directory so that it
will not be accidentally committed back to the repository. 



---
Contact: Kiri Wagstaff, kiri.wagstaff@jpl.nasa.gov

