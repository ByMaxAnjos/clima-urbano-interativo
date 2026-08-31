# utils/navegacao.py
"""Navegação programática entre páginas.

O menu principal (streamlit_option_menu) é um componente com estado próprio no
navegador: sem passar `manual_select`, um `st.session_state.navigation = "X"`
seguido de `st.rerun()` NÃO move o menu para "X" — ele reaparece na última aba
clicada manualmente. Este helper marca um pedido de navegação pendente
(`nav_override`) que app.py consome uma única vez para forçar o `manual_select`
do menu, e então o limpa, deixando o usuário livre para clicar nas abas
normalmente depois.
"""

import streamlit as st


def ir_para(pagina: str):
    """Navega programaticamente para outra página do menu principal."""
    st.session_state.navigation = pagina
    st.session_state.nav_override = True
    st.rerun()
