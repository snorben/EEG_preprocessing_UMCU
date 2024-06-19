# -*- coding: utf-8 -*-
"""
Created on Wed May  1 09:56:45 2024

@author: hvand
"""
import mne
import matplotlib

mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')
matplotlib.use('TkAgg')  # Setting bakcend working best for Spyder
#matplotlib.use('Qt5Agg')  # Set the backend to Qt5

# deaults for gui user input
default_ica_components = 25
default_downsample_factor = 1
default_epoch_length = 8
sample_frequencies = [250, 256, 500, 512, 1000, 1024, 1250, 2000, 2048, 5000]
input_file_patterns = ['.bdf 32', '.bdf 64', '.bdf 128', '.edf bio32', '.edf bio64',
                       '.edf bio128', '.edf 10-20', '.eeg', '.edf GSN-Hydrocel 64', 'easycap-M1', '.txt bio32', '.txt bio64', '.txt 10-20']
