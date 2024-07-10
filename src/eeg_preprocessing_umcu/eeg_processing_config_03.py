# -*- coding: utf-8 -*-
"""
Created on Wed May  1 09:56:45 2024

@author: hvand
"""
import mne
import matplotlib
# matplotlib.use('Qt5Agg')  # Set the backend to Qt5
# mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')
matplotlib.use('TkAgg')  # Setting bakcend working best for Spyder
mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')  # Setting for Spyder
# deaults for gui user input
default_ica_components = 25
default_downsample_factor = 1
default_epoch_length = 8
sample_frequencies = [250, 256, 500, 512, 1000, 1024, 1250, 2000, 2048, 5000]
input_file_patterns = ['.bdf_32', '.bdf_64', '.bdf_128', '.edf_bio32', '.edf_bio64',
                       '.edf_bio128', '.edf_10-20', '.eeg','.edf_GSN-Hydrocel_64', '.txt_bio32', '.txt_bio64', '.txt_10-20']




