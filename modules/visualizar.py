# modules/visualizar.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from utils import processamento
from utils.lcz4r import CORES_LCZ
from utils.navegacao import ir_para
from utils.ui import renderizar_cabecalho_modulo

LCZ_ORDER = [f"LCZ {i}" for i in range(1, 11)] + [f"LCZ {letter}" for letter in "ABCDEFG"]
LCZ_URBANAS = {f"LCZ {i}" for i in range(1, 11)}


def _ordem_lcz_presentes(series):
    """Mantem a sequencia oficial LCZ e deixa classes inesperadas no final."""
    presentes = [classe for classe in LCZ_ORDER if classe in set(series.dropna())]
    extras = sorted(set(series.dropna()) - set(LCZ_ORDER))
    return presentes + extras


def _tipo_lcz(classe):
    return "Construida" if classe in LCZ_URBANAS else "Natural / cobertura"


def _layout_didatico(fig, titulo=None, altura=420, legenda=True):
    fig.update_layout(
        title=dict(text=titulo, x=0.02, xanchor="left") if titulo else None,
        height=altura,
        margin=dict(l=18, r=18, t=58 if titulo else 24, b=34),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.72)",
        font=dict(family="Arial, sans-serif", size=13, color="#163044"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title=None,
            font=dict(size=11),
        ),
        showlegend=legenda,
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.22)",
        zeroline=False,
        title_font=dict(size=12),
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
        title_font=dict(size=12),
        tickfont=dict(size=11),
    )
    return fig


def _adicionar_linha_media(fig, media, orientacao="h", rotulo="Média geral"):
    if orientacao == "h":
        fig.add_hline(
            y=media,
            line_dash="dot",
            line_color="#163044",
            annotation_text=f"{rotulo}: {media:.2f}",
            annotation_position="top left",
        )
    else:
        fig.add_vline(
            x=media,
            line_dash="dot",
            line_color="#163044",
            annotation_text=f"{rotulo}: {media:.2f}",
            annotation_position="top right",
        )


def renderizar_pagina():
    """Renderiza a página do módulo Visualizar."""
    
    renderizar_cabecalho_modulo(
        "Módulo Visualizar",
        "Explore gráficos e estatísticas detalhadas da sua análise",
        icone="visualize"
    )

    # Verificar se a análise foi executada
    if 'analise_pronta' not in st.session_state or not st.session_state.get('analise_pronta'):
        st.warning("""
        ⚠️ **Análise não encontrada**
        
        Para visualizar resultados, primeiro execute uma análise no módulo **Investigar**:
        1. Carregue seus dados de campo (CSV)
        2. Defina uma área de interesse no mapa
        3. Execute a análise
        """)
        
        if st.button("🔬 Ir para Investigar", type="primary"):
            ir_para("Investigar")
        return

    # Recuperar dados da sessão
    dados_usuario = st.session_state.get('dados_usuario')
    area_de_interesse_geojson = st.session_state.get('area_de_interesse')
    gdf_zcl_base, gdf_temp_base = st.session_state.get('dados_base', (None, None))

    if gdf_zcl_base is None:
        st.error("❌ Dados base de ZCL não foram carregados. Verifique a configuração da aplicação.")
        return

    st.markdown("""
    <div class="learning-guide">
        <div class="learning-guide-step is-active"><span>1</span><div><strong>Observe</strong><small>mapa e composição</small></div></div>
        <div class="learning-guide-connector"></div>
        <div class="learning-guide-step"><span>2</span><div><strong>Compare</strong><small>classes e valores</small></div></div>
        <div class="learning-guide-connector"></div>
        <div class="learning-guide-step"><span>3</span><div><strong>Registre</strong><small>relatório e dados</small></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Comece pelo mapa para entender o contexto. Depois compare os valores entre as Zonas Climáticas Locais.")

    # Layout principal em uma sequência de leitura simples.
    tab1, tab2, tab3 = st.tabs(["1. Mapa e contexto", "2. Comparar valores", "3. Relatório"])
    
    with tab1:
        st.info("Leia esta etapa como uma pergunta: **onde estão as zonas e os pontos mais quentes?**")
        renderizar_analise_espacial(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)
    
    with tab2:
        st.info("Aqui você testa a hipótese: **as diferenças entre zonas aparecem nos dados medidos?**")
        renderizar_analise_estatistica(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)
    
    with tab3:
        st.info("Use o relatório para registrar a interpretação e baixar os dados já associados às ZCL.")
        renderizar_relatorio(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)

def renderizar_analise_espacial(dados_usuario, area_de_interesse_geojson, gdf_zcl_base):
    """Renderiza a aba de análise espacial."""
    
    st.markdown("### 🗺️ Composição da Área de Interesse")
    
    if area_de_interesse_geojson:
        # Filtrar ZCL para a área de interesse
        zcl_na_area = processamento.filtrar_dados_por_area(gdf_zcl_base, area_de_interesse_geojson)
        
        if not zcl_na_area.empty:
            # Calcular estatísticas da área
            stats = processamento.calcular_estatisticas_area(zcl_na_area)
            
            if stats:
                df_composicao = pd.DataFrame(stats['composicao'])
                ordem = _ordem_lcz_presentes(df_composicao['zcl_classe'])
                df_composicao['zcl_classe'] = pd.Categorical(
                    df_composicao['zcl_classe'], categories=ordem, ordered=True
                )
                df_composicao = df_composicao.sort_values('zcl_classe')
                df_composicao['area_km2'] = df_composicao['sum'] / 1_000_000
                df_composicao['tipo'] = df_composicao['zcl_classe'].astype(str).map(_tipo_lcz)
                classe_dominante = df_composicao.loc[df_composicao['percentual'].idxmax()]
                pct_construida = df_composicao.loc[
                    df_composicao['tipo'] == "Construida", 'percentual'
                ].sum()

                col1, col2, col3 = st.columns(3)
                col1.metric("Área total", f"{stats['total_area_m2']/1_000_000:.2f} km²")
                col2.metric("Classe dominante", str(classe_dominante['zcl_classe']),
                            f"{classe_dominante['percentual']:.1f}%")
                col3.metric("Área construída", f"{pct_construida:.1f}%",
                            help="Soma das classes LCZ 1 a LCZ 10 dentro da área.")

                fig_area = px.bar(
                    df_composicao,
                    x='percentual',
                    y='zcl_classe',
                    orientation='h',
                    color='zcl_classe',
                    color_discrete_map=CORES_LCZ,
                    category_orders={'zcl_classe': ordem},
                    text=df_composicao['percentual'].map(lambda v: f"{v:.1f}%"),
                    custom_data=['tipo', 'area_km2'],
                    labels={
                        'zcl_classe': 'Classe LCZ',
                        'percentual': 'Participação na área (%)',
                        'area_km2': 'Área (km²)',
                        'tipo': 'Grupo',
                    },
                )
                fig_area.update_traces(
                    textposition='outside',
                    marker_line_color='rgba(22,48,68,0.24)',
                    marker_line_width=0.8,
                    hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Área: %{customdata[1]:.3f} km²<br>Participação: %{x:.1f}%<extra></extra>",
                )
                fig_area.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': ordem[::-1]})
                _layout_didatico(fig_area, "Composição da área por classe LCZ", 440, legenda=False)
                fig_area.update_xaxes(range=[0, max(5, df_composicao['percentual'].max() * 1.18)])
                st.plotly_chart(fig_area, use_container_width=True)

                st.caption(
                    "Leitura: barras maiores indicam quais formas urbanas ou coberturas dominam a área. "
                    "As cores seguem a paleta oficial LCZ, facilitando comparar esta seção com os mapas."
                )

                df_display = df_composicao.copy()
                df_display['zcl_classe'] = df_display['zcl_classe'].astype(str)
                df_display = df_display[['zcl_classe', 'tipo', 'area_km2', 'percentual']].round(3)
                df_display.columns = ['Zona climática', 'Grupo', 'Área (km²)', 'Percentual (%)']
                st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma Zona Climática encontrada na área desenhada.")
    else:
        st.info("Defina uma área de interesse no módulo Investigar para ver a análise espacial.")

    # Análise dos pontos de dados do usuário
    if dados_usuario is not None:
        st.markdown("### 📍 Análise dos Pontos de Medição")
        
        # Filtrar pontos para a área de interesse
        if area_de_interesse_geojson:
            pontos_na_area = processamento.filtrar_dados_por_area(dados_usuario, area_de_interesse_geojson)
        else:
            pontos_na_area = dados_usuario
        
        if not pontos_na_area.empty:
            # Juntar pontos com informações de ZCL
            pontos_com_info = processamento.juntar_dados_espaciais(pontos_na_area, gdf_zcl_base)
            pontos_com_info = pontos_com_info.dropna(subset=['zcl_classe']).copy()

            if pontos_com_info.empty:
                st.warning("Os pontos foram carregados, mas nenhum caiu dentro das classes LCZ mapeadas.")
                return

            ordem_pontos = _ordem_lcz_presentes(pontos_com_info['zcl_classe'])
            pontos_com_info['zcl_classe'] = pd.Categorical(
                pontos_com_info['zcl_classe'], categories=ordem_pontos, ordered=True
            )
            pontos_com_info['classe_texto'] = pontos_com_info['zcl_classe'].astype(str)
            pontos_com_info['grupo_lcz'] = pontos_com_info['classe_texto'].map(_tipo_lcz)
            valor_min = pontos_com_info['valor'].min()
            valor_max = pontos_com_info['valor'].max()
            if valor_max == valor_min:
                pontos_com_info['tamanho_ponto'] = 10
            else:
                pontos_com_info['tamanho_ponto'] = 7 + (
                    (pontos_com_info['valor'] - valor_min) / (valor_max - valor_min) * 15
                )

            col1, col2 = st.columns([1.2, 1])

            with col1:
                fig_scatter = px.scatter_mapbox(
                    pontos_com_info,
                    lat='latitude',
                    lon='longitude',
                    color='classe_texto',
                    size='tamanho_ponto',
                    color_discrete_map=CORES_LCZ,
                    category_orders={'classe_texto': ordem_pontos},
                    custom_data=['classe_texto', 'grupo_lcz', 'valor'],
                    title="Pontos medidos sobre as classes LCZ",
                    mapbox_style="open-street-map",
                    height=460,
                    zoom=10,
                )
                fig_scatter.update_traces(
                    marker=dict(opacity=0.88, sizemode='diameter', line=dict(width=1.2, color="#163044")),
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Valor medido: %{customdata[2]:.2f}<extra></extra>",
                )
                fig_scatter.update_layout(
                    margin=dict(l=0, r=0, t=56, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            with col2:
                fig_hist = px.histogram(
                    pontos_com_info,
                    x='valor',
                    color='classe_texto',
                    nbins=min(12, max(5, len(pontos_com_info) // 2)),
                    barmode='overlay',
                    opacity=0.72,
                    color_discrete_map=CORES_LCZ,
                    category_orders={'classe_texto': ordem_pontos},
                    labels={'valor': 'Valor medido', 'count': 'Número de pontos', 'classe_texto': 'Classe LCZ'},
                    title="Distribuição dos valores por LCZ",
                )
                _adicionar_linha_media(fig_hist, pontos_com_info['valor'].mean(), orientacao="v")
                _layout_didatico(fig_hist, "Distribuição dos valores por LCZ", 460, legenda=True)
                st.plotly_chart(fig_hist, use_container_width=True)

            st.caption(
                "No mapa, a cor indica a classe LCZ e o tamanho indica a intensidade do valor medido. "
                "No histograma, barras deslocadas para a direita indicam classes com medições mais altas."
            )
        else:
            st.warning("Nenhum ponto de medição encontrado na área de interesse.")

def renderizar_analise_estatistica(dados_usuario, area_de_interesse_geojson, gdf_zcl_base):
    """Renderiza a aba de análise estatística."""
    
    st.markdown("### 📈 Análise Estatística Detalhada")
    
    if dados_usuario is None:
        st.info("Carregue dados de campo no módulo Investigar para ver análises estatísticas.")
        return
    
    # Filtrar pontos para a área de interesse
    if area_de_interesse_geojson:
        pontos_na_area = processamento.filtrar_dados_por_area(dados_usuario, area_de_interesse_geojson)
    else:
        pontos_na_area = dados_usuario
    
    if pontos_na_area.empty:
        st.warning("Nenhum ponto de dados na área de interesse.")
        return
    
    # Juntar com informações de ZCL
    pontos_com_info = processamento.juntar_dados_espaciais(pontos_na_area, gdf_zcl_base)
    pontos_com_zcl = pontos_com_info.dropna(subset=['zcl_classe'])
    
    if pontos_com_zcl.empty:
        st.warning("Nenhum ponto está localizado dentro de uma Zona Climática mapeada.")
        return
    
    # Estatísticas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Pontos", len(pontos_com_zcl))
    with col2:
        st.metric("Valor Médio", f"{pontos_com_zcl['valor'].mean():.2f}")
    with col3:
        st.metric("Desvio Padrão", f"{pontos_com_zcl['valor'].std():.2f}")
    with col4:
        st.metric("Amplitude", f"{pontos_com_zcl['valor'].max() - pontos_com_zcl['valor'].min():.2f}")

    st.caption("Média = valor típico · Desvio padrão = variação entre pontos · Amplitude = distância entre menor e maior valor.")
    
    # Análise por ZCL
    st.markdown("#### 🏘️ Análise por Zona Climática Local")
    ordem_zcl = _ordem_lcz_presentes(pontos_com_zcl['zcl_classe'])
    pontos_com_zcl = pontos_com_zcl.copy()
    pontos_com_zcl['classe_texto'] = pontos_com_zcl['zcl_classe'].astype(str)
    pontos_com_zcl['grupo_lcz'] = pontos_com_zcl['classe_texto'].map(_tipo_lcz)

    stats_por_zcl = (
        pontos_com_zcl.groupby('classe_texto', observed=True)['valor']
        .agg(['mean', 'std', 'count', 'min', 'max'])
        .reset_index()
    )
    stats_por_zcl['grupo_lcz'] = stats_por_zcl['classe_texto'].map(_tipo_lcz)
    stats_por_zcl['erro'] = stats_por_zcl['std'].fillna(0)
    stats_por_zcl['rotulo'] = stats_por_zcl.apply(
        lambda row: f"{row['mean']:.1f}  n={int(row['count'])}", axis=1
    )
    media_geral = pontos_com_zcl['valor'].mean()

    col1, col2 = st.columns(2)

    with col1:
        fig_box = px.box(
            pontos_com_zcl,
            x='classe_texto',
            y='valor',
            points='all',
            color='classe_texto',
            color_discrete_map=CORES_LCZ,
            category_orders={'classe_texto': ordem_zcl},
            labels={'classe_texto': 'Classe LCZ', 'valor': 'Valor medido'},
            title="Variação dos valores dentro de cada LCZ",
            hover_data={'grupo_lcz': True, 'latitude': ':.5f', 'longitude': ':.5f'},
        )
        fig_box.update_traces(
            marker=dict(opacity=0.72, size=7, line=dict(width=0.6, color="#163044")),
            line=dict(width=1.4),
        )
        _adicionar_linha_media(fig_box, media_geral, orientacao="h")
        _layout_didatico(fig_box, "Variação dos valores dentro de cada LCZ", 460, legenda=False)
        fig_box.update_xaxes(tickangle=0)
        st.plotly_chart(fig_box, use_container_width=True)

    with col2:
        stats_ranking = stats_por_zcl.sort_values('mean', ascending=True)
        fig_bar = px.bar(
            stats_ranking,
            x='mean',
            y='classe_texto',
            orientation='h',
            error_x='erro',
            color='classe_texto',
            color_discrete_map=CORES_LCZ,
            category_orders={'classe_texto': ordem_zcl},
            text='rotulo',
            custom_data=['grupo_lcz', 'count', 'std', 'min', 'max'],
            labels={'classe_texto': 'Classe LCZ', 'mean': 'Valor médio'},
            title="Ranking das médias por LCZ",
        )
        fig_bar.update_traces(
            textposition='outside',
            marker_line_color='rgba(22,48,68,0.24)',
            marker_line_width=0.8,
            hovertemplate=(
                "<b>%{y}</b><br>%{customdata[0]}<br>"
                "Média: %{x:.2f}<br>"
                "Desvio padrão: %{customdata[2]:.2f}<br>"
                "Pontos: %{customdata[1]}<br>"
                "Mín-Máx: %{customdata[3]:.2f} a %{customdata[4]:.2f}<extra></extra>"
            ),
        )
        _adicionar_linha_media(fig_bar, media_geral, orientacao="v")
        _layout_didatico(fig_bar, "Ranking das médias por LCZ", 460, legenda=False)
        desvio_geral = pontos_com_zcl['valor'].std()
        if pd.isna(desvio_geral) or desvio_geral == 0:
            desvio_geral = max(1, abs(media_geral) * 0.05)
        fig_bar.update_xaxes(range=[
            min(stats_ranking['mean'].min(), media_geral) - max(1, desvio_geral * 0.35),
            stats_ranking['mean'].max() + max(1, desvio_geral * 1.25),
        ])
        st.plotly_chart(fig_bar, use_container_width=True)

    st.caption(
        "No boxplot, a linha central mostra a mediana e os pontos mostram as medições reais. "
        "No ranking, barras à direita da média geral indicam classes com valores médios mais altos."
    )
    
    # Tabela de estatísticas detalhadas
    st.markdown("#### 📊 Estatísticas Detalhadas por ZCL")
    
    stats_detalhadas = pontos_com_zcl.groupby('classe_texto')['valor'].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(2)
    stats_detalhadas = stats_detalhadas.reindex(ordem_zcl).dropna(how='all')
    stats_detalhadas.columns = ['Pontos', 'Média', 'Desvio padrão', 'Mínimo', 'Máximo']
    stats_detalhadas.insert(0, 'Grupo', [_tipo_lcz(idx) for idx in stats_detalhadas.index])
    st.dataframe(stats_detalhadas, use_container_width=True)
    
    # Análise de correlação (se houver dados suficientes)
    if len(pontos_com_zcl) > 10:
        st.markdown("#### 🔗 Tendência dos Valores ao Longo do Espaço")
        st.caption(
            "Isto mostra se os valores tendem a crescer/diminuir de norte a sul ou de "
            "leste a oeste. É uma correlação simples com a coordenada, diferente de "
            "métodos de **autocorrelação espacial** (ex. Índice de Moran), que exigiriam "
            "mais pontos e uma análise dedicada."
        )

        # Correlação simples entre coordenadas e valores
        corr_lat = pontos_com_zcl['valor'].corr(pontos_com_zcl['latitude'])
        corr_lon = pontos_com_zcl['valor'].corr(pontos_com_zcl['longitude'])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Correlação com Latitude", f"{corr_lat:.3f}")
        with col2:
            st.metric("Correlação com Longitude", f"{corr_lon:.3f}")
        
        fig_corr = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Gradiente norte-sul', 'Gradiente oeste-leste')
        )

        for classe in ordem_zcl:
            subset = pontos_com_zcl[pontos_com_zcl['classe_texto'] == classe]
            if subset.empty:
                continue
            cor = CORES_LCZ.get(classe, "#0f766e")
            fig_corr.add_trace(
                go.Scatter(
                    x=subset['latitude'],
                    y=subset['valor'],
                    mode='markers',
                    name=classe,
                    marker=dict(size=9, color=cor, line=dict(width=0.8, color="#163044"), opacity=0.82),
                    hovertemplate=f"<b>{classe}</b><br>Latitude: %{{x:.5f}}<br>Valor: %{{y:.2f}}<extra></extra>",
                    legendgroup=classe,
                    showlegend=True,
                ),
                row=1, col=1
            )
            fig_corr.add_trace(
                go.Scatter(
                    x=subset['longitude'],
                    y=subset['valor'],
                    mode='markers',
                    name=classe,
                    marker=dict(size=9, color=cor, line=dict(width=0.8, color="#163044"), opacity=0.82),
                    hovertemplate=f"<b>{classe}</b><br>Longitude: %{{x:.5f}}<br>Valor: %{{y:.2f}}<extra></extra>",
                    legendgroup=classe,
                    showlegend=False,
                ),
                row=1, col=2
            )

        for col, eixo in enumerate(['latitude', 'longitude'], start=1):
            if pontos_com_zcl[eixo].nunique() > 1:
                coef = np.polyfit(pontos_com_zcl[eixo], pontos_com_zcl['valor'], 1)
                x_line = np.array([pontos_com_zcl[eixo].min(), pontos_com_zcl[eixo].max()])
                y_line = coef[0] * x_line + coef[1]
                fig_corr.add_trace(
                    go.Scatter(
                        x=x_line,
                        y=y_line,
                        mode='lines',
                        name='Tendência',
                        line=dict(color="#163044", dash="dot", width=2),
                        hoverinfo='skip',
                        showlegend=(col == 1),
                    ),
                    row=1, col=col,
                )

        _layout_didatico(fig_corr, "Tendência espacial dos valores medidos", 430, legenda=True)
        fig_corr.update_xaxes(title_text="Latitude", row=1, col=1)
        fig_corr.update_xaxes(title_text="Longitude", row=1, col=2)
        fig_corr.update_yaxes(title_text="Valor medido", row=1, col=1)
        fig_corr.update_yaxes(title_text="", row=1, col=2)
        st.plotly_chart(fig_corr, use_container_width=True)

def renderizar_relatorio(dados_usuario, area_de_interesse_geojson, gdf_zcl_base):
    """Renderiza a aba de relatório."""
    
    st.markdown("### 📋 Relatório de Análise")
    
    # Gerar relatório automático
    relatorio = gerar_relatorio_automatico(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)
    
    # Mostrar relatório
    st.markdown(relatorio)
    
    # Opções de exportação
    st.markdown("---")
    st.markdown("### 📥 Exportar Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Botão para baixar relatório
        st.download_button(
            label="📄 Baixar Relatório (Markdown)",
            data=relatorio,
            file_name="relatorio_analise_clima_urbano.md",
            mime="text/markdown"
        )
    
    with col2:
        # Botão para baixar dados processados
        if dados_usuario is not None:
            if area_de_interesse_geojson:
                pontos_filtrados = processamento.filtrar_dados_por_area(dados_usuario, area_de_interesse_geojson)
            else:
                pontos_filtrados = dados_usuario
            
            if not pontos_filtrados.empty:
                pontos_com_zcl = processamento.juntar_dados_espaciais(pontos_filtrados, gdf_zcl_base)
                csv_data = pontos_com_zcl.drop(columns='geometry').to_csv(index=False)
                
                st.download_button(
                    label="📊 Baixar Dados Processados (CSV)",
                    data=csv_data,
                    file_name="dados_processados_clima_urbano.csv",
                    mime="text/csv"
                )

def gerar_relatorio_automatico(dados_usuario, area_de_interesse_geojson, gdf_zcl_base):
    """Gera um relatório automático da análise."""
    
    from datetime import datetime
    
    relatorio = f"""# Relatório de Análise - Clima Urbano

**Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Plataforma:** Clima Urbano Interativo v3.0

## 📊 Resumo Executivo

"""
    
    # Análise da área de interesse
    if area_de_interesse_geojson:
        zcl_na_area = processamento.filtrar_dados_por_area(gdf_zcl_base, area_de_interesse_geojson)
        if not zcl_na_area.empty:
            stats = processamento.calcular_estatisticas_area(zcl_na_area)
            if stats:
                relatorio += f"""### 🗺️ Área de Interesse
- **Área Total:** {stats['total_area_m2']/1000000:.2f} km²
- **Número de Classes ZCL:** {stats['num_classes']}

#### Composição por Zona Climática Local:
"""
                for item in stats['composicao']:
                    relatorio += f"- **{item['zcl_classe']}:** {item['percentual']:.1f}% ({item['sum']/1000000:.3f} km²)\n"
    
    # Análise dos dados do usuário
    if dados_usuario is not None:
        if area_de_interesse_geojson:
            pontos_na_area = processamento.filtrar_dados_por_area(dados_usuario, area_de_interesse_geojson)
        else:
            pontos_na_area = dados_usuario
        
        if not pontos_na_area.empty:
            pontos_com_zcl = processamento.juntar_dados_espaciais(pontos_na_area, gdf_zcl_base)
            pontos_com_zcl = pontos_com_zcl.dropna(subset=['zcl_classe'])
            
            relatorio += f"""

### 📍 Dados de Campo
- **Total de Pontos Analisados:** {len(pontos_com_zcl)}
- **Valor Médio:** {pontos_com_zcl['valor'].mean():.2f}
- **Desvio Padrão:** {pontos_com_zcl['valor'].std():.2f}
- **Amplitude:** {pontos_com_zcl['valor'].max() - pontos_com_zcl['valor'].min():.2f}

#### Estatísticas por Zona Climática Local:
"""
            stats_por_zcl = pontos_com_zcl.groupby('zcl_classe')['valor'].agg(['count', 'mean', 'std']).round(2)
            for zcl, row in stats_por_zcl.iterrows():
                relatorio += f"- **{zcl}:** {row['count']} pontos, média {row['mean']:.2f} ± {row['std']:.2f}\n"
    
    # Monta achados a partir dos números já calculados acima (não é texto fixo genérico)
    relatorio += "\n\n## 🎓 Interpretação e Recomendações\n\n### Principais Achados:\n"

    n_achado = 1
    if area_de_interesse_geojson and 'stats' in locals() and stats:
        classe_dominante = max(stats['composicao'], key=lambda c: c['percentual'])
        relatorio += (
            f"{n_achado}. Na área analisada, a classe dominante foi "
            f"**{classe_dominante['zcl_classe']}** ({classe_dominante['percentual']:.1f}% da área).\n"
        )
        n_achado += 1

    if dados_usuario is not None and 'pontos_com_zcl' in locals() and not pontos_com_zcl.empty:
        stats_por_zcl_dict = pontos_com_zcl.groupby('zcl_classe')['valor'].mean()
        if len(stats_por_zcl_dict) > 0:
            zcl_max = stats_por_zcl_dict.idxmax()
            zcl_min = stats_por_zcl_dict.idxmin()
            relatorio += (
                f"{n_achado}. Os {len(pontos_com_zcl)} pontos de campo mostraram média de "
                f"{pontos_com_zcl['valor'].mean():.2f}, com maior diferença entre "
                f"**{zcl_max}** ({stats_por_zcl_dict.max():.2f}) e **{zcl_min}** "
                f"({stats_por_zcl_dict.min():.2f}).\n"
            )
            n_achado += 1

    relatorio += (
        f"{n_achado}. Estes resultados são preliminares e dependem da densidade e "
        "distribuição dos pontos coletados. Trate como indicativo, não conclusivo.\n"
    )

    relatorio += """
### Recomendações para Estudos Futuros:
- Ampliar a coleta de dados para diferentes horários e estações
- Incluir medições de umidade relativa e velocidade do vento
- Analisar a influência de fatores como albedo e rugosidade da superfície
- Comparar com dados de sensoriamento remoto

## 📚 Referências Metodológicas

- Stewart, I. D., & Oke, T. R. (2012). Local climate zones for urban temperature studies. *Bulletin of the American Meteorological Society*, 93(12), 1879-1900.
- WUDAPT (World Urban Database and Portal Tools) - Protocolo para mapeamento de ZCL
- LCZ Generator - Ferramenta automatizada para classificação de zonas climáticas

---
*Relatório gerado automaticamente pela Plataforma Clima Urbano Interativo*
"""
    
    return relatorio
