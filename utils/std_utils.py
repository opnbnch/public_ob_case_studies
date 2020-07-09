import molvs
import os
import pandas as pd

from multiprocessing import pool
from rdkit import Chem

import utils.meta_utils as meta_utils

__version__ = 'v1.0.0 (07-01-2020)'


def read_data(data_path):
    """
    read_data reads the relevant columns from a dataframe given the path
    :str path: path to data
    """
    return pd.read_csv(data_path)


def std_mol_from_smiles(smiles):
    """
    Adapted from:
    github.com/ATOMconsortium/AMPL/blob/master/atomsci/ddm/utils/struct_utils.py
    Following some rules set out here: https://doi.org/10.1021/ci100176x
    Generate a standardized RDKit Mol object for the larges fragment
    of the molecule specified by smiles.
    :str smiles: SMILES formatted string
    """

    cmpd_mol = Chem.MolFromSmiles(smiles)

    if cmpd_mol is None:
        return None
    else:
        stdizer = molvs.standardize.Standardizer(prefer_organic=True)
        return stdizer.fragment_parent(cmpd_mol)


def _std_smiles_from_smiles(smiles):
    """
    Adapted from:
    github.com/ATOMconsortium/AMPL/blob/master/atomsci/ddm/utils/struct_utils.py
    Generate a standardized SMILES string for the largest fragment
    of the molecule specified by smiles.
    :str smiles: SMILES formatted string
    """

    try:
        std_mol = std_mol_from_smiles(smiles)
        return Chem.MolToSmiles(std_mol)
    except Exception:
        return 'invalid_smiles'


def _std_ik_from_smiles(smiles):
    """
    Generate a standardized inchi key for a given molecule specified by smiles
    :str smiles: SMILES formatted string
    """

    try:
        std_mol = std_mol_from_smiles(smiles)
        return Chem.inchi.MolToInchiKey(std_mol)
    except Exception:
        return "invalid_smiles"


def _list_smiles_from_smiles(smi_list):
    """
    Private function for multiprocessing in multi_smiles_to_smiles
    """
    return [_std_smiles_from_smiles(smi) for smi in smi_list]


def _list_ik_from_smiles(smi_list):
    """
    Private function for multiprocessing in multi_smiles_to_ik
    """
    return [_std_ik_from_smiles(smi) for smi in smi_list]


def multi_smiles_to_smiles(smi_list, workers=8):
    """
    Parallelize smiles standardization on CPU
    Concept adapted from Atom AMPL: https://github.com/ATOMconsortium/AMPL/
    :list smi_list: list of SMILES strings
    :int workers: number of cores to devote to job
    """

    func = _list_smiles_from_smiles

    if workers > 1:
        # Multi-process if you have workers for it.
        batchsize = 200
        batches = [smi_list[i:i+batchsize]
                   for i in range(0, len(smi_list), batchsize)]

        with pool.Pool(workers) as p:
            std_smiles = p.map(func, batches)
            std_smiles = [y for x in std_smiles for y in x]  # Flatten results
    else:
        # Process one-by-one in list comprehension
        std_smiles = func(smi_list)

    return std_smiles


def multi_ik_from_smiles(smi_list, workers=8):
    """
    Parallelize inchi key generation on CPU
    :list smi_list: list of SMILES strings
    :int workers: number of cores to devote to job
    """

    func = _list_ik_from_smiles

    if workers > 1:
        # Multi-process if you have workers for it.
        batchsize = 200
        batches = [smi_list[i:i+batchsize]
                   for i in range(0, len(smi_list), batchsize)]

        with pool.Pool(workers) as p:
            std_ik = p.map(func, batches)
            std_ik = [y for x in std_ik for y in x]  # Flatten results
    else:
        # Process one-by-one in list comprehension
        std_ik = func(smi_list)

    return std_ik


def df_add_std_smiles(df, smiles_col, workers=8):
    """
    df_add_std_smiles adds a standardized smiles column to a df
    :pd.DataFrame df: df of interest
    :str smiles_col: name of smiles column
    :int workers: number of CPUs to devote
    """

    df_smiles = list(df[smiles_col])
    df['std_smiles'] = multi_smiles_to_smiles(df_smiles, workers)

    return df


def df_add_ik(df, smiles_col, workers=8):
    """
    df_add_ik adds an inchi key column to a df
    :pd.DataFrame df: df of interest
    :str smiles_col: name of smiles column
    :int workers: number of CPUs to devote
    """

    df_smiles = list(df[smiles_col])
    df['inchi_key'] = multi_ik_from_smiles(df_smiles, workers)

    return df


def get_invalid_smiles(df, base_smiles_col, std_smiles_col):
    """
    Return invalid smiles indices for a given data frame
    :pd.DataFrame df:
    :str base_smiles_col: name for base smiles column
    :str std_smiles_col: name for std smiles column
    """

    invalids = df.loc[lambda x:x[std_smiles_col] == 'invalid_smiles']

    invalid_dict = {}
    for row in invalids.iterrows():
        invalid_dict.update({row[1][base_smiles_col]: row[0]})

    return invalid_dict


def write_std(df, path, prefix='std_'):
    """
    write_std writes a standardized csv at a specified path
    :pd.DataFrame df: The dataframe to write
    :str outpath: path to output directory
    :str filename: specific filename to write to
    """

    # Compose filename from prefix and data path
    meta = meta_utils.read_meta(path)

    outpath = os.path.dirname(meta.get('data_path'))
    old_name = os.path.basename(meta.get('data_path'))
    filename = prefix + old_name

    if not os.path.isdir(outpath):
        os.makedirs(outpath)

    fullpath = os.path.join(outpath, filename)

    df.to_csv(fullpath, index=False)

    return fullpath


def subset_data(df, subset_cols):
    """
    For a given dataset, get the columns you want in the order you want them
    :pd.DataFrame df: a pandas DF
    :list subset_cols: a list of column names strings
    """

    subset = [x for x in subset_cols if x in df.columns]

    return df.loc[::, subset]


def get_yes_no(prompt):
    """
    Turn a user input into a yes/no mapped respectively to True/False
    :str prompt: question to prompt the user with
    """

    acc = ['yes', 'y', 'true', 'accept', 't', '1']
    rej = ['no', 'n', 'false', 'reject', 'f', '0']

    ans = input(prompt)
    while ans.lower() not in acc + rej:
        print('\tNot a valid response. Please enter yes or no.')
        ans = input(prompt)
    if ans in acc:
        return True
    return False


def get_subset_cols(remaining, default_cols):
    """
    Get a subset of columns to keep and columns to discard by
    repeatedly prompting for user input.
    :list cols: a list of all column names strings
    :list default_cols: list of forced keep columns
    """
    cols = list(set(remaining) - set(default_cols))
    all_cols = remaining.copy()
    kept_cols = []

    prompt = \
        """
        Type columns (space-separated) to keep from the following.
        Enter "all" to keep all. Enter "done" to stop.
        \n\t{}:
        """
    ans = input(prompt.format('[' + ', '.join(cols) + ']'))
    while len(cols) > 0 and ans.lower() != 'done' and ans.lower() != 'all':
        ans_list = ans.split()
        valid = [cur for cur in ans_list if cur in cols]
        for cur in valid:
            kept_cols.append(cur)
            cols.remove(cur)
        ans = input(prompt.format('[' + ', '.join(cols) + ']'))

    if ans == 'all':
        return all_cols, []
    return kept_cols + default_cols, cols


def select_cols(std_df, default_cols):
    """
    Get input from the user to keep either default columns or
    their own subset of columns.
    :pd.DataFrame df: a pandas DF
    :list default_cols: list of default columns to keep
    """

    text1 = \
        """
        Let's decide which columns to keep in the final dataset.
        """
    print(text1)

    default_q = \
        """
        Do you want to only keep the default columns? {}:
        """
    default_question = default_q.format('[' + ', '.join(default_cols) + ']')
    keep_default = get_yes_no(default_question)

    if keep_default:
        return default_cols, list(set(std_df.columns) - set(default_cols))
    else:
        all_cols = list(std_df.columns)
        return get_subset_cols(all_cols, default_cols)


def get_valid_col(prompt, valid_cols, optional=False):
    """
    General helper function to get a single value
    from a list of values.
    :str prompt: Prompt to give to the user
    :list valid_cols: columns the user can choose from
    :bool optional: If selection is optional
    """

    col = input(prompt.format('[' + ', '.join(valid_cols) + ']'))
    while col not in valid_cols:
        if optional and col == 'none':
            return None
        print('\tEnter a valid column name.')
        col = input(prompt.format('[' + ', '.join(valid_cols) + ']'))
    return col


def get_smiles_col(free_cols):
    """
    Get input from the user to assign the
    smiles column.
    :list free_cols: list of unassigned df columns
    """

    text1 = \
        """
        Let's select the SMILES column in the file.
        """
    print(text1)

    prompt = \
        """
        Please select the SMILES column from the list: {}:
        """
    return get_valid_col(prompt, free_cols)


def get_rel_col(free_cols):
    """
    Get input from the user to discern the relation
    column if data contains values.
    :list free_cols: list of unassigned df columns
    """

    prompt = \
        """
        Please select the relationship column from the list: {}:
        Enter "none" if there is not a relationship column.
        """

    rel_col = get_valid_col(prompt, free_cols, True)

    if rel_col:
        free_cols.remove(rel_col)
    return rel_col


def get_col_types(free_cols):
    """
    Get input from the user to discern the data type
    and the name of the data column.
    :list free_cols: list of unassigned df columns
    """

    text1 = \
        """
        Which column(s) store our classes or values?
        """
    print(text1)

    prompt = \
        """
        Please select the class column from the list: {}:
        Enter "none" if there is not a class column.
        """
    class_col = get_valid_col(prompt, free_cols, True)

    if class_col is not None:
        free_cols.remove(class_col)

    prompt = \
        """
        Please select the value column from the list: {}:
        Enter "none" if there is not a value column.
        """
    value_col = get_valid_col(prompt, free_cols, True)

    if value_col is not None:
        free_cols.remove(value_col)
    return class_col, value_col


def get_unit_col(df, free_cols):
    """
    Get input from the user to get unit_col.
    If there is no unit_col ask for creation.
    :pd.DataFrame df: The dataframe of interest
    :list free_cols: list of unassigned df columns
    """

    created = False
    text1 = \
        """
        Is there a column storing unit values in the file?
        """
    print(text1)

    prompt = \
        """
        Please select the unit column from the list: {}:
        Enter "none" if there is not a unit column.
        """
    unit_col = get_valid_col(prompt, free_cols, True)

    if unit_col is None:
        prompt = \
            """
            Would you like to create a unit column? [y/n]
            """
        create_unit = get_yes_no(prompt)
        if create_unit:
            unit_col = 'unit_col'
            unit_type = input('\tWhat is the unit type of the data?')
            df = df_add_units(df, unit_col, unit_type)
            created = True
        else:
            return None
    else:
        free_cols.remove(unit_col)
    return unit_col, df, created


def df_add_units(df, unit_col, unit_type):
    """
    Add a unit column to a df.
    :pd.DataFrame df: The dataframe of interest
    :str unit_col: unit column in DF
    :str unit_type: type of units in column
    """

    df[unit_col] = unit_type

    return df


def df_add_value(df, value_col):
    """
    Add the value column to a df.
    :pd.DataFrame df: The dataframe of interest
    :str value_col: value column in DF
    """

    df['value_col'] = df[value_col]

    return df
