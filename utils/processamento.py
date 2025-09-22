# utils/processamento.py

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import streamlit as st

def carregar_dados_base(caminho_zcl, caminho_temp):
    """Carrega os arquivos GeoJSON base em GeoDataFrames."""
    try:
        gdf_zcl = gpd.read_file(caminho_zcl)
        gdf_temp = gpd.read_file(caminho_temp)
        return gdf_zcl, gdf_temp, None
    except Exception as e:
        return None, None, f"Erro ao carregar dados base: {e}. Verifique se os arquivos estão na pasta 'data/'."

def validar_e_processar_csv(arquivo_carregado):
    """
    Lê um arquivo CSV carregado, valida as colunas essenciais (lat, lon, valor)
    e o converte para um GeoDataFrame de pontos.
    """
    try:
        df = pd.read_csv(arquivo_carregado)
        
        # Tenta encontrar colunas de latitude, longitude e valor (insensível a maiúsculas/minúsculas)
        lat_col = None
        lon_col = None
        val_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'lat' in col_lower and lat_col is None:
                lat_col = col
            elif 'lon' in col_lower and lon_col is None:
                lon_col = col
            elif any(v in col_lower for v in ['val', 'temp', 'medida', 'valor']) and val_col is None:
                val_col = col
        
        if not all([lat_col, lon_col, val_col]):
            return None, "Não foi possível encontrar colunas de 'latitude', 'longitude' e 'valor' no arquivo. Verifique se as colunas têm nomes apropriados."

        # Renomeia para nomes padrão
        df = df.rename(columns={lat_col: 'latitude', lon_col: 'longitude', val_col: 'valor'})

        # Converte para numérico, forçando erros a se tornarem NaN
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

        # Remove linhas com valores nulos nas colunas essenciais
        df_original_len = len(df)
        df.dropna(subset=['latitude', 'longitude', 'valor'], inplace=True)

        if df.empty:
            return None, "Nenhuma linha válida encontrada no arquivo após a limpeza. Verifique os dados."

        # Cria geometrias de ponto
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        gdf_pontos = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
        linhas_removidas = df_original_len - len(df)
        mensagem_sucesso = f"{len(gdf_pontos)} pontos carregados com sucesso!"
        if linhas_removidas > 0:
            mensagem_sucesso += f" ({linhas_removidas} linhas com dados inválidos foram removidas)"
            
        return gdf_pontos, None
        
    except Exception as e:
        return None, f"Erro inesperado ao processar o arquivo: {e}"

def filtrar_dados_por_area(gdf, area_de_interesse_geojson):
    """
    Filtra um GeoDataFrame para manter apenas o que está dentro da 'area_de_interesse'.
    """
    if not area_de_interesse_geojson or gdf.empty:
        return gdf # Se não há área ou dados, retorna todos os dados

    try:
        # Extrai as coordenadas do GeoJSON
        if area_de_interesse_geojson['type'] == 'Polygon':
            coords = area_de_interesse_geojson['coordinates'][0]
        else:
            return gdf.iloc[0:0]  # Retorna GDF vazio se não for polígono
            
        poly = Polygon(coords)
        area_gdf = gpd.GeoDataFrame([1], geometry=[poly], crs="EPSG:4326")
        dados_filtrados = gpd.clip(gdf, area_gdf)
        return dados_filtrados
    except Exception as e:
        st.error(f"Erro ao filtrar dados por área: {e}")
        return gdf.iloc[0:0]  # Retorna GDF vazio em caso de erro

def juntar_dados_espaciais(pontos_usuario, gdf_zcl):
    """
    Junta espacialmente os pontos do usuário com as ZCLs.
    """
    if pontos_usuario.empty or gdf_zcl.empty:
        return pontos_usuario
    
    try:
        # Realiza o spatial join
        pontos_com_zcl = gpd.sjoin(pontos_usuario, gdf_zcl, how="left", predicate="within")
        return pontos_com_zcl
    except Exception as e:
        st.error(f"Erro ao juntar dados espaciais: {e}")
        return pontos_usuario

def calcular_estatisticas_area(gdf_zcl_filtrado):
    """
    Calcula estatísticas básicas sobre a composição de ZCL em uma área.
    """
    if gdf_zcl_filtrado.empty:
        return {}
    
    try:
        # Calcula a área em um CRS projetado para obter valores em m²
        gdf_proj = gdf_zcl_filtrado.to_crs(epsg=32723)  # UTM Zone 23S para São Paulo
        gdf_proj['area_m2'] = gdf_proj.geometry.area
        
        # Agrupa por classe de ZCL
        stats = gdf_proj.groupby('zcl_classe')['area_m2'].agg(['sum', 'count']).reset_index()
        stats['percentual'] = (stats['sum'] / stats['sum'].sum()) * 100
        
        return {
            'total_area_m2': stats['sum'].sum(),
            'composicao': stats.to_dict('records'),
            'num_classes': len(stats)
        }
    except Exception as e:
        st.error(f"Erro ao calcular estatísticas: {e}")
        return {}

