# modules/explorar.py

import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.colormap import linear
import pandas as pd

def renderizar_pagina(gdf_zcl, gdf_temp):
    """Renderiza a página do módulo Explorar."""
    
    st.markdown("""
    <div class="module-header">
        <h1>🌍 Módulo Explorar</h1>
        <p>Visualize e explore mapas interativos de Zonas Climáticas Locais e temperatura da superfície</p>
    </div>
    """, unsafe_allow_html=True)

    # Painel de controle na barra lateral
    with st.sidebar:
        st.markdown("### 🎛️ Controles de Visualização")
        
        # Seleção de cidade
        cidade_selecionada = st.selectbox(
            "📍 Selecione uma cidade:",
            ["São Paulo (Exemplo)"],
            help="Mais cidades serão adicionadas em versões futuras"
        )
        
        st.markdown("### 🗂️ Camadas de Dados")
        
        # Controles de camadas com descrições
        mostrar_zcl = st.checkbox(
            "🏘️ Zonas Climáticas Locais (ZCL)", 
            value=True,
            help="Mostra a classificação do uso do solo urbano segundo Stewart & Oke (2012)"
        )
        
        mostrar_temp = st.checkbox(
            "🌡️ Temperatura da Superfície", 
            value=False,
            help="Dados de temperatura obtidos por sensoriamento remoto"
        )
        
        # Informações sobre os dados
        if mostrar_zcl or mostrar_temp:
            st.markdown("### ℹ️ Informações dos Dados")
            
            if mostrar_zcl:
                st.info("""
                **ZCL Ativas:**
                - LCZ 2: Compact midrise
                - LCZ 5: Open midrise  
                - LCZ 8: Large low-rise
                - LCZ A: Dense trees
                - LCZ D: Low plants
                """)
            
            if mostrar_temp:
                if gdf_temp is not None and not gdf_temp.empty:
                    temp_min = gdf_temp['temperatura_c'].min()
                    temp_max = gdf_temp['temperatura_c'].max()
                    st.info(f"""
                    **Temperatura:**
                    - Mínima: {temp_min:.1f}°C
                    - Máxima: {temp_max:.1f}°C
                    - Fonte: Landsat 8 TIRS
                    """)

    # Área principal do mapa
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Configuração do mapa base
        map_center = [-23.5505, -46.6333]  # Centro de São Paulo
        m = folium.Map(
            location=map_center, 
            zoom_start=9, 
            tiles="CartoDB positron",  # Um tile inicial obrigatório
            prefer_canvas=True
        )
        # Adicionar camada de ZCL se selecionada
        if mostrar_zcl and gdf_zcl is not None and not gdf_zcl.empty:
            # Mapeamento de cores para as classes de ZCL
            zcl_color_map = {
            'LCZ 1':  '#910613',  # Compact high-rise
            'LCZ 2':  '#D9081C',  # Compact midrise
            'LCZ 3':  '#FF0A22',  # Compact low-rise
            'LCZ 4':  '#C54F1E',  # Open high-rise
            'LCZ 5':  '#FF6628',  # Open midrise
            'LCZ 6':  '#FF985E',  # Open low-rise
            'LCZ 7':  '#FDED3F',  # Lightweight low-rise
            'LCZ 8':  '#BBBBBB',  # Large low-rise
            'LCZ 9':  '#FFCBAB',  # Sparsely built
            'LCZ 10': '#565656',  # Heavy industry
            'LCZ A':  '#006A18',  # Dense trees
            'LCZ B':  '#00A926',  # Scattered trees
            'LCZ C':  '#628432',  # Bush / scrub
            'LCZ D':  '#B5DA7F',  # Low plants
            'LCZ E':  '#000000',  # Bare rock / paved
            'LCZ F':  '#FCF7B1',  # Bare soil / sand
            'LCZ G':  '#656BFA'   # Water
        }
            
            # Adiciona cada polígono de ZCL ao mapa
            for _, row in gdf_zcl.iterrows():
                zcl_classe = row.get('zcl_classe', 'Desconhecida')
                cor = zcl_color_map.get(zcl_classe, '#gray')
                
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
                        <div style='width: 200px'>
                        <h4>{zcl_classe}</h4>
                        <p><b>Características:</b></p>
                        <p>{row.get('descricao', 'Sem descrição disponível')}</p>
                        <p><b>Efeito Térmico:</b> {row.get('efeito_temp', 'Não disponível')}</p>
                        <p><b>Ilha de Calor:</b> {row.get('ilha_calor', 'Não disponível')}</p>
                        <p><b>Intervenção Recomendada:</b> {row.get('intervencao', 'Não disponível')}</p>
                        </div>
                        """,
                        max_width=250
                    )
                ).add_to(m)

        # Adicionar camada de temperatura se selecionada
        if mostrar_temp and gdf_temp is not None and not gdf_temp.empty:
            # Criar mapa de cores para temperatura
            temp_min = gdf_temp['temperatura_c'].min()
            temp_max = gdf_temp['temperatura_c'].max()
            
            colormap = linear.YlOrRd_09.scale(temp_min, temp_max)
            colormap.caption = 'Temperatura da Superfície (°C)'
            m.add_child(colormap)

            # Adiciona cada célula de temperatura ao mapa
            for _, row in gdf_temp.iterrows():
                temp_valor = row['temperatura_c']
                
                folium.GeoJson(
                    row.geometry,
                    style_function=lambda feature, temp=temp_valor: {
                        'fillColor': colormap(temp),
                        'color': 'none',
                        'weight': 0,
                        'fillOpacity': 0.6,
                    },
                    tooltip=folium.Tooltip(
                        f"<b>Temperatura:</b> {temp_valor:.1f}°C",
                        sticky=True
                    )
                ).add_to(m)

        # Adicionar controle de camadas
        folium.LayerControl().add_to(m)
        
        # Renderizar o mapa
        map_data = st_folium(
            m, 
            width=None, 
            height=600, 
            returned_objects=["last_object_clicked"],
            key="explorar_map"
        )
        
    with col2:
        st.markdown("### 🎯 Instruções")
        st.markdown("""
        **Como usar:**
        1. Selecione as camadas desejadas na barra lateral
        2. Clique nos elementos do mapa para ver detalhes
        3. Use os controles de zoom para explorar
        4. Ative/desative camadas conforme necessário
        """)
        
        # Mostrar informações do último clique
        if map_data and map_data.get("last_object_clicked"):
            st.markdown("### 📍 Último Clique")
            clicked_data = map_data["last_object_clicked"]
            if clicked_data:
                st.json(clicked_data)
        
        # Estatísticas rápidas
        st.markdown("### 📊 Estatísticas Rápidas")
        
        if gdf_zcl is not None and not gdf_zcl.empty:
            num_zcl = len(gdf_zcl['zcl_classe'].unique())
            st.metric("Classes de ZCL", num_zcl)
            
        if gdf_temp is not None and not gdf_temp.empty:
            temp_media = gdf_temp['temperatura_c'].mean()
            st.metric("Temp. Média", f"{temp_media:.1f}°C")

    # Seção de legenda expandida
    
    
   # Dicionário de cores das LCZ
    lcz_color_map = {
        'LCZ 1': '#910613', 'LCZ 2': '#D9081C', 'LCZ 3': '#FF0A22',
        'LCZ 4': '#C54F1E', 'LCZ 5': '#FF6628', 'LCZ 6': '#FF985E',
        'LCZ 7': '#FDED3F', 'LCZ 8': '#BBBBBB', 'LCZ 9': '#FFCBAB',
        'LCZ 10': '#565656', 'LCZ A': '#006A18', 'LCZ B': '#00A926',
        'LCZ C': '#628432', 'LCZ D': '#B5DA7F', 'LCZ E': '#000000',
        'LCZ F': '#FCF7B1', 'LCZ G': '#656BFA'
    }

    with st.expander("📖 Legenda Detalhada das Zonas Climáticas Locais"):
        st.markdown("""
        ### Zonas Construídas (Built Types)
        """)

        built_lcz = [
            ('LCZ 1', 'Compact high-rise', 'Maior retenção de calor urbano, forte aquecimento noturno', 'Muito forte', 'Criar ventilação urbana, áreas verdes verticais, telhados frios'),
            ('LCZ 2', 'Compact midrise', 'Aquecimento elevado, mas menos intenso que arranha-céus', 'Forte', 'Manter corredores de ventilação e arborização'),
            ('LCZ 3', 'Compact low-rise', 'Aquecimento leve', 'Baixa', 'Expandir vegetação urbana e reduzir impermeabilização'),
            ('LCZ 4', 'Open high-rise', 'Menor que LCZ 1, ventilação importante', 'Moderada', 'Manter áreas verdes e reduzir impermeabilização'),
            ('LCZ 5', 'Open midrise', 'Aquecimento leve a moderado', 'Baixa', 'Evitar adensamento excessivo, introduzir arborização'),
            ('LCZ 6', 'Open low-rise', 'Aquecimento leve, efeito térmico relativamente baixo', 'Baixa', 'Expandir vegetação e áreas permeáveis'),
            ('LCZ 7', 'Lightweight low-rise', 'Suaviza temperaturas durante o dia', 'Baixa', 'Expandir áreas verdes e gramados'),
            ('LCZ 8', 'Large low-rise', 'Superfícies extensas acumulam calor e irradiam à noite', 'Pode gerar ilhas de calor locais', 'Aplicar coberturas frias, reduzir pavimentação impermeável'),
            ('LCZ 9', 'Sparsely built', 'Aquecimento baixo a moderado', 'Baixa', 'Introduzir vegetação, manter permeabilidade'),
            ('LCZ 10', 'Heavy industry', 'Superfícies industriais acumulam calor', 'Alta localmente', 'Aplicar coberturas frias, reduzir pavimentos quentes')
        ]

        for lcz, desc, efeito, ilha, interv in built_lcz:
            cor = lcz_color_map.get(lcz, '#808080')
            st.markdown(f"""
            <span style="background-color:{cor};color:white;padding:3px 8px;border-radius:4px">{lcz}</span>  
            **{desc}**  
            *Efeito térmico:* {efeito}  
            *Contribuição à ilha de calor:* {ilha}  
            *Intervenção recomendada:* {interv}  
            """, unsafe_allow_html=True)

        st.markdown("### Cobertura Natural (Land Cover Types)")

        natural_lcz = [
            ('LCZ A', 'Dense trees', 'Resfriamento significativo por sombra e evapotranspiração', 'Mitigação significativa', 'Preservar e ampliar parques urbanos'),
            ('LCZ B', 'Scattered trees', 'Redução moderada da temperatura', 'Mitigação moderada', 'Aumentar densidade arbórea e conectar corredores verdes'),
            ('LCZ C', 'Bush, scrub', 'Suaviza temperaturas, menor efeito que árvores densas', 'Mitigação leve', 'Expandir cobertura arbustiva e corredores verdes'),
            ('LCZ D', 'Low plants', 'Suaviza temperaturas durante o dia, pouco efeito noturno', 'Mitigação leve a moderada', 'Expandir áreas permeáveis e gramados'),
            ('LCZ E', 'Bare rock or paved', 'Retém calor, aumenta temperatura local', 'Aumenta efeito de aquecimento', 'Reduzir pavimentação, aplicar coberturas reflexivas'),
            ('LCZ F', 'Bare soil or sand', 'Leve aquecimento, menor que pavimentado', 'Baixa', 'Plantar vegetação baixa ou gramados'),
            ('LCZ G', 'Water', 'Resfriamento local', 'Mitiga, pode resfriar microclimas', 'Proteger e integrar corpos d\'água no tecido urbano')
        ]

        for lcz, desc, efeito, ilha, interv in natural_lcz:
            cor = lcz_color_map.get(lcz, '#808080')
            st.markdown(f"""
            <span style="background-color:{cor};color:white;padding:3px 8px;border-radius:4px">{lcz}</span>  
            **{desc}**  
            *Efeito térmico:* {efeito}  
            *Contribuição à ilha de calor:* {ilha}  
            *Intervenção recomendada:* {interv}  
            """, unsafe_allow_html=True)

    # Dicas de uso
    st.markdown("""
    ---
    ### 💡 Dicas de Uso

    - **Combine camadas:** Ative simultaneamente as camadas de ZCL e de temperatura da superfície para visualizar como diferentes tipos de uso do solo influenciam o microclima urbano.  
    - **Explore diferentes escalas:** Utilize o zoom para examinar desde grandes regiões da cidade até quarteirões específicos, identificando padrões locais de aquecimento e resfriamento.  
    - **Compare áreas:** Observe diferenças de temperatura entre zonas verdes (por exemplo, LCZ A – Dense Trees) e áreas densamente construídas (como LCZ 2, 5 ou 8) para entender o impacto das características urbanas.  
    - **Planeje intervenções:** Use o mapa para identificar áreas que podem se beneficiar de estratégias de mitigação da ilha de calor, como arborização, telhados frios ou aumento de áreas permeáveis.  
    - **Próximo passo:** Acesse o módulo "Investigar" para trabalhar com seus próprios dados de campo e aprofundar a análise.
    """)

