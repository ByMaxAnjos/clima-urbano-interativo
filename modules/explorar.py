# modules/explorar.py

import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.colormap import linear
import pandas as pd
import geopandas as gpd
import os
import base64
from io import StringIO
import sys
import traceback

# Importar funções LCZ4r
try:
    from utils.lcz4r import lcz_get_map, process_lcz_map, enhance_lcz_data
except ImportError as e:
    st.error(f"Erro ao importar módulo LCZ4r: {e}")

def load_logo():
    """Carrega o logo LCZ4r em base64."""
    try:
        logo_path = "assets/images/lcz4r_logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    return None

def processar_cidade_lcz4r(nome_cidade, progress_bar=None, status_text=None):
    """
    Processa uma cidade usando LCZ4r e retorna o GeoDataFrame.
    
    Parameters
    ----------
    nome_cidade : str
        Nome da cidade para processamento
    progress_bar : streamlit.progress, optional
        Barra de progresso do Streamlit
    status_text : streamlit.empty, optional
        Texto de status do Streamlit
    
    Returns
    -------
    geopandas.GeoDataFrame or None
        GeoDataFrame com dados LCZ processados
    """
    try:
        if status_text:
            status_text.text("🔍 Buscando cidade no OpenStreetMap...")
        if progress_bar:
            progress_bar.progress(10)
        
        # Download do mapa LCZ
        if status_text:
            status_text.text("📡 Baixando dados LCZ globais...")
        if progress_bar:
            progress_bar.progress(30)
            
        raster_data, raster_profile = lcz_get_map(city=nome_cidade)
        
        if status_text:
            status_text.text("🔄 Processando dados raster...")
        if progress_bar:
            progress_bar.progress(60)
        
        # Processar para formato vetorial
        lcz_gdf = process_lcz_map(raster_data, raster_profile, factor=5)
        
        if status_text:
            status_text.text("✨ Aprimorando dados LCZ...")
        if progress_bar:
            progress_bar.progress(80)
        
        # Aprimorar dados
        enhanced_gdf = enhance_lcz_data(lcz_gdf)
        
        if status_text:
            status_text.text("💾 Salvando arquivo GeoJSON...")
        if progress_bar:
            progress_bar.progress(90)
        
        # Salvar como map_lcz.geojson
        output_path = "data/map_lcz.geojson"
        enhanced_gdf.to_file(output_path, driver='GeoJSON')
        
        if status_text:
            status_text.text("✅ Processamento concluído!")
        if progress_bar:
            progress_bar.progress(100)
        
        return enhanced_gdf
        
    except Exception as e:
        error_msg = f"Erro no processamento LCZ4r: {str(e)}"
        if status_text:
            status_text.error(error_msg)
        st.error(error_msg)
        st.error("Detalhes do erro:")
        st.code(traceback.format_exc())
        return None

def carregar_dados_lcz():
    """Carrega dados LCZ existentes ou usa dados de exemplo."""
    # Tentar carregar map_lcz.geojson primeiro
    lcz_path = "data/map_lcz.geojson"
    if os.path.exists(lcz_path):
        try:
            gdf = gpd.read_file(lcz_path)
            return gdf, "Dados LCZ personalizados"
        except Exception as e:
            st.warning(f"Erro ao carregar {lcz_path}: {e}")
    
    # Fallback para dados de exemplo
    exemplo_path = "data/sao_paulo_zcl.geojson"
    if os.path.exists(exemplo_path):
        try:
            gdf = gpd.read_file(exemplo_path)
            return gdf, "Dados de exemplo (São Paulo)"
        except Exception as e:
            st.warning(f"Erro ao carregar dados de exemplo: {e}")
    
    return None, "Nenhum dado disponível"

def renderizar_pagina(gdf_zcl, gdf_temp):
    """Renderiza a página do módulo Explorar com integração LCZ4r."""
    
    # Header com logo LCZ4r
    logo_b64 = load_logo()
    
    if logo_b64:
        st.markdown(f"""
        <div class="module-header" style="display: flex; align-items: center; gap: 20px; margin-bottom: 30px;">
            <img src="data:image/png;base64,{logo_b64}" style="width: 80px; height: 80px;">
            <div>
                <h1 style="margin: 0;">🌍 Módulo Explorar</h1>
                <p style="margin: 5px 0 0 0; color: #666;">Gere e visualize mapas de Zonas Climáticas Locais personalizados com LCZ4r</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="module-header">
            <h1>🌍 Módulo Explorar</h1>
            <p>Gere e visualize mapas de Zonas Climáticas Locais personalizados com LCZ4r</p>
        </div>
        """, unsafe_allow_html=True)

    # Seção LCZ4r Generator
    st.markdown("### 🚀 Gerador de Mapas LCZ4r")
    
    with st.expander("🔧 Gerar Novo Mapa LCZ", expanded=False):
        st.markdown("""
        **LCZ4r** é uma ferramenta avançada para processamento de Zonas Climáticas Locais que permite:
        - 🌍 Gerar mapas LCZ para qualquer cidade do mundo
        - 📊 Processar dados de alta resolução automaticamente
        - 🗺️ Visualizar resultados de forma interativa
        - 💾 Salvar dados para análises futuras
        """)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            nome_cidade = st.text_input(
                "🏙️ Nome da Cidade:",
                placeholder="Ex: São Paulo, New York, London, Tokyo...",
                help="Digite o nome de qualquer cidade do mundo"
            )
        
        with col2:
            processar_button = st.button(
                "🚀 Gerar Mapa LCZ",
                type="primary",
                use_container_width=True
            )
        
        if processar_button and nome_cidade:
            with st.spinner("Processando dados LCZ4r..."):
                # Containers para progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Processar cidade
                novo_gdf = processar_cidade_lcz4r(nome_cidade, progress_bar, status_text)
                
                if novo_gdf is not None:
                    st.success(f"✅ Mapa LCZ gerado com sucesso para {nome_cidade}!")
                    st.info("O novo mapa substituiu os dados anteriores e está sendo exibido abaixo.")
                    
                    # Atualizar dados para visualização
                    gdf_zcl = novo_gdf
                    
                    # Mostrar estatísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Classes LCZ", len(novo_gdf['zcl_classe'].unique()))
                    with col2:
                        st.metric("Polígonos", len(novo_gdf))
                    with col3:
                        area_total = novo_gdf['area_km2'].sum() if 'area_km2' in novo_gdf.columns else 0
                        st.metric("Área Total", f"{area_total:.1f} km²")
                else:
                    st.error("❌ Falha no processamento. Verifique o nome da cidade e tente novamente.")
        
        elif processar_button and not nome_cidade:
            st.warning("⚠️ Por favor, digite o nome de uma cidade.")

    # Carregar dados LCZ atuais
    gdf_zcl_atual, fonte_dados = carregar_dados_lcz()
    if gdf_zcl_atual is not None:
        gdf_zcl = gdf_zcl_atual

    # Painel de controle na barra lateral
    with st.sidebar:
        st.markdown("### 🎛️ Controles de Visualização")
        
        # Status dos dados
        st.markdown(f"**📊 Dados Ativos:** {fonte_dados}")
        
        st.markdown("### 🗂️ Camadas de Dados")
        
        # Controles de camadas com descrições
        mostrar_zcl = st.checkbox(
            "🏘️ Zonas Climáticas Locais (ZCL)", 
            value=True,
            help="Mostra a classificação do uso do solo urbano segundo Stewart & Oke (2012)"
        )
        
        mostrar_temp = st.checkbox(
            "🌡️ Temperatura da Superfície", 
            value=False,
            help="Dados de temperatura obtidos por sensoriamento remoto"
        )
        
        # Informações sobre os dados
        if mostrar_zcl and gdf_zcl is not None and not gdf_zcl.empty:
            st.markdown("### ℹ️ Informações dos Dados")
            
            classes_unicas = gdf_zcl['zcl_classe'].unique()
            st.info(f"""
            **Classes LCZ Presentes:**
            {chr(10).join([f"- {classe}" for classe in sorted(classes_unicas)])}
            """)
            
        if mostrar_temp and gdf_temp is not None and not gdf_temp.empty:
            temp_min = gdf_temp['temperatura_c'].min()
            temp_max = gdf_temp['temperatura_c'].max()
            st.info(f"""
            **Temperatura:**
            - Mínima: {temp_min:.1f}°C
            - Máxima: {temp_max:.1f}°C
            - Fonte: Landsat 8 TIRS
            """)

    # Área principal do mapa
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if gdf_zcl is not None and not gdf_zcl.empty:
            # Configuração do mapa base
            bounds = gdf_zcl.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            map_center = [center_lat, center_lon]
            
            m = folium.Map(
                location=map_center, 
                zoom_start=11, 
                tiles="CartoDB positron",
                prefer_canvas=True
            )

            # Adicionar camada de ZCL se selecionada
            if mostrar_zcl:
                # Mapeamento de cores para as classes de ZCL (padrão LCZ4r)
                zcl_color_map = {
                    'LCZ 1': '#910613',    # Compact high-rise
                    'LCZ 2': '#D9081C',    # Compact midrise
                    'LCZ 3': '#FF0A22',    # Compact low-rise
                    'LCZ 4': '#C54F1E',    # Open high-rise
                    'LCZ 5': '#FF6628',    # Open midrise
                    'LCZ 6': '#FF985E',    # Open low-rise
                    'LCZ 7': '#FDED3F',    # Lightweight low-rise
                    'LCZ 8': '#BBBBBB',    # Large low-rise
                    'LCZ 9': '#FFCBAB',    # Sparsely built
                    'LCZ 10': '#565656',   # Heavy industry
                    'LCZ A': '#006A18',    # Dense trees
                    'LCZ B': '#00A926',    # Scattered trees
                    'LCZ C': '#628432',    # Bush, scrub
                    'LCZ D': '#B5DA7F',    # Low plants
                    'LCZ E': '#000000',    # Bare rock or paved
                    'LCZ F': '#FCF7B1',    # Bare soil or sand
                    'LCZ G': '#656BFA'     # Water
                }
                
                # Adiciona cada polígono de ZCL ao mapa
                for _, row in gdf_zcl.iterrows():
                    zcl_classe = row.get('zcl_classe', 'Desconhecida')
                    cor = zcl_color_map.get(zcl_classe, '#gray')
                    
                    # Informações para tooltip e popup
                    descricao = row.get('descricao', 'Sem descrição')
                    efeito_temp = row.get('efeito_temp', 'Sem informação')
                    area_info = f"Área: {row.get('area_km2', 0):.2f} km²" if 'area_km2' in row else ""
                    
                    folium.GeoJson(
                        row.geometry,
                        style_function=lambda feature, color=cor: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.7,
                            'opacity': 0.8
                        },
                        tooltip=folium.Tooltip(
                            f"""
                            <b>Zona Climática:</b> {zcl_classe}<br>
                            <b>Descrição:</b> {descricao}<br>
                            {area_info}
                            """,
                            sticky=True
                        ),
                        popup=folium.Popup(
                            f"""
                            <div style='width: 300px'>
                            <h4>{zcl_classe}</h4>
                            <p><b>Características:</b></p>
                            <p>{descricao}</p>
                            <p><b>Efeito Térmico:</b></p>
                            <p>{efeito_temp}</p>
                            {f'<p><b>{area_info}</b></p>' if area_info else ''}
                            </div>
                            """,
                            max_width=350
                        )
                    ).add_to(m)

            # Adicionar camada de temperatura se selecionada
            if mostrar_temp and gdf_temp is not None and not gdf_temp.empty:
                # Criar mapa de cores para temperatura
                temp_min = gdf_temp['temperatura_c'].min()
                temp_max = gdf_temp['temperatura_c'].max()
                
                colormap = linear.YlOrRd_09.scale(temp_min, temp_max)
                colormap.caption = 'Temperatura da Superfície (°C)'
                m.add_child(colormap)

                # Adiciona cada célula de temperatura ao mapa
                for _, row in gdf_temp.iterrows():
                    temp_valor = row['temperatura_c']
                    
                    folium.GeoJson(
                        row.geometry,
                        style_function=lambda feature, temp=temp_valor: {
                            'fillColor': colormap(temp),
                            'color': 'none',
                            'weight': 0,
                            'fillOpacity': 0.6,
                        },
                        tooltip=folium.Tooltip(
                            f"<b>Temperatura:</b> {temp_valor:.1f}°C",
                            sticky=True
                        )
                    ).add_to(m)

            # Adicionar controle de camadas
            folium.LayerControl().add_to(m)
            
            # Renderizar o mapa
            map_data = st_folium(
                m, 
                width=None, 
                height=600, 
                returned_objects=["last_object_clicked"],
                key="explorar_map"
            )
        else:
            st.warning("⚠️ Nenhum dado LCZ disponível. Use o gerador LCZ4r acima para criar um mapa.")
            st.info("💡 Dica: Digite o nome de uma cidade e clique em 'Gerar Mapa LCZ' para começar.")

    with col2:
        st.markdown("### 🎯 Instruções")
        st.markdown("""
        **Como usar:**
        1. 🚀 **Gerar novo mapa:** Use o gerador LCZ4r acima
        2. 🗂️ **Selecionar camadas:** Ative/desative na barra lateral
        3. 🖱️ **Explorar:** Clique nos elementos do mapa
        4. 🔍 **Zoom:** Use os controles para diferentes escalas
        """)
        
        # Mostrar informações do último clique
        if 'map_data' in locals() and map_data and map_data.get("last_object_clicked"):
            st.markdown("### 📍 Último Clique")
            clicked_data = map_data["last_object_clicked"]
            if clicked_data:
                st.json(clicked_data)
        
        # Estatísticas rápidas
        st.markdown("### 📊 Estatísticas Rápidas")
        
        if gdf_zcl is not None and not gdf_zcl.empty:
            num_zcl = len(gdf_zcl['zcl_classe'].unique())
            st.metric("Classes de ZCL", num_zcl)
            
            if 'area_km2' in gdf_zcl.columns:
                area_total = gdf_zcl['area_km2'].sum()
                st.metric("Área Total", f"{area_total:.1f} km²")
            
        if gdf_temp is not None and not gdf_temp.empty:
            temp_media = gdf_temp['temperatura_c'].mean()
            st.metric("Temp. Média", f"{temp_media:.1f}°C")

    # Seção de legenda expandida
    with st.expander("📖 Legenda Detalhada das Zonas Climáticas Locais"):
        st.markdown("""
        ### Zonas Construídas (Built Types)
        - **LCZ 1 - Compact high-rise:** Edifícios altos e compactos
        - **LCZ 2 - Compact midrise:** Edifícios de altura média e compactos  
        - **LCZ 3 - Compact low-rise:** Edifícios baixos e compactos
        - **LCZ 4 - Open high-rise:** Edifícios altos com espaços abertos
        - **LCZ 5 - Open midrise:** Edifícios de altura média com espaços abertos
        - **LCZ 6 - Open low-rise:** Edifícios baixos com espaços abertos
        - **LCZ 7 - Lightweight low-rise:** Edifícios baixos e leves
        - **LCZ 8 - Large low-rise:** Edifícios baixos e extensos
        - **LCZ 9 - Sparsely built:** Construções esparsas
        - **LCZ 10 - Heavy industry:** Indústria pesada
        
        ### Cobertura Natural (Land Cover Types)
        - **LCZ A - Dense trees:** Árvores densas
        - **LCZ B - Scattered trees:** Árvores esparsas
        - **LCZ C - Bush, scrub:** Arbustos e vegetação baixa
        - **LCZ D - Low plants:** Plantas baixas
        - **LCZ E - Bare rock or paved:** Rocha nua ou pavimentado
        - **LCZ F - Bare soil or sand:** Solo nu ou areia
        - **LCZ G - Water:** Corpos d'água
        """)

    # Informações sobre LCZ4r
    with st.expander("ℹ️ Sobre o LCZ4r"):
        st.markdown("""
        ### 🔬 LCZ4r - Local Climate Zone for R
        
        **LCZ4r** é uma ferramenta científica desenvolvida para processamento automatizado de Zonas Climáticas Locais (LCZ). 
        
        **Características principais:**
        - 🌍 **Cobertura global:** Processa qualquer cidade do mundo
        - 📊 **Alta resolução:** Dados de 100m de resolução espacial
        - 🔬 **Base científica:** Baseado na metodologia Stewart & Oke (2012)
        - 🚀 **Processamento automático:** Download e processamento em tempo real
        - 💾 **Formato padrão:** Saída em GeoJSON para máxima compatibilidade
        
        **Fonte de dados:** 
        - Mapa global LCZ v3 (Demuzere et al., 2022)
        - Disponível em: https://zenodo.org/records/8419340
        
        **Desenvolvido por:** Max Anjos  
        **GitHub:** https://github.com/ByMaxAnjos/LCZ4r
        """)

    # Dicas de uso
    st.markdown("""
    ---
    ### 💡 Dicas de Uso
    
    - **🌍 Explore globalmente:** Teste diferentes cidades ao redor do mundo
    - **🔄 Compare dados:** Gere mapas para cidades similares e compare padrões
    - **📊 Combine camadas:** Ative tanto ZCL quanto temperatura para análises integradas
    - **🔍 Analise escalas:** Use zoom para estudar desde regiões metropolitanas até quarteirões
    - **➡️ Próximo passo:** Vá para "Investigar" para análises detalhadas ou "Simular" para testar intervenções
    """)


    # Seção para Visualizar LCZ Map
    st.markdown("---")
    from utils.lcz_visualizer import renderizar_secao_visualizar_lcz
    renderizar_secao_visualizar_lcz()
