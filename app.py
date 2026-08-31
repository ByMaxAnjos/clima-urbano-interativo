# app.py - Plataforma Clima Urbano Interativo

import streamlit as st
from streamlit_option_menu import option_menu
import os
from modules import inicio, explorar, investigar, visualizar, simular, clima_bairro, avaliacao, info
from utils import processamento, simulacao, lcz4r

# Configuração da página
st.set_page_config(
    page_title="Plataforma Clima Urbano",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/maxanjos/plataforma-clima-urbano',
        'Report a bug': 'https://github.com/maxanjos/plataforma-clima-urbano/issues',
        'About': """
        # Plataforma Clima Urbano Interativo v2.0
        
        Ferramenta educacional para análise de Ilhas de Calor Urbanas (ICU) 
        e Zonas Climáticas Locais (ZCL).
        
        Desenvolvido para estudantes e pesquisadores de Geografia.
        """
    }
)

# Carregar CSS customizado
def load_css():
    """Carrega o arquivo CSS customizado."""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Carregar CSS
load_css()

# Inicializar estado da sessão
def init_session_state():
    """Inicializa variáveis de estado da sessão."""
    if 'navigation' not in st.session_state:
        st.session_state.navigation = "Início"
    if 'dados_usuario' not in st.session_state:
        st.session_state.dados_usuario = None
    if 'area_de_interesse' not in st.session_state:
        st.session_state.area_de_interesse = None
    if 'analise_pronta' not in st.session_state:
        st.session_state.analise_pronta = False

init_session_state()

# Carregar dados base uma única vez
@st.cache_data
def carregar_dados_base():
    """Carrega os dados base de ZCL e temperatura."""
    caminho_zcl = os.path.join(os.path.dirname(__file__), "data", "sao_paulo_zcl.geojson")
    caminho_temp = os.path.join(os.path.dirname(__file__), "data", "sao_paulo_temp.geojson")
    
    gdf_zcl, gdf_temp, erro = processamento.carregar_dados_base(caminho_zcl, caminho_temp)
    
    if erro:
        st.error(f"❌ {erro}")
        st.stop()
    
    return gdf_zcl, gdf_temp

# Carregar dados
try:
    gdf_zcl_base, gdf_temp_base = carregar_dados_base()
    # Armazenar na sessão para acesso pelos módulos
    st.session_state['dados_base'] = (gdf_zcl_base, gdf_temp_base)
except Exception as e:
    st.error(f"❌ Erro ao carregar dados base: {e}")
    st.stop()

# Navigation
# --- MENU COM GLASSMORPHISM ---
with st.container():
    menu_options = [
        "Início",
        "Explorar",
        "Investigar",
        "Visualizar",
        "Simular",
        "Clima de Bairro",
        "Avaliar plataforma",
        "Informações"
    ]

    # Consome um pedido de navegação programática (utils.navegacao.ir_para), se houver,
    # forçando o menu a refletir a página de destino. default_index fica fixo em 0
    # (só afeta a primeira montagem); manual_select é o mecanismo do componente para
    # forçar uma seleção pós-montagem sem interferir em cliques manuais nas outras abas.
    manual_select = None
    if st.session_state.pop('nav_override', False):
        pagina_alvo = st.session_state.get('navigation', 'Início')
        if pagina_alvo in menu_options:
            manual_select = menu_options.index(pagina_alvo)

    pagina_selecionada = option_menu(
        menu_title=None,
        options=menu_options,
        icons=[
            "house",
            "cloud-upload",
            "search",
            "bar-chart",
            "cpu",
            "signpost-split",
            "award",
            "info-circle",
        ],
        menu_icon="cast",
        default_index=0,
        manual_select=manual_select,
        key="main_option_menu",
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0.7rem 1rem",
                "background": "rgba(255, 255, 255, 0.25)",
                "backdrop-filter": "blur(12px)",   # efeito vidro
                "border-radius": "24px",
                "box-shadow": "0 8px 32px 0 rgba(15, 118, 110, 0.25)",
                "margin-bottom": "2rem"
            },
            "icon": {
                "color": "#0f766e",
                "font-size": "18px"
            },
            "nav-link": {
                "font-size": "1rem",
                "font-weight": "600",
                "letter-spacing": "0.5px",
                "text-transform": "uppercase",
                "margin": "0px 8px",
                "padding": "14px 20px",
                "color": "#48604a",
                "--hover-color": "rgba(255, 255, 255, 0.15)",
                "border-radius": "16px",
                "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, rgba(15,118,110,0.85), rgba(14,165,233,0.85))",
                "color": "white",
                "border-radius": "16px",
                "box-shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
                "text-shadow": "0 1px 3px rgba(0,0,0,0.3)"
            },
        }
    )
    st.session_state.navigation = pagina_selecionada

# Área principal - Roteamento de páginas
if pagina_selecionada == "Início":
    inicio.renderizar_pagina()
elif pagina_selecionada == "Explorar":
    explorar.renderizar_pagina()
elif pagina_selecionada == "Investigar":
    investigar.renderizar_pagina()
elif pagina_selecionada == "Visualizar":
    visualizar.renderizar_pagina()
elif pagina_selecionada == "Simular":
    simular.renderizar_pagina()
elif pagina_selecionada == "Clima de Bairro":
    clima_bairro.renderizar_pagina()
elif st.session_state['navigation'] == "Avaliar plataforma":
    avaliacao.renderizar_pagina()
elif st.session_state['navigation'] == "Informações":
    info.renderizar_pagina()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7F8C8D; padding: 1rem;">
    <p>
        <strong>Plataforma Clima Urbano Interativo</strong> | 
        Desenvolvido para ensino e pesquisa em Geografia | 
        <a href="https://github.com/ByMaxAnjos" target="_blank">GitHub</a> |
        <a href="mailto:maxanjos@campus.ul.pt">Contato</a>
    </p>
    <p style="font-size: 0.8rem;">
        @Max Anjos & @Mariana Dias - 2025
    </p>
</div>
""", unsafe_allow_html=True)

