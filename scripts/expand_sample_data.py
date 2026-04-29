#!/usr/bin/env python3
"""
Script para expandir exemplo_dados.csv com dados realistas
de Juiz de Fora, Rio de Janeiro, São Paulo e outras localidades urbanas.

Uso:
    python scripts/expand_sample_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_sample_data():
    """
    Gera dados de exemplo expandidos com variação realista.

    Returns
    -------
    pd.DataFrame
        DataFrame com 35+ registros de múltiplas cidades
    """

    # Definição de cidades com contexto geográfico e climático
    cities_data = {
        'São Paulo': {
            'base_coords': (-23.5505, -46.6333),
            'temp_range': (28, 36),
            'humidity_range': (35, 65),
            'altitude_base': 750,
            'neighborhoods': [
                'Centro', 'Ibirapuera', 'Paulista', 'Vila Madalena',
                'Liberdade', 'Bela Vista', 'Pinheiros', 'Consolação',
                'Vila Mariana', 'Cambuci'
            ]
        },
        'Rio de Janeiro': {
            'base_coords': (-22.9068, -43.1729),
            'temp_range': (28, 36),
            'humidity_range': (40, 70),
            'altitude_base': 815,
            'neighborhoods': [
                'Centro', 'Santa Tereza', 'Copacabana', 'Lapa',
                'Ipanema', 'Leblon', 'Botafogo', 'Gávea',
                'Niterói', 'Arpoador'
            ]
        },
        'Juiz de Fora': {
            'base_coords': (-20.1551, -42.8527),
            'temp_range': (25, 31),
            'humidity_range': (65, 80),
            'altitude_base': 922,
            'neighborhoods': [
                'Centro', 'São Benedito', 'Vila Ideal', 'Grama',
                'Pascoal Rossi', 'Santa Cândida', 'Poço Rico', 'Jóquei Clube',
                'Rodoviária', 'Flores'
            ]
        }
    }

    records = []

    for city_name, city_info in cities_data.items():
        base_lat, base_lon = city_info['base_coords']
        neighborhoods = city_info['neighborhoods']
        temp_min, temp_max = city_info['temp_range']
        humid_min, humid_max = city_info['humidity_range']
        altitude_base = city_info['altitude_base']

        # Gerar registros com seed baseado no nome da cidade para reprodutibilidade
        np.random.seed(hash(city_name) % 2**32)

        for i, neighborhood in enumerate(neighborhoods):
            # Adicionar variação pequena de coordenadas (aprox 2-3 km)
            lat = base_lat + np.random.uniform(-0.02, 0.02)
            lon = base_lon + np.random.uniform(-0.02, 0.02)

            # Temperatura com variação realista
            temp = np.random.uniform(temp_min, temp_max)

            # Umidade com correlação inversa à temperatura
            umidade_offset = (temp - temp_min) / (temp_max - temp_min) * (humid_max - humid_min)
            humid = humid_max - umidade_offset + np.random.normal(0, 2)
            humid = np.clip(humid, humid_min, humid_max)

            # Altitude com pequena variação topográfica
            alt = altitude_base + np.random.uniform(-50, 50)

            records.append({
                'latitude': round(lat, 4),
                'longitude': round(lon, 4),
                'temperatura': round(temp, 1),
                'local': neighborhood,
                'umidade': round(humid, 1),
                'altitude_m': int(round(alt))
            })

    df = pd.DataFrame(records)

    # Validação de dados
    assert len(df) >= 30, f"Esperado >= 30 registros, obteve {len(df)}"
    assert 'latitude' in df.columns, "Coluna 'latitude' faltante"
    assert 'longitude' in df.columns, "Coluna 'longitude' faltante"
    assert 'temperatura' in df.columns, "Coluna 'temperatura' faltante"
    assert 'local' in df.columns, "Coluna 'local' faltante"

    # Validar ranges
    assert df['latitude'].min() >= -90 and df['latitude'].max() <= 90, "Latitudes inválidas"
    assert df['longitude'].min() >= -180 and df['longitude'].max() <= 180, "Longitudes inválidas"
    assert df['temperatura'].min() >= 20 and df['temperatura'].max() <= 40, "Temperaturas fora do esperado"
    assert df['umidade'].min() >= 0 and df['umidade'].max() <= 100, "Umidade fora do range 0-100"

    return df.sort_values('temperatura').reset_index(drop=True)


def main():
    """Função principal para gerar e salvar dados."""

    # Gerar dados
    print("📊 Gerando dados de exemplo...")
    df = generate_sample_data()

    # Determinar caminho de saída
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    output_path = repo_root / "exemplo_dados.csv"

    # Salvar arquivo
    df.to_csv(output_path, index=False)

    print(f"\n✅ Arquivo salvo com sucesso: {output_path}")
    print(f"\n📊 ESTATÍSTICAS DOS DADOS:")
    print(f"   Total de registros: {len(df)}")
    print(f"   Cidades: {df['local'].nunique()}")
    print(f"   Bairros: {df['local'].nunique()}")
    print(f"\n🌡️  TEMPERATURA:")
    print(f"   Mínima: {df['temperatura'].min():.1f}°C")
    print(f"   Média: {df['temperatura'].mean():.1f}°C")
    print(f"   Máxima: {df['temperatura'].max():.1f}°C")
    print(f"   Desvio Padrão: {df['temperatura'].std():.1f}°C")

    print(f"\n💧 UMIDADE:")
    print(f"   Mínima: {df['umidade'].min():.1f}%")
    print(f"   Média: {df['umidade'].mean():.1f}%")
    print(f"   Máxima: {df['umidade'].max():.1f}%")

    print(f"\n📍 ALTITUDE:")
    print(f"   Mínima: {df['altitude_m'].min():.0f}m")
    print(f"   Máxima: {df['altitude_m'].max():.0f}m")

    print(f"\n🏙️  DISTRIBUIÇÃO POR CIDADE:")
    for city in df['local'].unique():
        count = len(df[df['local'] == city])
        print(f"   {city}: {count} registros")

    print(f"\n📋 Primeiras linhas do dataset:")
    print(df.head(10).to_string(index=False))

    print(f"\n✨ Dataset pronto para uso!")


if __name__ == "__main__":
    main()
