#!/usr/bin/env python
# Functional tests with Earth time series data.
# Inspired by Gary's PDSC functional tests, e.g.:
# https://github-fn.jpl.nasa.gov/COSMIC/COSMIC_PDSC/blob/master/test/test_ingest.py
#
# Hannah Kerner
# 10/4/21

import os
import shutil
from unittest import TestCase
import pytest
from test_utils import check_results
from dora_exp_pipeline.dora_exp import start

@pytest.mark.functional
class TestEarthTimeSeries(TestCase):

    def setUp(self):

        self.outdir = '/tmp/dora/test/earth_time_series'
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    def test_run(self):

        config_file = 'test/earth_time_series.config'

        # Run the experiment; also tests ability to parse config file
        start(config_file, self.outdir)

        # Check results for each algorithm
        for file_base in ['demud-k=3/selections-demud.csv',
                          'iforest-n_trees=100-fit_single_trees=False/selections-iforest.csv',
                          'negative_sampling-percent_increase=20/selections-negative_sampling.csv',
                          'pca-k=3/selections-pca.csv',
                          'rx/selections-rx.csv',
                          'random/selections-random.csv'
                          ]:
            correct_file = 'test/ref-results/earth_fieldsamples/%s' % file_base
            output_file = '%s/%s' % (self.outdir, file_base)

            # Check results against correct output
            assert check_results(output_file, correct_file)

    def tearDown(self):
        # Remove any intermediate files
        shutil.rmtree(self.outdir)
