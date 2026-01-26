"""
Pylinac QA Suite - Aplicação Streamlit para Controle de Qualidade em Radioterapia
Baseado na biblioteca pylinac: https://pylinac.readthedocs.io/
"""

import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Pylinac QA Suite",
    page_icon="☢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .module-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<p class="main-header">☢️ Pylinac QA Suite</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Sistema Completo de Controle de Qualidade para Radioterapia</p>', unsafe_allow_html=True)

st.divider()

# Descrição
st.markdown("""
### Bem-vindo ao Pylinac QA Suite

Esta aplicação fornece uma interface gráfica completa para realizar testes de controle de qualidade
em radioterapia utilizando a biblioteca **pylinac**. Selecione um módulo no menu lateral para começar.
""")

st.divider()

# Grid de módulos disponíveis
st.subheader("Módulos Disponíveis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🎯 Posicionamento")
    st.markdown("""
    - **Winston-Lutz**: Análise de isocentro
    - **Winston-Lutz Multi-Target**: Múltiplos alvos
    - **Starshot**: Análise de spokes
    """)

    st.markdown("#### 📊 Análise de MLC")
    st.markdown("""
    - **Picket Fence**: Posicionamento de lâminas
    - **VMAT**: Testes DRGS e DRMLC
    """)

with col2:
    st.markdown("#### 📷 Imagem Planar")
    st.markdown("""
    - **Leeds TOR**: Contraste e resolução
    - **QC-3 / QC-kV**: Standard Imaging
    - **Las Vegas**: Análise de contraste
    - **Doselab MC2**: Controle de qualidade
    - **PTW EPID QC**: Análise EPID
    """)

    st.markdown("#### 🔬 CBCT")
    st.markdown("""
    - **CatPhan**: 503, 504, 600, 604
    - **Quart DVT**: Análise DVT
    - **ACR CT/MR**: Phantomas ACR
    """)

with col3:
    st.markdown("#### ⚡ Calibração de Dose")
    st.markdown("""
    - **TG-51**: Protocolo AAPM
    - **TRS-398**: Protocolo IAEA
    """)

    st.markdown("#### 📈 Análise de Campo")
    st.markdown("""
    - **Field Analysis**: Análise de campo aberto
    - **Field Profile**: Perfis de dose
    """)

    st.markdown("#### 📁 Logs")
    st.markdown("""
    - **Dynalog Analyzer**: Logs Varian
    - **Trajectory Log**: Análise de trajetória
    """)

st.divider()

# Instruções
with st.expander("📖 Como usar esta aplicação"):
    st.markdown("""
    1. **Selecione um módulo** no menu lateral esquerdo
    2. **Faça upload** da(s) imagem(ns) DICOM ou arquivo de log
    3. **Configure os parâmetros** de análise conforme necessário
    4. **Execute a análise** e visualize os resultados
    5. **Exporte o relatório** em PDF se desejar

    ### Formatos de arquivo suportados:
    - Imagens DICOM (.dcm)
    - Imagens TIFF (.tif, .tiff)
    - Arquivos ZIP contendo múltiplas imagens
    - Dynalogs (.dlg)
    - Trajectory logs (.bin)

    ### Requisitos:
    - Python 3.8+
    - pylinac >= 3.0
    - streamlit >= 1.20
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9rem;'>
    Desenvolvido com ❤️ usando <a href='https://pylinac.readthedocs.io/'>pylinac</a> e
    <a href='https://streamlit.io/'>Streamlit</a>
</div>
""", unsafe_allow_html=True)
