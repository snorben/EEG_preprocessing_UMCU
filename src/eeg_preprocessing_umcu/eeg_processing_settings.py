# -*- coding: utf-8 -*-
"""
Created on Wed May  1 09:56:45 2024
# test Herman
@author: hvand
"""
import mne
import matplotlib
import PySimpleGUI as sg
# matplotlib.use('Qt5Agg')  # Set the backend to Qt5
# mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')
matplotlib.use('TkAgg')  # Setting bakcend working best for Spyder
mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')  # Setting for Spyder
# deaults for gui user input
sg.theme('Default1')
font = ("Ubuntu Medium", 14)
# my_image=sg.Image('download3.png')
my_image = sg.Image('UMC_logo.png')  # UMC logo
sg.set_options(tooltip_font=(16))  # tootip size
settings={}

settings['default_epoch_length'] = 8
settings['default_ica_components'] = 25
settings['default_downsample_factor'] = 1
settings['sample_frequencies'] = [250, 256, 500, 512, 1000, 1024, 1250, 2000, 2048, 5000]

settings['montage',".txt_bio32"] = "biosemi32"
settings['montage',".txt_bio64"] = "biosemi64"
settings['montage',".txt_10-20"] = "standard_1020"
settings['montage',".bdf_32"] = "biosemi32"
settings['montage',".bdf_64"] = "biosemi64"
settings['montage',".bdf_128"] = "biosemi128"
settings['montage',".edf_bio32"] = "biosemi32"
settings['montage',".edf_bio64"] = "biosemi64"
settings['montage',".edf_bio128"] = "biosemi128"
settings['montage',".edf_10-20"] = "standard_1020"
settings['montage',".edf_GSN-Hydrocel_64"] = "GSN-HydroCel-64_1.0"
settings['montage',".eeg"] = "n/a"

settings['input_file_pattern',".txt_bio32"] = "*.txt"
settings['input_file_pattern',".txt_bio64"] = "*.txt"
settings['input_file_pattern',".txt_10-20"] = "*.txt"
settings['input_file_pattern',".bdf_32"] = "*.bdf"
settings['input_file_pattern',".bdf_64"] = "*.bdf"
settings['input_file_pattern',".bdf_128"] = "*.bdf"
settings['input_file_pattern',".edf_bio32"] = "*.edf"
settings['input_file_pattern',".edf_bio64"] = "*.edf"
settings['input_file_pattern',".edf_bio128"] = "*.edf"
settings['input_file_pattern',".edf_10-20"] = "*.edf"
settings['input_file_pattern',".edf_GSN-Hydrocel_64"] = "*.edf"
settings['input_file_pattern',".eeg"] = "*.vhdr"

settings['input_file_patterns'] = ['.bdf_32', '.bdf_64', '.bdf_128', '.edf_bio32', '.edf_bio64',
                       '.edf_bio128', '.edf_10-20', '.eeg','.edf_GSN-Hydrocel_64', '.txt_bio32', '.txt_bio64', '.txt_10-20']
# text & tool tips
settings['input_file_patterns','text']="Enter file type"
settings['input_file_patterns','tooltip']='Enter one filetype and electrode layout: .bdf 32ch, .bdf 64ch, .bdf 128ch, .edf biosemi 32 layout,\n .edf biosemi 64 layout, .edf biosemi 128 layout, .edf general 10-20 layout, .eeg, .txt biosemi 32 layout,\n .txt biosemi 64 layout, .txt general 10-20 layout, \nsee https://mne.tools/dev/auto_tutorials/intro/40_sensor_locations.html for the electrode layouts (montages) used'
settings['load_config_file','text']="Select a previously created .pkl file"
settings['input_file_paths','type_EEG']=(("EEG .txt Files", "*.txt"), ("EEG .bdf Files", "*.bdf"),
            ("EEG .vhdr Files", "*.vhdr"), ("EEG .edf Files", "*.edf"),) # note the comma...
settings['input_file_paths','text']="Select input EEG file(s) - on Mac use 'Options' to filter file types "  


