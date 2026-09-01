# modules/explorar.py

import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
import json

from utils.lcz4r import lcz_get_map, process_lcz_map, enhance_lcz_data, lcz_plot_map

# Paleta oficial das classes LCZ (Stewart & Oke, 2012 / WUDAPT).
CORES_LCZ = {
    'LCZ 1': '#910613', 'LCZ 2': '#D9081C', 'LCZ 3': '#FF0A22', 'LCZ 4': '#C54F1E',
    'LCZ 5': '#FF6628', 'LCZ 6': '#FF985E', 'LCZ 7': '#FDED3F', 'LCZ 8': '#BBBBBB',
    'LCZ 9': '#FFCBAB', 'LCZ 10': '#565656', 'LCZ A': '#006A18', 'LCZ B': '#00A926',
    'LCZ C': '#628432', 'LCZ D': '#B5DA7F', 'LCZ E': '#000000', 'LCZ F': '#FCF7B1',
    'LCZ G': '#656BFA'
}


def init_session_state():
    """Inicializa o estado da sessão com valores padrão."""
    defaults = {
        'lcz_data': None,
        'lcz_raster_data': None,
        'lcz_raster_profile': None,
        'lcz_raster_path': None,
        'lcz_city_name': None,
        'lcz_success_message': "",
        'lcz_error_message': "",
        'lcz_area_stats': None,
        'lcz_plot_data': None,
        'lcz_area_summary': None,
        'lcz_lst_result': None,
        'lcz_pollution_result': None,
        'lcz_pollution_poluente': None,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def clear_lcz_session_data():
    """Limpa os dados de uma exploração anterior antes de gerar um novo mapa."""
    for key in list(st.session_state.keys()):
        if key.startswith('lcz_'):
            st.session_state[key] = None
    st.session_state.lcz_success_message = ""
    st.session_state.lcz_error_message = ""


def save_lcz_data_to_session(data, profile, city_name, enhanced_gdf, raster_path=None):
    """Salva os dados de uma exploração recém-gerada na sessão."""
    st.session_state.lcz_raster_data = data
    st.session_state.lcz_raster_profile = profile
    st.session_state.lcz_city_name = city_name
    st.session_state.lcz_data = enhanced_gdf
    st.session_state.lcz_raster_path = raster_path
    st.session_state.lcz_success_message = f"Mapa LCZ gerado com sucesso para {city_name}."
    st.session_state.lcz_error_message = ""


def renderizar_pagina():
    """Renderiza a página do módulo Explorar."""
    init_session_state()

    from utils.ui import renderizar_cabecalho_modulo
    renderizar_cabecalho_modulo(
        "Módulo Explorar",
        "Gere e visualize mapas de Zonas Climáticas Locais (LCZ) para uma cidade",
        icone="explore",
    )

    if st.session_state.lcz_success_message:
        st.success(st.session_state.lcz_success_message)
    if st.session_state.lcz_error_message:
        st.error(st.session_state.lcz_error_message)

    renderizar_gerador_lcz()

    if st.session_state.lcz_data is not None:
        st.divider()
        aba_mapa, aba_area, aba_temperatura, aba_poluicao = st.tabs([
            "🗺️ Mapa", "📊 Área por Classe", "🌡️ Temperatura de Superfície", "🏭 Qualidade do Ar",
        ])
        with aba_mapa:
            renderizar_aba_mapa()
        with aba_area:
            renderizar_aba_area()
        with aba_temperatura:
            renderizar_aba_temperatura_superficie()
        with aba_poluicao:
            renderizar_aba_qualidade_ar()
    else:
        st.info(
            "👆 Digite o nome de uma cidade acima e clique em **Gerar Mapa LCZ** para começar. "
            "Use o nome completo com o país (ex.: \"Juiz de Fora, Brazil\")."
        )


def renderizar_gerador_lcz():
    """Formulário para gerar um novo mapa LCZ."""
    col1, col2 = st.columns([4, 1])
    with col1:
        cidade_nome = st.text_input(
            "Nome da cidade",
            placeholder="Ex: São Paulo, Brazil",
            label_visibility="collapsed",
            value=st.session_state.lcz_city_name or "",
        )
    with col2:
        gerar_mapa = st.button("🚀 Gerar Mapa LCZ", type="primary", use_container_width=True)

    if gerar_mapa and cidade_nome:
        processar_mapa_lcz(cidade_nome.strip())


def processar_mapa_lcz(cidade_nome):
    """Baixa e processa o mapa LCZ para a cidade informada."""
    clear_lcz_session_data()

    with st.spinner(f"Baixando e processando o mapa LCZ de {cidade_nome}... (pode levar 1-2 minutos)"):
        try:
            from utils.lcz4r import GeocodeError, DataProcessingError

            data, profile, cached_raster_path = lcz_get_map(cidade_nome, isave_map=False, return_path=True)
            lcz_gdf = process_lcz_map(data, profile)
            enhanced_gdf = enhance_lcz_data(lcz_gdf)

            save_lcz_data_to_session(data, profile, cidade_nome, enhanced_gdf, raster_path=cached_raster_path)

        except GeocodeError as e:
            st.session_state.lcz_error_message = (
                f"Não encontramos a cidade \"{cidade_nome}\". Tente o nome completo com o país "
                f"(ex.: \"{cidade_nome}, Brazil\")."
            )
        except (DataProcessingError, ConnectionError) as e:
            st.session_state.lcz_error_message = str(e)
        except Exception as e:
            st.session_state.lcz_error_message = f"Erro inesperado ao gerar o mapa: {e}"

    st.rerun()


def renderizar_aba_mapa():
    """Mapa LCZ: visão geral (Plotly) + exploração por clique (MapLibre)."""
    data = st.session_state.lcz_raster_data
    profile = st.session_state.lcz_raster_profile
    cidade = st.session_state.lcz_city_name or "Cidade"

    resultado = lcz_plot_map((data, profile), title=f"Zonas Climáticas Locais — {cidade}", isave=False)
    # LCZ4py entrega a legenda em fonte pequena (13-14px); aumentamos aqui para
    # ficar legível no tamanho em que o gráfico é exibido na plataforma.
    resultado.fig.update_layout(
        legend=dict(font=dict(size=15), title=dict(font=dict(size=16))),
    )
    st.plotly_chart(resultado.fig, use_container_width=True)

    with st.expander("⬇️ Baixar dados do mapa"):
        col1, col2 = st.columns(2)
        with col1:
            # Só exporta a imagem via Kaleido (headless browser, ~15-20s) quando
            # pedido — gerá-la a cada rerun do script (inclusive ao trocar de
            # aba) deixaria a página pesada sem necessidade.
            if st.button("📸 Gerar imagem PNG"):
                png_data = resultado.fig.to_image(format="png", scale=2)
                st.download_button("⬇️ Baixar Imagem PNG", png_data, f"lcz_map_{cidade}.png", "image/png",
                                    use_container_width=True)
        with col2:
            geojson_data = st.session_state.lcz_data.to_json()
            st.download_button("🗺️ GeoJSON", geojson_data, f"lcz_data_{cidade}.geojson", "application/json",
                                use_container_width=True)

    st.markdown("##### Explore por classe")
    st.caption("Clique em um polígono para entender a classe LCZ, o aquecimento esperado e as ações de mitigação. Áreas sem classificação ficam transparentes.")
    renderizar_mapa_maplibre()


def renderizar_mapa_maplibre():
    """Mapa MapLibre com OpenFreeMap e camada LCZ clicável."""
    gdf_lcz = st.session_state.lcz_data
    if gdf_lcz is None or gdf_lcz.empty:
        return
    geojson = json.dumps(json.loads(gdf_lcz.to_json()), ensure_ascii=False).replace("</", "<\\/")
    colors = json.dumps(CORES_LCZ)
    styles = {
        "Positron": "https://tiles.openfreemap.org/styles/positron",
        "Liberty": "https://tiles.openfreemap.org/styles/liberty",
        "Bright": "https://tiles.openfreemap.org/styles/bright",
        "Dark": "https://tiles.openfreemap.org/styles/dark",
        "Fiord": "https://tiles.openfreemap.org/styles/fiord",
        # O OpenFreeMap implementa o modo 3D com Liberty + câmera inclinada;
        # não há um endpoint /styles/3d separado.
        "3D": "https://tiles.openfreemap.org/styles/liberty",
    }
    options = "".join(
        f'<option value="{url}"{(" data-mode=3d selected" if name == "3D" else "")}>{name}</option>'
        for name, url in styles.items()
    )
    html = f'''<!doctype html><html lang="pt-BR"><head>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<style>
* {{ box-sizing:border-box }} body {{ margin:0; font-family:Arial,sans-serif; overflow:hidden }} #map {{ height:570px; width:100%; background:#e7eff2 }}
.toolbar {{ position:absolute; z-index:3; top:12px; left:12px; right:12px; display:flex; gap:8px; flex-wrap:wrap }}
.toolbar label,.toolbar button {{ background:rgba(255,255,255,.95); border:1px solid #cbd5e1; border-radius:7px; padding:8px 10px; box-shadow:0 2px 8px #0f172a22; font-size:12px }}
.toolbar select {{ border:0; background:transparent; font-weight:700; color:#163044 }} .toolbar button {{ cursor:pointer; font-weight:700 }}
.layers {{ position:absolute; z-index:4; top:54px; right:12px; width:min(270px,calc(100% - 24px)); max-height:420px; overflow:auto; padding:12px; display:none; background:#fff; border:1px solid #cbd5e1; border-radius:8px; box-shadow:0 3px 14px #0f172a2b }}
.layers.open {{ display:block }} .layers h3 {{ margin:0 0 8px; font-size:13px }} .layer {{ display:flex; gap:7px; padding:4px 0; font-size:11px }}
.maplibregl-popup-content {{ width:310px; max-width:calc(100vw - 44px); font-size:12px; line-height:1.45 }} .maplibregl-popup-content h3 {{ color:#0f766e; margin:0 0 8px }} .popup-label {{ display:block; margin-top:7px; color:#475569; font-weight:700; font-size:11px }}
@media (max-width:650px) {{ #map {{ height:620px }} }}
</style></head><body><div id="map"></div>
<div class="toolbar"><label>Estilo <select id="style">{options}</select></label><label>Transparência <input id="opacity" type="range" min="0" max="100" value="76" step="1" aria-label="Transparência da camada LCZ"><output id="opacity-value">76%</output></label><button id="layer-button">Camadas</button><button id="reset">Recentrar</button></div>
<div id="layers" class="layers"><h3>Camadas do estilo ativo</h3><div id="layer-list"></div></div>
<script>
const data={geojson}; const colors={colors}; let hoveredId=null; let lczOpacity=.76; const map=new maplibregl.Map({{container:'map',style:'{styles['Liberty']}',center:[-46.63,-23.55],zoom:10,pitch:60,bearing:55}}); map.addControl(new maplibregl.NavigationControl({{visualizePitch:true}}),'bottom-right'); map.dragRotate.enable();
function bounds(){{const b=new maplibregl.LngLatBounds(); const walk=c=>Array.isArray(c[0])?c.forEach(walk):b.extend(c); data.features.forEach(f=>walk(f.geometry.coordinates)); return b;}}
function safe(v){{return String(v||'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
function popup(e){{const p=e.features[0].properties||{{}};const title=safe(p.zcl_classe||'Zona LCZ');const html='<h3>'+title+'</h3>'+'<span class="popup-label">O que é</span><div>'+safe(p.descricao||'Descrição não disponível para esta área.')+'</div>'+'<span class="popup-label">O que esperar</span><div>'+safe(p.efeito_temp||'Efeito térmico não disponível para esta área.')+'</div>'+'<span class="popup-label">Contribuição para a ilha de calor</span><div>'+safe(p.ilha_calor||'Informação não disponível para esta área.')+'</div>'+'<span class="popup-label">Como atuar</span><div>'+safe(p.intervencao||'Consulte dados locais antes de propor uma intervenção.')+'</div>';new maplibregl.Popup().setLngLat(e.lngLat).setHTML(html).addTo(map);}}
function overlay(){{['lcz-fill','lcz-line'].forEach(id=>{{if(map.getLayer(id))map.removeLayer(id);}});if(map.getSource('lcz'))map.removeSource('lcz');map.addSource('lcz',{{type:'geojson',data,generateId:true}});const noClass=['==',['get','zcl_classe'],null];const color=['case',noClass,'rgba(0,0,0,0)',['match',['get','zcl_classe'],...Object.entries(colors).flat(),'rgba(0,0,0,0)']];map.addLayer({{id:'lcz-fill',type:'fill',source:'lcz',paint:{{'fill-color':color,'fill-opacity':['case',noClass,0,lczOpacity]}}}});map.addLayer({{id:'lcz-line',type:'line',source:'lcz',paint:{{'line-color':'#163044','line-opacity':['case',noClass,0,Math.min(.7,lczOpacity+.1)],'line-width':['case',['boolean',['feature-state','hover'],false],2.4,.65]}}}});map.on('click','lcz-fill',popup);map.on('mouseenter','lcz-fill',e=>{{map.getCanvas().style.cursor='pointer';if(hoveredId!==null)map.setFeatureState({{source:'lcz',id:hoveredId}},{{hover:false}});hoveredId=e.features[0].id;map.setFeatureState({{source:'lcz',id:hoveredId}},{{hover:true}});}});map.on('mouseleave','lcz-fill',()=>{{map.getCanvas().style.cursor='';if(hoveredId!==null)map.setFeatureState({{source:'lcz',id:hoveredId}},{{hover:false}});hoveredId=null;}});map.fitBounds(bounds(),{{padding:35,maxZoom:13,duration:500}});}}
function layers(){{const list=document.getElementById('layer-list');list.innerHTML='';(map.getStyle().layers||[]).forEach(layer=>{{if(['lcz-fill','lcz-line'].includes(layer.id))return;const row=document.createElement('label');row.className='layer';const input=document.createElement('input');input.type='checkbox';input.checked=map.getLayoutProperty(layer.id,'visibility')!=='none';input.onchange=()=>map.setLayoutProperty(layer.id,'visibility',input.checked?'visible':'none');row.append(input,document.createTextNode(layer.id));list.append(row);}});}}
map.on('load',()=>{{overlay();layers();}}); function change(url,is3d){{map.setStyle(url);map.dragRotate[is3d?'enable':'disable']();map.once('idle',()=>{{overlay();layers();}});map.once('style.load',()=>map.easeTo({{pitch:is3d?60:0,bearing:is3d?55:0,duration:700}}));}}
document.getElementById('style').onchange=e=>change(e.target.value,e.target.selectedOptions[0].dataset.mode==='3d');document.getElementById('opacity').oninput=e=>{{lczOpacity=Number(e.target.value)/100;document.getElementById('opacity-value').textContent=e.target.value+'%';if(map.getLayer('lcz-fill'))map.setPaintProperty('lcz-fill','fill-opacity',['case',['==',['get','zcl_classe'],null],0,lczOpacity]);if(map.getLayer('lcz-line'))map.setPaintProperty('lcz-line','line-opacity',['case',['==',['get','zcl_classe'],null],0,Math.min(.7,lczOpacity+.1)]);}};document.getElementById('layer-button').onclick=()=>document.getElementById('layers').classList.toggle('open');document.getElementById('reset').onclick=()=>map.fitBounds(bounds(),{{padding:35,maxZoom:13,duration:500}});
</script></body></html>'''
    components.html(html, height=640, scrolling=False)


def renderizar_aba_area():
    """Estatísticas e gráfico de distribuição de área por classe LCZ."""
    if st.session_state.lcz_area_stats is None:
        with st.spinner("Calculando área por classe..."):
            from utils.lcz4r import lcz_cal_area
            resultado = lcz_cal_area(st.session_state.lcz_data, raster_path=st.session_state.lcz_raster_path)
            st.session_state.lcz_area_stats = resultado['stats']
            st.session_state.lcz_plot_data = resultado['plot_data']
            st.session_state.lcz_area_summary = resultado['summary']

    area_stats = st.session_state.lcz_area_stats
    summary = st.session_state.lcz_area_summary

    urbano = area_stats[area_stats['zcl_classe'].str.contains('LCZ [1-9]|LCZ 10')]['area_total_km2'].sum()
    natural = area_stats[area_stats['zcl_classe'].str.contains('LCZ [A-G]')]['area_total_km2'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Área total", f"{summary['total_area_km2']:.1f} km²")
    col2.metric("Classe dominante", summary['classe_dominante'],
                f"{summary['percentual_classe_dominante']:.1f}%")
    col3.metric("Área construída (LCZ 1-10)", f"{urbano / summary['total_area_km2'] * 100:.0f}%",
                help=f"{urbano:.1f} km² construídos vs. {natural:.1f} km² de cobertura de terreno (LCZ A-G)")

    fig = px.bar(
        area_stats.sort_values('area_total_km2', ascending=True),
        x='area_total_km2', y='zcl_classe', orientation='h',
        color='zcl_classe', color_discrete_map=CORES_LCZ,
        labels={'area_total_km2': 'Área total (km²)', 'zcl_classe': 'Classe LCZ'},
    )
    fig.update_layout(showlegend=False, height=500, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Tabela e mais opções"):
        st.dataframe(
            area_stats[['zcl_classe', 'area_total_km2', 'percentual']].rename(columns={
                'zcl_classe': 'Classe LCZ', 'area_total_km2': 'Área total (km²)', 'percentual': 'Percentual (%)',
            }),
            use_container_width=True, hide_index=True,
        )
        st.download_button("📊 Baixar dados (CSV)", area_stats.to_csv(index=False),
                            f"lcz_area_{st.session_state.lcz_city_name}.csv", "text/csv")


def _mapa_grade_media(array, titulo, colorscale, unidade):
    """Heatmap Plotly leve (sem dependências extras) da média espacial de uma
    grade (n_bandas, altura, largura), usada para LST e poluição do ar."""
    media = np.nanmean(array, axis=0)
    fig = go.Figure(go.Heatmap(z=media, colorscale=colorscale, colorbar_title=unidade))
    fig.update_layout(title=titulo, height=420, yaxis=dict(scaleanchor='x'), margin=dict(t=40, b=10))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange='reversed')
    st.plotly_chart(fig, use_container_width=True)
    return media


def renderizar_aba_temperatura_superficie():
    """Temperatura de Superfície (LST) por satélite — recorte da área do mapa."""
    st.markdown(
        "A **Temperatura de Superfície (LST)** é a temperatura que um satélite mede olhando para "
        "o topo dos telhados, ruas e copas das árvores. É diferente da temperatura do ar que sentimos, "
        "e costuma ser mais alta nas classes LCZ mais construídas e compactas."
    )

    if st.session_state.lcz_lst_result is None:
        st.caption(
            "Baixa 3 dias recentes de imagens de satélite (Sentinel-3) recortadas na área do mapa. "
            "São poucos MB, mas pode levar 1-2 minutos (cada dia é baixado separadamente)."
        )
        if st.button("🌡️ Carregar temperatura de superfície"):
            with st.spinner("Baixando imagens de satélite..."):
                try:
                    from utils.lcz4r import lcz_get_lst
                    st.session_state.lcz_lst_result = lcz_get_lst(st.session_state.lcz_raster_path)
                except Exception as e:
                    st.error(f"Não foi possível baixar a temperatura de superfície: {e}")
        return

    resultado = st.session_state.lcz_lst_result
    cidade = st.session_state.lcz_city_name or "Cidade"
    media = _mapa_grade_media(
        resultado.array, f"LST média ({resultado.dates[0]} a {resultado.dates[-1]}) — {cidade}",
        colorscale="RdYlBu_r", unidade="°C",
    )
    col1, col2 = st.columns(2)
    col1.metric("Área mais fria", f"{np.nanmin(media):.1f} °C")
    col2.metric("Área mais quente", f"{np.nanmax(media):.1f} °C")
    st.caption(
        "Compare este mapa com a aba **Mapa**: as áreas mais quentes tendem a coincidir com classes "
        "LCZ compactas (1-3) e as mais frias, com árvores e vegetação (A-D)."
    )


def renderizar_aba_qualidade_ar():
    """Qualidade do ar (PM2.5/O3/CO) — grade anual recortada na área do mapa."""
    st.markdown(
        "Zonas com mais construções e tráfego tendem a concentrar mais poluentes do ar. "
        "O **PM2.5** (partículas finas) é o poluente mais associado a problemas respiratórios."
    )

    poluente_label = st.radio(
        "Poluente", ["PM2.5", "Ozônio (O₃)", "Monóxido de carbono (CO)"], horizontal=True,
    )
    poluente = {"PM2.5": "pm25", "Ozônio (O₃)": "o3", "Monóxido de carbono (CO)": "co"}[poluente_label]

    if st.session_state.lcz_pollution_result is None or st.session_state.lcz_pollution_poluente != poluente:
        st.caption("Baixa 1 grade anual (dataset GHAP, sem necessidade de conta/API key) recortada na área do mapa.")
        if st.button("🏭 Carregar qualidade do ar"):
            with st.spinner("Baixando grade de poluição..."):
                try:
                    from utils.lcz4r import lcz_grid_poluicao
                    st.session_state.lcz_pollution_result = lcz_grid_poluicao(
                        st.session_state.lcz_raster_path, poluente=poluente
                    )
                    st.session_state.lcz_pollution_poluente = poluente
                except Exception as e:
                    st.error(f"Não foi possível baixar a qualidade do ar: {e}")
        return

    resultado = st.session_state.lcz_pollution_result
    cidade = st.session_state.lcz_city_name or "Cidade"
    unidade = "µg/m³" if poluente == "pm25" else "ppb"
    media = _mapa_grade_media(
        resultado.array, f"{poluente_label} — média anual — {cidade}", colorscale="Reds", unidade=unidade,
    )

    if poluente == "pm25":
        media_cidade = float(np.nanmean(media))
        col1, col2 = st.columns(2)
        col1.metric("Média da área", f"{media_cidade:.1f} µg/m³")
        col2.metric("Limite anual recomendado pela OMS", "5 µg/m³")
        if media_cidade > 5:
            st.caption(
                f"A média da área está **{media_cidade / 5:.1f}x acima** do limite anual recomendado "
                "pela Organização Mundial da Saúde (5 µg/m³)."
            )
