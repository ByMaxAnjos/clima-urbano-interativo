# utils/ui.py
"""Componentes de UI compartilhados entre os módulos da plataforma."""

import streamlit as st
import os


ICON_PATHS = {
    "brand": '<path d="M15 18V9h4v9M22 18V5h4v13M29 18v-7h4v7M36 18V3h5v15"/><path d="M12 21c8-4 15-5 23-3 5 1 9 0 14-3"/><path d="M34 12c5 0 9 3 10 7-5 1-9-1-11-4-1-1 0-2 1-3Z"/>',
    "overview": '<circle cx="32" cy="32" r="20"/><path d="M32 18v28M18 32h28M23 23l18 18M41 23 23 41"/><circle cx="32" cy="32" r="4" fill="currentColor" stroke="none"/>',
    "start": '<path d="M17 13h25a5 5 0 0 1 5 5v28H22a5 5 0 0 1-5-5V13Z"/><path d="m27 25 12 7-12 7V25Z"/><path d="M17 19h-5v28a5 5 0 0 0 5 5h24"/>',
    "explore": '<circle cx="28" cy="28" r="15"/><path d="m39 39 11 11M28 18v20M18 28h20"/><path d="m25 31 4-8 4 8-4 4-4-4Z"/>',
    "investigate": '<circle cx="27" cy="27" r="14"/><path d="m37 37 12 12M27 20v14M20 27h14"/><path d="M15 49h18"/>',
    "visualize": '<path d="M15 48V34h8v14M28 48V22h8v26M41 48V12h8v36"/><path d="M11 50h42M14 27l11-8 8 4 15-13"/>',
    "simulate": '<path d="M15 16h34M15 32h34M15 48h34"/><circle cx="25" cy="16" r="4"/><circle cx="40" cy="32" r="4"/><circle cx="31" cy="48" r="4"/>',
    "neighborhood": '<path d="m13 29 19-16 19 16v21H13V29Z"/><path d="M25 50V37h14v13M9 50h46M45 13c5 2 8 6 8 11-5 0-9-3-10-7 0-2 0-3 2-4Z"/>',
    "resources": '<path d="M14 14h15a6 6 0 0 1 6 6v28H20a6 6 0 0 0-6 6V14ZM50 14H35a6 6 0 0 0-6 6v28h15a6 6 0 0 1 6 6V14Z"/><path d="M20 25h9M20 32h9"/>',
    "evaluation": '<rect x="16" y="13" width="32" height="38" rx="3"/><path d="M24 13v-3h16v3M23 25h18M23 33h18M23 41h10M24 25l2 2 4-5"/>',
    "info": '<circle cx="32" cy="32" r="21"/><path d="M32 28v14M32 20v2M21 49 16 55h32l-5-6"/>',
}

MODULE_ANIMATIONS = {
    "explore": '''<svg viewBox="0 0 220 150" class="module-animation-svg" aria-hidden="true">
        <path class="anim-map-line" d="M18 27h184M18 51h184M18 75h184M18 99h184M18 123h184M40 12v126M76 12v126M112 12v126M148 12v126M184 12v126"/>
        <path class="anim-map-route" d="M28 112c30-38 47 4 75-35s43 8 88-43"/>
        <circle class="anim-pulse" cx="103" cy="78" r="12"/><path class="anim-pin" d="M103 67c-8 0-13 5-13 12 0 10 13 22 13 22s13-12 13-22c0-7-5-12-13-12Z"/><circle cx="103" cy="79" r="4"/>
    </svg>''',
    "investigate": '''<svg viewBox="0 0 220 150" class="module-animation-svg" aria-hidden="true">
        <path class="anim-field" d="M28 111c26-44 45-25 68-54 22-28 44 5 96-29"/>
        <circle class="anim-point p1" cx="40" cy="96" r="5"/><circle class="anim-point p2" cx="82" cy="75" r="5"/><circle class="anim-point p3" cx="114" cy="54" r="5"/><circle class="anim-point p4" cx="161" cy="53" r="5"/>
        <circle class="anim-lens" cx="151" cy="91" r="25"/><path class="anim-lens-handle" d="m169 109 25 25"/><path d="M140 91h22M151 80v22"/>
    </svg>''',
    "visualize": '''<svg viewBox="0 0 220 150" class="module-animation-svg" aria-hidden="true">
        <path class="anim-axis" d="M22 126h180M30 18v108"/>
        <rect class="anim-bar b1" x="48" y="83" width="18" height="43" rx="3"/><rect class="anim-bar b2" x="82" y="61" width="18" height="65" rx="3"/><rect class="anim-bar b3" x="116" y="42" width="18" height="84" rx="3"/><rect class="anim-bar b4" x="150" y="25" width="18" height="101" rx="3"/>
        <path class="anim-chart-line" d="M44 103 91 78l29 11 44-51"/><circle class="anim-chart-dot" cx="164" cy="38" r="5"/>
    </svg>''',
    "simulate": '''<svg viewBox="0 0 220 150" class="module-animation-svg" aria-hidden="true">
        <path class="anim-control" d="M28 39h164M28 75h164M28 111h164"/>
        <circle class="anim-knob k1" cx="78" cy="39" r="9"/><circle class="anim-knob k2" cx="145" cy="75" r="9"/><circle class="anim-knob k3" cx="105" cy="111" r="9"/>
        <path class="anim-thermo" d="M181 22v65a18 18 0 1 0 10 0V22a5 5 0 0 0-10 0Z"/><path class="anim-temp" d="M186 43v47"/><circle cx="186" cy="104" r="9" class="anim-temp-fill"/>
    </svg>''',
}


def icon_markup(label: str, size: str = "2.5rem", icon: str = "brand") -> str:
    """Retorna um ícone temático, acessível e sem dependências externas."""
    paths = ICON_PATHS.get(icon, ICON_PATHS["brand"])
    return (
        f'<svg class="platform-icon platform-icon--{icon}" viewBox="0 0 64 64" '
        f'role="img" aria-label="{label}" style="width:{size};height:{size};" '
        f'fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
        f'stroke-linejoin="round">{paths}</svg>'
    )


def renderizar_cabecalho_modulo(
    titulo: str,
    subtitulo: str,
    logo_base64: str | None = None,
    mostrar_marca: bool = True,
    icone: str = "brand",
):
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
    marca_html = icon_markup(titulo, icon=icone) if mostrar_marca else ""
    animation = MODULE_ANIMATIONS.get(icone, MODULE_ANIMATIONS["explore"])
    html = (
        '<div class="module-header">'
        '<div class="module-header-content">'
        f'<div class="module-header-copy">{logo_html}{marca_html}<div><h1>{titulo}</h1><p>{subtitulo}</p></div></div>'
        f'<div class="module-animation module-animation--{icone}">{animation}</div>'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)
