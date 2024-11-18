"""
Created on Wed May  1 09:56:45 2024
# x
@author: hvand
"""

import matplotlib
import mne
import PySimpleGUI as sg

# matplotlib.use('Qt5Agg')  # Set the backend to Qt5
# mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')
matplotlib.use('TkAgg')  # Setting bakcend working best for Spyder
mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')  # Setting for Spyder

# deaults for gui user input
sg.theme('Default1')
font = ("Ubuntu Medium", 14)
f_font=("Courier New", 12) # font filter frequency inputs
f_size=5 # font size filter frequency inputs
my_image = sg.Image('UMC_logo.png', subsample=2, pad=(0,0), background_color="#E6F3FF")  # UMC logo

sg.set_options(tooltip_font=(16))  # tootip size
settings={}
filter_settings={}

# script run defaults
settings['default_epoch_length'] = 8
settings['default_ica_components'] = 25
settings['default_downsample_factor'] = 1
settings['sample_frequencies'] = [250, 256, 500, 512, 1000, 1024, 1250, 2000, 2048, 5000]
settings['apply_average_ref'] = 1
settings['apply_epoch_selection'] = 0
settings['apply_output_filtering'] = 0
settings['epoch_length'] = 0.0
settings['apply_ica'] = 0
settings['rerun'] = 0
#settings['rerun_no_previous_epoch_selection'] = 0
settings['apply_beamformer'] = 0
settings['channels_to_be_dropped_selected'] = 0
settings['nr_ica_components'] = 0
settings['max_channels'] = 0
settings['skip_input_file'] = 0
settings['file_pattern'] = '-'
settings['input_file_pattern'] = '-'
settings['montage'] = '-'
settings['input_file_names'] = []
settings['input_file_paths'] = []
settings['channel_names'] = []
settings['sample_frequency'] = 250
settings['downsampled_sample_frequency'] = 250 # default, will be set in script
settings['config_file'] = ' '
settings['log_file'] = ' '
settings['previous_run_config_file'] = ' '
settings['output_directory'] = ' '
settings['batch_output_subdirectory'] = ' '
settings['file_output_subdirectory'] = ' '
settings['input_directory'] = ' '
settings['batch_name'] = ' '
settings['frequency_bands_modified'] = 0
settings['batch_prefix'] = ' '


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
settings['montage',".fif"] = "n/a"

settings['input_file_pattern',".txt_bio32"] = "*.txt"
settings['input_file_pattern',".txt_bio64"] = "*.txt"
settings['input_file_pattern',".txt_10-20"] = "*.txt"
settings['input_file_pattern',".bdf_32"] = "*.bdf"
settings['input_file_pattern',".bdf_64"] = "*.bdf"
settings['input_file_pattern',".bdf_128"] = "*.bdf"
settings['input_file_pattern',".edf_bio32"] = "*.edf" # Biosemi montage
settings['input_file_pattern',".edf_bio64"] = "*.edf" # Biosemi montage
settings['input_file_pattern',".edf_bio128"] = "*.edf" # Biosemi montage
settings['input_file_pattern',".edf_10-20"] = "*.edf" # Generic 10-20 montage
settings['input_file_pattern',".edf_GSN-Hydrocel_64"] = "*.edf"
settings['input_file_pattern',".eeg"] = "*.vhdr"
settings['input_file_pattern',".fif"] = "*.fif"

# defaults for frequency band filter settings
settings['frequency_bands'] = ("delta_low","delta_high","theta_low","theta_high","alpha_low",
                               "alpha_high","beta1_low", "beta1_high","beta2_low","beta2_high",
                               "broadband_low","broadband_high")

# Default filter settings
settings['cut_off_frequency','delta_low'] = 0.5
settings['cut_off_frequency','delta_high'] = 4
settings['cut_off_frequency','theta_low'] = 4
settings['cut_off_frequency','theta_high'] = 8
settings['cut_off_frequency','alpha_low'] = 8
settings['cut_off_frequency','alpha_high'] = 13
settings['cut_off_frequency','beta1_low'] = 13
settings['cut_off_frequency','beta1_high'] = 20
settings['cut_off_frequency','beta2_low'] = 20
settings['cut_off_frequency','beta2_high'] = 30
settings['cut_off_frequency','broadband_low'] = 0.5
settings['cut_off_frequency','broadband_high'] = 47

settings['input_file_patterns'] = ['.bdf_32', '.bdf_64', '.bdf_128', '.edf_bio32', '.edf_bio64',
                       '.edf_bio128', '.edf_10-20', '.fif', '.eeg','.edf_GSN-Hydrocel_64', '.txt_bio32', '.txt_bio64', '.txt_10-20']
# text & tool tips
settings['input_file_patterns','text']="Enter file type"
settings['input_file_patterns','tooltip']='Enter one filetype and electrode layout: .bdf 32ch, .bdf 64ch, .bdf 128ch, .edf biosemi 32 layout,\n .edf biosemi 64 layout, .edf biosemi 128 layout, .edf general 10-20 layout, .eeg, .txt biosemi 32 layout,\n .txt biosemi 64 layout, .txt general 10-20 layout, \nsee https://mne.tools/dev/auto_tutorials/intro/40_sensor_locations.html for the electrode layouts (montages) used'
settings['load_config_file','text']="Select a previously created .pkl file"
settings['input_file_paths','type_EEG']=(("EEG .txt Files", "*.txt"), ("EEG .bdf Files", "*.bdf"),
            ("EEG .vhdr Files", "*.vhdr"), ("EEG .edf Files", "*.edf"), ("Fif", "*.fif")) # note the comma...
settings['input_file_paths','text']="Select input EEG file(s) - on Mac use 'Options' to filter file types "  

settings['output_txt_decimals']=4 # used in np.round to round down exported txt files
