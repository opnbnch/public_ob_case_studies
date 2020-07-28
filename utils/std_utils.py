import molvs
import os
import pandas as pd
import questionary
import tqdm

from multiprocessing import pool
from rdkit import Chem

from rdkit import rdBase

import utils.meta_utils as meta_utils

rdBase.DisableLog('rdApp.error')
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


def _list_smiles_from_smiles(smi_list, single_thread=False):
    """
    Private function for multiprocessing in multi_smiles_to_smiles
    :list smi_list: Batch of smiles strings to process
    :bool single_thread: If not multiprocessing
    """
    if single_thread:
        std_smiles = []
        for smi in tqdm.tqdm(smi_list):
            std_smiles.append(_std_smiles_from_smiles(smi))

        return std_smiles
    else:
        return [_std_smiles_from_smiles(smi) for smi in smi_list]


def _list_ik_from_smiles(smi_list, single_thread=False):
    """
    Private function for multiprocessing in multi_smiles_to_ik
    :list smi_list: Batch of smiles strings to process
    :bool single_thread: If not multiprocessing
    """
    if single_thread:
        std_ik = []
        for smi in tqdm.tqdm(smi_list):
            std_ik.append(_std_ik_from_smiles(smi))

        return std_ik
    else:
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

        n_iters = len(batches)
        with pool.Pool(workers) as p:
            std_smiles = list(tqdm.tqdm(p.imap(func, batches), total=n_iters))
            std_smiles = [y for x in std_smiles for y in x]  # Flatten results
    else:
        # Process one-by-one in list comprehension
        std_smiles = func(smi_list, single_thread=True)

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

        n_iters = len(batches)
        with pool.Pool(workers) as p:
            std_ik = list(tqdm.tqdm(p.imap(func, batches), total=n_iters))
            std_ik = [y for x in std_ik for y in x]  # Flatten results
    else:
        # Process one-by-one in list comprehension
        std_ik = func(smi_list, single_thread=True)

    return std_ik


def df_add_std_smiles(df, smiles_col, workers=8):
    """
    df_add_std_smiles adds a standardized smiles column to a df
    :pd.DataFrame df: df of interest
    :str smiles_col: name of smiles column
    :int workers: number of CPUs to devote
    """

    df_smiles = list(df[smiles_col])
    print('Standardizing Smiles')
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
    print('Creating Inchi Keys')
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


def get_subset_cols(remaining, default_cols):
    """
    Get a subset of columns to keep and columns to discard by
    repeatedly prompting for user input.
    :list cols: a list of all column names strings
    :list default_cols: list of forced keep columns
    """
    cols = list(set(remaining) - set(default_cols))

    prompt = "Select columns to keep from the following."
    kept_cols = questionary.checkbox(prompt, choices=cols).ask()

    return kept_cols + default_cols, cols


def select_cols(std_df, default_cols):
    """
    Get input from the user to keep either default columns or
    their own subset of columns.
    :pd.DataFrame df: a pandas DF
    :list default_cols: list of default columns to keep
    """

    text1 = "Let's decide which columns to keep in the final dataset."
    print(text1)

    default_q = "Do you want to only keep the default columns? {}:"

    default_question = default_q.format('[' + ', '.join(default_cols) + ']')
    keep_default = questionary.confirm(default_question).ask()

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

    if optional:
        valid_cols.append('none')
    col = questionary.rawselect(prompt, choices=valid_cols).ask()

    if optional:
        valid_cols.remove('none')

    if col == 'none':
        return None

    return col


def get_smiles_col(free_cols):
    """
    Get input from the user to assign the
    smiles column.
    :list free_cols: list of unassigned df columns
    """

    text1 = "Let's select the SMILES column in the file."
    print(text1)

    prompt = "Please select the SMILES column from the list:"

    return get_valid_col(prompt, free_cols)


def get_rel_col(free_cols):
    """
    Get input from the user to discern the relation
    column if data contains values.
    :list free_cols: list of unassigned df columns
    """

    prompt = "Please select the relationship column from the list." \
        " Select 'none' if there is not a relationship column."

    rel_col = get_valid_col(prompt, free_cols, True)

    if rel_col:
        free_cols.remove(rel_col)
    return rel_col


def remove_nan(col, df):
    """
    Replace nan values with None in a df column
    :str col: column to replace values
    :pd.DataFrame df: The dataframe of interest
    """
    cur_col = df[col]
    new_col = cur_col.where(pd.notnull(cur_col), None)
    df[col] = new_col
    return df


def get_col_types(free_cols, df):
    """
    Get input from the user to discern the data type
    and the name of the data column.
    :list free_cols: list of unassigned df columns
    :pd.DataFrame df: The dataframe of interest
    """

    text1 = "Which column(s) store our classes or values?"
    print(text1)

    class_prompt = "Please select the class column from the list." \
        " Select 'none' if there is not a class column."

    class_col = get_valid_col(class_prompt, free_cols, optional=True)

    if class_col is not None:
        free_cols.remove(class_col)
        df = remove_nan(class_col, df)

    value_prompt = "Please select the value column from the list." \
        " Select 'none' if there is not a value column."

    value_col = get_valid_col(value_prompt, free_cols, optional=True)

    if value_col is not None:
        free_cols.remove(value_col)
        df = remove_nan(value_col, df)
    return class_col, value_col, df


def get_unit_col(df, free_cols):
    """
    Get input from the user to get unit_col.
    If there is no unit_col ask for creation.
    :pd.DataFrame df: The dataframe of interest
    :list free_cols: list of unassigned df columns
    """

    text1 = "Is there a column storing unit values in the file?"
    print(text1)

    prompt = "Please select the unit column from the list." \
        " Select 'none' if there is not a unit column."

    unit_col = get_valid_col(prompt, free_cols, optional=True)

    if unit_col is None:
        prompt = "Would you like to create a unit column?"
        create_unit = questionary.confirm(prompt).ask()
        if create_unit:
            unit_col = 'unit_col'
            prompt = "What units should be assigned to this data?"
            unit_type = questionary.text(prompt).ask()
            df = df_add_units(df, unit_col, unit_type)
        else:
            return None, df
    else:
        free_cols.remove(unit_col)

    return unit_col, df


def df_add_units(df, unit_col, unit_type):
    """
    Add a unit column to a df.
    :pd.DataFrame df: The dataframe of interest
    :str unit_col: unit column in DF
    :str unit_type: type of units in column
    """

    df = df.assign(unit_col=unit_type)

    return df


def map_compliance(map, key):
    """
    Converts all map keys to type str to comply with
    adding meta_data
    :dict map: dict of keys: values
    """

    inner_map = map[key]

    n_map = {str(k): v for k, v in inner_map.items()}

    f_map = dict()
    key = str(key)
    f_map[key] = n_map

    return f_map


def df_add_value(df, value_col):
    """
    Add the value column to a df.
    :pd.DataFrame df: The dataframe of interest
    :str value_col: value column in DF
    """

    df.loc[::, 'value_col'] = df[value_col]

    return df
