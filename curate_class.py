import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_std_data
from utils.curate_utils import df_filter_invalid_smi, df_filter_class_replicates
from utils.curate_utils import unanimous_class_filter, get_keep_indices

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data to standardize")
    args = parser.parse_args()

    meta = read_meta(args.path)
    meta_path = meta.get('meta_path')
    std_smiles_col = meta.get('std_smiles_col')
    std_data_path = meta.get('std_data_path')
    std_key_col = meta.get('std_key_col')

    std_data = read_std_data(args.path)

    curated_data = df_filter_invalid_smi(std_data, std_smiles_col)
    idx_keep_dict = get_keep_indices(curated_data,
                                     std_key_col,
                                     filter_fn=unanimous_class_filter)
    curated_data = df_filter_class_replicates(curated_data, idx_keep_dict)

    print(curated_data)
