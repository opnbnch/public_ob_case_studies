
def get_mqd(df, smiles_col, col2):
    """
    For a given df, get the columns you want in the order you want them
    :pd.DataFrame df: a pandas DF
    :str smile_col: smiles column in df
    :str col2: value or class column
    """

    subset = [smiles_col, col2]

    return df.loc[::, subset]
