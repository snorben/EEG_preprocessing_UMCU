## Badges

(Customize these badges with your own links, and check https://shields.io/ or https://badgen.net/ to see which other badges are available.)

| fair-software.eu recommendations | |
| :-- | :--  |
| (1/5) code repository              | [![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](https://github.com/snorben/eeg_preprocessing_umcu) |
| (2/5) license                      | [![github license badge](https://img.shields.io/github/license/snorben/eeg_preprocessing_umcu)](https://github.com/snorben/eeg_preprocessing_umcu) |
| (3/5) community registry           | [![RSD](https://img.shields.io/badge/rsd-eeg_preprocessing_umcu-00a3e3.svg)](https://www.research-software.nl/software/eeg_preprocessing_umcu) [![workflow pypi badge](https://img.shields.io/pypi/v/eeg_preprocessing_umcu.svg?colorB=blue)](https://pypi.python.org/project/eeg_preprocessing_umcu/) |
| (4/5) citation                     | [![DOI](https://zenodo.org/badge/DOI/<replace-with-created-DOI>.svg)](https://doi.org/<replace-with-created-DOI>) |
| (5/5) checklist                    | [![workflow cii badge](https://bestpractices.coreinfrastructure.org/projects/<replace-with-created-project-identifier>/badge)](https://bestpractices.coreinfrastructure.org/projects/<replace-with-created-project-identifier>) |
| howfairis                          | [![fair-software badge](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu) |
| **Other best practices**           | &nbsp; |
| Static analysis                    | [![workflow scq badge](https://sonarcloud.io/api/project_badges/measure?project=snorben_eeg_preprocessing_umcu&metric=alert_status)](https://sonarcloud.io/dashboard?id=snorben_eeg_preprocessing_umcu) |
| Coverage                           | [![workflow scc badge](https://sonarcloud.io/api/project_badges/measure?project=snorben_eeg_preprocessing_umcu&metric=coverage)](https://sonarcloud.io/dashboard?id=snorben_eeg_preprocessing_umcu) |
| Documentation                      | [![Documentation Status](https://readthedocs.org/projects/eeg_preprocessing_umcu/badge/?version=latest)](https://eeg_preprocessing_umcu.readthedocs.io/en/latest/?badge=latest) |
| **GitHub Actions**                 | &nbsp; |
| Build                              | [![build](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/build.yml/badge.svg)](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/build.yml) |
| Citation data consistency          | [![cffconvert](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/cffconvert.yml/badge.svg)](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/cffconvert.yml) |
| SonarCloud                         | [![sonarcloud](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/sonarcloud.yml) |
| MarkDown link checker              | [![markdown-link-check](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/markdown-link-check.yml/badge.svg)](https://github.com/snorben/eeg_preprocessing_umcu/actions/workflows/markdown-link-check.yml) |

## What is this software?

With our software, we hope to provide users with an accessible way to preprocess resting-state EEG files, while still including powerful analysis tools. We do this by combining several functions from the MNE (MEG/EEG preprocessing) open-source project. By using an intuitive graphical user interface on top of a Python script, we hope that our software is easy to start using without coding experience, while still allowing more experienced users to adapt the software to their needs by altering the underlying code. 

The software is currently able to:
- Open EEG files of type .txt, .bdf, .edf, .eeg and .fif.
- Open a single EEG or choose analysis settings for an entire batch of files.
- Apply a montage to the raw EEG (including electrode coordinates necessary for some analyses).
- Drop bad channels entirely.
- Interpolate bad channels after visual inspection.
- Apply an average reference.
- Apply independent component analysis to remove artefacts.
- Apply beamformer source reconstruction to the EEG.
- Down sample the file to a lower sample frequency.
- Perform interactive visual epoch selection.
- Perform filtering in different frequency bands and broadband output.
- After performing analyses on a batch, rerun the batch with preservation of channel and epoch selection.
- Log the chosen settings and performed analyses steps in a log file.

The software is not (yet) able to:
- Analyse task EEG data.
- Calculate quantitative features on the output epochs (coming in the near future).
- Open EEG files with data types not mentioned previously.

## Installation

To install eeg_preprocessing_umcu from GitHub repository, do:

```console
git clone git@github.com:snorben/eeg_preprocessing_umcu.git
cd eeg_preprocessing_umcu
python -m pip install .
```

## Documentation

Include a link to your project's full documentation here.

## Contributing

If you want to contribute to the development of eeg_preprocessing_umcu,
have a look at the [contribution guidelines](CONTRIBUTING.md).

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
