import os
import numpy as np
import pandas as pd
import mne

def calc_filt_transition(cutoff_freq):
    if cutoff_freq is None:
        return None
    base_transition = min(max(cutoff_freq * 0.1, 0.4), 1.5)
    return float(min(base_transition, cutoff_freq))

def filter_data(raw, low_freq, high_freq, l_trans, h_trans):
    if low_freq is None and high_freq is None:
        return raw.get_data().flatten()
    raw_copy = raw.copy()
    raw_copy.filter(l_freq=low_freq, h_freq=high_freq, 
                    l_trans_bandwidth=l_trans, h_trans_bandwidth=h_trans,
                    fir_design='firwin', filter_length='auto', phase='zero')
    return raw_copy.get_data().flatten()

def process_eeg_files(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    eeg_files = [f for f in os.listdir(input_folder) if f.endswith('_raw_eeg.txt')]
    
    sfreq = 512

    # Define frequency bands
    bands = {
        'unfiltered': (None, None),
        'broadband': (0.5, 47),
        'delta': (0.5, 4),
        'widened_delta': (0.5, 6),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta1': (13, 20),
        'beta2': (20, 30)
    }

    rejection_stats = []

    for eeg_file in eeg_files:
        participant_id = eeg_file.split('_')[0]
        mask_file = f"{participant_id}_prepared_V2p0_mask.txt"

        # Load EEG and mask data
        eeg_data = np.loadtxt(os.path.join(input_folder, eeg_file))
        mask_data = np.loadtxt(os.path.join(input_folder, mask_file))

        # Create MNE RawArray object
        ch_names = ['EEG']
        ch_types = ['eeg']
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
        raw = mne.io.RawArray(eeg_data.reshape(1, -1), info)

        # Process each frequency band
        filtered_data = {}
        for band_name, (low_freq, high_freq) in bands.items():
            l_trans = calc_filt_transition(low_freq)
            h_trans = calc_filt_transition(high_freq)
            filtered_data[band_name] = filter_data(raw, low_freq, high_freq, l_trans, h_trans)

        # Apply mask to broadband data
        masked_data = filtered_data['broadband'] * mask_data

        # Cut epochs of 8 seconds
        epoch_samples = 8 * sfreq
        num_epochs = len(masked_data) // epoch_samples
        broadband_epochs = np.array_split(masked_data[:num_epochs * epoch_samples], num_epochs)

        # Perform epoch selection on broadband data
        total_epochs = len(broadband_epochs)
        epochs_after_mask = sum(1 for epoch in broadband_epochs if not np.any(epoch == 0))

        all_epochs_sd = np.std([epoch for epoch in broadband_epochs if not np.any(epoch == 0)])
        valid_epoch_indices = [i for i, epoch in enumerate(broadband_epochs) 
                               if not np.any(epoch == 0) and np.all(np.abs(epoch) <= 5 * all_epochs_sd)]
        epochs_after_sd = len(valid_epoch_indices)

        # Calculate rejection percentages
        percent_rejected_mask = (total_epochs - epochs_after_mask) / total_epochs * 100
        percent_rejected_sd = (epochs_after_mask - epochs_after_sd) / total_epochs * 100
        percent_rejected_total = (total_epochs - epochs_after_sd) / total_epochs * 100

        if epochs_after_sd >= 8:
            rejection_stats.append({
                'Participant ID': participant_id,
                'Total Epochs': total_epochs,
                'Epochs After Mask': epochs_after_mask,
                'Epochs After SD': epochs_after_sd,
                'Epochs Rejected (Mask) %': round(percent_rejected_mask, 2),
                'Epochs Rejected (SD) %': round(percent_rejected_sd, 2),
                'Total Epochs Rejected %': round(percent_rejected_total, 2)
            })

            for band_name in bands.keys():
                band_folder = os.path.join(output_folder, band_name, participant_id)
                os.makedirs(band_folder, exist_ok=True)

                band_epochs = np.array_split(filtered_data[band_name][:num_epochs * epoch_samples], num_epochs)

                # Apply the epoch selection from broadband to all frequency bands
                for epoch_count, i in enumerate(valid_epoch_indices, 1):
                    epoch_file = os.path.join(band_folder, f"epoch_{epoch_count}.txt")
                    np.savetxt(epoch_file, np.round(band_epochs[i], decimals=4), fmt='%.4f')

            print(f"Processed and saved {epochs_after_sd} epochs for participant {participant_id}")
        else:
            print(f"Discarded participant {participant_id} due to insufficient epochs")

    if rejection_stats:
        df_stats = pd.DataFrame(rejection_stats)
        stats_file = os.path.join(output_folder, 'epoch_rejection_statistics.xlsx')
        df_stats.to_excel(stats_file, index=False)
        print(f"Saved epoch rejection statistics to {stats_file}")
    else:
        print("No participants had sufficient epochs. No statistics file was created.")


# Usage (change input and output folders. Input folder should contain the
# .txt EEG and mask files for each participant)
input_folder = "/Volumes/STICK 250GB/Val3 data/Ruwe_EEGs_en_masks"
output_folder = "/Volumes/STICK 250GB/Val3 data/Val3_ouput_epochs_preprocessed_3"
process_eeg_files(input_folder, output_folder)