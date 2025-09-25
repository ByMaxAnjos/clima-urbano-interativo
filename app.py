# app.py - Plataforma Clima Urbano Interativo

import streamlit as st
from streamlit_option_menu import option_menu
import os
from modules import inicio, explorar, investigar, visualizar, simular, avaliacao, info
from utils import processamento, simulacao, lcz4r, lcz_visualizer

# Configuração da página
st.set_page_config(
    page_title="Plataforma Clima Urbano",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/seu-usuario/plataforma-clima-urbano',
        'Report a bug': 'https://github.com/seu-usuario/plataforma-clima-urbano/issues',
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
    pagina_selecionada = option_menu(
        menu_title=None,
        options=[
            "Início", 
            "Explorar", 
            "Investigar", 
            "Visualizar", 
            "Simular", 
            "Avaliar plataforma",
            "Informações"
        ],
        icons=[
            "house", 
            "cloud-upload", 
            "search", 
            "bar-chart", 
            "cpu", 
            "award",
            "about",
        ],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0.7rem 1rem",
                "background": "rgba(255, 255, 255, 0.25)",
                "backdrop-filter": "blur(12px)",   # efeito vidro
                "border-radius": "var(--border-radius-xl)",
                "box-shadow": "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
                "margin-bottom": "2rem"
            },
            "icon": {
                "color": "var(--primary-color)", 
                "font-size": "18px"
            },
            "nav-link": {
                "font-size": "1rem", 
                "font-weight": "600",
                "letter-spacing": "0.5px", 
                "text-transform": "uppercase",
                "margin": "0px 8px", 
                "padding": "14px 20px",
                "color": "var(--text-secondary)", 
                "--hover-color": "rgba(255, 255, 255, 0.15)",
                "border-radius": "var(--border-radius-lg)",
                "transition": "var(--transition)"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, rgba(102,126,234,0.8), rgba(118,75,162,0.8))",
                "color": "white",
                "border-radius": "var(--border-radius-lg)",
                "box-shadow": "var(--shadow-md)",
                "text-shadow": "0 1px 3px rgba(0,0,0,0.3)"
            },
        }
    )
    st.session_state.navigation = pagina_selecionada

# Área principal - Roteamento de páginas
if pagina_selecionada == "Início":
    inicio.renderizar_pagina()
elif pagina_selecionada == "Explorar":
    explorar.renderizar_pagina(gdf_zcl_base, gdf_temp_base)
elif pagina_selecionada == "Investigar":
    investigar.renderizar_pagina()
elif pagina_selecionada == "Visualizar":
    visualizar.renderizar_pagina()
elif pagina_selecionada == "Simular":
    simular.renderizar_pagina()
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
        <a href="https://github.com/maxanjos" target="_blank">GitHub</a> | 
        <a href="mailto:maxanjos@campus.ul.pt">Contato</a>
    </p>
    <p style="font-size: 0.8rem;">
        @Max Anjos & @Mariana Dias - 2025
    </p>
</div>
""", unsafe_allow_html=True)

