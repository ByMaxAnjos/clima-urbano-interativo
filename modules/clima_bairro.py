# modules/clima_bairro.py
"""
Módulo Clima de Bairro.

Amarra os módulos existentes (Explorar, Investigar, Visualizar, Simular) num
roteiro guiado de investigação escolar/comunitária do clima do bairro, seguindo
a proposta descrita em proposta_resumo_eregeo_clima_de_bairro.md: usar a
plataforma como primeira ferramenta de aproximação, seguida de trabalho de
campo, percepção social e devolutiva comunitária.
"""

from datetime import datetime

import streamlit as st

from utils import processamento
from utils.glossario import renderizar_entenda_dados
from utils.navegacao import ir_para

ETAPAS = [
    "Aproximação pela plataforma",
    "Delimitação do bairro/área de estudo",
    "Trabalho de campo escolar",
    "Integração dos dados na plataforma",
    "Percepção, debate e devolutiva",
]

ROTEIRO_CAMPO_MD = """# Roteiro de Campo — Clima de Bairro

## Antes de sair
- Escolha pontos contrastantes: pátio escolar, rua sem sombra, rua arborizada,
  praça, ponto de ônibus, área comercial, quadra esportiva, encosta ou fundo de vale.
- Anote a **data e o horário** — meça os pontos em condições comparáveis
  (mesmo período do dia, evitando chuva/vento forte), pois isso afeta a comparação.
- Leve termohigrômetro (se houver), celular com GPS, planilha ou aplicativo de anotação.

## Em cada ponto, registre
- Latitude e longitude (ou nome do local + referência)
- Horário da medição
- Temperatura do ar e umidade relativa (se houver instrumento)
- Tipo de superfície (asfalto, terra, grama, concreto...)
- Presença de sombra (sim/não, de árvore ou construção)
- Intensidade de tráfego percebida (baixa/média/alta)
- Vento percebido (calmo/moderado/forte)
- Uma foto do local
- Uma frase sobre a sensação térmica (conforto/desconforto)

## Depois
Organize os dados em uma planilha CSV com colunas de **latitude**, **longitude**
e **temperatura** (ou outro valor medido) — esse é o formato que o módulo
**Investigar** espera para o upload.
"""


def _inicializar_estado():
    if "clima_bairro_etapas" not in st.session_state:
        st.session_state.clima_bairro_etapas = {etapa: False for etapa in ETAPAS}
    if "clima_bairro_percepcao" not in st.session_state:
        st.session_state.clima_bairro_percepcao = {
            "lugares_quentes": "",
            "lugares_frescos": "",
            "trajetos": "",
            "sugestoes": "",
        }


def renderizar_pagina():
    """Renderiza o módulo Clima de Bairro."""
    _inicializar_estado()

    st.markdown("""
    <div class="module-header">
        <h2>🏘️ Clima de Bairro</h2>
        <p>Um roteiro guiado para estudar o clima do bairro da escola — do mapa ao campo, do dado à comunidade.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "**Clima de bairro** é uma escala intermediária entre o clima da cidade inteira e o "
        "microclima de um único ponto: a rua da escola, a quadra sem sombra, a praça arborizada, "
        "o trajeto cotidiano. Esta seção organiza as cinco etapas de uma investigação de clima de "
        "bairro, conectando os módulos **Explorar**, **Investigar**, **Visualizar** e **Simular** "
        "num único fluxo, do jeito que ele é usado numa turma ou num grupo comunitário."
    )
    renderizar_entenda_dados(
        termos=["LCZ (Zona Climática Local)", "Ilha de calor do ar (dossel)", "Ilha de calor de superfície (LST)"],
        titulo="🔍 Antes de começar: entenda os termos"
    )

    concluidas = sum(st.session_state.clima_bairro_etapas.values())
    st.progress(concluidas / len(ETAPAS), text=f"{concluidas}/{len(ETAPAS)} etapas marcadas como concluídas")

    # --- Etapa 1 ---
    with st.expander(f"**1. {ETAPAS[0]}**", expanded=not st.session_state.clima_bairro_etapas[ETAPAS[0]]):
        st.markdown(
            "Gere ou visualize o mapa de Zonas Climáticas Locais do entorno da escola no módulo "
            "**Explorar**. A turma identifica classes construídas e de cobertura de terreno, áreas "
            "mais impermeabilizadas e manchas de vegetação, e formula hipóteses — por exemplo: "
            "*'as ruas com pouca arborização serão mais quentes?'*, *'o pátio da escola se comporta "
            "como ilha de calor?'*"
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🌍 Ir para Explorar", key="ir_explorar", use_container_width=True):
                ir_para("Explorar")
        with col2:
            st.session_state.clima_bairro_etapas[ETAPAS[0]] = st.checkbox(
                "Marcar etapa como concluída", value=st.session_state.clima_bairro_etapas[ETAPAS[0]],
                key="check_etapa_1"
            )

    # --- Etapa 2 ---
    with st.expander(f"**2. {ETAPAS[1]}**", expanded=not st.session_state.clima_bairro_etapas[ETAPAS[1]]):
        st.markdown(
            "Defina um recorte caminhável e pedagogicamente viável: entorno imediato da escola, "
            "raio de 500 m a 1 km, ou conjunto de ruas frequentadas pelos estudantes. Desenhe essa "
            "área no mapa do módulo **Investigar** (ferramenta de desenho de polígono)."
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✏️ Ir para Investigar (delimitar área)", key="ir_investigar_area", use_container_width=True):
                ir_para("Investigar")
        with col2:
            st.session_state.clima_bairro_etapas[ETAPAS[1]] = st.checkbox(
                "Marcar etapa como concluída", value=st.session_state.clima_bairro_etapas[ETAPAS[1]],
                key="check_etapa_2"
            )
        if st.session_state.get("area_de_interesse"):
            st.success("✅ Já existe uma área de interesse desenhada nesta sessão.")

    # --- Etapa 3 ---
    with st.expander(f"**3. {ETAPAS[2]}**", expanded=not st.session_state.clima_bairro_etapas[ETAPAS[2]]):
        st.markdown(
            "Colete dados em pontos contrastantes do bairro (pátio, rua arborizada, rua exposta, "
            "praça, ponto de ônibus...). Baixe o roteiro abaixo para orientar a turma em campo."
        )
        st.download_button(
            "📥 Baixar Roteiro de Campo (Markdown)",
            data=ROTEIRO_CAMPO_MD,
            file_name="roteiro_campo_clima_de_bairro.md",
            mime="text/markdown",
            key="download_roteiro"
        )
        st.session_state.clima_bairro_etapas[ETAPAS[2]] = st.checkbox(
            "Marcar etapa como concluída", value=st.session_state.clima_bairro_etapas[ETAPAS[2]],
            key="check_etapa_3"
        )

    # --- Etapa 4 ---
    with st.expander(f"**4. {ETAPAS[3]}**", expanded=not st.session_state.clima_bairro_etapas[ETAPAS[3]]):
        st.markdown(
            "Organize os dados coletados em uma planilha CSV com latitude, longitude e o valor "
            "medido, carregue-a no módulo **Investigar**, e compare médias e distribuição por "
            "LCZ no módulo **Visualizar**. O módulo **Simular** pode ser usado para discutir "
            "cenários: mais árvores no pátio, pavimento permeável, telhado verde, pintura clara."
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 Investigar (upload CSV)", key="ir_investigar_csv", use_container_width=True):
                ir_para("Investigar")
        with col2:
            if st.button("📊 Visualizar", key="ir_visualizar", use_container_width=True):
                ir_para("Visualizar")
        with col3:
            if st.button("🧪 Simular", key="ir_simular", use_container_width=True):
                ir_para("Simular")
        st.session_state.clima_bairro_etapas[ETAPAS[3]] = st.checkbox(
            "Marcar etapa como concluída", value=st.session_state.clima_bairro_etapas[ETAPAS[3]],
            key="check_etapa_4"
        )

    # --- Etapa 5 ---
    with st.expander(f"**5. {ETAPAS[4]}**", expanded=not st.session_state.clima_bairro_etapas[ETAPAS[4]]):
        st.markdown(
            "Reúna a percepção de estudantes, professores e moradores — lugares mais quentes/frios, "
            "trajetos cotidianos, efeitos na saúde, sugestões de melhoria. Registre abaixo para gerar "
            "uma devolutiva simples para a comunidade escolar."
        )
        percepcao = st.session_state.clima_bairro_percepcao
        percepcao["lugares_quentes"] = st.text_area(
            "Lugares mais quentes/desconfortáveis (relatados pela turma)",
            value=percepcao["lugares_quentes"], key="perc_quentes"
        )
        percepcao["lugares_frescos"] = st.text_area(
            "Lugares mais frescos/agradáveis", value=percepcao["lugares_frescos"], key="perc_frescos"
        )
        percepcao["trajetos"] = st.text_area(
            "Trajetos cotidianos afetados pelo calor", value=percepcao["trajetos"], key="perc_trajetos"
        )
        percepcao["sugestoes"] = st.text_area(
            "Sugestões de intervenção da turma/comunidade", value=percepcao["sugestoes"], key="perc_sugestoes"
        )

        devolutiva = _gerar_devolutiva(percepcao)
        st.download_button(
            "📥 Baixar Devolutiva Comunitária (Markdown)",
            data=devolutiva,
            file_name="devolutiva_clima_de_bairro.md",
            mime="text/markdown",
            key="download_devolutiva"
        )
        st.session_state.clima_bairro_etapas[ETAPAS[4]] = st.checkbox(
            "Marcar etapa como concluída", value=st.session_state.clima_bairro_etapas[ETAPAS[4]],
            key="check_etapa_5"
        )

    if concluidas == len(ETAPAS):
        st.success("🎉 As cinco etapas do roteiro de Clima de Bairro foram concluídas!")


def _gerar_devolutiva(percepcao: dict) -> str:
    """Monta um documento simples de devolutiva comunitária, combinando dados já
    coletados na sessão (área/pontos, se existirem) com a percepção social registrada.
    Usa linguagem acessível, evitando jargão técnico, por ser destinado à comunidade escolar.
    """
    dados_usuario = st.session_state.get("dados_usuario")
    gdf_zcl_base, _ = st.session_state.get("dados_base", (None, None))
    area_de_interesse_geojson = st.session_state.get("area_de_interesse")

    linhas = [
        "# Devolutiva Comunitária — Clima do Nosso Bairro",
        f"\n*Produzido em {datetime.now().strftime('%d/%m/%Y')}*\n",
        "## O que estudamos",
        (
            "Usamos mapas e medições simples para entender onde o nosso bairro fica mais quente "
            "ou mais fresco, e como isso se relaciona com sombra, vegetação e o tipo de construção "
            "ao redor.\n"
        ),
    ]

    if area_de_interesse_geojson and gdf_zcl_base is not None:
        zcl_na_area = processamento.filtrar_dados_por_area(gdf_zcl_base, area_de_interesse_geojson)
        if not zcl_na_area.empty:
            stats = processamento.calcular_estatisticas_area(zcl_na_area)
            if stats and stats.get("composicao"):
                classe_dominante = max(stats["composicao"], key=lambda c: c["percentual"])
                linhas.append(
                    f"## O que os mapas mostram\nA área estudada é dominada pela classe "
                    f"**{classe_dominante['zcl_classe']}** ({classe_dominante['percentual']:.0f}% da área).\n"
                )

    if dados_usuario is not None and gdf_zcl_base is not None:
        pontos_na_area = (
            processamento.filtrar_dados_por_area(dados_usuario, area_de_interesse_geojson)
            if area_de_interesse_geojson else dados_usuario
        )
        if not pontos_na_area.empty:
            pontos_com_zcl = processamento.juntar_dados_espaciais(pontos_na_area, gdf_zcl_base)
            pontos_com_zcl = pontos_com_zcl.dropna(subset=["valor"])
            if not pontos_com_zcl.empty:
                linhas.append(
                    f"## O que medimos em campo\nForam analisados **{len(pontos_com_zcl)} pontos**, "
                    f"com valor médio de **{pontos_com_zcl['valor'].mean():.1f}** e variação entre "
                    f"{pontos_com_zcl['valor'].min():.1f} e {pontos_com_zcl['valor'].max():.1f}.\n"
                )

    linhas.append("## O que a comunidade percebe")
    if percepcao.get("lugares_quentes"):
        linhas.append(f"**Lugares mais quentes/desconfortáveis:** {percepcao['lugares_quentes']}\n")
    if percepcao.get("lugares_frescos"):
        linhas.append(f"**Lugares mais frescos/agradáveis:** {percepcao['lugares_frescos']}\n")
    if percepcao.get("trajetos"):
        linhas.append(f"**Trajetos cotidianos afetados pelo calor:** {percepcao['trajetos']}\n")
    if percepcao.get("sugestoes"):
        linhas.append(f"**Sugestões da turma/comunidade:** {percepcao['sugestoes']}\n")

    linhas.append(
        "\n---\n*Este material foi produzido com a Plataforma Interativa de Clima Urbano como "
        "parte de uma investigação escolar/comunitária de clima de bairro. Os resultados são "
        "preliminares e dependem da quantidade de dados coletados — servem para iniciar a "
        "conversa sobre o bairro, não como diagnóstico técnico definitivo.*"
    )

    return "\n".join(linhas)
