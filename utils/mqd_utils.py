import questionary
import numpy as np

from utils.units_utils import get_unit_map, df_units_to_vals


def get_mqd(df, smiles_col, col2):
    """
    For a given df, get the columns you want in the order you want them
    :pd.DataFrame df: a pandas DF
    :str smiles_col: smiles column in df
    :str col2: value or class column
    """

    subset = [smiles_col, col2]

    return df.loc[::, subset]


def get_kept_col(class_col, value_col):
    """
    Prompt the user to select either class or value column for final MQD
    :str class_col: Class column in df
    :str value_col: Value column in df
    """
    print('You have both a class and a value column. We can only keep one.')

    prompt = 'Please select a column to keep.'
    options = [class_col, value_col]
    return questionary.select(prompt, options).ask()


def _get_value_transform():
    """
    Prompt the user on getting a transformation for the value column data
    """
    p1 = 'Would you like to perform a tranformation on your value data?'
    p2 = 'Choose a transformation method:'

    options = ['log transform', 'pIC50 transform']
    to_transform = questionary.confirm(p1).ask()

    if to_transform:
        return questionary.select(p2, options).ask()
    else:
        return False


def _transform_value(df, transform, value_col):
    """
    Perform a transformation on the value column of a df
    :pd.DataFrame df: a pandas DF
    :str transform: transformation to perform
    :str value_col: value column of df
    """
    if transform == 'log transform':
        df[value_col] = np.log10(df[value_col])

    elif transform == 'pIC50 transform':
        df[value_col] = -1 * np.log10(df[value_col])

    return df


def _get_N_sig_figs(df, value_col, num_figs):
    """
    Returns a value_col cut to the proper number of sig_figs
    :pd.DataFrame df: a pandas DF
    :str value_col: value column in df
    :int num_figs: number of sig figs to use
    """
    N = '%.' + str(num_figs) + 'g'

    cut = ['%s' % float(N % x) for x in df[value_col]]
    return [float(x) for x in cut]


def fix_value_col(df, units_col, value_col, relation_col):
    """
    Optionally transform and handle a relation column in the df
    :pd.DataFrame df: a pandas DF
    :str units_col: units column in df
    :str value_col: value column in df
    :str relation_col: relation column in df
    """
    transform = _get_value_transform()

    if transform:
        if transform == 'pIC50 transform':
            print('All units must be of type M.')
            unit_map, std_unit = get_unit_map(df, units_col, forced_unit='M')
            df = df_units_to_vals(df, units_col, value_col, unit_map)
        df = _transform_value(df, transform, value_col)

    df[value_col] = _get_N_sig_figs(df, value_col, num_figs=5)

    # TODO: Handle relations

    return df, transform
