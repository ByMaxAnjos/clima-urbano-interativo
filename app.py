# app.py - Plataforma Clima Urbano Interativo

import streamlit as st
import os
from modules import inicio, explorar, investigar, visualizar, avaliacao, info
from utils import processamento

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

# Barra Lateral de Navegação
with st.sidebar:
    # Logo e título
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: #2E86AB; margin: 0;">🌍</h1>
        <h2 style="color: #2E86AB; margin: 0; font-size: 1.5rem;">Clima Urbano</h2>
        <p style="color: #7F8C8D; margin: 0; font-size: 0.9rem;">Plataforma Interativa</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Menu de navegação
    st.markdown("### 📋 Sequência Didática")
    
    # Usar radio button para navegação
    pagina_selecionada = st.radio(
        "Selecione um módulo:",
        ["Início", "Explorar", "Investigar", "Visualizar", "Simular", "Avaliar plataforma", "Informações"],
        index=["Início", "Explorar", "Investigar", "Visualizar", "Simular", "Avaliar plataforma", "Informações"].index(st.session_state.navigation),
        key="nav_radio"
    )
    
    # Atualizar estado da navegação
    if pagina_selecionada != st.session_state.navigation:
        st.session_state.navigation = pagina_selecionada
        st.rerun()
    
    st.markdown("---")
    
    # Status da análise
    st.markdown("### 📊 Status da Análise")
    
    # Indicadores de status
    if st.session_state.get('dados_usuario') is not None:
        st.success("✅ Dados carregados")
        num_pontos = len(st.session_state['dados_usuario'])
        st.metric("Pontos", num_pontos)
    else:
        st.info("⏳ Sem dados")
    
    if st.session_state.get('area_de_interesse') is not None:
        st.success("✅ Área definida")
    else:
        st.info("⏳ Sem área")
    
    if st.session_state.get('analise_pronta'):
        st.success("✅ Análise pronta")
    else:
        st.info("⏳ Sem análise")
    
    st.markdown("---")
    
    # Informações da versão
    st.markdown("""
    <div style="text-align: center; color: #7F8C8D; font-size: 0.8rem;">
        <p><strong>Versão:</strong> 2.0</p>
        <p><strong>Fase:</strong> Análise Interativa</p>
        <p><strong>Dados:</strong> São Paulo (Exemplo)</p>
    </div>
    """, unsafe_allow_html=True)

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

