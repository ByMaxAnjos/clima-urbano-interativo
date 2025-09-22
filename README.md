# 🌍 Plataforma Clima Urbano Interativo

Uma ferramenta educacional moderna e interativa para análise de **Ilhas de Calor Urbanas (ICU)** e **Zonas Climáticas Locais (ZCL)**, desenvolvida especificamente para estudantes e pesquisadores de Geografia.

![Versão](https://img.shields.io/badge/versão-2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.49+-red)
![Licença](https://img.shields.io/badge/licença-MIT-yellow)

## 🎯 Sobre o Projeto

Esta plataforma foi desenvolvida com base nas metodologias científicas estabelecidas por **Stewart & Oke (2012)** e o protocolo **WUDAPT (World Urban Database and Portal Tools)**. O objetivo é democratizar o acesso a ferramentas de análise climática urbana, tornando conceitos complexos acessíveis através de uma interface moderna e intuitiva.

### 🔬 Base Científica

- **Stewart & Oke (2012)** - Sistema de classificação das Zonas Climáticas Locais
- **WUDAPT** - Protocolo global para mapeamento urbano
- **LCZ Generator** - Ferramenta automatizada para geração de mapas de ZCL

## ✨ Funcionalidades

### 🌍 Módulo Explorar
- Visualização interativa de mapas de ZCL e temperatura
- Camadas sobrepostas de dados geoespaciais
- Interface intuitiva com controles de zoom e navegação
- Tooltips informativos com detalhes das zonas climáticas

### 🔬 Módulo Investigar
- Upload de dados de campo em formato CSV
- Ferramenta de desenho para definição de áreas de interesse
- Validação automática de dados
- Processamento espacial em tempo real

### 📊 Módulo Visualizar
- Gráficos interativos com Plotly
- Estatísticas descritivas por zona climática
- Análise de correlação espacial
- Relatórios automáticos em Markdown
- Exportação de dados processados

### 💡 Módulo Simular (Em Desenvolvimento)
- Simulação de intervenções urbanas
- Análise de impacto climático
- Cenários "E se?"

## 🚀 Instalação e Execução

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/plataforma-clima-urbano.git
cd plataforma-clima-urbano
```

2. **Instale as dependências:**
```bash
pip install streamlit pandas geopandas folium streamlit-folium plotly shapely branca
```

3. **Execute a aplicação:**
```bash
streamlit run app.py
```

4. **Acesse no navegador:**
```
http://localhost:8501
```

## 📁 Estrutura do Projeto

```
plataforma_clima_urbano/
│
├── app.py                      # Arquivo principal da aplicação
│
├── data/                       # Dados de exemplo
│   ├── sao_paulo_zcl.geojson  # Zonas Climáticas Locais
│   └── sao_paulo_temp.geojson # Dados de temperatura
│
├── modules/                    # Módulos da aplicação
│   ├── __init__.py
│   ├── inicio.py              # Página inicial
│   ├── explorar.py            # Módulo Explorar
│   ├── investigar.py          # Módulo Investigar
│   └── visualizar.py          # Módulo Visualizar
│
├── utils/                      # Utilitários
│   ├── __init__.py
│   └── processamento.py       # Funções de processamento de dados
│
├── assets/                     # Recursos estáticos
│   └── css/
│       └── style.css          # Estilos CSS customizados
│
├── exemplo_dados.csv          # Arquivo de exemplo para upload
└── README.md                  # Documentação
```

## 📊 Formato de Dados

### Dados de Campo (CSV)

Seu arquivo CSV deve conter as seguintes colunas:

| Coluna | Descrição | Nomes Aceitos |
|--------|-----------|---------------|
| Latitude | Coordenada geográfica | `lat`, `latitude`, `LAT`, `Latitude` |
| Longitude | Coordenada geográfica | `lon`, `lng`, `longitude`, `LON`, `Longitude` |
| Valor | Medição realizada | `valor`, `temp`, `temperatura`, `medida`, `value` |

**Exemplo:**
```csv
latitude,longitude,temperatura,local
-23.5505,-46.6333,32.5,Centro
-23.5489,-46.6388,28.2,Ibirapuera
-23.5558,-46.6396,35.1,Paulista
```

### Dados Geoespaciais

- **Formato:** GeoJSON
- **Sistema de Coordenadas:** WGS84 (EPSG:4326)
- **Geometrias:** Polígonos para ZCL, Pontos para medições

## 🎨 Design e Interface

A plataforma utiliza um design moderno com:

- **Tipografia:** Inter e Poppins (Google Fonts)
- **Cores:** Gradientes modernos em tons de azul e roxo
- **Componentes:** Cards responsivos, botões com efeitos hover
- **Animações:** Transições suaves e efeitos visuais
- **Responsividade:** Adaptável para desktop e mobile

### Paleta de Cores

- **Primária:** `#667eea` (Azul)
- **Secundária:** `#764ba2` (Roxo)
- **Sucesso:** `#48bb78` (Verde)
- **Aviso:** `#ed8936` (Laranja)
- **Erro:** `#f56565` (Vermelho)

## 🔧 Tecnologias Utilizadas

- **[Streamlit](https://streamlit.io/)** - Framework web para Python
- **[GeoPandas](https://geopandas.org/)** - Manipulação de dados geoespaciais
- **[Folium](https://python-visualization.github.io/folium/)** - Mapas interativos
- **[Plotly](https://plotly.com/python/)** - Gráficos interativos
- **[Pandas](https://pandas.pydata.org/)** - Análise de dados
- **[Shapely](https://shapely.readthedocs.io/)** - Geometrias espaciais

## 📚 Como Usar

### 1. Exploração Inicial
1. Acesse o módulo **Explorar**
2. Selecione as camadas desejadas (ZCL, Temperatura)
3. Navegue pelo mapa interativo
4. Clique nos elementos para ver detalhes

### 2. Análise de Dados Próprios
1. Vá para o módulo **Investigar**
2. Carregue seu arquivo CSV com dados de campo
3. Desenhe uma área de interesse no mapa
4. Execute a análise

### 3. Visualização de Resultados
1. Acesse o módulo **Visualizar**
2. Explore os gráficos interativos
3. Analise as estatísticas por zona climática
4. Baixe o relatório automático

## 🎓 Aplicações Educacionais

### Para Professores
- Ferramenta de ensino visual e interativa
- Dados reais para exercícios práticos
- Metodologia científica aplicada
- Suporte a diferentes níveis de ensino

### Para Estudantes
- Interface intuitiva e moderna
- Aprendizado baseado em projetos
- Análise de dados reais
- Desenvolvimento de pensamento crítico

### Para Pesquisadores
- Ferramenta de análise preliminar
- Validação de metodologias
- Visualização de resultados
- Base para estudos mais aprofundados

## 🌟 Exemplos de Uso

### Estudo de Caso: São Paulo
A plataforma inclui dados de exemplo para São Paulo, demonstrando:
- Diferentes tipos de ZCL na região metropolitana
- Variações de temperatura entre zonas urbanas e verdes
- Correlação entre uso do solo e clima local

### Projetos Sugeridos
1. **Mapeamento de Ilha de Calor:** Compare temperaturas entre centro urbano e áreas verdes
2. **Análise de Bairro:** Estude as características climáticas de um bairro específico
3. **Impacto da Vegetação:** Analise o efeito de parques na temperatura local
4. **Planejamento Urbano:** Identifique áreas prioritárias para intervenções

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

- **Desenvolvedor:** [Seu Nome]
- **Email:** contato@exemplo.com
- **GitHub:** [@seu-usuario](https://github.com/seu-usuario)

## 🙏 Agradecimentos

- **Stewart & Oke (2012)** pela metodologia das Zonas Climáticas Locais
- **WUDAPT** pelo protocolo de mapeamento urbano
- **Comunidade Streamlit** pelas ferramentas e documentação
- **OpenStreetMap** pelos dados cartográficos

---

**Desenvolvido com ❤️ para a educação em Geografia e Climatologia Urbana**

