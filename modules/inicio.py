# modules/inicio.py

import base64
import random
from pathlib import Path

import streamlit as st
from utils.glossario import renderizar_entenda_dados
from utils.navegacao import ir_para
from utils.ui import icon_markup

# Paleta oficial das classes LCZ (Stewart & Oke, 2012 / WUDAPT)
_LCZ_BUILT_CORE = ["#910613", "#D9081C", "#FF0A22"]              # compact high/mid/lowrise
_LCZ_BUILT_OPEN = ["#C54F1E", "#FF6628", "#FF985E"]              # open high/mid/lowrise
_LCZ_BUILT_LOW = ["#BBBBBB", "#FFCBAB", "#565656", "#FDED3F"]    # large lowrise, sparsely built, heavy industry, lightweight lowrise
_LCZ_NATURAL = ["#006A18", "#00A926", "#628432", "#B5DA7F"]      # dense/scattered trees, bush/scrub, low plants
_LCZ_RARE = ["#FCF7B1", "#656BFA"]                                # bare soil/sand, water


def _asset_data_uri(path):
    """Codifica imagens locais para uso confiável em HTML dentro do Streamlit."""
    asset = Path(path)
    if not asset.exists():
        return ""
    mime = "image/svg+xml" if asset.suffix.lower() == ".svg" else f"image/{asset.suffix.lower().lstrip('.')}"
    if mime == "image/jpg":
        mime = "image/jpeg"
    data = base64.b64encode(asset.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _team_card(person, destaque=False):
    links = "".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in person.get("links", [])
    )
    photo = _asset_data_uri(person["foto"])
    logo = _asset_data_uri(person["logo"])
    card_class = "team-card team-card--featured" if destaque else "team-card"
    description = f'<p class="team-bio">{person["bio"]}</p>' if person.get("bio") else ""
    return (
        f'<article class="{card_class}">'
        '<div class="team-photo-wrap">'
        f'<img class="team-photo" src="{photo}" alt="Foto de {person["nome"]}">'
        '</div>'
        '<div class="team-card-body">'
        '<div class="team-card-head">'
        '<div>'
        f'<p class="team-role">{person["papel"]}</p>'
        f'<h4>{person["nome"]}</h4>'
        '</div>'
        f'<img class="institution-logo" src="{logo}" alt="Logo {person["instituicao"]}">'
        '</div>'
        f'<p class="team-affiliation">{person["instituicao_nome"]}</p>'
        f'{description}'
        f'<div class="team-links">{links}</div>'
        '</div>'
        '</article>'
    )


def _renderizar_equipe():
    ufjf_logo = "assets/institutions/ufjf-logo.jpg"
    uerj_logo = "assets/institutions/uerj-logo.png"
    desenvolvedores = [
        {
            "nome": "Max Anjos",
            "papel": "Desenvolvedor · Coordenação científica",
            "instituicao": "UFJF",
            "instituicao_nome": "Universidade Federal de Juiz de Fora",
            "foto": "assets/team/max.jpg",
            "logo": ufjf_logo,
            "bio": "Professor do Departamento de Geociências da UFJF. Atua em clima urbano, machine learning, modelagem ambiental e análise geoespacial.",
            "links": [
                ("GitHub", "https://github.com/ByMaxAnjos"),
                ("LinkedIn", "https://www.linkedin.com/in/maxanjos/"),
                ("Email", "mailto:maxanjos@campus.ul.pt"),
            ],
        },
        {
            "nome": "Mariana Andreotti Dias",
            "papel": "Desenvolvedora · Pesquisa e ensino",
            "instituicao": "UERJ",
            "instituicao_nome": "Universidade do Estado do Rio de Janeiro",
            "foto": "assets/team/mariana.jpg",
            "logo": uerj_logo,
            "bio": "Pesquisadora na UERJ. Atua em Geografia da Saúde, Ensino de Geografia e Climatologia Geográfica.",
            "links": [
                ("ResearchGate", "https://www.researchgate.net/profile/Mariana-Dias"),
                ("Email", "mailto:marianaandreotti@gmail.com"),
            ],
        },
    ]
    contribuidores = [
        {
            "nome": "Hyago Pinto Rodrigues Melo",
            "papel": "Contribuidor",
            "instituicao": "UFJF",
            "instituicao_nome": "Universidade Federal de Juiz de Fora",
            "foto": "assets/team/hyago.jpg",
            "logo": ufjf_logo,
            "links": [("Email", "mailto:hyago.melo@estudante.ufjf.br")],
        },
        {
            "nome": "Aline Gabriel de Brito Rodrigues",
            "papel": "Contribuidora",
            "instituicao": "UFJF",
            "instituicao_nome": "Universidade Federal de Juiz de Fora",
            "foto": "assets/team/aline.jpg",
            "logo": ufjf_logo,
            "links": [("Email", "mailto:gbrito.aline@gmail.com")],
        },
        {
            "nome": "Henrique Carcelen da Silva",
            "papel": "Contribuidor",
            "instituicao": "UFJF",
            "instituicao_nome": "Universidade Federal de Juiz de Fora",
            "foto": "assets/team/henrique.jpg",
            "logo": ufjf_logo,
            "links": [("Email", "mailto:202627007@estudante.ufjf.br")],
        },
        {
            "nome": "Maria Cristina Alves Pereira",
            "papel": "Contribuidora",
            "instituicao": "UFJF",
            "instituicao_nome": "Universidade Federal de Juiz de Fora",
            "foto": "assets/team/mariacristina.jpg",
            "logo": ufjf_logo,
            "links": [("Email", "mailto:mcristinaalvespereira@msn.com")],
        },
    ]
    dev_cards = "".join(_team_card(p, destaque=True) for p in desenvolvedores)
    contributor_cards = "".join(_team_card(p) for p in contribuidores)
    st.markdown(
        '<section class="team-section">'
        '<div class="team-section-header"><p class="team-eyebrow">Equipe</p><h3>Desenvolvedores</h3></div>'
        f'<div class="team-grid team-grid--featured">{dev_cards}</div>'
        '<div class="team-section-header team-section-header--compact"><p class="team-eyebrow">Rede de apoio</p><h3>Contribuidores</h3></div>'
        f'<div class="team-grid team-grid--contributors">{contributor_cards}</div>'
        '</section>',
        unsafe_allow_html=True,
    )


def _gerar_mosaico_lcz(cols=15, rows=10, seed=7):
    """Gera um mosaico de células coloridas com as classes LCZ, concentrando os
    tons construídos (vermelho/laranja) num núcleo urbano cercado por vegetação —
    a mesma lógica de qualquer mapeamento LCZ real, sem reproduzir um mapa específico."""
    rnd = random.Random(seed)
    cx, cy = cols * 0.62, rows * 0.5
    max_d = (cx ** 2 + cy ** 2) ** 0.5
    cells = []
    for r in range(rows):
        for c in range(cols):
            d = (((c - cx) ** 2 + (r - cy) ** 2) ** 0.5) / max_d
            roll = rnd.random()
            if d < 0.20:
                color = rnd.choice(_LCZ_BUILT_CORE) if roll > 0.15 else rnd.choice(_LCZ_BUILT_OPEN)
            elif d < 0.38:
                color = rnd.choice(_LCZ_BUILT_OPEN) if roll > 0.3 else rnd.choice(_LCZ_BUILT_CORE + _LCZ_BUILT_LOW)
            elif d < 0.55:
                color = rnd.choice(_LCZ_BUILT_LOW) if roll > 0.45 else rnd.choice(_LCZ_NATURAL)
            elif roll > 0.94:
                color = rnd.choice(_LCZ_RARE)
            elif roll > 0.8:
                color = rnd.choice(_LCZ_BUILT_LOW)
            else:
                color = rnd.choice(_LCZ_NATURAL)
            delay = round(d * 2.2 + rnd.random() * 0.6, 2)
            cells.append((c, r, color, delay, rnd.random() > 0.93))
    return cells


def _svg_mosaico_lcz_hero():
    """Monta o SVG do mosaico: células nas cores oficiais das classes LCZ,
    surgindo em onda do núcleo urbano para a vegetação ao redor."""
    cell, gap = 26, 3
    size = cell - gap
    cells = _gerar_mosaico_lcz()
    cols = max(c for c, *_ in cells) + 1
    rows = max(r for _, r, *_ in cells) + 1
    rects = "".join(
        f'<rect x="{c * cell}" y="{r * cell}" width="{size}" height="{size}" rx="3" '
        f'fill="{color}" class="lcz-cell{" lcz-cell-shift" if shift else ""}" '
        f'style="animation-delay:{delay}s"/>'
        for c, r, color, delay, shift in cells
    )
    return (
        f'<svg viewBox="0 0 {cols * cell} {rows * cell}" preserveAspectRatio="xMidYMid slice" '
        f'class="lcz-hero-svg">{rects}</svg>'
    )


def renderizar_pagina():
    """Renderiza a página inicial da plataforma."""

    # Header principal: título à esquerda, animação com as classes/cores LCZ à direita
    st.markdown(f"""
    <div class="main-header main-header-split">
        <div class="main-header-text">
            <p class="hero-eyebrow">MAPAS · DADOS · CENÁRIOS</p>
            <h1><span class="hero-brand-icon">{icon_markup("Marca Clima Urbano", "3.25rem", "brand")}</span> Plataforma Interativa de Clima Urbano</h1>
            <p class="subtitle">Ferramenta educacional para análise de Ilhas de Calor e Zonas Climáticas Locais</p>
            <span class="hero-signal" aria-hidden="true"></span>
        </div>
        <div class="main-header-media lcz-hero-mosaic">
            {_svg_mosaico_lcz_hero()}
        </div>
    </div>
    <style>
    .lcz-hero-mosaic {{ overflow: hidden; }}
    .lcz-hero-svg {{ width: 100%; height: 100%; display: block; }}
    .lcz-cell {{ opacity: 0; transform-origin: center; animation: lczFadeIn 7s ease-in-out infinite; }}
    @keyframes lczFadeIn {{
        0%   {{ opacity: 0; transform: scale(0.85); }}
        12%  {{ opacity: 1; transform: scale(1); }}
        75%  {{ opacity: 1; transform: scale(1); }}
        100% {{ opacity: 0; transform: scale(0.85); }}
    }}
    .lcz-cell-shift {{ animation: lczFadeIn 7s ease-in-out infinite, lczHue 9s ease-in-out infinite; }}
    @keyframes lczHue {{
        0%, 100% {{ filter: hue-rotate(0deg); }}
        50%      {{ filter: hue-rotate(28deg); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        .lcz-cell, .lcz-cell-shift {{ animation: none !important; opacity: 1; }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # Seção de introdução
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <h3 class="section-title-with-icon">{icon_markup("Sobre a Plataforma", "2rem", "overview")}<span>Sobre a Plataforma</span></h3>
        
        Esta plataforma foi desenvolvida especificamente para **estudantes e pesquisadores de Geografia** 
        interessados em compreender os fenômenos do clima urbano. Nosso foco principal são:
        
        - **🏙️ Ilhas de Calor Urbanas (ICU):** fenômeno em que áreas com maior densidade construída
          e menor vegetação ficam mais quentes do que áreas com estrutura e cobertura diferentes nas
          proximidades — por isso hoje se compara zona a zona (LCZ a LCZ), e não apenas "cidade vs. campo"
        - **🗺️ Zonas Climáticas Locais (LCZ):** sistema que classifica um recorte urbano pela sua
          estrutura física (altura e espaçamento das construções) e pela cobertura de superfície
          (vegetação, pavimento, água) — não pelo uso do terreno. Duas áreas com o mesmo uso podem
          estar em LCZ diferentes, e vice-versa
        
        <h3 class="section-title-with-icon">{icon_markup("Como começar", "2rem", "start")}<span>Como Começar</span></h3>
        
        A plataforma está organizada em módulos progressivos:
        """, unsafe_allow_html=True)
        
        # Cards dos módulos
        st.markdown(f"""
        <div class="module-cards">
            <div class="module-card">
                <h4>{icon_markup("Explorar", "1.8rem", "explore")} Explorar</h4>
                <p>Visualize mapas interativos de ZCL e temperatura para cidades de exemplo</p>
            </div>
            <div class="module-card">
                <h4>{icon_markup("Investigar", "1.8rem", "investigate")} Investigar</h4>
                <p>Carregue seus próprios dados de campo e defina áreas de interesse para análise</p>
            </div>
            <div class="module-card">
                <h4>{icon_markup("Visualizar", "1.8rem", "visualize")} Visualizar</h4>
                <p>Gere gráficos e estatísticas detalhadas sobre sua área de estudo</p>
            </div>
            <div class="module-card">
                <h4>{icon_markup("Simular", "1.8rem", "simulate")} Simular</h4>
                <p>Explore o impacto de intervenções urbanas no clima local</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <h3 class="section-title-with-icon">{icon_markup("Recursos educacionais", "2rem", "resources")}<span>Recursos Educacionais</span></h3>

        **Metodologias:**
        - Sensoriamento remoto
        - Análise espacial
        - Coleta de dados de campo
        - Modelagem climática
        """, unsafe_allow_html=True)
        renderizar_entenda_dados(titulo="Conceitos Fundamentais (glossário)")

        # Botão de início
        if st.button("🚀 Começar Exploração", type="primary", use_container_width=True):
            ir_para("Explorar")
        
    _renderizar_equipe()

    # Footer informativo
    st.markdown("""
    ---
    ### 🔬 Base Científica
    
    Esta plataforma é inspirada nos trabalhos de:
    
    - Anjos, M., Medeiros, D., Castelhano, F. et al. LCZ4r package R for local climate zones and urban heat islands. Sci Rep 15, 7710 (2025). https://doi.org/10.1038/s41598-025-92000-0
    - **LCZ4r** - Software para análise de LCZ e ilha de calor urbana (https://bymaxanjos.github.io/LCZ4r/index.html)
    - **Stewart & Oke (2012)** - Local climate zones for urban temperature studies. Bull. Am. Meteorol. Soc. 93, 1879–1900 (2012).
    - **WUDAPT (World Urban Database and Portal Tools)** - Protocolo global para mapeamento urbano (https://www.wudapt.org/)
    - **Projeto LCZ Generator** - Ferramenta automatizada para geração de mapas de ZCL (https://lcz-generator.rub.de/)
    
    **Versão:** 3.0 (Fase de Análise Interativa)
    **Desenvolvido para:** Ensino e Pesquisa em Geografia e Climatologia Urbana
    """)
