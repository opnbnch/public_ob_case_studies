import argparse
import json
import os
import pandas as pd
import sys

import meta_utils


def read_data(path):

    meta = meta_utils.read_meta(path)

    data_path = os.path.join(path, os.path.basename(meta.get('data_path')))

    smiles_col = meta.get('smiles_col')
    class_col = meta.get('class_col')
    value_col = meta.get('value_col')
    column_subset = [col for col in [smiles_col, class_col, value_col] if col]

    # subset to columns of interest
    df = pd.read_csv(data_path).loc[::,column_subset]

    return(df)
