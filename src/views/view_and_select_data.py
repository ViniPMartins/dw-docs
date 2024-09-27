import streamlit as st
import pandas as pd
import os
from database import update_table, tables, fetch_data_from
from ydata_profiling import ProfileReport
from streamlit.components.v1 import components
import duckdb

def show_header():
    st.title("BI Documentação")
    list_dir =  [ark.split('.')[0] for ark in os.listdir('bases/examples')]
    base_selecionada = st.selectbox("Selecione a base a ser trabalhada", list_dir)
    return base_selecionada

@st.cache_data
def get_source_data(base_selecionada):
    table_names = tables()
    if base_selecionada in table_names:
        column_names = fetch_data_from(base_selecionada)
    else:
        column_names = pd.read_csv(f'bases/table_fields/{base_selecionada}.csv', sep=';', index_col='FIELDNAME', encoding='utf-8')
        column_names = column_names[['SCRTEXT_M', 'DDTEXT']]
        column_names['Selecionar'] = True

    example = pd.read_csv(f'bases/examples/{base_selecionada}.csv', sep=';')

    return column_names, example

@st.cache_resource
def define_session_state(example: pd.DataFrame, column_names: pd.DataFrame, base_selecionada: str):
    if 'columns_to_exclude' not in st.session_state:
        st.session_state.columns_to_exclude = None

    if 'base_selecionada' not in st.session_state:
        st.session_state.base_selecionada = None

    if st.session_state.base_selecionada != base_selecionada:
        st.session_state.base_selecionada = base_selecionada
        st.session_state.column_names = column_names
        selected_columns = list(column_names[column_names['Selecionar'] == True].index)
        st.session_state.select_columns = selected_columns
        st.session_state.example = example

def remove_columns():
    #st.cache_resource.clear()
    columns_to_exclude: list = st.session_state.columns_to_exclude
    selected_columns: list = st.session_state.select_columns

    if columns_to_exclude:
        for col in columns_to_exclude:
            selected_columns.remove(col)

    st.session_state.columns_to_exclude = columns_to_exclude
    st.session_state.select_columns = selected_columns

def column_config():
    if "column_config" not in st.session_state:
        column_config = {}
        indices = dict(st.session_state.column_names['DDTEXT'])
        for idx, desc in indices.items():
            column_config[idx] = st.column_config.Column(
                idx + " - " + desc,
                help=f'**Nome Técnico**: {idx} | **Descrição**: {desc}'
            )
        st.session_state.column_config = column_config

@st.fragment
def main() -> dict:

    tab1, tab2 = st.tabs(['Exemplos dos dados: ', 'Status Seleção'])

    with tab1:
        st.subheader("Exemplos de dados:")
        # df_example = st.session_state.example
        # df = st.session_state.example[st.session_state.select_columns]
        event = st.dataframe(
            st.session_state.example[st.session_state.select_columns],
            column_config=st.session_state.column_config,
            key="data_example",
            on_select="rerun",
            selection_mode=["multi-column"])
        st.session_state.columns_to_exclude = event['selection']['columns']

        if event['selection']['columns']:

            if st.button(label='Excluir Colunas'):
                remove_columns()
                st.session_state.column_names.loc[st.session_state.columns_to_exclude, 'Selecionar'] = False
                update_table(st.session_state.base_selecionada, st.session_state.column_names)
                st.rerun(scope="fragment")

            if st.button("Gerar Análises"):
                with st.spinner('Gerando Análise'):
                    with st.expander("Ver Análises"):
                        profile = ProfileReport(st.session_state.example[event['selection']['columns']], title="Relatório do DataFrame", explorative=True)
                        profile_html = profile.to_html()
                        st.components.v1.html(profile_html, height=1000, scrolling=True)

    with tab2:
        st.subheader("Status Seleção Colunas:")
        df_edited = st.data_editor(st.session_state.column_names)
        if st.button("Atualizar Colunas"):
            selected_columns = list(df_edited[df_edited['Selecionar'] == True].index)
            st.session_state.select_columns = selected_columns
            st.session_state.column_names = df_edited
            update_table(st.session_state.base_selecionada, st.session_state.column_names)
            st.rerun(scope="fragment")


def page_view_and_select_data():
    base_selecionada = show_header()
    if st.button("Atualizar tabelas"):
        st.cache_data.clear()
        st.cache_resource.clear()
        column_names, example = get_source_data(base_selecionada)
        define_session_state(example, column_names, base_selecionada)
        column_config()
        main()

if __name__ == '__main__':
    page_view_and_select_data()