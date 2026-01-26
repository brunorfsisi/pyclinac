"""
Módulo Starshot - Análise de Colimador, Gantry e Mesa
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="Starshot", page_icon="⭐", layout="wide")

# Importações do pylinac
try:
    from pylinac import Starshot
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

# Adiciona path do utils
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, save_uploaded_files, cleanup_temp_files,
    get_pdf_download_button, create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="⭐ Starshot",
    description="""
    O teste Starshot analisa a precisão de rotação do gantry, colimador
    ou mesa através de exposições em padrão de estrela. O raio do menor
    círculo que engloba todas as interseções indica a precisão da rotação.
    """,
    references=[
        "Gonzalez A, et al. Quality assurance for IMRT. Med Phys. 2004",
        "AAPM TG-142: Quality assurance of medical accelerators"
    ]
)

st.title("⭐ Análise Starshot")
st.markdown("""
Verificação da precisão de rotação de gantry, colimador ou mesa através do padrão Starshot.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Tabs para diferentes modos
tab1, tab2 = st.tabs(["📷 Imagem Única", "📁 Múltiplas Imagens"])

with tab1:
    st.subheader("Análise de Imagem Única")
    st.markdown("Faça upload de uma imagem contendo o padrão starshot completo.")

    uploaded_file = st.file_uploader(
        "Selecione a imagem",
        type=['dcm', 'DCM', 'tif', 'tiff', 'png', 'jpg', 'jpeg'],
        key="starshot_single"
    )

    # Parâmetros
    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            radius = st.slider(
                "Raio de análise (%)",
                min_value=10,
                max_value=95,
                value=85,
                help="Porcentagem do raio da imagem a ser analisada"
            )

            min_peak_height = st.slider(
                "Altura mínima do pico",
                min_value=0.1,
                max_value=1.0,
                value=0.25,
                step=0.05,
                help="Limiar para detecção de spokes"
            )

        with col2:
            tolerance = st.number_input(
                "Tolerância (mm)",
                min_value=0.1,
                max_value=3.0,
                value=1.0,
                step=0.1,
                help="Raio máximo tolerável do círculo wobble"
            )

            sid = st.number_input(
                "SID (mm)",
                min_value=500.0,
                max_value=2000.0,
                value=1000.0,
                step=10.0,
                help="Distância fonte-imagem (necessário para cálculo de mm)"
            )

    # Parâmetros avançados
    with st.expander("🔧 Parâmetros Avançados"):
        col1, col2 = st.columns(2)

        with col1:
            invert = st.checkbox(
                "Inverter imagem",
                value=False,
                key="invert_single"
            )

            fwxm = st.slider(
                "FWXM",
                min_value=0.1,
                max_value=0.9,
                value=0.5,
                step=0.1,
                help="Fração do máximo para largura dos spokes"
            )

        with col2:
            recursive = st.checkbox(
                "Análise recursiva",
                value=True,
                help="Usa análise recursiva para melhor precisão"
            )

    if uploaded_file is not None:
        if st.button("🔬 Executar Análise", key="analyze_single", type="primary"):
            temp_path = save_uploaded_file(uploaded_file)

            try:
                with st.spinner("Analisando padrão Starshot..."):
                    star = Starshot(temp_path, sid=sid)
                    star.analyze(
                        radius=radius/100,
                        min_peak_height=min_peak_height,
                        tolerance=tolerance,
                        fwxm=fwxm,
                        recursive=recursive,
                        invert=invert
                    )

                # Status
                if star.passed:
                    st.success(f"✅ Teste APROVADO - Raio wobble: {star.wobble.radius_mm:.3f} mm")
                else:
                    st.error(f"❌ Teste REPROVADO - Raio wobble: {star.wobble.radius_mm:.3f} mm")

                # Métricas
                st.subheader("📊 Resultados")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Raio do Círculo Wobble",
                        f"{star.wobble.radius_mm:.3f} mm",
                        delta=f"Tol: {tolerance} mm",
                        delta_color="normal" if star.passed else "off"
                    )

                with col2:
                    st.metric(
                        "Diâmetro Wobble",
                        f"{star.wobble.radius_mm * 2:.3f} mm"
                    )

                with col3:
                    st.metric(
                        "Número de Spokes",
                        f"{len(star.lines)}"
                    )

                # Centro do círculo wobble
                st.subheader("📍 Centro do Círculo Wobble")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Centro X", f"{star.wobble.center.x:.2f} px")
                with col2:
                    st.metric("Centro Y", f"{star.wobble.center.y:.2f} px")

                # Visualização
                st.subheader("🖼️ Visualização")
                fig, ax = plt.subplots(figsize=(10, 10))
                star.plot_analyzed_image(ax=ax)
                st.pyplot(fig)
                plt.close(fig)

                # Subimagem com zoom
                with st.expander("🔍 Visualização com Zoom"):
                    fig_sub, ax_sub = plt.subplots(figsize=(8, 8))
                    star.plot_analyzed_subimage(ax=ax_sub)
                    st.pyplot(fig_sub)
                    plt.close(fig_sub)

                # Relatório PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    star.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, "starshot_report.pdf")
                    os.unlink(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files([temp_path])

with tab2:
    st.subheader("Análise de Múltiplas Imagens")
    st.markdown("""
    Faça upload de múltiplas imagens individuais de spokes para criar
    uma imagem starshot composta.
    """)

    uploaded_files = st.file_uploader(
        "Selecione as imagens dos spokes",
        type=['dcm', 'DCM', 'tif', 'tiff', 'png', 'jpg'],
        accept_multiple_files=True,
        key="starshot_multi"
    )

    # Parâmetros para múltiplas imagens
    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            radius_multi = st.slider(
                "Raio de análise (%)",
                min_value=10,
                max_value=95,
                value=85,
                key="radius_multi"
            )

            tolerance_multi = st.number_input(
                "Tolerância (mm)",
                min_value=0.1,
                max_value=3.0,
                value=1.0,
                step=0.1,
                key="tol_multi"
            )

        with col2:
            sid_multi = st.number_input(
                "SID (mm)",
                min_value=500.0,
                max_value=2000.0,
                value=1000.0,
                step=10.0,
                key="sid_multi"
            )

            superimpose = st.checkbox(
                "Superimpor imagens",
                value=True,
                help="Combina as imagens em uma única imagem composta"
            )

    if uploaded_files and len(uploaded_files) >= 2:
        if st.button("🔬 Executar Análise", key="analyze_multi", type="primary"):
            temp_paths = save_uploaded_files(uploaded_files)

            try:
                with st.spinner("Combinando e analisando imagens..."):
                    # Carrega múltiplas imagens
                    star = Starshot.from_multiple_images(temp_paths, sid=sid_multi)
                    star.analyze(
                        radius=radius_multi/100,
                        tolerance=tolerance_multi
                    )

                # Status
                if star.passed:
                    st.success(f"✅ Teste APROVADO - Raio wobble: {star.wobble.radius_mm:.3f} mm")
                else:
                    st.error(f"❌ Teste REPROVADO - Raio wobble: {star.wobble.radius_mm:.3f} mm")

                # Métricas
                st.subheader("📊 Resultados")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Raio Wobble", f"{star.wobble.radius_mm:.3f} mm")

                with col2:
                    st.metric("Diâmetro Wobble", f"{star.wobble.radius_mm * 2:.3f} mm")

                with col3:
                    st.metric("Número de Spokes", f"{len(star.lines)}")

                # Visualização
                st.subheader("🖼️ Visualização")
                fig, ax = plt.subplots(figsize=(10, 10))
                star.plot_analyzed_image(ax=ax)
                st.pyplot(fig)
                plt.close(fig)

                # Relatório PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    star.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, "starshot_multi_report.pdf")
                    os.unlink(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files(temp_paths)

    elif uploaded_files:
        st.warning("⚠️ Faça upload de pelo menos 2 imagens para análise múltipla.")

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar o teste Starshot:

    1. **Preparação**:
       - Configure um campo estreito (ex: 1x10 cm ou 2x20 cm)
       - Posicione o filme ou EPID no isocentro

    2. **Aquisição para teste de Gantry**:
       - Mantenha colimador e mesa fixos (0°)
       - Exponha em múltiplos ângulos de gantry (ex: 0°, 30°, 60°, ..., 330°)

    3. **Aquisição para teste de Colimador**:
       - Mantenha gantry e mesa fixos
       - Exponha em múltiplos ângulos de colimador

    4. **Aquisição para teste de Mesa**:
       - Mantenha gantry e colimador fixos
       - Exponha em múltiplos ângulos de mesa

    5. **Análise**:
       - Faça upload da imagem composta ou imagens individuais
       - Configure os parâmetros
       - Execute a análise

    6. **Interpretação**:
       - O raio do círculo wobble representa a precisão do isocentro
       - Quanto menor, melhor a precisão

    ### Tolerâncias Típicas (TG-142):
    - **Rotação de Gantry**: ≤ 1 mm (diâmetro ≤ 2 mm)
    - **Rotação de Colimador**: ≤ 1 mm (diâmetro ≤ 2 mm)
    - **Rotação de Mesa**: ≤ 1 mm (diâmetro ≤ 2 mm)
    - **SRS**: ≤ 0.75 mm (diâmetro ≤ 1.5 mm)

    ### Tipos de Starshot:
    - **Imagem única**: Todas as exposições em um único filme/detector
    - **Múltiplas imagens**: Exposições separadas que são combinadas digitalmente
    """)
