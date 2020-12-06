import pandas as pd
import numpy as np


def gmfe_score(x, y):
    """
    Geometric mean fold error, also known as average fold error (AAFE)
    :float_vec x: true values
    :float_vec y: predicted values
    """

    keep_bool = ~ (pd.isna(x) | pd.isna(y))

    x = np.array(x)[keep_bool]
    y = np.array(y)[keep_bool]

    fold = y/x

    gmfe = 10**(1/len(fold)*np.sum(np.abs(np.log10(fold))))

    return gmfe
