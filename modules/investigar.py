# modules/investigar.py

import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
import pandas as pd
from utils import processamento

def renderizar_pagina():
    """Renderiza a página do módulo Investigar."""
    
    st.markdown("""
    <div class="module-header">
        <h1>🔬 Módulo Investigar</h1>
        <p>Carregue seus dados de campo e defina áreas de interesse para análise detalhada</p>
    </div>
    """, unsafe_allow_html=True)

    # Inicializar variáveis de estado se não existirem
    if 'dados_usuario' not in st.session_state:
        st.session_state['dados_usuario'] = None
    if 'area_de_interesse' not in st.session_state:
        st.session_state['area_de_interesse'] = None

    # Layout em colunas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Passo 1: Upload do CSV
        st.markdown("### 📁 Passo 1: Carregue seus Dados de Campo")
        
        with st.expander("ℹ️ Formato do arquivo CSV", expanded=False):
            st.markdown("""
            **Seu arquivo CSV deve conter pelo menos estas colunas:**
            - **Latitude** (nomes aceitos: lat, latitude, LAT, Latitude)
            - **Longitude** (nomes aceitos: lon, lng, longitude, LON, Longitude)  
            - **Valor medido** (nomes aceitos: valor, temp, temperatura, medida, value)
            
            **Exemplo de estrutura:**
            ```
            latitude,longitude,temperatura,descricao
            -23.5505,-46.6333,32.5,Praça da Sé
            -23.5489,-46.6388,28.2,Parque Ibirapuera
            -23.5558,-46.6396,35.1,Av. Paulista
            ```
            """)
        
        arquivo_csv = st.file_uploader(
            "Selecione um arquivo .csv com seus dados de campo:",
            type="csv",
            help="O arquivo deve conter colunas de latitude, longitude e valores medidos"
        )

        if arquivo_csv:
            with st.spinner("Processando arquivo..."):
                gdf_pontos, erro = processamento.validar_e_processar_csv(arquivo_csv)
                
            if erro:
                st.error(f"❌ {erro}")
                st.session_state['dados_usuario'] = None
            else:
                st.success(f"✅ {len(gdf_pontos)} pontos carregados com sucesso!")
                st.session_state['dados_usuario'] = gdf_pontos
                
                # Mostrar preview dos dados
                with st.expander("👀 Visualizar dados carregados"):
                    st.dataframe(
                        gdf_pontos.drop(columns='geometry').head(10),
                        use_container_width=True
                    )
                    
                    # Estatísticas básicas
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    with col_stats1:
                        st.metric("Total de Pontos", len(gdf_pontos))
                    with col_stats2:
                        st.metric("Valor Médio", f"{gdf_pontos['valor'].mean():.2f}")
                    with col_stats3:
                        st.metric("Amplitude", f"{gdf_pontos['valor'].max() - gdf_pontos['valor'].min():.2f}")

        # Passo 2: Definir Área de Interesse
        st.markdown("### 🗺️ Passo 2: Defina sua Área de Interesse")
        
        st.info("""
        **Instruções:**
        1. Use a ferramenta de desenho (polígono) no mapa abaixo
        2. Clique nos pontos para criar o contorno da sua área de estudo
        3. Feche o polígono clicando no primeiro ponto novamente
        4. A área será automaticamente detectada
        """)

        # Criar mapa com ferramenta de desenho
        map_center = [-23.55, -46.63]
        m = folium.Map(
            location=map_center, 
            zoom_start=11, 
            tiles="CartoDB positron"
        )
        
        # Adicionar ferramenta de desenho
        draw = Draw(
            export=True,
            filename='area_interesse.geojson',
            draw_options={
                'polygon': {'showArea': True, 'metric': True},
                'rectangle': {'showArea': True, 'metric': True},
                'circle': False,
                'marker': False,
                'circlemarker': False,
                'polyline': False
            },
            edit_options={'edit': True}
        )
        draw.add_to(m)
        
        # Adicionar pontos do usuário se existirem
        if st.session_state['dados_usuario'] is not None:
            gdf_pontos = st.session_state['dados_usuario']
            for _, row in gdf_pontos.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=6,
                    popup=f"Valor: {row['valor']:.2f}",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.7
                ).add_to(m)
        
        # Renderizar mapa e capturar dados desenhados
        map_data = st_folium(
            m, 
            width=None, 
            height=500,
            returned_objects=["all_drawings"],
            key="investigar_map"
        )

        # Processar área desenhada
        if map_data and map_data.get("all_drawings") and len(map_data["all_drawings"]) > 0:
            area_desenhada = map_data["all_drawings"][-1]['geometry']  # Pega a última área desenhada
            st.session_state['area_de_interesse'] = area_desenhada
            
            # Calcular área aproximada
            try:
                from shapely.geometry import Polygon
                if area_desenhada['type'] == 'Polygon':
                    coords = area_desenhada['coordinates'][0]
                    poly = Polygon(coords)
                    # Conversão aproximada para m² (não é precisa, apenas indicativa)
                    area_graus = poly.area
                    area_km2 = area_graus * 111 * 111  # Aproximação grosseira
                    
                    st.success(f"✅ Área de interesse definida! Área aproximada: {area_km2:.2f} km²")
            except:
                st.success("✅ Área de interesse definida!")

    with col2:
        # Painel de status e controles
        st.markdown("### 📊 Status da Análise")
        
        # Status dos dados
        if st.session_state['dados_usuario'] is not None:
            st.success("✅ Dados carregados")
            num_pontos = len(st.session_state['dados_usuario'])
            st.metric("Pontos de dados", num_pontos)
        else:
            st.warning("⏳ Aguardando dados")
        
        # Status da área
        if st.session_state['area_de_interesse'] is not None:
            st.success("✅ Área definida")
        else:
            st.warning("⏳ Aguardando área")
        
        st.markdown("---")
        
        # Passo 3: Executar Análise
        st.markdown("### 🚀 Passo 3: Executar Análise")
        
        pode_analisar = (
            st.session_state['dados_usuario'] is not None or 
            st.session_state['area_de_interesse'] is not None
        )
        
        if not pode_analisar:
            st.info("Carregue dados e/ou defina uma área para habilitar a análise.")
        
        if st.button(
            "🔍 Executar Análise", 
            type="primary",
            disabled=not pode_analisar,
            use_container_width=True
        ):
            with st.spinner("Executando análise..."):
                # Simular processamento
                import time
                time.sleep(1)
                
                st.session_state['analise_pronta'] = True
                st.success("✅ Análise concluída!")
                st.info("Vá para o módulo **Visualizar** para ver os resultados detalhados.")
                
                # Opção de ir direto para visualizar
                if st.button("📊 Ir para Visualizar", use_container_width=True):
                    st.session_state.navigation = "Visualizar"
                    st.rerun()

        # Seção de ajuda
        st.markdown("---")
        st.markdown("### ❓ Precisa de Ajuda?")
        
        with st.expander("📋 Exemplo de dados CSV"):
            exemplo_csv = """latitude,longitude,temperatura,local
-23.5505,-46.6333,32.5,Centro
-23.5489,-46.6388,28.2,Ibirapuera
-23.5558,-46.6396,35.1,Paulista
-23.5629,-46.6544,30.8,Vila Madalena"""
            
            st.code(exemplo_csv, language="csv")
            
            # Botão para baixar exemplo
            st.download_button(
                label="📥 Baixar exemplo CSV",
                data=exemplo_csv,
                file_name="exemplo_dados_campo.csv",
                mime="text/csv"
            )
        
        with st.expander("🎯 Dicas de coleta"):
            st.markdown("""
            **Para coleta de dados de campo:**
            - Use GPS para coordenadas precisas
            - Meça em horários consistentes
            - Anote condições meteorológicas
            - Documente o tipo de superfície
            - Faça múltiplas medições por ponto
            """)

    # Seção de informações adicionais
    st.markdown("---")
    st.markdown("### 🎓 Metodologia Científica")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        **Coleta de Dados Recomendada:**
        - Temperatura do ar (°C)
        - Umidade relativa (%)
        - Velocidade do vento (m/s)
        - Coordenadas GPS precisas
        - Horário da medição
        - Descrição do local
        """)
    
    with col_info2:
        st.markdown("""
        **Análises Disponíveis:**
        - Correlação com Zonas Climáticas Locais
        - Estatísticas descritivas por área
        - Distribuição espacial dos valores
        - Comparação entre diferentes ZCLs
        - Identificação de hotspots
        """)

    # Footer com próximos passos
    if st.session_state.get('analise_pronta'):
        st.success("""
        🎉 **Análise pronta!** Seus dados foram processados com sucesso. 
        Vá para o módulo **Visualizar** para explorar os resultados em detalhes.
        """)

