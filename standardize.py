import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_data, write_std, __version__
from utils.std_utils import df_add_ik, df_add_std_smiles, get_invalid_smiles
from utils.class_utils import get_class_map, df_add_std_class
from utils.std_utils import select_cols, subset_data


def standardize(path, smiles_col, class_col=None):
    """
    :str path: a directory containing metadata and data to be standardized
    :str smiles_col: the name of that data's smiles column
    :str class_col: the name of that data's class column
    """

    # First read meta and store relevant paths into variables.
    meta = read_meta(path)
    meta_path = meta.get('meta_path')
    data_path = meta.get('data_path')

    # Add the smiles col into the meta for later use ...
    add_meta(meta_path, {'smiles_col': smiles_col})
    subset = [smiles_col]

    # Likewise with the class col if one is specified
    if class_col:
        add_meta(meta_path, {'class_col': class_col})
        subset.append(class_col)

    df = read_data(data_path).loc[::, subset]  # Now read in the raw data ...
    std_df = df_add_std_smiles(df, smiles_col)  # Add standardized SMILES ...
    std_df = df_add_ik(std_df, 'std_smiles')  # And InChI keys

    invalids = get_invalid_smiles(df, smiles_col, 'std_smiles')

    # If a class col is specified,
    if class_col:

        # Ask the user for a mapping from their class to integers
        class_map = get_class_map(std_df, class_col)
        std_df = df_add_std_class(std_df, class_map)

        # Store and write class meta
        class_meta = {'class_map': class_map,
                      'class_col': class_col,
                      'std_class_col': 'std_class'}

        add_meta(meta_path, class_meta)

    std_meta = {'std_smiles_col': 'std_smiles',
                'std_key_col': 'inchi_key',
                'invalid_smiles': invalids}

    add_meta(meta_path, std_meta)

    # List of columns to retain for final csv
    default_cols = ['std_smiles', 'std_class']
    kept_cols, removed = select_cols(std_df, default_cols)
    cur_df = subset_data(std_df, kept_cols)
    std_data_path = write_std(cur_df, path, prefix='std_')

    # Write standardized data and store meta
    kept_meta = {'std_data_path': std_data_path,
                    'retained_columns': kept_cols,
                    'removed_columns': removed,
                    'std_version': __version__,
                    'std_utc_fix': int(time.time())}

    add_meta(meta_path, kept_meta)

    # Print write paths
    print("Standard df will be written to:", std_data_path)
    print("Updated metadata at:", meta_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data to standardize")
    parser.add_argument('smiles_col', type=str,
                        help="name of string where SMILES are stored.")
    parser.add_argument('--class_col', '-c', type=str, default=None,
                        help='when used, standardize class column')
    parser.add_argument('--regress_col', '-r', type=str, default=None,
                        help='when used, standardize regression column')
    args = parser.parse_args()

    standardize(args.path, args.smiles_col, args.class_col, args.regress_col)
