# utils/lcz_visualizer.py

import streamlit as st
import os
import tempfile
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from utils.lcz4r import lcz_plot_map, lcz_get_map, process_lcz_map
import base64
from io import BytesIO

def criar_visualizacao_lcz(titulo_personalizado=None, qualidade_alta=True):
    """
    Cria visualização do mapa LCZ usando lcz_plot_map.
    
    Parameters
    ----------
    titulo_personalizado : str, optional
        Título personalizado para o mapa
    qualidade_alta : bool, default True
        Se True, gera imagem em alta resolução
    
    Returns
    -------
    tuple
        (figura matplotlib, caminho do arquivo salvo)
    """
    try:
        # Verificar se existe mapa LCZ gerado
        lcz_path = "data/map_lcz.geojson"
        if not os.path.exists(lcz_path):
            st.error("❌ Nenhum mapa LCZ encontrado. Gere um mapa primeiro usando o gerador LCZ4r.")
            return None, None
        
        # Carregar dados LCZ
        gdf_lcz = gpd.read_file(lcz_path)
        
        # Verificar se há dados raster salvos
        raster_path = "LCZ4r_output/lcz_map.tif"
        if os.path.exists(raster_path):
            # Usar dados raster se disponíveis
            with rasterio.open(raster_path) as src:
                data = src.read(1)
                profile = src.profile
            raster_data = (data, profile)
        else:
            st.warning("⚠️ Dados raster não encontrados. A visualização pode não estar disponível.")
            return None, None
        
        # Configurar parâmetros de qualidade
        if qualidade_alta:
            figsize = (16, 12)
            dpi = 300
            save_extension = "png"
        else:
            figsize = (12, 8)
            dpi = 150
            save_extension = "png"
        
        # Criar diretório de saída se não existir
        os.makedirs("LCZ4r_output", exist_ok=True)
        
        # Configurar título
        kwargs = {}
        if titulo_personalizado:
            kwargs['title'] = titulo_personalizado
        else:
            kwargs['title'] = "Mapa de Zonas Climáticas Locais (LCZ)"
        
        # Gerar visualização usando lcz_plot_map
        fig = lcz_plot_map(
            raster_data,
            isave=True,
            show_legend=True,
            save_extension=save_extension,
            figsize=figsize,
            **kwargs
        )
        
        # Caminho do arquivo salvo
        output_path = f"LCZ4r_output/lcz_plot_map.{save_extension}"
        
        return fig, output_path
        
    except Exception as e:
        st.error(f"❌ Erro ao criar visualização: {str(e)}")
        return None, None

def preparar_download_raster():
    """
    Prepara arquivo raster para download.
    
    Returns
    -------
    str or None
        Caminho do arquivo raster se disponível
    """
    raster_path = "LCZ4r_output/lcz_map.tif"
    if os.path.exists(raster_path):
        return raster_path
    else:
        st.warning("⚠️ Arquivo raster não encontrado. Gere um mapa LCZ primeiro.")
        return None

def preparar_download_imagem(caminho_imagem):
    """
    Prepara arquivo de imagem para download.
    
    Parameters
    ----------
    caminho_imagem : str
        Caminho para o arquivo de imagem
    
    Returns
    -------
    bytes or None
        Dados da imagem em bytes para download
    """
    try:
        if os.path.exists(caminho_imagem):
            with open(caminho_imagem, "rb") as f:
                return f.read()
        else:
            st.warning("⚠️ Arquivo de imagem não encontrado.")
            return None
    except Exception as e:
        st.error(f"❌ Erro ao preparar download da imagem: {str(e)}")
        return None

def exibir_preview_imagem(caminho_imagem):
    """
    Exibe preview da imagem gerada.
    
    Parameters
    ----------
    caminho_imagem : str
        Caminho para o arquivo de imagem
    """
    try:
        if os.path.exists(caminho_imagem):
            st.image(caminho_imagem, caption="Preview do Mapa LCZ Gerado", use_container_width=True)
        else:
            st.warning("⚠️ Preview não disponível.")
    except Exception as e:
        st.error(f"❌ Erro ao exibir preview: {str(e)}")

def obter_informacoes_mapa():
    """
    Obtém informações sobre o mapa LCZ atual.
    
    Returns
    -------
    dict or None
        Dicionário com informações do mapa
    """
    try:
        lcz_path = "data/map_lcz.geojson"
        if os.path.exists(lcz_path):
            gdf = gpd.read_file(lcz_path)
            
            info = {
                'classes_lcz': len(gdf['zcl_classe'].unique()) if 'zcl_classe' in gdf.columns else 0,
                'total_poligonos': len(gdf),
                'area_total_km2': gdf['area_km2'].sum() if 'area_km2' in gdf.columns else 0,
                'classes_presentes': sorted(gdf['zcl_classe'].unique()) if 'zcl_classe' in gdf.columns else []
            }
            return info
        else:
            return None
    except Exception as e:
        st.error(f"❌ Erro ao obter informações do mapa: {str(e)}")
        return None

def renderizar_secao_visualizar_lcz():
    """
    Renderiza a seção completa de visualização LCZ Map.
    """
    st.markdown("### 🎨 Visualizar LCZ Map")
    
    # Verificar se há dados disponíveis
    info_mapa = obter_informacoes_mapa()
    
    if info_mapa is None:
        st.warning("⚠️ Nenhum mapa LCZ disponível. Gere um mapa primeiro usando o gerador LCZ4r acima.")
        return
    
    # Exibir informações do mapa atual
    with st.expander("ℹ️ Informações do Mapa Atual", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Classes LCZ", info_mapa['classes_lcz'])
        with col2:
            st.metric("Polígonos", info_mapa['total_poligonos'])
        with col3:
            st.metric("Área Total", f"{info_mapa['area_total_km2']:.1f} km²")
        
        if info_mapa['classes_presentes']:
            st.write("**Classes LCZ Presentes:**")
            st.write(", ".join(info_mapa['classes_presentes']))
    
    # Interface de configuração
    st.markdown("#### ⚙️ Configurações de Visualização")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        titulo_personalizado = st.text_input(
            "🏷️ Título do Mapa (opcional):",
            placeholder="Ex: Zonas Climáticas Locais - Rio de Janeiro",
            help="Deixe em branco para usar o título padrão"
        )
    
    with col2:
        qualidade_alta = st.checkbox(
            "📸 Alta Resolução",
            value=True,
            help="Gera imagem em 300 DPI para melhor qualidade"
        )
    
    # Botão para gerar visualização
    if st.button("🎨 Gerar Visualização", type="primary", use_container_width=True):
        with st.spinner("Gerando visualização de alta qualidade..."):
            fig, caminho_imagem = criar_visualizacao_lcz(titulo_personalizado, qualidade_alta)
            
            if fig is not None and caminho_imagem is not None:
                st.success("✅ Visualização gerada com sucesso!")
                
                # Armazenar no session state para downloads
                st.session_state['lcz_imagem_path'] = caminho_imagem
                st.session_state['lcz_titulo'] = titulo_personalizado or "Mapa LCZ"
                
                # Exibir preview
                st.markdown("#### 🖼️ Preview da Visualização")
                exibir_preview_imagem(caminho_imagem)
                
                # Fechar a figura para liberar memória
                plt.close(fig)
    
    # Seção de downloads
    if 'lcz_imagem_path' in st.session_state:
        st.markdown("#### 📥 Downloads Disponíveis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download da imagem PNG
            dados_imagem = preparar_download_imagem(st.session_state['lcz_imagem_path'])
            if dados_imagem:
                st.download_button(
                    label="📸 Baixar Imagem PNG",
                    data=dados_imagem,
                    file_name="lcz_plot_map.png",
                    mime="image/png",
                    help="Imagem do mapa LCZ em alta resolução",
                    use_container_width=True
                )
        
        with col2:
            # Download do arquivo raster
            raster_path = preparar_download_raster()
            if raster_path:
                with open(raster_path, "rb") as f:
                    dados_raster = f.read()
                
                st.download_button(
                    label="🗺️ Baixar Raster TIF",
                    data=dados_raster,
                    file_name="lcz_map.tif",
                    mime="image/tiff",
                    help="Arquivo raster do mapa LCZ para análises GIS",
                    use_container_width=True
                )
        
        # Informações sobre os formatos
        with st.expander("ℹ️ Sobre os Formatos de Download"):
            st.markdown("""
            **📸 lcz_plot_map.png:**
            - Imagem de alta resolução (300 DPI) do mapa LCZ
            - Inclui legenda completa e título personalizado
            - Ideal para apresentações, relatórios e publicações
            - Formato: PNG com transparência
            
            **🗺️ lcz_map.tif:**
            - Arquivo raster geoespacial do mapa LCZ
            - Mantém informações de projeção e coordenadas
            - Compatível com softwares GIS (QGIS, ArcGIS, etc.)
            - Formato: GeoTIFF com metadados espaciais
            """)
    
    # Dicas de uso
    st.markdown("""
    ---
    ### 💡 Dicas para Visualização LCZ
    
    - **🎨 Personalize o título:** Adicione informações específicas como nome da cidade e data
    - **📸 Use alta resolução:** Para apresentações e publicações acadêmicas
    - **🗺️ Combine formatos:** Use PNG para visualização e TIF para análises espaciais
    - **🔄 Atualize conforme necessário:** Gere novas visualizações após criar mapas para outras cidades
    """)
