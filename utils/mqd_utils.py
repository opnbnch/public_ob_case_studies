import questionary
import numpy as np


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


def get_value_transform():
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


def transform_value(df, transform, value_col):
    """
    Perform a transformation on the value column of a df
    :pd.DataFrame df: a pandas DF
    :str transform: transformation to perform
    :str value_col: value column of df
    """
    if transform == 'log transform':
        df[value_col] = np.log10(df[value_col])

    elif transform == 'pIC50 transform':
        pass

    return df
