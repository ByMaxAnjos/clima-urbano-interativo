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
    Download e processamento do mapa global de Zonas Climáticas Locais (LCZ)
    
    Parameters
    ----------
    city : str, optional
        Nome da cidade para busca no OpenStreetMap
    roi : geopandas.GeoDataFrame, optional
        Região de interesse em formato GeoDataFrame
    isave_map : bool, default False
        Salvar mapa recortado como arquivo TIFF
    isave_global : bool, default False  
        Salvar mapa global completo como arquivo TIFF

    Returns
    -------
    tuple
        (dados numpy, perfil rasterio)
    """
    
    if city is None and roi is None:
        raise ValueError("Forneça um nome de cidade ou um polígono ROI")

    lcz_url = "https://zenodo.org/records/8419340/files/lcz_filter_v3.tif?download=1"
    
    try:
        with rasterio.open(f"/vsicurl/{lcz_url}") as src:
            # Obter geometria de recorte
            if city is not None:
                study_area = ox.geocode_to_gdf(city).to_crs(src.crs)
                geometries = [study_area.iloc[0].geometry]
            else:
                if roi.crs != src.crs:
                    roi = roi.to_crs(src.crs)
                geometries = roi.geometry

            # Recortar raster
            new_nodata = 255
            out_image, out_transform = mask(
                src, geometries, crop=True, all_touched=True, nodata=new_nodata
            )
            data = out_image[0]

            # Atualizar perfil
            profile = src.profile.copy()
            profile.update({
                "height": data.shape[0],
                "width": data.shape[1],
                "transform": out_transform,
                "nodata": new_nodata
            })

            # Salvar arquivos se solicitado
            if isave_map or isave_global:
                os.makedirs("LCZ4r_output", exist_ok=True)
                
                if isave_map:
                    output_path = "LCZ4r_output/lcz_map.tif"
                    with rasterio.open(output_path, "w", **profile) as dst:
                        dst.write(data, 1)
                    print(f"Mapa salvo: {os.path.abspath(output_path)}")
                
                if isave_global:
                    global_path = "LCZ4r_output/lcz_global_map.tif"
                    with requests.get(lcz_url, stream=True) as r, open(global_path, "wb") as f:
                        shutil.copyfileobj(r.raw, f)
                    print(f"Mapa global salvo: {os.path.abspath(global_path)}")

            return data, profile

    except Exception as e:
        raise Exception(f"Erro no processamento do mapa LCZ: {str(e)}")

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

# Exemplo de uso
if __name__ == "__main__":
    # Download e visualização do mapa
    data, profile = lcz_get_map(city="São Paulo", isave_map=True)
    
    # Plotar mapa
    fig = lcz_plot_map(
        (data, profile), 
        title="Mapa LCZ de São Paulo",
        isave=True,
        save_extension="png"
    )
    plt.show()
    
    # Processar para formato vetorial
    lcz_gdf = process_lcz_map(data, profile)
    
    # Aprimorar dados
    enhanced_gdf = enhance_lcz_data(lcz_gdf)
    
    # Salvar resultado
    enhanced_gdf.to_file("LCZ4r_output/map_lcz.geojson", driver="GeoJSON")
    print("Processamento concluído!")

