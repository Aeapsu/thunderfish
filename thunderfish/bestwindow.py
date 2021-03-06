"""
# Best-window selection
Functions needed for selecting the region within a recording with the
most stable signal of largest amplitude that is not clipped.

## Main functions:
- `clip_amplitudes()`: estimated clipping amplitudes from the data.
- `best_window_indices()`: select start- and end-indices of the best window
- `best_window_times()`: select start end end-time of the best window
- `best_window()`: return data of the best window

## Configuration parameter
- `add_clip_config()`: add parameters for clip_amplitudes() to configuration.
- `clip_args()`: retrieve parameters for clip_amplitudes() from configuration.
- `add_best_window_config()`: add parameters for best_window() to configuration.
- `best_window_args()`: retrieve parameters for best_window*() from configuration.

## Visualization of the algorithms
- `plot_clipping()`: visualization of the algorithm for detecting clipped amplitudes in clip_amplitudes().
- `plot_best_window()`: visualization of the algorithm used in best_window_indices().
"""

import numpy as np
from .eventdetection import percentile_threshold, detect_peaks, trim_to_peak
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass


def clip_amplitudes(data, win_indices, min_fac=2.0, nbins=20,
                    min_ampl=-1.0, max_ampl=1.0,
                    plot_hist_func=None, **kwargs):
    """Find the amplitudes where the signal clips by looking at
    the histograms in data segements of win_indices length.
    If the bins at the edges are more than min_fac times as large as
    the neighboring bins, clipping at the bin's amplitude is assumed.

    Args:
      data (array): 1-D array with the data.
      win_indices (int): size of the analysis window in indices.
      min_fac (float): if the first or the second bin is at least min_fac times
        as large as the third bin, their upper bin edge is set as min_clip.
        Likewise for the last and next-to last bin.
      nbins (int): number of bins used for computing a histogram within min_ampl and max_ampl
      min_ampl (float): minimum to be expected amplitude of the data
      max_ampl (float): maximum to be expected amplitude of the data
      plot_hist_func(data, winx0, winx1, bins, h,
                     min_clip, max_clip, min_ampl, max_ampl, kwargs):
        function for visualizing the histograms, is called for every window.
        plot_clipping() is a simple function that can be passed as plot_hist_func.
        data: the full data array
        winx0: the start index of the current window
        winx1: the end index of the current window
        bins: the bin edges of the histogram
        h: the histogram, plot it with plt.bar(bins[:-1], h, width=np.mean(np.diff(bins)))
        min_clip: the current value of the minimum clip amplitude
        max_clip: the current value of the minimum clip amplitude
        min_ampl: the minimum amplitude of the data
        max_ampl: the maximum amplitude of the data
        kwargs: further user supplied key-word arguments.

    Returns:
      min_clip : minimum amplitude that is not clipped.
      max_clip : maximum amplitude that is not clipped.
    """

    min_clipa = min_ampl
    max_clipa = max_ampl
    bins = np.linspace(min_ampl, max_ampl, nbins, endpoint=True)
    win_tinxs = np.arange(0, len(data) - win_indices, win_indices)
    for wtinx in win_tinxs:
        h, b = np.histogram(data[wtinx:wtinx + win_indices], bins)
        if h[0] > min_fac * h[2] and b[0] < -0.4:
            if h[1] > min_fac * h[2] and b[2] > min_clipa:
                min_clipa = b[2]
            elif b[1] > min_clipa:
                min_clipa = b[1]
        if h[-1] > min_fac * h[-3] and b[-1] > 0.4:
            if h[-2] > min_fac * h[-3] and b[-3] < max_clipa:
                max_clipa = b[-3]
            elif b[-2] < max_clipa:
                max_clipa = b[-2]
        if plot_hist_func:
            plot_hist_func(data, wtinx, wtinx + win_indices,
                           b, h, min_clipa, max_clipa,
                           min_ampl, max_ampl, **kwargs)
    return min_clipa, max_clipa


def plot_clipping(data, winx0, winx1, bins,
                  h, min_clip, max_clip, min_ampl, max_ampl):
    """Visualize the data histograms and the detected clipping amplitudes in clip_amplitudes().
    """
    plt.subplot(2, 1, 1)
    plt.plot(data[winx0:winx1], 'b')
    plt.axhline(min_clip, color='r')
    plt.axhline(max_clip, color='r')
    plt.ylim(-1.0, 1.0)
    plt.subplot(2, 1, 2)
    plt.bar(bins[:-1], h, width=np.mean(np.diff(bins)))
    plt.axvline(min_clip, color='r')
    plt.axvline(max_clip, color='r')
    plt.xlim(-1.0, 1.0)
    plt.show()


def add_clip_config(cfg, min_clip=0.0, max_clip=0.0,
                    window=1.0, min_fac=2.0, nbins=20,
                    min_ampl=-1.0, max_ampl=1.0):
    """ Add parameter needed for clip_amplitudes() as
    a new section to a configuration.

    Args:
      cfg (ConfigFile): the configuration
      min_clip (float): default minimum clip amplitude.
      max_clip (float): default maximum clip amplitude.
      See clip_amplitudes() for details on the remaining arguments.
    """

    cfg.add_section('Clipping amplitudes:')
    cfg.add('minClipAmplitude', min_clip, '', 'Minimum amplitude that is not clipped. If zero estimate from data.')
    cfg.add('maxClipAmplitude', max_clip, '', 'Maximum amplitude that is not clipped. If zero estimate from data.')
    cfg.add('clipWindow', window, 's', 'Window size for estimating clip amplitudes.')
    cfg.add('clipBins', nbins, '', 'Number of bins used for constructing histograms of signal amplitudes.')
    cfg.add('minClipFactor', min_fac, '',
            'Edge bins of the histogram of clipped signals have to be larger then their neighbors by this factor.')
    cfg.add('minDataAmplitude', min_ampl, '', 'Minimum amplitude that is to be expected  in the data.')
    cfg.add('maxDataAmplitude', max_ampl, '', 'Maximum amplitude that is to be expected  in the data.')


def clip_args(cfg, rate):
    """ Translates a configuration to the
    respective parameter names of the function clip_amplitudes().
    The return value can then be passed as key-word arguments to this function.

    Args:
      cfg (ConfigFile): the configuration
      rate (float): the sampling rate of the data

    Returns:
      a (dict): dictionary with names of arguments of the clip_amplitudes() function and their values as supplied by cfg.
    """
    a = cfg.map({'min_fac': 'minClipFactor', 'nbins': 'clipBins',
                 'min_ampl': 'minDataAmplitude', 'max_ampl': 'maxDataAmplitude'})
    a['win_indices'] = int(cfg.value('clipWindow') * rate)
    return a


def best_window_indices(data, samplerate, single=True, win_size=1., win_shift=0.1,
                        th_factor=0.8, percentile=10.0, min_clip=-np.inf, max_clip=np.inf,
                        w_cv_interv=1.0, w_ampl=1.0, w_cv_ampl=1.0, tolerance=0.5,
                        plot_data_func=None, **kwargs):
    """ Detect the best window of the data to be analyzed. The data have
    been sampled with rate Hz.
    
    First, large peaks and troughs of the data are detected.  Peaks and
    troughs have to be separated in amplitude by at least the value of a
    dynamic threshold.  The threshold is computed in win_shift wide
    windows as thresh_ampl_fac times the interpercentile range at
    the percentile and 100.0-percentile percentile of the data
    using the eventdetection.percentile_threshold() function.

    Second, criteria for selecting the best window are computed for each
    window of width win_size shifted by win_shift trough the data. The
    three criteria are:

    - the coefficient of variation of the inter-peak and inter-trough
    intervals.
    - the mean peak-to-trough amplitude multiplied with the fraction of
    non clipped peak and trough amplitudes.
    - the coefficient of variation of the peak-to-trough amplitude.

    Third, a cost function is computed as a weighted sum of the three
    criteria (mean-amplitude is taken negatively). The weights are given
    by w_cv_interv, w_ampl, and w_cv_ampl.

    Finally, a threshold is set to the minimum value of the cost
    function plus tolerance.  Then the largest region with the cost
    function below this threshold is selected as the best window.  If
    single is True, then only the single window with smallest cost
    within the selected largest region is returned.

    Data of the best window algorithm can be visualized by supplying the
    function plot_data_func.  Additional arguments for this function can
    be supplied via key-word arguments kwargs.

    :param data: (1-D array). The data to be analyzed
    :param samplerate: (float). Sampling rate of the data in Hz
    :param single: (boolean). If true return only the single window with the smallest cost. If False return the largest window with the cost below the minimum cost plus tolerance.
    :param win_size: (float). Size of the best window in seconds. Choose it large enough for a minimum analysis.
    :param win_shift: (float). Time shift in seconds between windows. Should be smaller or equal to win_size and not smaller than about one tenth of win_shift.
    :param percentile: (float). percentile parameter for the eventdetection.percentile_threshold() function used to estimate thresholds for detecting peaks in the data.
    :param th_factor: (float). th_factor parameter for the eventdetection.percentile_threshold() function used to estimate thresholds for detecting peaks in the data.
    :param min_clip: (float). Minimum amplitude below which data are clipped.
    :param max_clip: (float). Maximum amplitude above which data are clipped.
    :param w_cv_interv: (float). Weight for the coefficient of variation of the intervals.
    :param w_ampl: (float). Weight for the mean peak-to-trough amplitude.
    :param w_cv_ampl: (float). Weight for the coefficient of variation of the amplitudes.
    :param tolerance: (float). Added to the minimum cost for selecting the region of best windows.
    :param plot_data_func: Function for plotting the raw data, detected peaks and troughs, the criteria,
    the cost function and the selected best window.
    plot_best_window() is a simple function that can be passed as plot_data_func.
        plot_data_func(data, rate, peak_idx, trough_idx, idx0, idx1,
                       win_start_times, cv_interv, mean_ampl, cv_ampl, clipped_frac, cost,
                       thresh, valid_wins, **kwargs)
        :param data (array): the raw data.
        :param rate (float): the sampling rate of the data.
        :param peak_idx (array): indices into raw data indicating detected peaks.
        :param trough_idx (array): indices into raw data indicating detected troughs.
        :param idx0 (int): index of the start of the best window.
        :param idx1 (int): index of the end of the best window.
        :param win_start_times (array): the times of the analysis windows.
        :param cv_interv (array): the coefficient of variation of the inter-peak and -trough intervals.
        :param mean_ampl (array): the mean peak-to-trough amplitude.
        :param cv_ampl (array): the coefficient of variation of the peak-to-trough amplitudes.
        :param clipped_frac (array): the fraction of clipped peaks or troughs.
        :param cost (array): the cost function.
        :param thresh (float): the threshold for the cost function.
        :param valid_wins (array): boolean array indicating the windows which fulfill all three criteria.
        :param **kwargs: further user supplied key-word arguments.
    :param kwargs: Keyword arguments passed to plot_data_func and plot_window_func. 
    
    :return start_index: int. Index of the start of the best window.
    :return end_index: int. Index of the end of the best window.
    :return clipped: float. The fraction of clipped peaks or troughs.
    """

    # too little data:
    if len(data) / samplerate <= win_size:
        raise UserWarning('not enough data')

    # threshold for peak detection:
    threshold = percentile_threshold(data, samplerate, win_shift,
                                     th_factor=th_factor, percentile=percentile)

    # detect large peaks and troughs:
    peak_idx, trough_idx = detect_peaks(data, threshold)
    if len(peak_idx) == 0 or len(trough_idx) == 0:
        raise UserWarning('no peaks or troughs detected')

    # compute cv of intervals, mean peak amplitude and its cv:
    invalid_cv = 1000.0
    win_size_indices = int(win_size * samplerate)
    win_start_inxs = np.arange(0, len(data) - win_size_indices, int(win_shift * samplerate))
    cv_interv = np.zeros(len(win_start_inxs))
    mean_ampl = np.zeros(len(win_start_inxs))
    cv_ampl = np.zeros(len(win_start_inxs))
    clipped_frac = np.zeros(len(win_start_inxs))
    for i, wtinx in enumerate(win_start_inxs):
        # indices of peaks and troughs inside analysis window:
        pinx = (peak_idx >= wtinx) & (peak_idx <= wtinx + win_size_indices)
        tinx = (trough_idx >= wtinx) & (trough_idx <= wtinx + win_size_indices)
        p_idx, t_idx = trim_to_peak(peak_idx[pinx], trough_idx[tinx])
        # interval statistics:
        ipis = np.diff(p_idx)
        itis = np.diff(t_idx)
        if len(ipis) > 2:
            cv_interv[i] = 0.5 * (np.std(ipis) / np.mean(ipis) + np.std(itis) / np.mean(itis))
            # penalize regions without detected peaks:
            mean_interv = np.mean(ipis)
            if p_idx[0] - wtinx > mean_interv:
                cv_interv[i] *= (p_idx[0] - wtinx) / mean_interv
            if wtinx + win_size_indices - p_idx[-1] > mean_interv:
                cv_interv[i] *= (wtinx + win_size_indices - p_idx[-1]) / mean_interv
        else:
            cv_interv[i] = invalid_cv
        # statistics of peak-to-trough amplitude:
        p2t_ampl = data[p_idx] - data[t_idx]
        if len(p2t_ampl) > 2:
            mean_ampl[i] = np.mean(p2t_ampl)
            cv_ampl[i] = np.std(p2t_ampl) / mean_ampl[i]
            # penalize for clipped peaks:
            clipped_frac[i] = float(np.sum(data[p_idx] > max_clip) +
                                    np.sum(data[t_idx] < min_clip)) / 2.0 / len(p2t_ampl)
            mean_ampl[i] *= (1.0 - clipped_frac[i]) ** 2.0
        else:
            mean_ampl[i] = 0.0
            cv_ampl[i] = invalid_cv

    # check:
    if len(mean_ampl[mean_ampl > 0.0]) <= 0:
        raise UserWarning('no finite amplitudes detected')
    if len(cv_interv[cv_interv < invalid_cv]) <= 0:
        raise UserWarning('no valid interval cv detected')
    if len(cv_ampl[cv_ampl < invalid_cv]) <= 0:
        raise UserWarning('no valid amplitude cv detected')

    # cost function:
    cost = w_cv_interv * cv_interv + w_cv_ampl * cv_ampl - w_ampl * mean_ampl
    thresh = np.min(cost) + tolerance

    # find largest region with low costs:
    valid_win_idx = np.nonzero(cost <= thresh)[0]
    cidx0 = valid_win_idx[0]  # start of current window
    cidx1 = cidx0 + 1  # end of current window
    win_idx0 = cidx0   # start of largest window
    win_idx1 = cidx1   # end of largest window
    i = 1
    while i < len(valid_win_idx):  # loop through all valid window positions
        if valid_win_idx[i] == valid_win_idx[i - 1] + 1:
            cidx1 = valid_win_idx[i] + 1
        else:
            cidx0 = valid_win_idx[i]
        if cidx1 - cidx0 > win_idx1 - win_idx0:  # current window is largest
            win_idx0 = cidx0
            win_idx1 = cidx1
        i += 1

    # find single best window within the largest region:
    if single:
        win_idx0 += np.argmin(cost[win_idx0:win_idx1])
        win_idx1 = win_idx0 + 1

    # retrive indices of best window for data:
    idx0 = win_start_inxs[win_idx0]
    idx1 = win_start_inxs[win_idx1 - 1] + win_size_indices

    # clipped data?
    clipped = np.mean(clipped_frac[win_idx0:win_idx1])

    if plot_data_func:
        plot_data_func(data, samplerate, peak_idx, trough_idx, idx0, idx1,
                       win_start_inxs / samplerate, cv_interv, mean_ampl, cv_ampl, clipped_frac,
                       cost, thresh, win_idx0, win_idx1, **kwargs)

    return idx0, idx1, clipped


def best_window_times(data, samplerate, single=True, win_size=1., win_shift=0.1,
                      th_factor=0.8, percentile=10.0, min_clip=-np.inf, max_clip=np.inf,
                      w_cv_interv=1.0, w_ampl=1.0, w_cv_ampl=1.0, tolerance=0.5,
                      plot_data_func=None, **kwargs):
    """Finds the window within data with the best data. See best_window_indices() for details.

    Returns:
      start_time (float): Time of the start of the best window.
      end_time (float): Time of the end of the best window.
      clipped (float): The fraction of clipped peaks or troughs.
    """
    start_inx, end_inx, clipped = best_window_indices(data, samplerate, single,
                                                      win_size, win_shift,
                                                      th_factor, percentile,
                                                      min_clip, max_clip,
                                                      w_cv_interv, w_ampl, w_cv_ampl, tolerance,
                                                      plot_data_func, **kwargs)
    return start_inx / samplerate, end_inx / samplerate, clipped


def best_window(data, samplerate, single=True, win_size=1., win_shift=0.1,
                th_factor=0.8, percentile=10.0, min_clip=-np.inf, max_clip=np.inf,
                w_cv_interv=1.0, w_ampl=1.0, w_cv_ampl=1.0, tolerance=0.5,
                plot_data_func=None, **kwargs):
    """Finds the window within data with the best data. See best_window_indices() for details.

    Returns:
      data (array): the data of the best window.
      clipped (float): The fraction of clipped peaks or troughs.
    """
    start_inx, end_inx, clipped = best_window_indices(data, samplerate, single,
                                                      win_size, win_shift,
                                                      th_factor, percentile,
                                                      min_clip, max_clip,
                                                      w_cv_interv, w_ampl, w_cv_ampl,
                                                      tolerance, plot_data_func, **kwargs)
    return data[start_inx:end_inx], clipped


def plot_best_window(data, rate, peak_idx, trough_idx, idx0, idx1,
                     win_times, cv_interv, mean_ampl, cv_ampl, clipped_frac,
                     cost, thresh, win_idx0, win_idx1, ax):
    """Visualize the cost function of best_window_indices().
    """
    # raw data:
    time = np.arange(0.0, len(data)) / rate
    ax[0].plot(time, data, lw=3)
    if np.mean(clipped_frac[win_idx0:win_idx1]) > 0.01:
        ax[0].plot(time[idx0:idx1], data[idx0:idx1], color='magenta', lw=3)
    else:
        ax[0].plot(time[idx0:idx1], data[idx0:idx1], color='grey', lw=3)
    ax[0].plot(time[peak_idx], data[peak_idx], 'o', mfc='red', ms=6)
    ax[0].plot(time[trough_idx], data[trough_idx], 'o', mfc='green', ms=6)
    up_lim = np.max(data) * 1.05
    down_lim = np.min(data) * .95
    ax[0].set_ylim((down_lim, up_lim))
    ax[0].set_ylabel('Amplitude [a.u]')

    # cv of inter-peak intervals:
    ax[1].plot(win_times[cv_interv < 1000.0], cv_interv[cv_interv < 1000.0], 'o', ms=10, color='grey', mew=2.,
               mec='black', alpha=0.6)
    ax[1].plot(win_times[win_idx0:win_idx1], cv_interv[win_idx0:win_idx1], 'o', ms=10, color='red', mew=2., mec='black',
               alpha=0.6)
    ax[1].set_ylabel('CV intervals')
    ax[1].set_ylim(bottom=0.0)

    # mean amplitude:
    ax[2].plot(win_times[mean_ampl > 0.0], mean_ampl[mean_ampl > 0.0], 'o', ms=10, color='grey', mew=2., mec='black',
               alpha=0.6)
    ax[2].plot(win_times[win_idx0:win_idx1], mean_ampl[win_idx0:win_idx1], 'o', ms=10, color='red', mew=2., mec='black',
               alpha=0.6)
    ax[2].set_ylabel('Mean amplitude [a.u]')
    ax[2].set_ylim(bottom=0.0)

    # cv:
    ax[3].plot(win_times[cv_ampl < 1000.0], cv_ampl[cv_ampl < 1000.0], 'o', ms=10, color='grey', mew=2., mec='black',
               alpha=0.6)
    ax[3].plot(win_times[win_idx0:win_idx1], cv_ampl[win_idx0:win_idx1], 'o', ms=10, color='red', mew=2., mec='black',
               alpha=0.6)
    ax[3].set_ylabel('CV amplitude')
    ax[3].set_ylim(bottom=0.0)

    # cost:
    ax[4].plot(win_times[cost < thresh + 10], cost[cost < thresh + 10], 'o', ms=10, color='grey', mew=2., mec='black',
               alpha=0.6)
    ax[4].plot(win_times[win_idx0:win_idx1], cost[win_idx0:win_idx1], 'o', ms=10, color='red', mew=2., mec='black',
               alpha=0.6)
    ax[4].axhline(thresh, color='k')
    ax[4].set_ylabel('Cost')
    ax[4].set_xlabel('Time [sec]')

    
def add_best_window_config(cfg, single=True, win_size=1., win_shift=0.1,
                           th_factor=0.8, percentile=10.0,
                           min_clip=-np.inf, max_clip=np.inf,
                           w_cv_interv=1.0, w_ampl=1.0, w_cv_ampl=1.0,
                           tolerance=0.5):
    """ Add parameter needed for the best_window() functions as
    a new section to a configuration dictionary.

    Args:
      cfg (ConfigFile): the configuration
      See best_window_indices() for details on the remaining arguments.
    """

    cfg.add_section('Best window detection:')
    cfg.add('bestWindowSize', win_size, 's', 'Size of the best window.')
    cfg.add('bestWindowShift', win_shift, 's',
            'Increment for shifting the analysis windows trough the data.')
    cfg.add('bestWindowThresholdPercentile', percentile, '%',
            'Percentile for estimating interpercentile range.')
    cfg.add('bestWindowThresholdFactor', th_factor, '',
            'Threshold for detecting peaks is interperecntile range of the data times this factor.')
    cfg.add('weightCVInterval', w_cv_interv, '',
            'Weight factor for the coefficient of variation of the inter-peak and inter-trough intervals.')
    cfg.add('weightAmplitude', w_ampl, '',
            'Weight factor for the mean peak-to-trough amplitudes.')
    cfg.add('weightCVAmplitude', w_cv_ampl, '',
            'Weight factor for the coefficient of variation of the peak-to-trough amplitude.')
    cfg.add('bestWindowTolerance', tolerance, '',
            'Add this to the minimum value of the cost function to get a threshold for selecting the largest best window.')
    cfg.add('singleBestWindow', single, '',
            'Return only a single best window. If False return the largest valid best window.')


def best_window_args(cfg):
    """ Translates a configuration to the
    respective parameter names of the functions best_window*().
    The return value can then be passed as key-word arguments to these functions.

    Args:
      cfg (ConfigFile): the configuration

    Returns:
      a (dict): dictionary with names of arguments of the best_window*() functions and their values as supplied by cfg.
    """
    return cfg.map({'win_size': 'bestWindowSize',
                    'win_shift': 'bestWindowShift',
                    'percentile': 'bestWindowThresholdPercentile',
                    'th_factor': 'bestWindowThresholdFactor',
                    'w_cv_interv': 'weightCVInterval',
                    'w_ampl': 'weightAmplitude',
                    'w_cv_ampl': 'weightCVAmplitude',
                    'tolerance': 'bestWindowTolerance',
                    'single': 'singleBestWindow'})


if __name__ == "__main__":
    print("Checking bestwindow module ...")
    import sys

    title = "bestwindow"
    if len(sys.argv) < 2:
        # generate data:
        print("generate waveform...")
        rate = 100000.0
        time = np.arange(0.0, 1.0, 1.0 / rate)
        f = 600.0
        snippets = []
        amf = 20.0
        for ampl in [0.2, 0.5, 0.8]:
            for am_ampl in [0.0, 0.3, 0.9]:
                data = ampl * np.sin(2.0 * np.pi * f * time) * (1.0 + am_ampl * np.sin(2.0 * np.pi * amf * time))
                data[data > 1.3] = 1.3
                data[data < -1.3] = -1.3
                snippets.extend(data)
        data = np.asarray(snippets)
        title = "test sines"
        data += 0.01 * np.random.randn(len(data))
    else:
        from .dataloader import load_data

        print("load %s ..." % sys.argv[1])
        data, rate, unit = load_data(sys.argv[1], 0)
        title = sys.argv[1]

    # determine clipping amplitudes:
    clip_win_size = 0.5
    min_clip_fac = 2.0
    min_clip, max_clip = clip_amplitudes(data, int(clip_win_size * rate),
                                         min_fac=min_clip_fac)
    # min_clip, max_clip = clip_amplitudes(data, int(clip_win_size*rate),
    #                                      min_fac=min_clip_fac,
    #                                      plot_hist_func=plot_clipping)

    # setup plots:
    fig, ax = plt.subplots(5, sharex=True, figsize=(20, 12))
    fig.canvas.set_window_title(title)

    # compute best window:
    print("call bestwindow() function...")
    best_window_indices(data, rate, single=False,
                        win_size=4.0, win_shift=0.5, th_factor=0.8, percentile=10.0,
                        min_clip=min_clip, max_clip=max_clip,
                        w_cv_ampl=10.0, tolerance=0.5,
                        plot_data_func=plot_best_window, ax=ax)

    plt.tight_layout()
    plt.show()
