import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_std_data, write_std
from utils.curate_utils import df_filter_invalid_smi, df_filter_replicates
from utils.curate_utils import unanimous_class_filter, get_keep_indices
from utils.curate_utils import __version__

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data to standardize")
    parser.add_argument('filter_fn', type=str,
                        help='unanimous or majority filter function')
    args = parser.parse_args()

    filters = ['unanimous', 'majority']
    if args.filter_fn not in filters:
        raise SyntaxError('You must specify one of the following filter '
                          'functions: ' + str(filters))

    meta = read_meta(args.path)
    meta_path = meta.get('meta_path')
    std_smiles_col = meta.get('std_smiles_col')
    std_key_col = meta.get('std_key_col')

    std_data = read_std_data(args.path)

    curated_data = df_filter_invalid_smi(std_data, std_smiles_col)
    idx_keep_dict = get_keep_indices(curated_data,
                                     std_key_col,
                                     filter_fn=unanimous_class_filter)
    curated_data = df_filter_replicates(curated_data, idx_keep_dict)

    curated_data_path = write_std(curated_data, args.path, prefix='curated_')

    curated_meta = {'curated_data_path': curated_data_path,
                    'curated_rows': int(curated_data.shape[0]),
                    'curated_indices': idx_keep_dict,
                    'curated_version': __version__,
                    'curated_utc_fix': int(time.time())}

    add_meta(meta_path, curated_meta)  # Update metadata

    print("Curated df will be written to:", curated_data_path)
    print("Updated metadata at:", meta_path)
