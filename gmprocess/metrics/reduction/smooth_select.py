# Third party imports
import numpy as np

# Local imports
from gmprocess.metrics.exception import PGMException
from gmprocess.metrics.reduction.reduction import Reduction
from gmprocess.smoothing.konno_ohmachi import konno_ohmachi_smooth


class Smooth_Select(Reduction):
    def __init__(self, reduction_data, bandwidth=None, percentile=None,
                 period=None, smoothing=None):
        """
        Args:
            reduction_data (obspy.core.stream.Stream or numpy.ndarray): Intensity
                    measurement component.
            percentile (float): Percentile for rotation calculations.
            period (float): Period for smoothing (Fourier amplitude spectra)
                    calculations.
            smoothing (string): Smoothing type.
            bandwidth (float): Bandwidth for the smoothing operation.

        Raises:
            PGMException: if the bandwidth, period, or smoothing values
                    are None.
        """
        super().__init__(reduction_data, bandwidth=None, percentile=None,
                         period=None, smoothing=None)
        if period is None:
            raise PGMException('Smooth_Select: The period value must '
                               'be defined and of type float or int.')
        if bandwidth is None:
            raise PGMException('Smooth_Select: The bandwidth value must '
                               'be defined and of type float or int.')
        if smoothing is None:
            raise PGMException('Smooth_Select: The smoothing value must '
                               'be defined and of type string.')
        self.period = period
        self.smoothing = smoothing
        self.bandwidth = bandwidth
        self.result = self.get_pick()

    def get_pick(self):
        """
        Performs smoothing and picks values for each defined period.

        Returns:
            picked: Dictionary of values for each period.
        """
        fas_frequencies = 1 / np.asarray([self.period])
        smoothed_values = np.empty_like(fas_frequencies)

        keys = [k for k in self.reduction_data]
        channels = [k for k in keys if k != 'freqs']
        if len(channels) == 1:
            picked = {}
            fft_trace = self.reduction_data[channels[0]]
            if self.smoothing.lower() == 'konno_ohmachi':
                konno_ohmachi_smooth(fft_trace.astype(np.double), self.reduction_data['freqs'],
                                     fas_frequencies, smoothed_values, self.bandwidth)
                picked_value = smoothed_values[0]
                picked[''] = picked_value
        else:
            picked = {}
            for chan in channels:
                fft_trace = self.reduction_data[chan]
                if self.smoothing.lower() == 'konno_ohmachi':
                    konno_ohmachi_smooth(fft_trace.astype(np.double), self.reduction_data['freqs'],
                                         fas_frequencies, smoothed_values, self.bandwidth)
                    picked_value = smoothed_values[0]
                    picked[chan] = picked_value
        return picked
