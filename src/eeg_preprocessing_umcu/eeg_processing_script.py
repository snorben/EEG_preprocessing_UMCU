
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 08:50:06 2024

@authors: Herman van Dellen en Yorben Lodema
"""

import PySimpleGUI as sg
import os
import pandas as pd
import mne
import numpy as np
import pickle
import posixpath
from pathlib import Path
import traceback
import webbrowser as wb
from mne.preprocessing import ICA
from datetime import datetime
from eeg_processing_settings import *
from mne.beamformer import apply_lcmv_raw, make_lcmv
from mne.datasets import fetch_fsaverage

#settings={} # suppress warnings

# Set the working directory to the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
font=font # taken from settings
f_font=f_font  # font filter frequency inputs taken from settings
f_size=f_size # font size filter frequency inputs taken from settings
settings=settings # taken from settings
my_image=my_image # taken from settings

EEG_version = "v3.6a"

# initial values
progress_value1 = 20
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
        120, 10), key='progressbar_files', bar_color=['red', 'grey'])],
    [sg.ProgressBar(progress_value2, orientation='h', size=(
        120, 10), key='progressbar_epochs', bar_color=['#003DA6', 'grey'])],
    [sg.Button('Exit')],
    [sg.Column([[my_image]], justification='center')]]

def print_dict(dict): # pprint and json.print do not work well with composite keys!
    for key in dict.keys():
        print(key, ":", dict[key])  

def write_config_file(config):
    fn = config['config_file']
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


def select_input_file_paths(config, settings):
    if config['rerun']==0:
        # https://stackoverflow.com/questions/73764314/more-than-one-file-type-in-pysimplegui
        type_EEG = settings['input_file_paths','type_EEG']
        txt = settings['input_file_paths','text']
        # popup_get_file does not support tooltip
        f = sg.popup_get_file(txt,  title="File selector", multiple_files=True,font=font,
                              file_types=type_EEG,
                              background_color='white', location=(100, 100))
        file_list = f.split(";") 
        config['input_file_paths'] = file_list  
    
    return config


def load_config_file():    
    # file_types=(('.pkl files','*.pkl'),) => from rerun
    txt=settings['load_config_file','text']
    config_file=sg.popup_get_file(txt,file_types=(('.pkl files','*.pkl'),),no_window=False,background_color='white', 
                               font=font,location=(100, 100))
    if type(config_file) != type(""): 
        sg.popup_error ("No file selected","Ok")
        exit()
    config=load_config(config_file)
    config['previous_run_config_file']=config_file
    
    msg = '\nConfig ' + config_file + ' loaded for rerun\n'
    window['-FILE_INFO-'].update(msg+'\n', append=True)
    
    return config



def ask_update_frequency_bands(config):
    txt = "Do you want to modify filter frequencies?"  # @@@
    tooltip = """Do you want to modify filter frequencies?"""
    layout = [[sg.Text(txt, tooltip=tooltip, enable_events=True)],
              [sg.Button('Yes'), sg.Button('No')]]
    window = sg.Window("EEG processing input parameters", layout,  font=font,modal=True, use_custom_titlebar=True, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Yes':
            config['frequency_bands_modified'] = 1
            print_dict(config) # check
            config = update_frequency_bands(config)
            print_dict(config) # check
            break
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()
    
    return config

def update_frequency_bands(config):  
    tooltip=""
    layout = [
        [sg.Text(
            "Filter cut-off frequencies", tooltip=tooltip,font=font)],
        [sg.Text('delta_low     '), sg.Input(default_text= config['filter_frequencies','delta_low'], key='-FILTER_DL-',size=f_size),
         sg.Text('delta_high    '), sg.Input(default_text= config['filter_frequencies','delta_high'], key='-FILTER_DH-',size=f_size)],
        [sg.Text('theta_low     '), sg.Input(default_text= config['filter_frequencies','theta_low'], key='-FILTER_TL-',size=f_size),
         sg.Text('theta_high    '), sg.Input(default_text= config['filter_frequencies','theta_high'], key='-FILTER_TH-',size=f_size)],
        [sg.Text('alpha_low     '), sg.Input(default_text= config['filter_frequencies','alpha_low'], key='-FILTER_AL-',size=f_size),
         sg.Text('alpha_high    '), sg.Input(default_text= config['filter_frequencies','alpha_high'], key='-FILTER_AH-',size=f_size)],
        [sg.Text('beta_low      '), sg.Input(default_text= config['filter_frequencies','beta_low'], key='-FILTER_BL-',size=f_size),
         sg.Text('beta_high     '), sg.Input(default_text= config['filter_frequencies','beta_high'], key='-FILTER_BH-',size=f_size)],
        [sg.Text('broadband_low '), sg.Input(default_text= config['filter_frequencies','broadband_low'], key='-FILTER_BRL-',size=f_size),
         sg.Text('broadband_high'), sg.Input(default_text= config['filter_frequencies','broadband_high'], key='-FILTER_BRH-',size=f_size)],
        [sg.Button('Select',font=font)]
    ]
    window = sg.Window("Filter", layout, modal=True, use_custom_titlebar=True, font=f_font, 
                       background_color='white', location=(100, 100))
    while True:
        event, values = window.read()
        if event == 'Select':
            try:
                config['filter_frequencies',"delta_low"] = values["-FILTER_DL-"]
                config['filter_frequencies',"delta_high"] = values["-FILTER_DH-"]
                config['filter_frequencies',"theta_low"]= values['-FILTER_TL-']
                config['filter_frequencies',"theta_high"]= values['-FILTER_TH-']
                config['filter_frequencies',"alpha_low"]= values['-FILTER_AL-']
                config['filter_frequencies',"alpha_high"]= values['-FILTER_AH-']
                config['filter_frequencies',"beta_low"]= values['-FILTER_BL-']
                config['filter_frequencies',"beta_high"]= values['-FILTER_BH-']
                config['filter_frequencies',"broadband_low"]= values['-FILTER_BRL-']
                config['filter_frequencies',"broadband_high"]= values['-FILTER_BRH-']
                print_dict(config) # check
                break
            except:
                sg.popup_error('No valid frequencies', location=(100, 100),font=font)
                window.close()
        if event in (sg.WIN_CLOSED, 'Ok'):
            break
    window.close()

    return config




def select_output_directory(config):
    if not config['rerun']:
        tooltip = 'Output folder for exported epoch- and log files'
        working_directory = os.getcwd()
        layout = [
            [sg.Text(
                "Select base output directory to save epoch- and log files to\n(Subdirectories will be created for log, epochs etc.)", tooltip=tooltip)],
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
    txt = "Do you want to apply Beamforming?"
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
    if config['rerun']==0 or (config['rerun']==1 and config['apply_epoch_selection']==0): 
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
    # note: input_file_patterns read from eeg_processing_settings file
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
    tooltip = "Select one or more channels to be dropped, or only press OK to drop none"
    items = in_list
    txt = "Select channels to be dropped (if any)\nNote: for ICA make sure to drop empty or non-EEG channels"

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
    items = list(range(0, max_comp))
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


def set_batch_related_names(config):
    '''
    Function that performs the actions necessary to define all file/folder/path names
    associated with the current EEG batch that is being processed. These names are fixed for the 
    entire batch.
    '''
    # batch_prefix batch_name batch_output_subdirectory config_file logfile
    today = datetime.today()
    dt = today.strftime('%Y%m%d_%H%M%S')  # suffix

    if config['rerun']==0:
        tooltip = 'Enter a prefix (e.g. study name) for this batch. The log file will be named <prefix><timestamp>.log'
        txt="Enter a prefix for this batch (e.g. BIOCOG_batch1)\n(This prefix will be used to create the subdirectory for this batch)\n(Prefix should not contain spaces):"
        layout = [
            [sg.Text(text=txt, tooltip=tooltip)],
            [sg.InputText(key='-BATCH_PREFIX-')],
            [sg.Button('Ok', bind_return_key=True)]
        ]
        window = sg.Window("EEG processing input parameters", layout, modal=True, use_custom_titlebar=True, font=font, 
                           background_color='white', location=(100, 100))
        while True:
            event, values = window.read()
            if event == 'Ok':
                try:
                    prefix = values["-BATCH_PREFIX-"]
                    if not prefix:
                        sg.popup_error('No valid prefix', location=(
                            100, 100),font=font)  # empty string
                        window.close()
                    prefix = prefix.replace(" ", "_")
                    config['batch_prefix'] = prefix # replace spaces
                    break
                except:
                    # not sure if except is needed
                    sg.popup_error('No value', location=(100, 100),font=font)
                    window.close()
            if event in (sg.WIN_CLOSED, 'Ok'):
                break
        window.close()
        
    # else use config['batch_prefix'] from previous run  
    config['batch_name'] = config['batch_prefix'] + '_' + dt
    config['batch_output_subdirectory'] = os.path.join(config['output_directory'], config['batch_name'])    
    # create if not existing
    if not os.path.exists(config['batch_output_subdirectory']):
       os.makedirs(config['batch_output_subdirectory']) 
    
    fn = config['batch_name'] + '.log'
    config['logfile'] = os.path.join(config['batch_output_subdirectory'], fn)
    fn = config['batch_name'] + '.pkl'
    config['config_file'] = os.path.join(config['batch_output_subdirectory'], fn)
    # print('set_batch_related_names config_file ', config['config_file'])
        
    return config


def set_file_output_related_names(config):    
    # Scope: in file loop
    '''
    Function that performs the actions necessary to define all file/folder/path names
    associated with the current EEG FILE that is being processed. These names change
    for each file in the batch.
    '''
    # strip file_name for use as sub dir
    fn = config['file_name'].replace(" ", "")
    fn = fn.replace(".", "")
    # Split the file path and extension to use when constructing the output file names
    root, ext = os.path.splitext(config['file_path'])
    config['file_output_subdirectory'] = posixpath.join(config['batch_output_subdirectory'], fn ) # this is the sub-dir for output (epoch) files, remove spaces
    if not os.path.exists(config['file_output_subdirectory']):
       os.makedirs(config['file_output_subdirectory'])  
    
    file_name_sensor = os.path.basename(root) + "_Sensor_level"
    config['file_path_sensor'] = os.path.join(config['file_output_subdirectory'], file_name_sensor)
    
    file_name_source = os.path.basename(root) + "_Source_level"
    config['file_path_source'] = os.path.join(config['file_output_subdirectory'], file_name_source)
       
    return config


def create_dict():  
    '''
    Function to create initial dict with starting values for processing.
    '''
    try:
        # # print('create_dict')
        # config = {'apply_average_ref': 1,
        #           'apply_epoch_selection': 0,
        #           'epoch_length': 0.0,
        #           'apply_ica': 0,
        #           'rerun': 0,
        #           'apply_beamformer': 0,
        #           'channels_to_be_dropped_selected': 0,
        #           'nr_ica_components': 0,
        #           'max_channels': 0,  # max channels for IA, determine per input file
        #           'skip_input_file': 0,
        #           'file_pattern': '-',
        #           'input_file_pattern': "-",
        #           'montage': '-',
        #           'input_file_names': [],  # file name without path, selected by user or used in rerun run
        #           'input_file_paths': [],  # full file paths
        #           'channel_names': [],  # file names only
        #           'sample_frequency': 250,                  
        #           'config_file': ' ',  # used to save config to disk
        #           'log_file': ' ',  # used to save config to disk
        #           'previous_run_config_file ': ' ',  # used for rerun function
        #           'output_directory': ' ',
        #           'batch_output_subdirectory': ' ',
        #           'file_output_subdirectory': ' ',
        #           'input_directory': ' ', # set in file loop
        #           'batch_name': ' ',
        #           'frequency_bands_modified' : 0,
        #           'batch_prefix': ' '}
        config=settings # read defaults from settings file


        return config
    except:
        sg.popup_error('Error create_dict:', location=(100, 100),font=font)
        window.close()

        
def save_epoch_data_to_txt(epoch_data, base, scalings):
    '''
    Function to save an MNE epoch object to txt files. 
    '''
    for i in range(len(epoch_data)):
        epoch_df = epoch_data[i].to_data_frame(picks='eeg', scalings=scalings)
        epoch_df = epoch_df.drop(columns=['time', 'condition', 'epoch'])
        epoch_df = np.round(epoch_df, decimals=4)
        
        file_name_out = base + "_Epoch" + str(i + 1) + ".txt"
        epoch_df.to_csv(file_name_out, sep='\t', index=False)

        msg = 'Output file ' + file_name_out + ' created'
        window['-FILE_INFO-'].update(msg+'\n', append=True)
        progress_bar_epochs.UpdateBar(i+1)
        

def create_spatial_filter(raw_b,config):
    '''
    Function used to create a spatial filter for the LCMV beamforming method. The MNE function make_lcmv is used.
    '''
    fs_dir = fetch_fsaverage(verbose=True)
    subjects_dir = os.path.dirname(fs_dir)
    subject = "fsaverage"
    trans = "fsaverage"

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
        raw_b.info,
        trans=trans,
        src=src,
        bem=bem,
        eeg=True,
        mindist=0,
        n_jobs=None
    )

    # Inverse Problem
    data_cov = mne.compute_raw_covariance(raw_b)

    # Create a new matrix noise_matrix (noise cov. matrix) with the same size as data_cov
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
    spatial_filter = make_lcmv(raw_b.info,
                               fwd,
                               data_cov,
                               reg=0.05,
                               noise_cov=noise_cov,
                               pick_ori='max-power',
                               weight_norm='unit-noise-gain',
                               rank=None,
                               )  # *2
    return spatial_filter

  
def create_raw(config,montage):
    '''
    Function used to load a raw EEG file using the correct MNE function based on the file type that has to be
    loaded (.txt, .bdf, .eeg or .edf). Note: for .eeg files the header (.vhdr) is primarily loaded by MNE. For
    non-.eeg files, the electrode montage is also set, supplying spatial coordinates needed for interpolation
    and beamforming of the EEG. For .eeg files, this information is already read from the header file.
    '''
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
        #config['sample_frequency'] = raw.info["sfreq"] # Niet nodig toch?
        
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
    elif config['file_pattern'] == "*.fif":
        raw = mne.io.read_raw_fif(file_path, preload=True, )
        raw.pick_types(eeg=True, meg=False, eog=False)

    if config['file_pattern'] != "*.vhdr" and config['file_pattern'] != "*.fif": # Only .EEG raws already automatically have a montage
        raw.set_montage(montage = montage, on_missing ='ignore')
        
    if config['file_pattern'] != "*.txt":
        config['sample_frequency'] = raw.info["sfreq"]
    
    return raw, config


def update_channels_to_be_dropped (raw,config):
    channel_names = raw.ch_names
    channels_to_be_dropped = select_channels_to_be_dropped(channel_names)  # ask user to select
    config['channels_to_be_dropped'] = channels_to_be_dropped # store for rerun function
    return raw,config


def perform_ica (raw,raw_temp,config):
    # ask # components (this is per file)
    msg = 'Max # components = ' + \
        str(config['max_channels'])
    window['-RUN_INFO-'].update(msg+'\n', append=True)

    # Preparation of clean raw object to calculate ICA on
    raw_ica = raw.copy()
    raw_ica.filter(l_freq=1, h_freq=45,l_trans_bandwidth=0.5, h_trans_bandwidth=4)

    raw_ica.info['bads'] = config[file_name, 'bad']  # *3 read from config
    raw_ica.interpolate_bads(reset_bads=True)

    # Fitting the ICA
    ica = ICA(n_components=config['nr_ica_components'],
              method='fastica')
    ica.fit(raw_ica,  picks='eeg')
    ica

    ica.plot_components()  # head plot heat map
    ica.plot_sources(raw_ica, block=True)

    # https://mne.discourse.group/t/variance-of-ica-components/5544/2
    # unitize variances explained by PCA components, so the values sum to 1
    pca_explained_variances = ica.pca_explained_variance_ / \
        ica.pca_explained_variance_.sum()
    ica_explained_variances = pca_explained_variances[:ica.n_components_]
    cumul_pct = 0.0

    for idx, var in enumerate(ica_explained_variances):
        pct = round(100 * var, 2)
        cumul_pct += pct
        msg = 'Explained variance for ICA component ' + \
            str(idx) + ': ' + str(pct) + '%' + \
            ' ('+str(round(cumul_pct, 1)) + ' %)'
        window['-RUN_INFO-'].update(msg+'\n', append=True)

    ica.apply(raw_temp)
    
    return raw_temp,ica,config


def perform_bad_channels_selection(raw,config):
    '''
    Function that applies MNE plotting to interactively select bad channels and save these to the config. 
    These channels can later be interpolated or dropped depending on the needs.
    '''
    msg = "Select bad channels by left-clicking channels"
    window['-RUN_INFO-'].update(msg+'\n', append=True)
    raw.plot(n_channels=len(
        raw.ch_names), block=True, title="Bandpass filtered data")

    config[file_name, 'bad'] = raw.info['bads']  # *1 ### Aparte bad_channels variable is nu weg
    
    return raw,config


def plot_power_spectrum(raw, filtered=False):
    '''
    Function that plots the power spectrum of the separate EEG channels
    of either the unfiltered or filtered EEG (from 0-60 Hz).
    '''
    fig = raw.compute_psd(fmax=60).plot(
        picks='eeg', exclude=[])
    axes = fig.get_axes()
    if filtered:
        axes[0].set_title("Band 0.5-45 Hz filtered power spectrum.")
    else:
        axes[0].set_title("Unfiltered power spectrum")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.canvas.draw()   
    
    
def perform_temp_down_sampling(raw,config):
    '''
    Function that down samples the temporary raw EEG to 250 or 256 Hz depending on the sample frequency
    (power of 2 or not). This should speed up preprocessing.
    '''
    temporary_sample_f = 256 if config['sample_frequency'] % 256 == 0 else 250
    print("temp. sample fr: ", temporary_sample_f)
    raw.resample(temporary_sample_f, npad="auto")
    
    return raw, temporary_sample_f

    
def perform_average_reference(raw):
    '''
    Function that applies a global average reference on the 'eeg' type channels of the raw EEG.
    '''
    raw.set_eeg_reference('average', projection=True, ch_type='eeg')
    
    raw.apply_proj()
    return raw

def perform_beamform(raw,config):
    '''
    Function that drops bad channels and creates the spatial filter used for LCMV beamforming.
    '''
    raw.drop_channels(config[file_name, 'bad'])
    msg = "channels left in raw_beamform: " + str(len(raw.ch_names))
    window['-RUN_INFO-'].update(msg+'\n', append=True)
    raw = perform_average_reference(raw)
    spatial_filter = create_spatial_filter(raw,config)
    return spatial_filter

def perform_epoch_selection(raw,config):
    '''
    Function that performs epoch selection on the raw file. This function is for use on the temporary raw object.
    '''
    events = mne.make_fixed_length_events(raw, duration=(config['epoch_length']))
    epochs = mne.Epochs(raw, events=events, tmin=0, tmax=(
        config['epoch_length']-(1/temporary_sample_f)), baseline=(0, config['epoch_length']-(1/temporary_sample_f)), preload=True)

    # Generate events at each second as seconds markers for the epochs plot
    time_event_ids = np.arange(config['epoch_length']*len(events))
    time_event_samples = (temporary_sample_f * time_event_ids).astype(int)
    time_events = np.column_stack(
        (time_event_samples, np.zeros_like(time_event_samples), time_event_ids))

    # Plot the epochs for visual inspection
    msg = "Select bad epochs by left-clicking data"
    window['-RUN_INFO-'].update(msg+'\n', append=True)
    epochs.plot(n_epochs=1, n_channels=len(
        raw.ch_names), events=time_events, event_color= 'm',block=True, picks=['eeg', 'eog', 'ecg'])

    config[file_name, 'epochs'] = epochs.selection  # *1
    return config
    
 
def apply_epoch_selection(raw_output,config,sfreq):
    '''
    Function that applies the epoch selection made earlier (either in a previous run
    or during current pre processing) to the raw EEG used for saving output to file.
    '''
    events_out = mne.make_fixed_length_events(raw_output, duration=config['epoch_length'])
    epochs_out = mne.Epochs(raw_output, events=events_out, tmin=0, tmax=(config['epoch_length'] - \
        (1 / sfreq)), baseline=(0, config['epoch_length']))
    selected_epochs_out = epochs_out[config[file_name, 'epochs']]
    selected_epochs_out.drop_bad()
    return selected_epochs_out

def apply_bad_channels(raw,config):
    '''
    Function that applies bad channels (either from previous run or current pre processing)
    to raw EEG object used to export the final output.
    '''
    raw.info['bads'] = config[file_name, 'bad']
    raw.interpolate_bads(reset_bads=True)
    msg = "Interpolated " + str(len(config[file_name, 'bad'])) + \
        " channels on (non-beamformed) output signal"
    window['-RUN_INFO-'].update(msg+'\n', append=True)
    return raw
    
def apply_spatial_filter(raw, config, spatial_filter):
    '''
    Function that applies the spatial filter created earlier to the final 
    raw EEG object used to export the final output.
    '''
    desikanlabels = pd.read_csv('DesikanVoxLabels.csv', header=None)
    desikan_channel_names = desikanlabels[0].tolist()
    stc = apply_lcmv_raw(raw, spatial_filter)
    info = mne.create_info(
        ch_names = desikan_channel_names, sfreq = config['sample_frequency'], ch_types='eeg')
    raw_source = mne.io.RawArray(stc.data, info)
    raw_source.resample(config['sample_frequency']//config['downsample_factor'], npad="auto")
    msg = "Beamformed output signal downsampled to " + \
          str(config['sample_frequency']//config['downsample_factor']) + " Hz"
    window['-RUN_INFO-'].update(msg+'\n', append=True)
    return raw_source

##################################################################################

window = sg.Window('UMC Utrecht MNE EEG Preprocessing', layout, location=(
    30, 30), size=(1000, 700), finalize=True, font=font)

progress_bar_files = window.find_element('progressbar_files')
progress_bar_epochs = window.find_element('progressbar_epochs')

# config['rerun_new_epoch_selection'] = False # config nog niet

while True:  # @noloop remove
    # https://trinket.io/pygame/36bf0df5f3, https://github.com/PySimpleGUI/PySimpleGUI/issues/2805
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # note: dependencies on config['rerun'] are always handled in the ask_ or select_ functions
    if event == "Rerun previous batch" :
        config = load_config_file() # .pkl file
        config['rerun']=1
        config = ask_update_frequency_bands(config)
        config = select_input_file_paths(config, settings) # read from pkl
        config = set_batch_related_names(config) # batch_prefix batch_name batch_output_subdirectory config_file logfile
        config = select_output_directory(config)
        config = ask_epoch_selection(config) # function will check if epoch_selection has already been made, if not then it will ask
        config = ask_average_ref(config)
        config = ask_ica_option(config)
        config = ask_beamformer_option(config)
        config = ask_downsample_factor(config,settings)
        msg = 'Loaded config:'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        print_dict(config)
        msg = 'You may now start processing'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        
    elif event == 'Enter parameters for this batch':
        print('Enter parameters for this batch')
        config = create_dict()  # before file loop
        config['rerun'] = 0
        config = ask_update_frequency_bands(config)
        config = select_input_file_paths(config, settings) # gui file explorer
        config = select_output_directory(config) # gui file explorer
        config = set_batch_related_names(config) # batch_prefix batch_name batch_output_subdirectory config_file logfile
        config = ask_average_ref(config)
        config = ask_epoch_selection(config)
        config = ask_ica_option(config)
        config = ask_beamformer_option(config)  # before file loop
        # list of patterns read from eeg_processing_config_XX
        config = ask_input_file_pattern(config, settings)
        
        # sample frequency of bdf, eeg and edf are available in raw
        if (config['input_file_pattern'].find('.txt') >= 0):
            config = ask_sample_frequency(
                config,settings)  # ask sample frequency
            sample_frequency = config['sample_frequency']  # check

        config = ask_downsample_factor(config,settings)

        
        msg = 'Created config:'
        window['-RUN_INFO-'].update(msg+'\n', append=True)
        print_dict(config)
        msg = 'You may now start processing'
        window['-RUN_INFO-'].update(msg+'\n', append=True)


    elif event == 'Start processing':
        try:
            # reset progress bars
            progress_bar_files.UpdateBar(0,0)
            progress_bar_epochs.UpdateBar(0,0)
            no_montage_patterns = ["*.vhdr", "*.fif"]
            config['file_pattern'] = settings['input_file_pattern', config['input_file_pattern']]
            
            if config['file_pattern'] not in no_montage_patterns:
                montage = mne.channels.make_standard_montage(settings['montage', config['input_file_pattern']])
            else:
                montage = "NA"
                        
            # Adjust the file extension as needed to recognize the correct file type
            if config['file_pattern'] != "*.vhdr" and config['file_pattern'] != "*.fif":
                montage = mne.channels.make_standard_montage(settings['montage',config['input_file_pattern']])
            else:
                montage = "NA"

            # progess bar vars
            lfl = len(config['input_file_paths'])
            filenum = 0

            for file_path in config['input_file_paths']:  # @noloop do not execute
                config['file_path'] = file_path # to be used by functions, this is the current file_path
                f = Path(file_path)
                file_name = f.name
                input_dir = str(f.parents[0]) # to prevent error print config json
                config['input_directory'] = input_dir # save, scope=batch
                config['file_name'] = file_name
                config=set_file_output_related_names(config) # set output directory for epochs etc. 
                # add file name to list in config file, to be used in rerun                
                config['input_file_names'].append(file_name) # add file name to config file, to be used in rerun
                msg = '\n*** Processing file ' + file_path + ' ***'
                window['-RUN_INFO-'].update(msg+'\n', append=True)
                window['-FILE_INFO-'].update(msg+'\n', append=True)
                
                # create_raw(file_path
                raw,config = create_raw(config,montage)   
                    
                # update_channels_to_be_dropped
                if config['rerun'] == 0 and config['channels_to_be_dropped_selected'] == 0:
                    raw,config = update_channels_to_be_dropped (raw,config)
                    config['channels_to_be_dropped_selected'] = 1
                raw.drop_channels(config['channels_to_be_dropped'])
                
                # Temporary raw file to work with during preprocessing, raw is used to finally export data
                raw_temp = raw.copy()

                plot_power_spectrum(raw_temp, filtered=False)

                raw_temp.filter(l_freq=0.5, h_freq=45, l_trans_bandwidth=0.25, \
                                h_trans_bandwidth=4, picks='eeg')
                
                # To ensure bad channels are reloaded during a rerun:
                if config['rerun'] == 1:
                    raw_temp.info['bads'] = config[file_name, 'bad']
                    
                raw_temp,config = perform_bad_channels_selection(raw_temp, config)
                raw_temp.interpolate_bads(reset_bads=True)
                
                # ask_skip_input_file(config) to allow user to skip current EEG file
                config = ask_skip_input_file(config)
                if config['skip_input_file'] == 1:
                    msg = 'File ' + file_path + ' skipped'
                    window['-FILE_INFO-'].update(msg+'\n', append=True)
                    filenum += 1
                    progress_bar_files.UpdateBar(filenum, lfl)
                    continue
                
                # determine max nr_channels (= upper limit of nr of ICA components) @@@
                config['max_channels'] = int(len(raw.ch_names)- 1 -len(config[file_name, 'bad'])) # @@@ check
                print("max ICA channels: ", config['max_channels'])

                if config['apply_ica']:
                    raw_temp,ica,config = perform_ica(raw, raw_temp, config)
                
                if config['apply_beamformer']:
                    spatial_filter = perform_beamform(raw_temp,config)
                
                
                raw_temp,temporary_sample_f = perform_temp_down_sampling(raw_temp,config)
                
                plot_power_spectrum(raw_temp, filtered=True)

                raw_temp = perform_average_reference(raw_temp)

                if config['apply_epoch_selection']:
                    config = perform_epoch_selection(raw_temp,config)
                
                # if config['apply_epoch_selection'] and config['rerun'] == 0:
                #     config = perform_epoch_selection(raw_temp,config)
                
                # if rerun_new_epoch_selection:
                #     config = perform_epoch_selection(raw_temp,config)



                # ********** Preparation of the final raw file and epochs for export **********                
                raw = apply_bad_channels(raw,config)

                if config['apply_ica'] or config['apply_beamformer']:
                    raw.filter(l_freq=0.5, h_freq=45, l_trans_bandwidth=0.25,
                               h_trans_bandwidth=4, picks='eeg')
                    msg = "Output signal filtered to 0.5-45 Hz (transition bands 0.25 Hz and 4 Hz resp. \
                        Necessary for ICA and/or Beamforming"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                if config['apply_ica']:
                    ica.apply(raw)
                    msg = "Ica applied to output signal"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                if config['apply_average_ref']:
                    raw = perform_average_reference(raw)
                    msg = "Average reference set on output signal"
                else:
                    msg = "No rereferencing applied"
                window['-RUN_INFO-'].update(msg+'\n', append=True)

                if config['apply_beamformer']:
                    raw_beamform_output = raw.copy()
                    raw_beamform_output.drop_channels(config[file_name, 'bad'])
                    msg = "Dropped " + str(len(config[file_name, 'bad'])) + \
                        " bad channels on beamformed output signal"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                    msg = "The EEG file used for beamforming now contains " + \
                        str(len(raw_beamform_output.ch_names)) + " channels"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)
                    
                    raw_source = apply_spatial_filter(raw_beamform_output, config, spatial_filter)

                downsampled_sample_frequency = config['sample_frequency']//config['downsample_factor']
                if config['downsample_factor'] != 1:
                    raw.resample(downsampled_sample_frequency, npad="auto")
                    msg = "Non-beamformed output signal downsampled to " + \
                        str(downsampled_sample_frequency) + " Hz"
                else:
                    msg = "No downsampling applied to output signal"
                window['-RUN_INFO-'].update(msg+'\n', append=True)

                root, ext = os.path.splitext(file_path) ### Nog nodig?

                # Create output epochs and export to .txt
                if config['apply_epoch_selection']:  # rename to epoch_output #*3
                    selected_epochs_sensor = apply_epoch_selection(raw, config, downsampled_sample_frequency)
                    # config[selected_indices] #*1

                    len2 = len(selected_epochs_sensor)
                    progress_bar_epochs.UpdateBar(0, len2)

                    save_epoch_data_to_txt(selected_epochs_sensor, config['file_path_sensor'], None)

                    if config['apply_beamformer']:
                        # Export beamformed epochs
                        selected_epochs_source = apply_epoch_selection(raw_source, config, downsampled_sample_frequency)
                        save_epoch_data_to_txt(selected_epochs_source, config['file_path_source'], dict(
                            eeg=1, mag=1e15, grad=1e13))

                else:  # equals no epoch_output
                    msg = "No epoch selection performed"
                    window['-RUN_INFO-'].update(msg+'\n', append=True)

                    raw_df = raw.to_data_frame(picks='eeg')
                    raw_df = raw_df.iloc[:, 1:]  # Drop first (time) column
                    raw_df = np.round(raw_df, decimals=4)

                    file_name_sensor = os.path.basename(
                        root) + "_Sensor_level.txt"


                    # Define the output file path
                    # @@@outputfile aanpassen
                    # file_path_sensor = os.path.join(
                    #     config['output_directory'], file_name_sensor)
                    # file_path_sensor = os.path.join(
                    #     config['file_output_subdirectory'], file_name_sensor)
                    # print ('main 1098  file_name_sensor: ',file_name_sensor)
                    # print ('main 1098  file_path_sensor: ',file_name_sensor)

                    # Save the DataFrame to a text file
                    raw_df.to_csv(config['file_path_sensor'], sep='\t', index=False)
                    progress_bar_epochs.UpdateBar(1, 1) # epochs

                    if config['apply_beamformer']:
                        # @@@ output file aanpassen
                        raw_source_df = raw_source.to_data_frame(
                            picks='eeg', scalings=dict(eeg=1, mag=1e15, grad=1e13))
                        raw_source_df = raw_source_df.iloc[:, 1:]
                        raw_source_df = np.round(raw_source_df, decimals=4)
                        file_name_source = os.path.basename(
                            root) + "_Source_level.txt"

                        # print ('main 1115 apply_beamformer  file_name_source: ',file_name_source)
                        # print ('main 1115 apply_beamformer  file_path_source: ',file_path_source)
                        raw_source_df.to_csv(config['file_path_source'], sep='\t', index=False)

                filenum = filenum+1
                progress_bar_files.UpdateBar(filenum, lfl) # files
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
        

window.close()
