# utils/processamento.py

import io

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, shape
import streamlit as st
import numpy as np

# Cidades com dados-base de ZCL prontos para a análise no módulo Investigar/Visualizar
# (arquivo "temp" da Juiz de Fora reaproveita o zcl porque gdf_temp_base não é
# consumido por nenhum módulo hoje — ver comentário em app.py).
CIDADES_BASE = {
    "São Paulo": {
        "zcl": "sao_paulo_zcl.geojson",
        "temp": "sao_paulo_temp.geojson",
        "exemplo_csv": "exemplo_dados_sao_paulo.csv",
    },
    "Juiz de Fora": {
        "zcl": "juiz_de_fora_zcl.geojson",
        "temp": "juiz_de_fora_zcl.geojson",
        "exemplo_csv": "exemplo_dados_juiz_de_fora.csv",
    },
}


def carregar_dados_base(caminho_zcl, caminho_temp):
    """Carrega os arquivos GeoJSON base em GeoDataFrames."""
    try:
        gdf_zcl = gpd.read_file(caminho_zcl)
        gdf_temp = gpd.read_file(caminho_temp)
        return gdf_zcl, gdf_temp, None
    except Exception as e:
        return None, None, f"Erro ao carregar dados base: {e}. Verifique se os arquivos estão na pasta 'data/'."

def ler_csv_tolerante(arquivo_carregado):
    """
    Lê um CSV aceitando separador vírgula ou ponto-e-vírgula (detectado pela
    primeira linha). Retorna (DataFrame, separador_usado).
    """
    bruto = arquivo_carregado.read()
    texto = bruto.decode("utf-8", errors="replace") if isinstance(bruto, bytes) else bruto
    arquivo_carregado.seek(0)

    primeira_linha = texto.splitlines()[0] if texto else ""
    separador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","
    df = pd.read_csv(io.StringIO(texto), sep=separador)
    return df, separador


def detectar_colunas(df):
    """
    Tenta identificar as colunas de latitude, longitude e valor por nome
    (insensível a maiúsculas/minúsculas), aceitando aliases comuns como 'lng'.
    Retorna (lat_col, lon_col, val_col); cada um pode ser None se não encontrado.
    """
    lat_col = lon_col = val_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if lon_col is None and any(a in col_lower for a in ["lon", "lng", "lgn"]):
            lon_col = col
        elif lat_col is None and "lat" in col_lower:
            lat_col = col
        elif val_col is None and any(v in col_lower for v in ["val", "temp", "medida", "valor"]):
            val_col = col
    return lat_col, lon_col, val_col


def _coagir_numerico_tolerante(serie):
    """Converte para numérico aceitando tanto ponto quanto vírgula decimal."""
    numerico = pd.to_numeric(serie, errors="coerce")
    faltantes = numerico.isna() & serie.notna()
    if faltantes.any():
        alternativo = pd.to_numeric(
            serie.astype(str).str.replace(",", ".", regex=False), errors="coerce"
        )
        numerico = numerico.where(~faltantes, alternativo)
    return numerico


def validar_e_processar_csv(arquivo_carregado, lat_col=None, lon_col=None, val_col=None):
    """
    Lê um arquivo CSV carregado, identifica (ou recebe explicitamente) as colunas
    de latitude, longitude e valor, valida os dados e converte para um
    GeoDataFrame de pontos.

    lat_col/lon_col/val_col: nomes de coluna para sobrepor a detecção automática.

    Retorna (gdf_pontos, erro, info) onde info é um dict com:
      - 'colunas_detectadas': (lat_col, lon_col, val_col) usados
      - 'problemas_linha': lista de (numero_linha_original, motivos) removidos
      - 'separador': separador do CSV detectado
    """
    try:
        df, separador = ler_csv_tolerante(arquivo_carregado)

        lat_auto, lon_auto, val_auto = detectar_colunas(df)
        lat_col = lat_col or lat_auto
        lon_col = lon_col or lon_auto
        val_col = val_col or val_auto

        if not all([lat_col, lon_col, val_col]):
            return None, (
                "Não foi possível encontrar colunas de 'latitude', 'longitude' e 'valor' no "
                "arquivo. Verifique os nomes das colunas ou selecione-as manualmente."
            ), {"colunas_detectadas": (lat_col, lon_col, val_col), "problemas_linha": [], "separador": separador}

        # Renomeia para nomes padrão (mantém o índice original para reportar problemas por linha)
        df = df.rename(columns={lat_col: "latitude", lon_col: "longitude", val_col: "valor"})
        df["_linha_original"] = df.index + 2  # +2: cabeçalho (linha 1) + índice 0-based

        df["latitude"] = _coagir_numerico_tolerante(df["latitude"])
        df["longitude"] = _coagir_numerico_tolerante(df["longitude"])
        df["valor"] = _coagir_numerico_tolerante(df["valor"])

        problemas_linha = []
        for _, linha in df.iterrows():
            motivos = []
            if pd.isna(linha["latitude"]) or not (-90 <= linha["latitude"] <= 90):
                motivos.append("latitude ausente ou fora do intervalo [-90, 90]")
            if pd.isna(linha["longitude"]) or not (-180 <= linha["longitude"] <= 180):
                motivos.append("longitude ausente ou fora do intervalo [-180, 180]")
            if pd.isna(linha["valor"]):
                motivos.append("valor ausente ou não numérico")
            if motivos:
                problemas_linha.append((int(linha["_linha_original"]), motivos))

        linhas_invalidas = {n for n, _ in problemas_linha}
        df_valido = df[~df["_linha_original"].isin(linhas_invalidas)].drop(columns="_linha_original")

        info = {
            "colunas_detectadas": (lat_col, lon_col, val_col),
            "problemas_linha": problemas_linha,
            "separador": separador,
        }

        if df_valido.empty:
            return None, "Nenhuma linha válida encontrada no arquivo após a validação. Verifique os dados.", info

        geometry = [Point(xy) for xy in zip(df_valido["longitude"], df_valido["latitude"])]
        gdf_pontos = gpd.GeoDataFrame(df_valido, geometry=geometry, crs="EPSG:4326")

        return gdf_pontos, None, info

    except Exception as e:
        return None, f"Erro inesperado ao processar o arquivo: {e}", {"colunas_detectadas": (lat_col, lon_col, val_col), "problemas_linha": [], "separador": None}


def calcular_area_poligono_m2(geojson_geometry):
    """
    Calcula a área de uma geometria GeoJSON (em WGS84) em metros quadrados,
    reprojetando para um CRS UTM estimado a partir da própria geometria — método
    geograficamente correto, ao contrário de aproximações em graus (ex.: * 111km²).
    """
    if not geojson_geometry:
        return 0.0
    try:
        geom = shape(geojson_geometry)
        gdf = gpd.GeoDataFrame([1], geometry=[geom], crs="EPSG:4326")
        crs_utm = gdf.estimate_utm_crs()
        return float(gdf.to_crs(crs_utm).geometry.area.iloc[0])
    except Exception:
        return 0.0

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
        # Calcula a área em um CRS UTM estimado a partir dos dados (funciona para qualquer região,
        # não apenas São Paulo)
        crs_utm = gdf_zcl_filtrado.estimate_utm_crs()
        gdf_proj = gdf_zcl_filtrado.to_crs(crs_utm)
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