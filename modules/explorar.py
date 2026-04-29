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
import streamlit as st
import pandas as pd
import geopandas as gpd
from utils.lcz4r import lcz_get_map, process_lcz_map, enhance_lcz_data, lcz_plot_map
from utils.ui_components_modern import design4_glassmorphism_premium

# Configurar matplotlib para usar backend não-interativo
matplotlib.use('Agg')

def init_session_state():
    """
    Inicializa o estado da sessão com valores padrão e validação.
    Implementa controle de versão e limpeza automática de dados antigos.
    """
    # Versão do esquema de dados para controle de compatibilidade
    current_version = "1.2.0"
    
    # Verificar e atualizar versão do esquema
    if 'lcz_schema_version' not in st.session_state:
        st.session_state.lcz_schema_version = current_version
    elif st.session_state.lcz_schema_version != current_version:
        # Limpar dados antigos se a versão mudou
        clear_lcz_session_data()
        st.session_state.lcz_schema_version = current_version
    
    # Inicializar dados principais
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
        'lcz_validation_result': None,
        'lcz_session_id': None
    }
    
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Gerar ID único da sessão se não existir
    if st.session_state.lcz_session_id is None:
        import uuid
        st.session_state.lcz_session_id = str(uuid.uuid4())[:8]
    
    # Verificar integridade dos dados existentes
    validate_session_data()


def validate_session_data():
    """
    Valida a integridade dos dados na sessão e corrige inconsistências.
    """
    try:
        # Verificar consistência entre dados vetoriais e raster
        if st.session_state.lcz_data is not None:
            if not hasattr(st.session_state.lcz_data, 'geometry'):
                st.warning("⚠️ Dados LCZ corrompidos detectados. Limpando sessão...")
                clear_lcz_session_data()
                return
            
            # Calcular tamanho dos dados em memória
            import sys
            data_size = sys.getsizeof(st.session_state.lcz_data) / (1024 * 1024)
            st.session_state.lcz_data_size_mb = round(data_size, 2)
            
            # Verificar se os dados são muito antigos (mais de 1 hora)
            if st.session_state.lcz_last_update:
                from datetime import datetime, timedelta
                if isinstance(st.session_state.lcz_last_update, str):
                    last_update = datetime.fromisoformat(st.session_state.lcz_last_update)
                else:
                    last_update = st.session_state.lcz_last_update
                
                if datetime.now() - last_update > timedelta(hours=1):
                    st.info("ℹ️ Dados LCZ antigos detectados. Considere gerar um novo mapa.")
        
        # Verificar limite de memória (máximo 100MB por sessão)
        if st.session_state.lcz_data_size_mb > 100:
            st.warning("⚠️ Uso de memória alto detectado. Considere limpar os dados da sessão.")
            
    except Exception as e:
        st.error(f"❌ Erro na validação da sessão: {str(e)}")
        clear_lcz_session_data()


def clear_lcz_session_data():
    """
    Limpa dados LCZ da sessão de forma segura e completa.
    Mantém configurações importantes e libera memória.
    """
    # Lista de chaves a serem limpas
    keys_to_clear = [
        'lcz_data', 'lcz_raster_data', 'lcz_raster_profile',
        'lcz_city_name', 'lcz_processing_success', 'lcz_success_message',
        'lcz_error_message', 'lcz_last_update', 'lcz_data_size_mb',
        'lcz_area_stats', 'lcz_plot_data', 'lcz_validation_result'
    ]
    
    # Limpar dados específicos
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None if key != 'lcz_processing_success' else False
    
    # Resetar valores específicos
    st.session_state.lcz_processing_success = False
    st.session_state.lcz_success_message = ""
    st.session_state.lcz_error_message = ""
    st.session_state.lcz_data_size_mb = 0.0
    
    # Forçar coleta de lixo para liberar memória
    import gc
    gc.collect()


def get_session_info():
    """
    Retorna informações sobre o estado atual da sessão.
    
    Returns
    -------
    dict
        Informações da sessão incluindo status, tamanhos e timestamps
    """
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
    """
    Atualiza o timestamp da última modificação dos dados.
    """
    from datetime import datetime
    st.session_state.lcz_last_update = datetime.now().isoformat()


def save_lcz_data_to_session(data, profile, city_name, enhanced_gdf):
    """
    Salva dados LCZ na sessão de forma segura e organizada.
    
    Parameters
    ----------
    data : numpy.ndarray
        Dados raster LCZ
    profile : dict
        Perfil do raster
    city_name : str
        Nome da cidade
    enhanced_gdf : geopandas.GeoDataFrame
        Dados vetoriais aprimorados
    """
    try:
        # Salvar dados principais
        st.session_state.lcz_raster_data = data
        st.session_state.lcz_raster_profile = profile
        st.session_state.lcz_city_name = city_name
        st.session_state.lcz_data = enhanced_gdf
        
        # Atualizar status
        st.session_state.lcz_processing_success = True
        st.session_state.lcz_success_message = f"✅ Mapa LCZ gerado com sucesso para {city_name}!"
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

def renderizar_pagina():
    """
    Renderiza a página do módulo Explorar com tratamento robusto de erros,
    feedback do usuário e monitoramento de sessão.
    """
    
    try:
        # Inicializar estado da sessão com tratamento de erro
        init_session_state()
        
        # Renderizar cabeçalho do módulo
        renderizar_cabecalho_modulo()
        
        # Exibir status da sessão e feedback do usuário
        renderizar_feedback_usuario()
        
        # Seção principal: Gerador de mapas LCZ4r
        st.markdown("## 🚀 Gerador de Mapas LCZ4r")
        
        try:
            renderizar_gerador_lcz()
        except Exception as e:
            st.error(f"❌ Erro no gerador LCZ: {str(e)}")
            with st.expander("🔧 Detalhes técnicos"):
                st.code(f"Erro: {type(e).__name__}\nDetalhes: {str(e)}")
        
        # Seções condicionais baseadas na disponibilidade de dados
        if st.session_state.lcz_data is not None:
            renderizar_secoes_analise()
        else:
            renderizar_instrucoes_iniciais()
        
        # Seção de informações e ajuda
        renderizar_secao_ajuda()
        
        # Monitoramento de sessão (apenas para debug, se necessário)
        if st.sidebar.checkbox("🔧 Modo Debug", help="Exibir informações técnicas da sessão"):
            renderizar_debug_sessao()
            
    except Exception as e:
        # Tratamento de erro global para a página
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
    """Renderiza o cabeçalho visual do módulo."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
            <img src="data:image/png;base64,{}" width="80" style="border-radius: 10px;">
            <div>
                <h1 style="color: white; margin: 0; font-size: 2.5rem;">🌍 Módulo Explorar</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1.2rem;">
                    Gere e visualize mapas de Zonas Climáticas Locais (LCZ) interativos
                </p>
            </div>
        </div>
    </div>
    """.format(get_logo_base64()), unsafe_allow_html=True)


def renderizar_feedback_usuario():
    """Renderiza feedback persistente e status da sessão para o usuário."""
    
    # Mensagens de sucesso persistentes
    if st.session_state.lcz_processing_success and st.session_state.lcz_success_message:
        st.success(st.session_state.lcz_success_message)
    
    # Mensagens de erro persistentes
    if st.session_state.lcz_error_message:
        st.error(f"❌ **Último erro:** {st.session_state.lcz_error_message}")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Limpar Erro", help="Remove a mensagem de erro"):
                st.session_state.lcz_error_message = ""
                st.rerun()
    
    # Status da sessão (compacto)
    if st.session_state.lcz_data is not None:
        session_info = get_session_info()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Status", 
                "Dados Carregados",
                help=f"Cidade: {session_info['city_name']}"
            )
        
        with col2:
            st.metric(
                "💾 Memória", 
                f"{session_info['data_size_mb']:.1f} MB",
                help="Uso de memória da sessão"
            )
        
        with col3:
            if session_info['last_update']:
                from datetime import datetime
                try:
                    if isinstance(session_info['last_update'], str):
                        last_update = datetime.fromisoformat(session_info['last_update'])
                    else:
                        last_update = session_info['last_update']
                    
                    time_diff = datetime.now() - last_update
                    if time_diff.seconds < 60:
                        time_str = "Agora"
                    elif time_diff.seconds < 3600:
                        time_str = f"{time_diff.seconds//60}min"
                    else:
                        time_str = f"{time_diff.seconds//3600}h"
                    
                    st.metric("🕒 Atualizado", time_str, help="Última atualização dos dados")
                except:
                    st.metric("🕒 Atualizado", "N/A")
            else:
                st.metric("🕒 Atualizado", "N/A")
        
        with col4:
            st.metric(
                "🆔 Sessão", 
                session_info['session_id'],
                help="ID único da sessão atual"
            )


def renderizar_secoes_analise():
    """Renderiza as seções de análise quando há dados disponíveis."""
    
    try:
        # 1. Visualização com matplotlib
        st.markdown("---")
        st.markdown("## 🎨 Visualizar LCZ Map")
        
        try:
            renderizar_secao_matplotlib()
        except Exception as e:
            st.error(f"❌ Erro na visualização matplotlib: {str(e)}")
            if st.button("🔄 Tentar Novamente - Matplotlib"):
                st.rerun()
        
        # 2. Análise de área
        st.markdown("---")
        st.markdown("## 📊 Análise de Área por Classe LCZ")
        
        try:
            renderizar_secao_calculo_area()
        except Exception as e:
            st.error(f"❌ Erro na análise de área: {str(e)}")
            # Limpar dados corrompidos de área
            st.session_state.lcz_area_stats = None
            st.session_state.lcz_plot_data = None
            st.session_state.lcz_area_summary = None
            
            if st.button("🔄 Recalcular Análise de Área"):
                st.rerun()
        
        # 3. Mapa interativo Folium
        st.markdown("---")
        st.markdown("## 🗺️ Mapa Interativo")
        
        try:
            renderizar_mapa_folium()
        except Exception as e:
            st.error(f"❌ Erro no mapa interativo: {str(e)}")
            if st.button("🔄 Recarregar Mapa Interativo"):
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Erro nas seções de análise: {str(e)}")


def renderizar_instrucoes_iniciais():
    """Renderiza seção inicial com Design 4 moderno."""

    # Hero modernizado com Design 4 — Premium Glassmorphism
    st.markdown(
        design4_glassmorphism_premium(
            titulo="Explorar Zonas Climáticas Locais",
            subtitulo="Entenda o padrão climático em sua cidade através de 17 classes de morfologia urbana",
            badge_text="🌍 Análise Climática",
            cta_text="Gerar Meu Primeiro Mapa →"
        ),
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Guia rápido de uso (colapsado)
    with st.expander("📖 Guia Rápido — Como Começar", expanded=False):
        st.markdown("""
        ### 🚀 Primeiros Passos

        1. **Digite o nome de uma cidade** no campo acima (ex: "São Paulo, Brazil")
        2. **Clique em "Gerar Mapa LCZ"** para processar os dados
        3. **Aguarde o processamento** (2-5 minutos, depende do tamanho)
        4. **Explore as visualizações** que aparecerão automaticamente

        ### 💡 Dicas Importantes

        - **Nomes de cidades:** Use nomes completos com país: "São Paulo, Brazil", "New York, USA"
        - **Conexão:** Certifique-se de ter internet estável (dados baixados do Zenodo)
        - **Paciência:** Processamento geoespacial é intensivo em CPU
        - **Memória:** Cidades muito grandes (>10M habitantes) podem usar mais RAM

        ### 🌍 Cidades Testadas com Sucesso

        - São Paulo, Brazil
        - Rio de Janeiro, Brazil
        - New York, USA
        - London, UK
        - Tokyo, Japan
        """)


def renderizar_secao_ajuda():
    """Renderiza seção de ajuda e instruções finais."""
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 💡 Como Usar o Módulo Explorar
        
        1. **🚀 Gere um Mapa:** Use o gerador LCZ4r para criar um mapa para sua cidade de interesse
        2. **🎨 Visualize:** Veja o mapa em formato científico com matplotlib
        3. **📊 Analise:** Explore a distribuição de áreas por classe LCZ com gráficos interativos
        4. **🗺️ Explore:** Interaja com o mapa usando a interface Folium
        5. **➡️ Próximo passo:** Vá para "Investigar" para análises detalhadas ou "Simular" para testar intervenções
        """)
    
    with col2:
        st.markdown("### 🆘 Precisa de Ajuda?")
        
        if st.button("🔄 Reiniciar Módulo", help="Limpa todos os dados e reinicia"):
            clear_lcz_session_data()
            st.success("✅ Módulo reiniciado!")
            st.rerun()
        
        if st.button("📊 Ver Status da Sessão", help="Mostra informações técnicas"):
            info = get_session_info()
            st.json(info)
        
        with st.expander("❓ FAQ"):
            st.markdown("""
            **P: O processamento está muito lento?**
            R: Isso é normal. Aguarde alguns minutos.
            
            **P: Erro de conexão?**
            R: Verifique sua internet e tente novamente.
            
            **P: Cidade não encontrada?**
            R: Tente usar o nome completo com país.
            
            **P: Como limpar os dados?**
            R: Use o botão "Limpar Dados" ou "Reiniciar Módulo".
            """)


def renderizar_debug_sessao():
    """Renderiza informações de debug da sessão (apenas para desenvolvimento)."""
    
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
    
    with st.expander("🔧 Gerar Novo Mapa LCZ", expanded=not st.session_state.lcz_processing_success):
        st.markdown("""
        **LCZ4r** é uma ferramenta avançada para processamento de Zonas Climáticas Locais que permite:
        
        - 🌍 Gerar mapas LCZ para qualquer cidade do mundo
        - 📊 Processar dados de alta resolução automaticamente  
        - 🗺️ Visualizar resultados de forma interativa
        - 💾 Salvar dados na sessão para análises futuras
        """)
        
        # Interface de entrada
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            cidade_nome = st.text_input(
                "🏙️ Nome da Cidade:",
                placeholder="Ex: São Paulo, New York, London, Tokyo...",
                help="Digite o nome da cidade para gerar o mapa LCZ",
                value=st.session_state.lcz_city_name or ""
            )
        
        with col2:
            gerar_mapa = st.button("🚀 Gerar Mapa LCZ", type="primary", use_container_width=True)
        
        with col3:
            if st.button("🗑️ Limpar Dados", use_container_width=True):
                clear_lcz_session_data()
                st.rerun()
        
        # Processamento do mapa
        if gerar_mapa and cidade_nome:
            processar_mapa_lcz(cidade_nome)

def processar_mapa_lcz(cidade_nome):
    """
    Processa e gera o mapa LCZ para a cidade especificada com tratamento robusto de erros.
    Utiliza o sistema aprimorado de gerenciamento de sessão.
    """
    
    # Limpar dados anteriores
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
        
        # Etapa 2: Geocodificação
        status_text.text("📡 Conectando ao serviço de geocodificação...")
        progress_bar.progress(25)
        
        # Etapa 3: Download dos dados LCZ
        status_text.text("🌍 Baixando dados LCZ globais...")
        progress_bar.progress(45)
        
        # Importar exceções personalizadas
        from utils.lcz4r import GeocodeError, DataProcessingError
        
        data, profile = lcz_get_map(cidade_nome)
        
        # Etapa 4: Processamento vetorial
        status_text.text("⚙️ Processando dados LCZ...")
        progress_bar.progress(65)
        
        lcz_gdf = process_lcz_map(data, profile)
        
        # Etapa 5: Aprimoramento dos dados
        status_text.text("✨ Aprimorando dados...")
        progress_bar.progress(80)
        
        enhanced_gdf = enhance_lcz_data(lcz_gdf)
        
        # Etapa 6: Validação dos dados processados
        status_text.text("🔍 Validando dados processados...")
        progress_bar.progress(90)
        
        from utils.lcz4r import validate_lcz_data
        validation_result = validate_lcz_data(enhanced_gdf)
        
        if not validation_result['valid']:
            raise DataProcessingError(f"Dados inválidos: {'; '.join(validation_result['errors'])}")
        
        # Etapa 7: Salvamento na sessão
        status_text.text("💾 Salvando na sessão...")
        progress_bar.progress(95)
        
        # Usar função aprimorada de salvamento
        success = save_lcz_data_to_session(data, profile, cidade_nome, enhanced_gdf)
        
        if not success:
            raise Exception("Falha ao salvar dados na sessão")
        
        # Salvar resultado da validação
        st.session_state.lcz_validation_result = validation_result
        
        # Etapa 8: Finalização
        progress_bar.progress(100)
        status_text.text("✅ Processamento concluído!")
        
        # Exibir métricas de sucesso
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Classes LCZ", len(enhanced_gdf['zcl_classe'].unique()))
        with col2:
            st.metric("Polígonos", len(enhanced_gdf))
        with col3:
            area_total = enhanced_gdf['area_km2'].sum() if 'area_km2' in enhanced_gdf.columns else 0
            st.metric("Área Total", f"{area_total:.1f} km²")
        with col4:
            st.metric("Tamanho", f"{st.session_state.lcz_data_size_mb:.1f} MB")
        
        # Exibir avisos de validação se houver
        if validation_result['warnings']:
            with st.expander("⚠️ Avisos de Validação", expanded=False):
                for warning in validation_result['warnings']:
                    st.warning(f"⚠️ {warning}")
        
        # Aguardar um pouco para mostrar o progresso completo
        time.sleep(1)
        
        # Forçar rerun para atualizar as seções
        st.rerun()
        
    except GeocodeError as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"🌐 **Erro de Geocodificação:** {str(e)}")
        
        with error_container.expander("💡 Dicas para resolver problemas de geocodificação"):
            st.markdown("""
            **Sugestões para melhorar a busca:**
            - Tente usar o nome completo da cidade: "São Paulo, Brazil"
            - Use nomes em inglês quando possível: "Rio de Janeiro, Brazil"
            - Verifique a ortografia do nome da cidade
            - Tente variações do nome (ex: "NYC" → "New York City")
            - Para cidades pequenas, adicione o estado/província
            """)
        
        st.session_state.lcz_error_message = str(e)
        
    except DataProcessingError as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"📊 **Erro no Processamento:** {str(e)}")
        
        with error_container.expander("💡 Possíveis soluções"):
            st.markdown("""
            **Problemas comuns e soluções:**
            - **Área fora de cobertura:** Verifique se a cidade está na cobertura global do LCZ
            - **Dados insuficientes:** Tente uma área metropolitana maior
            - **Nome incorreto:** Confirme se o nome da cidade está correto
            - **Região muito pequena:** LCZ funciona melhor com áreas urbanas maiores
            """)
        
        st.session_state.lcz_error_message = str(e)
        
    except ConnectionError as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"🌐 **Erro de Conexão:** {str(e)}")
        
        with error_container.expander("💡 Dicas para resolver problemas de conexão"):
            st.markdown("""
            **Soluções para problemas de rede:**
            - Verifique sua conexão com a internet
            - Tente novamente em alguns minutos
            - Verifique se não há firewall bloqueando o acesso
            - Se o problema persistir, o serviço pode estar temporariamente indisponível
            """)
        
        st.session_state.lcz_error_message = str(e)
        
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        error_container.error(f"❌ **Erro Inesperado:** {str(e)}")
        
        with error_container.expander("🔧 Informações técnicas"):
            st.code(f"Tipo do erro: {type(e).__name__}\nDetalhes: {str(e)}")
            st.markdown("""
            **Se o problema persistir:**
            - Tente limpar os dados da sessão e gerar novamente
            - Verifique se o nome da cidade está correto
            - Tente uma cidade diferente para testar o sistema
            """)
        
        st.session_state.lcz_error_message = str(e)
    
    finally:
        # Sempre limpar elementos temporários
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()

def renderizar_secao_matplotlib():
    """Renderiza a seção de visualização com matplotlib."""
    
    st.markdown("### ⚙️ Configurações de Visualização")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        titulo_personalizado = st.text_input(
            "🏷️ Título do Mapa (opcional):",
            placeholder=f"Ex: Zonas Climáticas Locais - {st.session_state.lcz_city_name or 'Cidade'}",
            help="Deixe em branco para usar o título padrão"
        )
    
    with col2:
        alta_resolucao = st.checkbox(
            "📸 Alta Resolução",
            value=True,
            help="Gera imagem em 300 DPI para melhor qualidade"
        )
    
    # Botão para gerar visualização
    if st.button("🎨 Gerar Visualização", type="primary", use_container_width=True):
        gerar_visualizacao_matplotlib(titulo_personalizado, alta_resolucao)

def gerar_visualizacao_matplotlib(titulo_personalizado=None, alta_resolucao=True):
    """Gera visualização usando matplotlib e lcz_plot_map."""
    
    with st.spinner("Gerando visualização de alta qualidade..."):
        try:
            # Usar dados da sessão
            data = st.session_state.lcz_raster_data
            profile = st.session_state.lcz_raster_profile
            
            if data is None or profile is None:
                st.error("❌ Dados raster não encontrados na sessão. Gere um mapa primeiro.")
                return
            
            # Configurar parâmetros
            figsize = (16, 12) if alta_resolucao else (12, 8)
            dpi = 300 if alta_resolucao else 150
            
            # Configurar título
            cidade = st.session_state.lcz_city_name or "Cidade"
            titulo = titulo_personalizado if titulo_personalizado else f"Mapa de Zonas Climáticas Locais - {cidade}"
            
            # Gerar visualização usando lcz_plot_map
            plt.figure(figsize=figsize, dpi=dpi)
            fig = lcz_plot_map(
                (data, profile),
                title=titulo,
                show_legend=True,
                isave=False  # Não salvar automaticamente
            )
            
            # Salvar em buffer para exibição
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            
            # Exibir a imagem
            st.markdown("#### 🖼️ Visualização Gerada")
            st.image(buf, caption=titulo, use_container_width=True)
            
            # Preparar dados para download
            buf.seek(0)
            png_data = buf.getvalue()
            
            # Botões de download
            col1, col2 = st.columns(2)
            
            with col1:
                # Download da imagem PNG
                st.download_button(
                    label="📸 Baixar Imagem PNG",
                    data=png_data,
                    file_name=f"lcz_map_{st.session_state.lcz_city_name or 'cidade'}.png",
                    mime="image/png",
                    help="Imagem do mapa LCZ em alta resolução",
                    use_container_width=True
                )
            
            with col2:
                # Download do GeoJSON
                if st.session_state.lcz_data is not None:
                    geojson_data = st.session_state.lcz_data.to_json()
                    st.download_button(
                        label="🗺️ Baixar GeoJSON",
                        data=geojson_data,
                        file_name=f"lcz_data_{st.session_state.lcz_city_name or 'cidade'}.geojson",
                        mime="application/json",
                        help="Dados vetoriais do mapa LCZ",
                        use_container_width=True
                    )
            
            plt.close(fig)  # Liberar memória
            st.success("✅ Visualização gerada com sucesso!")
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar visualização: {str(e)}")

def renderizar_secao_calculo_area():
    """
    Renderiza a seção de cálculo de área com análise avançada usando lcz_cal_area.
    Inclui gráficos Plotly interativos, relatórios e estatísticas detalhadas.
    """
    
    if st.session_state.lcz_data is None:
        st.warning("⚠️ Dados LCZ não encontrados na sessão.")
        return
    
    try:
        # Verificar se já temos dados de área calculados na sessão
        if st.session_state.lcz_area_stats is None or st.session_state.lcz_plot_data is None:
            with st.spinner("Calculando estatísticas de área..."):
                from utils.lcz4r import lcz_cal_area
                result = lcz_cal_area(st.session_state.lcz_data)
                st.session_state.lcz_area_stats = result['stats']
                st.session_state.lcz_plot_data = result['plot_data']
                st.session_state.lcz_area_summary = result['summary']
        
        # Usar dados da sessão
        area_stats = st.session_state.lcz_area_stats
        plot_data = st.session_state.lcz_plot_data
        summary = st.session_state.lcz_area_summary
        
        # Exibir resumo geral
        st.markdown("### 📈 Resumo Geral")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Área Total", 
                f"{summary['total_area_km2']:.1f} km²",
                help="Área total coberta pelo mapa LCZ"
            )
        
        with col2:
            st.metric(
                "Classes LCZ", 
                summary['num_classes'],
                help="Número de diferentes classes LCZ presentes"
            )
        
        with col3:
            st.metric(
                "Polígonos", 
                summary['num_total_poligonos'],
                help="Número total de polígonos no mapa"
            )
        
        with col4:
            st.metric(
                "Classe Dominante", 
                summary['classe_dominante'],
                f"{summary['percentual_classe_dominante']:.1f}%",
                help="Classe LCZ com maior área"
            )
        
        # Interface de controle para visualização
        st.markdown("### ⚙️ Configurações de Visualização")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            tipo_grafico = st.selectbox(
                "📊 Tipo de Gráfico:",
                ["bar", "pie", "donut", "treemap"],
                format_func=lambda x: {
                    "bar": "📊 Gráfico de Barras", 
                    "pie": "🥧 Gráfico de Pizza", 
                    "donut": "🍩 Gráfico Donut",
                    "treemap": "🗂️ Mapa de Árvore"
                }[x],
                help="Escolha o tipo de visualização para a distribuição de áreas"
            )
        
        with col2:
            mostrar_tabela = st.checkbox("📋 Mostrar Tabela", value=True)
        
        with col3:
            mostrar_relatorio = st.checkbox("📄 Gerar Relatório", value=False)
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            gerar_analise = st.button("📊 Gerar Análise Completa", type="primary", use_container_width=True)
        
        with col2:
            recalcular = st.button("🔄 Recalcular Áreas", use_container_width=True)
        
        # Recalcular se solicitado
        if recalcular:
            st.session_state.lcz_area_stats = None
            st.session_state.lcz_plot_data = None
            st.session_state.lcz_area_summary = None
            st.rerun()
        
        # Gerar análise completa
        if gerar_analise:
            gerar_analise_area_completa(area_stats, plot_data, summary, tipo_grafico, mostrar_tabela, mostrar_relatorio)
            
    except Exception as e:
        st.error(f"❌ Erro na análise de área: {str(e)}")
        # Limpar dados corrompidos
        st.session_state.lcz_area_stats = None
        st.session_state.lcz_plot_data = None
        st.session_state.lcz_area_summary = None


def gerar_analise_area_completa(area_stats, plot_data, summary, tipo_grafico, mostrar_tabela, mostrar_relatorio):
    """
    Gera análise completa de área com gráficos interativos, tabelas e relatórios.
    """
    
    try:
        st.markdown("### 📊 Análise de Distribuição de Área")
        
        # Gerar gráfico principal
        fig = criar_grafico_area_plotly(area_stats, plot_data, tipo_grafico)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Salvar gráfico para download
            import plotly.io as pio
            img_bytes = pio.to_image(fig, format="png", width=1200, height=800, scale=2)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📸 Baixar Gráfico PNG",
                    data=img_bytes,
                    file_name=f"lcz_area_analysis_{st.session_state.lcz_city_name or 'cidade'}.png",
                    mime="image/png",
                    help="Baixar gráfico de análise de área em alta resolução"
                )
            
            with col2:
                # Download dos dados em CSV
                csv_data = area_stats.to_csv(index=False)
                st.download_button(
                    label="📊 Baixar Dados CSV",
                    data=csv_data,
                    file_name=f"lcz_area_stats_{st.session_state.lcz_city_name or 'cidade'}.csv",
                    mime="text/csv",
                    help="Baixar estatísticas de área em formato CSV"
                )
        
        # Mostrar tabela detalhada se solicitado
        if mostrar_tabela:
            st.markdown("### 📋 Tabela Detalhada de Estatísticas")
            
            # Formatar tabela para melhor visualização
            area_stats_display = area_stats.copy()
            area_stats_display['area_total_km2'] = area_stats_display['area_total_km2'].round(2)
            area_stats_display['area_media_km2'] = area_stats_display['area_media_km2'].round(3)
            area_stats_display['percentual'] = area_stats_display['percentual'].round(1)
            
            st.dataframe(
                area_stats_display,
                use_container_width=True,
                column_config={
                    "zcl_classe": "Classe LCZ",
                    "area_total_km2": st.column_config.NumberColumn(
                        "Área Total (km²)",
                        format="%.2f"
                    ),
                    "num_poligonos": "Polígonos",
                    "area_media_km2": st.column_config.NumberColumn(
                        "Área Média (km²)",
                        format="%.3f"
                    ),
                    "percentual": st.column_config.NumberColumn(
                        "Percentual (%)",
                        format="%.1f%%"
                    )
                }
            )
        
        # Gerar relatório se solicitado
        if mostrar_relatorio:
            st.markdown("### 📄 Relatório de Análise LCZ")
            
            from utils.lcz4r import lcz_area_analysis_report
            relatorio = lcz_area_analysis_report(st.session_state.lcz_data, st.session_state.lcz_city_name)
            
            st.text_area(
                "Relatório Completo:",
                value=relatorio,
                height=400,
                help="Relatório detalhado da análise de área LCZ"
            )
            
            # Download do relatório
            st.download_button(
                label="📄 Baixar Relatório TXT",
                data=relatorio,
                file_name=f"relatorio_lcz_{st.session_state.lcz_city_name or 'cidade'}.txt",
                mime="text/plain",
                help="Baixar relatório completo em formato texto"
            )
        
        # Análise adicional
        st.markdown("### 🔍 Análise Adicional")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Análise urbano vs natural
            urbano_mask = area_stats['zcl_classe'].str.contains('LCZ [1-9]|LCZ 10')
            natural_mask = area_stats['zcl_classe'].str.contains('LCZ [A-G]')
            
            area_urbana = area_stats[urbano_mask]['area_total_km2'].sum()
            area_natural = area_stats[natural_mask]['area_total_km2'].sum()
            
            st.metric(
                "Área Urbana (LCZ 1-10)",
                f"{area_urbana:.1f} km²",
                f"{(area_urbana/summary['total_area_km2']*100):.1f}%"
            )
            
            st.metric(
                "Área Natural (LCZ A-G)",
                f"{area_natural:.1f} km²",
                f"{(area_natural/summary['total_area_km2']*100):.1f}%"
            )
        
        with col2:
            # Fragmentação e densidade
            fragmentacao = summary['num_total_poligonos'] / summary['total_area_km2']
            
            st.metric(
                "Fragmentação",
                f"{fragmentacao:.2f} pol/km²",
                help="Número de polígonos por km² (maior = mais fragmentado)"
            )
            
            # Classe mais fragmentada
            area_stats['fragmentacao'] = area_stats['num_poligonos'] / area_stats['area_total_km2']
            classe_fragmentada = area_stats.loc[area_stats['fragmentacao'].idxmax(), 'zcl_classe']
            
            st.metric(
                "Classe Mais Fragmentada",
                classe_fragmentada,
                f"{area_stats['fragmentacao'].max():.2f} pol/km²"
            )
        
        st.success("✅ Análise de área gerada com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao gerar análise: {str(e)}")


def criar_grafico_area_plotly(area_stats, plot_data, tipo_grafico):
    """
    Cria gráfico Plotly baseado no tipo selecionado.
    """
    
    try:
        cores_lcz = plot_data['cores_lcz']
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
                    'num_poligonos': 'Número de Polígonos',
                    'area_media_km2': 'Área Média (km²)',
                    'percentual': 'Percentual (%)'
                }
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            
        elif tipo_grafico == "pie":
            fig = px.pie(
                area_stats,
                values='area_total_km2',
                names='zcl_classe',
                title=f"Distribuição Percentual de Área por Classe LCZ - {cidade_nome}",
                color='zcl_classe',
                color_discrete_map=cores_lcz,
                hover_data=['num_poligonos']
            )
            
        elif tipo_grafico == "donut":
            fig = go.Figure(data=[go.Pie(
                labels=area_stats['zcl_classe'],
                values=area_stats['area_total_km2'],
                hole=0.4,
                marker_colors=colors,
                hovertemplate='<b>%{label}</b><br>' +
                             'Área: %{value:.2f} km²<br>' +
                             'Percentual: %{percent}<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title=f"Distribuição de Área LCZ (Donut) - {cidade_nome}",
                annotations=[dict(text='LCZ', x=0.5, y=0.5, font_size=20, showarrow=False)]
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
            font=dict(size=12),
            title_font_size=16,
            height=600
        )
        
        return fig
        
    except Exception as e:
        st.error(f"❌ Erro ao criar gráfico: {str(e)}")
        return None

def gerar_grafico_area_plotly(area_stats, tipo_grafico, mostrar_tabela):
    """Gera gráficos interativos de área usando Plotly."""
    
    try:
        # Preparar dados
        classes = area_stats['Classe LCZ']
        areas = area_stats['Área Total (km²)']
        
        # Cores LCZ padrão
        cores_lcz = {
            'LCZ 1': '#910613', 'LCZ 2': '#D9081C', 'LCZ 3': '#FF0A22', 'LCZ 4': '#C54F1E',
            'LCZ 5': '#FF6628', 'LCZ 6': '#FF985E', 'LCZ 7': '#FDED3F', 'LCZ 8': '#BBBBBB',
            'LCZ 9': '#FFCBAB', 'LCZ 10': '#565656', 'LCZ A': '#006A18', 'LCZ B': '#00A926',
            'LCZ C': '#628432', 'LCZ D': '#B5DA7F', 'LCZ E': '#000000', 'LCZ F': '#FCF7B1',
            'LCZ G': '#656BFA'
        }
        
        colors = [cores_lcz.get(classe, '#808080') for classe in classes]
        
        # Criar gráfico baseado no tipo selecionado
        if tipo_grafico == "bar":
            fig = px.bar(
                area_stats, 
                x='Classe LCZ', 
                y='Área Total (km²)',
                title=f"Distribuição de Área por Classe LCZ - {st.session_state.lcz_city_name or 'Cidade'}",
                color='Classe LCZ',
                color_discrete_map=cores_lcz,
                hover_data=['Número de Polígonos', 'Área Média (km²)']
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            
        elif tipo_grafico == "pie":
            fig = px.pie(
                area_stats,
                values='Área Total (km²)',
                names='Classe LCZ',
                title=f"Distribuição Percentual de Área por Classe LCZ - {st.session_state.lcz_city_name or 'Cidade'}",
                color='Classe LCZ',
                color_discrete_map=cores_lcz
            )
            
        elif tipo_grafico == "donut":
            fig = go.Figure(data=[go.Pie(
                labels=classes,
                values=areas,
                hole=0.4,
                marker_colors=colors,
                hovertemplate='<b>%{label}</b><br>Área: %{value:.2f} km²<br>Percentual: %{percent}<extra></extra>'
            )])
            fig.update_layout(
                title=f"Distribuição de Área por Classe LCZ - {st.session_state.lcz_city_name or 'Cidade'}",
                annotations=[dict(text='LCZ', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
        
        # Configurações gerais do layout
        fig.update_layout(
            height=600,
            font=dict(size=12),
            title_font_size=16,
            margin=dict(t=80, b=40, l=40, r=40)
        )
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Exibir tabela se solicitado
        if mostrar_tabela:
            st.markdown("#### 📋 Tabela Detalhada")
            
            # Adicionar percentuais
            area_stats_display = area_stats.copy()
            area_stats_display['Percentual (%)'] = (area_stats_display['Área Total (km²)'] / area_stats_display['Área Total (km²)'].sum() * 100).round(2)
            
            st.dataframe(
                area_stats_display,
                use_container_width=True,
                hide_index=True
            )
        
        # Botões de download
        col1, col2 = st.columns(2)
        
        with col1:
            # Download da tabela CSV
            csv_data = area_stats.to_csv(index=False)
            st.download_button(
                label="📊 Baixar Dados CSV",
                data=csv_data,
                file_name=f"lcz_area_analysis_{st.session_state.lcz_city_name or 'cidade'}.csv",
                mime="text/csv",
                help="Baixar dados de área em formato CSV",
                use_container_width=True
            )
        
        with col2:
            # Download do gráfico HTML
            html_data = fig.to_html()
            st.download_button(
                label="📈 Baixar Gráfico HTML",
                data=html_data,
                file_name=f"lcz_area_chart_{st.session_state.lcz_city_name or 'cidade'}.html",
                mime="text/html",
                help="Baixar gráfico interativo em HTML",
                use_container_width=True
            )
        
        st.success("✅ Análise de área gerada com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao gerar análise de área: {str(e)}")

def renderizar_mapa_folium():
    """Renderiza o mapa interativo com Folium usando dados da sessão."""
    
    try:
        # Usar dados da sessão
        gdf_lcz = st.session_state.lcz_data
        
        if gdf_lcz is None or gdf_lcz.empty:
            st.warning("⚠️ Dados LCZ não encontrados na sessão.")
            return
        
        # Calcular centro do mapa
        bounds = gdf_lcz.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Criar mapa base
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Definir cores para as classes LCZ
        cores_lcz = {
            'LCZ 1':  '#910613',  'LCZ 2':  '#D9081C',  'LCZ 3':  '#FF0A22',  'LCZ 4':  '#C54F1E',
            'LCZ 5':  '#FF6628',  'LCZ 6':  '#FF985E',  'LCZ 7':  '#FDED3F',  'LCZ 8':  '#BBBBBB',
            'LCZ 9':  '#FFCBAB',  'LCZ 10': '#565656',  'LCZ A':  '#006A18',  'LCZ B':  '#00A926',
            'LCZ C':  '#628432',  'LCZ D':  '#B5DA7F',  'LCZ E':  '#000000',  'LCZ F':  '#FCF7B1',
            'LCZ G':  '#656BFA'
        }
        
        # Adicionar camada GeoJSON
        for idx, row in gdf_lcz.iterrows():
            classe = row.get('zcl_classe', 'Desconhecida')
            cor = cores_lcz.get(classe, '#808080')
            area = row.get('area_km2', 0)
            
            folium.GeoJson(
                row.geometry,
                style_function=lambda feature, color=cor: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7,
                    'opacity': 0.8
                },
                popup=folium.Popup(
                    f"""
                    <div style='width: 250px; font-family: Arial, sans-serif;'>
                        <h4 style='color: {cor}; margin-bottom: 10px;'>{classe}</h4>
                        <p><b>📏 Área:</b> {area:.2f} km²</p>
                        <p><b>📋 Características:</b></p>
                        <p style='font-size: 12px;'>{row.get('descricao', 'Sem descrição disponível')}</p>
                        <p><b>🌡️ Efeito Térmico:</b></p>
                        <p style='font-size: 12px;'>{row.get('efeito_temp', 'Não disponível')}</p>
                        <p><b>🏙️ Ilha de Calor:</b></p>
                        <p style='font-size: 12px;'>{row.get('ilha_calor', 'Não disponível')}</p>
                        <p><b>💡 Intervenção Recomendada:</b></p>
                        <p style='font-size: 12px;'>{row.get('intervencao', 'Não disponível')}</p>
                    </div>
                    """,
                    max_width=300
                )
            ).add_to(m)
        
        # Ajustar zoom aos dados
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        
        # Adicionar controles
        folium.LayerControl().add_to(m)
        
        # Instruções de uso
        st.markdown("""
        #### 🎯 Instruções de Uso
        
        **Como interagir com o mapa:**
        1. 🖱️ **Clique nos polígonos** para ver informações detalhadas sobre cada zona climática
        2. 🔍 **Use os controles de zoom** para explorar diferentes escalas
        3. 🗺️ **Navegue pelo mapa** arrastando para explorar toda a área
        4. 📊 **Observe as cores** que representam diferentes classes LCZ
        """)
        
        # Exibir mapa
        map_data = st_folium(m, width="100%", height=800, returned_objects=["last_object_clicked"])
        
        # Exibir informações do clique
        if map_data['last_object_clicked']:
            st.info(f"🎯 Último elemento clicado: {map_data['last_object_clicked']}")
        
        # Estatísticas do mapa
        with st.expander("📊 Estatísticas do Mapa", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏙️ Cidade", st.session_state.lcz_city_name or "N/A")
            
            with col2:
                st.metric("🎨 Classes LCZ", len(gdf_lcz['zcl_classe'].unique()))
            
            with col3:
                st.metric("📐 Total de Polígonos", len(gdf_lcz))
            
            with col4:
                area_total = gdf_lcz['area_km2'].sum() if 'area_km2' in gdf_lcz.columns else 0
                st.metric("📏 Área Total", f"{area_total:.1f} km²")
            
            # Distribuição por classe
            if 'zcl_classe' in gdf_lcz.columns:
                st.markdown("**📊 Distribuição por Classe LCZ:**")
                distribuicao = gdf_lcz['zcl_classe'].value_counts()
                st.bar_chart(distribuicao)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar mapa: {str(e)}")
        st.info("💡 Tente gerar um novo mapa LCZ usando o gerador acima.")
