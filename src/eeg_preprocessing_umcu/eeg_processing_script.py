
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
import pickle
import posixpath
from pathlib import Path
# path handling
# from pathlib import Path
# import matplotlib
import traceback
import webbrowser as wb
# import pprint  # pretty print dict
from mne.preprocessing import ICA
# import matplotlib.pyplot as plt
from datetime import datetime
settings={} # suppress warnings
from eeg_processing_settings import *
from mne.beamformer import apply_lcmv_raw, make_lcmv
from mne.datasets import fetch_fsaverage


EEG_version = "v3.35"

progress_value1 = 20  # initial values
progress_value2 = 20

layout = [
    [sg.Text('EEG Preprocessing', size=(30, 1), font=("Ubuntu Medium", 35), text_color='#003DA6',
             justification='c'), sg.Text(EEG_version)],
    [sg.Multiline('File info: \n', autoscroll=True, size=(
        120, 10), k='-FILE_INFO-', reroute_stdout=True)],  # True=redirect console to window @@@
    [sg.Text('Functions:'), sg.Button(
        'Enter parameters for this batch'), sg.Button('Rerun previous batch'),sg.Button('Start processing')],
    [sg.Multiline('Run info: \n', autoscroll=True,
                  size=(120, 10), k='-RUN_INFO-', reroute_stdout=True)],  # True=redirect console to window @@@
    [sg.ProgressBar(progress_value1, orientation='h', size=(
        120, 10), key='progressbar', bar_color=['red', 'grey'])],
    [sg.ProgressBar(progress_value2, orientation='h', size=(
        120, 10), key='progressbar2', bar_color=['#003DA6', 'grey'])],
    [sg.Button('Exit')],
    [sg.Column([[my_image]], justification='center')]]

def print_dict(dict): # pprint and json.print do not work well with composite keys!
    for key in dict.keys():
        print(key, ":", dict[key])
        

def write_config_file(config):
    fn = config['configfile']
    # first remove raw data (legacy)
    config.pop('raw', None)  # remove from dict if exists
    config.pop('raw_temp', None)  # remove from dict if exists
    config.pop('raw_temp_filtered', None)  # remove from dict if exists
    config.pop('raw_interpolated', None)  # remove from dict if exists
    config.pop('raw_ica', None)  # remove from dict if exists
    config.pop('ica', None)  # remove from dict if exists
    config.pop('file_path', None)  # remove from dict, this is the current file_path in loop
    with open(fn, 'wb') as f:
        pickle.dump(config, f)
    return fn


def load_config(fn): 
    with open(fn, 'rb') as f:
        config = pickle.load(f)
    return config

def set_output_fn():  # for .log and .pkl
    today = datetime.today()
    dt = today.strftime('%Y%m%d_%H%M%S')  # suffix
    fn = config['logfile_prefix'] + '_'+dt + ext
    file_name_out = os.path.join(config['output_directory'], fn)
    return (file_name_out)

def set_output_file_names(config):  # for .log & .pkl
    today = datetime.today()
    dt = today.strftime('%Y%m%d_%H%M%S')  # suffix
    fn = config['logfile_prefix'] + '_'+dt + '.log'
    config['logfile'] = os.path.join(config['output_directory'], fn)
    fn = config['logfile_prefix'] + '_'+dt + '.pkl'
    config['configfile'] = os.path.join(config['output_directory'], fn)
    return (config)

def select_input_file_paths(config):
    # https://stackoverflow.com/questions/73764314/more-than-one-file-type-in-pysimplegui
    type_EEG = settings['input_file_paths','type_EEG']
    txt=settings['input_file_paths','text']
    # popup_get_file does not support tooltip
    f = sg.popup_get_file(txt,  title="File selector", multiple_files=True,font=font,
                          file_types=type_EEG,
                          background_color='white', location=(100, 100))
    file_list = f.split(";") 
    config['input_file_paths'] = file_list    
    return config

def load_config_file():    
    # file_types=(('.pkl files','*.pkl'),)
    txt=settings['load_config_file','text']
    pkl_file=sg.popup_get_file(txt,file_types=(('.pkl files','*.pkl'),),no_window=False,background_color='white', 
                               font=font,location=(100, 100))
    if type(pkl_file) != type(""): 
        sg.popup_error ("No file selected","Ok")
        exit()
    config=load_config(pkl_file)
    msg = '\nConfig ' + pkl_file + ' loaded for rerun\n'
    window['-RUN_INFO-'].update(msg+'\n', append=True)
    return config

def select_output_directory(config):
    tooltip = 'Output folder for exported epoch- and log files'
    working_directory = os.getcwd()
    layout = [
        [sg.Text(
            "Select folder to save processed EEG (epochs or uncut EEG) to", tooltip=tooltip)],
        [sg.InputText(default_text=working_directory, key="-FOLDER_PATH-"),
         sg.FolderBrowse(initial_folder=working_directory)],
        [sg.Button('Select')]
    ]
    window = sg.Window("Directory", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Select':
            try:
                config['output_directory'] = values["-FOLDER_PATH-"]
                break
            except:
                sg.popup_error('No valid folder', location=(100, 100),font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config

def ask_average_ref(config):
    txt = "Do you want to apply average reference to the raw EEG?"
    tooltip = """Do you want to apply average reference to the raw EEG?"""
    url = "https://mne.tools/stable/auto_tutorials/preprocessing/55_setting_eeg_reference.html"

    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True)],
              [sg.Button('Yes'), sg.Button('No')], [sg.Push(), sg.Button('More info...')]]

    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, 
                       font=font,background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'More info...':
            wb.open_new_tab(url)
            continue
        if event == 'Yes':
            config['apply_average_ref'] = 1
            break
        elif event == 'No':
            config['apply_average_ref'] = 0
            break
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config

def ask_ica_option(config):
    txt = "Do you want to apply ICA?\nNote: make sure to deselect electrodes with overlapping positions\ne.g. HR, ML, Nose"  # @@@
    tooltip = """Do you want to apply ICA?"""
    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True)],
              [sg.Button('Yes'), sg.Button('No')]]
    window = sg.Window("EEG processing input parameters", layout,  font=font,modal=True, use_custom_titlebar=True, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Yes':
            config['apply_ica'] = 1
            config = ask_nr_ica_components(
                config,settings)    # ask nr components
            break
        elif event == 'No':
            config['apply_ica'] = 0
            break
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_beamformer_option(config):
    txt = "Do you want to apply Beamforming?"  # @@@
    tooltip = """Do you want to apply Beamforming?"""
    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True)],
              [sg.Button('Yes'), sg.Button('No')]]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Yes':
            config['apply_beamformer'] = 1
            config['apply_average_ref'] = 1  # prereq for beamformer
            break
        elif event == 'No':
            config['apply_beamformer'] = 0
            break
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config

def ask_epoch_selection(config):
    tooltip = """Do you want to apply epoch selection?
    The alternative is to export uncut data"""
    txt = "Do you want to apply epoch selection?"
    url = "https://mne.tools/stable/generated/mne.Epochs.html#mne.Epochs.plot"
    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True)],
              [sg.Button('Yes'), sg.Button('No')], [sg.Push(), sg.Button('More info...')]]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'More info...':
            # os.system('cmd /c start chrome '+url) # force to use Chrome
            wb.open_new_tab(url)
            continue
        if event == 'Yes':
            config['apply_epoch_selection'] = 1
            config = ask_epoch_length(
                config,settings)    # ask epoch length
            break
        if event == 'No':
            config['apply_epoch_selection'] = 0
            break
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_input_file_pattern(config, settings):
    # note: input_file_patterns read from eeg_processing_config file
    txt=settings['input_file_patterns','text']
    tooltip=settings['input_file_patterns','tooltip']
    layout = [
        [sg.Text(txt, tooltip=tooltip)],
        [sg.Listbox(values=settings['input_file_patterns'], size=(15, None), enable_events=True, bind_return_key=True,
                    select_mode='single', key='_LISTBOX_', background_color='white')],
        [sg.Button('Ok', bind_return_key=True)]]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=font, location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                selection = values["_LISTBOX_"]
                selection = selection[0]
                # print(selection)
                # check if valid selection was made, else raise exception
                index = settings['input_file_patterns'].index(selection)
                config['input_file_pattern'] = selection
                break
            except:
                sg.popup_error('No valid selection', location=(100, 100),font=font)
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
                    select_mode='multiple', key='_LISTBOX_', background_color='white')],
        [sg.Button('Ok', bind_return_key=True,)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=font, location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                out_list = values["_LISTBOX_"]
                break
            except:
                sg.popup_error('No valid selection', location=(100, 100),font=font)
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
                    select_mode='multiple', key='_LISTBOX_C_', background_color='white')],
        [sg.Button('Ok', bind_return_key=True,)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=font, location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                out_list = values["_LISTBOX_C_"]
                break
            except:
                sg.popup_error('No valid selection', location=(100, 100),font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return out_list


def ask_skip_input_file(config):
    ch = sg.popup_yes_no("Do you want to skip this file?",
                         title="YesNo", location=(100, 100),font=font)
    if ch == 'Yes':
        config['skip_input_file'] = 1
    else:
        config['skip_input_file'] = 0
    return config


def ask_sample_frequency(config,settings):
    # note: only asked for .txt files, scope=batch
    # note: sample_frequencies read from config file
    tooltip = 'xxx'
    layout = [
        [sg.Text("Select sample frequency", tooltip=tooltip)],
        [sg.Listbox(values=settings['sample_frequencies'], size=(15, None), enable_events=True, bind_return_key=True,
                    select_mode='single', key='_LISTBOX_', background_color='white')],
        [sg.Button('Ok', bind_return_key=True,)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True,
                       use_custom_titlebar=True, font=font, location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                selection = values["_LISTBOX_"]
                selection = selection[0]
                config['sample_frequency'] = selection
                break
            except:
                sg.popup_error('No valid selection',font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_epoch_length(config,settings):
    tooltip = 'Enter a number for epoch length between 1 and 100 seconds (int or float)'
    layout = [
        [sg.Text("Enter epoch length in seconds:", tooltip=tooltip)],
        [sg.InputText(default_text=settings['default_epoch_length'],
                      key='-EPOCH_LENGTH-')],
        [sg.Button('Ok', bind_return_key=True)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                config['epoch_length'] = float(values["-EPOCH_LENGTH-"])
                break
            except:
                sg.popup_error('No valid number', location=(100, 100),font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_nr_ica_components(config,settings):
    tooltip = 'Enter number of ICA components'
    layout = [
        [sg.Text("Enter number of ICA components:",
                 tooltip=tooltip)],
        [sg.InputText(default_text=settings['default_ica_components'],
                      key='-ICA_COMPONENTS-')],
        [sg.Button('Ok', bind_return_key=True)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                config['nr_ica_components'] = int(values["-ICA_COMPONENTS-"])
                # set to min (ica_components, max components(config['max_channels'])) @@@
                break
            except:
                sg.popup_error('No valid integer value', location=(100, 100),font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def ask_downsample_factor(config,settings):
    tooltip = 'Enter a whole number to downsample by between 1 (no downsampling) and 100 (see https://mne.tools/stable/generated/mne.filter.resample.html)'
    layout = [
        [sg.Text("Enter downsample factor (1 equals no downsampling):", tooltip=tooltip)],
        [sg.InputText(default_text=settings['default_downsample_factor'],
                      key='-DOWNSAMPLE_FACTOR-')],
        [sg.Button('Ok', bind_return_key=True)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                config['downsample_factor'] = int(
                    values["-DOWNSAMPLE_FACTOR-"])
                break
            except:
                sg.popup_error('No valid integer value', location=(100, 100),font=font)
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
        [sg.Button('Ok', bind_return_key=True)]
    ]
    window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Ok':
            try:
                prefix = values["-LOGFILE_PREFIX-"]
                if not prefix:
                    sg.popup_error('No valid prefix', location=(
                        100, 100),font=font)  # empty string
                    window.close()
                config['logfile_prefix'] = prefix
                break
            except:
                # not sure if except is needed
                sg.popup_error('No value', location=(100, 100),font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    return config


def create_dict():  # create initial dict for manual processing
    try:
        config = {'apply_average_ref': 1,
                  'apply_epoch_selection': 0,
                  'epoch_length': 0.0,
                  'apply_ica': 0,
                  'apply_beamformer': 0,
                  'channels_to_be_dropped_selected': 0,
                  'nr_ica_components': 0,
                  'max_channels': 0,  # max channels for IA, determine per input file
                  'skip_input_file': 0,
                  'file_pattern': '-',
                  'input_file_pattern': "-",
                  'montage': '-',
                  'input_file_names': [],  # file name without path, selected by user or used in rerun run
                  'input_file_paths': [],  # full file paths
                  'pkl_file': [],  # used to save config to disk
                  'input_pkl_file': [],  # used for rerun function
                  'channel_names': [],  # file names only
                  'sample_frequency': 250,
                  'output_directory': 'C:\\AgileInzichtShare\\Engagements\\UMC\\Preprocessing EEG\\output',
                  'input_directory': ' ',
                  'logfile_prefix': 'herman'}


        return config
    except:
        sg.popup_error('Error create_dict:', location=(100, 100),font=font)
        window.close()
    return


# Functions for exporting data
def extract_epoch_data(raw_output, epoch_length, selected_indices, sfreq):
    events_out = mne.make_fixed_length_events(
        raw_output, duration=(epoch_length - (1 / sfreq)))
    epochs_out = mne.Epochs(raw_output, events=events_out, tmin=0, tmax=(epoch_length - (1 / sfreq)),
                            baseline=(0, epoch_length))
    selected_epochs_out = epochs_out[selected_indices]
    selected_epochs_out.drop_bad()
    return selected_epochs_out


def save_epoch_data_to_txt(config,epoch_data, file_suffix, scalings):
    for i in range(len(epoch_data)):
        epoch_df = epoch_data[i].to_data_frame(picks='eeg', scalings=scalings)
        epoch_df = epoch_df.drop(columns=['time', 'condition', 'epoch'])
        epoch_df = np.round(epoch_df, decimals=4)
        file_name = os.path.basename(
            root) + file_suffix + "Epoch" + str(i + 1) + ".txt"
        file_name_out = os.path.join(config['output_directory'], file_name)
        epoch_df.to_csv(file_name_out, sep='\t', index=False)

        msg = 'Output file ' + file_name_out + ' created'
        window['-FILE_INFO-'].update(msg+'\n', append=True)
        progress_bar2.UpdateBar(i+1)
        

def create_spatial_filter(config):
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
        mri=None,
        bem=bem,
    )

    label_names = mne.read_labels_from_annot(
        'fsaverage', parc='aparc', hemi='both', subjects_dir=subjects_dir)
    source_labels = [
        label.name for label in label_names if 'unknown' not in label.name.lower()]

    # Forward Solution
    fwd = mne.make_forward_solution(
        raw_beamform.info,
        trans=trans,
        src=src,
        bem=bem,
        eeg=True,
        mindist=0,
        n_jobs=None
    )

    # Inverse Problem
    # covariance matrix
    data_cov = mne.compute_raw_covariance(raw_beamform)

    # noise covariance matrix
    # Create a new matrix noise_matrix with the same size as data_cov
    noise_matrix = np.zeros_like(data_cov['data'])
    diagonal_values = np.diag(data_cov['data'])
    # Set the diagonal values of noise_matrix to the diagonal values of data_cov
    np.fill_diagonal(noise_matrix, diagonal_values)
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
                               noise_cov=noise_cov,
                               pick_ori='max-power',
                               weight_norm='unit-noise-gain',
                               rank=None,
                               )  # *2
    return spatial_filter

def create_raw(config):

    if config['file_pattern'] == "*.txt":
        with open(file_path, "r") as file:
            df = pd.read_csv(
                file, sep='\t', index_col=False, header=0)

        if config['channel_names'] == []:  # only do this once
            ch_names = list(df.columns)
            config['channel_names'] = ch_names
        ch_types = ["eeg"]*len(ch_names)
        info = mne.create_info(
            ch_names=ch_names, sfreq=config['sample_frequency'], ch_types=ch_types)
        df = df.iloc[:, 0:len(ch_names)]
        samples = df.T*1e-6  # Scaling from µV to V
        raw = mne.io.RawArray(samples, info)
        config['sample_frequency'] = raw.info["sfreq"]
        
        missing = df.columns[df.isna().any()].tolist()
        if missing != '[]':
            sg.popup_ok('Warning: channels with missing values found:',
                        missing, "please drop these channel(s)!", location=(100, 100),font=font)
            
    elif config['file_pattern'] == "*.bdf":
        raw = mne.io.read_raw_bdf(file_path, preload=True)
    elif config['file_pattern'] == "*.vhdr":
        raw = mne.io.read_raw_brainvision(file_path, preload=True)
    elif config['file_pattern'] == "*.edf":
        raw = mne.io.read_raw_edf(file_path, preload=True)

    if config['file_pattern'] != "*.vhdr": # Only .EEG files require explicit montage setting
        raw.set_montage(montage=montage, on_missing='ignore')
    return raw, config

def update_channels_to_be_dropped (raw,config):
    if config['rerun'] == 0 and config['channels_to_be_dropped_selected'] == 0:  # only in 1st batch if not yet selected
        channel_names = raw.ch_names
        channels_to_be_dropped = select_channels_to_be_dropped(
            channel_names)  # ask user to select
        config['channels_to_be_dropped_selected']=1 # *3 skip this
        config['channels_to_be_dropped'] = channels_to_be_dropped # store for rerun function
    raw.drop_channels(config['channels_to_be_dropped'])
    return raw,config

def perform_ica (raw,config):
    # ask # components (this is per file)
    msg = 'Max # components = ' + \
        str(config['max_channels'])
    window['-RUN_INFO-'].update(msg+'\n', append=True)

    # Preparation of clean raw object to calculate ICA on
    raw_ica = raw.copy()
    raw_ica.filter(l_freq=1, h_freq=45,l_trans_bandwidth=0.5, h_trans_bandwidth=4)

    raw_ica.info['bads'] = bad_channels  # *3 read from config
    raw_ica.interpolate_bads(reset_bads=True)

    # Fitting the ICA
    ica = ICA(n_components=config['nr_ica_components'],
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
    max_comp = config['nr_ica_components']
    components_to_be_dropped = select_components_to_be_dropped(
        max_comp)
    config[config['file_name'], 'dropped components'] =components_to_be_dropped
    msg = "Dropped components " + \
          str(components_to_be_dropped)                    # msg = "Dropped components " + components_to_be_dropped
    window['-RUN_INFO-'].update(msg+'\n', append=True)

    if len(components_to_be_dropped) > 0:
        ica.exclude = components_to_be_dropped

    # Apply ICA
    ica.apply(raw_interp)  # *1 skip if rerun
    return raw_ica,ica,config


# start loop
# window = make_win1()
# window = sg.Window('Test',layout=layout)
# window = sg.Window('Pattern 2B', layout,finalize=True)
window = sg.Window('UMC Utrecht MNE EEG Preprocessing', layout, location=(
    30, 30), size=(1000, 700), finalize=True, font=font)
# progress_bar = window.FindElement('progressbar')
# progress_bar2 = window.FindElement('progressbar2')
progress_bar = window.find_element('progressbar')
progress_bar2 = window.find_element('progressbar2')
# progress_bar = window.key('progressbar')
# progress_bar2 = window.key('progressbar2')

# removed while loop
while True:  # @noloop remove
    # window,  event, values = sg.read_all_windows()
    # https://trinket.io/pygame/36bf0df5f3, https://github.com/PySimpleGUI/PySimpleGUI/issues/2805
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    if event == "Rerun previous batch" :
        config = load_config_file() # .pkl file
        print (config)
        config['rerun']=1
        if not config['apply_epoch_selection']: # already done?
            config = ask_epoch_selection(config) # option to do epoch_selection
        config = ask_average_ref(config)
        config = ask_ica_option(config)
        config = ask_beamformer_option(config)
        config = ask_downsample_factor(config,settings)
        # logfile_prefix taken from saved_config
        # channels_to_be_dropped taken from saved_config  
        # config = select_input_file_paths(config) # generate from saved_config in loop - dir from pkl
        config = select_output_directory(config)
        # config = set_output_file_names(config) # composed in batch loop
        msg = 'You may now start processing'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        
    elif event == 'Enter parameters for this batch':
        config = create_dict()  # before file loop
        config['rerun']=0
        config = ask_average_ref(config)
        config = ask_epoch_selection(config)
        config = ask_ica_option(config)
        config = ask_beamformer_option(config)  # before file loop
        config = select_input_file_paths(config)
        config = select_output_directory(config)
        # list of patterns read from eeg_processing_config_XX
        config = ask_input_file_pattern(config, settings)
        # sample frequency of bdf, eeg and edf are available in raw
        if (config['input_file_pattern'].find('.txt') >= 0):
            config = ask_sample_frequency(
                config,settings)  # ask sample frequency
            sample_frequency = config['sample_frequency']  # check

        config = ask_downsample_factor(config,settings)
        config = ask_logfile_prefix(config)  # before file loop
        # set file names for config and log
        config = set_output_file_names(config)
        print (config)
        msg = 'You may now start processing'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        # print(config)

    elif event == 'Start processing':
        try:
            # Adjust the file extension as needed to recognize the correct file type
            montage=mne.channels.make_standard_montage(settings['montage',config['input_file_pattern']])
            config['file_pattern'] = settings['input_file_pattern',config['input_file_pattern']]

            # progess bar vars
            lfl = len(config['input_file_paths'])
            filenum = 0

            # Iterate through each file and open it
            for file_path in config['input_file_paths']:  # @noloop do not execute
                config['file_path']=file_path # to be used by functions, this is the current file_path
                # file_path="C:/AgileInzichtShare/Engagements/UMC/Yorben/Nieuwe functies/Bestanden Herman 22022024/Bestanden Herman 22022024/s041_512Hz_64ch_aver_ref.txt"
                # file name to be used in rerun
                # update config for rerun function
                f = Path(file_path)
                file_name = f.name
                config['file_name']=file_name
                input_dir=str(f.parents[0]) # to prevent error print config json
                config['input_directory']=input_dir # save, scope=batch
                # strip file_name for use as sub dir
                fn=file_name.replace(" ", "")
                fn=fn.replace(".", "")
                output_dir=posixpath.join(input_dir, fn ) # this is the sub-dir for output (epoch) files, remove spaces
                config['output_directory']=output_dir # save
                # create output sub directory if not existing
                if not os.path.exists(config['output_directory']):
                   os.makedirs(config['output_directory'])
                # add file name to list in config file, to be used in rerun
                config['input_file_names'].append(file_name) # add file name to config file, to be used in rerun
                msg = '\n************ Processing file ' + file_path + ' ************'
                window['-RUN_INFO-'].update(msg+'\n', append=True)
                window['-FILE_INFO-'].update(msg+'\n', append=True)
                
                # *** create_raw(file_path)                           ***
                raw,config=create_raw(config)   
                    
                # *** update_channels_to_be_dropped                   ***
                raw,config=update_channels_to_be_dropped (raw,config)
                
                # Temporary raw file to work with during preprocessing, raw is used to finally export epochs
                raw_temp = raw.copy()
                config['raw_temp'] = raw_temp

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
                raw_temp.filter(
                    l_freq=0.5, h_freq=45, l_trans_bandwidth=0.25, h_trans_bandwidth=4, picks='eeg')

                # Select bad channels interactively
                msg = "Select bad channels bij left-clicking channels"
                window['-RUN_INFO-'].update(msg+'\n', append=True)
                raw_temp.plot(n_channels=len(
                    raw.ch_names), block=True, title="Bandpass filtered data")
                ask_skip_input_file(config)

                # Retrieve the list of bad channels to use during export of the final file
                bad_channels = raw_temp.info['bads']  # *1
                config[file_name, 'bad'] = bad_channels  # store for rerun function

                # ask_skip_input_file(config)
                if config['skip_input_file'] == 1:
                    msg = 'File ' + file_path + ' skipped'
                    window['-FILE_INFO-'].update(msg+'\n', append=True)
                    filenum = filenum+1
                    progress_bar.UpdateBar(filenum, lfl)
                    continue
                
                # # *** perfom_ica                                      ***
                if config['apply_ica']:
                    raw_ica,ica,config=perform_ica(raw,config)
                

                # Interpolate or drop bad channels
                raw_interp = raw_temp.copy()
                raw_interp.interpolate_bads(
                    reset_bads=True)  # *3 712 t/m 754 skip

                # *3 812 t/m 869 skip if rerun
                # For beamforming, interpolated channels need to be dropped first
                if config['apply_beamformer']:
                    raw_beamform = raw_interp.copy()
                    raw_beamform.drop_channels(bad_channels)
                    msg = "channels left in raw_beamform: " + \
                        str(len(raw_beamform.ch_names))
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                # Downsample to 250 or 256 Hz to facilitate quick processing (if not beamforming)
                if not config['apply_beamformer']:
                    if config['sample_frequency'] % 256 == 0:
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
                    "Band 0.5-45 Hz filtered power spectrum. FIR transition bandwidths 0.25 and 4 Hz resp.")
                fig2.tight_layout(rect=[0, 0, 1, 0.95])
                fig2.canvas.draw()

                # Set average reference
                raw_interp.set_eeg_reference(
                    'average', projection=True, ch_type='eeg')
                raw_interp.apply_proj()  # Apply the average reference as a projector
                if config['apply_beamformer']:
                    raw_beamform.set_eeg_reference(
                        'average', projection=True, ch_type='eeg')
                    raw_beamform.apply_proj()
                

                if config['apply_epoch_selection']:
                    # Cut epochs
                    events = mne.make_fixed_length_events(raw_interp, duration=(
                        config['epoch_length']-(1/raw_resample_f)))  # Create epoch starting points
                    epochs = mne.Epochs(raw_interp, events=events, tmin=0, tmax=(
                        config['epoch_length']-(1/raw_resample_f)), baseline=(0, config['epoch_length']))

                    # Generate events at each second
                    # One event ID for each second
                    time_event_ids = np.arange(
                        config['epoch_length']*len(events))
                    time_event_samples = (
                        raw_resample_f * time_event_ids).astype(int)
                    time_events = np.column_stack(
                        (time_event_samples, np.zeros_like(time_event_samples), time_event_ids))

                    # Plot the epochs for visual inspection
                    msg = "Select bad epochs bij left-clicking data"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                    epochs.plot(n_epochs=1, n_channels=len(
                        raw.ch_names), events=time_events, block=True, picks=['eeg', 'eog', 'ecg'])

                    # Retrieve the indices of the selected epochs to use during export of the final files
                    selected_indices = epochs.selection  # *1
                    # *1 rewrite ??
                    config[file_name, 'epochs'] = selected_indices
                    # *3 812 t/m 869 skip if rerun

                if config['apply_beamformer']:  # naar apart func t/m 884 #*2
                    spatial_filter = create_spatial_filter(config)

                # Preparation of the final raw file and epochs for export

                # Apply the chosen bad channels to the output raw object(s)
                raw.info['bads'] = bad_channels  # extra write #*1
                config[file_name, 'bad'] = bad_channels  # *1 rewrite ??

                # Interpolate bad channels on the second Raw object
                raw.interpolate_bads(reset_bads=True)
                msg = "Interpolated " + \
                    str(len(bad_channels)) + \
                    " channels on (non-beamformed) output signal"
                window['-RUN_INFO-'].update(msg+'\n', append=True)

                if config['apply_ica'] or config['apply_beamformer']:
                    raw.filter(l_freq=0.5, h_freq=45, l_trans_bandwidth=0.25,
                               h_trans_bandwidth=4, picks='eeg')
                    msg = "Output signal filtered to 0.5-45 Hz (transition bands 0.25 Hz and 4 Hz resp. Necessary for ICA and/or Beamforming"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                if config['apply_ica']:
                    ica.apply(raw)
                    msg = "Ica applied to output signal"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                # Set EEG average reference (optional)
                if config['apply_average_ref']:
                    raw.set_eeg_reference(
                        'average', projection=True, ch_type='eeg')
                    raw.apply_proj()  # Apply the average reference as a projector
                    msg = "Average reference set on output signal"
                else:
                    msg = "No rereferencing applied"
                window['-RUN_INFO-'].update(msg+'\n', append=True)

                # Copy exported raw object before applying possible downsampling
                if config['apply_beamformer']:
                    raw_beamform_output = raw.copy()
                    raw_beamform_output.drop_channels(bad_channels)
                    msg = "Dropped " + \
                        str(len(bad_channels)) + \
                        " bad channels on beamformed output signal"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                    msg = "The EEG file used for beamforming now contains " + \
                        str(len(raw_beamform_output.ch_names)) + " channels"
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

                if config['apply_beamformer']:
                    # Load Desikan area labels for source channel names
                    desikanlabels = pd.read_csv(
                        'DesikanVoxLabels.csv', header=None)
                    desikan_channel_names = desikanlabels[0].tolist()

                    # Apply beamformer again to export raw object
                    stc = apply_lcmv_raw(raw_beamform_output, spatial_filter)
                    info = mne.create_info(
                        ch_names=desikan_channel_names, sfreq=config['sample_frequency'], ch_types='eeg')
                    rawSource = mne.io.RawArray(stc.data, info)
                    rawSource.resample(
                        downsampled_sample_frequency, npad="auto")
                    msg = "Beamformed output signal downsampled to " + \
                          str(downsampled_sample_frequency) + " Hz"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                # Create output epochs and export to .txt (non-beamformed)
                if config['apply_epoch_selection']:  # rename to epoch_output #*3
                    # *3 load selected_indces from  fig
                    selected_epochs_out = extract_epoch_data(
                        raw, config['epoch_length'], selected_indices, downsampled_sample_frequency)
                    # config[selected_indices] #*1

                    len2 = len(selected_epochs_out)
                    progress_bar2.UpdateBar(0, len2)
                    #(config,epoch_data, file_suffix, scalings)
                    save_epoch_data_to_txt(config, selected_epochs_out, "_Sensor_level_", None)

                    if config['apply_beamformer']:
                        # Export beamformed epochs
                        epoch_data_source = extract_epoch_data(
                            rawSource, config['epoch_length'], selected_indices, downsampled_sample_frequency)
                        save_epoch_data_to_txt(config, epoch_data_source, "_Source_level_", dict(
                            eeg=1, mag=1e15, grad=1e13))

                else:  # = no epoch_output
                    msg = "No epoch selection performed"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                    # Extract the data into a DataFrame
                    raw_df = raw.to_data_frame(picks='eeg')
                    raw_df = raw_df.iloc[:, 1:]  # Drop first (time) column
                    raw_df = np.round(raw_df, decimals=4)

                    # Define the file name
                    file_name_sensor = os.path.basename(
                        root) + "_Sensor_level.txt"

                    # Define the output file path
                    file_path_sensor = os.path.join(
                        config['output_directory'], file_name_sensor)

                    # Save the DataFrame to a text file
                    raw_df.to_csv(file_path_sensor, sep='\t', index=False)
                    progress_bar2.UpdateBar(1, 1) # epochs

                    if config['apply_beamformer']:
                        rawSource_df = rawSource.to_data_frame(
                            picks='eeg', scalings=dict(eeg=1, mag=1e15, grad=1e13))
                        # Drop first (time) column
                        rawSource_df = rawSource_df.iloc[:, 1:]
                        rawSource_df = np.round(rawSource_df, decimals=4)
                        file_name_source = os.path.basename(
                            root) + "_Source_level.txt"
                        file_path_source = os.path.join(
                            config['output_directory'], file_name_source)
                        rawSource_df.to_csv(
                            file_path_source, sep='\t', index=False)

                filenum = filenum+1
                progress_bar.UpdateBar(filenum, lfl) # files
                # end of for loop over files

        # except:
        except Exception as e:

            print(traceback.format_exc())
            print_dict(config)
            # write config to pkl file
            write_config_file(config)
            fn = config['logfile']
            with open(fn, "a", encoding='UTF-8') as f:
                f.write(traceback.format_exc())
                f.write(window['-FILE_INFO-'].get())
            with open(fn, "wt", encoding='UTF-8') as f:
                f.write(window['-RUN_INFO-'].get())
            sg.popup_error_with_traceback(
                'Error - info:', e)
            # window.close()
            # break

        # write config to pkl file
        print_dict(config)
        fn=write_config_file(config)
        msg = 'Config created for this batch (to be used for rerun) : '+fn
        window['-FILE_INFO-'].update(msg+'\n', append=True)
        # write log file
        fn = config['logfile']
        with open(fn, "wt", encoding='UTF-8') as f:
            f.write(window['-RUN_INFO-'].get())
        with open(fn, "a", encoding='UTF-8') as f:
            f.write(window['-FILE_INFO-'].get())
        msg = 'Log file created: ' + fn
        window['-FILE_INFO-'].update(msg+'\n', append=True)
        msg = 'Processing complete \n'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        

        # end of while loop @noloop unindent to this line

    # event, values = window.read()
    # @noloop remove this section

    # if event == 'Exit': # part of main while loop
    #     break

    # if event == sg.WIN_CLOSED: # part of main while loop
    #     break


window.close()
