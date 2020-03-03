# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class Quadratic_Mean(Combination):
    """Class for calculation of quadratic mean."""

    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary or numpy.ndarray): Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_quadratic_mean()

    def get_quadratic_mean(self):
        """
        Performs calculation of quadratic mean.

        Returns:
            gm: Dictionary of quadratic mean.
        """
        if 'freqs' in self.combination_data:
            time_freq = self.combination_data.pop('freqs')
            horizontal_traces = []
            qm = {}
            for chan in [c for c in self.combination_data]:
                horizontal_traces += [self.combination_data[chan]]
            qm['freqs'] = time_freq
            qm[''] = np.sqrt(np.mean(
                [np.abs(trace)**2 for trace in horizontal_traces], axis=0))
        else:
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            qm = {'': np.sqrt(np.mean([h1**2, h2**2]))}
        return qm
