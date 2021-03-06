import argparse
import time

from utils.meta_utils import read_meta, add_meta
from utils.std_utils import read_data, write_std, __version__
from utils.std_utils import df_add_ik, df_add_std_smiles, get_invalid_smiles
from utils.class_utils import get_class_map, df_add_std_class
from utils.std_utils import select_cols, subset_data, df_add_value
from utils.std_utils import get_col_types, get_smiles_col, get_rel_col
from utils.relation_utils import get_relation_map, df_add_std_relation
from utils.std_utils import get_unit_col, map_compliance
from utils.units_utils import get_unit_map, df_add_std_units
from utils.units_utils import df_units_to_vals


def standardize(path):
    """
    :str path: a directory containing metadata and data to be standardized
    """

    # First read meta and store relevant paths into variables.
    meta = read_meta(path)
    meta_path = meta.get('meta_path')
    data_path = meta.get('data_path')

    df = read_data(data_path)  # Now read in the raw data ...
    free_cols = list(df.columns)

    # Add the smiles col into the meta for later use ...
    smiles_col = get_smiles_col(free_cols)
    free_cols.remove(smiles_col)

    add_meta(meta_path, {'smiles_col': smiles_col})

    # Get column names
    class_col, value_col, df = get_col_types(free_cols, df)

    std_df = df_add_std_smiles(df, smiles_col)  # Add standardized SMILES ...
    std_df = df_add_ik(std_df, 'std_smiles')  # And InChI keys
    default_cols = ['std_smiles']  # Initialize default columns to keep

    invalids = get_invalid_smiles(df, smiles_col, 'std_smiles')

    # If a class col is specified,
    if class_col:

        # Ask the user for a mapping from their class to integers
        class_map = get_class_map(std_df, class_col)
        std_df = df_add_std_class(std_df, class_map)

        # Keys can only be str, int, float, bool, or None
        # Enforce keys are str for writing to meta_data only
        compliant_class_map = map_compliance(class_map, class_col)
        # Store and write class meta
        class_meta = {'class_map': compliant_class_map,
                      'class_col': class_col,
                      'std_class_col': 'std_class'}

        add_meta(meta_path, class_meta)
        default_cols.append('std_class')

    if value_col:

        relation_col = get_rel_col(free_cols)
        if relation_col:

            # Get user mapping for relation operators
            relation_map = get_relation_map(std_df, relation_col)
            std_df = df_add_std_relation(std_df, relation_map, relation_col)

            # Store relation meta
            relation_meta = {'relation_map': relation_map,
                             'relation_col': relation_col,
                             'std_relation_col': 'std_relation'}

        else:
            std_df = std_df.assign(std_relation='=')
            relation_meta = {'std_relation_col': 'std_relation'}

        # Write relation meta
        add_meta(meta_path, relation_meta)
        default_cols.append('std_relation')

        # Get unit column
        unit_col, std_df = get_unit_col(std_df, free_cols)
        if unit_col:
            unit_map, std_unit = get_unit_map(std_df, unit_col)
            std_df = df_add_std_units(std_df, std_unit)
            std_df = df_units_to_vals(std_df, unit_col, value_col, unit_map)
            unit_meta = {'unit_map': unit_map,
                         'std_unit': std_unit,
                         'unit_col': unit_col,
                         'std_unit_col': 'std_units',
                         'std_value_col': 'std_values'}
            add_meta(meta_path, unit_meta)
            default_cols.append('std_units')
            default_cols.append('std_values')
        else:
            std_df = df_add_value(std_df, value_col)
            add_meta(meta_path, {'value_col': value_col})
            default_cols.append(value_col)

    std_meta = {'std_smiles_col': 'std_smiles',
                'std_key_col': 'inchi_key',
                'invalid_smiles': invalids}

    default_cols.append('inchi_key')
    add_meta(meta_path, std_meta)

    # List of columns to retain for final csv
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
    args = parser.parse_args()

    standardize(args.path)
