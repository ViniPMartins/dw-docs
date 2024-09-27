from views.update_docs import page_update_docs
from views.view_and_select_data import page_view_and_select_data
import streamlit as st

page_view_and_select = st.Page(page_view_and_select_data, title="Visualizar e Editar Dados")
page_upd_docs = st.Page(page_update_docs, title="Atualizar Documentação")

pg = st.navigation([page_view_and_select, page_upd_docs])

st.set_page_config(
    page_title="Data Manager - BI Docs",
    page_icon="📋",
    layout="wide",
)

pg.run()