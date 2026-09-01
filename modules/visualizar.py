# modules/visualizar.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from utils import processamento
from utils.navegacao import ir_para
from utils.ui import renderizar_cabecalho_modulo

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
                    st.caption("A composição mostra como a área se divide entre diferentes formas urbanas e coberturas.")
                    
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

    st.caption("Média = valor típico · Desvio padrão = variação entre pontos · Amplitude = distância entre menor e maior valor.")
    
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
