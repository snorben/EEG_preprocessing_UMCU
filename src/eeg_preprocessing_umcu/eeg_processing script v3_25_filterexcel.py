
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 08:50:06 2024

@author: hvand
"""

import PySimpleGUI as sg
import os
import pandas as pd
import mne
import numpy as np
import traceback
import webbrowser as wb
import pprint  # pretty print dict
#import openpyxl
from mne.preprocessing import ICA
# import matplotlib.pyplot as plt
from datetime import datetime
from eeg_processing_config_02 import *
from mne.beamformer import apply_lcmv_raw,make_lcmv
from mne.datasets import fetch_fsaverage

# Pip install nibabel, scikit-learn

beamforming = True
filtering = True

# Define the Excel file to save epoch selections
excel_file = "epoch_selection.xlsx"

# Frequency bands used for filtering exported epochs and signals
delta_low=0.5
delta_high=4
theta_low=4
theta_high=8
alpha_low=8
alpha_high=13
beta_low=13
beta_high=25
broadband_low=0.5
broadband_high=48

EEG_version = "v3.25f"
# flag to prevent repeated channel_to_be_dropped selection
to_be_dropped_selected = False
# # matplotlib.use('Qt5Agg')  # set this in the config file!
# matplotlib.use('TkAgg')  # Setting bakcend working best for Spyder
# mne.set_config('MNE_BROWSER_BACKEND', 'matplotlib')  # Setting for Spyder set this in the config file!
progress_value1 = 20  # initial values
progress_value2 = 20
sg.theme('Default1')
font = ("Ubuntu Medium", 14)
# my_image=sg.Image('download3.png')
my_image = sg.Image('UMC_logo.png')  # UMC logo
sg.set_options(tooltip_font=(16))  # tootip size


def make_win1():
    layout = [
        [sg.Text('EEG Preprocessing', size=(30, 1), font=("Ubuntu Medium", 35), text_color='#003DA6',
                 justification='c'), sg.Text(EEG_version)],
        [sg.Multiline('File info: ', autoscroll=True, size=(
            120, 10), k='-FILE_INFO-', reroute_stdout=True)],  # True=redirect console to window @@@
        [sg.Text('Functions:'), sg.Button(
            'Enter parameters for this batch'), sg.Button('Start processing')],
        [sg.Multiline('Run info: ', autoscroll=True,
                      size=(120, 10), k='-RUN_INFO-', reroute_stdout=True)],  # True=redirect console to window @@@
        [sg.ProgressBar(progress_value1, orientation='h', size=(
            80, 10), key='progressbar', bar_color=['red', 'grey'])],
        [sg.ProgressBar(progress_value2, orientation='h', size=(
            80, 10), key='progressbar2', bar_color=['#003DA6', 'grey'])],
        [sg.Button('Exit')],
        [sg.Column([[my_image]], justification='center')]]
    return sg.Window('UMC Utrecht MNE EEG Preprocessing', layout, location=(30, 30), size=(1000, 700), finalize=True, font=("Ubuntu Medium", 13))


def select_input_files(config):
    # https://stackoverflow.com/questions/73764314/more-than-one-file-type-in-pysimplegui
    # note the comma...
    type_EEG = (("EEG Files", "*.txt *.bdf *.vhdr *.edf"),)
    f = sg.popup_get_file('Select input EEG file(s)',  title="File selector", multiple_files=True,
                          file_types=type_EEG, background_color='light blue', location=(100, 100))
    file_list = f.split(";")
    config['input_files'] = file_list
    return config


def select_epoch_directory(config):
    tooltip = 'Output folder for exported epoch- and log files'
    working_directory = os.getcwd()
    layout = [
        [sg.Text(
            "Select folder to save processed EEG (epochs or uncut EEG) to", tooltip=tooltip)],
        [sg.InputText(default_text=working_directory, key="-FOLDER_PATH-"),
         sg.FolderBrowse(initial_folder=working_directory)],
        [sg.Button('Select')]
    ]
    window = sg.Window("Directory", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Select':
            try:
                config['epoch_directory'] = values["-FOLDER_PATH-"]
                break
            except:
                sg.popup_error('No valid folder', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_average_ref(config):
    txt = "Do you want to apply average reference to the raw EEG?"
    tooltip = """Do you want to apply average reference to the raw EEG?"""
    url = "https://mne.tools/stable/auto_tutorials/preprocessing/55_setting_eeg_reference.html"

    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True, font=font)],
              [sg.Radio("Yes", "avgref", key='-AVERAGE_REF_YES-', default=True),
               sg.Radio("No", "avgref", key='-AVERAGE_REF1_NO-', default=False), sg.Button('More info')],
              [sg.Button('Ok')]]

    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'More info':
            # os.system('cmd /c start chrome '+url) # force to use Chrome
            wb.open_new_tab(url)
            continue
        if event == 'Ok':
            try:
                if values['-AVERAGE_REF_YES-'] == True:
                    config['average_ref'] = 1
                else:
                    config['average_ref'] = 0
                break
            except:
                sg.popup_error('No valid value', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_ica_option(config):
    txt = "Do you want to apply ICA?\nNote: make sure to deselect electrodes with overlapping positions\ne.g. HR, ML, Nose"  # @@@
    tooltip = """Do you want to apply ICA?"""

    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True, font=font)],
              [sg.Radio("Yes", "ica_option", key='-ICA_OPTION_YES-', default=False),
               sg.Radio("No", "ica_option", key='-ICA_OPTION_NO-', default=True)],
              [sg.Button('Ok')]]

    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                if values['-ICA_OPTION_YES-'] == True:
                    config['apply_ica'] = 1
                    # config = ask_nr_ica_components(
                    #     config)    # ask how many components => move to file loop
                else:
                    config['apply_ica'] = 0
                break
            except:
                sg.popup_error('No valid value', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_epoch_selection(config):
    tooltip = """Do you want to apply epoch selection?
    The alternative is to export uncut data"""

    url = "https://mne.tools/stable/generated/mne.Epochs.html#mne.Epochs.plot"
    layout = [[sg.Text("Apply epoch selection", tooltip=tooltip)],
              [sg.Radio("Yes", "epsel", key='-EPOCH_SELECTION_YES-', default=True),
              sg.Radio("No", "epsel", key='-EPOCH_SELECTION_NO-', default=False), sg.Button('More info')],
              [sg.Button('Ok')]]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'More info':
            wb.open_new_tab(url)
            continue
        if event == 'Ok':
            try:
                if values['-EPOCH_SELECTION_YES-'] == True:
                    config['epoch_selection'] = 1
                    config = ask_epoch_length(
                        config)    # ask epoch length
                else:
                    config['epoch_selection'] = 0
                break
            except:
                sg.popup_error('No valid value', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_input_file_pattern(config):
    # note: input_file_patterns read from config file
    tooltip = 'Enter one filetype and electrode layout: .bdf 32ch, .bdf 64ch, .bdf 128ch, .edf biosemi 32 layout, .edf biosemi 64 layout, .edf biosemi 128 layout, .edf general 10-20 layout, .eeg, .txt biosemi 32 layout, .txt biosemi 64 layout, .txt general 10-20 layout, see https://mne.tools/dev/auto_tutorials/intro/40_sensor_locations.html for the electrode layouts (montages) used'
    layout = [
        [sg.Text("Enter file type", tooltip=tooltip)],
        [sg.Listbox(values=input_file_patterns, size=(15, None), enable_events=True, bind_return_key=True,
                    select_mode='single', key='_LISTBOX_', background_color='light blue')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=("Ubuntu Medium", 13), location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                selection = values["_LISTBOX_"]
                selection = selection[0]
                # check if valid selection was made, else raise exception
                index = input_file_patterns.index(selection)
                config['input_file_pattern'] = selection
                break
            except:
                sg.popup_error('No valid selection', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def select_channels_to_be_dropped(in_list):
    tooltip = "select one or more channels to be dropped, just press OK if you don't want to"
    items = in_list
    txt = "Select channels to be dropped (if any)\nNote: for ICA make sure to drop at least S1,S2/VO,VB,HR,HL,MR,ML,Nose"

    layout = [
        [sg.Text(txt, tooltip=tooltip)],
        [sg.Listbox(values=items, size=(15, 30), enable_events=True, bind_return_key=True,
                    select_mode='multiple', key='_LISTBOX_', background_color='light blue')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=("Ubuntu Medium", 13), location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                out_list = values["_LISTBOX_"]
                break
            except:
                sg.popup_error('No valid selection', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return out_list


def select_components_to_be_dropped(max_comp):
    tooltip = "select one or more components to be dropped, just press OK if you don't want to"
    txt = "Select components to be dropped (if any)"
    items = list(range(0, max_comp))  # @@@ numbering starts at 0
    layout = [
        [sg.Text(txt, tooltip=tooltip)],
        [sg.Listbox(values=items, size=(15, 30), enable_events=True, bind_return_key=True,
                    select_mode='multiple', key='_LISTBOX_C_', background_color='light blue')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=("Ubuntu Medium", 13), location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                out_list = values["_LISTBOX_C_"]
                break
            except:
                sg.popup_error('No valid selection', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return out_list


def ask_skip_input_file(config):
    ch = sg.popup_yes_no("Do you want to skip this file?",
                         title="YesNo", location=(100, 100))
    if ch == 'Yes':
        config['skip_input_file'] = 1
    else:
        config['skip_input_file'] = 0
    return config


def ask_sample_frequency(config):
    # note: sample_frequencies read from config file
    tooltip = 'xxx'
    layout = [
        [sg.Text("Select sample frequency", tooltip=tooltip)],
        [sg.Listbox(values=sample_frequencies, size=(15, None), enable_events=True, bind_return_key=True,
                    select_mode='single', key='_LISTBOX_', background_color='light blue')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=("Ubuntu Medium", 13), location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                selection = values["_LISTBOX_"]
                selection = selection[0]
                config['sample_frequency'] = selection
                break
            except:
                sg.popup_error('No valid selection')
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_epoch_length(config):
    tooltip = 'Enter a number for epoch length between 1 and 100 seconds (int or float)'
    layout = [
        [sg.Text("Enter epoch length in seconds:", tooltip=tooltip)],
        [sg.InputText(default_text=default_epoch_length,
                      key='-EPOCH_LENGTH-')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                config['epoch_length'] = float(values["-EPOCH_LENGTH-"])
                break
            except:
                sg.popup_error('No valid number', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_nr_ica_components(config):
    tooltip = 'Enter number of ICA components'
    layout = [
        [sg.Text("Enter number of ICA components:",
                 tooltip=tooltip)],
        [sg.InputText(default_text=default_ica_components,
                      key='-ICA_COMPONENTS-')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                config['ica_components'] = int(values["-ICA_COMPONENTS-"])
                # set to min (ica_components, max components(config['max_channels'])) @@@
                break
            except:
                sg.popup_error('No valid integer value', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_downsample_factor(config):
    tooltip = 'Enter a whole number to downsample by between 1 (no downsampling) and 100 (see https://mne.tools/stable/generated/mne.filter.resample.html)'
    layout = [
        [sg.Text("Enter downsample factor (1 equals no downsampling):", tooltip=tooltip)],
        [sg.InputText(default_text=default_downsample_factor,
                      key='-DOWNSAMPLE_FACTOR-')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                config['downsample_factor'] = int(
                    values["-DOWNSAMPLE_FACTOR-"])
                break
            except:
                sg.popup_error('No valid integer value', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_logfile_prefix(config):
    tooltip = 'Enter a prefix (name) for the log file. The log file will be named <prefix><timestamp>.log'
    layout = [
        [sg.Text("Enter prefix (e.g. your name) for the log file:", tooltip=tooltip)],
        [sg.InputText(key='-LOGFILE_PREFIX-')],
        [sg.Button('Ok')]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=(
        "Ubuntu Medium", 13), background_color='light blue', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                prefix = values["-LOGFILE_PREFIX-"]
                if not prefix:
                    sg.popup_error('No valid prefix', location=(
                        100, 100))  # empty string
                    window.close()
                config['logfile_prefix'] = prefix
                break
            except:
                # not sure if except is needed
                sg.popup_error('No value', location=(100, 100))
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def create_dict():  # create initial dict for manual processing
    try:
        config = {'average_ref': 1,
                  'epoch_selection': 0,
                  'epoch_length': 0.0,
                  'apply_ica': 0,
                  'ica_components': 0,
                  'max_channels': 0,  # max channels for IA, determine per input file
                  'skip_input_file': 0,
                  'n_channels': 64,  # ??? not used
                  'downsample_factor': 100,
                  'file_pattern': '-',
                  'input_file_pattern': "-",
                  'montage': '-',
                  'input_files': [],
                  'channel_names': [],
                  'sample_frequency': 250,
                  'epoch_directory': 'C:\\AgileInzichtShare\\Engagements\\UMC\\Preprocessing EEG\\output',
                  'logfile_prefix': 'herman'}

        return config
    except:
        sg.popup_error('Error create_dict:', location=(100, 100))
        window.close()
    return

### Functions for exporting data
def extract_epoch_data(raw_output, epoch_length, selected_indices, sfreq,filtering=False,l_freq=0, h_freq=0, l_trans=0, h_trans=0):
    if filtering: 
        raw_output= raw_output.copy().filter(l_freq=l_freq, h_freq=h_freq, picks='eeg', l_trans_bandwidth=l_trans, h_trans_bandwidth=h_trans) 
    events_out = mne.make_fixed_length_events(raw_output, duration=epoch_length)
    epochs_out = mne.Epochs(raw_output, events=events_out, tmin=0, tmax=(epoch_length - (1 / sfreq)),
                            baseline=(0, epoch_length))
    selected_epochs_out = epochs_out[selected_indices]
    selected_epochs_out.drop_bad()
    return selected_epochs_out   

# def save_epoch_data_to_txt(epoch_data, output_directory, file_suffix, scalings):
#     for i in range(len(epoch_data)):
#         epoch_df = epoch_data[i].to_data_frame(picks='eeg', scalings=scalings)
#         epoch_df = epoch_df.drop(columns=['time', 'condition', 'epoch'])
#         epoch_df = np.round(epoch_df, decimals=4)
#         file_name = os.path.basename(root) + file_suffix + "Epoch" + str(i + 1) + ".txt"
#         file_name_out = os.path.join(output_directory, file_name)
#         epoch_df.to_csv(file_name_out, sep='\t', index=False) 
        
#         msg = 'Output file ' + file_name_out + ' created'
#         window['-FILE_INFO-'].update(msg+'\n', append=True)
#         progress_bar2.UpdateBar(i+1) 
        
        
def save_epoch_data_to_txt(file_path, epoch_data, output_directory, file_suffix, scalings):
    # Extract the base name without extension for the folder creation
    eeg_file_base_name = os.path.splitext(os.path.basename(file_path))[0]
    subfolder_path = os.path.join(output_directory, eeg_file_base_name)
    
    # Ensure the directory exists
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)
    
    # Process each epoch and save the data
    for i in range(len(epoch_data)):
        epoch_df = epoch_data[i].to_data_frame(picks='eeg', scalings=scalings)
        epoch_df = epoch_df.drop(columns=['time', 'condition', 'epoch'])
        epoch_df = np.round(epoch_df, decimals=4)
        file_name = eeg_file_base_name + file_suffix + "Epoch" + str(i + 1) + ".txt"
        file_name_out = os.path.join(subfolder_path, file_name)
        epoch_df.to_csv(file_name_out, sep='\t', index=False)
        
        msg = 'Output file ' + file_name_out + ' created'
        window['-FILE_INFO-'].update(msg+'\n', append=True)
        progress_bar2.UpdateBar(i + 1)


def save_selection_to_excel(file_path, selected_indices, bad_channels, epoch_directory):
    """
    Save the epoch selection and bad channels to an Excel file with a timestamp.
    :param file_path: Path of the EEG file
    :param selected_indices: List of selected epoch indices
    :param bad_channels: List of bad channels
    :param epoch_directory: Directory where the Excel file should be saved
    """
    filename = os.path.basename(file_path)
    # Ensure all elements are strings
    selected_indices = [str(idx) for idx in selected_indices]  # Convert numpy array to list of strings
    bad_channels = [str(channel) for channel in bad_channels]

    # Get the current date and time
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    # Create the Excel filename
    excel_filename = f"epoch_selection_{timestamp}.xlsx"
    excel_file = os.path.join(epoch_directory, excel_filename)

    # Prepare the data for epoch selection and bad channels
    epoch_data = [filename] + selected_indices
    bad_channels_data = [filename] + bad_channels

    try:
        if not any(fname.startswith("epoch_selection_") and fname.endswith(".xlsx") for fname in os.listdir(epoch_directory)):
            # Create the file with timestamp in name
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                pd.DataFrame([epoch_data]).to_excel(writer, index=False, header=False, sheet_name='Selections')
                pd.DataFrame([bad_channels_data]).to_excel(writer, index=False, header=False, sheet_name='Selections', startrow=1)
            print(f"Excel file created at: {os.path.abspath(excel_file)}")
        else:
            # Find the existing file
            existing_file = next(fname for fname in os.listdir(epoch_directory) if fname.startswith("epoch_selection_") and fname.endswith(".xlsx"))
            existing_file_path = os.path.join(epoch_directory, existing_file)
            with pd.ExcelWriter(existing_file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                existing_df = pd.read_excel(existing_file_path, engine='openpyxl', sheet_name='Selections')
                startrow = existing_df.shape[0]  # add new data after the last row
                pd.DataFrame([epoch_data]).to_excel(writer, index=False, header=False, sheet_name='Selections', startrow=startrow+ 1)
                pd.DataFrame([bad_channels_data]).to_excel(writer, index=False, header=False, sheet_name='Selections', startrow=startrow + 2)
            print(f"Excel file updated at: {os.path.abspath(existing_file_path)}")
    except Exception as e:
        print(f"Error saving to Excel: {e}")
        print(traceback.format_exc())



# start loop
window1 = make_win1()
progress_bar = window1.FindElement('progressbar')
progress_bar2 = window1.FindElement('progressbar2')

# removed while loop
while True:  # @noloop remove
    window,  event, values = sg.read_all_windows()

    if event == 'Enter parameters for this batch':
        config = create_dict()  # before file loop
        config = select_input_files(config)  # before file loop
        config = ask_input_file_pattern(config)
        # sample frequency of bdf, eeg and edf are available in raw
        if (config['input_file_pattern'].find('.txt') >= 0):
            config = ask_sample_frequency(
                config)  # ask sample frequency
            sample_frequency = config['sample_frequency']  # check
        config = select_epoch_directory(config)  # before file loop
        config = ask_average_ref(config)
        config = ask_epoch_selection(config)
        config = ask_ica_option(config)
        config = ask_downsample_factor(config)
        config = ask_logfile_prefix(config)  # before file loop
        msg = 'You may now start processing'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        # print(config)

    if event == 'Start processing':
        try:
            msg = 'epoch_directory: ' + config['epoch_directory']
            window['-FILE_INFO-'].update(msg+'\n', append=True)

            # Adjust the file extension as needed to recognize the correct file type
            if config['input_file_pattern'] == ".txt bio32":
                montage = mne.channels.make_standard_montage("biosemi32")
                config['file_pattern'] = "*.txt"
            elif config['input_file_pattern'] == ".txt bio64":
                montage = mne.channels.make_standard_montage("biosemi64")
                config['file_pattern'] = "*.txt"
            elif config['input_file_pattern'] == ".txt 10-20":
                montage = mne.channels.make_standard_montage("standard_1020")
                config['file_pattern'] = "*.txt"
            elif config['input_file_pattern'] == ".bdf 32":
                montage = mne.channels.make_standard_montage("biosemi32")
                config['file_pattern'] = "*.bdf"
            elif config['input_file_pattern'] == ".bdf 64":
                montage = mne.channels.make_standard_montage("biosemi64")
                config['file_pattern'] = "*.bdf"
            elif config['input_file_pattern'] == ".bdf 128":
                montage = mne.channels.make_standard_montage("biosemi128")
                config['file_pattern'] = "*.bdf"
            elif config['input_file_pattern'] == ".edf bio32":
                montage = mne.channels.make_standard_montage("biosemi32")
                config['file_pattern'] = "*.edf"
            elif config['input_file_pattern'] == ".edf bio64":
                montage = mne.channels.make_standard_montage("biosemi64")
                config['file_pattern'] = "*.edf"
            elif config['input_file_pattern'] == ".edf bio128":
                montage = mne.channels.make_standard_montage("biosemi128")
                config['file_pattern'] = "*.edf"
            elif config['input_file_pattern'] == ".edf 10-20":
                montage = mne.channels.make_standard_montage("standard_1020")
                config['file_pattern'] = "*.edf"
            elif config['input_file_pattern'] == ".edf GSN-Hydrocel 64":
                montage = mne.channels.make_standard_montage("GSN-HydroCel-64_1.0")
                config['file_pattern'] = "*.edf"   
            elif config['input_file_pattern'] == "easycap-M1":
                montage = mne.channels.make_standard_montage("easycap-M1")
                config['file_pattern'] = "*.fif"  
            elif config['input_file_pattern'] == ".eeg":
                config['file_pattern'] = "*.vhdr"
            
            else:
                print("Unrecognized filetype ",
                      config['input_file_pattern'], " of raw file")
            pprint.pprint(dict(config), indent=6, width=1)
            
            
            # progess bar vars
            lfl = len(config['input_files'])
            filenum = 0

            # Iterate through each file and open it
            for file_path in config['input_files']:  # @noloop do not execute
                # file_path="C:/AgileInzichtShare/Engagements/UMC/Yorben/Nieuwe functies/Bestanden Herman 22022024/Bestanden Herman 22022024/s041_512Hz_64ch_aver_ref.txt"

                msg = 'Processing file ' + file_path
                window['-FILE_INFO-'].update(msg+'\n', append=True)
                if config['file_pattern'] == "*.txt":
                    with open(file_path, "r") as file:
                        df = pd.read_csv(
                            file, sep='\t', index_col=False, header=0)
                    # get channel names if not yet done
                    if config['channel_names'] == []:  # only do this once
                        ch_names = list(df.columns)
                        config['channel_names'] = ch_names
                    ch_types = ["eeg"]*len(ch_names)
                    info = mne.create_info(
                        ch_names=ch_names, sfreq=sample_frequency, ch_types=ch_types)
                    df = df.iloc[:, 0:len(ch_names)]
                    samples = df.T*1e-6  # Scaling from µV to V
                    # Create raw EEG object compatible with MNE functions
                    raw = mne.io.RawArray(samples, info)
                    # check for NaN columns and issie warning
                    missing = df.columns[df.isna().any()].tolist()
                    if missing != '[]':
                        sg.popup_ok('Warning: channels with missing values found:',
                                    missing, "please drop these channel(s)!", location=(100, 100))
                elif config['file_pattern'] == "*.bdf":
                    raw = mne.io.read_raw_bdf(file_path, preload=True)
                elif config['file_pattern'] == "*.vhdr":
                    raw = mne.io.read_raw_brainvision(file_path, preload=True)
                elif config['file_pattern'] == "*.edf":
                    raw = mne.io.read_raw_edf(file_path, preload=True)
                elif config['file_pattern'] == "*.fif" :
                    raw = mne.io.read_raw_fif(file_path, preload=True)
                # read sample freq from raw
                if config['file_pattern'] != "*.txt":  # take sfreq from raw
                    sample_frequency = raw.info["sfreq"]
                    # update dict
                    config['sample_frequency'] = sample_frequency
                    # print ('sample_frequency',sample_frequency)

                # Set montage for electrodes (provides 3D coordinates for each electrode position, needed for channel interpolation)
                if config['file_pattern'] != "*.vhdr":
                    raw.set_montage(montage=montage, on_missing='ignore')
                # print(mne.channel_indices_by_type(raw.info))

                # Drop channels
                if not to_be_dropped_selected:
                    channel_names = raw.ch_names
                    to_be_dropped = select_channels_to_be_dropped(
                        channel_names)  # ask user to select
                    to_be_dropped_selected = True
                raw.drop_channels(to_be_dropped)
                
                # Temporary raw file to work with during preprocessing, raw is used to finally export epochs
                raw_temp = raw.copy()
                
                # determine max nr_channels (= upper limit of nr_components) @@@
                max_channels = len(raw.ch_names)-1  # @@@ check
                # store for later use
                config['max_channels'] = int(max_channels)
                
                # Plot power spectrum
                fig = raw_temp.compute_psd(fmax=60).plot(
                    picks="eeg")  # Plot raw power spectrum
                axes = fig.get_axes()
                axes[0].set_title("Unfiltered power spectrum")
                fig.tight_layout(rect=[0, 0, 1, 0.95])
                fig.canvas.draw()
                
                # Filter before dropping bad channels
                raw_temp.filter(l_freq=0.5, h_freq=48, l_trans_bandwidth=0.25, h_trans_bandwidth=1, picks='eeg')                 

                # Select bad channels interactively
                raw_temp.plot(n_channels=len(
                    raw.ch_names), block=True, title="Bandpass filtered data")
                ask_skip_input_file(config)

                # Retrieve the list of bad channels to use during export of the final file
                bad_channels = raw_temp.info['bads']
                
                # @@@ ask if file should be skipped
                # ask_skip_input_file(config)
                if config['skip_input_file'] == 1:
                    msg = 'File ' + file_path + ' skipped'
                    window['-FILE_INFO-'].update(msg+'\n', append=True)
                    filenum = filenum+1
                    progress_bar.UpdateBar(filenum, lfl)
                    continue
                
                # Interpolate or drop bad channels
                raw_interp = raw_temp.copy()
                raw_interp.interpolate_bads(reset_bads=True)
                    
                if config['apply_ica']:
                    # ask # components (this is per file)
                    msg = 'Max # components = ' + \
                        str(config['max_channels'])
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                    config = ask_nr_ica_components(
                        config)    # ask how many components ( check max_channels!) @@@
                    
                    # Preparation of clean raw object to calculate ICA on
                    raw_ica = raw.copy()
                    raw_ica.filter(l_freq=1, h_freq=48, l_trans_bandwidth=0.5, h_trans_bandwidth=1)
                    
                    raw_ica.info['bads'] = bad_channels 
                    raw_ica.interpolate_bads(reset_bads=True)

                    # Fitting the ICA
                    ica = ICA(n_components=config['ica_components'],
                              method='fastica')
                    ica.fit(raw_ica,  picks='eeg')
                    ica

                    # Plot ICA results
                    ica.plot_components()  # heat map hoofd
                    ica.plot_sources(raw_ica, block=False)  # source

                    # https://mne.discourse.group/t/variance-of-ica-components/5544/2
                    # unitize variances explained by PCA components, so the values sum to 1
                    pca_explained_variances = ica.pca_explained_variance_ / \
                        ica.pca_explained_variance_.sum()
                    # Now extract the variances for those components that were used to perform ICA
                    ica_explained_variances = pca_explained_variances[:ica.n_components_]
                    cumul_pct = 0.0
                    # for idx, var in enumerate(ica_explained_variances):
                    #     pct=str(round(100 * var, 1))
                    #     msg = 'Explained variance for ICA component ' + \
                    #         str(idx) + ': ' + str(round(100 * var, 1)) + '%'
                    #     window['-RUN_INFO-'].update(msg+'\n', append=True)
                    for idx, var in enumerate(ica_explained_variances):
                        pct = round(100 * var, 2)
                        cumul_pct += pct
                        msg = 'Explained variance for ICA component ' + \
                            str(idx) + ': ' + str(pct) + '%' + \
                            ' ('+str(round(cumul_pct, 1)) + ' %)'
                        window['-RUN_INFO-'].update(msg+'\n', append=True)

                    # ask which components to be deselected @@@
                    max_comp = config['ica_components']
                    components_to_be_dropped = select_components_to_be_dropped(
                        max_comp)
                    # input_string = input(
                    #     "Please enter bad IC's (integers) separated by commas: ")
                    # # Split the input string into components based on commas
                    # string_list = input_string.split(',')
                    # # Convert each component into an integer and store in a list
                    # integer_list = [int(item.strip()) for item in string_list]
                    if len(components_to_be_dropped) > 0:
                        ica.exclude = components_to_be_dropped

                    # Apply ICA
                    ica.apply(raw_interp)
                    
                
                # For beamforming, interpolated channels need to be dropped first
                if beamforming:
                    raw_beamform = raw_interp.copy()
                    raw_beamform.drop_channels(bad_channels)
                    msg = "channels left in raw_beamform: " + str(len(raw_beamform.ch_names))
                    window['-RUN_INFO-'].update(msg+'\n', append=True)  
     
                # Downsample to 250 or 256 Hz to facilitate quick processing (if not beamforming)
                if beamforming == False:
                    if config['sample_frequency']%256 == 0:
                        raw_resample_f = 256
                    else:
                        raw_resample_f = 250       
                    raw_interp.resample(raw_resample_f, npad="auto")  
                else:
                    raw_resample_f = config['sample_frequency']
                                      

                # Plot power spectrum again
                fig2 = raw_interp.compute_psd(fmax=60).plot(
                    picks='eeg', exclude=[])  # Plot filtered power spectrum
                axes2 = fig2.get_axes()
                axes2[0].set_title(
                    "Band 0.5-48 Hz filtered power spectrum. FIR transition bandwidths 0.25 and 1 Hz resp.")
                fig2.tight_layout(rect=[0, 0, 1, 0.95])
                fig2.canvas.draw()

                # Set average reference
                raw_interp.set_eeg_reference(
                    'average', projection=True, ch_type='eeg')
                raw_interp.apply_proj()  # Apply the average reference as a projector
                if beamforming:
                    raw_beamform.set_eeg_reference(
                        'average', projection=True, ch_type='eeg')
                    raw_beamform.apply_proj()  

                if config['epoch_selection']:
                    # Cut epochs 
                    events = mne.make_fixed_length_events(raw_interp, duration = config['epoch_length']) # Create epoch starting points
                    epochs = mne.Epochs(raw_interp, events=events, tmin=0, tmax=(config['epoch_length']-(1/raw_resample_f)), baseline=(0, config['epoch_length']))

                    # Generate events at each second
                    # One event ID for each second
                    time_event_ids = np.arange(
                        config['epoch_length']*len(events))
                    time_event_samples = (raw_resample_f * time_event_ids).astype(int)
                    time_events = np.column_stack(
                        (time_event_samples, np.zeros_like(time_event_samples), time_event_ids))

                    # Plot the epochs for visual inspection
                    epochs.plot(n_epochs=1, n_channels=len(
                        raw.ch_names), events=time_events, block=True, picks=['eeg', 'eog', 'ecg'])

                    # Retrieve the indices of the selected epochs to use during export of the final files
                    selected_indices = epochs.selection
                    print(selected_indices)
                    
                    # Save epoch selection to excel file row
                    save_selection_to_excel(file_path, selected_indices, bad_channels, config['epoch_directory'])



                if beamforming:
                    # Forward Problem:
                    fs_dir = fetch_fsaverage(verbose=True)
                    subjects_dir = os.path.dirname(fs_dir)
                    subject = "fsaverage"
                    trans = "fsaverage"     # standard MNE fsaverage transformation
            
                    # Loading boundary-element model
                    bem = os.path.join(fs_dir, "bem", "fsaverage-5120-5120-5120-bem-sol.fif")
            
                    # Setting up source space according to Desikan-Killiany atlas
                    DesikanVox = pd.read_excel('DesikanVox.xlsx', header=None)
                    Voxels_pos = DesikanVox.values
                    Voxels_pos = Voxels_pos.astype(float)
            
                    Voxels_nn = -Voxels_pos
                    # Normalize the normals to unit length
                    Voxels_nn /= np.linalg.norm(Voxels_nn, axis=1)[:, np.newaxis]
            
                    Voxels_pos_dict = {'rr': Voxels_pos, 'nn': Voxels_nn}
            
                    src = mne.setup_volume_source_space(
                        subject=subject, 
                        pos=Voxels_pos_dict, 
                        mri= None, 
                        bem=bem, 
                        )

                    label_names = mne.read_labels_from_annot('fsaverage', parc='aparc', hemi='both', subjects_dir=subjects_dir)
                    source_labels = [label.name for label in label_names if 'unknown' not in label.name.lower()]
            
                    ## Forward Solution
                    fwd = mne.make_forward_solution(
                        raw_beamform.info, 
                        trans=trans, 
                        src=src, 
                        bem=bem,
                        eeg=True, 
                        mindist=0, 
                        n_jobs=None
                    )
            
                    ## Inverse Problem
                    # covariance matrix
                    data_cov = mne.compute_raw_covariance(raw_beamform)
            
                    # noise covariance matrix
                    noise_matrix = np.zeros_like(data_cov['data'])  # Create a new matrix noise_matrix with the same size as data_cov
                    diagonal_values = np.diag(data_cov['data'])
                    np.fill_diagonal(noise_matrix, diagonal_values) # Set the diagonal values of noise_matrix to the diagonal values of data_cov
                    noise_cov = mne.Covariance(data=noise_matrix, 
                                            names=data_cov['names'], 
                                            bads=data_cov['bads'], 
                                            projs=data_cov['projs'],
                                            nfree=data_cov['nfree']
                                            )
            
                    # LCMV beamformer
                    spatial_filter = make_lcmv(raw_beamform.info, 
                                       fwd,
                                       data_cov,
                                       reg=0.05,
                                       noise_cov = noise_cov,
                                       pick_ori='max-power',
                                       weight_norm='unit-noise-gain',
                                       rank=None,
                                       )
                    # Apply LCMV beamformer
                    # stc = apply_lcmv_raw(raw_beamform, spatial_filter) 
                
                                           
                ### Preparation of the final raw file and epochs for export
                
                # Apply the chosen bad channels to the output raw object(s)
                raw.info['bads'] = bad_channels

                # Interpolate bad channels on the second Raw object
                raw.interpolate_bads(reset_bads=True)
                msg = "Interpolated " + str(len(bad_channels)) + " channels on (non-beamformed) output signal"
                window['-RUN_INFO-'].update(msg+'\n', append=True)                

                if config['apply_ica'] or beamforming:
                    raw.filter(l_freq=0.5, h_freq=48, l_trans_bandwidth=0.25,
                               h_trans_bandwidth=1, picks='eeg')
                    msg = "Output signal filtered to 0.5-48 Hz (transition bands 0.25 Hz and 1 Hz resp. Necessary for ICA and/or Beamforming"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)  
                
                if config['apply_ica']:
                    ica.apply(raw)
                    msg = "Ica applied to output signal"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)  

                # Set EEG average reference (optional)
                if config['average_ref']:
                    raw.set_eeg_reference(
                        'average', projection=True, ch_type='eeg')
                    raw.apply_proj()  # Apply the average reference as a projector
                    msg = "Average reference set on output signal"
                else:
                    msg = "No rereferencing applied"
                window['-RUN_INFO-'].update(msg+'\n', append=True)
                
                # Copy exported raw object before applying possible downsampling
                if beamforming:
                    raw_beamform_output = raw.copy()
                    raw_beamform_output.drop_channels(bad_channels)
                    msg = "Dropped " + str(len(bad_channels)) + " bad channels on beamformed output signal" 
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                    msg = "The EEG file used for beamforming now contains " + str(len(raw_beamform_output.ch_names)) + " channels"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                
                # Downsample to preferred sample frequency if factor is not 1
                downsampled_sample_frequency = config['sample_frequency']//config['downsample_factor']
                if config['downsample_factor'] != 1:   
                    raw.resample(downsampled_sample_frequency, npad="auto")
                    msg = "Non-beamformed output signal downsampled to " + \
                    str(downsampled_sample_frequency) + " Hz" 
                else:
                    msg = "No downsampling applied to output signal"
                window['-RUN_INFO-'].update(msg+'\n', append=True)                

                # Split the file path and extension to use when constructing the output file names
                root, ext = os.path.splitext(file_path)
                
                if beamforming:                     
                    # Load Desikan area labels for source channel names
                    desikanlabels = pd.read_csv('DesikanVoxLabels.csv', header=None)
                    desikan_channel_names = desikanlabels[0].tolist()                        
                    
                    # Apply beamformer again to export raw object
                    stc = apply_lcmv_raw(raw_beamform_output, spatial_filter)
                    info = mne.create_info(ch_names=desikan_channel_names, sfreq=config['sample_frequency'], ch_types='eeg')
                    rawSource = mne.io.RawArray(stc.data, info)
                    rawSource.resample(downsampled_sample_frequency, npad="auto")    
                    msg = "Beamformed output signal downsampled to " + \
                          str(downsampled_sample_frequency) + " Hz"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)                 

                # Create output epochs and export to .txt (non-beamformed)
                if config['epoch_selection']:
                    
                    selected_epochs_out = extract_epoch_data(raw, config['epoch_length'], selected_indices, downsampled_sample_frequency)
                    
                    len2 = len(selected_epochs_out)
                    progress_bar2.UpdateBar(0, len2)
                    epoch_export_name = "_Sensor_level_broadband_05-48_" if beamforming or config['apply_ica'] else "_Sensor_level_nofilter_"
                    save_epoch_data_to_txt(file_path, selected_epochs_out, config['epoch_directory'], epoch_export_name, None)
                    
                    if filtering:
                        for band in ["broadband_05-48","delta","theta","alpha","beta"]:
                            if band=="broadband_05-48":
                                if beamforming or config['apply_ica']:
                                    continue
                                l_trans=0.5*broadband_low
                                low=broadband_low
                                high=broadband_high
                            elif band=="delta":
                                l_trans=None if beamforming or config['apply_ica'] else 0.5*delta_low
                                low=None if beamforming or config['apply_ica'] else delta_low
                                high=delta_high
                            elif band=="theta":
                                l_trans=1
                                low=theta_low
                                high=theta_high
                            elif band=="alpha":
                                l_trans=1
                                low=alpha_low
                                high=alpha_high
                            elif band=="beta":
                                l_trans=1
                                low=beta_low
                                high=beta_high
                                
                            name_ext = "_Sensor_level_" + band + "_"
                            selected_epochs_out = extract_epoch_data(raw, config['epoch_length'], selected_indices, downsampled_sample_frequency,filtering=True,l_freq=low, h_freq=high, l_trans=l_trans, h_trans=1)
                            save_epoch_data_to_txt(file_path, selected_epochs_out, config['epoch_directory'], name_ext, None)

                        
                    if beamforming:                     
                        # Export beamformed epochs
                        epoch_data_source = extract_epoch_data(rawSource, config['epoch_length'], selected_indices, downsampled_sample_frequency)
                        save_epoch_data_to_txt(file_path, epoch_data_source, config['epoch_directory'], "_Source_level_broadband_05-48_", dict(eeg=1, mag=1e15, grad=1e13))
                        
                        if filtering:
                            for band in ["delta","theta","alpha","beta"]:
                                if band=="delta":
                                    l_trans=None
                                    low=None
                                    high=delta_high
                                elif band=="theta":
                                    l_trans=1
                                    low=theta_low
                                    high=theta_high
                                elif band=="alpha":
                                    l_trans=1
                                    low=alpha_low
                                    high=alpha_high
                                elif band=="beta":
                                    l_trans=1
                                    low=beta_low
                                    high=beta_high
                                    
                                name_ext = "_Source_level_" + band + "_"
                                epoch_data_source_filt = extract_epoch_data(rawSource, config['epoch_length'], selected_indices, downsampled_sample_frequency,filtering=True,l_freq=low, h_freq=high, l_trans=l_trans, h_trans=1)
                                save_epoch_data_to_txt(file_path, epoch_data_source_filt, config['epoch_directory'], name_ext, dict(eeg=1, mag=1e15, grad=1e13))
                                                                                                
                else:
                    msg = "No epoch selection performed"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                    # Extract the data into a DataFrame
                    raw_df = raw.to_data_frame(picks='eeg')
                    raw_df = raw_df.iloc[:, 1:]  # Drop first (time) column
                    raw_df = np.round(raw_df, decimals=4)
                    
                    # Define the file name
                    epoch_export_extension = "_Sensor_level_broadband_05-48.txt" if beamforming or config['apply_ica'] else "_Sensor_level_nofilter.txt"
                    file_name_sensor = os.path.basename(root) + epoch_export_extension
                    
                    # Define the output file path
                    file_path_sensor = os.path.join(
                        config['epoch_directory'], file_name_sensor)

                    # Save the DataFrame to a text file
                    raw_df.to_csv(file_path_sensor, sep='\t', index=False)
                    progress_bar2.UpdateBar(1, 1)

                    if filtering:
                        for band in ["broadband_05-48","delta","theta","alpha","beta"]:
                            if band=="broadband_05-48":
                                if beamforming or config['apply_ica']:
                                    continue
                                l_trans=0.5*broadband_low
                                low=broadband_low
                                high=broadband_high
                            elif band=="delta":
                                l_trans=None if beamforming or config['apply_ica'] else 0.5*delta_low
                                low=None if beamforming or config['apply_ica'] else delta_low
                                high=delta_high
                            elif band=="theta":
                                l_trans=1
                                low=theta_low
                                high=theta_high
                            elif band=="alpha":
                                l_trans=1
                                low=alpha_low
                                high=alpha_high
                            elif band=="beta":
                                l_trans=1
                                low=beta_low
                                high=beta_high   
                            
                            raw_output_filt = raw.copy().filter(l_freq=low, h_freq=high, picks='eeg', l_trans_bandwidth=l_trans, h_trans_bandwidth=1) 
                            raw_df = raw_output_filt.to_data_frame(picks='eeg')
                            raw_df = raw_df.iloc[:, 1:]  # Drop first (time) column
                            raw_df = np.round(raw_df, decimals=4)
                            file_name_sensor = os.path.basename(root) + "_Sensor_level_" + band + ".txt"    
                            file_path_sensor = os.path.join(
                                config['epoch_directory'], file_name_sensor)
                            raw_df.to_csv(file_path_sensor, sep='\t', index=False)
                            
                    
                    if beamforming:
                        rawSource_df = rawSource.to_data_frame(picks='eeg', scalings=dict(eeg=1, mag=1e15, grad=1e13))
                        rawSource_df = rawSource_df.iloc[:, 1:]  # Drop first (time) column
                        rawSource_df = np.round(rawSource_df, decimals=4)
                        file_name_source = os.path.basename(root) + "_Source_level_broadband_05-48.txt"
                        file_path_source = os.path.join(
                            config['epoch_directory'], file_name_source) 
                        rawSource_df.to_csv(file_path_source, sep='\t', index=False)
                        
                        if filtering:
                            for band in ["delta","theta","alpha","beta"]:
                                if band=="delta":
                                    l_trans=None
                                    low=None
                                    high=delta_high
                                elif band=="theta":
                                    l_trans=1
                                    low=theta_low
                                    high=theta_high
                                elif band=="alpha":
                                    l_trans=1
                                    low=alpha_low
                                    high=alpha_high
                                elif band=="beta":
                                    l_trans=1
                                    low=beta_low
                                    high=beta_high 
                                  
                                rawSource_filter = rawSource.copy().filter(l_freq=low, h_freq=high, picks='eeg', l_trans_bandwidth=l_trans, h_trans_bandwidth=1) 
                                rawSource_df = rawSource_filter.to_data_frame(picks='eeg', scalings=dict(eeg=1, mag=1e15, grad=1e13))
                                rawSource_df = rawSource_df.iloc[:, 1:]  # Drop first (time) column
                                rawSource_df = np.round(rawSource_df, decimals=4)
                                file_name_source = os.path.basename(root) + "_Source_level_" + band + ".txt"
                                file_path_source = os.path.join(
                                    config['epoch_directory'], file_name_source) 
                                rawSource_df.to_csv(file_path_source, sep='\t', index=False)

                filenum = filenum+1
                progress_bar.UpdateBar(filenum, lfl)
                # end of for loop

        # except:
        except Exception as e:
            print(traceback.format_exc())
            pprint.pprint(dict(config), indent=6, width=1)
            # sg.popup_error_with_traceback(f'Error - info:', e,location=(100, 100))
            sg.popup_error_with_traceback(
                'Error - info:', e)
            today = datetime.today()
            dt = today.strftime('%Y%m%d_%H%M%S')  # suffix
            fn = config['logfile_prefix'] + '_'+dt + '.log'
            file_name_out = os.path.join(config['epoch_directory'], fn)
            # with open(file_name_out, "wt", encoding='UTF-8') as f:
            #     f.write(window['-FILE_INFO-'].get())
            with open(file_name_out, "a", encoding='UTF-8') as f:
                f.write(traceback.format_exc())
                f.write(window['-FILE_INFO-'].get())
            # with open(file_name_out, "a", encoding='UTF-8') as f:
            #     f.write(traceback.format_exc())

            window.close()
            # break

        msg = 'Processing complete '
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        # write log window to file
        today = datetime.today()
        dt = today.strftime('%Y%m%d_%H%M%S')  # suffix
        fn = config['logfile_prefix'] + '_'+dt + '.log'
        file_name_out = os.path.join(config['epoch_directory'], fn)
        with open(file_name_out, "wt", encoding='UTF-8') as f:
            f.write(window['-RUN_INFO-'].get())
        with open(file_name_out, "a", encoding='UTF-8') as f:
            f.write(window['-FILE_INFO-'].get())

        msg = 'Log file created: ' + file_name_out
        window['-FILE_INFO-'].update(msg+'\n', append=True)
        # end of while loop @noloop unindent to this line

    # event, values = window1.read()
    # @noloop remove this section
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
        # pass
window.close()

# window.close()
