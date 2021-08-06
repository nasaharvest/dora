#!/usr/bin/bash
# Script to run DORA on Navcam images

# Change to the root of the repo so DORA imports work correctly
# to execute the current code
cd ../../../..

# Run algorithms with
# images-to-fit: images from sols 1343 to 1349 in ../images-fit
# images-to-score: images from sol 1371 in ../images-score
# Note: config file, log file, and out_dir pathnames are relative to repo root
config_file=sample_data/planetary_rover/png/exp/navcam.config
log_file=sample_data/planetary_rover/png/exp/dora.log
out_dir=sample_data/planetary_rover/png/exp/results
dora_exp -l $log_file -o $out_dir $config_file

# Results will be written to results/ subdirectories.

