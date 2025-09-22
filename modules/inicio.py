# modules/inicio.py

import streamlit as st
import base64

def renderizar_pagina():
    """Renderiza a página inicial da plataforma."""
    
    # Header principal com estilo
    st.markdown("""
    <div class="main-header">
        <h1>🌍 Plataforma Interativa de Clima Urbano</h1>
        <p class="subtitle">Ferramenta educacional para análise de Ilhas de Calor e Zonas Climáticas Locais</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de introdução
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 Sobre a Plataforma
        
        Esta plataforma foi desenvolvida especificamente para **estudantes e pesquisadores de Geografia** 
        interessados em compreender os fenômenos do clima urbano. Nosso foco principal são:
        
        - **🏙️ Ilhas de Calor Urbanas (ICU):** Fenômeno onde áreas urbanas apresentam temperaturas 
          mais elevadas que as áreas rurais circundantes
        - **🗺️ Zonas Climáticas Locais (ZCL):** Sistema de classificação que categoriza diferentes 
          tipos de cobertura e uso do solo urbano
        
        ### 🚀 Como Começar
        
        A plataforma está organizada em módulos progressivos:
        """)
        
        # Cards dos módulos
        st.markdown("""
        <div class="module-cards">
            <div class="module-card">
                <h4>🌍 Explorar</h4>
                <p>Visualize mapas interativos de ZCL e temperatura para cidades de exemplo</p>
            </div>
            <div class="module-card">
                <h4>🔬 Investigar</h4>
                <p>Carregue seus próprios dados de campo e defina áreas de interesse para análise</p>
            </div>
            <div class="module-card">
                <h4>📊 Visualizar</h4>
                <p>Gere gráficos e estatísticas detalhadas sobre sua área de estudo</p>
            </div>
            <div class="module-card">
                <h4>💡 Simular</h4>
                <p>Explore o impacto de intervenções urbanas no clima local (em desenvolvimento)</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### 📚 Recursos Educacionais
        
        **Conceitos Fundamentais:**
        - Albedo urbano
        - Rugosidade da superfície
        - Capacidade térmica
        - Evapotranspiração
        
        **Metodologias:**
        - Sensoriamento remoto
        - Análise espacial
        - Coleta de dados de campo
        - Modelagem climática
        """)
        
        # Botão de início
        if st.button("🚀 Começar Exploração", type="primary", use_container_width=True):
            st.session_state.navigation = "Explorar"
            st.rerun()
        
    # Author info section
    st.markdown("### 👥 Desenvolvedores")

    col1, col2 = st.columns(2)

    with col1:
        # Author card 1
        with st.expander("**Max Anjos**", expanded=True):
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                try:
                    st.image("assets/max_photo.jpg", use_container_width=True)
                except:
                    st.info("👤")
            
            with col_info:
                st.write("Pesquisador da TU Berlin. Áreas de atuação: clima urbano, machine learning, modelagem ambiental e análise geoespacial.")
                st.markdown("""
                - [GitHub](https://github.com/maxanjos)
                - [LinkedIn](https://www.linkedin.com/in/maxanjos/)
                - [Email](mailto:maxanjos@campus.ul.pt)
                """)

    with col2:
        # Author card 2
        with st.expander("**Mariana Andreotti Dias**", expanded=True):
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                try:
                    st.image("assets/mari_photo.jpg", use_container_width=True)
                except:
                    st.info("👤")
            
            with col_info:
                st.write("❤ Mãe do Caetano e pesquisadora UERJ: Áreas de atuação: Geografia da Saúde, Ensino de Geografia e Climatologia Geógrafica")
                st.markdown("""
                - [ResearchGate](https://www.researchgate.net/profile/Mariana-Dias)
                - [Email](mailto:marianaandreotti@gmail.com)
                """)
        
    # Footer informativo
    st.markdown("""
    ---
    ### 🔬 Base Científica
    
    Esta plataforma é inpirada nos trabalhos de:
    
    - Anjos, M., Medeiros, D., Castelhano, F. et al. LCZ4r package R for local climate zones and urban heat islands. Sci Rep 15, 7710 (2025). https://doi.org/10.1038/s41598-025-92000-0
    - **LCZ4r** - Software para análise de LCZ e ilha de calor urbana (https://bymaxanjos.github.io/LCZ4r/index.html)
    - **Stewart & Oke (2012)** -Local climate zones for urban temperature studies. Bull. Am. Meteorol. Soc. 93, 1879–1900 (2012).
    - **WUDAPT (World Urban Database and Portal Tools)** - Protocolo global para mapeamento urbano (https://www.wudapt.org/)
    - **Projeto LCZ Generator** - Ferramenta automatizada para geração de mapas de ZCL (https://lcz-generator.rub.de/)
    
    **Versão:** 1.0 (Fase de Análise Interativa)  
    **Desenvolvido para:** Ensino e Pesquisa em Geografia e Climatologia Urbana
    """)
