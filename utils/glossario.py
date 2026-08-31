# utils/glossario.py
"""Glossário mínimo de termos de clima urbano usados na plataforma."""

import streamlit as st

GLOSSARIO = {
    "LCZ (Zona Climática Local)": (
        "Classifica um recorte urbano pela sua estrutura física (altura e espaçamento das "
        "construções) e cobertura de superfície (vegetação, pavimento, água) — não pelo uso "
        "do terreno. Proposto por Stewart & Oke (2012)."
    ),
    "Ilha de calor do ar (dossel)": (
        "Diferença de temperatura do ar entre áreas urbanas e áreas com estrutura/cobertura "
        "diferentes nas proximidades, medida próxima ao nível das pessoas."
    ),
    "Ilha de calor de superfície (LST)": (
        "Diferença de temperatura da superfície (telhados, asfalto, solo, copas), medida por "
        "sensoriamento remoto. É mais intensa de dia e não é a mesma coisa que a temperatura "
        "do ar sentida pelas pessoas."
    ),
    "Albedo": "Fração da radiação solar que uma superfície reflete, ao invés de absorver. Superfícies claras têm albedo alto e aquecem menos.",
    "Rugosidade da superfície": "Quão irregular é a superfície urbana (altura e espaçamento de prédios), o que afeta a circulação do vento e a troca de calor com a atmosfera.",
    "Evapotranspiração": "Perda de água para a atmosfera pela evaporação do solo e pela transpiração das plantas — processo que resfria o ar ao redor da vegetação.",
    "Correlação espacial vs. autocorrelação espacial": (
        "Correlação espacial simples relaciona um valor a uma coordenada (ex. latitude). "
        "Autocorrelação espacial (ex. Índice de Moran) mede se pontos próximos entre si "
        "tendem a ter valores parecidos — é uma análise diferente e mais exigente em dados."
    ),
    "Vulnerabilidade socioambiental": "Grau em que um grupo social é afetado por um risco ambiental (como calor extremo), considerando exposição, sensibilidade e capacidade de resposta.",
}


def renderizar_entenda_dados(termos: list[str] | None = None, titulo: str = "🔍 Entenda os dados"):
    """Mostra um expander com definições do glossário para os termos indicados.

    Args:
        termos: lista de chaves de GLOSSARIO a exibir. Se None, mostra todos.
        titulo: texto do expander.
    """
    termos = termos or list(GLOSSARIO.keys())
    with st.expander(titulo):
        for termo in termos:
            definicao = GLOSSARIO.get(termo)
            if definicao:
                st.markdown(f"**{termo}:** {definicao}")
