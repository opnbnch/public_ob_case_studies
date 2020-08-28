import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_data, write_std
from utils.mqd_utils import get_mqd, get_kept_col
from utils.mqd_utils import fix_value_col, fix_relation_col, tripartite


def mqd(path):
    """
    :str path: a directory containing metadata and csv
    """

    # First read meta and store relevant paths into variables.
    meta = read_meta(path)
    meta_path = meta.get('meta_path')
    std_smiles_col = meta.get('std_smiles_col')
    class_col = meta.get('std_class_col')
    value_col = meta.get('std_value_col') or meta.get('value_col')
    units_col = meta.get('std_unit_col')
    relation_col = meta.get('std_relation_col')
    resolved_data_path = meta.get('resolved_data_path')

    df = read_data(resolved_data_path)

    if not class_col and not value_col:
        raise ValueError('Data must contain a value column, '
                         'class column, or both.')
    elif bool(class_col) != bool(value_col):
        kept_col = class_col if class_col in df.columns else value_col
    else:
        kept_col = get_kept_col(class_col, value_col)

    if kept_col == value_col:
        # Start by finding relevant splits
        upper_limit, lower_limit = fix_relation_col(df, relation_col,
                                                    value_col)

        if upper_limit or lower_limit:
            df, upper_df, lower_df, = tripartite(df, lower_limit,
                                                 upper_limit,
                                                 relation_col,
                                                 value_col,
                                                 units_col,
                                                 std_smiles_col)

        # Next we transform the rx dataset if desired
        df, transformation = fix_value_col(df, units_col, value_col)
        add_meta(meta_path, {'value_transformation': transformation})

        # Write out upper + lower dfs if they exist
        if upper_limit:
            upper_data_path = write_std(upper_df, path, prefix='mqd_upper_')
            add_meta(meta_path, {'mqd_upper_path': upper_data_path})
            add_meta(meta_path, {'upper_limit': upper_limit})
        if lower_limit:
            lower_data_path = write_std(lower_df, path, prefix='mqd_lower_')
            add_meta(meta_path, {'mqd_lower_path': lower_data_path})
            add_meta(meta_path, {'lower_limit': lower_limit})

    df = get_mqd(df, std_smiles_col, kept_col)

    mqd_data_path = write_std(df, path, prefix='mqd_')
    mqd_col = df.columns[1]

    # Write standardized data and store meta
    meta = {'mqd_data_path': mqd_data_path,
            'mqd_column': mqd_col,
            'std_utc_fix': int(time.time())}

    add_meta(meta_path, meta)

    # Print write paths
    print("Standard df will be written to:", mqd_data_path)
    print("Updated metadata at:", meta_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str,
                        help="path to directory with data to produce mqd")
    args = parser.parse_args()

    mqd(args.path)
