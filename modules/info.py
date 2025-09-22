import streamlit as st

def renderizar_pagina():
    st.markdown("# 🌍 Plataforma Clima Urbano Interativo", unsafe_allow_html=True)
    st.markdown("Uma ferramenta educacional moderna e interativa para análise de **Ilhas de Calor Urbanas (ICU)** e **Zonas Climáticas Locais (ZCL)**, desenvolvida para estudantes e pesquisadores de Geografia.")
    
    # Badges
    st.markdown("""
![Versão](https://img.shields.io/badge/versão-2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.49+-red)
![Licença](https://img.shields.io/badge/licença-MIT-yellow)
""")
    
    # Sub-seção: Manual
    with st.expander("📖 Manual do Usuário"):
        st.markdown("## 🚀 Primeiros Passos")
        st.markdown("""
1. Abra seu navegador
2. Acesse a URL da plataforma
3. Página inicial será carregada
        """)
        
        st.markdown("## 🌍 Módulo Explorar")
        st.markdown("""
- Visualização de mapas de ZCL e temperatura
- Camadas sobrepostas de dados geoespaciais
- Zoom, pan e tooltips interativos
        """)
        
        st.markdown("## 🔬 Módulo Investigar")
        st.markdown("""
- Upload de dados CSV
- Ferramenta de desenho de áreas de interesse
- Processamento em tempo real
        """)
        
        st.markdown("## 📊 Módulo Visualizar")
        st.markdown("""
- Gráficos interativos
- Estatísticas por zona climática
- Relatórios automáticos
        """)
        
        st.markdown("## 📞 Suporte")
        st.markdown("""
- Email: contato@exemplo.com
- GitHub Issues no repositório
        """)

    # Sub-seção: Aplicações
    with st.expander("🎓 Aplicações Educacionais"):
        st.markdown("### Para Professores")
        st.write("- Ferramenta visual e interativa")
        st.write("- Exercícios práticos com dados reais")
        
        st.markdown("### Para Estudantes")
        st.write("- Interface moderna")
        st.write("- Aprendizado baseado em projetos")
        
        st.markdown("### Para Pesquisadores")
        st.write("- Validação de metodologias")
        st.write("- Visualização de resultados preliminares")
        
        st.markdown("### Exemplos de Uso")
        st.write("- Estudo de caso: São Paulo")
        st.write("- Projetos sugeridos: Mapeamento de Ilha de Calor, Análise de Bairro, Impacto da Vegetação, Planejamento Urbano")

    # Sub-seção: Sobre / Mais informações
    with st.expander("ℹ️ Mais Informações"):
        st.markdown("## 🎯 Sobre o Projeto")
        st.write("Baseada no software LCZ4r, Stewart & Oke (2012) e protocolo WUDAPT, democratiza acesso a ferramentas de análise climática urbana.")
        
        st.markdown("## 🔧 Tecnologias")
        st.write("- Streamlit, GeoPandas, Folium, Plotly, Pandas, Shapely")
        
        st.markdown("**Última atualização:** Setembro 2025  \n**Versão da Plataforma:** 2.0")
