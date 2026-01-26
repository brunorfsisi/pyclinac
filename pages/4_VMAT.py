"""
Módulo VMAT - Análise de DRGS e DRMLC
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="VMAT QA", page_icon="🔄", layout="wide")

# Importações do pylinac
try:
    from pylinac import DRGS, DRMLC
    from pylinac.vmat import ImageType
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

# Adiciona path do utils
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, cleanup_temp_files, get_pdf_download_button,
    create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="🔄 VMAT QA",
    description="""
    Os testes VMAT verificam a precisão da entrega de dose em
    tratamentos de arco volumétrico modulado através dos testes
    DRGS (Dose Rate & Gantry Speed) e DRMLC (Dose Rate & MLC).
    """,
    references=[
        "Ling CC, et al. Commissioning and QA of RapidArc. Int J Radiat Oncol Biol Phys. 2008",
        "Mancuso GM, et al. VMAT QA test using EPID. Med Phys. 2012"
    ]
)

st.title("🔄 Análise VMAT")
st.markdown("""
Verificação de qualidade de tratamentos VMAT através dos testes DRGS e DRMLC.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Explicação dos testes
with st.expander("ℹ️ Sobre os Testes VMAT"):
    st.markdown("""
    ### DRGS (Dose Rate & Gantry Speed)
    - Testa a interação entre taxa de dose e velocidade do gantry
    - Usa um campo aberto como referência
    - Compara a dose em diferentes segmentos

    ### DRMLC (Dose Rate & MLC)
    - Testa a interação entre taxa de dose e movimento do MLC
    - Usa um campo aberto como referência
    - Avalia a precisão do movimento dinâmico das lâminas
    """)

# Tabs para DRGS e DRMLC
tab1, tab2 = st.tabs(["📊 DRGS", "📊 DRMLC"])

# =============================================================================
# TAB DRGS
# =============================================================================
with tab1:
    st.subheader("Teste DRGS (Dose Rate & Gantry Speed)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Imagem DRGS (VMAT)**")
        drgs_image = st.file_uploader(
            "Selecione a imagem DRGS",
            type=['dcm', 'DCM'],
            key="drgs_vmat",
            help="Imagem adquirida com o plano DRGS"
        )

    with col2:
        st.markdown("**Imagem de Referência (Campo Aberto)**")
        drgs_open = st.file_uploader(
            "Selecione a imagem de referência",
            type=['dcm', 'DCM'],
            key="drgs_open",
            help="Imagem de campo aberto para referência"
        )

    # Parâmetros DRGS
    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            drgs_tolerance = st.number_input(
                "Tolerância (%)",
                min_value=0.5,
                max_value=5.0,
                value=1.5,
                step=0.1,
                key="drgs_tol",
                help="Tolerância máxima de desvio percentual"
            )

        with col2:
            drgs_segments = st.number_input(
                "Número de segmentos",
                min_value=1,
                max_value=20,
                value=7,
                key="drgs_seg",
                help="Número de segmentos para análise"
            )

    if drgs_image and drgs_open:
        if st.button("🔬 Analisar DRGS", key="analyze_drgs", type="primary"):
            drgs_path = save_uploaded_file(drgs_image)
            open_path = save_uploaded_file(drgs_open)

            try:
                with st.spinner("Analisando teste DRGS..."):
                    drgs = DRGS(image_paths=[drgs_path, open_path])
                    drgs.analyze(tolerance=drgs_tolerance)

                # Status
                if drgs.passed:
                    st.success("✅ Teste DRGS APROVADO")
                else:
                    st.error("❌ Teste DRGS REPROVADO")

                # Métricas
                st.subheader("📊 Resultados DRGS")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Desvio Máximo",
                        f"{drgs.max_r_deviation:.2f}%",
                        delta=f"Tol: {drgs_tolerance}%",
                        delta_color="normal" if drgs.passed else "off"
                    )

                with col2:
                    st.metric(
                        "Desvio Médio Absoluto",
                        f"{drgs.avg_abs_r_deviation:.2f}%"
                    )

                with col3:
                    st.metric(
                        "Segmentos Analisados",
                        f"{len(drgs.segments)}"
                    )

                # Visualização
                st.subheader("🖼️ Visualização")
                fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                drgs.plot_analyzed_image(axes=axes)
                st.pyplot(fig)
                plt.close(fig)

                # Detalhes por segmento
                with st.expander("📋 Detalhes por Segmento"):
                    seg_data = []
                    for i, seg in enumerate(drgs.segments):
                        seg_data.append({
                            "Segmento": i + 1,
                            "R Esperado": f"{seg.r_corr:.4f}",
                            "R Medido": f"{seg.r_dev:.4f}",
                            "Desvio (%)": f"{seg.r_dev:.2f}",
                            "Status": "✅" if abs(seg.r_dev) <= drgs_tolerance else "❌"
                        })
                    st.dataframe(seg_data, use_container_width=True)

                # Relatório PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    drgs.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, "drgs_report.pdf")
                    os.unlink(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files([drgs_path, open_path])

    else:
        st.info("👆 Faça upload das imagens DRGS e de referência para começar.")

# =============================================================================
# TAB DRMLC
# =============================================================================
with tab2:
    st.subheader("Teste DRMLC (Dose Rate & MLC)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Imagem DRMLC (VMAT)**")
        drmlc_image = st.file_uploader(
            "Selecione a imagem DRMLC",
            type=['dcm', 'DCM'],
            key="drmlc_vmat",
            help="Imagem adquirida com o plano DRMLC"
        )

    with col2:
        st.markdown("**Imagem de Referência (Campo Aberto)**")
        drmlc_open = st.file_uploader(
            "Selecione a imagem de referência",
            type=['dcm', 'DCM'],
            key="drmlc_open",
            help="Imagem de campo aberto para referência"
        )

    # Parâmetros DRMLC
    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            drmlc_tolerance = st.number_input(
                "Tolerância (%)",
                min_value=0.5,
                max_value=5.0,
                value=1.5,
                step=0.1,
                key="drmlc_tol",
                help="Tolerância máxima de desvio percentual"
            )

        with col2:
            drmlc_segments = st.number_input(
                "Número de segmentos",
                min_value=1,
                max_value=20,
                value=7,
                key="drmlc_seg",
                help="Número de segmentos para análise"
            )

    if drmlc_image and drmlc_open:
        if st.button("🔬 Analisar DRMLC", key="analyze_drmlc", type="primary"):
            drmlc_path = save_uploaded_file(drmlc_image)
            open_mlc_path = save_uploaded_file(drmlc_open)

            try:
                with st.spinner("Analisando teste DRMLC..."):
                    drmlc = DRMLC(image_paths=[drmlc_path, open_mlc_path])
                    drmlc.analyze(tolerance=drmlc_tolerance)

                # Status
                if drmlc.passed:
                    st.success("✅ Teste DRMLC APROVADO")
                else:
                    st.error("❌ Teste DRMLC REPROVADO")

                # Métricas
                st.subheader("📊 Resultados DRMLC")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Desvio Máximo",
                        f"{drmlc.max_r_deviation:.2f}%",
                        delta=f"Tol: {drmlc_tolerance}%",
                        delta_color="normal" if drmlc.passed else "off"
                    )

                with col2:
                    st.metric(
                        "Desvio Médio Absoluto",
                        f"{drmlc.avg_abs_r_deviation:.2f}%"
                    )

                with col3:
                    st.metric(
                        "Segmentos Analisados",
                        f"{len(drmlc.segments)}"
                    )

                # Visualização
                st.subheader("🖼️ Visualização")
                fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                drmlc.plot_analyzed_image(axes=axes)
                st.pyplot(fig)
                plt.close(fig)

                # Detalhes por segmento
                with st.expander("📋 Detalhes por Segmento"):
                    seg_data = []
                    for i, seg in enumerate(drmlc.segments):
                        seg_data.append({
                            "Segmento": i + 1,
                            "R Esperado": f"{seg.r_corr:.4f}",
                            "R Medido": f"{seg.r_dev:.4f}",
                            "Desvio (%)": f"{seg.r_dev:.2f}",
                            "Status": "✅" if abs(seg.r_dev) <= drmlc_tolerance else "❌"
                        })
                    st.dataframe(seg_data, use_container_width=True)

                # Relatório PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    drmlc.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, "drmlc_report.pdf")
                    os.unlink(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files([drmlc_path, open_mlc_path])

    else:
        st.info("👆 Faça upload das imagens DRMLC e de referência para começar.")

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar os testes VMAT:

    #### Teste DRGS
    1. **Planejamento**:
       - Crie um arco VMAT com variação de taxa de dose e velocidade do gantry
       - Mantenha as lâminas do MLC fixas

    2. **Aquisição**:
       - Adquira uma imagem com o plano DRGS
       - Adquira uma imagem de campo aberto como referência

    3. **Análise**:
       - Faça upload de ambas as imagens
       - Configure a tolerância desejada
       - Execute a análise

    #### Teste DRMLC
    1. **Planejamento**:
       - Crie um arco VMAT com movimento de MLC em sliding window
       - Varie a taxa de dose durante o arco

    2. **Aquisição**:
       - Adquira uma imagem com o plano DRMLC
       - Adquira uma imagem de campo aberto como referência

    3. **Análise**:
       - Faça upload de ambas as imagens
       - Configure a tolerância desejada
       - Execute a análise

    ### Tolerâncias Típicas:
    - **DRGS**: ≤ 1.5% de desvio
    - **DRMLC**: ≤ 1.5% de desvio

    ### Interpretação:
    - Desvios maiores podem indicar problemas com:
      - Calibração da taxa de dose
      - Velocidade do gantry
      - Posicionamento do MLC
      - Comunicação entre sistemas
    """)
