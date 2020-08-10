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


def _relation_display(df, relation_col, as_perc=True):
    """
    Displays the most common relations from the relation column.
    :pd.DataFrame df: a pandas DF
    :str relation_col: relation column in df
    :bool as_perc: display as percentage instead of raw count
    """
    value_counts = df[relation_col].value_counts()
    length = len(set(value_counts))
    if as_perc:
        print('The {} most common relations by percentage (%):'.format(length))
        print(np.round(value_counts/df.shape[0]*100, 2))
    else:
        print('The {} most common relations by count (N):'.format(length))
        print(value_counts)


def _get_relations_choice(df, relation_col, unique_relations):
    """
    Prompts user to split dataset based upon relations or to keep it as is.
    :pd.DataFrame df: a pandas DF
    :str relation_col: relation column in df
    :lost unique_relations: list of relations in relation_col
    """
    info = "We recommend limiting rx datasets to only using the '=' relation."
    print(info)
    _relation_display(df, relation_col)

    initial_prompt = 'Do you want to subset your data based upon relation?'
    to_change = questionary.confirm(initial_prompt).ask()

    if not to_change:
        return False
    else:
        # get upper if it exists
        upper_prompt = 'Do you want to create an upper limit classifier?'


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

    df[value_col] = _get_N_sig_figs(df, value_col, num_figs=3)

    upper_relations = ['>', '>=']
    lower_relations = ['<', '<=']

    unique_relations = list(set(df[relation_col]))

    # Nothing to change if all relations are '='
    if len(unique_relations == 1) and unique_relations[0] == '=':
        return df, transform

    relations = _get_relations_choice(df, relation_col, unique_relations)

    return df, transform
