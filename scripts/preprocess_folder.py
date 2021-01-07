#! /user/bin/env python
import argparse, glob, os

from pynwb import NWBHDF5IO

from process_nwb.resample import store_resample
from process_nwb.wavelet_transform import store_wavelet_transform
from process_nwb import store_linenoise_notch_CAR


parser = argparse.ArgumentParser(description='Preprocess nwbs in a folder.' +
                                 '\nPerforms the following steps:' +
                                 '\n1) Resample to frequency and store result,' +
                                 '\n2) Remove 60Hz noise and remove and store the CAR, and' +
                                 '\n3) Perform and store a wavelet decomposition.')
parser.add_argument('folder', type=str, help='Folder')
parser.add_argument('--frequency', type=float, default=400., help='Frequency to resample to.')
parser.add_argument('--filters', type=str, default='default',
                    help='Type of filter bank to use for wavelets.')
parser.add_argument('--acq-name', type=str, default='ElectricalSeries',
                    help='Name of acquisition in NWB file')
parser.add_argument('--chunked', '--chunk', action='store_true',
                    help='Run wavelet transform separately for each channel/band (requires' +
                    'much less memory)')

args = parser.parse_args()

folder = args.folder
frequency = args.frequency
filters = args.filters
acq_name = args.acq_name
chunked = args.chunked

files = glob.glob(os.path.join(folder, '*.nwb'))
for fname in files:
    print('Processing {}'.format(fname))
    with NWBHDF5IO(fname, 'a') as io:
        nwbfile = io.read()
        electrical_series = nwbfile.acquisition[str(acq_name)]
        nwbfile.create_processing_module(name='preprocessing',
                                         description='Preprocessing.')

        _, electrical_series_ds = store_resample(electrical_series,
                                                 nwbfile.processing['preprocessing'],
                                                 frequency)
        del _

        _, electrical_series_CAR = store_linenoise_notch_CAR(electrical_series_ds,
                                                             nwbfile.processing['preprocessing'])
        del _

        _, electrical_series_wvlt = store_wavelet_transform(electrical_series_CAR,
                                                            nwbfile.processing['preprocessing'],
                                                            filters=filters, chunked=chunked)
        del _

        io.write(nwbfile)

    print("Done processing {}".format(fname))
