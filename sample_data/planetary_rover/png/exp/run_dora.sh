#!/usr/bin/bash
# Script to run DORA on Navcam images

config_file=navcam.config

# Run algorithms with
# images-to-fit: images from sols 1343 to 1349 in ../images-fit
# images-to-score: images from sol 1371 in ../images-score
dora_exp -l dora.log $config_file

# Results will be written to results/ subdirectories.

