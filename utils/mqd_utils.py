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
    length = len(set(df[relation_col]))
    if as_perc:
        print('The {} most common relations by percentage (%):'.format(length))
        print(np.round(value_counts/df.shape[0]*100, 2))
    else:
        print('The {} most common relations by count (N):'.format(length))
        print(value_counts)


def _top_relation_vals(df, relation_col, value_col, relations):

    info = 'Here are the most common values for {} relations:'
    print(info.format(relations))

    ge_df = df \
        .loc[lambda x:x[relation_col].isin(relations)]
    print(ge_df[value_col].value_counts().head(10))


def _get_relation_limits(df, relation_col, value_col, unique_relations):
    """
    Prompts user to split dataset based upon relations or to keep it as is.
    :pd.DataFrame df: a pandas DF
    :str relation_col: relation column in df
    :str value_col: value column in df
    :lost unique_relations: list of relations in relation_col
    """

    upper_relations = ['>', '>=']
    lower_relations = ['<', '<=']

    info = "\nWe recommend limiting rx datasets to only the '=' relation."
    print(info)
    _relation_display(df, relation_col)

    initial_prompt = 'Do you want to subset your data based upon relation?'
    to_change = questionary.confirm(initial_prompt).ask()

    if not to_change:
        return False, False
    else:
        # get upper limit if upper relations are in data
        if any(item in upper_relations for item in unique_relations):
            to_upper = 'Do you want to create an upper limit classifier?'
            to_create_upper = questionary.confirm(to_upper).ask()
            if to_create_upper:
                _top_relation_vals(df, relation_col, value_col,
                                   upper_relations)

                upper_limit = questionary.text('Input the upper limit').ask()
                try:
                    upper_limit = float(upper_limit)
                except ValueError:
                    raise ValueError('Upper limit must be a number')
            else:
                upper_limit = False

        # get lower limit if lower relations are in data
        if any(item in lower_relations for item in unique_relations):
            to_lower = 'Do you want to create a lower limit classifier?'
            to_create_lower = questionary.confirm(to_lower).ask()
            if to_create_lower:
                _top_relation_vals(df, relation_col, value_col,
                                   lower_relations)
                lower_limit = questionary.text('Input the lower limit').ask()
                try:
                    lower_limit = float(lower_limit)
                except ValueError:
                    raise ValueError('Lower limit must be a number')
            else:
                lower_limit = False

        return upper_limit, lower_limit


def tripartite(df, lower_limit, upper_limit, relation_col, value_col,
               units_col, smiles_col, truncate_reg=False):
    """
    Splits the data into 3 datasets depending upon upper and lower limits.
    :pd.DataFrame df: a pandas DF
    :float lower_limit: lower limit to filter
    :float upper_limit: upper limit to filter
    :str relation_col: relation column in df
    :str value_col: value column in df
    :str units_col: units column in df
    :smiles_col: smiles column in df
    """

    # Regrssion dataframe
    regression_df = df.loc[lambda x:x[relation_col] == '='] \
        .loc[::, [smiles_col, value_col, units_col]]
    if truncate_reg:
        regression_df = regression_df \
            .loc[lambda x:x[value_col].between(lower_limit/100.,
                                               upper_limit * 10)]

    # Upper Limit df
    if upper_limit:
        upper_class_df = df.loc[lambda x: ~((x[value_col] < upper_limit) &
                                (x[relation_col].isin(['>', '>='])))]
        is_active = ((upper_class_df[value_col].values >= upper_limit) &
                     (upper_class_df[relation_col] != '<'))
        upper_class_df = upper_class_df.assign(
            active=[int(a) for a in is_active])
        upper_class_df = upper_class_df \
            .loc[::, [smiles_col, 'active']]
    else:
        upper_class_df = None

    # Lower class df
    if lower_limit:
        lower_class_df = df.loc[lambda x: ~((x[value_col] > lower_limit) &
                                (x[relation_col].isin(['<', '<='])))]
        is_active = ((lower_class_df[value_col].values <= lower_limit) &
                     (lower_class_df[relation_col] != '>'))
        lower_class_df = lower_class_df.assign(
            active=[int(a) for a in is_active])
        lower_class_df = lower_class_df \
            .loc[::, [smiles_col, 'active']]
    else:
        lower_class_df = None

    return regression_df, upper_class_df, lower_class_df


def fix_value_col(df, units_col, value_col):
    """
    Optionally transform and handle a relation column in the df
    :pd.DataFrame df: a pandas DF
    :str units_col: units column in df
    :str value_col: value column in df
    """

    transform = _get_value_transform()

    if transform:
        if transform == 'pIC50 transform':
            print('All units must be of type M.')
            unit_map, std_unit = get_unit_map(df, units_col, forced_unit='M')
            df = df_units_to_vals(df, units_col, value_col, unit_map)
        df = _transform_value(df, transform, value_col)

    df[value_col] = _get_N_sig_figs(df, value_col, num_figs=3)

    return df, transform


def fix_relation_col(df, relation_col, value_col):
    """
    Optionally fixes the relation column by splitting into multiple groups
    defined by upper and lower limits.
    :pd.DataFrame df: a pandas DF
    :str relation_col: relation column in df
    :str value_col: value column in df
    """

    unique_relations = list(set(df[relation_col]))

    # Nothing to change if all relations are '='
    if len(unique_relations) == 1 and unique_relations[0] == '=':
        return None, None

    return _get_relation_limits(df, relation_col, value_col, unique_relations)
