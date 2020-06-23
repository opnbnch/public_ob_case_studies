import molvs
import os
import pandas as pd

from functools import partial
from multiprocessing import pool
from rdkit import Chem

import utils.meta_utils as meta_utils

__version__ = 'v1.0.0 (06-18-2020)'


def read_data(path):
    """
    read_data reads the relevant columns from a dataframe given the path
    :str path: path to dir where data lives
    """

    meta = meta_utils.read_meta(path)

    data_path = os.path.join(path, os.path.basename(meta.get('data_path')))

    smiles_col = meta.get('smiles_col')
    class_col = meta.get('class_col')
    value_col = meta.get('value_col')
    column_subset = [col for col in [smiles_col, class_col, value_col] if col]

    # subset to columns of interest
    df = pd.read_csv(data_path).loc[::, column_subset]

    return(df)

def read_std_data(path):
    """
    Read the relevant columns from a dataframe given the path
    :str path: path to dir where data lives
    """

    meta = meta_utils.read_meta(path)
    data_path = os.path.join(path, os.path.basename(meta.get('std_data_path')))
    df = pd.read_csv(data_path)

    return(df)

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


def std_smiles_from_smiles(smiles):
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


def std_ik_from_smiles(smiles):
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
    return [std_smiles_from_smiles(smi) for smi in smi_list]


def _list_ik_from_smiles(smi_list):
    """
    Private function for multiprocessing in multi_smiles_to_ik
    """
    return [std_ik_from_smiles(smi) for smi in smi_list]


def multi_smiles_to_smiles(smi_list, workers=8):
    """
    Parallelize smiles standardization on CPU
    :list smi_list: list of SMILES strings
    :int workers: number of cores to devote to job
    """

    func = partial(_list_smiles_from_smiles)

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
        std_smiles = _list_smiles_from_smiles(smi_list)

    return std_smiles


def multi_ik_from_smiles(smi_list, workers=8):
    """
    Parallelize inchi key generation on CPU
    :list smi_list: list of SMILES strings
    :int workers: number of cores to devote to job
    """

    func = partial(_list_ik_from_smiles)

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
        std_ik = _list_ik_from_smiles(smi_list)

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


def write_std(df, outpath, prefix='std_'):
    """
    write_std writes a standardized csv at a specified path
    :pd.DataFrame df: The dataframe to write
    :str outpath: path to output directory
    :str filename: specific filename to write to
    """

    # Compose filename from meta_dict
    meta = meta_utils.read_meta(outpath)
    old_name = os.path.basename(meta.get('data_path'))
    filename = prefix + old_name

    if not os.path.isdir(outpath):
        os.makedirs(outpath)

    fullpath = os.path.join(outpath, filename)

    df.to_csv(fullpath, index=False)

    return fullpath
