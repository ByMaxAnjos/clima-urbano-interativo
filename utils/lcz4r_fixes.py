"""
Correções e extensões para utils/lcz4r.py

Este módulo contém as funções que devem ser adicionadas/corrigidas em lcz4r.py:

1. Mover definições de exceções para antes de seu uso
2. Adicionar função validate_lcz_data() que é referenciada em explorar.py
3. Melhorar robustez de processamento

Instruções de aplicação estão no IMPLEMENTATION_PLAN.md — FASE 3
"""

# ============================================================
# EXCEÇÕES PERSONALIZADAS — Mover para linha ~30 de lcz4r.py
# ============================================================

class GeocodeError(Exception):
    """
    Exceção para erros de geocodificação.

    Levantada quando OSMnx não consegue encontrar uma localidade
    ou quando há falha na busca por coordenadas.
    """
    pass


class DataProcessingError(Exception):
    """
    Exceção para erros no processamento de dados LCZ.

    Levantada quando há problemas ao baixar, recortar ou
    processar dados raster do mapa global LCZ.
    """
    pass


class ValidationError(Exception):
    """
    Exceção para erros de validação de dados.

    Levantada quando dados processados não atendem aos
    critérios de qualidade esperados.
    """
    pass


# ============================================================
# FUNÇÃO DE VALIDAÇÃO — Adicionar após lcz_plot_map()
# ============================================================

def validate_lcz_data(gdf):
    """
    Valida integridade de dados LCZ GeoDataFrame.

    Esta função verifica se dados LCZ estão em formato correto,
    possuem geometrias válidas, e contêm as colunas obrigatórias.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Dados LCZ para validação. Esperado ter coluna 'geometry'
        e opcionalmente 'zcl_classe', 'area_m2'.

    Returns
    -------
    dict
        Dicionário com chaves:
        - 'valid' (bool): Dados são válidos?
        - 'errors' (list): Erros críticos encontrados
        - 'warnings' (list): Avisos não-críticos

    Examples
    --------
    >>> validation = validate_lcz_data(gdf_lcz)
    >>> if validation['valid']:
    ...     print("Dados LCZ válidos!")
    ... else:
    ...     print(f"Erros: {validation['errors']}")
    """

    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    try:
        # Verificação 1: Tipo de dado
        if not hasattr(gdf, 'geometry'):
            result['valid'] = False
            result['errors'].append(
                "GeoDataFrame não possui coluna 'geometry'"
            )
            return result

        # Verificação 2: DataFrame vazio
        if len(gdf) == 0:
            result['valid'] = False
            result['errors'].append(
                "GeoDataFrame está vazio (0 registros)"
            )
            return result

        # Verificação 3: CRS válido
        if gdf.crs is None:
            result['warnings'].append(
                "CRS não definido. Assumindo EPSG:4326"
            )
            try:
                gdf = gdf.set_crs("EPSG:4326")
            except Exception as e:
                result['errors'].append(f"Erro ao definir CRS: {str(e)}")
                result['valid'] = False

        # Verificação 4: Geometrias válidas
        invalid_geoms = gdf[~gdf.geometry.is_valid]
        if len(invalid_geoms) > 0:
            result['warnings'].append(
                f"{len(invalid_geoms)} ({len(invalid_geoms)/len(gdf)*100:.1f}%) "
                "geometrias inválidas detectadas"
            )

        # Verificação 5: Colunas obrigatórias
        required_cols = ['zcl_classe']
        missing_cols = [col for col in required_cols if col not in gdf.columns]
        if missing_cols:
            result['warnings'].append(
                f"Colunas opcionais faltantes: {missing_cols}"
            )

        # Verificação 6: Dados duplicados
        if gdf.duplicated(subset=['geometry']).any():
            dup_count = gdf.duplicated(subset=['geometry']).sum()
            result['warnings'].append(
                f"{dup_count} geometrias duplicadas detectadas"
            )

        # Verificação 7: Bounds válidos
        total_bounds = gdf.total_bounds
        if any([
            total_bounds[0] < -180,  # lon_min
            total_bounds[2] > 180,   # lon_max
            total_bounds[1] < -90,   # lat_min
            total_bounds[3] > 90     # lat_max
        ]):
            result['errors'].append(
                "Bounds de geometria fora dos limites globais"
            )
            result['valid'] = False

        # Verificação 8: Área de dados (se coluna 'area_m2' existir)
        if 'area_m2' in gdf.columns:
            total_area = gdf['area_m2'].sum()
            if total_area < 1e6:  # Menos de 1 km²
                result['warnings'].append(
                    f"Área total pequena: {total_area/1e6:.2f} km² "
                    "(esperado >= 1 km²)"
                )

        return result

    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Erro na validação: {str(e)}")
        return result


# ============================================================
# ALTERAÇÃO NO ARQUIVO lcz4r.py — CHECKLIST
# ============================================================

"""
CHECKLIST DE IMPLEMENTAÇÃO:

[ ] 1. Localizar linhas 329-336 em lcz4r.py que definem exceções
       no final do arquivo

[ ] 2. Cortar as linhas:
       class GeocodeError(Exception):
           pass
       class DataProcessingError(Exception):
           pass

[ ] 3. Colar após line ~30 (após imports e comentário de configuração)
       antes da definição de LCZ_INFO

[ ] 4. Adicionar nova classe ValidationError também neste ponto

[ ] 5. Adicionar função validate_lcz_data() inteira após lcz_plot_map()
       (aproximadamente linha 456)

[ ] 6. Atualizar imports em explorar.py linha 20:
       from utils.lcz4r import (
           lcz_get_map,
           process_lcz_map,
           enhance_lcz_data,
           lcz_plot_map,
           validate_lcz_data,      # ← ADICIONAR
           GeocodeError,
           DataProcessingError,
           ValidationError         # ← ADICIONAR
       )

[ ] 7. Testar com: python -c "from utils.lcz4r import lcz_get_map; print('OK')"

RESULTADO ESPERADO:
    ✅ lcz_get_map() pode ser importada
    ✅ lcz_get_map('São Paulo, Brazil') executa sem erro NameError
    ✅ validate_lcz_data() retorna dict com 'valid', 'errors', 'warnings'
    ✅ Exceções podem ser levantadas e capturadas normalmente
"""
