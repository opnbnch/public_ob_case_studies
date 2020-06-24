import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_std_data, write_std

from utils.curate_utils import df_filter_invalid_smi, df_filter_replicates
from utils.curate_utils import get_keep_indices, __version__
from utils.curate_utils import ask_for_filter, process_filter_input, filters

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help='path to directory with data to curate')
    parser.add_argument('--filter_fn', '-f', type=str, default=None,
                        choices=list(filters.keys()),
                        help='specify a filter function for curation')
    args = parser.parse_args()

    meta = read_meta(args.path)
    meta_path = meta.get('meta_path')
    std_smiles_col = meta.get('std_smiles_col')
    std_key_col = meta.get('std_key_col')

    # First, read standardized data and remove invalid smiles
    std_data = read_std_data(args.path)
    curated_data = df_filter_invalid_smi(std_data, std_smiles_col)

    # Then, process filter function and extract indices to keep
    filter_fn = process_filter_input(args.filter_fn, filters)
    idx_keep_dict = get_keep_indices(curated_data, std_key_col, filter_fn)

    # Filter replicates and write data to curated data path
    curated_data = df_filter_replicates(curated_data, idx_keep_dict)
    curated_data_path = write_std(curated_data, args.path, prefix='curated_')

    curated_meta = {'curated_data_path': curated_data_path,
                    'curated_indices': idx_keep_dict,
                    'curated_rows': int(curated_data.shape[0]),
                    'curation_function': filter_fn.__name__,
                    'curated_version': __version__,
                    'curated_utc_fix': int(time.time())}

    add_meta(meta_path, curated_meta)  # Update metadata

    print("Curated df will be written to:", curated_data_path)
    print("Updated metadata at:", meta_path)
