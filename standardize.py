import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_data, write_std, __version__
from utils.std_utils import df_add_ik, df_add_std_smiles
from utils.class_utils import get_class_map, df_add_std_class

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data to standardize")
    parser.add_argument('smiles_col', type=str,
                        help="name of string where SMILES are stored.")
    parser.add_argument('--class_col', '-c', type=str, default=None,
                        help='when used, standardize class column')
    args = parser.parse_args()

    meta = read_meta(args.path)
    meta_path = meta.get('meta_path')

    add_meta(meta_path, {'smiles_col': args.smiles_col})
    if args.class_col:
        add_meta(meta_path, {'class_col': args.class_col})

    df = read_data(args.path)
    std_df = df_add_ik(df_add_std_smiles(df, 'smiles'), 'std_smiles')

    if args.class_col:

        class_map = get_class_map(std_df, args.class_col)
        std_df = df_add_std_class(std_df, class_map)

        class_meta = {'class_map': class_map,
                      'class_col': args.class_col,
                      'std_class_col': 'std_class'}

        add_meta(meta_path, class_meta)

    std_data_path = write_std(std_df, args.path)
    std_meta = {'std_data_path': std_data_path,
                'smiles_col': args.smiles_col,
                'std_smiles_col': 'std_smiles',
                'std_version': __version__,
                'std_utc_fix': int(time.time())}
    add_meta(meta_path, std_meta)  # Update metadata

    print("Standard df will be written to:", std_data_path)
    print("Updated metadata at:", meta_path)
