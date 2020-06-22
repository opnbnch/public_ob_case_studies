

import utils.meta_utils as meta_utils

__version__ = 'v1.0.0 (06-22-2020)'

def read_std_data(path):
    """
    Read the relevant columns from a dataframe given the path
    :str path: path to dir where data lives
    """

    meta = meta_utils.read_meta(path)
    data_path = os.path.join(path, os.path.basename(meta.get('std_data_path')))
    df = pd.read_csv(data_path)

    return(df)
