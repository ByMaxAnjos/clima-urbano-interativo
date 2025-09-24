'''
Lógica de Simulação Climática para a Plataforma Clima Urbano Interativo
VERSÃO DIDÁTICA MELHORADA

Este módulo contém funções robustas para cálculo do impacto térmico (ΔT) 
de intervenções urbanas, com coeficientes baseados em literatura científica
e funcionalidades educativas.
'''

import numpy as np
import pandas as pd

# --- COEFICIENTES BASEADOS EM LITERATURA CIENTÍFICA ---
# Valores calibrados com base em estudos de ilha de calor urbana

# Fatores de impacto por unidade de área (°C por km²)
FATORES_BASE = {
    "parque_urbano": -3.0,      # Oke (1989), Bowler et al. (2010)
    "alteracao_albedo": -0.6,   # Akbari et al. (2001) - por 0.1 de aumento no albedo
    "telhado_verde": -1.8,      # Takebayashi & Moriyama (2007)
    "pavimento_permeavel": -1.2, # Li et al. (2013)
    "expansao_urbana": 2.5       # Oke (1982)
}

# Fatores de escala para conversão de área
FATOR_AREA = 1.0 / 1000000  # Converter m² para km²

# --- FUNÇÕES AUXILIARES EDUCATIVAS ---

def explicar_impacto(tipo_intervencao, parametros, area_m2, resultado):
    '''Gera explicação educativa para o resultado da simulação.'''
    explicacoes = {
        "Parque Urbano": f"""
        **Mecanismo de resfriamento**: Evapotranspiração e sombreamento
        - Área vegetada: {area_m2:,.0f} m²
        - Densidade da vegetação: {parametros.get('densidade', 0):.1f}
        - Efeito estimado: {resultado:.3f}°C de resfriamento
        """,
        
        "Alteração de Albedo": f"""
        **Mecanismo de resfriamento**: Aumento da reflexão de radiação solar
        - Albedo original: {parametros.get('albedo_original', 0):.2f}
        - Novo albedo: {parametros.get('novo_albedo', 0):.2f}
        - Melhoria: +{(parametros.get('novo_albedo', 0) - parametros.get('albedo_original', 0)):.2f}
        - Efeito estimado: {resultado:.3f}°C de resfriamento
        """,
        
        "Telhado Verde": f"""
        **Mecanismo de resfriamento**: Isolamento térmico e evapotranspiração
        - Área de telhado: {area_m2:,.0f} m²
        - Cobertura verde: {parametros.get('cobertura', 0)*100:.0f}%
        - Efeito estimado: {resultado:.3f}°C de resfriamento
        """,
        
        "Pavimento Permeável": f"""
        **Mecanismo de resfriamento**: Evaporação da água infiltrada
        - Área permeabilizada: {area_m2:,.0f} m²
        - Taxa de permeabilidade: {parametros.get('permeabilidade', 0)*100:.0f}%
        - Efeito estimado: {resultado:.3f}°C de resfriamento
        """,
        
        "Expansão Urbana": f"""
        **Mecanismo de aquecimento**: Aumento de superfícies impermeáveis e calor antropogênico
        - Área urbanizada: {area_m2:,.0f} m²
        - Intensidade construtiva: {parametros.get('fator_construcao', 0)*100:.0f}%
        - Efeito estimado: {resultado:+.3f}°C de aquecimento
        """
    }
    
    return explicacoes.get(tipo_intervencao, "Intervenção não reconhecida.")

def validar_parametros(tipo, parametros, area_m2):
    '''Valida os parâmetros de entrada e retorna mensagens educativas.'''
    erros = []
    alertas = []
    
    # Validação de área
    if area_m2 <= 0:
        erros.append("Área deve ser maior que zero")
    elif area_m2 > 100000000:  # 100 km²
        alertas.append("Área muito grande para escala local")
    elif area_m2 < 1000:  # 0.001 km²
        alertas.append("Área muito pequena para impacto significativo")
    
    # Validações específicas por tipo
    if tipo == "Parque Urbano":
        densidade = parametros.get('densidade', 0)
        if not 0 <= densidade <= 1:
            erros.append("Densidade deve estar entre 0 e 1")
        elif densidade < 0.3:
            alertas.append("Densidade baixa pode limitar o efeito de resfriamento")
    
    elif tipo == "Alteração de Albedo":
        albedo_original = parametros.get('albedo_original', 0)
        novo_albedo = parametros.get('novo_albedo', 0)
        
        if not 0 <= albedo_original <= 1 or not 0 <= novo_albedo <= 1:
            erros.append("Valores de albedo devem estar entre 0 e 1")
        
        if novo_albedo < albedo_original:
            alertas.append("Redução do albedo pode aumentar a temperatura")
    
    elif tipo == "Telhado Verde":
        cobertura = parametros.get('cobertura', 0)
        if not 0 <= cobertura <= 1:
            erros.append("Cobertura deve estar entre 0 e 1")
        elif cobertura < 0.2:
            alertas.append("Cobertura verde inferior a 20% pode ter efeito limitado")
    
    elif tipo == "Pavimento Permeável":
        permeabilidade = parametros.get('permeabilidade', 0)
        if not 0 <= permeabilidade <= 1:
            erros.append("Permeabilidade deve estar entre 0 e 1")
    
    elif tipo == "Expansão Urbana":
        fator_construcao = parametros.get('fator_construcao', 0)
        if not 0 <= fator_construcao <= 1:
            erros.append("Fator de construção deve estar entre 0 e 1")
        elif fator_construcao > 0.9:
            alertas.append("Alta densidade construtiva pode intensificar ilha de calor")
    
    return erros, alertas

# --- FUNÇÕES DE CÁLCULO MELHORADAS ---

def _calcular_impacto_parque(area_m2, densidade):
    '''Calcula o ΔT para um parque urbano com efeito não-linear.'''
    area_km2 = area_m2 * FATOR_AREA
    
    # Efeito não-linear: parques maiores têm maior eficiência
    fator_eficiencia = min(1.0, 0.5 + (area_km2 * 0.5))  # Limite de eficiência
    
    impacto = FATORES_BASE["parque_urbano"] * area_km2 * densidade * fator_eficiencia
    
    # Limitar efeito máximo realisticamente
    return max(impacto, -5.0)  # Máximo de 5°C de resfriamento

def _calcular_impacto_albedo(albedo_original, novo_albedo, area_m2):
    '''Calcula o ΔT para alteração de albedo com escala de área.'''
    diferenca_albedo = novo_albedo - albedo_original
    area_km2 = area_m2 * FATOR_AREA
    
    # Impacto proporcional à diferença de albedo e área
    impacto = FATORES_BASE["alteracao_albedo"] * diferenca_albedo * 10 * area_km2  # *10 para converter de 0.1
    
    return impacto

def _calcular_impacto_telhado_verde(area_m2, cobertura):
    '''Calcula o ΔT para telhados verdes.'''
    area_km2 = area_m2 * FATOR_AREA
    return FATORES_BASE["telhado_verde"] * area_km2 * cobertura

def _calcular_impacto_pavimento_permeavel(area_m2, permeabilidade):
    '''Calcula o ΔT para pavimentos permeáveis.'''
    area_km2 = area_m2 * FATOR_AREA
    
    # Efeito depende da permeabilidade
    impacto = FATORES_BASE["pavimento_permeavel"] * area_km2 * permeabilidade
    
    return impacto

def _calcular_impacto_expansao_urbana(area_m2, fator_construcao):
    '''Calcula o ΔT para expansão urbana com efeito de saturação.'''
    area_km2 = area_m2 * FATOR_AREA
    
    # Efeito de saturação: áreas muito construídas têm impacto relativo menor
    fator_saturacao = 1.0 - (fator_construcao * 0.2)  # Redução de 20% no máximo
    
    impacto = FATORES_BASE["expansao_urbana"] * area_km2 * fator_construcao * fator_saturacao
    
    return impacto

# --- DICIONÁRIO DE FUNÇÕES ATUALIZADO ---
MAPA_INTERVENCOES = {
    "Parque Urbano": _calcular_impacto_parque,
    "Alteração de Albedo": _calcular_impacto_albedo,
    "Telhado Verde": _calcular_impacto_telhado_verde,
    "Pavimento Permeável": _calcular_impacto_pavimento_permeavel,
    "Expansão Urbana": _calcular_impacto_expansao_urbana
}

# --- FUNÇÃO PRINCIPAL DE SIMULAÇÃO MELHORADA ---

def aplicar_intervencao(tipo, area_m2, parametros, retornar_explicacao=False):
    '''
    Aplica uma intervenção e calcula seu impacto térmico com validação.
    
    Args:
        tipo (str): Tipo de intervenção
        area_m2 (float): Área em metros quadrados
        parametros (dict): Parâmetros específicos
        retornar_explicacao (bool): Se deve retornar explicação educativa
    
    Returns:
        dict: Resultado com impacto e metadados
    '''
    # Validar entrada
    erros, alertas = validar_parametros(tipo, parametros, area_m2)
    
    if erros:
        raise ValueError(f"Erros de validação: {', '.join(erros)}")
    
    if tipo not in MAPA_INTERVENCOES:
        raise ValueError(f"Tipo de intervenção desconhecido: {tipo}")
    
    funcao_calculo = MAPA_INTERVENCOES[tipo]
    
    try:
        # Executar cálculo baseado no tipo
        if tipo == "Parque Urbano":
            impacto = funcao_calculo(area_m2, parametros.get('densidade', 0.5))
        elif tipo == "Alteração de Albedo":
            impacto = funcao_calculo(
                parametros.get('albedo_original', 0.2), 
                parametros.get('novo_albedo', 0.6),
                area_m2
            )
        elif tipo == "Telhado Verde":
            impacto = funcao_calculo(area_m2, parametros.get('cobertura', 0.5))
        elif tipo == "Pavimento Permeável":
            impacto = funcao_calculo(area_m2, parametros.get('permeabilidade', 0.5))
        elif tipo == "Expansão Urbana":
            impacto = funcao_calculo(area_m2, parametros.get('fator_construcao', 0.8))
        else:
            impacto = 0.0
        
        resultado = {
            'impacto': impacto,
            'valido': True,
            'alertas': alertas,
            'area_km2': area_m2 * FATOR_AREA
        }
        
        if retornar_explicacao:
            resultado['explicacao'] = explicar_impacto(tipo, parametros, area_m2, impacto)
        
        return resultado
        
    except Exception as e:
        return {
            'impacto': 0.0,
            'valido': False,
            'erro': str(e),
            'alertas': alertas
        }

def combinar_intervencoes(lista_intervencoes, pesos=None, retornar_detalhes=True):
    '''
    Calcula o impacto combinado de múltiplas intervenções.
    
    Args:
        lista_intervencoes (list): Lista de intervenções
        pesos (dict): Pesos relativos por tipo
        retornar_detalhes (bool): Se retorna análise detalhada
    
    Returns:
        tuple: (delta_total, resumo_detalhado)
    '''
    if pesos is None:
        pesos = {tipo: 1.0 for tipo in MAPA_INTERVENCOES.keys()}
    
    delta_total = 0.0
    resumo_detalhado = []
    intervencoes_invalidas = []
    
    for i, intervencao in enumerate(lista_intervencoes):
        tipo = intervencao.get('tipo', 'Desconhecido')
        area_m2 = intervencao.get('area_m2', 0.0)
        parametros = intervencao.get('parametros', {})
        
        # Aplicar intervenção individual
        resultado = aplicar_intervencao(tipo, area_m2, parametros, retornar_explicacao=True)
        
        if resultado['valido']:
            impacto_individual = resultado['impacto']
            peso = pesos.get(tipo, 1.0)
            impacto_ponderado = impacto_individual * peso
            
            delta_total += impacto_ponderado
            
            # Detalhes para relatório
            detalhe = {
                "id": i + 1,
                "tipo": tipo,
                "area_m2": area_m2,
                "area_km2": resultado.get('area_km2', 0),
                "parametros": parametros,
                "impacto_individual": impacto_individual,
                "peso_aplicado": peso,
                "impacto_ponderado": impacto_ponderado,
                "valido": True,
                "alertas": resultado.get('alertas', [])
            }
            
            if 'explicacao' in resultado:
                detalhe['explicacao'] = resultado['explicacao']
                
        else:
            intervencoes_invalidas.append(intervencao)
            detalhe = {
                "id": i + 1,
                "tipo": tipo,
                "area_m2": area_m2,
                "valido": False,
                "erro": resultado.get('erro', 'Erro desconhecido'),
                "impacto_individual": 0.0,
                "impacto_ponderado": 0.0
            }
        
        resumo_detalhado.append(detalhe)
    
    # Métadados adicionais para análise
    if retornar_detalhes:
        analise = {
            'total_intervencoes': len(lista_intervencoes),
            'intervencoes_validas': len(lista_intervencoes) - len(intervencoes_invalidas),
            'intervencoes_invalidas': len(intervencoes_invalidas),
            'area_total_km2': sum([d.get('area_km2', 0) for d in resumo_detalhado if d.get('valido', False)]),
            'impacto_maximo': max([d.get('impacto_ponderado', 0) for d in resumo_detalhado], default=0),
            'impacto_minimo': min([d.get('impacto_ponderado', 0) for d in resumo_detalhado], default=0)
        }
        
        for detalhe in resumo_detalhado:
            if detalhe.get('valido', False):
                detalhe['analise_geral'] = analise
    
    return delta_total, resumo_detalhado

# --- FUNÇÕES DE ANÁLISE AVANÇADA ---

def analisar_sensibilidade(tipo_intervencao, parametro, valores, area_base=50000):
    '''
    Analisa a sensibilidade do resultado a variações em um parâmetro.
    
    Args:
        tipo_intervencao (str): Tipo de intervenção
        parametro (str): Parâmetro a variar
        valores (list): Valores a testar
        area_base (float): Área base para teste
    
    Returns:
        DataFrame: Resultados da análise de sensibilidade
    '''
    resultados = []
    
    for valor in valores:
        parametros_test = {parametro: valor}
        
        try:
            resultado = aplicar_intervencao(tipo_intervencao, area_base, parametros_test)
            if resultado['valido']:
                resultados.append({
                    'parametro': parametro,
                    'valor': valor,
                    'impacto': resultado['impacto'],
                    'valido': True
                })
        except:
            resultados.append({
                'parametro': parametro,
                'valor': valor,
                'impacto': 0.0,
                'valido': False
            })
    
    return pd.DataFrame(resultados)

def comparar_estrategias(estrategias):
    '''
    Compara diferentes estratégias de intervenção.
    
    Args:
        estrategias (dict): Dicionário com listas de intervenções
    
    Returns:
        DataFrame: Comparação entre estratégias
    '''
    comparacao = []
    
    for nome, intervencoes in estrategias.items():
        try:
            delta_total, detalhes = combinar_intervencoes(intervencoes)
            
            comparacao.append({
                'estrategia': nome,
                'impacto_total': delta_total,
                'numero_intervencoes': len(intervencoes),
                'area_total': sum([i.get('area_m2', 0) for i in intervencoes]),
                'custo_relativo': len(intervencoes) * 0.1,  # Simplificado
                'eficiencia': delta_total / max(sum([i.get('area_m2', 0) for i in intervencoes]), 1)
            })
        except Exception as e:
            comparacao.append({
                'estrategia': nome,
                'impacto_total': 0.0,
                'erro': str(e)
            })
    
    return pd.DataFrame(comparacao)