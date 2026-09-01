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
from math import radians, cos

# --- Configurações e Constantes ---

TIPOS_INTERVENCAO = [
    "Parque Urbano",
    "Alteração de Albedo", 
    "Telhado Verde",
    "Pavimento Permeável",
    "Arborização de Rua",
    "Corpo d'Água Urbano",
    "Expansão Urbana"
]

EVIDENCIA_INTERVENCOES = {
    "Parque Urbano": {
        "metrica": "diferença de temperatura entre parque e entorno",
        "faixa": "1,7–3,3 °C em estudos de parques; até 5,9 °C em noite de verão em um estudo específico",
        "limite": "não é uma taxa universal por m²; depende de tamanho, forma, vegetação, vento, horário e clima",
        "fonte": "https://doi.org/10.1038/s41598-024-67277-2",
        "fonte_nome": "Zhang et al. (2024), Scientific Reports",
    },
    "Alteração de Albedo": {
        "metrica": "temperatura do ar urbano ao meio-dia",
        "faixa": "redução média de 0,8 °C em semanas típicas e 1,2 °C em ondas de calor, em Guangzhou",
        "limite": "resultado de cenário urbano específico; não equivale diretamente à temperatura de uma superfície",
        "fonte": "https://doi.org/10.1021/acs.est.5b04886",
        "fonte_nome": "Wang et al. (2016), Environmental Science & Technology",
    },
    "Telhado Verde": {
        "metrica": "temperatura da superfície do telhado",
        "faixa": "diferenças frequentemente acima de 20 °C e, em alguns momentos, acima de 30 °C",
        "limite": "é temperatura de superfície, não temperatura do ar do bairro; depende de insolação e umidade",
        "fonte": "https://doi.org/10.1016/j.buildenv.2023.110842",
        "fonte_nome": "Hunter College study (2023), Building and Environment",
    },
    "Pavimento Permeável": {
        "metrica": "temperatura do pavimento em experimento de canyon urbano",
        "faixa": "2,1 °C mais quente de dia e 2,0 °C mais frio à noite que concreto impermeável, no estudo consultado",
        "limite": "o efeito depende fortemente de sombra, chuva, umidade e material; não deve ser generalizado",
        "fonte": "https://doi.org/10.1016/j.buildenv.2025.113948",
        "fonte_nome": "Outdoor experiment (2026), Building and Environment",
    },
    "Arborização de Rua": {
        "metrica": "temperatura do ar sob a copa em ruas",
        "faixa": "redução média observada de 0,5–2,2 °C em ruas de Atenas sob condições de calor",
        "limite": "depende da espécie, copa, sombra, vento, umidade, orientação da rua e horário",
        "fonte": "https://doi.org/10.1016/j.renene.2009.12.021",
        "fonte_nome": "Street shade trees study (2010), Renewable Energy",
    },
    "Corpo d'Água Urbano": {
        "metrica": "ilha de frescor do ar durante o dia",
        "faixa": "0,1–0,6 °C de resfriamento diurno; o estudo também observou 1,2–1,3 °C de aquecimento noturno",
        "limite": "não é uma intervenção de resfriamento garantido; umidade, vento e armazenamento de calor mudam o efeito",
        "fonte": "https://doi.org/10.1016/j.buildenv.2023.110860",
        "fonte_nome": "Urban lakes field study (2023), Building and Environment",
    },
    "Expansão Urbana": {
        "metrica": "tendência de aquecimento por mudança de cobertura",
        "faixa": "sem faixa universal isolada: o efeito depende da substituição de vegetação, materiais, geometria e ventilação",
        "limite": "não exibir como +1–4 °C relativo a área rural sem cenário local e série de referência",
        "fonte": "https://doi.org/10.1038/s41598-024-67277-2",
        "fonte_nome": "Zhang et al. (2024), Scientific Reports",
    },
}

# Informações educativas para cada tipo de intervenção
INFO_INTERVENCOES = {
    "Parque Urbano": {
        "descricao": "Áreas verdes que reduzem temperaturas através da sombra e evapotranspiração",
        "beneficios": ["Redução de temperatura", "Melhoria da qualidade do ar", "Bem-estar psicológico"],
        "exemplos": ["Parque Ibirapuera (SP)", "Central Park (NY)", "Hyde Park (Londres)"],
        "impacto_teorico": "A evidência publicada varia por local e mede principalmente diferença parque-entorno ou temperatura de superfície."
    },
    "Alteração de Albedo": {
        "descricao": "Aumento da refletividade de superfícies para reduzir absorção de calor",
        "beneficios": ["Redução do efeito de ilha de calor", "Menor consumo de energia", "Conforto térmico"],
        "exemplos": ["Telhados brancos", "Pavimentos claros", "Superfícies reflexivas"],
        "impacto_teorico": "A resposta do ar depende da escala da intervenção e das condições meteorológicas."
    },
    "Telhado Verde": {
        "descricao": "Coberturas vegetadas que isolam termicamente e absorvem calor",
        "beneficios": ["Isolamento térmico", "Redução de enxurradas", "Biodiversidade urbana"],
        "exemplos": ["Prefeitura de Chicago (EUA)", "Centro de Vancouver (Canadá)", "Edifícios em Cingapura"],
        "impacto_teorico": "Os maiores efeitos publicados são de superfície do telhado, não do ar do bairro."
    },
    "Pavimento Permeável": {
        "descricao": "Superfícies que permitem infiltração de água, reduzindo calor por evaporação",
        "beneficios": ["Drenagem sustentável", "Redução de enchentes", "Conforto térmico"],
        "exemplos": ["Calçadas permeáveis", "Estacionamentos drenantes", "Vias com infiltração"],
        "impacto_teorico": "O efeito térmico varia entre dia e noite e é muito sensível à umidade e à sombra."
    },
    "Arborização de Rua": {
        "descricao": "Árvores de rua criam sombra e podem reduzir a temperatura do ar próximo ao pedestre",
        "beneficios": ["Sombra", "Conforto térmico", "Biodiversidade urbana"],
        "exemplos": ["Calçadas arborizadas", "Canteiros viários", "Ruas escolares sombreadas"],
        "impacto_teorico": "A evidência é local e depende da espécie, da copa e das condições de vento."
    },
    "Corpo d'Água Urbano": {
        "descricao": "Lagos, canais e espelhos d'água trocam calor e umidade com o entorno",
        "beneficios": ["Resfriamento diurno potencial", "Paisagem e lazer", "Biodiversidade"],
        "exemplos": ["Lagos urbanos", "Canais abertos", "Áreas úmidas restauradas"],
        "impacto_teorico": "O efeito pode inverter à noite; é necessário avaliar temperatura, umidade e vento juntos."
    },
    "Expansão Urbana": {
        "descricao": "Aumento de áreas construídas que geralmente intensifica ilhas de calor",
        "beneficios": ["Expansão econômica", "Mais habitações", "Desenvolvimento"],
        "desvantagens": ["Aumento de temperatura", "Maior impermeabilização", "Perda de áreas verdes"],
        "impacto_teorico": "Não há uma faixa única publicável para toda expansão urbana; o cenário precisa de referência local."
    }
}

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
        st.session_state.tutorial_ativo = False

# --- Componentes de Interface Melhorados ---

def renderizar_header():
    '''Renderiza o cabeçalho com informações educativas.'''
    from utils.ui import renderizar_cabecalho_modulo
    renderizar_cabecalho_modulo(
        "Módulo Simular",
        "Simule intervenções urbanas e entenda seu impacto no microclima",
        icone="simulate"
    )

    # Botão agora fica abaixo do cabeçalho
    st.markdown("""
    <div class="learning-guide simulation-guide">
        <div class="learning-guide-step is-active"><span>1</span><div><strong>Escolha</strong><small>uma intervenção</small></div></div>
        <div class="learning-guide-connector"></div>
        <div class="learning-guide-step"><span>2</span><div><strong>Delimite</strong><small>uma área no mapa</small></div></div>
        <div class="learning-guide-connector"></div>
        <div class="learning-guide-step"><span>3</span><div><strong>Simule</strong><small>e interprete</small></div></div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("A sequência é cumulativa: primeiro descreva a mudança, depois informe onde ela acontece e por fim observe o efeito estimado.")
    st.warning(
        "**Cuidado científico:** os resultados são cenários didáticos baseados em ordens de grandeza da literatura. "
        "Eles não são uma previsão local, não substituem medição de campo e não devem ser publicados como resultado empírico da sua área. "
        "A unidade e a faixa observada mudam conforme a intervenção."
    )
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
                    evidencia = EVIDENCIA_INTERVENCOES[tipo_selecionado]
                    st.markdown(
                        f"**Evidência publicada ({evidencia['metrica']}):** {evidencia['faixa']}  \n"
                        f"**Limite de interpretação:** {evidencia['limite']}  \n"
                        f"[Fonte: {evidencia['fonte_nome']}]({evidencia['fonte']})"
                    )
        
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
            st.caption(f"💧 {parametros['permeabilidade']*100:.0f}% da água da chuva será infiltrada")

        elif tipo_selecionado == "Arborização de Rua":
            parametros["cobertura_copa"] = st.slider(
                "Cobertura da Copa", 0.0, 1.0, 0.6, 0.05,
                help="Proporção do trecho coberta pela copa das árvores."
            )
            st.caption(f"🌳 Aproximadamente {parametros['cobertura_copa']*100:.0f}% do trecho terá sombra de copa")

        elif tipo_selecionado == "Corpo d'Água Urbano":
            parametros["proporcao_agua"] = st.slider(
                "Proporção de Água", 0.0, 1.0, 0.5, 0.05,
                help="Proporção da área ocupada pelo corpo d'água no cenário."
            )
            st.caption("💧 O efeito é diurno e local; à noite, a umidade e o calor armazenado podem inverter a resposta")
        
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
        camada_calor = st.checkbox(
            "🌡️ Exemplo Ilustrativo de Pontos Quentes (dado fictício)", value=True,
            help="Estes três pontos são um exemplo didático fixo (região de São Paulo), "
                 "não uma medição real da cidade selecionada. Use para discutir onde "
                 "pontos quentes tipicamente aparecem (centro, vias, áreas comerciais)."
        )

    # Criar mapa base
    m = folium.Map(location=[-23.55, -46.63], zoom_start=12)

    # Adicionar camada de calor ilustrativa (dado fictício, não medição real)
    if camada_calor:
        # Pontos fixos de exemplo (região de São Paulo) — não são dados reais da cidade selecionada
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
                popup=f"Exemplo ilustrativo (dado fictício): área de calor intenso {point[2]*100:.0f}%"
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
                for interv in st.session_state.intervencoes:
                    intervencao_corrigida = {
                        'tipo': interv.get('tipo', 'Parque Urbano'),
                        'area_m2': interv.get('area_m2', 50000.0),
                        'parametros': interv.get('parametros', {})
                    }
                    intervencoes_validadas.append(intervencao_corrigida)
                
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
    
    with col2:
        if st.session_state.resultado_simulacao:
            resultado = st.session_state.resultado_simulacao
            delta = resultado['delta_total']
            
            # Métrica principal
            st.metric(
                "Cenário térmico combinado (modelo didático)",
                f"{delta:.2f} °C",
                delta=f"{delta:.2f} °C",
                help="Valor de um modelo didático simplificado. Não é uma medição, não é uma previsão local "
                     "e não deve ser comparado diretamente com estudos que medem LST, superfície de telhado "
                     "ou temperatura do ar em outras escalas. Consulte a evidência da intervenção."
            )
            st.caption("O número combina intervenções por uma regra simplificada. Para uso científico ou publicação, substitua-o por dados locais, método explícito e incerteza.")
            
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

    col1, col2 = st.columns(2)

    with col1:
        df_resumo = pd.DataFrame(st.session_state.resultado_simulacao['resumo_detalhado'])
        st.download_button(
            "📊 Baixar CSV",
            df_resumo.to_csv(index=False),
            "simulacao_clima_urbano.csv",
            "text/csv",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            "📋 Baixar JSON",
            json.dumps(st.session_state.resultado_simulacao, indent=2),
            "simulacao_clima_urbano.json",
            "application/json",
            use_container_width=True,
        )

# --- Função Principal Melhorada ---

def renderizar_pagina():
    '''Função principal que renderiza toda a página.'''
    inicializar_session_state()
    
    # Header educativo
    renderizar_header()
    renderizar_tutorial()
    
    # Indicadores rápidos — só depois que existir algo a mostrar, para não
    # recepcionar quem acabou de abrir o módulo com 4 métricas zeradas.
    if (st.session_state.intervencoes or st.session_state.poligonos_desenhados
            or st.session_state.cenarios or st.session_state.historico_simulacoes):
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["1. Intervenções", "2. Mapa", "3. Simular", "4. Resultados", "5. Histórico"])
    
    with tab1:
        st.info("Escolha uma intervenção e ajuste seus parâmetros. Cada alteração representa uma hipótese sobre o clima urbano.")
        if st.session_state.intervencoes:
            st.markdown("### 📋 Intervenções Configuradas")
            for i, intervencao in enumerate(st.session_state.intervencoes):
                renderizar_card_intervencao_melhorado(intervencao, i)
            st.markdown("---")
        
        renderizar_formulario_nova_intervencao_melhorado()
        
        st.markdown("---")
        renderizar_gerenciamento_cenarios()
    
    with tab2:
        st.info("Desenhe no mapa a área onde a intervenção será aplicada. O tamanho da área influencia o resultado.")
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
        st.info("Quando as etapas anteriores estiverem prontas, execute a simulação e observe o sinal da variação térmica.")
        renderizar_simulacao_e_resultados_melhorado()
    
    with tab4:
        st.info("Compare o impacto de cada intervenção e procure explicações para o resultado, não apenas o maior número.")
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
