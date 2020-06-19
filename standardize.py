import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_data, write_std, __version__
from utils.std_utils import df_add_ik, df_add_std_smiles

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data of interest")
    args = parser.parse_args()

    meta = read_meta(args.path)
    smiles_col = meta.get('smiles_col')
    meta_path = meta.get('meta_path')

    df = read_data(args.path)
    std_df = df_add_ik(df_add_std_smiles(df, smiles_col), 'std_smiles')
    std_data_path = write_std(std_df, args.path)

    std_meta = {'std_data_path': std_data_path,
                'std_smiles_col': 'std_smiles',
                'std_version': __version__,
                'std_utc_fix': int(time.time())}

    print("Standard df will be written to:", std_data_path)
    print("Updated metadata at:", meta_path)

    add_meta(meta_path, std_meta)  # Update metadata
