import yaml
import pandas as pd
import os

def define_env(env):
    @env.macro
    def table_columns(yaml_file):
        abs_path = os.path.abspath(yaml_file)
        table = os.path.basename(yaml_file).split(".")[0]
        if not os.path.exists(abs_path):
            return f"Arquivo {abs_path} não encontrado."

        with open(abs_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        if not data:
            return "No data found."

        data_columns = data[table]['colunas']
        headers = data_columns[0].keys()
        table = []

        table.append('| ' + ' | '.join(headers) + ' |')
        table.append('|' + '---|' * len(headers))

        for row in data_columns:
            table.append('| ' + ' | '.join(str(row[h]) for h in headers) + ' |')

        return '\n'.join(table)
    
    @env.macro
    def example(file_path):
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return f"Arquivo {abs_path} não encontrado."

        df_table = pd.read_csv(abs_path, sep=';', encoding='utf-8', decimal=',', thousands='.').fillna('').head(10)
        table_md = df_table.to_markdown(index=False)

        return table_md