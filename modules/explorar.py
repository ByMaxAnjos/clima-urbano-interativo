# modules/explorar.py

import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib
import base64
from io import BytesIO
import tempfile
import rasterio
from utils.lcz4r import lcz_get_map, process_lcz_map, enhance_lcz_data, lcz_plot_map

# Configurar matplotlib para usar backend não-interativo
matplotlib.use('Agg')

def renderizar_pagina():
    """Renderiza a página do módulo Explorar com organização correta."""
    
    # Cabeçalho do módulo
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
            <img src="data:image/png;base64,{}" width="80" style="border-radius: 10px;">
            <div>
                <h1 style="color: white; margin: 0; font-size: 2.5rem;">🌍 Módulo Explorar</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1.2rem;">
                    Gere e visualize mapas de Zonas Climáticas Locais (LCZ) interativos
                </p>
            </div>
        </div>
    </div>
    """.format(get_logo_base64()), unsafe_allow_html=True)
    
    # 1. GERADOR DE MAPAS LCZ4r
    st.markdown("## 🚀 Gerador de Mapas LCZ4r")
    
    with st.expander("🔧 Gerar Novo Mapa LCZ", expanded=False):
        st.markdown("""
        **LCZ4r** é uma ferramenta avançada para processamento de Zonas Climáticas Locais que permite:
        
        - 🌍 Gerar mapas LCZ para qualquer cidade do mundo
        - 📊 Processar dados de alta resolução automaticamente  
        - 🗺️ Visualizar resultados de forma interativa
        - 💾 Salvar dados para análises futuras
        """)
        
        # Interface de entrada
        col1, col2 = st.columns([3, 1])
        with col1:
            cidade_nome = st.text_input(
                "🏙️ Nome da Cidade:",
                placeholder="Ex: São Paulo, New York, London, Tokyo...",
                help="Digite o nome da cidade para gerar o mapa LCZ"
            )
        
        with col2:
            gerar_mapa = st.button("🚀 Gerar Mapa LCZ", type="primary", width='stretch')
        
        # Processamento do mapa
        if gerar_mapa and cidade_nome:
            processar_mapa_lcz(cidade_nome)
    
    # 2. VISUALIZAR LCZ MAP COM MATPLOTLIB
    st.markdown("---")
    st.markdown("## 🎨 Visualizar LCZ Map")
    
    # Verificar se existe mapa gerado
    if verificar_dados_disponiveis():
        renderizar_secao_matplotlib()
    else:
        st.info("ℹ️ Gere um mapa LCZ primeiro para visualizar os resultados.")
    
    # 3. VISUALIZAR COM FOLIUM GEOJSON
    st.markdown("---")
    st.markdown("## 🗺️ Mapa Interativo")
    
    if verificar_dados_disponiveis():
        renderizar_mapa_folium()
    else:
        st.info("ℹ️ Gere um mapa LCZ primeiro para visualizar o mapa interativo.")
    
    # Instruções finais
    st.markdown("---")
    st.markdown("""
    ### 💡 Como Usar o Módulo Explorar
    
    1. **🚀 Gere um Mapa:** Use o gerador LCZ4r para criar um mapa para sua cidade de interesse
    2. **🎨 Visualize:** Veja o mapa em formato científico com matplotlib
    3. **🗺️ Explore:** Interaja com o mapa usando a interface Folium
    4. **➡️ Próximo passo:** Vá para "Investigar" para análises detalhadas ou "Simular" para testar intervenções
    """)

def get_logo_base64():
    """Retorna o logo LCZ4r em base64."""
    try:
        logo_path = "assets/images/lcz4r_logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

def processar_mapa_lcz(cidade_nome):
    """Processa e gera o mapa LCZ para a cidade especificada."""
    
    # Barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Etapa 1: Download dos dados
        status_text.text("📡 Baixando dados LCZ globais...")
        progress_bar.progress(25)
        
        data, profile = lcz_get_map(cidade_nome)
        
        # Etapa 2: Processamento
        status_text.text("⚙️ Processando dados LCZ...")
        progress_bar.progress(50)
        
        lcz_gdf = process_lcz_map(data, profile)
        
        # Etapa 3: Aprimoramento
        status_text.text("✨ Aprimorando dados...")
        progress_bar.progress(75)
        
        enhanced_gdf = enhance_lcz_data(lcz_gdf)
        
        # Etapa 4: Salvamento
        status_text.text("💾 Salvando resultados...")
        progress_bar.progress(90)
        
        # Criar diretórios se não existirem
        os.makedirs("data", exist_ok=True)
        os.makedirs("LCZ4r_output", exist_ok=True)
        
        # Salvar GeoJSON
        enhanced_gdf.to_file("data/map_lcz.geojson", driver="GeoJSON")
        
        # Salvar dados raster para visualização matplotlib
        with rasterio.open("LCZ4r_output/lcz_map.tif", 'w', **profile) as dst:
            dst.write(data, 1)
        
        # Finalização
        progress_bar.progress(100)
        status_text.text("✅ Processamento concluído!")
        
        # Exibir métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Classes LCZ", len(enhanced_gdf['zcl_classe'].unique()))
        with col2:
            st.metric("Polígonos", len(enhanced_gdf))
        with col3:
            area_total = enhanced_gdf['area_km2'].sum() if 'area_km2' in enhanced_gdf.columns else 0
            st.metric("Área Total", f"{area_total:.1f} km²")
        
        st.success(f"✅ Mapa LCZ gerado com sucesso para {cidade_nome}!")
        st.info("📍 O novo mapa substituiu os dados anteriores e está sendo exibido abaixo.")
        
        # Forçar rerun para atualizar as seções
        st.rerun()
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"❌ Erro ao processar mapa: {str(e)}")

def verificar_dados_disponiveis():
    """Verifica se existem dados LCZ disponíveis."""
    geojson_path = "data/map_lcz.geojson"
    raster_path = "LCZ4r_output/lcz_map.tif"
    return os.path.exists(geojson_path) and os.path.exists(raster_path)

def renderizar_secao_matplotlib():
    """Renderiza a seção de visualização com matplotlib."""
    
    st.markdown("### ⚙️ Configurações de Visualização")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        titulo_personalizado = st.text_input(
            "🏷️ Título do Mapa (opcional):",
            placeholder="Ex: Zonas Climáticas Locais - Rio de Janeiro",
            help="Deixe em branco para usar o título padrão"
        )
    
    with col2:
        alta_resolucao = st.checkbox(
            "📸 Alta Resolução",
            value=True,
            help="Gera imagem em 300 DPI para melhor qualidade"
        )
    
    # Botão para gerar visualização
    if st.button("🎨 Gerar Visualização", type="primary", width='stretch'):
        gerar_visualizacao_matplotlib(titulo_personalizado, alta_resolucao)

def gerar_visualizacao_matplotlib(titulo_personalizado=None, alta_resolucao=True):
    """Gera visualização usando matplotlib e lcz_plot_map."""
    
    with st.spinner("Gerando visualização de alta qualidade..."):
        try:
            # Carregar dados raster
            raster_path = "LCZ4r_output/lcz_map.tif"
            with rasterio.open(raster_path) as src:
                data = src.read(1)
                profile = src.profile
            
            # Configurar parâmetros
            figsize = (16, 12) if alta_resolucao else (12, 8)
            dpi = 300 if alta_resolucao else 150
            
            # Configurar título
            titulo = titulo_personalizado if titulo_personalizado else "Mapa de Zonas Climáticas Locais (LCZ)"
            
            # Gerar visualização usando lcz_plot_map
            plt.figure(figsize=figsize, dpi=dpi)
            fig = lcz_plot_map(
                (data, profile),
                title=titulo,
                show_legend=True,
                isave=False  # Não salvar automaticamente
            )
            
            # Salvar em buffer para exibição
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            
            # Exibir a imagem
            st.markdown("#### 🖼️ Visualização Gerada")
            st.image(buf, caption=titulo, width='stretch')
            
            # Salvar arquivo para download
            output_path = "LCZ4r_output/lcz_plot_map.png"
            plt.savefig(output_path, format='png', dpi=dpi, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            
            # Botões de download
            col1, col2 = st.columns(2)
            
            with col1:
                # Download da imagem PNG
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📸 Baixar Imagem PNG",
                        data=f.read(),
                        file_name="lcz_plot_map.png",
                        mime="image/png",
                        help="Imagem do mapa LCZ em alta resolução",
                        width='stretch'
                    )
            
            with col2:
                # Download do arquivo raster
                raster_path = "LCZ4r_output/lcz_map.tif"
                if os.path.exists(raster_path):
                    with open(raster_path, "rb") as f:
                        st.download_button(
                            label="🗺️ Baixar Raster TIF",
                            data=f.read(),
                            file_name="lcz_map.tif",
                            mime="image/tiff",
                            help="Arquivo raster do mapa LCZ para análises GIS",
                            width='stretch'
                        )
            
            plt.close(fig)  # Liberar memória
            st.success("✅ Visualização gerada com sucesso!")
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar visualização: {str(e)}")

def renderizar_mapa_folium():
    """Renderiza o mapa interativo com Folium."""
    
    try:
        # Carregar dados GeoJSON
        gdf_lcz = gpd.read_file("data/map_lcz.geojson")
        
        if gdf_lcz.empty:
            st.warning("⚠️ Dados LCZ não encontrados.")
            return
        
        # Calcular centro do mapa
        bounds = gdf_lcz.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Criar mapa base
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Definir cores para as classes LCZ
        cores_lcz = {
            'LCZ 1': '#8B0000', 'LCZ 2': '#CD5C5C', 'LCZ 3': '#F0E68C',
            'LCZ 4': '#FFD700', 'LCZ 5': '#FFA500', 'LCZ 6': '#FF8C00',
            'LCZ 7': '#FF6347', 'LCZ 8': '#FF4500', 'LCZ 9': '#DC143C',
            'LCZ 10': '#B22222', 'LCZ A': '#228B22', 'LCZ B': '#32CD32',
            'LCZ C': '#90EE90', 'LCZ D': '#98FB98', 'LCZ E': '#AFEEEE',
            'LCZ F': '#87CEEB', 'LCZ G': '#4682B4'
        }
        
        # Adicionar camada GeoJSON
        for idx, row in gdf_lcz.iterrows():
            classe = row.get('zcl_classe', 'Desconhecida')
            cor = cores_lcz.get(classe, '#808080')
            
            folium.GeoJson(
                    row.geometry,
                    style_function=lambda feature, color=cor: {
                        'fillColor': color,
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.7,
                        'opacity': 0.8
                    },
                    popup=folium.Popup(
                        f"""
                        <div style='width: 200px'>
                        <h4>{classe}</h4>
                        <p><b>Características:</b></p>
                        <p>{row.get('descricao', 'Sem descrição disponível')}</p>
                        <p><b>Efeito Térmico:</b> {row.get('efeito_temp', 'Não disponível')}</p>
                        <p><b>Ilha de Calor:</b> {row.get('ilha_calor', 'Não disponível')}</p>
                        <p><b>Intervenção Recomendada:</b> {row.get('intervencao', 'Não disponível')}</p>
                        </div>
                        """,
                        max_width=250
                    )
                ).add_to(m)
        
        # Ajustar zoom aos dados
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Adicionar controles
        folium.LayerControl().add_to(m)
        
        # Instruções de uso
        st.markdown("""
        #### 🎯 Instruções
        
        **Como usar:**
        1. 🖱️ **Gerar novo mapa:** Use o gerador LCZ4r acima
        2. 📍 **Selecionar camadas:** Ative/desative na barra lateral  
        3. ✨ **Explorar:** Clique nos elementos do mapa
        4. 🔍 **Zoom:** Use os controles para diferentes escalas
        """)
        
        # Exibir mapa
        map_data = st_folium(m, width=700, height=500, returned_objects=["last_object_clicked"])
        
        # Exibir informações do clique
        if map_data['last_object_clicked']:
            st.info(f"🎯 Último elemento clicado: {map_data['last_object_clicked']}")
        
        # Estatísticas do mapa
        with st.expander("📊 Estatísticas do Mapa", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Classes LCZ", len(gdf_lcz['zcl_classe'].unique()))
            
            with col2:
                st.metric("Total de Polígonos", len(gdf_lcz))
            
            with col3:
                area_total = gdf_lcz['area_km2'].sum() if 'area_km2' in gdf_lcz.columns else 0
                st.metric("Área Total", f"{area_total:.1f} km²")
            
            # Distribuição por classe
            if 'zcl_classe' in gdf_lcz.columns:
                st.markdown("**Distribuição por Classe LCZ:**")
                distribuicao = gdf_lcz['zcl_classe'].value_counts()
                st.bar_chart(distribuicao)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar mapa: {str(e)}")