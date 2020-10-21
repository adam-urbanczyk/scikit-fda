"""Depth Measures Module.

This module includes different methods to order functional data,
from the center (larger values) outwards(smaller ones)."""

import itertools

import scipy.integrate

import numpy as np

from . import multivariate
from .multivariate import Depth


__author__ = "Amanda Hernando Bernabé"
__email__ = "amanda.hernando@estudiante.uam.es"


class IntegratedDepth(Depth):
    r"""
    Functional depth as the integral of a multivariate depth.

    Args:
        multivariate_depth (Depth): Multivariate depth to integrate.
            By default it is the one used by Fraiman and Muniz, that is,

            .. math::
                D(x) = 1 - \left\lvert \frac{1}{2}- F(x)\right\rvert

    Examples:

        >>> import skfda
        >>>
        >>> data_matrix = [[1, 1, 2, 3, 2.5, 2],
        ...                [0.5, 0.5, 1, 2, 1.5, 1],
        ...                [-1, -1, -0.5, 1, 1, 0.5],
        ...                [-0.5, -0.5, -0.5, -1, -1, -1]]
        >>> grid_points = [0, 2, 4, 6, 8, 10]
        >>> fd = skfda.FDataGrid(data_matrix, grid_points)
        >>> depth = skfda.exploratory.depth.IntegratedDepth()
        >>> depth(fd)
        array([ 0.5  ,  0.75 ,  0.925,  0.875])

    References:

        Fraiman, R., & Muniz, G. (2001). Trimmed means for functional
        data. Test, 10(2), 419–440. https://doi.org/10.1007/BF02595706


    """

    def __init__(self, *,
                 multivariate_depth=multivariate._UnivariateFraimanMuniz()):
        self.multivariate_depth = multivariate_depth

    def fit(self, X, y=None):

        self._domain_range = X.domain_range
        self._grid_points = X.grid_points
        self.multivariate_depth.fit(X.data_matrix)
        return self

    def predict(self, X):

        pointwise_depth = self.multivariate_depth.predict(X.data_matrix)

        interval_len = (self._domain_range[0][1]
                        - self._domain_range[0][0])

        integrand = pointwise_depth

        for d, s in zip(X.domain_range, X.grid_points):
            integrand = scipy.integrate.simps(integrand,
                                              x=s,
                                              axis=1)
            interval_len = d[1] - d[0]
            integrand /= interval_len

        return integrand

    @property
    def max(self):
        return self.multivariate_depth.max

    @property
    def min(self):
        return self.multivariate_depth.min


class ModifiedBandDepth(IntegratedDepth):
    r"""
    Implementation of Modified Band Depth for functional data.

    The band depth of each sample is obtained by computing the fraction of time
    its graph is contained in the bands determined by two sample curves.
    In the case the fdatagrid domain dimension is 2, instead of curves,
    surfaces determine the bands. In larger dimensions, the hyperplanes
    determine the bands.

    Examples:

        >>> import skfda
        >>>
        >>> data_matrix = [[1, 1, 2, 3, 2.5, 2],
        ...                [0.5, 0.5, 1, 2, 1.5, 1],
        ...                [-1, -1, -0.5, 1, 1, 0.5],
        ...                [-0.5, -0.5, -0.5, -1, -1, -1]]
        >>> grid_points = [0, 2, 4, 6, 8, 10]
        >>> fd = skfda.FDataGrid(data_matrix, grid_points)
        >>> depth = skfda.exploratory.depth.ModifiedBandDepth()
        >>> values = depth(fd)
        >>> values.round(2)
        array([ 0.5 ,  0.83,  0.73,  0.67])

    References:

        López-Pintado, S., & Romo, J. (2009). On the Concept of
        Depth for Functional Data. Journal of the American Statistical
        Association, 104(486), 718–734.
        https://doi.org/10.1198/jasa.2009.0108
    """

    def __init__(self):
        super().__init__(multivariate_depth=multivariate.SimplicialDepth())


class BandDepth(Depth):
    r"""
    Implementation of Band Depth for functional data.

    The band depth of each sample is obtained by computing the fraction of the
    bands determined by two sample curves containing the whole graph of the
    first one. In the case the fdatagrid domain dimension is 2, instead of
    curves, surfaces determine the bands. In larger dimensions, the hyperplanes
    determine the bands.

    Examples:

        >>> import skfda
        >>>
        >>> data_matrix = [[1, 1, 2, 3, 2.5, 2],
        ...                [0.5, 0.5, 1, 2, 1.5, 1],
        ...                [-1, -1, -0.5, 1, 1, 0.5],
        ...                [-0.5, -0.5, -0.5, -1, -1, -1]]
        >>> grid_points = [0, 2, 4, 6, 8, 10]
        >>> fd = skfda.FDataGrid(data_matrix, grid_points)
        >>> depth = skfda.exploratory.depth.BandDepth()
        >>> depth(fd)
        array([ 0.5       ,  0.83333333,  0.5       ,  0.5       ])

    References:

        López-Pintado, S., & Romo, J. (2009). On the Concept of
        Depth for Functional Data. Journal of the American Statistical
        Association, 104(486), 718–734.
        https://doi.org/10.1198/jasa.2009.0108

    """

    def fit(self, X, y=None):

        if X.dim_codomain != 1:
            raise NotImplementedError("Band depth not implemented for vector "
                                      "valued functions")

        self._distribution = X
        return self

    def predict(self, X):

        num_in = 0
        n_total = 0

        for f1, f2 in itertools.combinations(self._distribution, 2):
            between_range_1 = (f1.data_matrix <= X.data_matrix) & (
                X.data_matrix <= f2.data_matrix)

            between_range_2 = (f2.data_matrix <= X.data_matrix) & (
                X.data_matrix <= f1.data_matrix)

            between_range = between_range_1 | between_range_2

            num_in += np.all(between_range,
                             axis=tuple(range(1, X.data_matrix.ndim)))
            n_total += 1

        return num_in / n_total
