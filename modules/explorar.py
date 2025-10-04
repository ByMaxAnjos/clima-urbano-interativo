# modules/explorar.py

import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib
import base64
from io import BytesIO
import tempfile
import rasterio
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
# Assumindo que utils.lcz4r está no caminho
from utils.lcz4r import lcz_get_map, process_lcz_map, enhance_lcz_data, lcz_plot_map, lcz_cal_area, lcz_area_analysis_report

# Configurar matplotlib para usar backend não-interativo
matplotlib.use('Agg')

# --- Funções de Gerenciamento de Sessão (Mantidas Robustas) ---

def init_session_state():
    """Inicializa o estado da sessão com valores padrão e validação."""
    current_version = "1.3.0" # Versão atualizada para refletir as melhorias
    
    if 'lcz_schema_version' not in st.session_state:
        st.session_state.lcz_schema_version = current_version
    elif st.session_state.lcz_schema_version != current_version:
        clear_lcz_session_data()
        st.session_state.lcz_schema_version = current_version
    
    session_defaults = {
        'lcz_data': None,
        'lcz_raster_data': None,
        'lcz_raster_profile': None,
        'lcz_city_name': None,
        'lcz_processing_success': False,
        'lcz_success_message': "",
        'lcz_error_message': "",
        'lcz_last_update': None,
        'lcz_data_size_mb': 0.0,
        'lcz_area_stats': None,
        'lcz_plot_data': None,
        'lcz_area_summary': None, # Adicionado
        'lcz_validation_result': None,
        'lcz_session_id': None
    }
    
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    if st.session_state.lcz_session_id is None:
        import uuid
        st.session_state.lcz_session_id = str(uuid.uuid4())[:8]
    
    validate_session_data()

def validate_session_data():
    """Valida a integridade dos dados na sessão e corrige inconsistências."""
    try:
        # Simplificação e foco na GeoDataFrame principal
        if st.session_state.lcz_data is not None:
            if not hasattr(st.session_state.lcz_data, 'geometry'):
                st.warning("⚠️ Dados LCZ corrompidos detectados. Limpando sessão...")
                clear_lcz_session_data()
                return
            
            import sys
            data_size = sys.getsizeof(st.session_state.lcz_data) / (1024 * 1024)
            st.session_state.lcz_data_size_mb = round(data_size, 2)
            
            # Checagem de dados antigos
            if st.session_state.lcz_last_update:
                from datetime import datetime, timedelta
                # Padronizar a conversão para datetime
                if isinstance(st.session_state.lcz_last_update, str):
                    last_update = datetime.fromisoformat(st.session_state.lcz_last_update)
                else:
                    last_update = st.session_state.lcz_last_update
                
                # Aviso de dados antigos
                if datetime.now() - last_update > timedelta(hours=1):
                    pass # Remoção do st.info para não poluir, a métrica de tempo no feedback já informa
        
        # Limite de memória (Aviso, não bloqueio)
        if st.session_state.lcz_data_size_mb > 100:
            st.warning("⚠️ Uso de memória alto detectado (> 100MB). Cidades muito grandes podem causar instabilidade.")
            
    except Exception as e:
        # Erro fatal na validação
        st.error(f"❌ Erro na validação da sessão: {str(e)}")
        clear_lcz_session_data()

def clear_lcz_session_data():
    """Limpa dados LCZ da sessão de forma segura e completa."""
    keys_to_clear = [
        'lcz_data', 'lcz_raster_data', 'lcz_raster_profile',
        'lcz_city_name', 'lcz_processing_success', 'lcz_success_message',
        'lcz_error_message', 'lcz_last_update', 'lcz_data_size_mb',
        'lcz_area_stats', 'lcz_plot_data', 'lcz_area_summary', 'lcz_validation_result'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None if key != 'lcz_processing_success' else False
    
    st.session_state.lcz_processing_success = False
    st.session_state.lcz_success_message = ""
    st.session_state.lcz_error_message = ""
    st.session_state.lcz_data_size_mb = 0.0
    
    import gc
    gc.collect()

def get_session_info():
    """Retorna informações sobre o estado atual da sessão."""
    # (Manter o corpo original da função)
    info = {
        'session_id': st.session_state.get('lcz_session_id', 'N/A'),
        'schema_version': st.session_state.get('lcz_schema_version', 'N/A'),
        'has_data': st.session_state.lcz_data is not None,
        'has_raster': st.session_state.lcz_raster_data is not None,
        'city_name': st.session_state.lcz_city_name or 'N/A',
        'data_size_mb': st.session_state.lcz_data_size_mb,
        'last_update': st.session_state.lcz_last_update,
        'processing_success': st.session_state.lcz_processing_success,
        'success_message': st.session_state.lcz_success_message,
        'error_message': st.session_state.lcz_error_message
    }
    
    return info

def update_session_timestamp():
    """Atualiza o timestamp da última modificação dos dados."""
    from datetime import datetime
    st.session_state.lcz_last_update = datetime.now().isoformat()

def save_lcz_data_to_session(data, profile, city_name, enhanced_gdf):
    """Salva dados LCZ na sessão de forma segura e organizada."""
    try:
        # Salvar dados principais
        st.session_state.lcz_raster_data = data
        st.session_state.lcz_raster_profile = profile
        st.session_state.lcz_city_name = city_name
        st.session_state.lcz_data = enhanced_gdf
        
        # Resetar dados de análise para que sejam recalculados com a nova GeoDataFrame
        st.session_state.lcz_area_stats = None
        st.session_state.lcz_plot_data = None
        st.session_state.lcz_area_summary = None
        
        # Atualizar status
        st.session_state.lcz_processing_success = True
        st.session_state.lcz_success_message = f"✅ Mapa LCZ gerado com sucesso para **{city_name}**!"
        st.session_state.lcz_error_message = ""
        
        # Atualizar timestamp
        update_session_timestamp()
        
        # Validar dados salvos
        validate_session_data()
        
        return True
        
    except Exception as e:
        st.session_state.lcz_error_message = f"Erro ao salvar dados na sessão: {str(e)}"
        st.session_state.lcz_processing_success = False
        return False

@st.cache_data
def get_logo_base64():
    """Retorna o logo LCZ4r em base64 com cache."""
    try:
        logo_path = "assets/lcz4r_logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return ""

# --- Funções de Renderização Aprimoradas ---

def renderizar_pagina():
    """
    Renderiza a página do módulo Explorar com foco didático,
    tratamento robusto de erros e monitoramento de sessão.
    """
    try:
        init_session_state()
        
        # 1. Cabeçalho
        renderizar_cabecalho_modulo()
        
        # 2. Feedback Persistente e Status
        renderizar_feedback_usuario()
        
        # 3. Conceitos Didáticos LCZ (Sempre visível)
        renderizar_conceitos_lcz()
        
        # 4. Gerador de Mapas
        st.markdown("---")
        st.markdown("## 🚀 Gerador de Mapas LCZ4r")
        try:
            renderizar_gerador_lcz()
        except Exception as e:
            st.error(f"❌ Erro no gerador LCZ: {str(e)}")
            with st.expander("🔧 Detalhes técnicos"):
                st.code(f"Erro: {type(e).__name__}\nDetalhes: {str(e)}")
        
        # 5. Seções de Análise (Condicionais)
        if st.session_state.lcz_data is not None and st.session_state.lcz_processing_success:
            renderizar_secoes_analise()
        else:
            renderizar_instrucoes_iniciais()
        
        # 6. Ajuda e Debug
        renderizar_secao_ajuda()
        
        if st.sidebar.checkbox("🔧 Modo Debug", help="Exibir informações técnicas da sessão"):
            renderizar_debug_sessao()
            
    except Exception as e:
        # Tratamento de erro global
        st.error("❌ **Erro crítico no módulo Explorar**")
        st.error(f"Detalhes: {str(e)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reiniciar Módulo", type="primary"):
                clear_lcz_session_data()
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar Sessão Completa"):
                for key in list(st.session_state.keys()):
                    if key.startswith('lcz_'):
                        del st.session_state[key]
                st.rerun()
        
        with st.expander("🔧 Informações Técnicas"):
            st.code(f"""
Tipo do erro: {type(e).__name__}
Detalhes: {str(e)}
Sessão ID: {st.session_state.get('lcz_session_id', 'N/A')}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
            """)

def renderizar_cabecalho_modulo():
    """Renderiza o cabeçalho visual do módulo com foco didático."""
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #007bff 0%, #00b4d8 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 1.5rem; text-align: center;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
            <img src="data:image/png;base64,{get_logo_base64()}" width="80" style="border-radius: 10px;">
            <div>
                <h1 style="color: white; margin: 0; font-size: 2.8rem; font-weight: 700;">
                    🗺️ Explorar o Clima Urbano
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1.3rem;">
                    Geração e Análise Interativa de Zonas Climáticas Locais (LCZ)
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
def renderizar_conceitos_lcz():
    """Nova seção didática para explicar o que são LCZ."""
    
    st.markdown("## 🧠 Conceitos Fundamentais: LCZ")
    
    with st.expander("O que são Zonas Climáticas Locais (LCZ)?", expanded=False):
        st.markdown("""
        As **Zonas Climáticas Locais (LCZ)** são um sistema de classificação padronizado globalmente,
        utilizado para caracterizar ambientes próximos à superfície terrestre com propriedades
        térmicas e físicas uniformes.
        
        Elas são cruciais para o estudo de **Ilhas de Calor Urbanas (ICU)**, pois cada classe LCZ
        possui um potencial diferente para reter ou dissipar calor.
        
        ### 📋 Classificação Resumida
        
        | Categoria | Classes (Ex.) | Características | Efeito Térmico Típico |
        | :---: | :---: | :---: | :---: |
        | **Urbana** | LCZ 1 (Densamente construída) | Prédios altos, superfícies impermeáveis | Retenção de calor, ICU Intensa |
        | | LCZ 6 (Baixa e Aberta) | Casas térreas, mais vegetação | Retenção moderada, ICU Moderada |
        | **Natural** | LCZ A (Árvores Densas) | Florestas, parques grandes | Resfriamento por evapotranspiração |
        | | LCZ D (Baixa Vegetação) | Campos, agricultura | Resfriamento moderado/aquecimento diurno |
        
        Use o mapa abaixo para ver a distribuição dessas classes na sua cidade!
        """)

def renderizar_feedback_usuario():
    """Renderiza feedback persistente e status da sessão para o usuário."""
    
    if st.session_state.lcz_processing_success and st.session_state.lcz_success_message:
        st.success(st.session_state.lcz_success_message)
    
    if st.session_state.lcz_error_message:
        st.error(f"❌ **Último erro:** {st.session_state.lcz_error_message}")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Limpar Erro", key="clear_error_btn", help="Remove a mensagem de erro"):
                st.session_state.lcz_error_message = ""
                st.rerun()
    
    # Status da sessão (compacto)
    if st.session_state.lcz_data is not None:
        session_info = get_session_info()
        st.markdown("---")
        st.markdown("#### 🚀 Status do Mapa Carregado")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🏙️ Cidade", 
                session_info['city_name'],
                help="Nome da cidade analisada"
            )
        
        with col2:
            st.metric(
                "💾 Memória", 
                f"{session_info['data_size_mb']:.1f} MB",
                help="Uso de memória da GeoDataFrame principal"
            )
        
        with col3:
            # Lógica de cálculo de tempo mantida
            time_str = "N/A"
            if session_info['last_update']:
                from datetime import datetime
                try:
                    if isinstance(session_info['last_update'], str):
                        last_update = datetime.fromisoformat(session_info['last_update'])
                    else:
                        last_update = session_info['last_update']
                    
                    time_diff = datetime.now() - last_update
                    if time_diff.total_seconds() < 60:
                        time_str = "Agora"
                    elif time_diff.total_seconds() < 3600:
                        time_str = f"{int(time_diff.total_seconds()//60)} min atrás"
                    else:
                        time_str = f"{int(time_diff.total_seconds()//3600)} h atrás"
                except:
                    pass
            
            st.metric("🕒 Última Geração", time_str, help="Última atualização dos dados LCZ")
        
        with col4:
            area_total = st.session_state.lcz_data['area_km2'].sum() if 'area_km2' in st.session_state.lcz_data.columns else 0
            st.metric("📏 Área Total", f"{area_total:.1f} km²", help="Área total coberta pelo mapa LCZ")
        st.markdown("---")

def renderizar_instrucoes_iniciais():
    """Renderiza instruções didáticas quando não há dados carregados."""
    
    st.info("ℹ️ **Pronto para começar?** Gere seu primeiro mapa LCZ para liberar as ferramentas de análise!")
    
    with st.expander("📖 Guia Rápido de Geração do Mapa LCZ", expanded=True):
        st.markdown("""
        ### 1. 🏙️ Selecione sua Cidade
        
        - **Busca Global:** Use o campo "Nome da Cidade" para buscar qualquer cidade do mundo.
        - **Dica:** Para resultados mais precisos, use o formato **"Cidade, País"** (Ex: *São Paulo, Brazil*).
        
        ### 2. ⏳ Gere o Mapa
        
        - **Clique em "🚀 Gerar Mapa LCZ":** O sistema irá geocodificar, baixar e processar os dados globais.
        - **Paciência:** O processamento pode levar de 2 a 5 minutos dependendo do tamanho da área e da conexão. Uma barra de progresso detalhada será exibida.
        
        ### 3. 📊 Explore e Analise
        
        Após o sucesso, novas seções aparecerão:
        - **Visualização:** Veja o mapa LCZ em formato científico.
        - **Análise de Área:** Explore gráficos de distribuição de área urbana vs. natural.
        - **Mapa Interativo (Folium):** Clique nos polígonos para ver as propriedades de cada LCZ e seu impacto no clima urbano.
        """)

def renderizar_secoes_analise():
    """Renderiza as seções de análise quando há dados disponíveis."""
    
    st.markdown("---")
    st.markdown(f"## 🔎 Análise LCZ para {st.session_state.lcz_city_name}")
    
    tab_matplot, tab_area, tab_folium = st.tabs(
        ["🎨 Visualização Científica", "📊 Análise de Área", "🗺️ Mapa Interativo"]
    )
    
    # 1. Visualização com Matplotlib (Científica)
    with tab_matplot:
        try:
            renderizar_secao_matplotlib()
        except Exception as e:
            st.error(f"❌ Erro na visualização Matplotlib. Detalhes: {str(e)}")

    # 2. Análise de Área (Didática/Estatística)
    with tab_area:
        try:
            renderizar_secao_calculo_area()
        except Exception as e:
            st.error(f"❌ Erro na análise de área. Detalhes: {str(e)}")
            st.session_state.lcz_area_stats = None
            st.session_state.lcz_plot_data = None
            st.session_state.lcz_area_summary = None
            if st.button("🔄 Recalcular Análise de Área", key="recal_area_fail"):
                st.rerun()
                
    # 3. Mapa Interativo Folium (Exploração)
    with tab_folium:
        try:
            renderizar_mapa_folium()
        except Exception as e:
            st.error(f"❌ Erro no mapa interativo. Detalhes: {str(e)}")
            if st.button("🔄 Recarregar Mapa Interativo", key="recal_folium_fail"):
                st.rerun()

def renderizar_secao_ajuda():
    """Renderiza seção de ajuda e instruções finais."""
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💡 Próximos Passos e Oportunidades")
        st.markdown("""
        O mapa LCZ é a base para diversas análises de clima urbano:
        1. **🌡️ Avalie a ICU:** Analise a área das LCZ mais críticas (LCZ 1-3) para entender a intensidade da Ilha de Calor.
        2. **🌳 Planeje Intervenções:** Identifique áreas com LCZ de baixa retenção (LCZ A, B, D) para expandir o resfriamento.
        3. **➡️ Módulos Avançados:** Use os dados gerados aqui nos módulos "Investigar" (para análises mais profundas) ou "Simular" (para testar planos de mitigação).
        """)
    
    with col2:
        st.markdown("### 🆘 Manutenção da Sessão")
        
        if st.button("🔄 Limpar Dados LCZ e Reiniciar", help="Limpa apenas os dados do mapa LCZ, mantendo a versão e ID da sessão.", use_container_width=True):
            clear_lcz_session_data()
            st.success("✅ Dados LCZ limpos e módulo reiniciado!")
            st.rerun()
        
        if st.button("📄 Gerar Relatório de Sessão", help="Mostra informações técnicas da sessão", use_container_width=True):
            info = get_session_info()
            st.json(info)
        
def renderizar_debug_sessao():
    """Renderiza informações de debug da sessão (apenas para desenvolvimento)."""
    # (Manter o corpo original da função)
    st.sidebar.markdown("### 🔧 Debug da Sessão")
    
    info = get_session_info()
    
    st.sidebar.json(info)
    
    if st.sidebar.button("🗑️ Limpar Sessão Debug"):
        clear_lcz_session_data()
        st.sidebar.success("Sessão limpa!")
    
    # Validação em tempo real
    if st.session_state.lcz_data is not None:
        from utils.lcz4r import validate_lcz_data
        validation = validate_lcz_data(st.session_state.lcz_data)
        
        st.sidebar.markdown("**Validação:**")
        if validation['valid']:
            st.sidebar.success("✅ Dados válidos")
        else:
            st.sidebar.error("❌ Dados inválidos")
        
        if validation['warnings']:
            st.sidebar.warning(f"⚠️ {len(validation['warnings'])} avisos")
        
        if validation['errors']:
            st.sidebar.error(f"❌ {len(validation['errors'])} erros")

def renderizar_gerador_lcz():
    """Renderiza a seção do gerador de mapas LCZ."""
    
    # Expandir automaticamente se não houver dados, para focar no primeiro passo
    expanded_state = not st.session_state.lcz_processing_success 
    if st.session_state.lcz_data is not None:
        expanded_state = False # Recolhe se já gerou um mapa
        
    with st.expander("🛠️ Configurações e Geração de Mapa LCZ", expanded=expanded_state):
        st.markdown("""
        A ferramenta **LCZ4r** utiliza dados de satélite de alta resolução para classificar o ambiente urbano.
        Gere um novo mapa ou use o mapa carregado na sessão:
        """)
        
        # Interface de entrada
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            cidade_nome = st.text_input(
                "🏙️ Nome da Cidade (Formato 'Cidade, País'):",
                placeholder="Ex: São Paulo, Brazil ou London, UK",
                help="Digite o nome completo da cidade para geocodificação",
                value=st.session_state.lcz_city_name or ""
            )
        
        with col2:
            gerar_mapa = st.button("🚀 Gerar Mapa LCZ", type="primary", use_container_width=True, key="gerar_mapa_btn")
        
        with col3:
            if st.session_state.lcz_data is not None:
                # Botão de limpar dados só aparece se houver dados
                if st.button("🗑️ Limpar Dados", use_container_width=True, key="limpar_dados_btn"):
                    clear_lcz_session_data()
                    st.rerun()
            else:
                st.empty() # Placeholder para manter o alinhamento
        
        # Processamento do mapa
        if gerar_mapa and cidade_nome:
            processar_mapa_lcz(cidade_nome)

def processar_mapa_lcz(cidade_nome):
    """
    Processa e gera o mapa LCZ para a cidade especificada com tratamento robusto de erros.
    """
    
    # Limpar dados anteriores (para garantir um novo processamento limpo)
    clear_lcz_session_data()
    
    # Barra de progresso e status
    progress_bar = st.progress(0)
    status_text = st.empty()
    error_container = st.empty()
    
    try:
        # Etapa 1: Validação inicial
        status_text.text("🔍 Validando entrada...")
        progress_bar.progress(10)
        
        if not cidade_nome or len(cidade_nome.strip()) < 2:
            raise ValueError("Nome da cidade deve ter pelo menos 2 caracteres")
        
        cidade_nome = cidade_nome.strip()
        
        # Etapa 2: Download dos dados LCZ
        status_text.text(f"🌍 Baixando dados LCZ para '{cidade_nome}'...")
        progress_bar.progress(45)
        
        # Importar exceções personalizadas (Assumindo que estão em utils.lcz4r)
        from utils.lcz4r import GeocodeError, DataProcessingError
        
        data, profile = lcz_get_map(cidade_nome)
        
        # Etapa 3: Processamento vetorial
        status_text.text("⚙️ Convertendo Raster para Polígonos (GeoDataFrame)...")
        progress_bar.progress(65)
        
        lcz_gdf = process_lcz_map(data, profile)
        
        # Etapa 4: Aprimoramento dos dados (Descrições, Áreas, etc.)
        status_text.text("✨ Calculando estatísticas e aprimorando atributos...")
        progress_bar.progress(80)
        
        enhanced_gdf = enhance_lcz_data(lcz_gdf)
        
        # Etapa 5: Validação e Salvamento
        status_text.text("💾 Validando e salvando dados na sessão...")
        progress_bar.progress(90)
        
        from utils.lcz4r import validate_lcz_data
        validation_result = validate_lcz_data(enhanced_gdf)
        
        if not validation_result['valid']:
            # Permite continuar, mas com aviso grave
            st.warning(f"⚠️ **Aviso de Validação Grave:** Dados LCZ gerados, mas com inconsistências. [Detalhes abaixo]")
            
        # Usar função aprimorada de salvamento
        success = save_lcz_data_to_session(data, profile, cidade_nome, enhanced_gdf)
        
        if not success:
            raise Exception("Falha ao salvar dados na sessão")
        
        st.session_state.lcz_validation_result = validation_result
        
        # Etapa 6: Finalização
        progress_bar.progress(100)
        status_text.text("✅ Processamento concluído! O mapa e as análises estão prontas para exploração.")
        
        # Exibir métricas de sucesso em linha
        gdf = st.session_state.lcz_data
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Classes Únicas", len(gdf['zcl_classe'].unique()))
        with col2:
            st.metric("Polígonos Totais", len(gdf))
        with col3:
            area_total = gdf['area_km2'].sum() if 'area_km2' in gdf.columns else 0
            st.metric("Área Coberta", f"{area_total:.1f} km²")
        with col4:
            st.metric("Tamanho na Memória", f"{st.session_state.lcz_data_size_mb:.1f} MB")
        
        if validation_result['warnings'] or validation_result['errors']:
            with st.expander("⚠️ Ver Avisos e Erros de Validação"):
                for warning in validation_result['warnings']:
                    st.warning(f"⚠️ {warning}")
                for error in validation_result['errors']:
                    st.error(f"❌ {error}")
        
        time.sleep(1)
        st.rerun()
        
    except GeocodeError as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"🌐 **Erro de Geocodificação:** Não foi possível localizar a cidade. {str(e)}")
        # (Manter dicas de GeocodeError)
        st.session_state.lcz_error_message = f"Geocodificação: {str(e)}"
        
    except DataProcessingError as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"📊 **Erro no Processamento:** Falha na conversão ou validação dos dados. {str(e)}")
        # (Manter dicas de DataProcessingError)
        st.session_state.lcz_error_message = f"Processamento: {str(e)}"
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"❌ **Erro Inesperado:** Ocorreu um erro crítico durante a geração. {str(e)}")
        # (Manter informações técnicas)
        st.session_state.lcz_error_message = f"Crítico: {type(e).__name__} - {str(e)}"
    
    finally:
        progress_bar.empty()
        status_text.empty()

def renderizar_secao_matplotlib():
    """Renderiza a seção de visualização com matplotlib (Científica)."""
    
    st.markdown("### 🗺️ Visualização para Publicação Científica")
    st.info("Utilize esta seção para gerar imagens estáticas em alta resolução, ideais para relatórios e artigos.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        titulo_personalizado = st.text_input(
            "🏷️ Título do Mapa:",
            placeholder=f"Zonas Climáticas Locais - {st.session_state.lcz_city_name or 'Cidade'}",
            value=st.session_state.lcz_city_name or ""
        )
    
    with col2:
        alta_resolucao = st.checkbox(
            "📸 Alta Resolução (300 DPI)",
            value=True,
            help="Ativar para melhor qualidade de impressão, mas pode levar mais tempo para gerar."
        )
    
    if st.button("🎨 Gerar/Atualizar Visualização", type="primary", use_container_width=True):
        gerar_visualizacao_matplotlib(titulo_personalizado, alta_resolucao)
        
    # Renderiza a última visualização gerada se estiver na sessão (opcional, requer salvar a figura em cache/sessão)
    # Para simplicidade, vamos garantir que o botão sempre gere a visualização.
    
    # Adicionar o download do GeoJSON aqui também
    if st.session_state.lcz_data is not None:
        geojson_data = st.session_state.lcz_data.to_json()
        st.download_button(
            label="🗺️ Baixar Dados GeoJSON (Vetorial)",
            data=geojson_data,
            file_name=f"lcz_data_{st.session_state.lcz_city_name or 'cidade'}.geojson",
            mime="application/json",
            help="Dados vetoriais completos do mapa LCZ, incluindo geometria e atributos aprimorados.",
            key="download_geojson_matplot"
        )

def gerar_visualizacao_matplotlib(titulo_personalizado=None, alta_resolucao=True):
    """Gera visualização usando matplotlib e lcz_plot_map."""
    
    with st.spinner("Gerando visualização de alta qualidade..."):
        try:
            data = st.session_state.lcz_raster_data
            profile = st.session_state.lcz_raster_profile
            
            if data is None or profile is None:
                st.error("❌ Dados raster não encontrados. Gere um mapa primeiro.")
                return
            
            figsize = (16, 12) if alta_resolucao else (12, 8)
            dpi = 300 if alta_resolucao else 150
            
            cidade = st.session_state.lcz_city_name or "Cidade"
            titulo = titulo_personalizado if titulo_personalizado else f"Mapa de Zonas Climáticas Locais - {cidade}"
            
            # Gerar visualização usando lcz_plot_map
            plt.figure(figsize=figsize, dpi=dpi)
            fig = lcz_plot_map(
                (data, profile),
                title=titulo,
                show_legend=True,
                isave=False
            )
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            
            st.markdown("#### 🖼️ Visualização Gerada")
            st.image(buf, caption=titulo, use_container_width=True)
            
            buf.seek(0)
            png_data = buf.getvalue()
            
            st.download_button(
                label="📸 Baixar Imagem PNG",
                data=png_data,
                file_name=f"lcz_map_{st.session_state.lcz_city_name or 'cidade'}_{'HR' if alta_resolucao else 'LR'}.png",
                mime="image/png",
                help="Imagem do mapa LCZ em formato PNG de alta qualidade",
                key="download_png_matplot_2" # Chave diferente para evitar conflito
            )
            
            plt.close(fig)
            st.success("✅ Visualização gerada com sucesso!")
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar visualização: {str(e)}")
            st.code(str(e))

def renderizar_secao_calculo_area():
    """
    Renderiza a seção de cálculo de área com análise avançada usando st.tabs para organização.
    """
    
    st.markdown("### 📈 Distribuição e Análise Estatística de Área")
    st.info("Esta análise quantifica a presença de cada classe LCZ na área total, sendo fundamental para o planejamento urbano e mitigação de ICU.")
    
    if st.session_state.lcz_data is None:
        st.warning("⚠️ Dados LCZ não encontrados na sessão.")
        return
    
    try:
        # 1. Pré-cálculo ou Recálculo se necessário
        if st.session_state.lcz_area_stats is None or st.session_state.lcz_plot_data is None:
            with st.spinner("Calculando estatísticas de área..."):
                result = lcz_cal_area(st.session_state.lcz_data)
                st.session_state.lcz_area_stats = result['stats']
                st.session_state.lcz_plot_data = result['plot_data']
                st.session_state.lcz_area_summary = result['summary']
        
        # Usar dados da sessão
        area_stats = st.session_state.lcz_area_stats
        plot_data = st.session_state.lcz_plot_data
        summary = st.session_state.lcz_area_summary
        
        # 2. Resumo e Controle
        col_resumo_1, col_resumo_2 = st.columns([3, 1])
        
        with col_resumo_1:
            st.markdown("#### Resumo da Cobertura")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Área", f"{summary['total_area_km2']:.1f} km²")
            with col2:
                st.metric("Classes Únicas", summary['num_classes'])
            with col3:
                st.metric("Polígonos", summary['num_total_poligonos'])
            with col4:
                st.metric("Dominante", summary['classe_dominante'], f"{summary['percentual_classe_dominante']:.1f}%")
        
        with col_resumo_2:
            st.markdown("#### Ações")
            if st.button("🔄 Recalcular Áreas", help="Força o recálculo das estatísticas", use_container_width=True):
                st.session_state.lcz_area_stats = None
                st.session_state.lcz_plot_data = None
                st.session_state.lcz_area_summary = None
                st.rerun()

        st.markdown("---")
        
        # 3. Tabs para organizar a análise
        tab_grafico, tab_tabela, tab_relatorio, tab_metrica = st.tabs(
            ["📈 Gráfico Interativo", "📋 Tabela Detalhada", "📄 Relatório TXT", "🔍 Métricas Avançadas"]
        )

        with tab_grafico:
            st.markdown("#### Configuração de Gráfico")
            col_g_1, col_g_2 = st.columns(2)
            with col_g_1:
                tipo_grafico = st.selectbox(
                    "📊 Tipo de Gráfico:",
                    ["bar", "pie", "donut", "treemap"],
                    format_func=lambda x: {"bar": "Barras (LCZ vs Área)", "pie": "Pizza (Percentual)", "donut": "Donut", "treemap": "Mapa de Árvore"}[x],
                    help="Escolha o formato de visualização"
                )
            with col_g_2:
                # Botão para gerar, forçar a regeneração do gráfico
                if st.button("🎨 Gerar Gráfico", key="gerar_grafico_area", type="primary", use_container_width=True):
                    # Força a geração e exibição (Plotly é exibido automaticamente)
                    pass
            
            # Gerar gráfico principal (Plotly)
            fig = criar_grafico_area_plotly(area_stats, plot_data, tipo_grafico)
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Download do Gráfico
                import plotly.io as pio
                col_d_1, col_d_2 = st.columns(2)
                with col_d_1:
                    img_bytes = pio.to_image(fig, format="png", width=1200, height=800, scale=2)
                    st.download_button(
                        label="📸 Baixar Gráfico PNG",
                        data=img_bytes,
                        file_name=f"lcz_area_{st.session_state.lcz_city_name}_{tipo_grafico}.png",
                        mime="image/png"
                    )
                with col_d_2:
                    html_data = fig.to_html(include_plotlyjs='cdn')
                    st.download_button(
                        label="🌐 Baixar Gráfico HTML (Interativo)",
                        data=html_data,
                        file_name=f"lcz_area_{st.session_state.lcz_city_name}_{tipo_grafico}.html",
                        mime="text/html"
                    )


        with tab_tabela:
            st.markdown("#### Tabela Estatística por Classe LCZ")
            st.info("Dados brutos e formatados para análise e exportação.")
            
            # Formatar tabela para melhor visualização
            area_stats_display = area_stats.copy()
            area_stats_display = area_stats_display.rename(columns={
                "zcl_classe": "Classe LCZ",
                "area_total_km2": "Área Total (km²)",
                "num_poligonos": "Polígonos",
                "area_media_km2": "Área Média (km²)",
                "percentual": "Percentual (%)"
            })
            
            st.dataframe(
                area_stats_display,
                use_container_width=True,
                column_config={
                    "Classe LCZ": "Classe LCZ",
                    "Área Total (km²)": st.column_config.NumberColumn(format="%.2f"),
                    "Polígonos": "Polígonos",
                    "Área Média (km²)": st.column_config.NumberColumn(format="%.3f"),
                    "Percentual (%)": st.column_config.NumberColumn(format="%.1f%%")
                }
            )
            
            # Download dos dados em CSV
            csv_data = area_stats.to_csv(index=False)
            st.download_button(
                label="📊 Baixar Dados CSV",
                data=csv_data,
                file_name=f"lcz_area_stats_{st.session_state.lcz_city_name or 'cidade'}.csv",
                mime="text/csv",
                help="Baixar estatísticas de área em formato CSV",
                key="download_csv_area"
            )

        with tab_relatorio:
            st.markdown("#### Relatório Detalhado de Análise LCZ")
            st.info("Um relatório em texto simples que resume a metodologia e os principais achados da análise.")
            
            # Gerar relatório
            relatorio = lcz_area_analysis_report(st.session_state.lcz_data, st.session_state.lcz_city_name)
            
            st.text_area("Conteúdo do Relatório:", value=relatorio, height=400)
            
            st.download_button(
                label="📄 Baixar Relatório TXT",
                data=relatorio,
                file_name=f"relatorio_lcz_area_{st.session_state.lcz_city_name or 'cidade'}.txt",
                mime="text/plain",
                help="Baixar relatório completo em formato texto",
                key="download_relatorio_area"
            )

        with tab_metrica:
            st.markdown("#### Métricas de Clima Urbano (LCZ)")
            st.info("Estas métricas ajudam a quantificar o nível de urbanização e fragmentação da área.")
            
            col_m_1, col_m_2 = st.columns(2)
            
            # Análise urbano vs natural
            urbano_mask = area_stats['zcl_classe'].str.contains('LCZ [1-9]|LCZ 10')
            natural_mask = area_stats['zcl_classe'].str.contains('LCZ [A-G]')
            
            area_urbana = area_stats[urbano_mask]['area_total_km2'].sum()
            area_natural = area_stats[natural_mask]['area_total_km2'].sum()
            
            percent_urbano = (area_urbana/summary['total_area_km2']*100) if summary['total_area_km2'] else 0
            percent_natural = (area_natural/summary['total_area_km2']*100) if summary['total_area_km2'] else 0
            
            with col_m_1:
                st.metric(
                    "Área Urbana (1-10)",
                    f"{area_urbana:.1f} km²",
                    f"{percent_urbano:.1f}%"
                )
                st.metric(
                    "Área Natural (A-G)",
                    f"{area_natural:.1f} km²",
                    f"{percent_natural:.1f}%"
                )
                
            with col_m_2:
                # Fragmentação
                fragmentacao = summary['num_total_poligonos'] / summary['total_area_km2'] if summary['total_area_km2'] else 0
                st.metric(
                    "Fragmentação (Pol/km²)",
                    f"{fragmentacao:.2f}",
                    help="Densidade de polígonos por km² (maior valor = mais fragmentado)"
                )
                
                # Classe mais fragmentada (manter lógica anterior)
                area_stats['fragmentacao'] = area_stats['num_poligonos'] / area_stats['area_total_km2'].replace(0, 1e-6) # Evita divisão por zero
                classe_fragmentada = area_stats.loc[area_stats['fragmentacao'].idxmax(), 'zcl_classe']
                
                st.metric(
                    "Classe Mais Fragmentada",
                    classe_fragmentada,
                    f"{area_stats['fragmentacao'].max():.2f} pol/km²"
                )

    except Exception as e:
        st.error(f"❌ Erro ao renderizar análise de área: {str(e)}")
        st.info("Limpeza dos dados de área recomendada para tentar novamente.")
        # Limpar dados corrompidos
        st.session_state.lcz_area_stats = None
        st.session_state.lcz_plot_data = None
        st.session_state.lcz_area_summary = None

def criar_grafico_area_plotly(area_stats, plot_data, tipo_grafico):
    """
    Cria gráfico Plotly baseado no tipo selecionado, com melhor estética.
    """
    
    try:
        cores_lcz = plot_data['cores_lcz'] # Cores LCZ completas do plot_data
        colors = [cores_lcz.get(classe, '#808080') for classe in area_stats['zcl_classe']]
        
        cidade_nome = st.session_state.lcz_city_name or 'Cidade'
        
        if tipo_grafico == "bar":
            fig = px.bar(
                area_stats, 
                x='zcl_classe', 
                y='area_total_km2',
                title=f"Distribuição de Área por Classe LCZ - {cidade_nome}",
                color='zcl_classe',
                color_discrete_map=cores_lcz,
                hover_data=['num_poligonos', 'area_media_km2', 'percentual'],
                labels={
                    'area_total_km2': 'Área Total (km²)',
                    'zcl_classe': 'Classe LCZ',
                    'num_poligonos': 'Nº Polígonos',
                    'area_media_km2': 'Área Média (km²)',
                    'percentual': 'Percentual (%)'
                }
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45, 
                              xaxis={'categoryorder': 'array', 'categoryarray': list(cores_lcz.keys())})
            
        elif tipo_grafico in ["pie", "donut"]:
            hole_val = 0.4 if tipo_grafico == "donut" else 0
            
            fig = go.Figure(data=[go.Pie(
                labels=area_stats['zcl_classe'],
                values=area_stats['area_total_km2'],
                hole=hole_val,
                marker_colors=colors,
                hovertemplate='<b>%{label}</b><br>' +
                             'Área: %{value:.2f} km²<br>' +
                             'Percentual: %{percent}<br>' +
                             'Nº Polígonos: %{customdata[0]}<extra></extra>',
                customdata=area_stats[['num_poligonos']]
            )])
            
            fig.update_layout(
                title=f"Distribuição Percentual de Área LCZ ({tipo_grafico.capitalize()}) - {cidade_nome}",
                annotations=[dict(text='LCZ', x=0.5, y=0.5, font_size=20, showarrow=False)] if tipo_grafico == "donut" else []
            )
            
        elif tipo_grafico == "treemap":
            fig = px.treemap(
                area_stats,
                path=['zcl_classe'],
                values='area_total_km2',
                title=f"Mapa de Árvore - Distribuição LCZ - {cidade_nome}",
                color='zcl_classe',
                color_discrete_map=cores_lcz,
                hover_data=['num_poligonos', 'percentual']
            )
        
        # Configurações gerais
        fig.update_layout(
            font=dict(size=12, family="Arial"),
            title_font_size=18,
            height=600,
            template="plotly_white" # Estilo mais limpo
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Erro ao criar gráfico: {str(e)}")
        return None

# Funções obsoletas removidas (gerar_grafico_area_plotly)
# Código de geração de gráfico limpo para usar a nova função criar_grafico_area_plotly

def renderizar_mapa_folium():
    """Renderiza o mapa interativo com Folium usando dados da sessão (Foco Didático no Popup)."""
    
    st.markdown("### 🖱️ Mapa Interativo LCZ e Impacto Urbano")
    st.info("Explore a distribuição espacial das LCZ. Clique em cada polígono para ver suas propriedades detalhadas e o impacto climático.")
    
    try:
        gdf_lcz = st.session_state.lcz_data
        
        if gdf_lcz is None or gdf_lcz.empty:
            st.warning("⚠️ Dados LCZ não encontrados na sessão.")
            return
        
        # Calcular centro e bounds
        bounds = gdf_lcz.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='CartoDB Positron' # Tile mais neutro para destacar o LCZ
        )
        
        # Cores LCZ padrão (aqui estamos usando a paleta de lcz4r)
        cores_lcz = {
            'LCZ 1':  '#910613',  'LCZ 2':  '#D9081C',  'LCZ 3':  '#FF0A22',  'LCZ 4':  '#C54F1E',
            'LCZ 5':  '#FF6628',  'LCZ 6':  '#FF985E',  'LCZ 7':  '#FDED3F',  'LCZ 8':  '#BBBBBB',
            'LCZ 9':  '#FFCBAB',  'LCZ 10': '#565656',  'LCZ A':  '#006A18',  'LCZ B':  '#00A926',
            'LCZ C':  '#628432',  'LCZ D':  '#B5DA7F',  'LCZ E':  '#000000',  'LCZ F':  '#FCF7B1',
            'LCZ G':  '#656BFA'
        }
        
        # Adicionar camada GeoJSON
        # Nota: O uso de iterrows pode ser lento para muitos polígonos. Para otimização, 
        # usar folium.GeoJson(gdf_lcz.to_json(), ...) é melhor, mas o popup dinâmico requer a iteração.
        
        # Tentar usar folium.GeoJson para a camada, e passar a função style/popup
        def style_function(feature):
            classe = feature['properties'].get('zcl_classe', 'Desconhecida')
            cor = cores_lcz.get(classe, '#808080')
            return {
                'fillColor': cor,
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7,
                'opacity': 0.8
            }
            
        def highlight_function(feature):
            return {
                'weight': 3,
                'color': '#ff0000',
                'fillOpacity': 0.9
            }

        # Cria a camada GeoJson com Tooltip e Popup aprimorados
        folium.GeoJson(
            gdf_lcz.to_json(),
            name=f"LCZ - {st.session_state.lcz_city_name}",
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['zcl_classe', 'area_km2', 'descricao', 'efeito_temp'],
                aliases=['Classe LCZ:', 'Área (km²):', 'Descrição:', 'Efeito Térmico:'],
                localize=True,
                sticky=False,
                labels=True,
                style=("background-color: white; color: black; font-family: sans-serif; font-size: 14px; padding: 10px;")
            ),
            popup=folium.GeoJsonPopup(
                fields=['zcl_classe', 'area_km2', 'descricao', 'efeito_temp', 'ilha_calor', 'intervencao'],
                aliases=['Classe:', 'Área (km²):', 'Descrição:', 'Efeito Térmico:', 'ICU:', 'Intervenção:'],
                localize=True,
                labels=True,
                style="background-color: white;",
                max_width=350
            )
        ).add_to(m)

        # Adicionar Legenda (Necessário implementar a legenda LCZ4r no folium, mas vamos simplificar aqui)
        # O folium não tem uma maneira fácil de adicionar a legenda LCZ4r. Deixar como melhoria.
        folium.LayerControl().add_to(m)
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Exibir mapa
        st_folium(m, width="100%", height=700, feature_group_to_add=m._children.get('geojson')) # O nome 'geojson' pode variar
        
        # Estatísticas do mapa (Simplificadas, já estão em outras seções)
        with st.expander("ℹ️ Informações sobre os Atributos do Mapa"):
            st.markdown("""
            Os polígonos no mapa contêm atributos aprimorados:
            - **zcl_classe:** O código da LCZ (ex: LCZ 2).
            - **area_km2:** Área total do polígono em quilômetros quadrados.
            - **descricao:** Descrição detalhada da classe LCZ.
            - **efeito_temp:** O efeito climático típico desta LCZ.
            - **ilha_calor:** O potencial de contribuição para a Ilha de Calor Urbana (ICU).
            - **intervencao:** Sugestão de intervenção para mitigação de ICU.
            """)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar mapa interativo: {str(e)}")
        st.info("💡 Verifique se a GeoDataFrame contém os atributos esperados ('zcl_classe', 'area_km2', etc.) ou tente limpar a sessão.")

# --- Fim das Funções de Renderização ---