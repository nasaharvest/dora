#!/usr/bin/bash
# Script to run novelty simulator on Navcam images

# Location of simulator code
sim=~/Research/CIF/git/novelty_targeting/

outdir=sol01371
mkdir -p $outdir
config_file=simulator_config_aegis_select.yml

# Run all algorithms on targets in image from sol 1371
# (prior sols 1343-1370)
python $sim/simulator.py -o $outdir -l $outdir/sim.log $config_file

# Visualize the results
targets_file=aegis_executions_sol1343-sol1400.json
$sim/viz_overlays.py $outdir -i navcam -m 1 -r -w -a $targets_file
