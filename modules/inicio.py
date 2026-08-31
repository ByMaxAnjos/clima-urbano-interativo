# modules/inicio.py

import streamlit as st
import base64
from utils.glossario import renderizar_entenda_dados
from utils.navegacao import ir_para

def renderizar_animacao_hero():
    """Renderiza a animação de fundo (mapa urbano LCZ + painéis analíticos) em loop contínuo."""
    st.markdown("""
    <div class="hero-anim">
      <svg viewBox="0 0 800 220" preserveAspectRatio="xMidYMid slice" class="hero-anim-svg">
        <defs>
          <linearGradient id="heroBg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#0A1E33"/>
            <stop offset="100%" stop-color="#123C5A"/>
          </linearGradient>
          <radialGradient id="heatGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#FF8C42" stop-opacity="0.55"/>
            <stop offset="100%" stop-color="#FF8C42" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <rect width="800" height="220" fill="url(#heroBg)"/>
        <circle cx="430" cy="120" r="90" fill="url(#heatGlow)" class="heat-pulse"/>
        <g class="lcz-grid">
""" + "".join(
            f'<rect x="{x}" y="{y}" width="46" height="34" rx="3" '
            f'fill="{color}" fill-opacity="0.82" class="lcz-block" '
            f'style="animation-delay:{delay:.2f}s"/>'
            for i, (x, y, color, delay) in enumerate([
                (60, 70, "#8A94A6", 0.0), (114, 70, "#4CAF7D", 0.15), (168, 70, "#FFB347", 0.3),
                (222, 70, "#2E86AB", 0.45), (276, 70, "#4CAF7D", 0.6), (330, 70, "#8A94A6", 0.75),
                (60, 112, "#FFB347", 0.9), (114, 112, "#2E86AB", 0.2), (168, 112, "#8A94A6", 0.5),
                (222, 112, "#4CAF7D", 0.35), (276, 112, "#FFB347", 0.65), (330, 112, "#2E86AB", 0.1),
                (60, 154, "#4CAF7D", 0.55), (114, 154, "#8A94A6", 0.25), (168, 154, "#FFB347", 0.8),
                (222, 154, "#4CAF7D", 0.4), (276, 154, "#8A94A6", 0.05), (330, 154, "#2E86AB", 0.7),
                (450, 70, "#2E86AB", 0.2), (504, 70, "#8A94A6", 0.5), (558, 70, "#FFB347", 0.35),
                (612, 70, "#4CAF7D", 0.65), (666, 70, "#8A94A6", 0.15), (720, 70, "#2E86AB", 0.45),
                (450, 112, "#FFB347", 0.6), (504, 112, "#4CAF7D", 0.3), (558, 112, "#2E86AB", 0.75),
                (612, 112, "#8A94A6", 0.1), (666, 112, "#FFB347", 0.5), (720, 112, "#4CAF7D", 0.85),
                (450, 154, "#8A94A6", 0.4), (504, 154, "#2E86AB", 0.7), (558, 154, "#4CAF7D", 0.2),
                (612, 154, "#FFB347", 0.55), (666, 154, "#2E86AB", 0.05), (720, 154, "#8A94A6", 0.9),
            ])
        ) + """
        </g>
        <polyline points="30,205 130,190 230,198 330,175 430,182 530,160 630,168 770,145"
                  class="clima-line" fill="none" stroke="#7FD1FF" stroke-width="2.5"/>
        <circle cx="628" cy="66" r="6" class="indicator ind-heat" fill="#FF8C42"/>
        <circle cx="196" cy="196" r="6" class="indicator ind-veg" fill="#4CAF7D"/>
        <circle cx="500" cy="196" r="6" class="indicator ind-vuln" fill="#E4572E"/>
        <g class="city-pin" transform="translate(400,20)">
          <path d="M0,0 C-7,0 -12,5 -12,12 C-12,21 0,34 0,34 C0,34 12,21 12,12 C12,5 7,0 0,0 Z"
                fill="#F2F6FA" fill-opacity="0.9"/>
          <circle cx="0" cy="12" r="4.5" fill="#123C5A"/>
        </g>
        <text x="400" y="70" text-anchor="middle" class="city-label" fill="#F2F6FA">Juiz de Fora, MG</text>
      </svg>
      <div class="hero-panel hero-panel-a">
        <span class="hero-panel-title">🌡️ Temp. Urbana</span>
        <span class="hero-panel-value">+3.4°C</span>
      </div>
      <div class="hero-panel hero-panel-b">
        <span class="hero-panel-title">🌳 Vegetação</span>
        <span class="hero-panel-value">-12%</span>
      </div>
      <div class="hero-panel hero-panel-c">
        <span class="hero-panel-title">⚠️ Vulnerabilidade</span>
        <span class="hero-panel-value">Moderada</span>
      </div>
    </div>
    <style>
    .hero-anim { position: relative; width: 100%; height: 220px; border-radius: 14px;
        overflow: hidden; margin-bottom: 1.2rem; box-shadow: 0 4px 24px rgba(10,30,51,0.35); }
    .hero-anim-svg { width: 100%; height: 100%; display: block; }
    .lcz-block { transform-origin: center; animation: lczRise 6s ease-in-out infinite; }
    @keyframes lczRise {
        0%   { opacity: 0; transform: translateY(6px) scale(0.92); }
        15%  { opacity: 1; transform: translateY(0) scale(1); }
        70%  { opacity: 1; transform: translateY(0) scale(1); }
        100% { opacity: 0; transform: translateY(6px) scale(0.92); }
    }
    .city-label { font-size: 12px; font-weight: 600; letter-spacing: 0.04em; opacity: 0.85; }
    .city-pin { animation: pinDrop 6s ease-in-out infinite; transform-origin: 400px 20px; }
    @keyframes pinDrop {
        0%, 100% { transform: translate(400px,20px) translateY(0); opacity: 0.9; }
        50%      { transform: translate(400px,20px) translateY(-4px); opacity: 1; }
    }
    .heat-pulse { animation: heatPulse 5s ease-in-out infinite; transform-origin: 430px 120px; }
    @keyframes heatPulse {
        0%, 100% { transform: scale(0.9); opacity: 0.5; }
        50%      { transform: scale(1.15); opacity: 0.9; }
    }
    .clima-line { stroke-dasharray: 900; stroke-dashoffset: 900;
        animation: drawLine 7s ease-in-out infinite; }
    @keyframes drawLine {
        0%   { stroke-dashoffset: 900; opacity: 0.3; }
        55%  { stroke-dashoffset: 0; opacity: 1; }
        100% { stroke-dashoffset: 0; opacity: 1; }
    }
    .indicator { animation: indPulse 2.4s ease-in-out infinite; }
    .ind-veg { animation-delay: 0.4s; }
    .ind-vuln { animation-delay: 0.8s; }
    @keyframes indPulse {
        0%, 100% { r: 5; opacity: 0.7; }
        50%      { r: 8; opacity: 1; }
    }
    .hero-panel { position: absolute; display: flex; flex-direction: column; gap: 2px;
        padding: 0.5rem 0.8rem; border-radius: 10px; backdrop-filter: blur(6px);
        background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18);
        color: #F2F6FA; font-size: 0.78rem; animation: floatPanel 6s ease-in-out infinite; }
    .hero-panel-title { opacity: 0.85; font-weight: 500; }
    .hero-panel-value { font-size: 1.05rem; font-weight: 700; }
    .hero-panel-a { top: 14px; left: 24px; animation-delay: 0s; }
    .hero-panel-b { bottom: 16px; left: 190px; animation-delay: 1.2s; }
    .hero-panel-c { top: 18px; right: 26px; animation-delay: 2.4s; }
    @keyframes floatPanel {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-6px); }
    }
    @media (prefers-reduced-motion: reduce) {
        .lcz-block, .heat-pulse, .clima-line, .indicator, .hero-panel { animation: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)


def renderizar_pagina():
    """Renderiza a página inicial da plataforma."""

    # Header principal com estilo
    st.markdown("""
    <div class="main-header">
        <h1>🌍 Plataforma Interativa de Clima Urbano</h1>
        <p class="subtitle">Ferramenta educacional para análise de Ilhas de Calor e Zonas Climáticas Locais</p>
    </div>
    """, unsafe_allow_html=True)

    renderizar_animacao_hero()

    # Seção de introdução
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 Sobre a Plataforma
        
        Esta plataforma foi desenvolvida especificamente para **estudantes e pesquisadores de Geografia** 
        interessados em compreender os fenômenos do clima urbano. Nosso foco principal são:
        
        - **🏙️ Ilhas de Calor Urbanas (ICU):** fenômeno em que áreas com maior densidade construída
          e menor vegetação ficam mais quentes do que áreas com estrutura e cobertura diferentes nas
          proximidades — por isso hoje se compara zona a zona (LCZ a LCZ), e não apenas "cidade vs. campo"
        - **🗺️ Zonas Climáticas Locais (LCZ):** sistema que classifica um recorte urbano pela sua
          estrutura física (altura e espaçamento das construções) e pela cobertura de superfície
          (vegetação, pavimento, água) — não pelo uso do terreno. Duas áreas com o mesmo uso podem
          estar em LCZ diferentes, e vice-versa
        
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

        **Metodologias:**
        - Sensoriamento remoto
        - Análise espacial
        - Coleta de dados de campo
        - Modelagem climática
        """)
        renderizar_entenda_dados(titulo="🔍 Conceitos Fundamentais (glossário)")

        # Botão de início
        if st.button("🚀 Começar Exploração", type="primary", use_container_width=True):
            ir_para("Explorar")
        
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
                st.write("Professor do Departamento de Geociências da Universidade Federal de Juiz de Fora (UFJF). Áreas de atuação: clima urbano, machine learning, modelagem ambiental e análise geoespacial.")
                st.markdown("""
                - [GitHub](https://github.com/ByMaxAnjos)
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
        
    # Contributors section
    st.markdown("### 🤝 Contribuidores")

    contribuidores = [
        ("Hyago Pinto Rodrigues Melo", "UFJF", "hyago.melo@estudante.ufjf.br", "assets/hyago_photo.jpg"),
        ("Aline Gabriel de Brito Rodrigues", "UFJF", "gbrito.aline@gmail.com", "assets/aline_photo.jpg"),
        ("Henrique Carcelen da Silva", "UFJF", "202627007@estudante.ufjf.br", "assets/henrique_photo.jpg"),
        ("Maria Cristina Alves Pereira", "UFJF", "mcristinaalvespereira@msn.com", "assets/mariacristina_photo.jpg"),
    ]

    cols = st.columns(4)
    for col, (nome, afiliacao, email, foto) in zip(cols, contribuidores):
        with col:
            try:
                st.image(foto, use_container_width=True)
            except Exception:
                st.info("👤")
            st.markdown(f"**{nome}**")
            st.caption(afiliacao)
            st.markdown(f"[Email](mailto:{email})")

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
