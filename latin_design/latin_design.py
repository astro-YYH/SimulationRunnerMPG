from typing import Optional
import numpy as np
import pandas as pd

from emukit.core.initial_designs.base import InitialDesignBase
from emukit.core import ParameterSpace
from latin_hypercube import lhscentered

class LatinDesign(InitialDesignBase):
    '''
    Latin hypercube experiment design.

    This is a hybrid of sbird's lyemu latin_hypercube and
    emukit.core.initial_designs.latin_design.LatinDesign
    without using pyDOE
    '''
    def __init__(self, parameter_space: ParameterSpace) -> None:
        '''
        :param parameter_space: The parameter space to generate design for.
        '''
        super(LatinDesign, self).__init__(parameter_space)

    def get_samples(self, point_count : int) -> np.ndarray:
        '''
        Generates requested amount of points.

        :param point_count: Number of points required.
        :return: A numpy array of generated samples,
            shape (point_count x space_dim)
        '''
        bounds = self.parameter_space.get_bounds()

        # implement sbird's latin hypercube
        X_design_aux = lhscentered(len(bounds), point_count)


        ones = np.ones((X_design_aux.shape[0], 1))

        lower_bound = np.asarray(bounds)[:, 0].reshape(1, len(bounds))
        upper_bound = np.asarray(bounds)[:, 1].reshape(1, len(bounds))

        diff = upper_bound - lower_bound

        X_design = np.dot(ones, lower_bound) + X_design_aux * np.dot(ones, diff)

        # this line is not doing anything for the default setting:
        # see: https://github.com/amzn/emukit/blob/master/emukit/core/parameter.py#L31
        samples = self.parameter_space.round(X_design)

        return samples

    def get_slhd_samples(self, filename: str = "SLHD_t20_m3_k5_seed0.csv", slice: Optional[int] = None) -> np.ndarray:
        """
        Parameters:
        ----
        filename: the path to the csv file, output from R SLHD package.
        slice: the slice you want to use. If none, use all slices.
        """
        slhd = pd.read_csv(filename)

        # sliced latin hypercube
        slices = slhd.values[:, 0]
        if slice == None:
            X_design_aux = slhd.values[:, 1:]
        else:
            X_design_aux = slhd.values[slices == slice, 1:]

        bounds = self.parameter_space.get_bounds()

        ones = np.ones((X_design_aux.shape[0], 1))

        lower_bound = np.asarray(bounds)[:, 0].reshape(1, len(bounds))
        upper_bound = np.asarray(bounds)[:, 1].reshape(1, len(bounds))

        diff = upper_bound - lower_bound

        X_design = np.dot(ones, lower_bound) + X_design_aux * np.dot(ones, diff)

        # this line is not doing anything for the default setting:
        # see: https://github.com/amzn/emukit/blob/master/emukit/core/parameter.py#L31
        samples = self.parameter_space.round(X_design)

        return samples
