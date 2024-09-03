import pandas as pd
import unicodedata
import re
import os
import yaml
import sys
from loguru import logger

def verifica_duplicado(df, input_string, nova_coluna: bool = False):
    string_normalizada = normalize_string(input_string)
    results = len(df[df['SCRTEXT_M'] == string_normalizada])

    quantidade_a_verificar = 0 if nova_coluna else 1

    if results > quantidade_a_verificar:
        return True
    else:
        return False

def normalize_string(input_string):
    normalized_string = ''.join(
        c for c in unicodedata.normalize('NFKD', input_string)
        if unicodedata.category(c) != 'Mn'
    )
    normalized_string = normalized_string.upper()
    normalized_string = normalized_string.replace(' ', '_')
    normalized_string = re.sub(r'[^A-Z0-9_]', '', normalized_string)
    return normalized_string

def obter_infos_tabelas():
    return pd.read_excel('Seleção Colunas.xlsx', sheet_name='field_names')

def seleciona_tabela(tabela):
    df = obter_infos_tabelas()
    return df[(df['TABNAME'] == tabela) & (df['Selecionado'])].reset_index(drop=True)


def cria_query_sql(tabela, df_campos_tabela):
    columns = []
    query = 'SELECT\n'
    ref_tabela = tabela[0].lower()

    for key, value in df_campos_tabela.iterrows():
        col = ref_tabela + '.' + value['FIELDNAME'] + ' AS ' + value['SCRTEXT_M']
        columns.append(col)

    query += ',\n'.join(columns)
    query += f'\nFROM SAPHANADB.{tabela} AS {ref_tabela}'
    return query

def criar_estrutura_yaml(tabela, df_campos_tabela, nome_bi, sis_origem):
    columns = []
    
    for _, row in df_campos_tabela.iterrows():
        column = {
            'coluna':row['SCRTEXT_M'],
            'coluna_sistema_origem': row['FIELDNAME'],
            'tipo': '',
            'descricao': row['DDTEXT'],
            'filtros': ''
        }
        columns.append(column)

    yaml_structure = {nome_bi: {
        "nome_tabela_bi": nome_bi,
        "sistema_origem": sis_origem,
        "tabela_origem": tabela,
        "colunas" : columns
    }}

    return yaml_structure

def escrever_query(query, nome_query):
    pasta_destino = './querys'
    
    if not os.path.exists(pasta_destino):
        os.mkdir(pasta_destino)
    
    with open(f'{pasta_destino}/{nome_query}.sql', 'w') as f:
        f.write(query)

    logger.info(f"Query da tabela {nome_query} salvo em {pasta_destino}!")
        
def escrever_yaml(yaml_file, tabela):
    pasta_destino = './yaml'
    
    if not os.path.exists(pasta_destino):
        os.mkdir(pasta_destino)
    
    with open(f'{pasta_destino}/{tabela}.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(yaml_file, file, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"Arquivo yaml da tabela {tabela} salvo em {pasta_destino}!")


def salvar_exemplo(tabela, yaml_data, nome_descritivo):
    new_name_cols = pd.DataFrame(yaml_data[nome_descritivo]['colunas'])
    columns = list(new_name_cols['coluna_sistema_origem'])
    path_csv = f'csv\originais\{tabela}.csv'
    df_original = pd.read_csv(path_csv, sep=';', header=0, usecols=columns)

    map_rename = {}
    for col in columns:
        new_column_name = new_name_cols.query(f"coluna_sistema_origem=='{col}'")['coluna'].values[0]
        map_rename[col] = new_column_name

    pasta_destino = 'csv/examples/'
    df_renamed = df_original.rename(columns=map_rename).head(10)
    df_renamed.to_csv(f'{pasta_destino}{nome_descritivo}.csv', index=False, sep=';', decimal=',')

    logger.info(f"Exemplo de dados {nome_descritivo} salvo em {pasta_destino}!")

def escrever_pagina_documentacao(tabela, sistema_origem, nome_descritivo):
    markdown_template = '''\
## Nome tabela
`{nome_descritivo}`

## Descrição
Descrição tabela

## Informações Origem
> ### **Sistema**
{indent}{sistema_origem}
> ### **Tabela**
{indent}{tabela}

----
## Informações Colunas
{{{{ table_columns("yaml/{nome_descritivo}.yaml") }}}}

## Exemplo

{{{{ example("csv/examples/{nome_descritivo}.csv") }}}}
'''

    markdown_content = markdown_template.format(
        nome_descritivo=nome_descritivo, 
        sistema_origem=sistema_origem, 
        tabela=tabela,
        indent='    '
    )

    pasta_destino = 'pages/tabelas/'
    output_filename = f"{pasta_destino}{nome_descritivo}.md"
    with open(output_filename, "w", encoding='utf-8') as file:
        file.write(markdown_content)

    logger.info(f"Documentação da {tabela} salva em {pasta_destino}!")

def renomear_colunas_texto_normalizado(df_tabela: pd.DataFrame):
    df_tabela['SCRTEXT_M'] = df_tabela['SCRTEXT_M'].apply(lambda x: normalize_string(x))
    for i, nome_coluna in df_tabela['SCRTEXT_M'].items():
        duplicado = verifica_duplicado(df_tabela[:i+1], nome_coluna)
        vazio = nome_coluna == ''
        while duplicado or vazio:
            if vazio:
                text = f'''A coluna {df_tabela.loc[i, 'FIELDNAME']} tem a descrição vazia.\nA descrição da coluna é a seguinte: {df_tabela.loc[i, 'DDTEXT']}\nInsira um nome para este campo: '''
                nome_coluna = input(text)
            else:
                nome_coluna = input(f"A coluna {nome_coluna} já existe. Forneça um novo nome: ")

            novo_nome_invalido = verifica_duplicado(df_tabela, nome_coluna, nova_coluna=True)
            if not novo_nome_invalido and nome_coluna != '':
                duplicado = False
                vazio = False
                novo_nome = normalize_string(nome_coluna)
                df_tabela.loc[i, 'SCRTEXT_M'] = novo_nome
                logger.info(f"Nome da coluna alterado para {novo_nome}")

    return df_tabela

def gerar_documentacao_tabela(tabela, nome_descritivo, sistema_origem):
    df_tabela = seleciona_tabela(tabela)
    # Verificar campos texto repetidos
    df_tabela_renomeada = renomear_colunas_texto_normalizado(df_tabela)
    query = cria_query_sql(tabela, df_tabela_renomeada)
    escrever_query(query, nome_descritivo)
    estrutura_yaml = criar_estrutura_yaml(tabela, df_tabela_renomeada, nome_descritivo, sistema_origem)
    escrever_yaml(estrutura_yaml, nome_descritivo)
    salvar_exemplo(tabela, estrutura_yaml, nome_descritivo)
    escrever_pagina_documentacao(tabela, sistema_origem, nome_descritivo)
    logger.info(f"Processo concluído!")
    return True


if __name__ == '__main__':
    # tabela = 'KNA1'
    # nome_descritivo = 'mestre_clientes_geral'
    # sistema_origem = 'SAP'

    tabela = input('Informe o nome da tabela original: ').upper()
    sistema_origem = input('Informe o sistema de origem: ').upper()
    nome_descritivo = input('Insira o nome da tabela para o BI: ')

    status = gerar_documentacao_tabela(tabela, nome_descritivo, sistema_origem)