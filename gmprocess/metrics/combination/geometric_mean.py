# Local imports
import numpy as np

# Third party imports
from gmprocess.metrics.combination.combination import Combination


class Geometric_Mean(Combination):
    """Class for calculation of geometric mean."""

    def __init__(self, combination_data):
        """
        Args:
            combination_data (dictionary or numpy.ndarray):
                Data for calculation.
        """
        super().__init__(combination_data)
        self.result = self.get_geometric_mean()

    def get_geometric_mean(self):
        """
        Performs calculation of geometric mean.

        Returns:
            gm: Dictionary of geometric mean.
        """
        if 'freqs' in self.combination_data:
            time_freq = self.combination_data.pop('freqs')
            horizontal_traces = []
            gm = {}
            for chan in [c for c in self.combination_data]:
                horizontal_traces += [self.combination_data[chan]]
            gm['freqs'] = time_freq
            gm[''] = np.sqrt(np.asarray(horizontal_traces[0])
                             * np.asarray(horizontal_traces[0]))
        else:
            horizontals = self._get_horizontals()
            h1, h2 = horizontals[0], horizontals[1]
            gm = {'': np.sqrt(h1 * h2)}
        return gm
