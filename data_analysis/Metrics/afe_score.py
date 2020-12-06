import pandas as pd
import numpy as np


def afe_score(x, y):
    """
    Absolute average fold error calculation (measure of bias)
    :float_vec x: true values
    :float_vec y: predicted values
    """

    keep_bool = ~ (pd.isna(x) | pd.isna(y))

    x = np.array(x)[keep_bool]
    y = np.array(y)[keep_bool]

    fold = y/x

    afe = 10**(1/len(fold)*np.sum(np.log10(fold)))

    return afe
