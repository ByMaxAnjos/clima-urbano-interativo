# modules/investigar.py

import json
import os

import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from shapely.geometry import Point
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
    if 'metadados_observacao' not in st.session_state:
        st.session_state['metadados_observacao'] = {}

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
                "e **valor medido** (valor, temp, temperatura, medida, value). Separador `,` ou `;` "
                "e vírgula ou ponto decimal são aceitos automaticamente."
            )
            st.caption(
                "🔎 **Origem do exemplo:** dado demonstrativo, não medição de campo real "
                "(ver `data/README.md`)."
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
                gdf_pontos, erro, info = processamento.validar_e_processar_csv(arquivo_csv)

            lat_auto, lon_auto, val_auto = info["colunas_detectadas"]
            colunas_nao_detectadas = lat_auto is None or lon_auto is None or val_auto is None

            if colunas_nao_detectadas:
                st.error(erro)
                st.caption("Selecione manualmente as colunas correspondentes:")
                colunas_arquivo = list(processamento.ler_csv_tolerante(arquivo_csv)[0].columns)
                col_a, col_b, col_c = st.columns(3)
                lat_manual = col_a.selectbox("Latitude", colunas_arquivo, index=colunas_arquivo.index(lat_auto) if lat_auto in colunas_arquivo else 0, key="col_lat")
                lon_manual = col_b.selectbox("Longitude", colunas_arquivo, index=colunas_arquivo.index(lon_auto) if lon_auto in colunas_arquivo else 0, key="col_lon")
                val_manual = col_c.selectbox("Valor", colunas_arquivo, index=colunas_arquivo.index(val_auto) if val_auto in colunas_arquivo else 0, key="col_val")
                if st.button("Usar estas colunas"):
                    gdf_pontos, erro, info = processamento.validar_e_processar_csv(
                        arquivo_csv, lat_col=lat_manual, lon_col=lon_manual, val_col=val_manual
                    )
                else:
                    gdf_pontos = None
            elif erro:
                st.error(erro)

            if gdf_pontos is not None:
                st.session_state['dados_usuario'] = gdf_pontos
                st.success(
                    f"{len(gdf_pontos)} pontos carregados. Valor médio "
                    f"{gdf_pontos['valor'].mean():.1f}, de {gdf_pontos['valor'].min():.1f} "
                    f"a {gdf_pontos['valor'].max():.1f}."
                )
                if info["problemas_linha"]:
                    with st.expander(f"⚠️ {len(info['problemas_linha'])} linha(s) descartada(s) — ver motivo"):
                        for numero_linha, motivos in info["problemas_linha"]:
                            st.write(f"Linha {numero_linha}: {', '.join(motivos)}")
                with st.expander("Ver dados carregados"):
                    st.dataframe(gdf_pontos.drop(columns='geometry').head(10), use_container_width=True)
            elif not erro:
                st.session_state['dados_usuario'] = None

        with st.expander("📋 Metadados da observação (opcional, recomendado)"):
            st.caption("Registrar isso ajuda a interpretar os dados depois e a comparar com outras turmas/medições.")
            meta = st.session_state['metadados_observacao']
            col_m1, col_m2 = st.columns(2)
            meta['variavel'] = col_m1.text_input("Variável medida", value=meta.get('variavel', ''), placeholder="Ex: temperatura do ar")
            meta['unidade'] = col_m2.text_input("Unidade", value=meta.get('unidade', ''), placeholder="Ex: °C")
            meta['origem'] = col_m1.selectbox("Origem", ["Medição própria (campo)", "Fonte externa/terceiros"], index=0 if meta.get('origem', 'Medição própria (campo)') == "Medição própria (campo)" else 1)
            meta['instrumento'] = col_m2.text_input("Instrumento", value=meta.get('instrumento', ''), placeholder="Ex: termômetro digital, sensor DHT22")
            meta['data'] = col_m1.text_input("Data da coleta", value=meta.get('data', ''), placeholder="AAAA-MM-DD")
            meta['horario'] = col_m2.text_input("Horário da coleta", value=meta.get('horario', ''), placeholder="Ex: 14:00")
            st.session_state['metadados_observacao'] = meta

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
                area_km2 = processamento.calcular_area_poligono_m2(area_desenhada) / 1_000_000
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

    st.divider()
    _renderizar_projeto()


def _renderizar_projeto():
    """Permite salvar o estado atual (dados, área, metadados, cenários) num arquivo
    JSON para reabrir em outra aula, e recarregar um projeto salvo anteriormente."""
    st.markdown("##### 💾 Salvar/reabrir projeto entre aulas")
    col_salvar, col_carregar = st.columns(2)

    with col_salvar:
        dados = st.session_state.get('dados_usuario')
        projeto = {
            "cidade_base": st.session_state.get('cidade_base'),
            "area_de_interesse": st.session_state.get('area_de_interesse'),
            "metadados_observacao": st.session_state.get('metadados_observacao', {}),
            "dados_usuario": dados.drop(columns='geometry').to_dict('records') if dados is not None else None,
            "cenarios": st.session_state.get('cenarios', {}),
        }
        st.download_button(
            "📥 Salvar projeto (.json)",
            json.dumps(projeto, indent=2, default=str),
            "projeto_clima_urbano.json",
            "application/json",
            use_container_width=True,
        )

    with col_carregar:
        arquivo_projeto = st.file_uploader("📂 Reabrir projeto (.json)", type="json", key="upload_projeto")
        if arquivo_projeto and st.button("Carregar projeto", use_container_width=True):
            try:
                projeto = json.load(arquivo_projeto)
                if projeto.get("cidade_base") in processamento.CIDADES_BASE:
                    st.session_state['cidade_base'] = projeto["cidade_base"]
                st.session_state['area_de_interesse'] = projeto.get("area_de_interesse")
                st.session_state['metadados_observacao'] = projeto.get("metadados_observacao", {})
                st.session_state['cenarios'] = projeto.get("cenarios", {})
                if projeto.get("dados_usuario"):
                    df = pd.DataFrame(projeto["dados_usuario"])
                    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
                    st.session_state['dados_usuario'] = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
                else:
                    st.session_state['dados_usuario'] = None
                st.success("Projeto carregado.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao carregar projeto: {e}")
