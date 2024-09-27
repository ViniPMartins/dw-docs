from .db import engine
from sqlalchemy import inspect
from pandas import DataFrame, read_sql_table

def update_table(table, dataframe: DataFrame):
    dataframe.to_sql(table, engine, if_exists='replace')

def tables():
    inspector = inspect(engine)
    return inspector.get_table_names()

def fetch_data_from(table):
    return read_sql_table(table, engine, index_col='FIELDNAME')