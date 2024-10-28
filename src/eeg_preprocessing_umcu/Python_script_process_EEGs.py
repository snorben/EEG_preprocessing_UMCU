import os
import numpy as np
import pandas as pd
import mne

def calc_filt_transition(cutoff_freq):
    base_transition = min(max(cutoff_freq * 0.1, 0.35), 2)
    return float(min(base_transition, cutoff_freq))

def process_eeg_files(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    eeg_files = [f for f in os.listdir(input_folder) if f.endswith('_raw_eeg.txt')]
    
    sfreq = 256  # Assuming a sampling rate of 256 Hz

    # Calculate custom transition bands
    l_freq, h_freq = 0.5, 47
    l_trans = calc_filt_transition(l_freq)
    h_trans = calc_filt_transition(h_freq)

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

        # Apply FIR filter with custom transition bands
        raw.filter(l_freq=l_freq, h_freq=h_freq, 
                   l_trans_bandwidth=l_trans, h_trans_bandwidth=h_trans,
                   fir_design='firwin', filter_length='auto', phase='zero')

        filtered_data = raw.get_data().flatten()
        masked_data = filtered_data * mask_data

        # Cut epochs of 8 seconds
        epoch_samples = 8 * sfreq
        num_epochs = len(masked_data) // epoch_samples
        epochs = np.array_split(masked_data[:num_epochs * epoch_samples], num_epochs)

        # Count epochs at each stage
        total_epochs = len(epochs)
        epochs_after_mask = sum(1 for epoch in epochs if not np.any(epoch == 0))

        all_epochs_sd = np.std([epoch for epoch in epochs if not np.any(epoch == 0)])
        epochs_after_sd = sum(1 for epoch in epochs 
                              if not np.any(epoch == 0) and np.all(np.abs(epoch) <= 4 * all_epochs_sd))

        # Calculate rejection percentages
        percent_rejected_mask = (total_epochs - epochs_after_mask) / total_epochs * 100
        percent_rejected_sd = (epochs_after_mask - epochs_after_sd) / total_epochs * 100
        percent_rejected_total = (total_epochs - epochs_after_sd) / total_epochs * 100

        rejection_stats.append({
            'Participant ID': participant_id,
            'Total Epochs': total_epochs,
            'Epochs After Mask': epochs_after_mask,
            'Epochs After SD': epochs_after_sd,
            'Epochs Rejected (Mask) %': round(percent_rejected_mask, 2),
            'Epochs Rejected (SD) %': round(percent_rejected_sd, 2),
            'Total Epochs Rejected %': round(percent_rejected_total, 2)
        })

        if epochs_after_sd >= 8:
            participant_folder = os.path.join(output_folder, participant_id)
            os.makedirs(participant_folder, exist_ok=True)

            epoch_count = 0
            for i, epoch in enumerate(epochs):
                if not np.any(epoch == 0) and np.all(np.abs(epoch) <= 5 * all_epochs_sd):
                    epoch_count += 1
                    epoch_file = os.path.join(participant_folder, f"epoch_{epoch_count}.txt")
                    np.savetxt(epoch_file, epoch, fmt='%.6f')

            print(f"Processed and saved {epochs_after_sd} epochs for participant {participant_id}")
        else:
            print(f"Discarded participant {participant_id} due to insufficient epochs")

    df_stats = pd.DataFrame(rejection_stats)
    stats_file = os.path.join(output_folder, 'epoch_rejection_statistics.xlsx')
    df_stats.to_excel(stats_file, index=False)
    print(f"Saved epoch rejection statistics to {stats_file}")

# Usage
input_folder = "/Volumes/STICK 250GB/Val3 data/test_eeg_masks"
output_folder = "/Volumes/STICK 250GB/Val3 data/Test1"
process_eeg_files(input_folder, output_folder)