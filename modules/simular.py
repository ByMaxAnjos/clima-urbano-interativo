'''
Módulo de Simulação de Intervenções Urbanas - Interface Streamlit
PLATAFORMA DIDÁTICA DE CLIMA URBANO

Este módulo fornece uma interface interativa e educativa para simular o impacto térmico
de intervenções urbanas, com foco em aprendizagem sobre ilhas de calor urbanas.
'''

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import folium
from shapely.geometry import Polygon
import json
from utils import simulacao
import time
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

# --- Configurações e Constantes ---

TIPOS_INTERVENCAO = [
    "Parque Urbano",
    "Alteração de Albedo", 
    "Telhado Verde",
    "Pavimento Permeável",
    "Expansão Urbana"
]

# Informações educativas para cada tipo de intervenção
INFO_INTERVENCOES = {
    "Parque Urbano": {
        "descricao": "Áreas verdes que reduzem temperaturas através da sombra e evapotranspiração",
        "beneficios": ["Redução de temperatura", "Melhoria da qualidade do ar", "Bem-estar psicológico"],
        "exemplos": ["Parque Ibirapuera (SP)", "Central Park (NY)", "Hyde Park (Londres)"],
        "impacto_teorico": "Pode reduzir a temperatura em 2-5°C localmente"
    },
    "Alteração de Albedo": {
        "descricao": "Aumento da refletividade de superfícies para reduzir absorção de calor",
        "beneficios": ["Redução do efeito de ilha de calor", "Menor consumo de energia", "Conforto térmico"],
        "exemplos": ["Telhados brancos", "Pavimentos claros", "Superfícies reflexivas"],
        "impacto_teorico": "Cada 0.1 de aumento no albedo pode reduzir a temperatura em 0.5-1°C"
    },
    "Telhado Verde": {
        "descricao": "Coberturas vegetadas que isolam termicamente e absorvem calor",
        "beneficios": ["Isolamento térmico", "Redução de enxurradas", "Biodiversidade urbana"],
        "exemplos": ["Prefeitura de Chicago (EUA)", "Centro de Vancouver (Canadá)", "Edifícios em Cingapura"],
        "impacto_teorico": "Pode reduzir a temperatura do telhado em até 30°C no verão"
    },
    "Pavimento Permeável": {
        "descricao": "Superfícies que permitem infiltração de água, reduzindo calor por evaporação",
        "beneficios": ["Drenagem sustentável", "Redução de enchentes", "Conforto térmico"],
        "exemplos": ["Calçadas permeáveis", "Estacionamentos drenantes", "Vias com infiltração"],
        "impacto_teorico": "Pode ser 5-10°C mais frio que pavimento convencional"
    },
    "Expansão Urbana": {
        "descricao": "Aumento de áreas construídas que geralmente intensifica ilhas de calor",
        "beneficios": ["Expansão econômica", "Mais habitações", "Desenvolvimento"],
        "desvantagens": ["Aumento de temperatura", "Maior impermeabilização", "Perda de áreas verdes"],
        "impacto_teorico": "Pode aumentar temperaturas em 1-4°C em relação a áreas rurais"
    }
}

# --- Novas Funções: Validação e Visualização de Resultados ---

def validar_parametros_intervencao(tipo: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Valida parâmetros de intervenção urbana com auto-correção.

    Valida os parâmetros de cada tipo de intervenção e aplica auto-correção
    para valores fora dos ranges permitidos, gerando warnings descritivos.

    Args:
        tipo (str): Tipo de intervenção urbana
            - "telhado_verde": cobertura vegetal em telhados
            - "parque_urbano": áreas verdes urbanas
            - "albedo": aumento de refletividade de superfícies
            - "arvores": plantação de árvores
        parametros (dict): Dicionário com parâmetros específicos do tipo

    Returns:
        dict: Dicionário estruturado com:
            - 'valid' (bool): Validação passou sem erros críticos
            - 'errors' (list): Erros que impedem execução
            - 'warnings' (list): Alertas sobre correções aplicadas
            - 'parametros_corrigidos' (dict): Parâmetros ajustados

    Examples:
        >>> validar_parametros_intervencao("telhado_verde", {"area": 50, "espessura": 3})
        {'valid': False, 'errors': ['area: valor 50 fora do range [0-100]'], ...}

        >>> validar_parametros_intervencao("arvores", {"densidade": 600, "altura": 5})
        {'valid': True, 'errors': [], 'warnings': ['densidade: corrigida de 600 para 500 (máximo)'], ...}
    '''

    # Dicionário de validação por tipo de intervenção
    validacao_rules = {
        "telhado_verde": {
            "area": {"min": 0, "max": 100, "tipo": "percentual", "default": 50},
            "espessura": {"min": 5, "max": 50, "tipo": "cm", "default": 15},
            "umidade": {"min": 30, "max": 90, "tipo": "percentual", "default": 60}
        },
        "parque_urbano": {
            "area": {"min": 0, "max": 100, "tipo": "percentual", "default": 50},
            "cobertura_vegetal": {"min": 20, "max": 100, "tipo": "percentual", "default": 70},
            "umidade": {"min": 40, "max": 95, "tipo": "percentual", "default": 70}
        },
        "albedo": {
            "valor_novo": {"min": 0.2, "max": 0.9, "tipo": "refletividade", "default": 0.6},
            "area_afetada": {"min": 0, "max": 100, "tipo": "percentual", "default": 50}
        },
        "arvores": {
            "densidade": {"min": 0, "max": 500, "tipo": "arvores/ha", "default": 200},
            "altura_media": {"min": 2, "max": 25, "tipo": "metros", "default": 10},
            "sombra_percentual": {"min": 10, "max": 80, "tipo": "percentual", "default": 50}
        }
    }

    resultado = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'parametros_corrigidos': {}
    }

    # Verificar se tipo é suportado
    if tipo not in validacao_rules:
        resultado['valid'] = False
        resultado['errors'].append(
            f"Tipo de intervenção não suportado: '{tipo}'. "
            f"Tipos válidos: {', '.join(validacao_rules.keys())}"
        )
        return resultado

    rules = validacao_rules[tipo]

    # Validar cada parâmetro
    for param_nome, rule in rules.items():
        valor = parametros.get(param_nome, rule['default'])
        min_val = rule['min']
        max_val = rule['max']
        tipo_param = rule['tipo']

        # Tentar converter para número
        try:
            valor_num = float(valor)
        except (ValueError, TypeError):
            resultado['valid'] = False
            resultado['errors'].append(
                f"{param_nome}: valor '{valor}' não é numérico (esperado {tipo_param})"
            )
            resultado['parametros_corrigidos'][param_nome] = rule['default']
            continue

        # Validar range e aplicar auto-correção
        if valor_num < min_val:
            resultado['warnings'].append(
                f"{param_nome}: corrigido de {valor_num} para {min_val} "
                f"(mínimo permitido para {tipo_param})"
            )
            resultado['parametros_corrigidos'][param_nome] = min_val
        elif valor_num > max_val:
            resultado['warnings'].append(
                f"{param_nome}: corrigido de {valor_num} para {max_val} "
                f"(máximo permitido para {tipo_param})"
            )
            resultado['parametros_corrigidos'][param_nome] = max_val
        else:
            resultado['parametros_corrigidos'][param_nome] = valor_num

    # Validações cruzadas específicas do tipo
    if tipo == "telhado_verde" and resultado['parametros_corrigidos'].get('espessura', 15) > 30:
        resultado['warnings'].append(
            "Espessura > 30cm: peso estrutural elevado, verificar viabilidade arquitetônica"
        )

    if tipo == "parque_urbano" and resultado['parametros_corrigidos'].get('cobertura_vegetal', 70) < 50:
        resultado['warnings'].append(
            "Cobertura vegetal < 50%: efetividade reduzida em resfriamento urbano"
        )

    if tipo == "arvores" and resultado['parametros_corrigidos'].get('altura_media', 10) < 5:
        resultado['warnings'].append(
            "Altura média < 5m: árvores jovens, benefício térmico limitado inicialmente"
        )

    return resultado


@st.cache_data
def _calcular_timeline_impacto(resultado_simulacao: Dict, num_meses: int = 12) -> pd.DataFrame:
    '''
    Calcula impacto progressivo ao longo do tempo.
    Função auxiliar com cache para performance.
    '''
    timeline = []
    impacto_total = resultado_simulacao.get('delta_total', 0)

    for mes in range(1, num_meses + 1):
        # Modelar crescimento com curva sigmoide (maturação progressiva)
        progresso = 1.0 / (1.0 + (10 ** (-1 * (mes - 6) / 2)))  # Saturação em ~6 meses
        impacto_mes = impacto_total * progresso

        timeline.append({
            'mês': mes,
            'impacto_acumulado': impacto_mes,
            'percentual_efetividade': progresso * 100
        })

    return pd.DataFrame(timeline)


def visualizar_resultado_simulacao(
    resultado: Dict[str, Any],
    tipo_intervencao: str,
    dados_original: Dict = None
) -> None:
    '''
    Visualiza resultados detalhados da simulação com gráficos comparativos.

    Cria uma análise visual completa do impacto da intervenção, incluindo:
    - Comparação antes/depois de temperatura
    - Cards de métricas de impacto
    - Timeline de maturação da intervenção
    - Mapa interativo da região afetada
    - Interpretação automática do resultado

    Args:
        resultado (dict): Resultado da simulação contendo:
            - 'delta_total' (float): Variação total de temperatura em °C
            - 'resumo_detalhado' (list): Detalhes por intervenção
        tipo_intervencao (str): Tipo de intervenção simulada
        dados_original (dict, optional): Dados contextuais (temperatura base, geometria)

    Returns:
        None (renderiza diretamente na interface Streamlit)

    Effects:
        - Exibe múltiplas visualizações interativas
        - Renderiza cards com métricas
        - Mostra interpretação educativa do resultado
    '''

    if not resultado or 'delta_total' not in resultado:
        st.error("❌ Resultado de simulação inválido ou vazio")
        return

    delta_total = resultado.get('delta_total', 0)
    resumo = resultado.get('resumo_detalhado', [])

    # Temperatura de referência (simulada se não fornecida)
    temp_base = 28.0  # São Paulo média verão
    temp_simulada = temp_base + delta_total

    st.markdown("---")
    st.markdown("### 📊 Visualização de Resultados - Simulação Detalhada")

    # ===== SEÇÃO 1: COMPARAÇÃO ANTES/DEPOIS =====
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🌡️ Temperatura Base",
            f"{temp_base:.1f}°C",
            help="Temperatura média urbana atual"
        )

    with col2:
        # Cor dinâmica baseada no impacto
        if delta_total < -1:
            cor_delta = "✅ Resfriamento"
        elif delta_total < 0:
            cor_delta = "🟢 Leve resfriamento"
        elif delta_total < 1:
            cor_delta = "⚪ Neutro"
        else:
            cor_delta = "🔴 Aquecimento"

        st.metric(
            "Variação de Temperatura",
            f"{delta_total:+.2f}°C",
            delta=f"{delta_total:+.2f}°C",
            help="Impacto estimado da intervenção"
        )

    with col3:
        st.metric(
            "🌡️ Temperatura Projetada",
            f"{temp_simulada:.1f}°C",
            delta=f"{delta_total:+.2f}°C",
            help="Temperatura após intervenção"
        )

    # ===== SEÇÃO 2: GRÁFICO COMPARATIVO ANTES/DEPOIS =====
    st.markdown("#### 📈 Comparação Térmica")

    df_comparacao = pd.DataFrame({
        'Cenário': ['Atual (Base)', 'Com Intervenção'],
        'Temperatura (°C)': [temp_base, temp_simulada]
    })

    fig_comparacao = px.bar(
        df_comparacao,
        x='Cenário',
        y='Temperatura (°C)',
        color='Cenário',
        color_discrete_sequence=['#ff6b6b', '#51cf66'],
        text_auto='.1f',
        title='Temperatura Média: Antes vs Depois da Intervenção',
        labels={'Temperatura (°C)': 'Temperatura (°C)'}
    )
    fig_comparacao.update_layout(height=350, showlegend=False)
    fig_comparacao.update_traces(textposition='outside')
    st.plotly_chart(fig_comparacao, use_container_width=True)

    # ===== SEÇÃO 3: CARDS DE MÉTRICAS =====
    st.markdown("#### 📊 Métricas de Impacto")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        # Redução de temperatura
        percentual_reducao = (abs(delta_total) / temp_base * 100) if temp_base > 0 else 0
        st.metric(
            "Redução Térmica",
            f"{abs(delta_total):.2f}°C",
            f"-{percentual_reducao:.1f}%",
            help="Diminuição absoluta e relativa de temperatura"
        )

    with col_m2:
        # Benefício energético estimado
        # Simplificação: ~0.5 kWh/habitante/ano por 0.1°C de resfriamento
        beneficio_kwh = abs(delta_total) * 0.5 * 10 * 1000  # × 1000 habitantes base
        st.metric(
            "Benefício Energético",
            f"{beneficio_kwh:,.0f}",
            "kWh/ano",
            help="Economia anual estimada em climatização"
        )

    with col_m3:
        # Área afetada (consolidada de resumo)
        area_total = sum([item.get('area_m2', 0) for item in resumo if item.get('valido', False)])
        area_ha = area_total / 10000
        st.metric(
            "Área Afetada",
            f"{area_ha:,.1f}",
            "hectares",
            help="Extensão territorial da intervenção"
        )

    with col_m4:
        # Custo estimado (simplificado)
        # Parque: ~$200/m², Telhado Verde: ~$150/m², Albedo: ~$30/m², Árvores: ~$50/un
        custos_unitarios = {
            'parque_urbano': 200,
            'telhado_verde': 150,
            'albedo': 30,
            'arvores': 50
        }
        custo_total = 0
        for item in resumo:
            area = item.get('area_m2', 0)
            tipo = item.get('tipo', '').lower()

            # Mapear tipos para chaves de custo
            if 'Parque' in item.get('tipo', ''):
                custo_total += area * custos_unitarios['parque_urbano']
            elif 'Telhado Verde' in item.get('tipo', ''):
                custo_total += area * custos_unitarios['telhado_verde']
            elif 'Albedo' in item.get('tipo', ''):
                custo_total += area * custos_unitarios['albedo']
            elif 'Árvores' in item.get('tipo', '') or 'arvores' in item.get('tipo', '').lower():
                custo_total += 50 * (area / 1000)  # ~50 árvores por 1000m²

        st.metric(
            "Custo Estimado",
            f"${custo_total:,.0f}",
            "USD",
            help="Investimento estimado em implementação"
        )

    # ===== SEÇÃO 4: TIMELINE DE MATURAÇÃO =====
    st.markdown("#### ⏳ Impacto Progressivo (Primeiros 12 Meses)")

    df_timeline = _calcular_timeline_impacto(resultado, num_meses=12)

    fig_timeline = px.line(
        df_timeline,
        x='mês',
        y='impacto_acumulado',
        markers=True,
        title='Evolução do Impacto Térmico ao Longo do Tempo',
        labels={
            'mês': 'Mês após implementação',
            'impacto_acumulado': 'Impacto Térmico Acumulado (°C)'
        },
        color_discrete_sequence=['#0ea5e9']
    )
    fig_timeline.add_hline(
        y=delta_total,
        line_dash="dash",
        line_color="green",
        annotation_text="Impacto máximo (100%)",
        annotation_position="right"
    )
    fig_timeline.update_layout(height=350, hovermode='x unified')
    st.plotly_chart(fig_timeline, use_container_width=True)

    # ===== SEÇÃO 5: INTERPRETAÇÃO AUTOMÁTICA =====
    st.markdown("#### 🔍 Interpretação do Resultado")

    if delta_total <= -2:
        nivel_impacto = "🌿 **ALTO IMPACTO** - Resfriamento Significativo"
        descricao = """
        Sua intervenção apresenta **forte potencial de resfriamento urbano**, com redução
        de 2°C ou mais. Este é um resultado **excelente** que:
        - Reduz significativamente a ilha de calor urbana
        - Melhora o conforto térmico da população
        - Gera economia energética importante em climatização
        - Aumenta a biodiversidade e qualidade de vida
        """
        cor_bg = "🟢"
    elif delta_total < 0:
        nivel_impacto = "✅ **IMPACTO MODERADO** - Resfriamento Positivo"
        descricao = """
        Sua intervenção gera **resfriamento moderado e benéfico**, com resultado entre 0 e -2°C.
        Este é um cenário **positivo** que:
        - Contribui para redução da ilha de calor
        - Oferece benefício ambiental e térmico
        - Pode ser combinado com outras intervenções para maior impacto
        - Segue direção correta para sustentabilidade urbana
        """
        cor_bg = "🟡"
    elif delta_total < 1:
        nivel_impacto = "⚖️ **IMPACTO NEUTRO** - Efeitos Balanceados"
        descricao = """
        Sua intervenção apresenta **efeito térmico mínimo ou equilibrado**. Recomenda-se:
        - Rever os parâmetros (densidade, cobertura vegetal, etc.)
        - Aumentar a área de intervenção
        - Combinar com outras medidas complementares
        - Focar em benefícios secundários (biodiversidade, drenagem)
        """
        cor_bg = "🔵"
    else:
        nivel_impacto = "🔥 **AQUECIMENTO ESTIMADO** - Atenção Necessária"
        descricao = """
        Sua intervenção pode **intensificar a ilha de calor urbana** com aquecimento positivo.
        **Ação recomendada:**
        - Revise completamente o cenário (especialmente expansões urbanas)
        - Adicione medidas de resfriamento (parques, telhados verdes)
        - Reduza fatores de construção ou impermeabilização
        - Consulte especialista em clima urbano antes de implementação
        """
        cor_bg = "🔴"

    with st.container(border=True):
        st.markdown(f"### {cor_bg} {nivel_impacto}")
        st.markdown(descricao)

    # ===== SEÇÃO 6: DISTRIBUIÇÃO DE IMPACTO POR INTERVENCAO =====
    if len(resumo) > 1:
        st.markdown("#### 🎯 Contribuição por Tipo de Intervenção")

        df_resumo = pd.DataFrame(resumo)
        df_resumo_valido = df_resumo[df_resumo.get('valido', True)]

        if len(df_resumo_valido) > 0:
            fig_pizza = px.pie(
                df_resumo_valido,
                values='impacto_ponderado',
                names='tipo',
                title='Distribuição do Impacto Térmico',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pizza.update_layout(height=400)
            st.plotly_chart(fig_pizza, use_container_width=True)

# --- Funções de Inicialização ---

def inicializar_session_state():
    '''Inicializa as variáveis de estado da sessão.'''
    if 'intervencoes' not in st.session_state:
        st.session_state.intervencoes = []
    if 'cenarios' not in st.session_state:
        st.session_state.cenarios = {}
    if 'poligonos_desenhados' not in st.session_state:
        st.session_state.poligonos_desenhados = []
    if 'resultado_simulacao' not in st.session_state:
        st.session_state.resultado_simulacao = None
    if 'historico_simulacoes' not in st.session_state:
        st.session_state.historico_simulacoes = []
    if 'tutorial_ativo' not in st.session_state:
        st.session_state.tutorial_ativo = True

# --- Componentes de Interface Melhorados ---

def renderizar_header():
    '''Renderiza o cabeçalho com informações educativas.'''
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); 
                padding: 2rem; border-radius: 10px; color: white;">
        <h1 style="color: white; margin: 0;">🌍 Módulo Simular</h1>
        <p style="color: white; font-size: 1.2rem; margin: 0.5rem 0 0 0;">
            Simule intervenções urbanas e entenda seu impacto no microclima
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Botão agora fica abaixo do cabeçalho
    st.markdown("<br>", unsafe_allow_html=True)  # espaço
    if st.button("🎓 Tutorial Interativo", use_container_width=False):
        st.session_state.tutorial_ativo = not st.session_state.tutorial_ativo

def renderizar_tutorial():
    '''Renderiza um tutorial interativo para novos usuários.'''
    if not st.session_state.tutorial_ativo:
        return
    
    with st.expander("🎓 Tutorial - Como usar esta plataforma", expanded=True):
        st.markdown("""
        ### Bem-vindo ao módulo Simulador!
        
        **Objetivo:** Esta ferramenta ajuda você a entender como diferentes intervenções 
        urbanas afetam a temperatura local (efeito de ilha de calor urbana).
        
        ### 📋 Passo a Passo:
        
        1. **🏗️ Adicione Intervenções**: Na aba 'Intervenções', selecione o tipo de mudança urbana
        2. **🗺️ Defina a Localização**: Use o mapa para desenhar onde a intervenção acontecerá
        3. **🚀 Execute a Simulação**: Clique em 'Executar Simulação' para calcular os impactos
        4. **📊 Analise Resultados**: Veja gráficos e interpretações dos resultados
        
        ### 💡 Conceitos Chave:
        - **Ilha de Calor Urbana**: Áreas urbanas significativamente mais quentes que zonas rurais vizinhas
        - **Albedo**: Refletividade de uma superfície (superfícies claras = alto albedo)
        - **Evapotranspiração**: Resfriamento por evaporação da água das plantas
        """)
        
        if st.button("Entendi, vamos começar!"):
            st.session_state.tutorial_ativo = False
            st.rerun()

def calcular_area_geografica(coords):
    '''Calcula área aproximada usando fórmula de Haversine.'''
    if len(coords) < 3:
        return 0
    
    # Simplificação: usar aproximação retangular para áreas pequenas
    lats = [coord[1] for coord in coords]
    lons = [coord[0] for coord in coords]
    
    # Converter para metros aproximadamente
    lat_center = sum(lats) / len(lats)
    
    # 1 grau de latitude ≈ 111 km
    # 1 grau de longitude ≈ 111 km * cos(latitude)
    lat_to_m = 111000
    lon_to_m = 111000 * cos(radians(lat_center))
    
    # Calcular área usando fórmula do shoelace
    area = 0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    
    area = abs(area) / 2
    
    # Converter para metros quadrados
    area_m2 = area * lat_to_m * lon_to_m
    
    return area_m2

def renderizar_card_intervencao_melhorado(intervencao, index):
    '''Renderiza um card expandido para uma intervenção.'''
    with st.container():
        # Header do card
        with st.expander(f"🏗️ Intervenção {index + 1}: {intervencao['tipo']}", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                area = intervencao.get('area_m2', 0)
                st.metric("Área", f"{area:,.0f} m²", help="Área total da intervenção")
                
                # Informações educativas
                info = INFO_INTERVENCOES.get(intervencao['tipo'], {})
                if info:
                    st.caption(f"💡 {info['descricao']}")
            
            with col2:
                parametros = intervencao.get('parametros', {})
                if parametros:
                    for k, v in parametros.items():
                        if isinstance(v, (int, float)):
                            st.progress(v, text=f"{k.replace('_', ' ').title()}: {v:.2f}")
                        else:
                            st.write(f"**{k.replace('_', ' ').title()}:** {v}")
            
            with col3:
                if st.button("❌ Remover", key=f"remove_{index}"):
                    st.session_state.intervencoes.pop(index)
                    st.rerun()
            
            # Detalhes expandidos
            if intervencao['tipo'] in INFO_INTERVENCOES:
                info = INFO_INTERVENCOES[intervencao['tipo']]
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("**✅ Benefícios:**")
                    for beneficio in info.get('beneficios', []):
                        st.write(f"• {beneficio}")
                
                with col_info2:
                    st.markdown("**🏛️ Exemplos Reais:**")
                    for exemplo in info.get('exemplos', []):
                        st.write(f"• {exemplo}")

def renderizar_formulario_nova_intervencao_melhorado():
    '''Renderiza o formulário com informações educativas.'''
    st.markdown("### ➕ Adicionar Nova Intervenção")
    
    with st.form("nova_intervencao", border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_selecionado = st.selectbox(
                "Tipo de Intervenção",
                TIPOS_INTERVENCAO,
                help="Selecione o tipo de mudança urbana que deseja simular."
            )
            
            # Exibir informações sobre a intervenção selecionada
            if tipo_selecionado in INFO_INTERVENCOES:
                info = INFO_INTERVENCOES[tipo_selecionado]
                with st.container():
                    st.markdown(f"**📚 Sobre {tipo_selecionado}:**")
                    st.info(info['descricao'])
        
        with col2:
            area_estimada = st.number_input(
                "Área Estimada (m²)",
                min_value=100.0,
                max_value=10_000_000.0,
                value=50_000.0,
                step=1000.0,
                help="Área aproximada da intervenção. Será atualizada se você desenhar no mapa."
            )
            
            # Comparativo de área
            if area_estimada > 0:
                campos_futebol = area_estimada / 7000  # Aproximadamente área de um campo
                st.caption(f"📏 Equivale a aproximadamente {campos_futebol:.1f} campos de futebol")
        
        # Parâmetros específicos com explicações
        st.markdown("**🔧 Parâmetros da Intervenção:**")
        parametros = {}
        
        if tipo_selecionado == "Parque Urbano":
            parametros["densidade"] = st.slider(
                "Densidade da Vegetação", 0.0, 1.0, 0.7, 0.05,
                help="Densidade de árvores e vegetação (0 = sem vegetação, 1 = muito denso)."
            )
            st.caption("🌳 Vegetação mais densa proporciona maior sombreamento e evapotranspiração")
        
        elif tipo_selecionado == "Alteração de Albedo":
            col_a, col_b = st.columns(2)
            with col_a:
                parametros["albedo_original"] = st.slider(
                    "Albedo Original", 0.0, 1.0, 0.2, 0.05,
                    help="Albedo médio da superfície antes da intervenção (0 = preto absoluto, 1 = branco perfeito)."
                )
                st.caption(f"🎨 Superfície atual reflete {parametros['albedo_original']*100:.0f}% da luz")
            with col_b:
                parametros["novo_albedo"] = st.slider(
                    "Novo Albedo", 0.0, 1.0, 0.6, 0.05,
                    help="Albedo da nova superfície após a intervenção."
                )
                st.caption(f"🎨 Nova superfície refletirá {parametros['novo_albedo']*100:.0f}% da luz")
        
        elif tipo_selecionado == "Telhado Verde":
            parametros["cobertura"] = st.slider(
                "Cobertura Verde", 0.0, 1.0, 0.5, 0.05,
                help="Percentual de cobertura verde nos telhados."
            )
            st.caption(f"🌿 {parametros['cobertura']*100:.0f}% da área terá vegetação")
        
        elif tipo_selecionado == "Pavimento Permeável":
            parametros["permeabilidade"] = st.slider(
                "Permeabilidade", 0.0, 1.0, 0.6, 0.05,
                help="Capacidade do pavimento de infiltrar água."
            )
            st.caption(f"💧 {parametros['permeabilidade']*100:.0f}% da água da chuva será infiltrará")
        
        elif tipo_selecionado == "Expansão Urbana":
            parametros["fator_construcao"] = st.slider(
                "Fator de Construção", 0.0, 1.0, 0.8, 0.05,
                help="Intensidade da construção na nova área."
            )
            st.caption(f"🏢 {parametros['fator_construcao']*100:.0f}% da área será construída")
        
        submitted = st.form_submit_button("➕ Adicionar Intervenção", type="primary", use_container_width=True)
        
        if submitted:
            nova_intervencao = {
                "tipo": tipo_selecionado,
                "area_m2": area_estimada,
                "parametros": parametros,
                "timestamp": pd.Timestamp.now().isoformat()
            }
            st.session_state.intervencoes.append(nova_intervencao)
            st.success(f"✅ Intervenção '{tipo_selecionado}' adicionada com sucesso!")
            st.balloons()
            time.sleep(1)
            st.rerun()

def renderizar_mapa_interativo_melhorado():
    '''Renderiza o mapa interativo com camadas educativas.'''
    st.markdown("### 🗺️ Mapa de Intervenções")
    
    # Controles do mapa
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info("📍 **Dica:** Desenhe polígonos no mapa para definir áreas de intervenção")
    
    with col2:
        if st.button("🗑️ Limpar Áreas", help="Remove todas as áreas desenhadas"):
            st.session_state.poligonos_desenhados = []
            st.rerun()
    
    with col3:
        camada_calor = st.checkbox("🌡️ Camada de Calor", value=True, 
                                 help="Mostra áreas de maior temperatura")
    
    # Criar mapa base
    m = folium.Map(location=[-23.55, -46.63], zoom_start=12)
    
    # Adicionar camada de calor simulada (dados educativos)
    if camada_calor:
        # Simular áreas de maior temperatura (ilhas de calor)
        heat_data = [
            [-23.55, -46.63, 0.9],  # Centro
            [-23.56, -46.65, 0.7],   # Área comercial
            [-23.54, -46.60, 0.6]    # Área residencial densa
        ]
        
        for point in heat_data:
            folium.Circle(
                location=point[:2],
                radius=500,
                color='red',
                fill=True,
                fillOpacity=point[2]*0.3,
                popup=f"Área de calor intenso: {point[2]*100:.0f}%"
            ).add_to(m)
    
    # Adicionar ferramenta de desenho
    folium.plugins.Draw(
        export=False,
        draw_options={
            'polygon': {'allowIntersection': False},
            'rectangle': True,
            'circle': False,
            'marker': False,
            'polyline': False
        }
    ).add_to(m)
    
    # Adicionar polígonos já desenhados
    for i, poligono in enumerate(st.session_state.poligonos_desenhados):
        # Cor baseada no tipo de intervenção (se associada)
        cor = 'blue'
        if 'intervencao_associada' in poligono:
            tipo = poligono['intervencao_associada']
            cores = {
                "Parque Urbano": "green",
                "Alteração de Albedo": "white",
                "Telhado Verde": "lightgreen",
                "Pavimento Permeável": "lightblue",
                "Expansão Urbana": "red"
            }
            cor = cores.get(tipo, 'blue')
        
        folium.Polygon(
            locations=poligono['coordinates'],
            color=cor,
            fill=True,
            fillOpacity=0.5,
            popup=f"Área {i+1}: {poligono.get('area_m2', 0):,.0f} m²"
        ).add_to(m)
    
    # Renderizar mapa
    map_data = st_folium(m, width=700, height=500)
    
    # Processar novos desenhos
    if map_data and 'all_drawings' in map_data and map_data['all_drawings']:
        for drawing in map_data['all_drawings']:
            if drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
                coords = drawing['geometry']['coordinates'][0]
                
                # Calcular área aproximada
                if len(coords) >= 3:
                    try:
                        area_m2 = calcular_area_geografica(coords)
                        
                        novo_poligono = {
                            'coordinates': coords,
                            'area_m2': area_m2,
                            'geometry': drawing['geometry'],
                            'timestamp': pd.Timestamp.now().isoformat()
                        }
                        
                        # Associar à última intervenção se existir
                        if st.session_state.intervencoes:
                            novo_poligono['intervencao_associada'] = st.session_state.intervencoes[-1]['tipo']
                        
                        if novo_poligono not in st.session_state.poligonos_desenhados:
                            st.session_state.poligonos_desenhados.append(novo_poligono)
                            st.rerun()
                    except Exception as e:
                        st.warning(f"Erro ao processar área desenhada: {e}")

def renderizar_gerenciamento_cenarios():
    '''Renderiza a seção de gerenciamento de cenários.'''
    st.markdown("### 💾 Gerenciamento de Cenários")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome_cenario = st.text_input(
            "Nome do Cenário",
            placeholder="Ex: Cenário Verde, Expansão Controlada...",
            help="Digite um nome descritivo para o cenário atual."
        )
        
        if st.button("💾 Salvar Cenário Atual", type="secondary"):
            if nome_cenario and st.session_state.intervencoes:
                st.session_state.cenarios[nome_cenario] = {
                    'intervencoes': st.session_state.intervencoes.copy(),
                    'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success(f"✅ Cenário '{nome_cenario}' salvo com sucesso!")
            else:
                st.warning("⚠️ Digite um nome e adicione pelo menos uma intervenção.")
    
    with col2:
        if st.session_state.cenarios:
            cenario_selecionado = st.selectbox(
                "Carregar Cenário Salvo",
                [""] + list(st.session_state.cenarios.keys()),
                help="Selecione um cenário salvo para carregar."
            )
            
            if st.button("📂 Carregar Cenário", type="secondary"):
                if cenario_selecionado:
                    st.session_state.intervencoes = st.session_state.cenarios[cenario_selecionado]['intervencoes'].copy()
                    st.success(f"✅ Cenário '{cenario_selecionado}' carregado!")
                    st.rerun()

def renderizar_simulacao_e_resultados_melhorado():
    '''Renderiza a seção de simulação com análise educativa.'''
    st.markdown("### 🚀 Simulação e Resultados")
    
    if not st.session_state.intervencoes:
        st.info("ℹ️ Adicione pelo menos uma intervenção para executar a simulação.")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**📋 Resumo das Intervenções:**")
        for i, interv in enumerate(st.session_state.intervencoes):
            tipo = interv.get('tipo', 'Tipo não definido')
            area = interv.get('area_m2', 0)
            st.write(f"• {tipo} ({area:,.0f} m²)")
        
        nome_simulacao = st.text_input("Nome da Simulação", value=f"Simulação {len(st.session_state.historico_simulacoes) + 1}")
        
        if st.button("🔥 Executar Simulação", type="primary", use_container_width=True):
            try:
                # Validar e corrigir estrutura das intervenções
                intervencoes_validadas = []
                validacoes_erros = []
                validacoes_avisos = []

                for i, interv in enumerate(st.session_state.intervencoes):
                    tipo_intervencao = interv.get('tipo', 'Parque Urbano')
                    parametros = interv.get('parametros', {})

                    # Aplicar validação robusta (compatível com tipos existentes)
                    # Nota: validador suporta novos tipos; aqui usamos para warnings
                    tipo_normalizado = tipo_intervencao.lower().replace(' ', '_')

                    intervencao_corrigida = {
                        'tipo': tipo_intervencao,
                        'area_m2': interv.get('area_m2', 50000.0),
                        'parametros': parametros
                    }

                    # Log de validação (informativo)
                    if tipo_normalizado in ['telhado_verde', 'parque_urbano', 'albedo', 'arvores']:
                        validacao = validar_parametros_intervencao(tipo_normalizado, parametros)
                        if validacao['warnings']:
                            validacoes_avisos.extend([f"[{tipo_intervencao}] {w}" for w in validacao['warnings']])
                        if validacao['errors']:
                            validacoes_erros.extend([f"[{tipo_intervencao}] {e}" for e in validacao['errors']])

                    intervencoes_validadas.append(intervencao_corrigida)

                # Exibir warnings e erros de validação
                if validacoes_erros:
                    with st.expander("⚠️ Erros de Validação Encontrados", expanded=False):
                        for erro in validacoes_erros:
                            st.error(f"• {erro}")

                if validacoes_avisos:
                    with st.expander("ℹ️ Avisos de Validação", expanded=False):
                        for aviso in validacoes_avisos:
                            st.warning(f"• {aviso}")

                # Executar simulação
                delta_total, resumo_detalhado = simulacao.combinar_intervencoes(intervencoes_validadas)

                resultado_simulacao = {
                    'delta_total': delta_total,
                    'resumo_detalhado': resumo_detalhado
                }

                st.session_state.resultado_simulacao = resultado_simulacao

                # Adicionar ao histórico
                st.session_state.historico_simulacoes.append({
                    'cenario': nome_simulacao,
                    'intervencoes': intervencoes_validadas,
                    'resultado': resultado_simulacao,
                    'timestamp': pd.Timestamp.now().isoformat()
                })

                st.rerun()

            except Exception as e:
                st.error(f"❌ Erro na simulação: {e}")
                st.write("**Debug Info:**")
                st.write(f"Intervenções: {st.session_state.intervencoes}")
    
    with col2:
        if st.session_state.resultado_simulacao:
            resultado = st.session_state.resultado_simulacao
            delta = resultado['delta_total']
            
            # Métrica principal
            st.metric(
                "Impacto Térmico Total",
                f"{delta:.2f} °C",
                delta=f"{delta:.2f} °C"
            )
            
            # Feedback educativo expandido
            if delta < -1:
                st.success("""
                **Excelente resultado!** 🌿
                - Forte potencial de resfriamento urbano
                - Redução significativa da ilha de calor
                - Benefícios múltiplos para a população
                """)
            elif delta < 0:
                st.success("""
                **Resultado positivo!** ✅
                - Efeito de resfriamento moderado
                - Contribuição para melhoria do microclima
                - Direção correta para sustentabilidade urbana
                """)
            elif delta < 1:
                st.warning("""
                **Impacto neutro** ⚖️
                - Intervenções com efeitos balanceados
                - Considere ajustar parâmetros ou adicionar mais intervenções de resfriamento
                """)
            else:
                st.error("""
                **Atenção: Aquecimento estimado** 🔥
                - As intervenções podem intensificar a ilha de calor
                - Revise as intervenções, especialmente expansões urbanas
                - Considere adicionar medidas de resfriamento
                """)

def renderizar_visualizacoes_avancadas_melhorado():
    '''Renderiza gráficos e análises educativas.'''
    if not st.session_state.resultado_simulacao:
        return

    # Renderizar visualização completa com nova função
    resultado = st.session_state.resultado_simulacao
    tipo_intervencao_principal = st.session_state.intervencoes[0].get('tipo', 'Simulação') if st.session_state.intervencoes else 'Simulação'

    visualizar_resultado_simulacao(resultado, tipo_intervencao_principal)

    # Análises adicionais expandidas
    st.markdown("---")
    st.markdown("### 📊 Análise Detalhada")
    
    resultado = st.session_state.resultado_simulacao
    resumo = resultado['resumo_detalhado']
    
    # Criar DataFrame para visualizações
    df_resumo = pd.DataFrame(resumo)
    
    # Abas para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Impacto por Intervenção", "🥧 Distribuição", "🌡️ Comparativo", "📋 Tabela Detalhada"])
    
    with tab1:
        # Gráfico de barras com cores significativas
        fig_barras = px.bar(
            df_resumo,
            x='tipo',
            y='impacto_ponderado',
            title='Contribuição de Cada Intervenção para a Variação de Temperatura',
            labels={'impacto_ponderado': 'Variação de Temperatura (°C)', 'tipo': 'Tipo de Intervenção'},
            color='impacto_ponderado',
            color_continuous_scale='RdYlBu_r',
            text_auto='.2f'
        )
        fig_barras.update_layout(
            height=400,
            xaxis_tickangle=-45,
            showlegend=False
        )
        fig_barras.update_traces(textposition='outside')
        st.plotly_chart(fig_barras, use_container_width=True)
        
        # Análise do gráfico
        st.markdown("**📋 Análise:**")
        if len(df_resumo) > 0:
            maior_impacto = df_resumo.loc[df_resumo['impacto_ponderado'].abs().idxmax()]
            st.write(f"- **Intervenção com maior impacto**: {maior_impacto['tipo']} ({maior_impacto['impacto_ponderado']:+.2f}°C)")
            st.write(f"- **Número de intervenções**: {len(df_resumo)}")
            st.write(f"- **Área total intervencionada**: {df_resumo['area_m2'].sum():,.0f} m²")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza - Distribuição de áreas
            fig_pizza_area = px.pie(
                df_resumo,
                values='area_m2',
                names='tipo',
                title='Distribuição de Áreas por Tipo de Intervenção',
                hole=0.4
            )
            fig_pizza_area.update_layout(height=400)
            st.plotly_chart(fig_pizza_area, use_container_width=True)
        
        with col2:
            # Gráfico de pizza - Distribuição de impacto
            df_impacto_abs = df_resumo.copy()
            df_impacto_abs['impacto_abs'] = df_impacto_abs['impacto_ponderado'].abs()
            
            fig_pizza_impacto = px.pie(
                df_impacto_abs,
                values='impacto_abs',
                names='tipo',
                title='Distribuição do Impacto Térmico (Absoluto)',
                hole=0.4
            )
            fig_pizza_impacto.update_layout(height=400)
            st.plotly_chart(fig_pizza_impacto, use_container_width=True)
    
    with tab3:
        # Gráfico de comparação área vs impacto
        fig_scatter = px.scatter(
            df_resumo,
            x='area_m2',
            y='impacto_ponderado',
            size='area_m2',
            color='tipo',
            title='Relação entre Área e Impacto Térmico',
            labels={'area_m2': 'Área (m²)', 'impacto_ponderado': 'Variação de Temperatura (°C)'}
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Análise de eficiência
        if len(df_resumo) > 0:
            st.markdown("**📈 Eficiência por Área:**")
            df_resumo['eficiencia'] = df_resumo['impacto_ponderado'] / (df_resumo['area_m2'] / 10000)  # Impacto por hectare
            mais_eficiente = df_resumo.loc[df_resumo['eficiencia'].abs().idxmax()]
            st.write(f"- **Intervenção mais eficiente**: {mais_eficiente['tipo']} ({mais_eficiente['eficiencia']:+.3f}°C/hectare)")
    
    with tab4:
        # Tabela detalhada interativa
        st.markdown("**📋 Detalhamento por Intervenção:**")
        df_display = df_resumo[['tipo', 'area_m2', 'impacto_individual', 'peso_aplicado', 'impacto_ponderado']].copy()
        df_display.columns = ['Tipo', 'Área (m²)', 'Impacto Individual (°C)', 'Peso', 'Impacto Ponderado (°C)']
        df_display['Área (m²)'] = df_display['Área (m²)'].apply(lambda x: f"{x:,.0f}")
        df_display['Impacto Ponderado (°C)'] = df_display['Impacto Ponderado (°C)'].apply(lambda x: f"{x:+.3f}")
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )

def renderizar_historico_comparativo():
    '''Renderiza comparação entre simulações do histórico.'''
    if len(st.session_state.historico_simulacoes) < 2:
        return
    
    st.markdown("### 📚 Comparativo do Histórico")
    
    # Preparar dados para comparação
    dados_comparacao = []
    for sim in st.session_state.historico_simulacoes:
        dados_comparacao.append({
            'Cenário': sim['cenario'],
            'ΔT (°C)': sim['resultado']['delta_total'],
            'Nº Intervenções': len(sim['intervencoes']),
            'Área Total (m²)': sum([i['area_m2'] for i in sim['intervencoes']])
        })
    
    df_comparacao = pd.DataFrame(dados_comparacao)
    
    # Gráfico de comparação
    fig_comparacao = px.bar(
        df_comparacao,
        x='Cenário',
        y='ΔT (°C)',
        title='Comparação entre Cenários Simulados',
        color='ΔT (°C)',
        color_continuous_scale='RdYlBu_r',
        text_auto='.2f'
    )
    fig_comparacao.update_layout(height=400)
    st.plotly_chart(fig_comparacao, use_container_width=True)
    
    # Tabela comparativa
    st.dataframe(df_comparacao, use_container_width=True)

def renderizar_exportacao():
    '''Renderiza opções de exportação dos resultados.'''
    if not st.session_state.resultado_simulacao:
        return
    
    st.markdown("### 📤 Exportar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Exportar CSV", use_container_width=True):
            df_resumo = pd.DataFrame(st.session_state.resultado_simulacao['resumo_detalhado'])
            csv = df_resumo.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar CSV",
                data=csv,
                file_name="simulacao_clima_urbano.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Exportar JSON", use_container_width=True):
            json_data = json.dumps(st.session_state.resultado_simulacao, indent=2)
            st.download_button(
                label="⬇️ Baixar JSON",
                data=json_data,
                file_name="simulacao_clima_urbano.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("📄 Gerar Relatório", use_container_width=True):
            st.info("🚧 Funcionalidade de relatório em desenvolvimento.")

# --- Função Principal Melhorada ---

def renderizar_pagina():
    '''Função principal que renderiza toda a página.'''
    inicializar_session_state()
    
    # Header educativo
    renderizar_header()
    renderizar_tutorial()
    
    # Indicadores rápidos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Intervenções Ativas", len(st.session_state.intervencoes))
    with col2:
        st.metric("Áreas Mapeadas", len(st.session_state.poligonos_desenhados))
    with col3:
        st.metric("Cenários Salvos", len(st.session_state.cenarios))
    with col4:
        st.metric("Simulações Realizadas", len(st.session_state.historico_simulacoes))
    
    # Layout principal em abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏗️ Intervenções", "🗺️ Mapa", "🚀 Simular", "📊 Resultados", "📚 Histórico"])
    
    with tab1:
        if st.session_state.intervencoes:
            st.markdown("### 📋 Intervenções Configuradas")
            for i, intervencao in enumerate(st.session_state.intervencoes):
                renderizar_card_intervencao_melhorado(intervencao, i)
            st.markdown("---")
        
        renderizar_formulario_nova_intervencao_melhorado()
        
        st.markdown("---")
        renderizar_gerenciamento_cenarios()
    
    with tab2:
        renderizar_mapa_interativo_melhorado()
        
        if st.session_state.poligonos_desenhados:
            st.markdown("**🗺️ Áreas Desenhadas:**")
            for i, poly in enumerate(st.session_state.poligonos_desenhados):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Área {i+1}**: {poly['area_m2']:,.0f} m²")
                    if 'intervencao_associada' in poly:
                        st.caption(f"Associada à: {poly['intervencao_associada']}")
                with col2:
                    if st.button("🗑️", key=f"del_poly_{i}"):
                        st.session_state.poligonos_desenhados.pop(i)
                        st.rerun()
    
    with tab3:
        renderizar_simulacao_e_resultados_melhorado()
    
    with tab4:
        if st.session_state.resultado_simulacao:
            renderizar_visualizacoes_avancadas_melhorado()
            renderizar_exportacao()
        else:
            st.info("🚀 Execute uma simulação na aba 'Simular' para ver resultados detalhados")
    
    with tab5:
        if st.session_state.historico_simulacoes:
            renderizar_historico_comparativo()
            
            # Opção para limpar histórico
            if st.button("🗑️ Limpar Histórico de Simulações", type="secondary"):
                st.session_state.historico_simulacoes = []
                st.rerun()
        else:
            st.info("📚 O histórico de simulações aparecerá aqui após múltiplas execuções")