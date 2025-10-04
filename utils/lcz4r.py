# -*- coding: utf-8 -*-
"""
LCZ Platform Tool - Processamento e Visualização de Zonas Climáticas Locais

Script otimizado para download, processamento e visualização de dados LCZ

https://colab.research.google.com/drive/1ZdReMbnI_7VSSS0ALpnb-O1Mie2BnPKw
"""

import os
import warnings
import tempfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio import features
from rasterio.crs import CRS
import rasterio.plot
import osmnx as ox
from shapely.geometry import box, shape
import requests
import shutil
import time
from urllib3.exceptions import NewConnectionError

# Configurações
warnings.filterwarnings("ignore")
plt.rcParams["figure.dpi"] = 150

# Informações LCZ (constante global)
LCZ_INFO = pd.DataFrame({
    "lcz": range(1, 18),
    "zcl_classe": [
        "LCZ 1", "LCZ 2", "LCZ 3", "LCZ 4", "LCZ 5", "LCZ 6", "LCZ 7",
        "LCZ 8", "LCZ 9", "LCZ 10", "LCZ A", "LCZ B", "LCZ C", "LCZ D",
        "LCZ E", "LCZ F", "LCZ G"
    ],
    "descricao": [
        "Compact high-rise – arranha-céus compactos",
        "Compact midrise – edifícios médios compactos",
        "Compact low-rise – edificações baixas compactas",
        "Open high-rise – torres altas espaçadas",
        "Open midrise – edifícios médios espaçados",
        "Open low-rise – casas baixas espaçadas",
        "Lightweight low-rise – construções leves, informais",
        "Large low-rise – galpões, shoppings, indústrias",
        "Sparsely built – edificações esparsas",
        "Heavy industry – áreas industriais pesadas",
        "Dense trees – florestas urbanas densas",
        "Scattered trees – árvores dispersas",
        "Bush, scrub – vegetação arbustiva",
        "Low plants – gramados, campos",
        "Bare rock or paved – solo exposto/pavimento",
        "Bare soil or sand – solo nu ou areia",
        "Water – rios, lagos, oceanos"
    ],
    "efeito_temp": [
        "Maior retenção de calor urbano, forte aquecimento noturno.",
        "Alta absorção de calor, pouca ventilação.",
        "Aquecimento elevado, mas menos intenso que arranha-céus.",
        "Aquecimento reduzido pela ventilação, mas forte calor diurno.",
        "Aquecimento moderado, ventilação razoável.",
        "Aquecimento leve, efeito térmico relativamente baixo.",
        "Materiais leves podem aquecer rapidamente durante o dia.",
        "Superfícies extensas acumulam calor e irradiam à noite.",
        "Aquecimento baixo a moderado, dependendo da densidade.",
        "Alto aquecimento devido a superfícies industriais impermeáveis.",
        "Resfriamento significativo por sombreamento e evapotranspiração.",
        "Redução moderada da temperatura, com ventilação importante.",
        "Pequeno efeito de resfriamento; limitada evapotranspiração.",
        "Suaviza temperaturas durante o dia, pouco efeito noturno.",
        "Pode intensificar calor local (ilha de calor de superfície).",
        "Contribuição moderada de superfície nua.",
        "Mitiga a ilha de calor, pode até resfriar microclimas."
    ],
    "ilha_calor": [
        "Muito forte contribuição à ilha de calor urbana.",
        "Forte contribuição à ilha de calor urbana.",
        "Forte contribuição, mas menor que LCZ 1–2.",
        "Contribuição moderada devido à ventilação.",
        "Contribuição moderada.",
        "Contribuição baixa.",
        "Contribuição variável, geralmente moderada.",
        "Pode gerar ilhas de calor locais industriais/comerciais.",
        "Contribuição baixa, mas pode acumular calor localmente.",
        "Contribuição alta, especialmente noturna.",
        "Mitigação significativa da ilha de calor.",
        "Mitigação moderada.",
        "Mitigação leve.",
        "Mitigação leve a moderada.",
        "Pode intensificar calor local (ilha de calor de superfície).",
        "Contribuição moderada de superfície nua.",
        "Mitiga a ilha de calor, pode até resfriar microclimas."
    ],
    "intervencao": [
        "Criar ventilação urbana, áreas verdes verticais, telhados frios.",
        "Ampliar áreas verdes, incentivar telhados verdes/reforçar ventilação.",
        "Manter corredores de ventilação e arborização.",
        "Integrar áreas verdes entre torres, favorecer ventilação cruzada.",
        "Preservar ventilação e arborizar ruas.",
        "Expandir vegetação urbana e reduzir impermeabilização.",
        "Melhorar infraestrutura urbana e aumentar vegetação.",
        "Aplicar coberturas frias, reduzir pavimentação impermeável.",
        "Evitar adensamento excessivo, introduzir arborização.",
        "Controlar emissões e aumentar arborização periférica.",
        "Preservar e ampliar parques urbanos.",
        "Aumentar densidade arbórea e conectar corredores verdes.",
        "Revegetar e controlar ocupação irregular.",
        "Expandir áreas permeáveis e gramados.",
        "Substituir por pavimentos frios, introduzir arborização.",
        "Revegetar áreas expostas ou estabilizar solos.",
        "Proteger e integrar áreas aquáticas ao tecido urbano."
    ]
})

def lcz_get_map(city=None, roi=None, isave_map=False, isave_global=False):
    """
    Download and process the Local Climate Zone (LCZ) global mapping dataset
    directly from a URL without saving the full file locally.

    Parameters
    ----------
    city : str, optional
        The name of your target area based on the OpenStreetMap project.
    roi : geopandas.GeoDataFrame, optional
        A Region of Interest (ROI) in GeoDataFrame format to clip the LCZ map to a custom area.
    isave_map : bool, default False
        Set to True if you wish to save the resulting clipped map as a raster TIFF file.
    isave_global : bool, default False
        Set to True if you wish to save the global LCZ map as a raster TIFF file.

    Returns
    -------
    tuple
        A tuple containing (data, profile) where:
        - data: numpy array with LCZ classes (1-17)
        - profile: rasterio profile dictionary with metadata

    References
    ----------
    Demuzere, M., et al. (2022). A global map of Local Climate Zones to support earth system modelling and urban scale environmental science.
    Earth Syst. Sci. Data 14(8) 3835-3873. DOI:https://doi.org/10.5194/essd-14-3835-2022
    Zenodo. https://doi.org/10.5281/zenodo.6364594
    Stewart ID, Oke TR. (2012). Local Climate Zones for Urban Temperature Studies.
    Bull Am Meteorol Soc. 93(12):1879-1900. doi:10.1175/BAMS-D-11-00019.1
    """

    # Validate inputs
    if city is None and roi is None:
        raise ValueError("Error: provide either a city name or a roi polygon")

    # LCZ map URL
    lcz_url = "https://zenodo.org/records/8419340/files/lcz_filter_v3.tif?download=1"

    # Open the global raster directly from the URL using the /vsicurl/ virtual file system
    try:
        with rasterio.open(f'/vsicurl/{lcz_url}') as src:
            src_profile = src.profile

            # Use the most robust method: mask and crop in a single step
            if city is not None:
                try:
                    # Get geometry from city name and ensure CRS matches the raster
                    study_area = ox.geocode_to_gdf(city).to_crs(src.crs)
                    geometries = [study_area.iloc[0].geometry]
                except Exception as e:
                    raise Exception(f"No polygonal boundary found for {city}. Error: {str(e)}")
            else: # roi is provided
                # Ensure ROI's CRS matches the raster's CRS
                if roi.crs != src.crs:
                    roi = roi.to_crs(src.crs)
                geometries = roi.geometry

            # Crop and mask the raster in a single, efficient step, setting a new nodata value
            try:
                # Set a new nodata value (e.g., 255) to avoid conflict with LCZ classes
                new_nodata_value = 255
                out_image, out_transform = mask(src, geometries, crop=True, all_touched=True, nodata=new_nodata_value)
                data = out_image[0]  # Get the single band of data
                transform = out_transform
            except Exception as e:
                raise Exception(f"Failed to crop and mask raster: {str(e)}")

            # Update profile for output raster
            output_profile = src_profile.copy()
            output_profile.update({
                'height': data.shape[0],
                'width': data.shape[1],
                'transform': transform,
                'dtype': data.dtype,
                'nodata': new_nodata_value # Set the new nodata value in the profile
            })

            # Save outputs if requested
            if isave_map or isave_global:
                output_dir = "LCZ4r_output"
                os.makedirs(output_dir, exist_ok=True)

                if isave_map:
                    output_path = os.path.join(output_dir, "lcz_map.tif")
                    with rasterio.open(output_path, 'w', **output_profile) as dst:
                        dst.write(data, 1)
                    print(f"Map saved to: {os.path.abspath(output_path)}")

                if isave_global:
                    global_output_path = os.path.join(output_dir, "lcz_global_map.tif")
                    # Use requests to download the global file, as it's the simplest way for a direct copy
                    import shutil
                    with requests.get(lcz_url, stream=True) as r, open(global_output_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    print(f"Global map saved to: {os.path.abspath(global_output_path)}")

            return data, output_profile

    except Exception as e:
        raise Exception(f"Failed to open or process LCZ map from URL: {str(e)}")

def lcz_plot_map(x, isave=False, show_legend=True, save_extension="png", 
                 inclusive=False, figsize=(12, 8), **kwargs):
    """
    Visualização do mapa LCZ
    
    Parameters
    ----------
    x : tuple, str ou rasterio.DatasetReader
        Dados do mapa LCZ
    isave : bool
        Salvar figura
    show_legend : bool
        Mostrar legenda
    save_extension : str
        Formato do arquivo de saída
    inclusive : bool
        Usar paleta colorblind-friendly
    figsize : tuple
        Tamanho da figura
    **kwargs : dict
        Parâmetros adicionais (title, suptitle, caption, etc.)
    """
    
    # Processar entrada
    if isinstance(x, tuple) and len(x) == 2:
        data, profile = x
        if data.ndim > 2:
            data = data[0]
    elif isinstance(x, str):
        with rasterio.open(x) as src:
            data = src.read(1)
            profile = src.profile
    elif hasattr(x, "read"):
        data = x.read(1)
        profile = x.profile
    else:
        raise ValueError("Tipo de entrada não suportado")

    # Processar dados
    nodata = profile.get("nodata", 255)
    data = data.astype(float)
    data[data == nodata] = np.nan

    # Configurar cores
    lcz_classes = list(range(1, 18))
    lcz_names = [
        "Compact highrise", "Compact midrise", "Compact lowrise", "Open highrise",
        "Open midrise", "Open lowrise", "Lightweight low-rise", "Large lowrise",
        "Sparsely built", "Heavy Industry", "Dense trees", "Scattered trees",
        "Bush, scrub", "Low plants", "Bare rock or paved", "Bare soil or sand", "Water"
    ]

    # Paletas de cores
    standard_colors = [
        "#910613", "#D9081C", "#FF0A22", "#C54F1E", "#FF6628", "#FF985E",
        "#FDED3F", "#BBBBBB", "#FFCBAB", "#565656", "#006A18", "#00A926",
        "#628432", "#B5DA7F", "#000000", "#FCF7B1", "#656BFA"
    ]
    
    colorblind_colors = [
        "#E16A86", "#D8755E", "#C98027", "#B48C00", "#989600", "#739F00",
        "#36A631", "#00AA63", "#00AD89", "#00ACAA", "#00A7C5", "#009EDA",
        "#6290E5", "#9E7FE5", "#C36FDA", "#D965C6", "#E264A9"
    ]

    colors = colorblind_colors if inclusive else standard_colors
    cmap = ListedColormap(colors)
    cmap.set_bad(color="None")

    # Criar figura
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    
    # Plotar raster
    rasterio.plot.show(data, transform=profile["transform"], ax=ax, 
                      cmap=cmap, vmin=1, vmax=17)
    ax.set_axis_off()

    # Adicionar títulos
    if "title" in kwargs:
        ax.set_title(kwargs["title"], fontsize=18, fontweight="bold", pad=20)
    if "suptitle" in kwargs:
        fig.suptitle(kwargs["suptitle"], fontsize=16, y=0.95)
    if "caption" in kwargs:
        fig.text(0.5, 0.01, kwargs["caption"], ha="center", fontsize=10, color="grey")

    # Adicionar legenda
    if show_legend:
        patches = [
            mpatches.Patch(color=colors[i], label=f"{lcz_id}. {lcz_name}")
            for i, (lcz_id, lcz_name) in enumerate(zip(lcz_classes, lcz_names))
        ]
        
        legend = ax.legend(
            handles=patches,
            loc="center left",
            bbox_to_anchor=(1.05, 0.5),
            title="LCZ Class",
            title_fontsize=14,
            fontsize=11,
            frameon=False
        )
        legend.get_title().set_fontweight("bold")
        plt.tight_layout()
        fig.subplots_adjust(right=0.75)
    else:
        plt.tight_layout()

    # Salvar figura
    if isave:
        os.makedirs("LCZ4r_output", exist_ok=True)
        valid_extensions = ["png", "jpg", "jpeg", "tif", "pdf", "svg"]
        extension = save_extension if save_extension.lower() in valid_extensions else "png"
        
        output_path = f"LCZ4r_output/lcz_plot_map.{extension}"
        plt.savefig(output_path, dpi=600, bbox_inches="tight", facecolor="white")
        print(f"Plot salvo: {os.path.abspath(output_path)}")

    return fig

def aggregate_raster(data, transform, factor=10):
    """
    Agrega raster usando moda (valor mais frequente)
    
    Parameters
    ----------
    data : numpy.ndarray
        Dados raster
    transform : affine.Affine
        Transformação do raster
    factor : int
        Fator de agregação

    Returns
    -------
    tuple
        (dados agregados, nova transformação)
    """
    height, width = data.shape
    new_height, new_width = height // factor, width // factor
    
    aggregated = np.full((new_height, new_width), 255, dtype=data.dtype)
    
    for i in range(new_height):
        for j in range(new_width):
            block = data[i*factor:(i+1)*factor, j*factor:(j+1)*factor]
            if block.size > 0:
                values, counts = np.unique(block[block != 255], return_counts=True)
                if len(values) > 0:
                    aggregated[i, j] = values[np.argmax(counts)]
    
    new_transform = transform * transform.scale(factor)
    return aggregated, new_transform

def raster_to_polygons(data, transform, crs):
    """
    Converte raster para polígonos GeoDataFrame
    
    Parameters
    ----------
    data : numpy.ndarray
        Dados raster
    transform : affine.Affine  
        Transformação do raster
    crs : rasterio.crs.CRS
        Sistema de coordenadas

    Returns
    -------
    geopandas.GeoDataFrame
        Polígonos LCZ
    """
    mask = data != 255
    shapes = features.shapes(data.astype(np.int32), mask=mask, transform=transform)
    
    geometries, lcz_values = [], []
    for geom, value in shapes:
        geometries.append(shape(geom))
        lcz_values.append(value)
    
    return gpd.GeoDataFrame(
        {"lcz": lcz_values}, 
        geometry=geometries, 
        crs=crs
    )

def process_lcz_map(raster_data, raster_profile, factor=10):
    """
    Processamento completo do mapa LCZ para formato vetorial
    
    Parameters
    ----------
    raster_data : numpy.ndarray
        Dados raster LCZ
    raster_profile : dict
        Perfil do raster
    factor : int
        Fator de agregação

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame com polígonos LCZ processados
    """
    # Agregar raster
    aggregated, new_transform = aggregate_raster(
        raster_data, raster_profile["transform"], factor
    )
    
    # Converter para polígonos
    polygons = raster_to_polygons(
        aggregated, new_transform, raster_profile["crs"]
    )
    
    # Dissolver por classe LCZ
    dissolved = polygons.dissolve(by="lcz").reset_index()
    
    # Adicionar informações LCZ
    result = dissolved.merge(LCZ_INFO, on="lcz", how="left")
    
    # Limpar colunas duplicadas
    result.columns = [col.replace("_x", "").replace("_y", "") for col in result.columns]
    
    return result

def enhance_lcz_data(gdf):
    """
    Função para melhorias adicionais nos dados LCZ
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Dados LCZ para aprimoramento

    Returns
    -------
    geopandas.GeoDataFrame
        Dados aprimorados
    """
    # Exemplo de aprimoramento: calcular área de cada polígono
    gdf = gdf.copy()
    gdf["area_km2"] = gdf.geometry.area / 1e6
    
    print("Dados LCZ aprimorados com sucesso")
    
    return gdf


def lcz_cal_area(gdf, return_stats=True, return_plot_data=True):
    """
    Calcula estatísticas de área para classes LCZ e prepara dados para visualização.
    
    Esta função é agnóstica em relação à biblioteca de plotagem e apenas processa 
    os dados brutos da GeoDataFrame para um formato tabular e de dicionário.
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame com dados LCZ contendo colunas 'zcl_classe' e geometria.
    return_stats : bool, default True
        Se True, retorna estatísticas detalhadas de área em formato DataFrame.
    return_plot_data : bool, default True
        Se True, retorna dados formatados em dicionário para plotagem (ex: cores LCZ e listas de valores).
    
    Returns
    -------
    dict
        Dicionário contendo:
        - 'stats': DataFrame com estatísticas de área por classe LCZ.
        - 'plot_data': Dados formatados (listas, cores) para visualização.
        - 'summary': Resumo geral das áreas.
    """
    
    if gdf is None or len(gdf) == 0:
        raise ValueError("GeoDataFrame vazio ou None fornecido.")
    
    # 1. Verificação de Colunas
    required_cols = ['zcl_classe']
    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
    
    # 2. Cálculo da Área (se necessário)
    gdf_work = gdf.copy()
    if 'area_km2' not in gdf_work.columns:
        # Reprojetar para um CRS apropriado para cálculo de área (Mollweide ou similar)
        # O uso do CRS projetado garante precisão.
        if gdf_work.crs and gdf_work.crs.is_geographic:
            # Usar projeção equivalente de área global (ESRI:54009 - World Mollweide)
            gdf_work = gdf_work.to_crs('ESRI:54009') 
        
        # Área em metros quadrados / 1 milhão = km²
        gdf_work['area_km2'] = gdf_work.geometry.area / 1e6
    
    # 3. Estatísticas por Classe LCZ
    area_stats = gdf_work.groupby('zcl_classe').agg({
        'area_km2': ['sum', 'count', 'mean', 'std', 'min', 'max']
    }).round(3)
    
    # Achatar colunas multi-nível
    area_stats.columns = ['area_total_km2', 'num_poligonos', 'area_media_km2', 
                         'area_std_km2', 'area_min_km2', 'area_max_km2']
    area_stats = area_stats.reset_index()
    
    # 4. Cálculo de Percentuais
    total_area = area_stats['area_total_km2'].sum()
    area_stats['percentual'] = (area_stats['area_total_km2'] / total_area * 100).round(2)
    
    # Ordenar por área total (decrescente)
    area_stats = area_stats.sort_values('area_total_km2', ascending=False)
    
    # 5. Preparar Dados para Plotagem (Plotly friendly)
    plot_data = {
        'classes': area_stats['zcl_classe'].tolist(),
        'areas': area_stats['area_total_km2'].tolist(),
        'percentuais': area_stats['percentual'].tolist(),
        'num_poligonos': area_stats['num_poligonos'].tolist(),
        # Manter o dicionário de cores fixo, essencial para a identidade visual
        'cores_lcz': {
            'LCZ 1': '#910613', 'LCZ 2': '#D9081C', 'LCZ 3': '#FF0A22', 
            'LCZ 4': '#C54F1E', 'LCZ 5': '#FF6628', 'LCZ 6': '#FF985E',
            'LCZ 7': '#FDED3F', 'LCZ 8': '#BBBBBB', 'LCZ 9': '#FFCBAB',
            'LCZ 10': '#565656', 'LCZ A': '#006A18', 'LCZ B': '#00A926',
            'LCZ C': '#628432', 'LCZ D': '#B5DA7F', 'LCZ E': '#000000',
            'LCZ F': '#FCF7B1', 'LCZ G': '#656BFA'
        }
    }
    
    # 6. Resumo Geral
    summary = {
        'total_area_km2': total_area,
        'num_classes': len(area_stats),
        'num_total_poligonos': area_stats['num_poligonos'].sum(),
        'classe_dominante': area_stats.iloc[0]['zcl_classe'],
        'area_classe_dominante_km2': area_stats.iloc[0]['area_total_km2'],
        'percentual_classe_dominante': area_stats.iloc[0]['percentual']
    }
    
    # 7. Preparar Resultado
    result = {}
    if return_stats:
        result['stats'] = area_stats
    if return_plot_data:
        result['plot_data'] = plot_data
    result['summary'] = summary
    
    return result

def lcz_area_analysis_report(gdf, city_name=None):
    """
    Gera um relatório completo de análise de área LCZ.
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame com dados LCZ
    city_name : str, optional
        Nome da cidade para incluir no relatório
    
    Returns
    -------
    str
        Relatório formatado em texto
    """
    
    try:
        # Calcular estatísticas
        result = lcz_cal_area(gdf)
        stats = result['stats']
        summary = result['summary']
        
        # Cabeçalho do relatório
        city_text = f" - {city_name}" if city_name else ""
        report = f"""
=== RELATÓRIO DE ANÁLISE LCZ{city_text} ===

RESUMO GERAL:
• Área total analisada: {summary['total_area_km2']:.2f} km²
• Número de classes LCZ: {summary['num_classes']}
• Total de polígonos: {summary['num_total_poligonos']}
• Classe dominante: {summary['classe_dominante']} ({summary['percentual_classe_dominante']:.1f}%)

DISTRIBUIÇÃO POR CLASSE LCZ:
"""
        
        # Adicionar detalhes por classe
        for _, row in stats.iterrows():
            report += f"""
{row['zcl_classe']}:
  • Área total: {row['area_total_km2']:.2f} km² ({row['percentual']:.1f}%)
  • Polígonos: {row['num_poligonos']}
  • Área média por polígono: {row['area_media_km2']:.3f} km²
"""
        
        # Análise adicional
        report += f"""
ANÁLISE ADICIONAL:
• Classes urbanas (LCZ 1-10): {stats[stats['zcl_classe'].str.contains('LCZ [1-9]|LCZ 10')]['area_total_km2'].sum():.2f} km²
• Classes naturais (LCZ A-G): {stats[stats['zcl_classe'].str.contains('LCZ [A-G]')]['area_total_km2'].sum():.2f} km²
• Fragmentação média: {stats['num_poligonos'].sum() / summary['total_area_km2']:.2f} polígonos/km²

=== FIM DO RELATÓRIO ===
"""
        
        return report
        
    except Exception as e:
        return f"Erro ao gerar relatório: {str(e)}"


def validate_lcz_data(gdf):
    """
    Valida a integridade dos dados LCZ.
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame com dados LCZ para validação
    
    Returns
    -------
    dict
        Resultado da validação com status e mensagens
    """
    
    validation_result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'info': []
    }
    
    try:
        # Verificar se o GeoDataFrame não está vazio
        if gdf is None or len(gdf) == 0:
            validation_result['valid'] = False
            validation_result['errors'].append("GeoDataFrame vazio ou None")
            return validation_result
        
        # Verificar colunas obrigatórias
        required_columns = ['zcl_classe', 'geometry']
        missing_columns = [col for col in required_columns if col not in gdf.columns]
        if missing_columns:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Colunas obrigatórias ausentes: {missing_columns}")
        
        # Verificar geometrias válidas
        invalid_geoms = gdf[~gdf.geometry.is_valid]
        if len(invalid_geoms) > 0:
            validation_result['warnings'].append(f"{len(invalid_geoms)} geometrias inválidas encontradas")
        
        # Verificar classes LCZ válidas
        valid_classes = [f"LCZ {i}" for i in range(1, 11)] + [f"LCZ {c}" for c in 'ABCDEFG']
        invalid_classes = gdf[~gdf['zcl_classe'].isin(valid_classes)]['zcl_classe'].unique()
        if len(invalid_classes) > 0:
            validation_result['warnings'].append(f"Classes LCZ não reconhecidas: {list(invalid_classes)}")
        
        # Verificar CRS
        if gdf.crs is None:
            validation_result['warnings'].append("Sistema de coordenadas (CRS) não definido")
        
        # Informações gerais
        validation_result['info'].append(f"Total de registros: {len(gdf)}")
        validation_result['info'].append(f"Classes LCZ presentes: {len(gdf['zcl_classe'].unique())}")
        
        if 'area_km2' in gdf.columns:
            total_area = gdf['area_km2'].sum()
            validation_result['info'].append(f"Área total: {total_area:.2f} km²")
        
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f"Erro durante validação: {str(e)}")
    
    return validation_result
