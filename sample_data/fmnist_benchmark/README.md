FMNIST and MNIST Benchmark Data (PNG format)
============================================

Ths directory images from the Fashion MNIST and MNIST datasets.

Data
----

This data is intended to act as a benchmark for algorithm performance.
The fifty images from Fashion MNIST (in `images_fit/`) are treated as the data 
to fit/inliers, while the ten images from MNIST (in `images_score/` ) are 
treated as the data to score/outliers.

Experiments
-----------

The `exp/` directory contains a shell to run DORA on the FMNIST/MNIST data using
the convolutional autoencoder algorithm. To run it:

```Console
> cd exp
> ./run_dora.sh
```