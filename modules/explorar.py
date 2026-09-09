# modules/explorar.py

import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import time
import json

from utils.lcz4r import lcz_get_map, process_lcz_map, enhance_lcz_data, lcz_plot_map, CORES_LCZ


def _suavizar_geometria(geom, distancia):
    """Arredonda os cantos retos do polígono derivado do raster com um buffer
    de fechamento (dilata depois erode, join arredondado) — visualmente suave,
    e como a dilatação e a erosão usam a mesma distância, a área muda pouco
    (testado <1% para `distancia` = meio pixel). Só para exibição — o
    GeoDataFrame de origem (área/estatísticas, download) não é alterado."""
    if geom is None or geom.is_empty:
        return geom
    return geom.buffer(distancia, join_style="round", cap_style="round").buffer(
        -distancia, join_style="round", cap_style="round"
    )


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
        'lcz_ucp_result': None,
        'lcz_ucp_requested': [],
        'lcz_pc_result': None,
        'lcz_indices_result': None,
        'lcz_indices_stats': None,
        'lcz_indices_requested': [],
        'lcz_indices_ano_referencia': None,
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
        aba_mapa, aba_area, aba_ucp, aba_indices = st.tabs([
            "🗺️ Mapa", "📊 Área por Classe", "🏙️ Parâmetros Urbanos", "🌿 Índices Espectrais",
        ])
        with aba_mapa:
            renderizar_aba_mapa()
        with aba_area:
            renderizar_aba_area()
        with aba_ucp:
            renderizar_aba_parametros_urbanos()
        with aba_indices:
            renderizar_aba_indices_espectrais()
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
            # Resolução nativa (~100m) para a maioria das cidades — só agrega
            # (perde detalhe) se o recorte for enorme (ex.: uma metrópole
            # inteira), para não travar a vetorização/dissolve.
            fator_agregacao = 1 if data.size <= 4_000_000 else 3
            lcz_gdf = process_lcz_map(data, profile, factor=fator_agregacao)
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
    st.caption("Fonte: mapa global de LCZ (WUDAPT), obtido e recortado com LCZ4py.")

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
    # Suaviza só a cópia usada neste mapa interativo (Explore por classe) — os
    # dados de origem (área/estatísticas, GeoJSON de download) continuam com
    # os limites exatos do pixel, sem a suavização cosmética. Raio de meio
    # pixel: arredonda os cantos retos sem deformar a forma perceptivelmente.
    raster_profile = st.session_state.lcz_raster_profile
    pixel_deg = abs(raster_profile["transform"].a) if raster_profile else 0.0009
    distancia_suavizacao = pixel_deg * 0.5
    gdf_suave = gdf_lcz.copy()
    gdf_suave["geometry"] = gdf_suave.geometry.apply(
        lambda g: _suavizar_geometria(g, distancia_suavizacao)
    )
    geojson = json.dumps(json.loads(gdf_suave.to_json()), ensure_ascii=False).replace("</", "<\\/")
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
    fig.update_layout(
        title=dict(text=f"Área por classe LCZ — {st.session_state.lcz_city_name or 'Cidade'}"),
        showlegend=False, height=500, margin=dict(t=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Fonte: mapa global de LCZ (WUDAPT); área calculada por contagem de pixels com LCZ4py.")

    with st.expander("📋 Tabela e mais opções"):
        st.dataframe(
            area_stats[['zcl_classe', 'area_total_km2', 'percentual']].rename(columns={
                'zcl_classe': 'Classe LCZ', 'area_total_km2': 'Área total (km²)', 'percentual': 'Percentual (%)',
            }),
            use_container_width=True, hide_index=True,
        )
        st.download_button("📊 Baixar dados (CSV)", area_stats.to_csv(index=False),
                            f"lcz_area_{st.session_state.lcz_city_name}.csv", "text/csv")

def renderizar_aba_parametros_urbanos():
    """Parâmetros Urbanos de Superfície (UCP) — morfologia da cidade que explica o efeito de cada classe LCZ."""
    from utils.lcz4r import (
        UCP_DESCRICOES, UCP_FONTE_CATEGORIA, UCP_CATEGORIA, UCP_INTERPRETACAO,
        UCP_ESTIMADO_LCZ_DESCRICAO, UCP_ESTIMADO_LCZ_PADRAO,
        lcz_get_parametros_lcz_estimados,
    )

    st.markdown(
        "As classes LCZ descrevem o **padrão** da paisagem urbana; os **Parâmetros Urbanos de Superfície "
        "(UCP)** medem diretamente os fatores físicos por trás do aquecimento — altura das edificações, "
        "quanto solo está impermeabilizado, cobertura arbórea, densidade populacional, entre outros."
    )

    fonte_modo = st.radio(
        "Fonte dos parâmetros",
        ["Estimativa rápida por LCZ", "Camadas globais externas"],
        horizontal=True,
        help=(
            "A estimativa rápida usa apenas o mapa LCZ já carregado. As camadas globais externas "
            "baixam dados GHSL/WUMPOD/vegetação e podem falhar no Streamlit Cloud."
        ),
    )

    if fonte_modo == "Estimativa rápida por LCZ":
        opcoes_estimadas = [v for v in UCP_ESTIMADO_LCZ_PADRAO if v in UCP_DESCRICOES]
        variavel = st.selectbox(
            "Parâmetro urbano a visualizar", opcoes_estimadas,
            format_func=lambda v: f"{v} — {UCP_DESCRICOES[v].split(' — ')[0]}",
        )
        resultado = lcz_get_parametros_lcz_estimados(
            st.session_state.lcz_raster_data,
            st.session_state.lcz_raster_profile,
            variables=opcoes_estimadas,
        )
        st.caption(UCP_ESTIMADO_LCZ_DESCRICAO)
    else:
        st.markdown("##### Escolha poucos parâmetros por tentativa")
        opcoes = list(UCP_DESCRICOES.keys())
        selecionados = st.multiselect(
            "Parâmetros urbanos", opcoes,
            default=["built_hei"],
            format_func=lambda v: f"{v} — {UCP_DESCRICOES[v].split(' — ')[0]}",
            label_visibility="collapsed",
        )
        for item in selecionados:
            st.caption(f"**{item}** — {UCP_DESCRICOES[item]}")

        st.caption(
            "Este modo baixa camadas globais recortadas na área do mapa. No Streamlit Cloud, "
            "prefira um grupo por vez: GHSL, WUMPOD ou vegetação."
        )
        if any(item in {"built_hei", "built_sur", "built_vol", "pop"} for item in selecionados):
            st.caption(
                "Altura, superfície e volume construído e população vêm do mesmo conjunto GHSL; "
                "ao escolher um deles, outros do mesmo pacote podem ficar disponíveis."
            )
        if st.button("🏙️ Carregar camadas globais", disabled=not selecionados):
            with st.spinner("Baixando e processando camadas globais..."):
                try:
                    from utils.lcz4r import lcz_get_parametros_urbanos
                    st.session_state.lcz_ucp_requested = selecionados
                    st.session_state.lcz_ucp_result = lcz_get_parametros_urbanos(
                        st.session_state.lcz_raster_path, variables=selecionados
                    )
                except Exception as e:
                    st.session_state.lcz_ucp_result = None
                    st.error(
                        "Não foi possível baixar as camadas globais agora. "
                        f"A estimativa rápida por LCZ continua disponível. Detalhe: {e}"
                    )

        if st.session_state.lcz_ucp_result is None:
            st.info("Carregue uma camada global acima ou volte para a estimativa rápida por LCZ.")
            return

        resultado = st.session_state.lcz_ucp_result
        variaveis = resultado["variable_list"]
        if not variaveis:
            st.warning("Nenhum parâmetro urbano ficou disponível para esta área.")
            return

        solicitados = st.session_state.get("lcz_ucp_requested") or variaveis
        disponiveis_solicitados = [v for v in solicitados if v in variaveis]
        extras_disponiveis = [v for v in variaveis if v not in solicitados]
        indisponiveis = [v for v in solicitados if v not in variaveis]

        st.success(
            f"{len(variaveis)} camada(s) urbana(s) disponíveis. "
            f"{len(disponiveis_solicitados)} de {len(solicitados)} parâmetro(s) selecionado(s) foram carregados."
        )
        if extras_disponiveis:
            st.caption(
                "Também ficaram disponíveis por serem baixados no mesmo pacote de fonte: "
                f"{', '.join(extras_disponiveis)}."
            )
        if indisponiveis:
            st.warning(
                "Alguns parâmetros selecionados não retornaram no processamento: "
                f"{', '.join(indisponiveis)}. Tente escolher menos grupos de fonte ou repetir o download."
            )

        falhas = resultado.get("failed_variables") or []
        falhas_usuario = [(nome, erro) for nome, erro in falhas if nome != "chamada_completa"]
        falhas_nomes = {nome for nome, _ in falhas_usuario}
        if falhas_usuario:
            st.caption(
                f"{len(falhas_usuario)} parâmetro(s) não puderam ser baixados para esta área "
                f"({', '.join(falhas_nomes)}) — provavelmente instabilidade na fonte de dados. "
                "Os demais abaixo carregaram normalmente."
            )

        variaveis_plotaveis = [v for v in variaveis if v not in falhas_nomes] or variaveis

        col1, col2 = st.columns([4, 1])
        with col1:
            variavel = st.selectbox(
                "Parâmetro urbano a visualizar", variaveis_plotaveis,
                format_func=lambda v: f"{v} — {UCP_DESCRICOES[v].split(' — ')[0]}" if v in UCP_DESCRICOES else v,
            )
        with col2:
            st.write("")
            if st.button("🔄 Escolher outros", use_container_width=True):
                st.session_state.lcz_ucp_result = None
                st.rerun()
        st.caption(f"Fonte da camada: {UCP_FONTE_CATEGORIA.get(UCP_CATEGORIA.get(variavel), 'LCZ4py')}.")

    variaveis = resultado["variable_list"]
    if not variaveis:
        st.warning("Nenhum parâmetro urbano ficou disponível para esta área.")
        return

    st.caption(UCP_DESCRICOES.get(variavel, "Descrição não disponível para este parâmetro."))

    try:
        with st.spinner("Gerando mapa..."):
            from utils.lcz4r import lcz_plot_parametro_urbano
            fig = lcz_plot_parametro_urbano(resultado, variavel)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(
            f"Não foi possível gerar o mapa de **{variavel}**: {e}. Tente escolher outro parâmetro "
            "ou clique em \"Escolher outros\" para baixar novamente."
        )
        return

    if variavel in UCP_INTERPRETACAO:
        st.info(f"Leitura didática: {UCP_INTERPRETACAO[variavel]}")

    st.caption(
        "Compare este mapa com a aba **Mapa**: os parâmetros mais associados a calor "
        "(altura/volume construído, superfície construída) tendem a coincidir com as classes LCZ "
        "compactas (1-3), enquanto cobertura arbórea e fração urbana baixa coincidem com as classes "
        "de vegetação (A-D)."
    )

    with st.expander("⬇️ Baixar esta camada"):
        col_tif, col_png = st.columns(2)
        cidade_arquivo = (st.session_state.lcz_city_name or "cidade").lower().replace(" ", "_")
        with col_tif:
            try:
                import io
                buf_tif = io.BytesIO()
                resultado["combined_rasters"][variavel].rio.to_raster(buf_tif, driver="GTiff")
                st.download_button(
                    "🗺️ GeoTIFF", buf_tif.getvalue(),
                    f"ucp_{variavel}_{cidade_arquivo}.tif", "image/tiff",
                    use_container_width=True,
                )
            except Exception as e:
                st.caption(f"GeoTIFF indisponível: {e}")
        with col_png:
            if st.button("📸 Gerar PNG", use_container_width=True):
                png_data = fig.to_image(format="png", scale=2)
                st.download_button(
                    "⬇️ Baixar PNG", png_data,
                    f"ucp_{variavel}_{cidade_arquivo}.png", "image/png",
                    use_container_width=True,
                )


def renderizar_aba_indices_espectrais():
    """Índices espectrais por satélite, escolhidos pelo usuário e comparados entre classes LCZ."""
    from utils.lcz4r import (
        INDICES_ESPECTRAIS_DESCRICOES,
        INDICES_ESPECTRAIS_FONTE,
        INDICES_ESPECTRAIS_PADRAO,
        INDICES_ESPECTRAIS_TEMA,
    )

    st.markdown(
        "**Índices espectrais** combinam bandas de satélite (Sentinel-2) em um único número por pixel "
        "para destacar vegetação, água ou área construída. Comparados por classe LCZ, mostram *por que* "
        "algumas áreas aquecem mais: menos vegetação (NDVI baixo) e mais construção (NDBI alto) tendem a "
        "andar juntos com temperaturas mais altas."
    )

    if st.session_state.lcz_indices_stats is None:
        st.markdown("##### Escolha os índices que quer calcular")
        opcoes = list(INDICES_ESPECTRAIS_DESCRICOES.keys())
        selecionados = st.multiselect(
            "Índices espectrais", opcoes, default=INDICES_ESPECTRAIS_PADRAO,
            format_func=lambda i: f"{i} — {INDICES_ESPECTRAIS_DESCRICOES[i].split(' — ')[0]}",
            label_visibility="collapsed",
        )
        for indice in selecionados:
            st.caption(f"**{indice}** — {INDICES_ESPECTRAIS_DESCRICOES[indice]}")

        from utils.lcz4r import LCZ_ANO_REFERENCIA_GLOBAL

        st.caption(
            f"Busca imagens do Sentinel-2 de **{LCZ_ANO_REFERENCIA_GLOBAL}** (poucas nuvens), recortadas na "
            "área do mapa, e calcula os índices escolhidos. Esse é o ano de referência do mapa global de "
            "LCZ (WUDAPT/Demuzere et al., 2022) usado nesta plataforma — comparar direto com uma imagem de "
            "hoje misturaria uma classificação de 2018 com cobertura do solo atual, sem dizer isso. Pode "
            "levar 1-2 minutos."
        )
        usar_recente = st.checkbox(
            "Usar imagens recentes (últimos 90 dias) em vez do ano de referência",
            value=False,
            help="Ignora o alinhamento com o ano do mapa LCZ e busca as imagens mais atuais disponíveis — "
                 "útil para comparar com a condição de hoje, mas a comparação com as classes LCZ deixa de "
                 "ser temporalmente coerente.",
        )
        if st.button("🌿 Carregar índices espectrais", disabled=not selecionados):
            with st.spinner("Baixando imagens de satélite e calculando índices..."):
                try:
                    from utils.lcz4r import (
                        lcz_baixar_sentinel2, lcz_calcular_indices, lcz_estatisticas_indices,
                    )
                    st.session_state.lcz_indices_requested = selecionados
                    ano_ref = None if usar_recente else LCZ_ANO_REFERENCIA_GLOBAL
                    pc_result = lcz_baixar_sentinel2(st.session_state.lcz_raster_path, ano_referencia=ano_ref)
                    indices_result = lcz_calcular_indices(pc_result, indices=selecionados)
                    st.session_state.lcz_pc_result = pc_result
                    st.session_state.lcz_indices_result = indices_result
                    st.session_state.lcz_indices_ano_referencia = ano_ref
                    st.session_state.lcz_indices_stats = lcz_estatisticas_indices(
                        st.session_state.lcz_raster_path, indices_result
                    )
                except Exception as e:
                    st.error(
                        f"Não foi possível calcular os índices espectrais: {e}. "
                        "Isso costuma acontecer quando não há imagens do Sentinel-2 com poucas nuvens "
                        "recentes para esta área — tente novamente mais tarde."
                    )
        return

    stats = st.session_state.lcz_indices_stats
    if st.button("🔄 Escolher outros índices"):
        st.session_state.lcz_indices_stats = None
        st.session_state.lcz_indices_result = None
        st.session_state.lcz_pc_result = None
        st.session_state.lcz_indices_requested = []
        st.rerun()

    tabela = stats.df
    if hasattr(tabela, "to_pandas"):
        tabela = tabela.to_pandas()

    solicitados = st.session_state.get("lcz_indices_requested") or INDICES_ESPECTRAIS_PADRAO
    colunas_indice = [c for c in tabela.columns if str(c).lower() in {"indice", "index", "indices", "variable", "variavel"}]
    if colunas_indice:
        indices_disponiveis = sorted(set(tabela[colunas_indice[0]].dropna().astype(str)))
    else:
        indices_disponiveis = [i for i in solicitados if i in str(stats.fig)]
    indisponiveis = [i for i in solicitados if i not in indices_disponiveis]

    temas = sorted({INDICES_ESPECTRAIS_TEMA.get(i, "Outro") for i in indices_disponiveis})
    st.success(
        f"{len(indices_disponiveis)} índice(s) espectral(is) calculado(s): "
        f"{', '.join(indices_disponiveis) if indices_disponiveis else 'nenhum'}."
    )
    if temas:
        st.caption(f"Temas cobertos: {', '.join(temas)}.")
    ano_usado = st.session_state.get("lcz_indices_ano_referencia")
    if ano_usado:
        st.caption(
            f"📅 Imagens buscadas em **{ano_usado}** — ano de referência do mapa global de LCZ, "
            "para manter a comparação temporalmente coerente com a classificação."
        )
    else:
        st.caption(
            "📅 Imagens recentes (últimos 90 dias), não alinhadas ao ano de referência do mapa LCZ "
            "(2018) — a comparação com as classes LCZ não é temporalmente coerente neste modo."
        )
    if indisponiveis:
        st.warning(
            "Alguns índices selecionados não apareceram no resultado final: "
            f"{', '.join(indisponiveis)}. Isso pode indicar falta de banda, nuvem, ou ausência de pixels válidos."
        )
    st.caption(f"Fonte dos dados: {INDICES_ESPECTRAIS_FONTE}")

    st.plotly_chart(stats.fig, use_container_width=True)

    st.markdown(
        "Cada caixa mostra a distribuição do índice dentro de uma classe LCZ: a linha central é a mediana, "
        "a caixa cobre a metade central dos valores (quartis), os pontos representam pixels amostrados e "
        "as cores seguem a paleta LCZ. Use NDVI/SAVI para vegetação, NDBI/UI para construção, MNDWI para água "
        "e BSI para solo exposto."
    )

    with st.expander("📋 Tabela e mais opções"):
        st.dataframe(tabela, use_container_width=True, hide_index=True)
        cidade_arquivo = (st.session_state.lcz_city_name or "cidade").lower().replace(" ", "_")
        col_csv, col_tif, col_png = st.columns(3)
        with col_csv:
            st.download_button(
                "📊 Estatísticas (CSV)", tabela.to_csv(index=False),
                f"lcz_indices_{cidade_arquivo}.csv", "text/csv",
                use_container_width=True,
            )
        with col_tif:
            indices_path = st.session_state.lcz_indices_result.path if st.session_state.lcz_indices_result else None
            if indices_path:
                try:
                    with open(indices_path, "rb") as f:
                        st.download_button(
                            "🗺️ Índices (GeoTIFF)", f.read(),
                            f"lcz_indices_{cidade_arquivo}.tif", "image/tiff",
                            use_container_width=True,
                            help="Multibanda — uma banda por índice calculado.",
                        )
                except OSError as e:
                    st.caption(f"GeoTIFF indisponível: {e}")
        with col_png:
            if st.button("📸 Gerar PNG (boxplot)", use_container_width=True):
                png_data = stats.fig.to_image(format="png", scale=2)
                st.download_button(
                    "⬇️ Baixar PNG", png_data,
                    f"lcz_indices_{cidade_arquivo}.png", "image/png",
                    use_container_width=True,
                )
