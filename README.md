# Pylinac QA Suite

Sistema completo de Controle de Qualidade para Radioterapia baseado na biblioteca [pylinac](https://pylinac.readthedocs.io/).

## Funcionalidades

### Testes de Posicionamento
- **Winston-Lutz**: Análise de precisão do isocentro
- **Winston-Lutz Multi-Target**: Extensão para múltiplos alvos
- **Starshot**: Análise de rotação de gantry, colimador e mesa

### Análise de MLC
- **Picket Fence**: Verificação de posicionamento de lâminas
- **VMAT (DRGS/DRMLC)**: Testes de tratamentos dinâmicos

### Calibração de Dose
- **TG-51**: Protocolo AAPM para calibração absoluta
- **TRS-398**: Protocolo IAEA para dosimetria de referência

### Imagem Planar
- **Leeds TOR 18/Blue**: Análise completa de resolução e contraste
- **Standard Imaging QC-3/QC-kV**: QC diário de EPID e OBI
- **Las Vegas**: Avaliação de baixo contraste
- **Doselab MC2**: Controle de qualidade kV/MV
- **PTW EPID QC**: Phantom PTW específico
- **SNC kV/MV**: Phantoms Sun Nuclear

### CBCT
- **CatPhan 503/504/600/604**: Análise completa de qualidade CT
- **Quart DVT**: Sistemas DVT dental
- **ACR CT/MRI**: Phantoms de acreditação ACR

### Análise de Logs
- **Dynalog Analyzer**: Logs de posição de MLC (formato antigo)
- **Trajectory Log**: Logs completos de trajetória (formato atual)

### Análise de Campo
- **Field Analysis**: Análise de campos abertos
- **Flatness/Symmetry**: Planura e simetria
- **Penumbra**: Análise de bordas do campo

## Instalação

### 1. Clone ou baixe o repositório

```bash
cd /home/brunorg/pyclinac
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

## Estrutura do Projeto

```
pyclinac/
├── app.py                      # Aplicação principal
├── requirements.txt            # Dependências
├── README.md                   # Este arquivo
├── pages/                      # Páginas dos módulos
│   ├── 1_Winston_Lutz.py
│   ├── 2_Picket_Fence.py
│   ├── 3_Starshot.py
│   ├── 4_VMAT.py
│   ├── 5_Calibracao_Dose.py
│   ├── 6_Planar_Imaging.py
│   ├── 7_CBCT.py
│   ├── 8_Log_Analyzer.py
│   └── 9_Field_Analysis.py
├── utils/                      # Funções utilitárias
│   ├── __init__.py
│   └── helpers.py
└── assets/                     # Recursos estáticos
```

## Uso

1. Acesse a aplicação no navegador
2. Selecione o módulo desejado no menu lateral
3. Faça upload das imagens DICOM ou arquivos de log
4. Configure os parâmetros de análise
5. Execute a análise e visualize os resultados
6. Exporte o relatório PDF se necessário

## Formatos Suportados

- **Imagens**: DICOM (.dcm), TIFF (.tif, .tiff), PNG, JPEG
- **Logs**: Dynalog (.dlg), Trajectory Log (.bin)
- **Arquivos compactados**: ZIP (para múltiplas imagens)

## Tolerâncias de Referência (TG-142)

| Teste | Tolerância |
|-------|------------|
| Winston-Lutz | ≤ 1 mm (SRS: ≤ 0.75 mm) |
| Picket Fence | ≤ 0.5 mm |
| Starshot | ≤ 1 mm diâmetro |
| VMAT | ≤ 1.5% desvio |
| Flatness | ≤ 3% |
| Symmetry | ≤ 3% |
| Tamanho de Campo | ± 2 mm |

## Referências

- [Pylinac Documentation](https://pylinac.readthedocs.io/)
- AAPM TG-142: Quality assurance of medical accelerators
- AAPM TG-51: Protocol for clinical reference dosimetry
- IAEA TRS-398: Absorbed Dose Determination in External Beam Radiotherapy

## Avisos

- Esta ferramenta é fornecida para fins educacionais e de pesquisa
- Para uso clínico, valide os resultados com métodos estabelecidos
- Consulte sempre os protocolos locais e regulamentações aplicáveis

## Licença

MIT License - Veja o arquivo LICENSE para detalhes.

## Contribuições

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.
