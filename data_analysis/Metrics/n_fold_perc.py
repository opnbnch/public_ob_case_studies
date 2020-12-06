import pandas as pd
import numpy as np


def n_fold_perc(x, y, n):
    """
    Calculate percent of compounds that are within n-fold of truth
    :float_vec x: true values
    :float_vec y: predicted values
    :float n: folds within which to calculate % error
    """

    keep_bool =  ~(pd.isna(x) | pd.isna(y))

    x = np.array(x)[keep_bool]
    y = np.array(y)[keep_bool]

    fold = y/x

    n_fe = [f >= (1/n) and f <= n for f in fold]
    n_fe_perc = 100. * np.sum(n_fe) / len(n_fe)

    return n_fe_perc
