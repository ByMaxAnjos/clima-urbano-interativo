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
    Download e processamento do mapa global de Zonas Climáticas Locais (LCZ)
    com tratamento robusto de erros de conexão e geocodificação aprimorada.

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
        
    Raises
    ------
    ValueError
        Se nem city nem roi forem fornecidos
    ConnectionError
        Se houver falha na conexão com serviços externos
    GeocodeError
        Se a cidade não for encontrada no serviço de geocodificação
    DataProcessingError
        Se houver erro no processamento dos dados LCZ
    """
    if city is None and roi is None:
        raise ValueError("Forneça um nome de cidade ou um polígono ROI")

    lcz_url = "https://zenodo.org/records/8419340/files/lcz_filter_v3.tif?download=1"
    max_retries = 5  # Aumentado para melhor robustez
    geocode_retries = 3  # Tentativas específicas para geocodificação
    
    # Variáveis para controle de erro
    geocode_success = False
    study_area_gdf = None
    last_geocode_error = None
    
    # Etapa 1: Geocodificação (se necessário)
    if city is not None:
        for geocode_attempt in range(geocode_retries):
            try:
                print(f"Geocodificação - Tentativa {geocode_attempt + 1}: Buscando '{city}'...")
                
                # Configurar timeout e user agent para OSMnx
                ox.settings.timeout = 30
                ox.settings.requests_timeout = 30
                
                # Tentar geocodificação com diferentes estratégias
                if geocode_attempt == 0:
                    # Primeira tentativa: busca direta
                    study_area_gdf = ox.geocode_to_gdf(city)
                elif geocode_attempt == 1:
                    # Segunda tentativa: adicionar país se não especificado
                    if ',' not in city:
                        study_area_gdf = ox.geocode_to_gdf(f"{city}, Brazil")
                    else:
                        study_area_gdf = ox.geocode_to_gdf(city)
                else:
                    # Terceira tentativa: busca mais específica
                    study_area_gdf = ox.geocode_to_gdf(f"{city} city")
                
                geocode_success = True
                print(f"Geocodificação bem-sucedida para '{city}'")
                break
                
            except Exception as e:
                last_geocode_error = e
                print(f"Erro na geocodificação (tentativa {geocode_attempt + 1}): {str(e)}")
                
                if geocode_attempt < geocode_retries - 1:
                    wait_time = 2 ** geocode_attempt + 1
                    print(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                    time.sleep(wait_time)
        
        if not geocode_success:
            raise GeocodeError(
                f"Não foi possível encontrar a cidade '{city}'. "
                f"Verifique se o nome está correto e tente variações como "
                f"'{city}, Brazil' ou '{city} city'. "
                f"Último erro: {str(last_geocode_error)}"
            )
    else:
        study_area_gdf = roi
        geocode_success = True
    
    # Etapa 2: Download e processamento do mapa LCZ
    for attempt in range(max_retries):
        try:
            print(f"Download LCZ - Tentativa {attempt + 1}: Acessando mapa global...")
            
            # Configurar timeout para rasterio
            import rasterio.env
            with rasterio.env.Env(GDAL_HTTP_TIMEOUT=60, GDAL_HTTP_CONNECTTIMEOUT=30):
                with rasterio.open(f"/vsicurl/{lcz_url}") as src:
                    print("Mapa LCZ global acessado com sucesso.")
                    
                    # Garantir que o CRS seja o mesmo
                    if study_area_gdf.crs != src.crs:
                        print("Reprojetando geometria para o CRS do raster...")
                        study_area_gdf = study_area_gdf.to_crs(src.crs)
                    
                    geometries = study_area_gdf.geometry
                    
                    # Verificar se a geometria está dentro dos limites do raster
                    raster_bounds = src.bounds
                    geom_bounds = study_area_gdf.total_bounds
                    
                    if not (raster_bounds.left <= geom_bounds[2] and 
                           raster_bounds.bottom <= geom_bounds[3] and
                           raster_bounds.right >= geom_bounds[0] and 
                           raster_bounds.top >= geom_bounds[1]):
                        print("Aviso: A geometria pode estar parcialmente fora dos limites do raster LCZ")

                    # Recortar raster
                    print("Recortando raster para a área de interesse...")
                    new_nodata = 255
                    out_image, out_transform = mask(
                        src, geometries, crop=True, all_touched=True, nodata=new_nodata
                    )
                    data = out_image[0]
                    
                    # Verificar se há dados válidos
                    valid_data = data[data != new_nodata]
                    if len(valid_data) == 0:
                        raise DataProcessingError(
                            f"Nenhum dado LCZ válido encontrado para '{city}'. "
                            "A área pode estar fora da cobertura do mapa LCZ global ou "
                            "o nome da cidade pode estar incorreto."
                        )
                    
                    print(f"Recorte concluído. Dados válidos: {len(valid_data)} pixels")

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
                            with requests.get(lcz_url, stream=True, timeout=120) as r:
                                r.raise_for_status()
                                with open(global_path, "wb") as f:
                                    shutil.copyfileobj(r.raw, f)
                            print(f"Mapa global salvo: {os.path.abspath(global_path)}")

                    return data, profile

        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                NewConnectionError,
                rasterio.errors.RasterioIOError) as e:
            print(f"Erro de conexão/rede na tentativa {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                backoff_time = min(2 ** (attempt + 1), 30)  # Máximo de 30 segundos
                print(f"Aguardando {backoff_time} segundos antes de tentar novamente...")
                time.sleep(backoff_time)
            else:
                raise ConnectionError(
                    "Falha na conexão com o serviço de dados LCZ após múltiplas tentativas. "
                    "Possíveis causas:\n"
                    "• Conexão com a internet instável\n"
                    "• Serviço temporariamente indisponível\n"
                    "• Firewall bloqueando o acesso\n"
                    "Tente novamente em alguns minutos."
                )
        except Exception as e:
            error_msg = str(e)
            if "No such file or directory" in error_msg or "404" in error_msg:
                raise DataProcessingError(
                    "O arquivo de dados LCZ não está disponível no servidor. "
                    "Tente novamente mais tarde."
                )
            elif "timeout" in error_msg.lower():
                if attempt < max_retries - 1:
                    print(f"Timeout na tentativa {attempt + 1}. Tentando novamente...")
                    time.sleep(5)
                    continue
                else:
                    raise ConnectionError(
                        "Timeout na conexão com o serviço de dados LCZ. "
                        "Verifique sua conexão com a internet."
                    )
            else:
                raise DataProcessingError(f"Erro no processamento dos dados LCZ: {error_msg}")

    # Se o loop terminar sem sucesso
    raise ConnectionError("Não foi possível processar o mapa LCZ devido a problemas de conexão.")


# Exceções personalizadas para melhor tratamento de erros
class GeocodeError(Exception):
    """Exceção para erros de geocodificação."""
    pass

class DataProcessingError(Exception):
    """Exceção para erros no processamento de dados."""
    pass

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

def aggregate_raster(data, transform, factor=2):
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

def process_lcz_map(raster_data, raster_profile, factor=2):
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
    
    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame com dados LCZ contendo colunas 'zcl_classe' e geometria
    return_stats : bool, default True
        Se True, retorna estatísticas detalhadas de área
    return_plot_data : bool, default True
        Se True, retorna dados formatados para plotagem
    
    Returns
    -------
    dict
        Dicionário contendo:
        - 'stats': DataFrame com estatísticas de área por classe LCZ
        - 'plot_data': Dados formatados para visualização
        - 'summary': Resumo geral das áreas
        
    Examples
    --------
    >>> result = lcz_cal_area(lcz_gdf)
    >>> print(result['summary'])
    >>> area_stats = result['stats']
    >>> plot_data = result['plot_data']
    """
    
    if gdf is None or len(gdf) == 0:
        raise ValueError("GeoDataFrame vazio ou None fornecido")
    
    # Verificar se as colunas necessárias existem
    required_cols = ['zcl_classe']
    missing_cols = [col for col in required_cols if col not in gdf.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
    
    # Calcular área se não existir
    gdf_work = gdf.copy()
    if 'area_km2' not in gdf_work.columns:
        # Reprojetar para um CRS apropriado para cálculo de área se necessário
        if gdf_work.crs and gdf_work.crs.is_geographic:
            # Usar projeção equivalente de área (Mollweide)
            gdf_work = gdf_work.to_crs('ESRI:54009')
        
        gdf_work['area_km2'] = gdf_work.geometry.area / 1e6
    
    # Calcular estatísticas por classe LCZ
    area_stats = gdf_work.groupby('zcl_classe').agg({
        'area_km2': ['sum', 'count', 'mean', 'std', 'min', 'max']
    }).round(3)
    
    # Achatar colunas multi-nível
    area_stats.columns = ['area_total_km2', 'num_poligonos', 'area_media_km2', 
                         'area_std_km2', 'area_min_km2', 'area_max_km2']
    area_stats = area_stats.reset_index()
    
    # Calcular percentuais
    total_area = area_stats['area_total_km2'].sum()
    area_stats['percentual'] = (area_stats['area_total_km2'] / total_area * 100).round(2)
    
    # Ordenar por área total (decrescente)
    area_stats = area_stats.sort_values('area_total_km2', ascending=False)
    
    # Preparar dados para plotagem
    plot_data = {
        'classes': area_stats['zcl_classe'].tolist(),
        'areas': area_stats['area_total_km2'].tolist(),
        'percentuais': area_stats['percentual'].tolist(),
        'num_poligonos': area_stats['num_poligonos'].tolist(),
        'cores_lcz': {
            'LCZ 1': '#910613', 'LCZ 2': '#D9081C', 'LCZ 3': '#FF0A22', 
            'LCZ 4': '#C54F1E', 'LCZ 5': '#FF6628', 'LCZ 6': '#FF985E',
            'LCZ 7': '#FDED3F', 'LCZ 8': '#BBBBBB', 'LCZ 9': '#FFCBAB',
            'LCZ 10': '#565656', 'LCZ A': '#006A18', 'LCZ B': '#00A926',
            'LCZ C': '#628432', 'LCZ D': '#B5DA7F', 'LCZ E': '#000000',
            'LCZ F': '#FCF7B1', 'LCZ G': '#656BFA'
        }
    }
    
    # Resumo geral
    summary = {
        'total_area_km2': total_area,
        'num_classes': len(area_stats),
        'num_total_poligonos': area_stats['num_poligonos'].sum(),
        'classe_dominante': area_stats.iloc[0]['zcl_classe'],
        'area_classe_dominante_km2': area_stats.iloc[0]['area_total_km2'],
        'percentual_classe_dominante': area_stats.iloc[0]['percentual']
    }
    
    # Preparar resultado
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

