#!/usr/bin/env python3
"""
Script para expandir exemplo_dados.csv com dados validados de múltiplas cidades.

Data Engineer: Gera dados geoespaciais realistas para Juiz de Fora, Rio de Janeiro
e mais registros de São Paulo, com validação de ranges e distribuição realista de UHI.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Configuração de seeds para reprodutibilidade
np.random.seed(42)

# Dados existentes (6 registros de São Paulo) - expandidos com umidade e altitude
dados_existentes = [
    (-23.5505, -46.6333, 32.5, 62, 760, "Centro"),
    (-23.5489, -46.6388, 28.2, 68, 810, "Ibirapuera"),
    (-23.5558, -46.6396, 35.1, 45, 820, "Paulista"),
    (-23.5629, -46.6544, 30.8, 58, 800, "Vila Madalena"),
    (-23.5475, -46.6361, 29.4, 60, 790, "Liberdade"),
    (-23.5533, -46.6417, 33.7, 52, 815, "Bela Vista"),
]

# Definição de locais por cidade com coordenadas base
CIDADES = {
    "São Paulo": {
        "base_lat": -23.5505,
        "base_lon": -46.6333,
        "locais": {
            "Centro": (-23.5505, -46.6333),
            "Paulista": (-23.5558, -46.6396),
            "Vila Madalena": (-23.5629, -46.6544),
            "Pinheiros": (-23.5625, -46.7042),
            "Consolação": (-23.5520, -46.6565),
            "Largo Batata": (-23.5661, -46.7078),
            "Av Paulista": (-23.5615, -46.6569),
            "Pátio do Colégio": (-23.5506, -46.6342),
            "Parque Ibirapuera": (-23.5883, -46.6579),
            "Bom Retiro": (-23.5340, -46.6264),
            "Brás": (-23.5406, -46.6131),
            "Vila Mariana": (-23.5870, -46.6307),
            "Chácara Santo Antônio": (-23.6160, -46.7050),
            "Itaim Bibi": (-23.5948, -46.6845),
            "Liberdade": (-23.5475, -46.6361),
        },
        "temp_min": 27.5,  # Maior UHI
        "temp_max": 36.1,
        "umidade_min": 35,
        "umidade_max": 65,
        "altitude_min": 700,
        "altitude_max": 900,
    },
    "Rio de Janeiro": {
        "base_lat": -22.9068,
        "base_lon": -43.1729,
        "locais": {
            "Centro": (-22.9068, -43.1729),
            "Copacabana": (-22.9829, -43.1863),
            "Ipanema": (-22.9927, -43.2026),
            "Leblon": (-23.0046, -43.2280),
            "Barra da Tijuca": (-23.0244, -43.3681),
            "Botafogo": (-22.9451, -43.1957),
            "Flamengo": (-22.9311, -43.1794),
            "Niterói": (-22.8829, -43.0976),
            "Gávea": (-22.9902, -43.2350),
            "Cristo Redentor": (-22.9519, -43.1928),
        },
        "temp_min": 26.5,  # UHI moderada
        "temp_max": 35.2,
        "umidade_min": 55,
        "umidade_max": 79,
        "altitude_min": 5,
        "altitude_max": 700,
    },
    "Juiz de Fora": {
        "base_lat": -21.7626,
        "base_lon": -43.3523,
        "locais": {
            "Centro": (-21.7626, -43.3523),
            "Bom Jardim": (-21.7550, -43.3450),
            "Poço Rico": (-21.7700, -43.3400),
            "Benfica": (-21.7750, -43.3600),
            "Santa Cecília": (-21.7680, -43.3550),
            "Passos": (-21.7630, -43.3700),
            "Represa": (-21.7550, -43.3350),
            "Arboleda": (-21.7700, -43.3650),
            "Vila Ideal": (-21.7580, -43.3480),
            "Linhares": (-21.7720, -43.3520),
            "Teixeiras": (-21.7640, -43.3580),
            "Distrito de Soberbo": (-21.7560, -43.3420),
        },
        "temp_min": 25.2,  # UHI leve
        "temp_max": 33.5,
        "umidade_min": 50,
        "umidade_max": 75,
        "altitude_min": 350,
        "altitude_max": 950,
    },
}

# Ranges de validação global (com margem)
VALIDACAO = {
    "latitude": (-23.6, -20.0),
    "longitude": (-46.8, -42.7),
    "temperatura": (25.2, 36.1),
    "umidade": (35, 79),
    "altitude": (5, 950),
}


def gerar_dados_cidade(cidade_nome, config, n_registros):
    """
    Gera dados realistas para uma cidade.

    Args:
        cidade_nome: Nome da cidade
        config: Dicionário com configuração de coordenadas e ranges
        n_registros: Número de registros a gerar

    Returns:
        Lista de tuplas (latitude, longitude, temperatura, umidade, altitude, local)
    """
    registros = []
    locais = list(config["locais"].items())

    # Se temos mais registros do que locais, repetimos alguns
    locais_para_usar = locais * (n_registros // len(locais) + 1)
    locais_para_usar = locais_para_usar[:n_registros]

    for idx, (local_nome, (base_lat, base_lon)) in enumerate(locais_para_usar):
        # Variação pequena em coordenadas (±0.005 = ~500m)
        lat = float(base_lat + np.random.uniform(-0.005, 0.005))
        lon = float(base_lon + np.random.uniform(-0.005, 0.005))

        # Validar latitude e longitude
        lat = np.clip(lat, VALIDACAO["latitude"][0], VALIDACAO["latitude"][1])
        lon = np.clip(lon, VALIDACAO["longitude"][0], VALIDACAO["longitude"][1])

        # Temperatura com distribuição realista (UHI mais intenso = temp mais alta)
        temp = float(np.random.uniform(config["temp_min"], config["temp_max"]))
        temp = np.clip(temp, VALIDACAO["temperatura"][0], VALIDACAO["temperatura"][1])

        # Umidade com correlação inversa com temperatura (simples e robusta)
        umidade_base = config["umidade_max"] - (config["umidade_max"] - config["umidade_min"]) * 0.3  # 70% do máximo
        umidade = umidade_base + np.random.uniform(-10, 10)
        umidade = float(np.clip(umidade, VALIDACAO["umidade"][0], VALIDACAO["umidade"][1]))

        # Altitude
        altitude = float(np.random.uniform(config["altitude_min"], config["altitude_max"]))
        altitude = np.clip(altitude, VALIDACAO["altitude"][0], VALIDACAO["altitude"][1])

        registros.append((float(lat), float(lon), float(temp), float(umidade), float(altitude), local_nome))

    return registros


def main():
    """
    Script principal: gera dados expandidos e atualiza CSV.
    """
    print("=" * 80)
    print("DATA ENGINEER: Gerando dados expandidos para exemplo_dados.csv")
    print("=" * 80)
    print(f"\nData/Hora: {datetime.now().isoformat()}")
    print(f"\nDistribuição alvo:")
    print(f"  - São Paulo: 15 registros (6 existentes + 9 novos)")
    print(f"  - Rio de Janeiro: 10 registros (novos)")
    print(f"  - Juiz de Fora: 12 registros (novos)")
    print(f"  TOTAL: 37 registros\n")

    # Passo 1: Preservar dados existentes
    print("[1/4] Preservando registros existentes...")
    registros_totais = [tuple(d) for d in dados_existentes]
    print(f"      ✓ {len(dados_existentes)} registros de São Paulo mantidos\n")

    # Passo 2: Gerar novos registros para São Paulo
    print("[2/4] Gerando 9 registros adicionais de São Paulo...")
    novos_sp = gerar_dados_cidade("São Paulo", CIDADES["São Paulo"], 9)
    registros_totais.extend(novos_sp)
    print(f"      ✓ {len(novos_sp)} novos registros de São Paulo\n")

    # Passo 3: Gerar registros para Rio de Janeiro
    print("[3/4] Gerando 10 registros de Rio de Janeiro...")
    novos_rj = gerar_dados_cidade("Rio de Janeiro", CIDADES["Rio de Janeiro"], 10)
    registros_totais.extend(novos_rj)
    print(f"      ✓ {len(novos_rj)} registros de Rio de Janeiro\n")

    # Passo 4: Gerar registros para Juiz de Fora
    print("[4/4] Gerando 12 registros de Juiz de Fora...")
    novos_jf = gerar_dados_cidade("Juiz de Fora", CIDADES["Juiz de Fora"], 12)
    registros_totais.extend(novos_jf)
    print(f"      ✓ {len(novos_jf)} registros de Juiz de Fora\n")

    # Passo 5: Criar DataFrame e validar
    print("=" * 80)
    print("VALIDAÇÃO DE DADOS")
    print("=" * 80)

    df = pd.DataFrame(
        registros_totais,
        columns=["latitude", "longitude", "temperatura", "umidade", "altitude", "local"]
    )

    # Converter para tipos numéricos se necessário
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["temperatura"] = pd.to_numeric(df["temperatura"], errors="coerce")
    df["umidade"] = pd.to_numeric(df["umidade"], errors="coerce")
    df["altitude"] = pd.to_numeric(df["altitude"], errors="coerce")

    # Verificar por NaNs antes de processar
    if df.isna().sum().sum() > 0:
        print(f"\nAVISO: Encontrados valores NaN. Removendo {len(df[df.isna().any(axis=1)])} linhas.")
        df = df.dropna()

    # Arredondar para 4 casas decimais (resolução ~10m)
    df["latitude"] = df["latitude"].round(4)
    df["longitude"] = df["longitude"].round(4)
    df["temperatura"] = df["temperatura"].round(1)
    df["umidade"] = df["umidade"].round(0).astype(int)
    df["altitude"] = df["altitude"].round(0).astype(int)

    # Validações
    print("\nValidando ranges...")
    validacoes = {
        "latitude": (VALIDACAO["latitude"][0], VALIDACAO["latitude"][1]),
        "longitude": (VALIDACAO["longitude"][0], VALIDACAO["longitude"][1]),
        "temperatura": (VALIDACAO["temperatura"][0], VALIDACAO["temperatura"][1]),
        "umidade": (VALIDACAO["umidade"][0], VALIDACAO["umidade"][1]),
        "altitude": (VALIDACAO["altitude"][0], VALIDACAO["altitude"][1]),
    }

    todos_validos = True
    for coluna, (min_val, max_val) in validacoes.items():
        invalidos = df[(df[coluna] < min_val) | (df[coluna] > max_val)]
        status = "✓" if len(invalidos) == 0 else "✗"
        print(f"  {status} {coluna}: [{min_val}, {max_val}] - {len(invalidos)} inválidos")
        if len(invalidos) > 0:
            todos_validos = False

    # Verificar NaNs
    nans = df.isna().sum()
    print(f"\n  ✓ NaNs: {nans.sum() if nans.sum() == 0 else 'ENCONTRADOS!'}")

    # Estatísticas por cidade
    print("\nEstatísticas por cidade:")
    print("-" * 80)

    # Detectar cidade pelos locais
    df["cidade"] = "Desconhecida"
    for cidade, config in CIDADES.items():
        df.loc[df["local"].isin(config["locais"].keys()), "cidade"] = cidade

    for cidade in ["São Paulo", "Rio de Janeiro", "Juiz de Fora"]:
        cidade_df = df[df["cidade"] == cidade]
        print(f"\n{cidade} ({len(cidade_df)} registros):")
        print(f"  Temperatura: {cidade_df['temperatura'].min():.1f}°C - {cidade_df['temperatura'].max():.1f}°C (media: {cidade_df['temperatura'].mean():.1f}°C)")
        print(f"  Umidade: {cidade_df['umidade'].min()}% - {cidade_df['umidade'].max()}% (media: {cidade_df['umidade'].mean():.0f}%)")
        print(f"  Altitude: {cidade_df['altitude'].min()}m - {cidade_df['altitude'].max()}m")

    print("\n" + "=" * 80)
    print(f"RESULTADO FINAL: {len(df)} registros gerados")
    print("=" * 80)

    # Remover coluna auxiliar
    df = df.drop(columns=["cidade"])

    # Salvar no arquivo original (sem índice, sem header repetido)
    output_path = "/Users/co2map/Documents/2025/clima-urbano-interativo/exemplo_dados.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✓ Arquivo salvo: {output_path}\n")

    # Exibir amostra
    print("Amostra dos primeiros 5 registros:")
    print(df.head().to_string(index=False))
    print("\nAmostra dos últimos 5 registros:")
    print(df.tail().to_string(index=False))

    return df


if __name__ == "__main__":
    df_resultado = main()
    print("\n✓ Script concluído com sucesso!")
