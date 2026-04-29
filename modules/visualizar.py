# modules/visualizar.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from datetime import datetime
from utils import processamento

def renderizar_pagina():
    """Renderiza a página do módulo Visualizar."""
    
    st.markdown("""
    <div class="module-header">
        <h1>📊 Módulo Visualizar</h1>
        <p>Explore gráficos e estatísticas detalhadas da sua análise</p>
    </div>
    """, unsafe_allow_html=True)

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
            st.session_state.navigation = "Investigar"
            st.rerun()
        return

    # Recuperar dados da sessão
    dados_usuario = st.session_state.get('dados_usuario')
    area_de_interesse_geojson = st.session_state.get('area_de_interesse')
    gdf_zcl_base, gdf_temp_base = st.session_state.get('dados_base', (None, None))

    if gdf_zcl_base is None:
        st.error("❌ Dados base de ZCL não foram carregados. Verifique a configuração da aplicação.")
        return

    # Layout principal
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Análise Espacial", "📈 Análise Estatística", "📊 Distribuição", "📋 Relatório"])

    with tab1:
        renderizar_analise_espacial(dados_usuario, area_de_interesse_geojson, gdf_zcl_base, gdf_temp_base)

    with tab2:
        renderizar_analise_estatistica(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)

    with tab3:
        renderizar_distribuicao_tab(dados_usuario)

    with tab4:
        renderizar_relatorio(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)

def renderizar_analise_espacial(dados_usuario, area_de_interesse_geojson, gdf_zcl_base, gdf_temp_base):
    """Renderiza a aba de análise espacial."""
    
    st.markdown("### 🗺️ Composição da Área de Interesse")
    
    if area_de_interesse_geojson:
        # Filtrar ZCL para a área de interesse
        zcl_na_area = processamento.filtrar_dados_por_area(gdf_zcl_base, area_de_interesse_geojson)
        
        if not zcl_na_area.empty:
            # Calcular estatísticas da área
            stats = processamento.calcular_estatisticas_area(zcl_na_area)
            
            if stats:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Gráfico de pizza da composição de ZCL
                    df_composicao = pd.DataFrame(stats['composicao'])
                    
                    fig_pizza = px.pie(
                        df_composicao, 
                        values='sum', 
                        names='zcl_classe',
                        title="Distribuição de Zonas Climáticas Locais",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pizza.update_layout(height=400)
                    st.plotly_chart(fig_pizza, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📏 Métricas da Área")
                    st.metric("Área Total", f"{stats['total_area_m2']/1000000:.2f} km²")
                    st.metric("Classes de ZCL", stats['num_classes'])
                    
                    # Tabela detalhada
                    st.markdown("#### 📊 Detalhamento")
                    df_display = df_composicao.copy()
                    df_display['area_km2'] = df_display['sum'] / 1000000
                    df_display = df_display[['zcl_classe', 'area_km2', 'percentual']].round(3)
                    df_display.columns = ['Zona Climática', 'Área (km²)', 'Percentual (%)']
                    st.dataframe(df_display, use_container_width=True)
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
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Mapa de dispersão dos valores
                fig_scatter = px.scatter_mapbox(
                    pontos_com_info,
                    lat='latitude',
                    lon='longitude',
                    color='valor',
                    size='valor',
                    hover_data=['zcl_classe'],
                    color_continuous_scale='RdYlBu_r',
                    title="Distribuição Espacial dos Valores Medidos",
                    mapbox_style="open-street-map",
                    height=400
                )
                fig_scatter.update_layout(mapbox_zoom=11)
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with col2:
                # Histograma dos valores
                fig_hist = px.histogram(
                    pontos_com_info,
                    x='valor',
                    nbins=20,
                    title="Distribuição dos Valores Medidos",
                    labels={'valor': 'Valor Medido', 'count': 'Frequência'}
                )
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)
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
    
    # Análise por ZCL
    st.markdown("#### 🏘️ Análise por Zona Climática Local")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Box plot por ZCL
        fig_box = px.box(
            pontos_com_zcl,
            x='zcl_classe',
            y='valor',
            title="Distribuição dos Valores por Zona Climática",
            labels={'zcl_classe': 'Zona Climática Local', 'valor': 'Valor Medido'}
        )
        fig_box.update_xaxes(tickangle=45)
        fig_box.update_layout(height=400)
        st.plotly_chart(fig_box, use_container_width=True)
    
    with col2:
        # Gráfico de barras com médias
        stats_por_zcl = pontos_com_zcl.groupby('zcl_classe')['valor'].agg(['mean', 'std', 'count']).reset_index()
        
        fig_bar = px.bar(
            stats_por_zcl,
            x='zcl_classe',
            y='mean',
            error_y='std',
            title="Valor Médio por Zona Climática",
            labels={'zcl_classe': 'Zona Climática Local', 'mean': 'Valor Médio'}
        )
        fig_bar.update_xaxes(tickangle=45)
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Tabela de estatísticas detalhadas
    st.markdown("#### 📊 Estatísticas Detalhadas por ZCL")
    
    stats_detalhadas = pontos_com_zcl.groupby('zcl_classe')['valor'].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(2)
    stats_detalhadas.columns = ['N° Pontos', 'Média', 'Desvio Padrão', 'Mínimo', 'Máximo']
    st.dataframe(stats_detalhadas, use_container_width=True)
    
    # Análise de correlação (se houver dados suficientes)
    if len(pontos_com_zcl) > 10:
        st.markdown("#### 🔗 Análise de Correlação Espacial")
        
        # Correlação simples entre coordenadas e valores
        corr_lat = pontos_com_zcl['valor'].corr(pontos_com_zcl['latitude'])
        corr_lon = pontos_com_zcl['valor'].corr(pontos_com_zcl['longitude'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Correlação com Latitude", f"{corr_lat:.3f}")
        with col2:
            st.metric("Correlação com Longitude", f"{corr_lon:.3f}")
        
        # Scatter plot das correlações
        fig_corr = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Valor vs Latitude', 'Valor vs Longitude')
        )
        
        fig_corr.add_trace(
            go.Scatter(x=pontos_com_zcl['latitude'], y=pontos_com_zcl['valor'], mode='markers', name='Latitude'),
            row=1, col=1
        )
        fig_corr.add_trace(
            go.Scatter(x=pontos_com_zcl['longitude'], y=pontos_com_zcl['valor'], mode='markers', name='Longitude'),
            row=1, col=2
        )
        
        fig_corr.update_layout(height=400, title_text="Correlações Espaciais")
        st.plotly_chart(fig_corr, use_container_width=True)

def renderizar_distribuicao_tab(dados_usuario: pd.DataFrame) -> None:
    """
    Renderiza a aba dedicada à análise de distribuição de temperatura.

    Entrada:
        dados_usuario (pd.DataFrame): Dados de temperatura do usuário
    """

    st.markdown("### 📊 Análise Avançada de Distribuição")

    if dados_usuario is None or dados_usuario.empty:
        st.info("📥 Carregue dados de campo no módulo Investigar para visualizar a análise de distribuição.")
        return

    try:
        renderizar_analise_distribuicao(dados_usuario)
    except ValueError as e:
        st.error(f"❌ Erro ao gerar análise de distribuição: {str(e)}")
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")


def renderizar_relatorio(dados_usuario, area_de_interesse_geojson, gdf_zcl_base):
    """Renderiza a aba de relatório."""

    st.markdown("### 📋 Relatório de Análise")

    # Gerar relatório automático (Markdown)
    relatorio_md = gerar_relatorio_automatico(dados_usuario, area_de_interesse_geojson, gdf_zcl_base)

    # Mostrar relatório
    st.markdown(relatorio_md)

    # Opções de exportação
    st.markdown("---")
    st.markdown("### 📥 Exportar Resultados")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Botão para baixar relatório Markdown
        st.download_button(
            label="📄 Relatório (Markdown)",
            data=relatorio_md,
            file_name="relatorio_analise_clima_urbano.md",
            mime="text/markdown"
        )

    with col2:
        # Botão para baixar relatório HTML
        if dados_usuario is not None and not dados_usuario.empty:
            try:
                relatorio_html = gerar_relatorio_html(
                    dados_usuario=dados_usuario,
                    cidade="Área de Interesse"
                )
                st.download_button(
                    label="🌐 Relatório (HTML)",
                    data=relatorio_html,
                    file_name="relatorio_analise_clima_urbano.html",
                    mime="text/html"
                )
            except ValueError as e:
                st.warning(f"⚠️ Não foi possível gerar relatório HTML: {str(e)}")
        else:
            st.info("Carregue dados para gerar relatório HTML")

    with col3:
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
                    label="📊 Dados (CSV)",
                    data=csv_data,
                    file_name="dados_processados_clima_urbano.csv",
                    mime="text/csv"
                )

def renderizar_analise_distribuicao(dados_usuario: pd.DataFrame) -> None:
    """
    Renderiza análise avançada da distribuição de temperatura com boxplot,
    histograma e densidade kernel (KDE).

    Entrada:
        dados_usuario (pd.DataFrame): DataFrame com colunas 'valor', 'latitude', 'longitude'

    Saída:
        Visualização interativa Plotly com múltiplas vistas de distribuição,
        permitindo zoom, hover com valores e download PNG.

    Raises:
        ValueError: Se dados_usuario é None ou vazio
        KeyError: Se coluna 'valor' não existe
    """

    # Validação de entrada
    if dados_usuario is None or dados_usuario.empty:
        st.warning("❌ Nenhum dado de temperatura disponível para análise de distribuição.")
        return

    if 'valor' not in dados_usuario.columns:
        st.error("❌ Coluna 'valor' não encontrada nos dados. Verifique o formato do CSV.")
        return

    # Remover valores nulos
    dados_limpos = dados_usuario.dropna(subset=['valor'])

    if dados_limpos.empty:
        st.warning("⚠️ Todos os valores de temperatura são nulos.")
        return

    valores = dados_limpos['valor'].values

    # Criar subplots: Boxplot + Histograma + Estatísticas
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Boxplot (Quartis e Outliers)',
            'Histograma com Densidade KDE',
            'Gráfico Q-Q (Normalidade)',
            'Estatísticas Descritivas'
        ),
        specs=[
            [{'type': 'box'}, {'type': 'histogram'}],
            [{'type': 'scatter'}, {'type': 'table'}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    # 1. BOXPLOT - mostra quartis, mediana, outliers
    fig.add_trace(
        go.Box(
            y=valores,
            name='Distribuição',
            boxmean='sd',  # mostra média e desvio padrão
            marker_color='#10b981',  # cor emerald do tema
            hovertemplate='<b>Valor:</b> %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )

    # 2. HISTOGRAMA + KDE Overlay
    # Usar algoritmo de Sturges para bins automáticos
    n_bins = int(np.ceil(np.log2(len(valores)) + 1))

    fig.add_trace(
        go.Histogram(
            x=valores,
            name='Frequência',
            nbinsx=n_bins,
            marker_color='rgba(16, 185, 129, 0.7)',  # emerald com transparência
            hovertemplate='<b>Faixa:</b> %{x:.2f}<br><b>Frequência:</b> %{y}<extra></extra>'
        ),
        row=1, col=2
    )

    # KDE overlay (densidade kernel)
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(valores)
        x_range = np.linspace(valores.min(), valores.max(), 200)
        density = kde(x_range)

        # Normalizar densidade para caber no histograma
        density_scaled = density * (len(valores) * (valores.max() - valores.min()) / n_bins)

        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=density_scaled,
                name='Densidade (KDE)',
                line=dict(color='#c2410c', width=3),  # cor terracotta
                hovertemplate='<b>Valor:</b> %{x:.2f}<br><b>Densidade:</b> %{y:.4f}<extra></extra>'
            ),
            row=1, col=2
        )
    except Exception as e:
        st.warning(f"⚠️ Não foi possível calcular KDE: {str(e)}")

    # 3. GRÁFICO Q-Q (testa normalidade dos dados)
    try:
        # Q-Q plot: quantis teóricos vs observados
        quantis_teoricos = scipy_stats.norm.ppf(np.linspace(0.01, 0.99, len(valores)))
        quantis_observados = np.sort(valores)

        fig.add_trace(
            go.Scatter(
                x=quantis_teoricos,
                y=quantis_observados,
                mode='markers',
                name='Dados Observados',
                marker=dict(color='#0ea5e9', size=5),  # cor sky
                hovertemplate='<b>Teórico:</b> %{x:.2f}<br><b>Observado:</b> %{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        # Linha de referência (reta ideal)
        min_q, max_q = quantis_observados.min(), quantis_observados.max()
        fig.add_trace(
            go.Scatter(
                x=[quantis_teoricos.min(), quantis_teoricos.max()],
                y=[min_q, max_q],
                mode='lines',
                name='Referência Normal',
                line=dict(color='gray', dash='dash'),
                hoverinfo='skip'
            ),
            row=2, col=1
        )
    except Exception as e:
        st.warning(f"⚠️ Não foi possível calcular Q-Q plot: {str(e)}")

    # 4. TABELA DE ESTATÍSTICAS DESCRITIVAS
    stats_descritivas = {
        'Métrica': [
            'N (amostra)',
            'Média',
            'Mediana',
            'Desvio Padrão',
            'Variância',
            'Mínimo',
            'Q1 (25%)',
            'Q3 (75%)',
            'Máximo',
            'Amplitude',
            'IQR',
            'Assimetria',
            'Curtose'
        ],
        'Valor': [
            f"{len(valores)}",
            f"{valores.mean():.3f}",
            f"{np.median(valores):.3f}",
            f"{valores.std():.3f}",
            f"{valores.var():.3f}",
            f"{valores.min():.3f}",
            f"{np.percentile(valores, 25):.3f}",
            f"{np.percentile(valores, 75):.3f}",
            f"{valores.max():.3f}",
            f"{valores.max() - valores.min():.3f}",
            f"{np.percentile(valores, 75) - np.percentile(valores, 25):.3f}",
            f"{scipy_stats.skew(valores):.3f}",
            f"{scipy_stats.kurtosis(valores):.3f}"
        ]
    }

    df_stats = pd.DataFrame(stats_descritivas)

    fig.add_trace(
        go.Table(
            header=dict(
                values=['<b>' + col + '</b>' for col in df_stats.columns],
                fill_color='#10b981',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[df_stats[col] for col in df_stats.columns],
                fill_color='rgba(16, 185, 129, 0.1)',
                align='left',
                font=dict(size=11)
            )
        ),
        row=2, col=2
    )

    # Configurar layout
    fig.update_xaxes(title_text="Boxplot", row=1, col=1)
    fig.update_xaxes(title_text="Valor de Temperatura", row=1, col=2)
    fig.update_xaxes(title_text="Quantis Teóricos", row=2, col=1)

    fig.update_yaxes(title_text="Temperatura", row=1, col=1)
    fig.update_yaxes(title_text="Frequência", row=1, col=2)
    fig.update_yaxes(title_text="Quantis Observados", row=2, col=1)

    fig.update_layout(
        height=900,
        title_text="<b>Análise Completa da Distribuição de Temperatura</b>",
        showlegend=True,
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretação automática
    assimetria = scipy_stats.skew(valores)
    curtose = scipy_stats.kurtosis(valores)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Interpretação dos Dados")
        if abs(assimetria) < 0.5:
            simetria = "**Simétrica** - distribuição bem balanceada"
        elif assimetria > 0:
            simetria = "**Assimétrica à direita** - cauda longa para valores altos"
        else:
            simetria = "**Assimétrica à esquerda** - cauda longa para valores baixos"

        st.write(f"- Simetria: {simetria}")
        st.write(f"- Curtose: {'Platicúrtica (achatada)' if curtose < 0 else 'Leptocúrtica (pontiaguda)'}")

    with col2:
        st.markdown("#### 📈 Detecção de Outliers")
        Q1 = np.percentile(valores, 25)
        Q3 = np.percentile(valores, 75)
        IQR = Q3 - Q1
        limite_inf = Q1 - 1.5 * IQR
        limite_sup = Q3 + 1.5 * IQR

        outliers = (valores < limite_inf) | (valores > limite_sup)
        n_outliers = outliers.sum()
        pct_outliers = (n_outliers / len(valores)) * 100

        st.write(f"- **Outliers detectados:** {n_outliers} ({pct_outliers:.1f}%)")
        st.write(f"- **Limites:** [{limite_inf:.2f}, {limite_sup:.2f}]")


@st.cache_data
def gerar_relatorio_html(
    dados_usuario: pd.DataFrame,
    area_stats: dict = None,
    cidade: str = "Área de Interesse"
) -> str:
    """
    Gera relatório HTML profissional com estatísticas, gráficos e mapa embarcado.

    Entrada:
        dados_usuario (pd.DataFrame): DataFrame com dados de temperatura
        area_stats (dict): Dicionário com estatísticas da área (opcional)
        cidade (str): Nome da cidade/área para o título

    Saída:
        str: HTML completo pronto para download

    Inclui:
        - Título e metadados
        - Estatísticas descritivas em tabela
        - Gráficos Plotly embutidos (boxplot, histograma)
        - Tabela de dados brutos
        - Estilo CSS profissional inline

    Raises:
        ValueError: Se dados_usuario é None ou vazio
    """

    # Validação de entrada
    if dados_usuario is None or dados_usuario.empty:
        raise ValueError("dados_usuario não pode ser None ou vazio")

    if 'valor' not in dados_usuario.columns:
        raise ValueError("Coluna 'valor' é obrigatória em dados_usuario")

    # Limpar dados
    dados_limpos = dados_usuario.dropna(subset=['valor'])

    if dados_limpos.empty:
        raise ValueError("Nenhum valor válido encontrado em dados_usuario")

    valores = dados_limpos['valor'].values

    # ============ GERAR GRÁFICOS PLOTLY ============

    # Boxplot
    fig_box = go.Figure()
    fig_box.add_trace(go.Box(y=valores, name='Temperatura', boxmean='sd'))
    fig_box.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=50))
    html_boxplot = fig_box.to_html(include_plotlyjs='cdn', div_id='boxplot')

    # Histograma com KDE
    n_bins = int(np.ceil(np.log2(len(valores)) + 1))
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=valores, nbinsx=n_bins, name='Frequência'))

    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(valores)
        x_range = np.linspace(valores.min(), valores.max(), 200)
        density = kde(x_range)
        density_scaled = density * (len(valores) * (valores.max() - valores.min()) / n_bins)
        fig_hist.add_trace(go.Scatter(x=x_range, y=density_scaled, name='Densidade', line=dict(color='red')))
    except:
        pass

    fig_hist.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=50))
    html_histogram = fig_hist.to_html(include_plotlyjs=False, div_id='histogram')

    # ============ CALCULAR ESTATÍSTICAS ============

    stats_desc = {
        'n': len(valores),
        'media': valores.mean(),
        'mediana': np.median(valores),
        'desvio': valores.std(),
        'minimo': valores.min(),
        'maximo': valores.max(),
        'q1': np.percentile(valores, 25),
        'q3': np.percentile(valores, 75),
    }

    # ============ GERAR HTML ============

    data_geracao = datetime.now().strftime('%d de %B de %Y às %H:%M')

    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório - Análise Clima Urbano</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f9fafb;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}

        .meta {{
            font-size: 0.9em;
            opacity: 0.85;
            margin-top: 15px;
        }}

        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid #10b981;
        }}

        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #10b981;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section h3 {{
            font-size: 1.3em;
            margin-top: 25px;
            margin-bottom: 15px;
            color: #374151;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95em;
        }}

        th {{
            background-color: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #111827;
            border-bottom: 2px solid #10b981;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}

        tr:hover {{
            background-color: #f9fafb;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #f0fdf4 0%, #f0f9ff 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #10b981;
        }}

        .stat-label {{
            font-size: 0.9em;
            color: #6b7280;
            font-weight: 500;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 1.8em;
            font-weight: 700;
            color: #10b981;
            font-family: 'JetBrains Mono', monospace;
        }}

        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background-color: #f9fafb;
            border-radius: 8px;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: #6b7280;
            font-size: 0.9em;
            border-top: 1px solid #e5e7eb;
            margin-top: 40px;
        }}

        .badge {{
            display: inline-block;
            background-color: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 8px;
        }}

        @media print {{
            body {{
                background-color: white;
            }}
            .section {{
                page-break-inside: avoid;
                box-shadow: none;
                border: 1px solid #e5e7eb;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>📊 Relatório de Análise Clima Urbano</h1>
            <p>{cidade}</p>
            <div class="meta">
                <strong>Gerado em:</strong> {data_geracao}<br>
                <strong>Plataforma:</strong> Clima Urbano Interativo v2.0
            </div>
        </div>

        <!-- RESUMO EXECUTIVO -->
        <div class="section">
            <h2>📈 Resumo Executivo</h2>
            <p>Análise estatística completa da distribuição de temperatura na área de interesse.</p>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total de Pontos</div>
                    <div class="stat-value">{stats_desc['n']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Temperatura Média</div>
                    <div class="stat-value">{stats_desc['media']:.2f}°</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Mediana</div>
                    <div class="stat-value">{stats_desc['mediana']:.2f}°</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Desvio Padrão</div>
                    <div class="stat-value">{stats_desc['desvio']:.2f}°</div>
                </div>
            </div>
        </div>

        <!-- ESTATÍSTICAS DESCRITIVAS -->
        <div class="section">
            <h2>📊 Estatísticas Descritivas</h2>

            <table>
                <thead>
                    <tr>
                        <th>Métrica</th>
                        <th>Valor</th>
                        <th>Interpretação</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>n (Amostra)</strong></td>
                        <td>{stats_desc['n']}</td>
                        <td>Número de observações coletadas</td>
                    </tr>
                    <tr>
                        <td><strong>Média</strong></td>
                        <td>{stats_desc['media']:.3f}°</td>
                        <td>Valor médio da temperatura</td>
                    </tr>
                    <tr>
                        <td><strong>Mediana</strong></td>
                        <td>{stats_desc['mediana']:.3f}°</td>
                        <td>Valor central (50º percentil)</td>
                    </tr>
                    <tr>
                        <td><strong>Desvio Padrão</strong></td>
                        <td>{stats_desc['desvio']:.3f}°</td>
                        <td>Dispersão em torno da média</td>
                    </tr>
                    <tr>
                        <td><strong>Mínimo</strong></td>
                        <td>{stats_desc['minimo']:.3f}°</td>
                        <td>Temperatura mais baixa registrada</td>
                    </tr>
                    <tr>
                        <td><strong>Máximo</strong></td>
                        <td>{stats_desc['maximo']:.3f}°</td>
                        <td>Temperatura mais alta registrada</td>
                    </tr>
                    <tr>
                        <td><strong>Q1 (25º percentil)</strong></td>
                        <td>{stats_desc['q1']:.3f}°</td>
                        <td>25% dos dados estão abaixo deste valor</td>
                    </tr>
                    <tr>
                        <td><strong>Q3 (75º percentil)</strong></td>
                        <td>{stats_desc['q3']:.3f}°</td>
                        <td>75% dos dados estão abaixo deste valor</td>
                    </tr>
                    <tr>
                        <td><strong>Amplitude</strong></td>
                        <td>{stats_desc['maximo'] - stats_desc['minimo']:.3f}°</td>
                        <td>Diferença entre máximo e mínimo</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- VISUALIZAÇÕES -->
        <div class="section">
            <h2>📉 Visualizações</h2>

            <h3>Boxplot - Distribuição de Quartis e Outliers</h3>
            <div class="chart-container">
                {html_boxplot}
            </div>

            <h3>Histograma com Densidade Kernel (KDE)</h3>
            <div class="chart-container">
                {html_histogram}
            </div>
        </div>

        <!-- DADOS BRUTOS -->
        <div class="section">
            <h2>📋 Dados Brutos ({len(dados_limpos)} registros)</h2>

            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>Valor (°)</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Adicionar linhas da tabela de dados
    for idx, (_, row) in enumerate(dados_limpos.iterrows(), 1):
        lat = row.get('latitude', row.get('lat', 'N/A'))
        lon = row.get('longitude', row.get('lon', 'N/A'))
        val = row.get('valor', 'N/A')

        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>{lat:.6f if isinstance(lat, (int, float)) else lat}</td>
                        <td>{lon:.6f if isinstance(lon, (int, float)) else lon}</td>
                        <td><strong>{val:.2f if isinstance(val, (int, float)) else val}°</strong></td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </div>

        <!-- RODAPÉ -->
        <div class="footer">
            <p>Este relatório foi gerado automaticamente pela Plataforma Clima Urbano Interativo.</p>
            <p>Dados confidenciais - Uso restrito à pesquisa acadêmica.</p>
        </div>
    </div>
</body>
</html>
"""

    return html_content


def gerar_relatorio_automatico(dados_usuario, area_de_interesse_geojson, gdf_zcl_base):
    """Gera um relatório automático da análise."""

    relatorio = f"""# Relatório de Análise - Clima Urbano

**Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Plataforma:** Clima Urbano Interativo v2.0

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
    
    relatorio += """

## 🎓 Interpretação e Recomendações

### Principais Achados:
1. A análise espacial revelou a distribuição das Zonas Climáticas Locais na área de estudo
2. Os dados de campo permitiram quantificar as variações microclimáticas
3. A correlação entre ZCL e valores medidos fornece insights sobre o clima urbano local

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

