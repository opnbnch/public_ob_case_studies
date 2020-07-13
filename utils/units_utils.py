import pandas as pd


def get_unit_values(df, unit_col):
    """
    return unique unit values for the unit_col
    :pd.DataFrame df: df of interest
    :str unit_col: name of the unit column
    """

    return list(set(df[unit_col].values))


def df_add_std_units(df, std_unit):
    """
    Add the std_unit column to a df.
    :pd.DataFrame df: The dataframe of interest
    :str std_unit: standardized unit
    """

    df = df.assign(std_units=std_unit)

    return df


def get_relationship(prompt, cur_unit, std_unit):
    """
    Gets the relationship between a different unit
    and the standard unit.
    :str prompt: prompt to ask user
    :str cur_unit: unit to standardize
    :str std_unit: unit to standardize to
    """

    while True:
        relation = input(prompt.format(cur_unit, std_unit))
        if relation == 'none':
            return relation
        try:
            val = float(relation)
            return val
        except ValueError:
            print('\tPlease enter a valid number')


def get_unit_map(df, unit_col):
    """
    Gets the user map to map non-standard units
    to the standard unit.
    :pd.DataFrame df: The dataframe of interest
    :str unit_col: column holding the units
    """

    unit_map = {}
    unit_values = get_unit_values(df, unit_col)
    unit_values = [str(x) for x in unit_values]
    num_units = len(unit_values)

    # Everything is already the same unit
    if num_units == 1:
        return unit_map, unit_values[0]

    text1 = \
        """
        You have {} different unit types. Here are the most common.
        """
    print(text1.format(num_units))
    print(pd.DataFrame(df[unit_col].value_counts()).head())

    prompt = \
        """
        Which units should be your standard units?
        """
    std_unit = input(prompt)

    if std_unit in unit_values:
        unit_values.remove(std_unit)
        unit_map[std_unit] = 1.0

    prompt = \
        """
        What is the multiplication factor to convert {} to {}?
        Enter 'none' if unit is non-standardizable.
        """
    for cur_unit in unit_values:
        mult_factor = get_relationship(prompt, cur_unit, std_unit)  # get float
        unit_map[cur_unit] = mult_factor

    return unit_map, std_unit


def df_units_to_vals(df, unit_col, value_col, unit_map):
    """
    Removes rows with non standardizable units and
    filters the non_standard units to match standard units.
    :pd.DataFrame df: The dataframe of interest
    :str unit_col: column holding the units
    :str value_col: column holding the values
    :dict unit_map: dict mapping non_standard units to
    multiplicative conversion to standard
    """
    non_std = [key for key in list(unit_map.keys()) if unit_map[key] == 'none']

    # Retain only valid standard changes
    for key in non_std:
        unit_map.pop(key, None)

    std_val_df = []

    # Remove non standardizable rows and standardize units
    for unit, factor in unit_map.items():
        group = df.loc[lambda x:x[unit_col] == unit]
        std_vals = [x * factor for x in group[value_col].to_list()]
        group = group.assign(std_values=std_vals)
        std_val_df.append(group)

    if len(std_val_df) > 1:
        std_val_df = pd.concat(std_val_df)

    return std_val_df
