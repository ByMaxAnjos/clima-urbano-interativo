# -*- coding: utf-8 -*-
"""
LCZ Platform Tool - Processamento e Visualização de Zonas Climáticas Locais

Script otimizado para download, processamento e visualização de dados LCZ

https://colab.research.google.com/drive/1ZdReMbnI_7VSSS0ALpnb-O1Mie2BnPKw
"""

import os
import warnings
import tempfile
from pathlib import Path
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

# Diretório de cache em disco compartilhado por todos os downloads pesados da
# LCZ4py (mapa LCZ, parâmetros urbanos, Sentinel-2) — mesmo padrão que a
# própria LCZ4py já usa para a maioria das suas funções, exceto lcz_get_ucp
# (que por padrão usa outro diretório); apontamos explicitamente para este
# aqui em cada wrapper para manter um único local, governado por
# `_podar_cache_lcz4py`.
CACHE_DIR_LCZ4PY = os.path.expanduser("~/.lcz4r_cache")

# Teto de tamanho do cache, em MB. No Streamlit Community Cloud o app roda num
# contêiner compartilhado por TODOS os usuários simultâneos, com disco efêmero
# e limitado — sem este teto, o cache (que a LCZ4py grava em disco sem nenhum
# limite de tamanho) cresceria sem parar a cada nova cidade/parâmetro/índice
# explorado, até encher o disco e derrubar o app para todo mundo, não só para
# quem gerou o cache. 500 MB é conservador: sobra espaço para o resto do app
# (Python, GDAL/rasterio, etc.) no plano gratuito.
CACHE_LIMITE_MB = 500


def _podar_cache_lcz4py(cache_dir=CACHE_DIR_LCZ4PY, limite_mb=CACHE_LIMITE_MB):
    """
    Mantém o cache de downloads da LCZ4py sob um teto de tamanho, removendo
    primeiro os arquivos acessados há mais tempo (aproximação de LRU) até
    caber no limite.

    Roda em best-effort — qualquer erro aqui é silenciado, porque poda de
    cache nunca deve interromper o fluxo principal (mostrar o mapa/parâmetro/
    índice ao usuário).
    """
    try:
        base = Path(os.path.expanduser(cache_dir))
        if not base.exists():
            return

        arquivos = [p for p in base.rglob("*") if p.is_file()]
        limite_bytes = limite_mb * 1024 * 1024
        total = sum(p.stat().st_size for p in arquivos)
        if total <= limite_bytes:
            return

        arquivos.sort(key=lambda p: p.stat().st_atime)
        for p in arquivos:
            if total <= limite_bytes:
                break
            try:
                tamanho = p.stat().st_size
                p.unlink()
                total -= tamanho
            except OSError:
                continue
    except Exception:
        pass

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

# Paleta oficial das classes LCZ (Stewart & Oke, 2012 / WUDAPT — mesmos hex do
# LCZ4py). Fonte única: reaproveitada por Explorar, Visualizar e lcz_cal_area
# abaixo, em vez de manter cópias divergentes em cada módulo.
CORES_LCZ = {
    'LCZ 1': '#910613', 'LCZ 2': '#D9081C', 'LCZ 3': '#FF0A22', 'LCZ 4': '#C54F1E',
    'LCZ 5': '#FF6628', 'LCZ 6': '#FF985E', 'LCZ 7': '#FDED3F', 'LCZ 8': '#BBBBBB',
    'LCZ 9': '#FFCBAB', 'LCZ 10': '#565656', 'LCZ A': '#006A18', 'LCZ B': '#00A926',
    'LCZ C': '#628432', 'LCZ D': '#B5DA7F', 'LCZ E': '#000000', 'LCZ F': '#FCF7B1',
    'LCZ G': '#656BFA'
}


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

    _podar_cache_lcz4py()

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
                 title=None, subtitle=None, caption=None, renderer="plotly", lang="pt"):
    """
    Visualização interativa do mapa LCZ.

    Wrapper fino sobre LCZ4py.general.lcz_plot_map: em vez de desenhar um PNG
    estático via matplotlib, delega para o motor Plotly/MapLibre do LCZ4py
    (zoom/pan reais, WebGL para rasters grandes). LCZ4py exige um caminho de
    arquivo ou dataset rasterio — se `x` vier como tupla (dados, perfil), como
    no contrato antigo desta função, ela é gravada num arquivo temporário.

    `lang="pt"` por padrão: sem isso, a legenda, o título do mapa e os nomes
    das classes LCZ saem em inglês (padrão do LCZ4py), inconsistente com o
    resto da plataforma, que é toda em português.

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
    lang : str, default "pt"
        Idioma da legenda, título e nomes das classes LCZ ("pt"/"en"/"es"/"zh",
        conforme suportado pelo LCZ4py)

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
            lang=lang,
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
    (média/desvio/mín/máx) continuam vindo do `gdf` vetorizado — LCZ4py não
    expõe contagem de polígonos, e esses valores ficam disponíveis no
    resultado mesmo que a UI atual não os exiba.

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
        'cores_lcz': CORES_LCZ,
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


# Descrições didáticas dos Parâmetros Urbanos de Superfície (UCP) mais
# relevantes para o tema da plataforma (morfologia urbana x ilha de calor);
# variáveis que a LCZ4py processe mas não estejam aqui aparecem com seu nome
# técnico mesmo (o processamento não fica limitado a esta lista).
UCP_DESCRICOES = {
    "built_hei": "Altura média das edificações (m) — quanto maior, mais a área retém calor à noite (efeito 'canyon urbano').",
    "built_sur": "Fração de superfície construída (%) — telhados e pavimento substituem vegetação, elevando a temperatura.",
    "built_vol": "Volume construído por área (m³) — combina altura e densidade de ocupação do solo.",
    "pop": "Densidade populacional (hab/célula) — proxy de atividade humana e emissão de calor antrópico.",
    "tree": "Cobertura arbórea (%) — árvores resfriam por sombreamento e evapotranspiração.",
    "urban": "Fração de área urbanizada (%) — quanto mais urbanizado, maior a tendência de ilha de calor.",
    "urban_frc": "Fração urbana (%) — mesma leitura de 'urban', em fonte de dado diferente.",
    "elevation": "Elevação do terreno (m) — influencia drenagem de ar frio e microclima local.",
    "hgt": "Altura do dossel/vegetação (m) — porte médio da cobertura vegetal na célula.",
    "frc_esa": "Fração de cobertura do solo (ESA WorldCover) — uso e ocupação do solo.",
    "cglc": "Classe de cobertura do solo (GLC_FCS30D) — categoria dominante de uso do solo.",
    "lb": "Comprimento médio das edificações (m) — dimensão típica dos edifícios na célula (WUMPOD).",
    "lc": "Fração de cobertura por edificações — quanto do solo é ocupado por construções (WUMPOD).",
    "lf": "Fração de terreno (não-água/não-vegetação) — proxy de área disponível para uso urbano (WUMPOD).",
    "lp": "Perímetro médio das edificações (m) — relacionado à complexidade da forma dos edifícios (WUMPOD).",
}

# Categoria de processamento (== grupo de download) de cada variável do UCP na
# LCZ4py, e a fonte/unidade de cada uma — usadas para (1) só disparar o
# download da categoria realmente selecionada pelo usuário (lcz_get_ucp baixa
# cada categoria inteira de uma vez, não variável por variável) e (2) montar
# título/legenda informativos no mapa.
UCP_CATEGORIA = {
    "built_hei": "ghsl", "built_sur": "ghsl", "built_vol": "ghsl", "pop": "ghsl",
    "elevation": "wumpod", "frc_esa": "wumpod", "hgt": "wumpod", "lb": "wumpod",
    "lc": "wumpod", "lf": "wumpod", "lp": "wumpod", "urban_frc": "wumpod", "cglc": "wumpod",
    "tree": "vegetacao", "urban": "vegetacao",
}
UCP_FONTE_CATEGORIA = {
    "ghsl": "Global Human Settlement Layer (GHSL), Comissão Europeia/JRC",
    "wumpod": "WUMPOD (Patel & Roth) e conjuntos associados (Zenodo)",
    "vegetacao": "GLC_FCS30D (Zhang et al., 2021)",
}
UCP_UNIDADE = {
    "built_hei": "m", "built_sur": "m²/m²", "built_vol": "m³", "pop": "hab/km²",
    "elevation": "m", "frc_esa": "fração", "hgt": "m", "lb": "m", "lc": "fração",
    "lf": "fração", "lp": "m", "urban_frc": "%", "cglc": "classe",
    "tree": "%", "urban": "%",
}
UCP_PALETA = {
    "built_hei": "YlOrRd", "built_sur": "YlOrRd", "built_vol": "YlOrRd",
    "pop": "OrRd", "urban": "YlOrRd", "urban_frc": "YlOrRd",
    "tree": "Greens", "hgt": "Greens", "elevation": "Viridis",
    "frc_esa": "Earth", "cglc": "Earth", "lb": "Cividis", "lc": "Cividis",
    "lf": "Cividis", "lp": "Cividis",
}
UCP_INTERPRETACAO = {
    "built_hei": "Valores altos indicam edifícios mais altos e maior potencial de cânions urbanos.",
    "built_sur": "Valores altos indicam maior presença de telhados/pavimentos e menor superfície permeável.",
    "built_vol": "Valores altos combinam densidade e verticalização da forma urbana.",
    "pop": "Valores altos indicam maior concentração de pessoas e atividade urbana.",
    "tree": "Valores altos indicam maior sombreamento e evapotranspiração, associados a resfriamento local.",
    "urban": "Valores altos indicam maior fração urbanizada.",
    "urban_frc": "Valores altos indicam maior fração urbana segundo a fonte WUMPOD.",
    "elevation": "Diferenças de altitude ajudam a interpretar drenagem de ar frio e exposição topográfica.",
    "hgt": "Valores altos indicam vegetação mais alta ou dossel mais desenvolvido.",
}

# Catálogo didático de índices espectrais oferecido ao usuário — um
# subconjunto (vegetação, água, urbano) do catálogo completo da LCZ4py
# (~30 índices), para manter as opções claras para fins de ensino.
INDICES_ESPECTRAIS_DESCRICOES = {
    "NDVI": "Índice de Vegetação (NDVI) — varia de -1 a 1; quanto mais próximo de 1, mais vegetação densa e saudável.",
    "SAVI": "Índice de Vegetação Ajustado ao Solo (SAVI) — como o NDVI, mas corrige a influência do solo exposto em áreas com pouca vegetação.",
    "NDBI": "Índice de Área Construída (NDBI) — valores positivos indicam superfícies construídas/impermeáveis.",
    "UI": "Índice Urbano (UI) — realça áreas construídas de forma parecida ao NDBI, útil para comparar os dois.",
    "MNDWI": "Índice de Água (MNDWI) — valores positivos indicam presença de água (rios, lagos, represas).",
    "BSI": "Índice de Solo Exposto (BSI) — valores altos indicam solo nu ou pavimento sem vegetação nem água.",
}
# Pré-seleção sugerida ao usuário: um índice de cada tema (vegetação/urbano/água).
INDICES_ESPECTRAIS_PADRAO = ["NDVI", "NDBI", "MNDWI"]
# Todos os índices deste catálogo didático variam nesta faixa (LCZ4py.PARAM_UNITS).
INDICES_ESPECTRAIS_FAIXA = "-1 a 1"
INDICES_ESPECTRAIS_TEMA = {
    "NDVI": "Vegetação",
    "SAVI": "Vegetação",
    "NDBI": "Construção",
    "UI": "Construção",
    "MNDWI": "Água",
    "BSI": "Solo exposto",
}
INDICES_ESPECTRAIS_FONTE = (
    "Sentinel-2 L2A (Copernicus/ESA), acessado via Microsoft Planetary Computer; "
    "estatísticas por LCZ calculadas com LCZ4py."
)


def _ajustar_layout_plotly(fig, title=None, height=560, legend=True):
    """Aplica um tema legível aos gráficos gerados pela LCZ4py."""
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=21)) if title else fig.layout.title,
        height=height,
        margin=dict(l=28, r=28, t=78, b=62),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.82)",
        font=dict(family="Arial, sans-serif", size=15, color="#163044"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0,
            title=dict(font=dict(size=15)),
            font=dict(size=14),
        ),
        showlegend=legend,
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial, sans-serif"),
    )
    fig.update_xaxes(
        title_font=dict(size=16),
        tickfont=dict(size=13),
        gridcolor="rgba(148,163,184,0.22)",
        zeroline=False,
    )
    fig.update_yaxes(
        title_font=dict(size=16),
        tickfont=dict(size=13),
        gridcolor="rgba(148,163,184,0.18)",
        zeroline=False,
    )
    return fig


def lcz_get_parametros_urbanos(raster_path, variables=None, cache_dir=CACHE_DIR_LCZ4PY):
    """
    Baixa e processa Parâmetros Urbanos de Superfície (UCP) — altura e volume
    construído, cobertura arbórea, densidade populacional, etc. — como uma
    pilha de rasters recortada na área do mapa LCZ já baixado.

    Wrapper fino sobre LCZ4py.general.lcz_get_ucp: chama sem `stations`, que
    faz a função devolver diretamente a pilha de rasters (`combined_rasters`)
    em vez de extrair valores pontuais, já que a plataforma explora a área
    como um todo em vez de estações específicas.

    Liga só as categorias de download (`process_ghsl`/`process_wumpod`/
    `process_vegetation`) que cobrem os `variables` pedidos, e desliga sempre
    `process_directional` (16 variáveis direcionais que esta plataforma não
    oferece). Por padrão, a LCZ4py liga as 4 categorias inteiras (>20
    variáveis, incluindo as 16 direcionais nunca usadas aqui) mesmo que
    `variables` peça só 1 parâmetro — isso é o que deixava o download lento
    e, quando alguma categoria não pedida falhava, fazia sobrar só 1 parâmetro
    disponível para plotar.

    Nota: dentro da LCZ4py, `variables` só filtra as categorias WUMPOD/
    vegetação — a categoria GHSL (altura, superfície e volume construído,
    população) é baixada e processada como bloco único, então pedir 1
    variável GHSL sempre traz as outras 3 junto.

    Parameters
    ----------
    raster_path : str
        Caminho do GeoTIFF do mapa LCZ recortado (o mesmo usado por lcz_cal_area)
    variables : list of str, optional
        Parâmetros a processar (ver `UCP_DESCRICOES`); por padrão processa
        todos os parâmetros disponíveis — passe uma lista para deixar a
        escolha explícita para o usuário e reduzir o tempo de download.
    cache_dir : str
        Diretório de cache dos dados brutos baixados (GHSL, WUMPOD, etc.) —
        por padrão o mesmo `CACHE_DIR_LCZ4PY` usado pelo mapa LCZ e pelo
        Sentinel-2, para que a poda de cache (`_podar_cache_lcz4py`) governe
        um único diretório em vez de vários crescendo sem controle.

    Returns
    -------
    dict
        Ver LCZ4py.general.lcz_get_ucp — usa-se aqui `combined_rasters`
        (xarray.Dataset) e `variable_list`.
    """
    from LCZ4py.general import lcz_get_ucp as _lcz4py_get_ucp

    if variables:
        categorias = {UCP_CATEGORIA.get(v) for v in variables}
    else:
        categorias = {"ghsl", "wumpod", "vegetacao"}

    resultado = _lcz4py_get_ucp(
        lcz_map=raster_path,
        stations=None,
        variables=variables,
        cache_dir=cache_dir,
        process_ghsl="ghsl" in categorias,
        process_wumpod="wumpod" in categorias,
        process_vegetation="vegetacao" in categorias,
        process_directional=False,
        verbose=False,
    )
    _podar_cache_lcz4py(cache_dir)
    return resultado


def lcz_plot_parametro_urbano(ucp_result, parametro):
    """
    Gera o mapa interativo (Plotly) de um Parâmetro Urbano de Superfície já
    processado por `lcz_get_parametros_urbanos`, com título, legenda (unidade)
    e nota de fonte de dados preenchidos — a LCZ4py só conhece as unidades dos
    ~34 parâmetros morfológicos clássicos (Stewart & Oke), não as dos UCP.

    Wrapper fino sobre LCZ4py.general.lcz_plot_parameters.

    Parameters
    ----------
    ucp_result : dict
        Resultado de `lcz_get_parametros_urbanos`
    parametro : str
        Nome da variável a plotar (um dos itens de `ucp_result['variable_list']`)

    Returns
    -------
    plotly.graph_objects.Figure
    """
    from LCZ4py.general import lcz_plot_parameters as _lcz4py_plot_parameters

    descricao = UCP_DESCRICOES.get(parametro, parametro)
    categoria = UCP_CATEGORIA.get(parametro)
    fonte = UCP_FONTE_CATEGORIA.get(categoria, "LCZ4py")
    unidade = UCP_UNIDADE.get(parametro, "")

    fig = _lcz4py_plot_parameters(
        ucp_result["combined_rasters"], iselect=parametro,
        title=f"{parametro} — {descricao.split(' — ')[0]}",
        subtitle=f"Fonte: {fonte}",
        caption="Processado com LCZ4py (github.com/ByMaxAnjos/LCZ4py)",
    )
    _ajustar_layout_plotly(
        fig,
        title=f"{parametro} — {descricao.split(' — ')[0]}",
        height=620,
        legend=True,
    )
    for trace in fig.data:
        if hasattr(trace, "coloraxis"):
            trace.coloraxis = "coloraxis"
        if hasattr(trace, "hovertemplate"):
            trace.hovertemplate = (
                f"<b>{parametro}</b><br>Valor: %{{z:.2f}} {unidade}<extra></extra>"
                if unidade else f"<b>{parametro}</b><br>Valor: %{{z:.2f}}<extra></extra>"
            )
    fig.update_layout(
        coloraxis=dict(
            colorscale=UCP_PALETA.get(parametro, "Viridis"),
            colorbar=dict(
                title=dict(text=unidade or parametro, font=dict(size=16)),
                tickfont=dict(size=13),
                len=0.78,
                thickness=18,
            ),
        ),
        annotations=[
            dict(
                text=f"Fonte: {fonte} · Processado com LCZ4py",
                xref="paper", yref="paper", x=0, y=-0.08,
                showarrow=False, xanchor="left", font=dict(size=13, color="#475569"),
            )
        ],
    )
    return fig


# Bandas do Sentinel-2 L2A necessárias para cobrir todo o catálogo didático em
# INDICES_ESPECTRAIS_DESCRICOES: red/green/blue/nir (B04/B03/B02/B08) cobrem
# NDVI/SAVI; NDBI, UI, MNDWI e BSI também precisam de swir1/swir2 (B11/B12) —
# o atalho "sentinel-2-l2a" da LCZ4py baixa só B04/B03/B02/B08 por padrão, o
# que faz esses 4 índices falharem com "banda(s) faltante(s): swir1/swir2".
BANDAS_SENTINEL2 = ["B04", "B03", "B02", "B08", "B11", "B12"]


def lcz_baixar_sentinel2(raster_path, dias=90, cobertura_nuvem_max=30):
    """
    Baixa bandas do Sentinel-2 (Microsoft Planetary Computer) recortadas na
    área do mapa LCZ já baixado, para uso no cálculo de índices espectrais.

    Wrapper fino sobre LCZ4py.general.lcz_get_planetary_computer: fixa uma
    janela recente (`dias`) em vez de deixar o intervalo em aberto, para
    manter o download leve o suficiente para rodar no Streamlit Cloud, e pede
    explicitamente `BANDAS_SENTINEL2` (em vez do atalho padrão da coleção, que
    só traz 4 bandas) para que todo índice do catálogo didático consiga ser
    calculado.

    Parameters
    ----------
    raster_path : str
        Caminho do GeoTIFF do mapa LCZ recortado
    dias : int, default 90
        Tamanho da janela de busca por imagens recentes com pouca nuvem
    cobertura_nuvem_max : float, default 30
        Cobertura de nuvem máxima aceita (%) nas cenas usadas

    Returns
    -------
    LCZ4py.general.LCZPCResult
        `.array` é (n_bandas, altura, largura); `.bands` nomeia cada banda
    """
    from datetime import date, timedelta
    from LCZ4py.general import lcz_get_planetary_computer as _lcz4py_get_pc

    fim = date.today()
    inicio = fim - timedelta(days=dias)

    resultado = _lcz4py_get_pc(
        raster_path,
        collection="sentinel-2-l2a",
        assets=BANDAS_SENTINEL2,
        start_date=inicio.isoformat(),
        end_date=fim.isoformat(),
        max_cloud_cover=cobertura_nuvem_max,
        cache_dir=CACHE_DIR_LCZ4PY,
        verbose=False,
        lang="pt",
    )
    _podar_cache_lcz4py()
    return resultado


def lcz_calcular_indices(pc_result, indices=None):
    """
    Calcula índices espectrais a partir das bandas do Sentinel-2 baixadas por
    `lcz_baixar_sentinel2`.

    Wrapper fino sobre LCZ4py.general.lcz_get_indices: por padrão restringe ao
    catálogo didático `INDICES_ESPECTRAIS_DESCRICOES` (~6 índices) em vez do
    catálogo completo da LCZ4py (~30), mantendo as opções claras para ensino
    e o processamento leve.

    Parameters
    ----------
    pc_result : LCZ4py.general.LCZPCResult
        Resultado de `lcz_baixar_sentinel2`
    indices : list of str, optional
        Índices a calcular (ver `INDICES_ESPECTRAIS_DESCRICOES`); por padrão
        usa `INDICES_ESPECTRAIS_PADRAO`.

    Returns
    -------
    LCZ4py.general.LCZIndicesResult
    """
    from LCZ4py.general import lcz_get_indices as _lcz4py_get_indices

    return _lcz4py_get_indices(pc_result, indices=indices or INDICES_ESPECTRAIS_PADRAO, lang="pt")


def lcz_estatisticas_indices(raster_path, indices_result):
    """
    Estatísticas descritivas por classe LCZ dos índices espectrais, com um
    gráfico de caixas (boxplot) comparando a distribuição de cada índice
    entre as classes LCZ da área.

    Wrapper fino sobre LCZ4py.general.lcz_cal_indices: preenche `subtitle`/
    `caption` com a fonte dos dados (a LCZ4py só anota título/legenda quando
    pedido explicitamente) e acrescenta a faixa de valores de cada índice
    (a LCZ4py não rotula isso nos títulos dos subgráficos).

    Parameters
    ----------
    raster_path : str
        Caminho do GeoTIFF do mapa LCZ recortado (mesma grade dos índices)
    indices_result : LCZ4py.general.LCZIndicesResult
        Resultado de `lcz_calcular_indices`

    Returns
    -------
    LCZ4py.general.LCZIndicesStatsResult
        `.df` tem uma linha por (índice, classe LCZ); `.fig['box']` é o
        gráfico Plotly
    """
    from LCZ4py.general import lcz_cal_indices as _lcz4py_cal_indices

    resultado = _lcz4py_cal_indices(
        raster_path, indices_result, plot_type="box", lang="pt",
        subtitle="Fonte: Sentinel-2 (Copernicus/ESA) via Microsoft Planetary Computer",
        caption="Processado com LCZ4py (github.com/ByMaxAnjos/LCZ4py)",
    )
    for annotation in resultado.fig.layout.annotations or []:
        if annotation.text in INDICES_ESPECTRAIS_DESCRICOES:
            annotation.text = f"{annotation.text} [{INDICES_ESPECTRAIS_FAIXA}]"
            annotation.font = dict(size=15, color="#163044")
    _ajustar_layout_plotly(
        resultado.fig,
        title="Distribuição dos índices espectrais por classe LCZ",
        height=620,
        legend=True,
    )
    for trace in resultado.fig.data:
        nome = str(getattr(trace, "name", ""))
        if nome in CORES_LCZ and hasattr(trace, "marker"):
            trace.marker.color = CORES_LCZ[nome]
            trace.marker.line = dict(color="#163044", width=0.8)
        if hasattr(trace, "line") and nome in CORES_LCZ:
            trace.line.color = CORES_LCZ[nome]
        if hasattr(trace, "boxmean"):
            trace.boxmean = "sd"
        if hasattr(trace, "jitter"):
            trace.jitter = 0.28
        if hasattr(trace, "pointpos"):
            trace.pointpos = -1.45
    resultado.fig.update_layout(
        boxmode="group",
        annotations=list(resultado.fig.layout.annotations or []) + [
            dict(
                text=f"Fonte: {INDICES_ESPECTRAIS_FONTE}",
                xref="paper", yref="paper", x=0, y=-0.1,
                showarrow=False, xanchor="left", font=dict(size=13, color="#475569"),
            )
        ],
    )
    return resultado
