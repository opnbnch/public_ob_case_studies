def get_unique_values(df, df_col):
    """
    return unique values for the df_col
    :pd.DataFrame df: df of interest
    :str df_col: name of the df column
    """

    return list(set(df[df_col].values))


def standardize_op(invalid_op, valid_ops):
    """
    ask the user for an assignment to the operpator in question
    :str invalid_op: The operator that needs to be assigned
    :list valid_ops: list of options for assignment
    """
    op_list = '[' + ', '.join(valid_ops) + ']'
    assign = input('Assign {} to one of the following values: {}:'.format
                   (invalid_op, op_list))
    while assign not in valid_ops:
        assign = input('Assign {} to one of the following values: {}:'.format
                       (invalid_op, op_list))
    return assign


def get_relation_map(df, relation_col):
    """
    Assign non-standard relation values to
    a standard relation value.
    :pd.DataFrame df: df with class to map
    :str relation_col: name of column containing relations
    """

    relation_map = {}
    valid_relations = ['<', '>', '>=', '<=', '=', '==']

    relation_vals = get_unique_values(df, relation_col)

    warned = False
    warning = \
        """
        There are invalid relationship operators in your
        relation column. Let\'s standardize them.
        """
    for op in relation_vals:
        if op not in list(relation_map.keys()) + valid_relations:
            if not warned:
                print(warning)
                warned = True
            assign = standardize_op(op, valid_relations)
            relation_map[op] = assign

    return relation_map


def df_add_std_relation(df, relation_map, relation_col):
    """
    df_add_std_relation adds standardized relations to a df
    :pd.DataFrame df: df of interest
    :dict relation_map: mapping of old relations to new
    """

    std_df = df \
        .replace(to_replace=relation_map) \
        .rename(columns={relation_col: 'std_relation'})

    std_df[relation_col] = df[relation_col]

    return std_df
