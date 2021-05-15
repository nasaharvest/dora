Astronomy (DES) Sample Data
=============================

Author: Umaa Rebbapragada (urebbapr@jpl.nasa.gov)
Date Created: 5/14/2021
Date Modified: 5/14/2021

This directory contains a sample of data from the Dark Energy Survey (DES) Gold 2.2 catalog. The catalog provided is galaxy photometry.  The data was pre-processed offline using scripts stored in JPL Github under des-ml (PI: Eric Huff).   

Data
----

Y3_mastercat_12_3_19_SOMv0.21_indexselect_p0.0001_lups_colors.h5

This .h5 file is a pandas dataframe (key='data') with shape (10892, 8). This a random 1/10000 subsample of the original DES filtered sample produced by running des-ml/src/des_read_filter_save_gold2.2_dec2019.py -p 0.0001 -o output.h5.  Umaa then manually removed columns that are not present or cannot be derived from the DES public release of Gold 2.2.

The index of this dataframe is the 'COADD_OBJECT_ID', an identifying ID used by DES for each object.  

The columns of this dataframe are: 

- 'lup_r', 'lup_err_r': r-band luptitude and error
- 'color_g_minus_r', 'color_err_g_minus_r': color g-r and error
- 'color_i_minus_r', 'color_err_i_minus_r': color i-r and error
- 'color_z_minus_r', 'color_err_z_minus_r': color z-r and error


