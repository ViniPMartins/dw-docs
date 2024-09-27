import streamlit as st
import os
from database.controller import tables, update_table
import pandas as pd

from backend import gerar_documentacao_tabela

def obter_dados(base_selecionada):
    column_names = pd.read_csv(f'bases/table_fields/{base_selecionada}.csv', sep=';', index_col='FIELDNAME', encoding='utf-8')
    column_names = column_names[['SCRTEXT_M', 'DDTEXT']]
    column_names['Selecionar'] = True
    return column_names


def page_update_docs():
    # Tabela: Select Box
    # Sistema de Origem: Select Box
    # nome_descritivo: Input_text
    st.title("Atualizar Documentação")
    ark_tables =  [ark.split('.')[0] for ark in os.listdir('bases/table_fields')]
    tabela = st.selectbox("Tabela: ", ark_tables, index=None, placeholder='Selecione a tabela')
    sys_origem = st.selectbox("Sistema de Origem: ", ['SAP'], index=None, placeholder='Selecione a sistema')
    desc_tabela = st.text_input("Descrição da tabela", placeholder="Escreva um descrição para a tabela")

    tipo_query = st.radio("Selecionar modo de construção", ['Ler Query', 'Criar Query'])
    querys =  [ark.split('.')[0] for ark in os.listdir('querys')]
    if tipo_query == 'Ler Query':
        contem_query = True
        nome_query = st.selectbox("Selecionar Tabela: ", querys, index=None, placeholder='Selecione a query')
    else:
        contem_query = False
        nome_query = st.text_input("Nome da tabela no BI", placeholder="Escolha um nome descritivo para a tabela: ")

    if tabela and sys_origem and nome_query and desc_tabela:
        if st.button("Salvar"):
            if tabela not in tables():
                st.warning("Tabela não está no banco de dados. Gerando uma nova tabela no banco")
                df = obter_dados(tabela)
                update_table(tabela, df)

            gerar_documentacao_tabela(tabela, nome_query, sys_origem, desc_tabela, contem_query)
            st.success("Documentação Atualizada")

if __name__ == '__main__':
    page_update_docs()