"""
ui_components_modern.py
=======================

Componentes reutilizáveis de UI/UX moderno para o módulo Explorar.
Integração com tema Forest Canopy (emerald, sky, terracotta).

Design System: 4 alternativas modernas (Gradient Hero, Timeline, Infographic, Glassmorphism)

Uso:
    from utils.ui_components_modern import design1_hero_cards, card_moderno

    st.markdown(design1_hero_cards(), unsafe_allow_html=True)
    st.markdown(card_moderno(...), unsafe_allow_html=True)
"""

import streamlit as st
from typing import Optional, Dict, Literal


# ==============================================================================
# DESIGN 1: Gradient Hero + Floating Cards
# ==============================================================================

def design1_hero_cards(
    titulo: str = "Explorar Zonas Climáticas Locais",
    subtitulo: str = "Entenda o padrão climático em sua cidade através de 17 classes de morfologia urbana",
    cta_text: str = "Gerar Meu Primeiro Mapa →",
    cards: Optional[list] = None
) -> str:
    """
    Design 1: Gradient Hero + Floating Cards

    Características:
    - Gradient animado (8s loop): emerald → sky → terracotta
    - 3 cards com glassmorphism + floating effect
    - Icon glow animation
    - Responsive: 3 cols (desktop) → 1 col (mobile)

    Args:
        titulo: Título principal
        subtitulo: Subtítulo/descrição
        cta_text: Texto do botão CTA
        cards: Lista de dicts com {"titulo", "descricao", "icone"}
                Se None, usa padrão (LCZ, Temperatura, Classes)

    Returns:
        HTML string pronto para st.markdown(..., unsafe_allow_html=True)
    """

    if cards is None:
        cards = [
            {
                "titulo": "O que é LCZ?",
                "descricao": "Zonas Climáticas Locais classificam áreas urbanas de forma padronizada, ajudando a entender por que diferentes partes da cidade têm climas diferentes.",
                "icone": "🏙️"
            },
            {
                "titulo": "Temperatura Urbana",
                "descricao": "As ilhas de calor urbanas (ICU) podem aumentar a temperatura até 8°C em áreas muito urbanizadas. Veja como isso ocorre em sua cidade.",
                "icone": "🌡️"
            },
            {
                "titulo": "17 Classes de Morfologia",
                "descricao": "Desde zonas de torres comerciais até parques e áreas rurais. Cada classe tem características únicas de forma urbana, materiais e cobertura.",
                "icone": "📊"
            }
        ]

    cards_html = ""
    for i, card in enumerate(cards):
        cards_html += f"""
        <div class="design1-card" style="animation-delay: {i * 0.1}s;">
          <div class="design1-card-icon">{card['icone']}</div>
          <h3>{card['titulo']}</h3>
          <p>{card['descricao']}</p>
        </div>
        """

    html = f"""
    <style>
      .design1-hero {{
        background: linear-gradient(135deg, #10b981 0%, #0ea5e9 50%, #c2410c 100%);
        background-size: 400% 400%;
        animation: gradientShift 8s ease infinite;
        color: white;
        padding: clamp(2rem, 8vw, 4rem);
        border-radius: 20px;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(26, 46, 26, 0.15);
        margin-bottom: 3rem;
      }}

      @keyframes gradientShift {{
        0%   {{ background-position: 0% 50%; }}
        50%  {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
      }}

      .design1-hero::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.2) 0%, transparent 70%);
        border-radius: 50%;
        animation: floatParticle 6s ease-in-out infinite;
      }}

      @keyframes floatParticle {{
        0%, 100% {{ transform: translate(0, 0); }}
        50% {{ transform: translate(30px, -30px); }}
      }}

      .design1-hero h1 {{
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 800;
        margin: 0 0 1rem 0;
        text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 2;
        font-family: 'Source Serif 4', Georgia, serif;
      }}

      .design1-hero p {{
        font-size: clamp(1rem, 2.5vw, 1.3rem);
        opacity: 0.95;
        margin: 0 0 2rem 0;
        position: relative;
        z-index: 2;
      }}

      .design1-cta-button {{
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border: 1.5px solid rgba(255, 255, 255, 0.4);
        color: white;
        padding: 1.1rem 2.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.05rem;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        z-index: 2;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      }}

      .design1-cta-button:hover {{
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-3px);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        border-color: rgba(255, 255, 255, 0.6);
      }}

      .design1-cards-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 2rem;
        margin-top: 3rem;
      }}

      .design1-card {{
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(16, 185, 129, 0.18);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(26, 46, 26, 0.10);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: cardFloatIn 0.6s ease-out backwards;
      }}

      @keyframes cardFloatIn {{
        from {{
          opacity: 0;
          transform: translateY(30px);
        }}
        to {{
          opacity: 1;
          transform: translateY(0);
        }}
      }}

      .design1-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #10b981, #0ea5e9, #c2410c);
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.4s ease;
      }}

      .design1-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 16px 48px rgba(26, 46, 26, 0.15);
        border-color: rgba(16, 185, 129, 0.35);
      }}

      .design1-card:hover::before {{
        transform: scaleX(1);
      }}

      .design1-card-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
        display: inline-block;
        filter: drop-shadow(0 4px 8px rgba(16, 185, 129, 0.2));
        animation: iconGlow 2.5s ease-in-out infinite;
      }}

      @keyframes iconGlow {{
        0%, 100% {{ filter: drop-shadow(0 4px 8px rgba(16, 185, 129, 0.2)); }}
        50% {{ filter: drop-shadow(0 8px 16px rgba(16, 185, 129, 0.35)); }}
      }}

      .design1-card h3 {{
        font-size: 1.35rem;
        color: #059669;
        margin: 1rem 0 0.75rem 0;
        font-weight: 700;
        font-family: 'Source Serif 4', Georgia, serif;
      }}

      .design1-card p {{
        color: #4a6741;
        font-size: 0.95rem;
        line-height: 1.65;
        margin: 0;
      }}

      @media (max-width: 768px) {{
        .design1-hero {{
          padding: 2rem 1.25rem;
        }}
        .design1-hero h1 {{
          font-size: 1.8rem;
        }}
        .design1-cards-container {{
          grid-template-columns: 1fr;
          gap: 1.25rem;
          margin-top: 2rem;
        }}
      }}

      @media (prefers-reduced-motion: reduce) {{
        .design1-hero,
        .design1-card,
        .design1-card-icon {{
          animation: none !important;
          transition: none !important;
        }}
      }}
    </style>

    <div class="design1-hero">
      <h1>{titulo}</h1>
      <p>{subtitulo}</p>
      <button class="design1-cta-button">{cta_text}</button>
    </div>

    <div class="design1-cards-container">
      {cards_html}
    </div>
    """

    return html


# ==============================================================================
# DESIGN 2: Timeline Interativa / Steps
# ==============================================================================

def design2_timeline_steps(
    current_step: int = 2,
    steps: Optional[list] = None
) -> str:
    """
    Design 2: Timeline Interativa com 4 passos.

    Características:
    - Linha conectando os passos (horizontal desktop, vertical mobile)
    - Estados: completed (✓), active (⊙), upcoming (⭕)
    - Step ativo com gradient e pulse animation
    - Chevrons entre passos (desktop)

    Args:
        current_step: 1, 2, 3, ou 4
        steps: Lista de dicts com {"titulo", "desc", "detail"}
               Se None, usa padrão (Entender, Explorar, Investigar, Simular)

    Returns:
        HTML string
    """

    if steps is None:
        steps = [
            {"title": "Entender", "desc": "O que é LCZ?", "detail": "Conceitos fundamentais de zonas climáticas"},
            {"title": "Explorar", "desc": "Visualizar mapa", "detail": "Gere mapas LCZ interativos"},
            {"title": "Investigar", "desc": "Analisar dados", "detail": "Upload e validação de dados"},
            {"title": "Simular", "desc": "Testar intervenções", "detail": "Green roofs, parques e albedo"}
        ]

    steps_html = ""
    for i, step in enumerate(steps, 1):
        if i < current_step:
            state_class = "completed"
        elif i == current_step:
            state_class = "active"
        else:
            state_class = "upcoming"

        steps_html += f"""
        <div class="design2-step {state_class}">
          <h3>{i}. {step['title']}</h3>
          <p>{step['desc']}</p>
          <div class="design2-step-detail">{step['detail']}</div>
        </div>
        """

        if i < len(steps):
            steps_html += '<div class="design2-chevron">→</div>'

    html = f"""
    <style>
      .design2-timeline {{
        position: relative;
        padding: 2rem 0;
        margin: 3rem 0;
      }}

      .design2-timeline::before {{
        content: '';
        position: absolute;
        top: 40px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #d1fae5 0%, #e0f2fe 100%);
        z-index: 1;
      }}

      @media (max-width: 768px) {{
        .design2-timeline::before {{
          left: 30px;
          right: auto;
          width: 2px;
          height: calc(100% - 80px);
          top: 80px;
          background: linear-gradient(180deg, #d1fae5 0%, #e0f2fe 100%);
        }}
      }}

      .design2-steps {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 2rem;
        position: relative;
        z-index: 2;
      }}

      @media (max-width: 768px) {{
        .design2-steps {{
          grid-template-columns: 1fr;
          gap: 1.5rem;
        }}
      }}

      .design2-step {{
        position: relative;
        padding: 2rem;
        background: var(--surface-color);
        border: 1.5px solid var(--border-color);
        border-radius: 12px;
        text-align: center;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
      }}

      .design2-step::before {{
        content: '';
        position: absolute;
        top: -50px;
        left: 50%;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: white;
        border: 2px solid var(--border-color);
        transform: translateX(-50%);
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 3;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--text-secondary);
      }}

      @media (max-width: 768px) {{
        .design2-step::before {{
          top: 50%;
          left: -50px;
        }}
      }}

      .design2-step.completed::before {{
        background: #d1fae5;
        border-color: #10b981;
        color: #059669;
        content: '✓';
      }}

      .design2-step.active {{
        background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
        color: white;
        border-color: #059669;
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.25);
        transform: scale(1.05);
      }}

      .design2-step.active::before {{
        background: #ffffff;
        border-color: #10b981;
        color: #10b981;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
        animation: stepPulse 2s ease-in-out infinite;
      }}

      @keyframes stepPulse {{
        0%, 100% {{ transform: translateX(-50%) scale(1); }}
        50% {{ transform: translateX(-50%) scale(1.15); }}
      }}

      .design2-step.upcoming::before {{
        background: #f0f4ef;
        border-color: #8aaa82;
        color: #8aaa82;
        content: '⭕';
      }}

      .design2-step h3 {{
        margin: 1rem 0 0.5rem 0;
        font-size: 1.15rem;
        font-weight: 700;
        font-family: 'Source Serif 4', Georgia, serif;
      }}

      .design2-step.active h3 {{
        color: white;
      }}

      .design2-step p {{
        font-size: 0.9rem;
        opacity: 0.8;
        margin: 0;
        line-height: 1.5;
      }}

      .design2-step.active p {{
        color: rgba(255, 255, 255, 0.95);
      }}

      .design2-step:hover:not(.active) {{
        transform: translateY(-3px);
        border-color: var(--primary-color);
        box-shadow: var(--shadow-md);
      }}

      .design2-chevron {{
        position: absolute;
        top: 50%;
        right: -1.25rem;
        transform: translateY(-50%);
        color: #8aaa82;
        font-size: 1.25rem;
        opacity: 0.5;
      }}

      @media (max-width: 768px) {{
        .design2-chevron {{
          display: none;
        }}
      }}

      .design2-step-detail {{
        margin-top: 1.5rem;
        font-size: 0.85rem;
        opacity: 0.7;
        padding: 1rem;
        background: var(--surface-hover);
        border-radius: 8px;
        border-left: 3px solid var(--primary-color);
      }}

      .design2-step.active .design2-step-detail {{
        background: rgba(0, 0, 0, 0.15);
        border-left-color: white;
      }}
    </style>

    <div class="design2-timeline">
      <div class="design2-steps">
        {steps_html}
      </div>
    </div>
    """

    return html


# ==============================================================================
# DESIGN 4: Glassmorphism Premium + Neon Accents
# ==============================================================================

def design4_glassmorphism_premium(
    titulo: str = "Explorar Zonas Climáticas Locais",
    subtitulo: str = "Visualize a morfologia urbana com tecnologia de dados avançada",
    badge_text: str = "✨ Premium Experience",
    cards: Optional[list] = None
) -> str:
    """
    Design 4: Glassmorphism Premium com Neon Accents (RECOMENDADO).

    Características:
    - Fundo escuro com orbs flutuantes (rgb gradients)
    - Hero com título gradient (emerald → sky)
    - Badge com neon pulse animation
    - Cards em glassmorphism com borda neon em hover
    - Icon float + scale on hover
    - Máximo "wow factor"

    Args:
        titulo: Título principal
        subtitulo: Subtítulo
        badge_text: Texto do badge (ex: "Beta", "Premium")
        cards: Lista de dicts com {"titulo", "descricao", "icone", "metrica"}
               Se None, usa padrão

    Returns:
        HTML string
    """

    if cards is None:
        cards = [
            {
                "titulo": "O que é LCZ?",
                "descricao": "Zonas Climáticas Locais classificam áreas urbanas em 17 tipos distintos, desde torres comerciais até parques e zonas rurais.",
                "icone": "🏙️",
                "metrica": {"valor": "17", "label": "Classes Definidas"},
                "progress": 100
            },
            {
                "titulo": "Clima Urbano",
                "descricao": "As ilhas de calor urbanas (ICU) podem elevar a temperatura até 8°C em áreas densamente construídas.",
                "icone": "🌡️",
                "metrica": {"valor": "+8°C", "label": "Diferença Máxima"},
                "progress": 75
            },
            {
                "titulo": "Análise Avançada",
                "descricao": "Ferramentas científicas para investigar, visualizar e simular intervenções urbanas com dados geoespaciais.",
                "icone": "📊",
                "metrica": {"valor": "100+", "label": "Cidades Mapeadas"},
                "progress": 85
            }
        ]

    cards_html = ""
    for card in cards:
        progress = card.get("progress", 75)
        cards_html += f"""
        <div class="design4-glass-card">
          <div class="design4-card-content">
            <div class="design4-card-icon">{card['icone']}</div>
            <h3 class="design4-card-title">{card['titulo']}</h3>
            <p class="design4-card-description">{card['descricao']}</p>
            <div class="design4-card-metric">
              <div class="design4-card-metric-value">{card['metrica']['valor']}</div>
              <div class="design4-card-metric-label">{card['metrica']['label']}</div>
            </div>
            <div class="design4-progress-bar">
              <div class="design4-progress-fill" style="width: {progress}%;"></div>
            </div>
          </div>
        </div>
        """

    html = f"""
    <style>
      .design4-dark-bg {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        position: relative;
        overflow: hidden;
        margin-bottom: 3rem;
      }}

      .design4-dark-bg::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%);
        border-radius: 50%;
        animation: orb-float 8s ease-in-out infinite;
      }}

      .design4-dark-bg::after {{
        content: '';
        position: absolute;
        bottom: -30%;
        left: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.08) 0%, transparent 70%);
        border-radius: 50%;
        animation: orb-float-reverse 10s ease-in-out infinite;
      }}

      @keyframes orb-float {{
        0%, 100% {{ transform: translate(0, 0); }}
        50% {{ transform: translate(30px, -40px); }}
      }}

      @keyframes orb-float-reverse {{
        0%, 100% {{ transform: translate(0, 0); }}
        50% {{ transform: translate(-30px, 40px); }}
      }}

      .design4-hero-content {{
        position: relative;
        z-index: 2;
        text-align: center;
      }}

      .design4-hero-content h1 {{
        font-size: clamp(2.2rem, 5vw, 3.5rem);
        font-weight: 800;
        margin: 0 0 1rem 0;
        font-family: 'Source Serif 4', Georgia, serif;
        background: linear-gradient(135deg, #10b981, #0ea5e9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }}

      .design4-hero-content p {{
        font-size: clamp(1rem, 2.5vw, 1.2rem);
        opacity: 0.9;
        margin: 0 0 2rem 0;
      }}

      .design4-badge {{
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #10b981;
        padding: 0.5rem 1.25rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 1.5rem;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
        animation: neon-pulse 2s ease-in-out infinite;
      }}

      @keyframes neon-pulse {{
        0%, 100% {{
          box-shadow: 0 0 20px rgba(16, 185, 129, 0.3),
                      0 0 40px rgba(16, 185, 129, 0.2);
        }}
        50% {{
          box-shadow: 0 0 30px rgba(16, 185, 129, 0.5),
                      0 0 60px rgba(16, 185, 129, 0.3);
        }}
      }}

      .design4-cards-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 2rem;
        margin-top: 3rem;
      }}

      .design4-glass-card {{
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1.5px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 2rem;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      }}

      .design4-glass-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg,
          rgba(16, 185, 129, 0) 0%,
          rgba(16, 185, 129, 0.1) 50%,
          rgba(14, 165, 233, 0) 100%
        );
        opacity: 0;
        transition: opacity 0.4s ease;
        border-radius: 16px;
        z-index: 0;
      }}

      .design4-glass-card:hover {{
        transform: translateY(-8px);
        border-color: rgba(16, 185, 129, 0.6);
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.25),
                    0 0 60px rgba(16, 185, 129, 0.12),
                    0 12px 48px rgba(0, 0, 0, 0.2);
      }}

      .design4-glass-card:hover::before {{
        opacity: 1;
      }}

      .design4-card-content {{
        position: relative;
        z-index: 1;
      }}

      .design4-card-icon {{
        font-size: 3.2rem;
        margin-bottom: 1.25rem;
        display: inline-block;
        animation: icon-float 3s ease-in-out infinite;
      }}

      @keyframes icon-float {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-8px); }}
      }}

      .design4-glass-card:hover .design4-card-icon {{
        animation: icon-float-hover 0.6s ease-out forwards;
      }}

      @keyframes icon-float-hover {{
        to {{ transform: translateY(-12px) scale(1.1); }}
      }}

      .design4-card-title {{
        font-size: 1.35rem;
        font-weight: 700;
        margin: 0 0 0.75rem 0;
        font-family: 'Source Serif 4', Georgia, serif;
        background: linear-gradient(135deg, #10b981, #0ea5e9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        transition: all 0.3s ease;
      }}

      .design4-card-description {{
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.95rem;
        line-height: 1.65;
        margin: 0;
      }}

      .design4-card-metric {{
        margin-top: 1.25rem;
        padding-top: 1.25rem;
        border-top: 1px solid rgba(16, 185, 129, 0.2);
      }}

      .design4-card-metric-value {{
        font-size: 2.2rem;
        font-weight: 800;
        color: #10b981;
        font-family: 'Source Serif 4', Georgia, serif;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
      }}

      .design4-card-metric-label {{
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
        margin-top: 0.4rem;
      }}

      .design4-progress-bar {{
        width: 100%;
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        margin-top: 1.25rem;
        overflow: hidden;
      }}

      .design4-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, #10b981, #0ea5e9);
        border-radius: 2px;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
      }}

      @media (max-width: 768px) {{
        .design4-dark-bg {{
          padding: 2rem 1.25rem;
        }}
        .design4-hero-content h1 {{
          font-size: 2rem;
        }}
        .design4-cards-container {{
          grid-template-columns: 1fr;
          gap: 1.5rem;
        }}
      }}

      @media (prefers-reduced-motion: reduce) {{
        .design4-dark-bg::before,
        .design4-dark-bg::after,
        .design4-badge,
        .design4-card-icon {{
          animation: none !important;
        }}
      }}
    </style>

    <div class="design4-dark-bg">
      <div class="design4-hero-content">
        <div class="design4-badge">{badge_text}</div>
        <h1>{titulo}</h1>
        <p>{subtitulo}</p>
      </div>
    </div>

    <div class="design4-cards-container">
      {cards_html}
    </div>
    """

    return html


# ==============================================================================
# Componentes Reutilizáveis Genéricos
# ==============================================================================

def card_moderno(
    titulo: str,
    descricao: str,
    icone: str,
    cor_primaria: str = "#10b981",
    metrica: Optional[Dict[str, str]] = None,
    design_style: Literal["design1", "design4"] = "design1"
) -> str:
    """
    Card moderno reutilizável com suporte a múltiplos designs.

    Args:
        titulo: Título do card
        descricao: Descrição/conteúdo
        icone: Emoji (ex: "🏙️")
        cor_primaria: Cor hex (default: emerald)
        metrica: Dict {"valor": "17", "label": "Classes"}
        design_style: "design1" ou "design4"

    Returns:
        HTML string
    """

    metric_html = ""
    if metrica:
        metric_html = f"""
        <div class="card-moderno-metric">
          <div class="card-moderno-metric-val">{metrica['valor']}</div>
          <div class="card-moderno-metric-label">{metrica['label']}</div>
        </div>
        """

    html = f"""
    <style>
      .card-moderno {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
      }}
      .card-moderno:hover {{
        transform: translateY(-5px);
        box-shadow: var(--shadow-md);
      }}
      .card-moderno-icon {{
        font-size: 2.5rem;
        margin-bottom: 1rem;
      }}
      .card-moderno-title {{
        color: {cor_primaria};
        font-weight: 700;
        font-size: 1.25rem;
        margin: 0 0 0.75rem 0;
        font-family: 'Source Serif 4', Georgia, serif;
      }}
      .card-moderno-desc {{
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin: 0;
        line-height: 1.6;
      }}
      .card-moderno-metric {{
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
      }}
      .card-moderno-metric-val {{
        font-size: 2rem;
        font-weight: 800;
        color: {cor_primaria};
        font-family: 'Source Serif 4', Georgia, serif;
      }}
      .card-moderno-metric-label {{
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        font-weight: 600;
      }}
    </style>

    <div class="card-moderno">
      <div class="card-moderno-icon">{icone}</div>
      <h3 class="card-moderno-title">{titulo}</h3>
      <p class="card-moderno-desc">{descricao}</p>
      {metric_html}
    </div>
    """

    return html


def metric_card_animado(
    numero: str,
    unidade: str,
    descricao: str,
    cor: str = "#10b981",
    icone: str = "📊"
) -> str:
    """
    Métrica com número grande, unidade e barra de progresso animada.
    """

    html = f"""
    <style>
      .metric-card-anim {{
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
      }}
      .metric-card-anim:hover {{
        transform: scale(1.05);
        box-shadow: var(--shadow-md);
      }}
      .metric-icon {{ font-size: 2.5rem; margin-bottom: 1rem; }}
      .metric-number {{
        font-size: 3rem;
        font-weight: 800;
        color: {cor};
        margin: 0;
        font-family: 'Source Serif 4', Georgia, serif;
      }}
      .metric-unit {{
        font-size: 1rem;
        color: var(--text-muted);
        margin: 0;
      }}
      .metric-desc {{
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-top: 1rem;
      }}
      .metric-progress {{
        width: 100%;
        height: 3px;
        background: var(--border-color);
        border-radius: 2px;
        margin-top: 1rem;
        overflow: hidden;
      }}
      .metric-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, {cor}, #0ea5e9);
        width: 75%;
        border-radius: 2px;
        animation: progress-load 1.2s ease-out;
      }}
      @keyframes progress-load {{
        from {{ width: 0; }}
        to {{ width: 75%; }}
      }}
    </style>

    <div class="metric-card-anim">
      <div class="metric-icon">{icone}</div>
      <p class="metric-number">{numero}</p>
      <p class="metric-unit">{unidade}</p>
      <p class="metric-desc">{descricao}</p>
      <div class="metric-progress">
        <div class="metric-progress-fill"></div>
      </div>
    </div>
    """

    return html


# ==============================================================================
# Exemplo de Uso (para teste)
# ==============================================================================

if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(layout="wide")

    st.title("UI Components Modern — Previews")

    # Design 1
    st.subheading("Design 1: Gradient Hero + Floating Cards")
    st.markdown(design1_hero_cards(), unsafe_allow_html=True)

    st.markdown("---")

    # Design 2
    st.subheading("Design 2: Timeline Interativa")
    st.markdown(design2_timeline_steps(current_step=2), unsafe_allow_html=True)

    st.markdown("---")

    # Design 4 (RECOMENDADO)
    st.subheading("Design 4: Glassmorphism Premium (RECOMENDADO)")
    st.markdown(design4_glassmorphism_premium(), unsafe_allow_html=True)

    st.markdown("---")

    # Componentes genéricos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            card_moderno(
                titulo="Teste Card",
                descricao="Componente reutilizável",
                icone="🧪",
                metrica={"valor": "100%", "label": "Funcional"}
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            metric_card_animado(
                numero="17",
                unidade="Classes",
                descricao="De LCZ",
                icone="🏙️"
            ),
            unsafe_allow_html=True
        )
