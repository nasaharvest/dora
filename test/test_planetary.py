#!/usr/bin/env python
# Functional tests with planetary science data.
# Inspired by Gary's PDSC functional tests, e.g.:
# https://github-fn.jpl.nasa.gov/COSMIC/COSMIC_PDSC/blob/master/test/test_ingest.py
#
# Kiri Wagstaff
# 8/19/21

import os
import shutil
from unittest import TestCase
import pytest
from test_utils import check_results
from dora_exp_pipeline.dora_exp import start

@pytest.mark.functional
class TestPlanetary(TestCase):

    def setUp(self):

        self.outdir = '/tmp/dora/test/planetary'
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    def test_run(self):

        config_file = 'test/planetary.config'

        # Run the experiment; also tests ability to parse config file
        start(config_file, self.outdir)

        # Check results for each algorithm
        for file_base in ['demud-k=5/selections-demud.csv',
                          'iforest-n_trees=100-fit_single_trees=False/selections-iforest.csv',
                          'lrx-inner_window=3-outer_window=9-bands=1/selections-lrx.csv',
                          'negative_sampling-percent_increase=20/selections-negative_sampling.csv',
                          'pca-k=5/selections-pca.csv',
                          'random/selections-random.csv'
                          ]:
            correct_file = 'test/ref-results/planetary_rover/functional/%s' % file_base
            output_file = '%s/%s' % (self.outdir, file_base)

            # Check results against correct output
            assert check_results(output_file, correct_file)

    def tearDown(self):
        # Remove any intermediate files
        shutil.rmtree(self.outdir)
