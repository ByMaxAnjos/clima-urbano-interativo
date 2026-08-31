# utils/ui.py
"""Componentes de UI compartilhados entre os módulos da plataforma."""

import streamlit as st


def renderizar_cabecalho_modulo(titulo: str, subtitulo: str, logo_base64: str | None = None):
    """Renderiza o cabeçalho padrão de um módulo (`.module-header` em style.css),
    substituindo os HTML/gradientes divergentes que cada módulo reimplementava
    inline (cores hardcoded diferentes por módulo, sem usar os tokens do CSS)."""
    logo_html = (
        f'<img src="data:image/png;base64,{logo_base64}" width="70" style="border-radius: 10px;">'
        if logo_base64 else ""
    )
    # Sem linhas em branco/só-espaço dentro do bloco: uma linha assim faz o
    # markdown do Streamlit tratar o HTML seguinte como um novo parágrafo e
    # escapá-lo em vez de renderizá-lo (bug visto ao interpolar logo_html="").
    html = (
        '<div class="module-header">'
        '<div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">'
        f'{logo_html}<div><h1>{titulo}</h1><p>{subtitulo}</p></div>'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)
