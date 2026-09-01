# modules/info.py
"""Módulo Informações: sobre o projeto + guia prático completo da plataforma."""

import streamlit as st

from utils.ui import renderizar_cabecalho_modulo
from utils.glossario import renderizar_entenda_dados
from utils.navegacao import ir_para


def renderizar_pagina():
    """Renderiza a página de Informações e o guia prático da plataforma."""

    renderizar_cabecalho_modulo(
        "Informações",
        "Sobre o projeto, base científica e guia prático de uso de cada módulo",
        icone="info"
    )

    st.markdown(
        "Ferramenta educacional para análise de **Ilhas de Calor Urbanas (ICU)** e "
        "**Zonas Climáticas Locais (LCZ)**, voltada a estudantes, professores, "
        "pesquisadores e técnicos municipais de Geografia e planejamento urbano."
    )

    st.markdown("""
![Versão](https://img.shields.io/badge/versão-3.0-teal)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.49+-blue)
![Licença](https://img.shields.io/badge/licença-MIT-yellow)
""")

    _renderizar_guia_pratico()
    _renderizar_aplicacoes_educacionais()
    _renderizar_sobre_projeto()


def _botao_abrir(pagina_destino: str, key: str):
    """Atalho de navegação direto para um módulo, a partir do guia."""
    if st.button(f"↪️ Abrir {pagina_destino}", key=key):
        ir_para(pagina_destino)


def _renderizar_guia_pratico():
    with st.expander("📖 Guia Prático da Plataforma", expanded=True):
        st.markdown(
            "Este guia cobre as funções de cada módulo, na ordem em que normalmente "
            "são usadas: Início → Explorar → Investigar → Visualizar → Simular → "
            "Clima de Bairro → Avaliar Plataforma."
        )

        st.markdown("---")
        st.markdown("### 🏠 Início")
        st.markdown(
            "Página de apresentação da plataforma, com conceitos fundamentais (glossário), "
            "cartões dos módulos disponíveis e créditos dos desenvolvedores."
        )
        _botao_abrir("Início", "abrir_inicio")

        st.markdown("---")
        st.markdown("### 🌍 Explorar — mapas de Zonas Climáticas Locais")
        st.markdown("""
Gera o mapa LCZ de qualquer cidade do mundo, a partir do produto global do
LCZ4r/LCZ4py, e permite explorar sua composição.

Digite o nome de uma cidade (ex.: `São Paulo, Brazil`) e clique em **🚀 Gerar
Mapa LCZ**. O processamento busca a fronteira da cidade, recorta o mapa LCZ
global e classifica a área; leva de segundos a poucos minutos, dependendo do
tamanho da cidade e do cache.

Depois de gerado, o mapa aparece em quatro abas:
- **Mapa** mostra a classificação com a paleta padrão do LCZ (1–10 tipos
  construídos, A–G tipos de cobertura de terreno) e um mapa Folium clicável,
  onde cada polígono mostra descrição, efeito térmico e uma sugestão genérica
  de intervenção (sempre com o aviso de que é um mapa global, não validado
  localmente).
- **Área por Classe** mostra a distribuição de área por classe LCZ.
- **Temperatura de Superfície** baixa uma pequena série de imagens de satélite
  (Sentinel-3) e mostra a média espacial na área.
- **Qualidade do Ar** baixa uma grade anual de poluentes (PM2.5, O₃ ou CO) na
  mesma área.

Use nomes completos como `"Rio de Janeiro, Brazil"` ou `"New York, USA"` para
melhorar a geocodificação.
""")
        _botao_abrir("Explorar", "abrir_explorar")

        st.markdown("---")
        st.markdown("### 🔬 Investigar — seus próprios dados de campo")
        st.markdown("""
Conecta dados coletados em campo (temperatura, umidade etc.) com as Zonas
Climáticas Locais de uma área.

Escolha a cidade de referência (afeta qual mapa LCZ é usado no cruzamento e
qual exemplo de CSV fica disponível), carregue uma planilha com colunas de
latitude, longitude e um valor medido, e desenhe no mapa a área de interesse.
A plataforma reconhece nomes de coluna parecidos automaticamente
(`lat`/`latitude`, `lon`/`longitude`, `temp`/`valor`/`medida`) e avisa se
alguma linha tiver dado inválido e precisar ser descartada.

O cruzamento com as LCZ acontece no módulo Visualizar; aqui você só prepara
os dados e a área.
""")
        _botao_abrir("Investigar", "abrir_investigar")

        st.markdown("---")
        st.markdown("### 📊 Visualizar — gráficos e relatório")
        st.markdown("""
Cruza os dados carregados em Investigar com as LCZ e gera estatísticas,
gráficos e um relatório para download, em três abas:

- **Mapa e contexto** mostra a composição de LCZ da área e a distribuição
  espacial dos pontos coletados.
- **Comparar valores** mostra médias, desvios e a distribuição dos valores
  por classe LCZ.
- **Relatório** gera um texto a partir dos números já calculados (classe
  dominante, médias, amplitude), com opção de baixar em Markdown e os dados
  processados em CSV.
""")
        _botao_abrir("Visualizar", "abrir_visualizar")

        st.markdown("---")
        st.markdown("### 🧪 Simular — impacto de intervenções urbanas")
        st.markdown("""
Estima, de forma didática (não é um modelo físico validado), o efeito de
intervenções de mitigação de calor urbano.

Adicione uma ou mais intervenções (Parque Urbano, Alteração de Albedo,
Telhado Verde, Pavimento Permeável, Expansão Urbana), cada uma com seus
próprios parâmetros, desenhe as áreas correspondentes no mapa e execute a
simulação para ver o impacto térmico combinado (ΔT) e uma explicação do
mecanismo de resfriamento ou aquecimento de cada uma. Cenários simulados
ficam salvos no histórico da sessão para comparação, e os resultados podem
ser baixados em CSV ou JSON.
""")
        _botao_abrir("Simular", "abrir_simular")

        st.markdown("---")
        st.markdown("### 🏘️ Clima de Bairro — roteiro guiado escola/comunidade")
        st.markdown("""
Amarra os quatro módulos acima num roteiro de cinco etapas para um estudo de
clima de bairro (ex.: entorno de uma escola), do mapa ao campo e à devolutiva
para a comunidade:

1. **Aproximação pela plataforma** — gerar o mapa LCZ do entorno, em Explorar.
2. **Delimitação do bairro** — desenhar a área de estudo, em Investigar.
3. **Trabalho de campo** — baixar o roteiro de campo pronto para impressão.
4. **Integração dos dados** — subir o CSV de campo e comparar por LCZ.
5. **Percepção, debate e devolutiva** — registrar a percepção da turma ou
   comunidade e gerar um documento de devolutiva combinando os dados
   coletados com os relatos de percepção, em linguagem acessível.

Cada etapa pode ser marcada como concluída, e o progresso fica salvo na sessão.
""")
        _botao_abrir("Clima de Bairro", "abrir_clima_bairro")

        st.markdown("---")
        st.markdown("### 🏆 Avaliar Plataforma")
        st.markdown("""
Formulário de avaliação (perfil do usuário, clareza dos recursos,
navegabilidade, alinhamento pedagógico, linguagem, sugestões livres). As
respostas ficam na sessão atual; baixe o CSV ao final e envie para a equipe
do projeto.
""")
        _botao_abrir("Avaliar plataforma", "abrir_avaliacao")

        renderizar_entenda_dados(titulo="🔍 Glossário completo (todos os termos)")


def _renderizar_aplicacoes_educacionais():
    with st.expander("🎓 Aplicações Educacionais"):
        st.markdown("### Para Professores")
        st.write("- Ferramenta visual para introduzir clima urbano e LCZ em sala de aula")
        st.write("- Base para atividades de investigação com dados reais coletados pelos estudantes")

        st.markdown("### Para Estudantes")
        st.write("- Interface guiada, com glossário e ressalvas de interpretação")
        st.write("- Aprendizado baseado em investigação (ver módulo Clima de Bairro)")

        st.markdown("### Para Pesquisadores e Técnicos Municipais")
        st.write("- Ponto de partida rápido para reconhecer padrões LCZ de uma área")
        st.write(
            "- Atenção: o mapa vem de um produto global automatizado, não validado "
            "localmente. Trate como hipótese de trabalho, não como diagnóstico final"
        )

        st.markdown("### Exemplos de Uso")
        st.write("- Mapeamento de Ilha de Calor de uma cidade")
        st.write("- Estudo de clima de bairro no entorno de uma escola (módulo Clima de Bairro)")
        st.write("- Discussão de intervenções de mitigação (módulo Simular)")


def _renderizar_sobre_projeto():
    with st.expander("ℹ️ Sobre o Projeto"):
        st.markdown("## 🎯 Base Científica")
        st.write(
            "Baseada no sistema de Zonas Climáticas Locais de Stewart & Oke (2012), "
            "no protocolo WUDAPT e no pacote LCZ4r/LCZ4py."
        )

        st.markdown("## 🔧 Tecnologias")
        st.write("Streamlit, GeoPandas, Folium, Plotly, Pandas, Shapely, Rasterio, LCZ4py.")

        st.markdown("**Última atualização:** Agosto 2026  \n**Versão da Plataforma:** 3.0")
