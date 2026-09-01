# modules/investigar.py

import os

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from shapely.geometry import Polygon
from utils import processamento
from utils.navegacao import ir_para
from utils.ui import renderizar_cabecalho_modulo

CENTRO_CIDADE = {
    "São Paulo": [-23.55, -46.63],
    "Juiz de Fora": [-21.76, -43.35],
}


def _ler_exemplo_csv(cidade: str) -> str:
    nome_arquivo = processamento.CIDADES_BASE[cidade]["exemplo_csv"]
    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), nome_arquivo)
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def renderizar_pagina():
    """Renderiza a página do módulo Investigar."""

    renderizar_cabecalho_modulo(
        "Módulo Investigar",
        "Carregue seus dados de campo e defina uma área de interesse para análise",
        icone="investigate",
    )

    if 'dados_usuario' not in st.session_state:
        st.session_state['dados_usuario'] = None
    if 'area_de_interesse' not in st.session_state:
        st.session_state['area_de_interesse'] = None

    cidade_selecionada = st.selectbox(
        "Cidade de referência para as Zonas Climáticas Locais",
        list(processamento.CIDADES_BASE.keys()),
        index=list(processamento.CIDADES_BASE.keys()).index(st.session_state.cidade_base),
        help="Define qual mapa de LCZ é usado para cruzar com seus dados no módulo Visualizar, "
             "e qual exemplo de CSV é oferecido abaixo. Escolha a cidade dos seus pontos de campo.",
    )
    if cidade_selecionada != st.session_state.cidade_base:
        st.session_state.cidade_base = cidade_selecionada
        st.session_state['dados_usuario'] = None
        st.session_state['area_de_interesse'] = None
        st.rerun()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("##### 1. Carregue seus dados de campo")

        arquivo_csv = st.file_uploader(
            "Arquivo .csv com latitude, longitude e valor medido",
            type="csv",
            help="Meça em condições comparáveis (mesmo período do dia, sem chuva/vento forte) "
                 "para poder comparar os pontos entre si.",
        )

        with st.expander("Formato do arquivo e exemplo"):
            st.markdown(
                "Colunas aceitas (o nome pode variar): **latitude** (lat), **longitude** (lon/lng) "
                "e **valor medido** (valor, temp, temperatura, medida, value)."
            )
            exemplo_csv = _ler_exemplo_csv(st.session_state.cidade_base)
            st.code(exemplo_csv, language="csv")
            st.download_button(
                f"📥 Baixar exemplo CSV ({st.session_state.cidade_base})",
                exemplo_csv,
                f"exemplo_dados_{st.session_state.cidade_base.lower().replace(' ', '_')}.csv",
                "text/csv",
            )

        if arquivo_csv:
            with st.spinner("Processando arquivo..."):
                gdf_pontos, erro = processamento.validar_e_processar_csv(arquivo_csv)

            if erro:
                st.error(erro)
                st.session_state['dados_usuario'] = None
            else:
                st.session_state['dados_usuario'] = gdf_pontos
                st.success(
                    f"{len(gdf_pontos)} pontos carregados. Valor médio "
                    f"{gdf_pontos['valor'].mean():.1f}, de {gdf_pontos['valor'].min():.1f} "
                    f"a {gdf_pontos['valor'].max():.1f}."
                )
                with st.expander("Ver dados carregados"):
                    st.dataframe(gdf_pontos.drop(columns='geometry').head(10), use_container_width=True)

        st.markdown("##### 2. Desenhe sua área de interesse")
        st.caption("Use a ferramenta de polígono (canto superior esquerdo do mapa) para marcar o contorno da área.")

        m = folium.Map(
            location=CENTRO_CIDADE.get(st.session_state.cidade_base, [-23.55, -46.63]),
            zoom_start=11, tiles="OpenStreetMap",
        )
        Draw(
            export=False,
            draw_options={
                'polygon': {'showArea': True, 'metric': True},
                'rectangle': {'showArea': True, 'metric': True},
                'circle': False, 'marker': False, 'circlemarker': False, 'polyline': False,
            },
            edit_options={'edit': True},
        ).add_to(m)

        if st.session_state['dados_usuario'] is not None:
            for _, row in st.session_state['dados_usuario'].iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=6, popup=f"Valor: {row['valor']:.2f}",
                    color='red', fill=True, fillColor='red', fillOpacity=0.7,
                ).add_to(m)

        map_data = st_folium(m, width=None, height=460, returned_objects=["all_drawings"], key="investigar_map")

        if map_data and map_data.get("all_drawings"):
            area_desenhada = map_data["all_drawings"][-1]['geometry']
            st.session_state['area_de_interesse'] = area_desenhada

            if area_desenhada['type'] == 'Polygon':
                # Conversão aproximada grau -> km² (suficiente para dar uma ideia de escala,
                # não para uso técnico — WGS84 não é uma projeção equivalente de área).
                area_km2 = Polygon(area_desenhada['coordinates'][0]).area * 111 * 111
                st.success(f"Área de interesse definida (~{area_km2:.2f} km²).")
            else:
                st.success("Área de interesse definida.")

    with col2:
        st.markdown("##### Status")
        st.write("✅ Dados carregados" if st.session_state['dados_usuario'] is not None else "⏳ Aguardando dados")
        st.write("✅ Área definida" if st.session_state['area_de_interesse'] is not None else "⏳ Aguardando área")

        st.divider()
        st.markdown("##### 3. Executar análise")

        pode_analisar = (
            st.session_state['dados_usuario'] is not None or st.session_state['area_de_interesse'] is not None
        )
        if not pode_analisar:
            st.caption("Carregue dados e/ou defina uma área para habilitar a análise.")

        if st.button("🔍 Executar Análise", type="primary", disabled=not pode_analisar, use_container_width=True):
            st.session_state['analise_pronta'] = True

        if st.session_state.get('analise_pronta'):
            st.success("Pronto! O cruzamento com as Zonas Climáticas Locais acontece no módulo Visualizar.")
            if st.button("📊 Ir para Visualizar", use_container_width=True):
                ir_para("Visualizar")
