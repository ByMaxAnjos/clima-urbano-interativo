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
import geopandas as gpd
import rasterio
from rasterio import features
from shapely.geometry import shape
import requests
import shutil
from urllib3.exceptions import NewConnectionError

# Configurações
warnings.filterwarnings("ignore")

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
        "Lightweight low-rise – construções leves e baixas, de material leve (madeira, chapas)",
        "Large low-rise – galpões, shoppings, indústrias",
        "Sparsely built – edificações esparsas",
        "Heavy industry – áreas industriais pesadas",
        "Dense trees – florestas urbanas densas",
        "Scattered trees – árvores dispersas",
        "Bush, scrub – vegetação arbustiva",
        "Low plants – gramados, campos",
        "Bare rock or paved – rocha exposta ou pavimento",
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
        "Aquece rapidamente sob sol direto, elevando a temperatura de superfície (LST); efeito menor sobre a temperatura do ar à noite.",
        "Aquecimento diurno intenso da superfície exposta, mas baixa capacidade de retenção noturna.",
        "Efeito de resfriamento pela evaporação; pode reduzir a temperatura do ar em seu entorno imediato."
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
        "Contribuição indireta e localizada à ICU, mais visível em imagens de satélite (LST) do que na temperatura do ar sentida pelas pessoas.",
        "Contribuição localizada, dependente da umidade do solo no momento da medição.",
        "Geralmente mitiga a ilha de calor local por evaporação, exceto quando a água está muito rasa/aquecida."
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
        "Preservar a vegetação arbustiva existente e evitar sua remoção para pavimentação.",
        "Expandir áreas permeáveis e gramados.",
        "Substituir por pavimentos frios, introduzir arborização.",
        "Revegetar áreas expostas ou estabilizar solos.",
        "Proteger e integrar áreas aquáticas ao tecido urbano."
    ]
})

def lcz_get_map(city=None, roi=None, isave_map=False, isave_global=False, return_path=False):
    """
    Download e processamento do mapa global de Zonas Climáticas Locais (LCZ).

    Wrapper fino sobre LCZ4py.general.lcz_get_map: delega geocodificação, streaming
    do COG global e recorte da área de interesse para o pacote (que já traz cache em
    disco de dois níveis, streaming via /vsicurl/ e retries), e adapta o retorno
    (caminho de arquivo) para o contrato (dados numpy, perfil rasterio) que o resto
    da plataforma (modules/explorar.py) já espera.

    Parameters
    ----------
    city : str, optional
        Nome da cidade para busca no serviço de geocodificação
    roi : geopandas.GeoDataFrame, optional
        Região de interesse em formato GeoDataFrame
    isave_map : bool, default False
        Salvar mapa recortado como arquivo TIFF (LCZ4r_output/lcz_map.tif)
    isave_global : bool, default False
        Salvar mapa global completo como arquivo TIFF (sem suporte nativo no
        LCZ4py; mantido via download direto para compatibilidade, mas não é
        usado por nenhum chamador atual da plataforma)
    return_path : bool, default False
        Se True, retorna também o caminho do GeoTIFF recortado que o LCZ4py já
        mantém em cache (`~/.lcz4r_cache/clipped_<hash>.tif`, chaveado pelo
        conteúdo da área — seguro para uso concorrente, ao contrário do arquivo
        fixo `LCZ4r_output/lcz_map.tif` de `isave_map`, que é sobrescrito a
        cada chamada). Use este caminho para alimentar `lcz_cal_area` em vez
        do caminho fixo, evitando colisão entre usuários/cidades simultâneos.

    Returns
    -------
    tuple
        (dados numpy, perfil rasterio) ou, se `return_path=True`,
        (dados numpy, perfil rasterio, caminho do GeoTIFF em cache)

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

    from LCZ4py.general import lcz_get_map as _lcz4py_get_map

    try:
        clipped_path = _lcz4py_get_map(city=city, roi=roi, isave_map=False, cache=True, verbose=False)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            NewConnectionError,
            OSError) as e:
        raise ConnectionError(
            "Falha na conexão com o serviço de dados LCZ. "
            "Possíveis causas:\n"
            "• Conexão com a internet instável\n"
            "• Serviço temporariamente indisponível\n"
            "• Firewall bloqueando o acesso\n"
            f"Detalhe: {e}"
        )
    except ValueError as e:
        msg = str(e)
        if city is not None and ("city" in msg.lower() or "geocod" in msg.lower()):
            raise GeocodeError(
                f"Não foi possível encontrar a cidade '{city}'. "
                f"Verifique se o nome está correto e tente variações como "
                f"'{city}, Brazil' ou '{city} city'. Detalhe: {msg}"
            )
        raise DataProcessingError(f"Erro no processamento dos dados LCZ: {msg}")
    except Exception as e:
        raise DataProcessingError(f"Erro no processamento dos dados LCZ: {e}")

    with rasterio.open(clipped_path) as src:
        data = src.read(1)
        profile = src.profile.copy()

    valid_data = data[data != profile.get("nodata", 255)]
    if len(valid_data) == 0:
        raise DataProcessingError(
            f"Nenhum dado LCZ válido encontrado para '{city}'. "
            "A área pode estar fora da cobertura do mapa LCZ global ou "
            "o nome da cidade pode estar incorreto."
        )

    if isave_map:
        os.makedirs("LCZ4r_output", exist_ok=True)
        output_path = "LCZ4r_output/lcz_map.tif"
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data, 1)

    if isave_global:
        lcz_url = "https://zenodo.org/records/8419340/files/lcz_filter_v3.tif?download=1"
        os.makedirs("LCZ4r_output", exist_ok=True)
        global_path = "LCZ4r_output/lcz_global_map.tif"
        with requests.get(lcz_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(global_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)

    if return_path:
        return data, profile, clipped_path
    return data, profile


# Exceções personalizadas para melhor tratamento de erros
class GeocodeError(Exception):
    """Exceção para erros de geocodificação."""
    pass

class DataProcessingError(Exception):
    """Exceção para erros no processamento de dados."""
    pass

def lcz_plot_map(x, isave=False, show_legend=True, inclusive=False,
                 title=None, subtitle=None, caption=None, renderer="plotly"):
    """
    Visualização interativa do mapa LCZ.

    Wrapper fino sobre LCZ4py.general.lcz_plot_map: em vez de desenhar um PNG
    estático via matplotlib, delega para o motor Plotly/MapLibre do LCZ4py
    (zoom/pan reais, WebGL para rasters grandes). LCZ4py exige um caminho de
    arquivo ou dataset rasterio — se `x` vier como tupla (dados, perfil), como
    no contrato antigo desta função, ela é gravada num arquivo temporário.

    Parameters
    ----------
    x : tuple (dados, perfil), str ou rasterio.DatasetReader
        Dados do mapa LCZ
    isave : bool
        Salvar figura em LCZ4r_output/lcz_plot_map.html
    show_legend : bool
        Mostrar legenda das classes LCZ
    inclusive : bool
        Usar paleta colorblind-friendly
    title, subtitle, caption : str, optional
        Anotações da figura
    renderer : {"plotly", "maplibre"}
        "plotly" retorna uma figura Plotly (zoom/pan, WebGL); "maplibre"
        retorna uma página HTML com o raster sobreposto a um basemap OSM

    Returns
    -------
    LCZPlotResult
        `.fig` é uma `plotly.graph_objects.Figure` (renderer="plotly") pronta
        para `st.plotly_chart`; `.html` é a página MapLibre (renderer="maplibre")
    """
    from LCZ4py.general import lcz_plot_map as _lcz4py_plot_map

    caminho_temporario = None
    if isinstance(x, tuple) and len(x) == 2:
        data, profile = x
        if data.ndim > 2:
            data = data[0]
        tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
        tmp.close()
        with rasterio.open(tmp.name, "w", **profile) as dst:
            dst.write(data, 1)
        caminho_temporario = tmp.name
        fonte = caminho_temporario
    elif isinstance(x, str) or hasattr(x, "read"):
        fonte = x
    else:
        raise ValueError("Tipo de entrada não suportado")

    try:
        return _lcz4py_plot_map(
            fonte,
            isave=isave,
            save_extension="html",
            show_legend=show_legend,
            inclusive=inclusive,
            title=title,
            subtitle=subtitle,
            caption=caption,
            renderer=renderer,
        )
    finally:
        if caminho_temporario:
            os.remove(caminho_temporario)

def aggregate_raster(data, transform, factor=5):
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

def process_lcz_map(raster_data, raster_profile, factor=5):
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


def _area_stats_from_raster(raster_path):
    """Calcula área total/percentual por classe LCZ contando pixels no raster
    via LCZ4py.general.lcz_cal_area, retornando no formato ('zcl_classe',
    'area_total_km2', 'percentual') usado pelo resto da plataforma."""
    from LCZ4py.general import lcz_cal_area as _lcz4py_cal_area

    df_pl = _lcz4py_cal_area(raster_path, iplot=False)
    df = df_pl.to_pandas()

    codigo_para_classe = dict(zip(LCZ_INFO['lcz'], LCZ_INFO['zcl_classe']))
    df['zcl_classe'] = df['lcz'].map(codigo_para_classe)
    df = df.rename(columns={'area_km2': 'area_total_km2', 'area_perc': 'percentual'})

    return df[['zcl_classe', 'area_total_km2', 'percentual']]


def lcz_cal_area(gdf, return_stats=True, return_plot_data=True, raster_path=None):
    """
    Calcula estatísticas de área para classes LCZ e prepara dados para visualização.

    Quando `raster_path` é fornecido, a área total e o percentual por classe vêm
    de LCZ4py.general.lcz_cal_area, que conta pixels diretamente no raster —
    mais rápido e sem os pequenos artefatos de vetorização/dissolve do caminho
    baseado em polígonos. `num_poligonos` e as estatísticas por polígono
    (média/desvio/mín/máx) continuam vindo do `gdf` vetorizado, pois são usadas
    como proxy de densidade de vetorização (ver métrica "Densidade de
    Polígonos" em explorar.py) — LCZ4py não expõe contagem de polígonos.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame com dados LCZ contendo colunas 'zcl_classe' e geometria
    return_stats : bool, default True
        Se True, retorna estatísticas detalhadas de área
    return_plot_data : bool, default True
        Se True, retorna dados formatados para plotagem
    raster_path : str, optional
        Caminho do GeoTIFF recortado; se fornecido, área/percentual vêm da
        contagem de pixels via LCZ4py em vez do polígono vetorizado

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

    # Estatísticas por polígono (contagem/média/desvio/mín/máx) sempre vêm do
    # gdf vetorizado — usadas como proxy de densidade de vetorização, não de
    # área total (ver docstring acima).
    poligono_stats = gdf_work.groupby('zcl_classe').agg({
        'area_km2': ['count', 'mean', 'std', 'min', 'max']
    }).round(3)
    poligono_stats.columns = ['num_poligonos', 'area_media_km2',
                               'area_std_km2', 'area_min_km2', 'area_max_km2']
    poligono_stats = poligono_stats.reset_index()

    if raster_path and os.path.exists(raster_path):
        area_stats = _area_stats_from_raster(raster_path)
        area_stats = area_stats.merge(poligono_stats, on='zcl_classe', how='left')
        area_stats['num_poligonos'] = area_stats['num_poligonos'].fillna(0).astype(int)
    else:
        area_total = gdf_work.groupby('zcl_classe')['area_km2'].sum().round(3)
        area_stats = poligono_stats.merge(
            area_total.rename('area_total_km2').reset_index(), on='zcl_classe'
        )
        area_stats['percentual'] = (
            area_stats['area_total_km2'] / area_stats['area_total_km2'].sum() * 100
        ).round(2)

    total_area = area_stats['area_total_km2'].sum()

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

