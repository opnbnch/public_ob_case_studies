import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_data, write_std

from utils.resolve_utils import df_filter_invalid_smi, df_filter_replicates
from utils.resolve_utils import class_keep_indices, __version__
from utils.resolve_utils import process_filter_input, filters
from utils.resolve_utils import value_keep_indices


def resolve_class(path, threshold):

    # Read meta and extra necessary elements
    meta = read_meta(path)
    meta_path = meta.get('meta_path')
    std_data_path = meta.get('std_data_path')
    std_smiles_col = meta.get('std_smiles_col')
    std_key_col = meta.get('std_key_col')
    class_col = meta.get('std_class_col')
    value_col = meta.get('value_col')
    relation_col = meta.get('std_relation_col')

    # Read standardized data and remove invalid smiles
    std_data = read_data(std_data_path)
    resolved_data = df_filter_invalid_smi(std_data, std_smiles_col)

    # Filter the class column if relevant
    if class_col is not None:
        filter_fn = process_filter_input(filters)
        idx_keep_dict = class_keep_indices(resolved_data,
                                           std_key_col, filter_fn)
        resolved_data = df_filter_replicates(resolved_data, idx_keep_dict)
        add_meta(meta_path, {'resolution_function': filter_fn.__name__})
        add_meta(meta_path, {'class_resolved_indices': idx_keep_dict})

    # TODO: include relation_col
    # Filter value column if relevant
    if value_col is not None:
        idx_keep_dict = value_keep_indices(resolved_data, std_key_col,
                                           relation_col, std_smiles_col,
                                           value_col, threshold)
        resolved_data = df_filter_replicates(resolved_data, idx_keep_dict)
        add_meta(meta_path, {'value_resolved_indices': idx_keep_dict})

    # Filter replicates and write data to curated data path
    resolved_data_path = write_std(resolved_data, path, prefix='resolved_')

    resolved_meta = {'resolved_data_path': resolved_data_path,
                     'resolved_rows': int(resolved_data.shape[0]),
                     'resolved_version': __version__,
                     'resolved_utc_fix': int(time.time())}

    add_meta(meta_path, resolved_meta)  # Update metadata

    print("Curated df will be written to:", resolved_data_path)
    print("Updated metadata at:", meta_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help='path to directory with data to curate')
    parser.add_argument('--threshold', '-t', type=float, default=0.01,
                        help='specify a threshold for value curation')
    args = parser.parse_args()

    resolve_class(args.path, args.threshold)
