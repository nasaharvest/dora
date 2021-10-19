# Script to run DORA on Fashion MNIST/MNIST images

# Change to the root of the repo so DORA imports work correctly
# to execute the current code
cd ../../..

# Run algorithms with
# images-to-fit: subset of fmnist images in ../images-fit
# images-to-score: subset of mnist images in ../images-score
# Note: config file, log file, and out_dir pathnames are relative to repo root
config_file=sample_data/fmnist_benchmark/exp/dora_fmnist_benchmark.yml
log_file=sample_data/fmnist_benchmark/exp/dora.log
out_dir=sample_data/fmnist_benchmark/exp/results
dora_exp -l $log_file -o $out_dir $config_file

# Results will be written to results/ subdirectories.
