"""
Módulo CBCT - Análise de Phantomas de Tomografia
CatPhan, Quart DVT, ACR CT/MRI, Cheese Phantoms (TomoTherapy)
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="CBCT Analysis", page_icon="🔬", layout="wide")

# Importações do pylinac
try:
    from pylinac import (
        CatPhan503, CatPhan504, CatPhan600, CatPhan604,
        QuartDVT, ACRCT, ACRMRILarge
    )
    PYLINAC_AVAILABLE = True

    # Tenta importar phantoms adicionais
    try:
        from pylinac import ACRMRISmall
        ACR_MRI_SMALL_AVAILABLE = True
    except ImportError:
        ACR_MRI_SMALL_AVAILABLE = False

    try:
        from pylinac.cheese import TomoCheese, CheesePhantomBase
        CHEESE_AVAILABLE = True
    except ImportError:
        CHEESE_AVAILABLE = False

except ImportError:
    PYLINAC_AVAILABLE = False
    CHEESE_AVAILABLE = False
    ACR_MRI_SMALL_AVAILABLE = False

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, extract_zip_to_temp, cleanup_temp_files,
    get_pdf_download_button, create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="🔬 CBCT Analysis",
    description="""
    Análise de qualidade de imagem CBCT/CT usando phantomas padronizados:
    - **CatPhan**: 503, 504, 600, 604
    - **Quart DVT**: Sistemas DVT dental
    - **ACR CT/MRI**: Phantomas de acreditação
    - **Cheese Phantom**: TomoTherapy QA
    """,
    references=[
        "AAPM TG-142: Quality assurance of medical accelerators",
        "AAPM TG-148: QA for helical tomotherapy",
        "ACR CT/MRI Accreditation Program",
        "Catphan 500 and 600 Manual"
    ]
)

st.title("🔬 Análise de Qualidade CBCT/CT")
st.markdown("""
Verificação de qualidade de imagem de tomografia computadorizada usando phantomas padronizados.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Tabs para diferentes categorias de phantom
tab1, tab2, tab3, tab4 = st.tabs([
    "🐱 CatPhan",
    "🏥 ACR CT/MRI",
    "🦷 Quart DVT",
    "🧀 Cheese (TomoTherapy)"
])

# =============================================================================
# TAB 1 - CATPHAN
# =============================================================================
with tab1:
    st.subheader("Análise CatPhan")
    st.markdown("Phantomas CatPhan para análise completa de qualidade CT/CBCT.")

    catphan_options = {
        "CatPhan 503": CatPhan503,
        "CatPhan 504": CatPhan504,
        "CatPhan 600": CatPhan600,
        "CatPhan 604": CatPhan604
    }

    selected_catphan = st.selectbox(
        "Selecione o modelo CatPhan",
        options=list(catphan_options.keys()),
        key="catphan_select"
    )

    # Descrição do CatPhan
    catphan_info = {
        "CatPhan 503": "Módulos: CTP404 (HU), CTP486 (Uniformidade), CTP528 (Alto Contraste)",
        "CatPhan 504": "Módulos: CTP404 (HU), CTP486 (Uniformidade), CTP528 (Alto Contraste), CTP515 (Baixo Contraste)",
        "CatPhan 600": "Completo: CTP404, CTP486, CTP528, CTP515, CTP591 (Fio fino)",
        "CatPhan 604": "Versão compacta do 600 para CBCT"
    }
    st.info(catphan_info[selected_catphan])

    uploaded_catphan = st.file_uploader(
        "Upload do arquivo ZIP com os DICOMs",
        type=['zip'],
        key="catphan_upload"
    )

    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            hu_tolerance = st.number_input("Tolerância HU", 10, 100, 40, key="cat_hu")
            thickness_tolerance = st.number_input("Tolerância Espessura (mm)", 0.1, 2.0, 0.2, 0.1, key="cat_thick")

        with col2:
            scaling_tolerance = st.number_input("Tolerância Escala (mm)", 0.1, 2.0, 1.0, 0.1, key="cat_scale")
            low_contrast_tolerance = st.number_input("Tolerância Baixo Contraste", 1, 10, 2, key="cat_lc")

    with st.expander("🔧 Parâmetros Avançados"):
        col1, col2 = st.columns(2)
        with col1:
            check_uid = st.checkbox("Verificar UID da série", True, key="cat_uid")
            cnr_threshold = st.number_input("Limiar CNR", 0.5, 5.0, 2.0, 0.1, key="cat_cnr")
        with col2:
            expected_roll = st.number_input("Rotação esperada (°)", -180.0, 180.0, 0.0, 1.0, key="cat_roll")

    if uploaded_catphan:
        if st.button("🔬 Analisar CatPhan", key="analyze_catphan", type="primary"):
            temp_paths = []

            try:
                with st.spinner(f"Analisando {selected_catphan}..."):
                    temp_dir = extract_zip_to_temp(uploaded_catphan)
                    temp_paths.append(temp_dir)

                    phantom_class = catphan_options[selected_catphan]
                    phantom = phantom_class(temp_dir, check_uid=check_uid)
                    phantom.analyze(
                        hu_tolerance=hu_tolerance,
                        scaling_tolerance=scaling_tolerance,
                        thickness_tolerance=thickness_tolerance,
                        low_contrast_tolerance=low_contrast_tolerance,
                        cnr_threshold=cnr_threshold
                    )

                st.success("✅ Análise concluída!")

                # Resultados gerais
                results = phantom.results_data()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Modelo", results.phantom_model)
                with col2:
                    st.metric("Imagens", results.num_images)
                with col3:
                    if hasattr(results, 'catphan_roll_deg'):
                        st.metric("Roll", f"{results.catphan_roll_deg:.1f}°")

                # Módulos
                st.subheader("📊 Resultados por Módulo")

                # CTP404 - Sensitometria
                if hasattr(phantom, 'ctp404'):
                    with st.expander("📐 CTP404 - Sensitometria/Geometria", expanded=True):
                        ctp404 = phantom.ctp404

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Geometria**")
                            if hasattr(ctp404, 'meas_slice_thickness'):
                                st.metric("Espessura de Slice", f"{ctp404.meas_slice_thickness:.2f} mm")
                            if hasattr(ctp404, 'geometry_passed'):
                                st.metric("Geometria", "✅ Passou" if ctp404.geometry_passed else "❌ Falhou")

                        with col2:
                            st.markdown("**Valores HU**")
                            if hasattr(ctp404, 'rois'):
                                hu_data = []
                                for name, roi in ctp404.rois.items():
                                    nominal = roi.nominal_val if hasattr(roi, 'nominal_val') else 0
                                    hu_data.append({
                                        "Material": name,
                                        "HU Medido": f"{roi.pixel_value:.1f}",
                                        "HU Nominal": f"{nominal:.1f}",
                                        "Diferença": f"{abs(roi.pixel_value - nominal):.1f}",
                                        "Status": "✅" if roi.passed else "❌"
                                    })
                                st.dataframe(hu_data, use_container_width=True)

                # CTP486 - Uniformidade
                if hasattr(phantom, 'ctp486'):
                    with st.expander("⚖️ CTP486 - Uniformidade"):
                        ctp486 = phantom.ctp486
                        col1, col2 = st.columns(2)
                        with col1:
                            if hasattr(ctp486, 'uniformity_index'):
                                st.metric("Índice de Uniformidade", f"{ctp486.uniformity_index:.2f}")
                            if hasattr(ctp486, 'passed'):
                                st.metric("Status", "✅ Passou" if ctp486.passed else "❌ Falhou")
                        with col2:
                            if hasattr(ctp486, 'rois'):
                                unif_data = [{"Região": n, "HU": f"{r.pixel_value:.1f}"} for n, r in ctp486.rois.items()]
                                st.dataframe(unif_data, use_container_width=True)

                # CTP528 - Alto Contraste (MTF)
                if hasattr(phantom, 'ctp528'):
                    with st.expander("🔍 CTP528 - Resolução de Alto Contraste"):
                        ctp528 = phantom.ctp528
                        col1, col2 = st.columns(2)
                        with col1:
                            if hasattr(ctp528, 'mtf'):
                                st.metric("MTF 50%", f"{ctp528.mtf.relative_resolution(50):.2f} lp/cm")
                                st.metric("MTF 30%", f"{ctp528.mtf.relative_resolution(30):.2f} lp/cm")
                                st.metric("MTF 10%", f"{ctp528.mtf.relative_resolution(10):.2f} lp/cm")
                        with col2:
                            if hasattr(ctp528, 'mtf'):
                                fig_mtf, ax_mtf = plt.subplots(figsize=(6, 4))
                                ctp528.mtf.plot(ax=ax_mtf)
                                st.pyplot(fig_mtf)
                                plt.close(fig_mtf)

                # CTP515 - Baixo Contraste
                if hasattr(phantom, 'ctp515'):
                    with st.expander("👁️ CTP515 - Resolução de Baixo Contraste"):
                        ctp515 = phantom.ctp515
                        if hasattr(ctp515, 'rois'):
                            num_visible = len([r for r in ctp515.rois.values() if r.passed])
                            st.metric("ROIs Visíveis", num_visible)
                            st.metric("Status", "✅ Passou" if ctp515.passed else "❌ Falhou")

                # Visualização completa
                st.subheader("🖼️ Visualização")
                fig = phantom.plot_analyzed_image(show=False)
                st.pyplot(fig)
                plt.close(fig)

                # Relatório PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    phantom.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, f"catphan_{selected_catphan.lower().replace(' ', '_')}_report.pdf")
                    temp_paths.append(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                st.exception(e)
            finally:
                cleanup_temp_files(temp_paths)

# =============================================================================
# TAB 2 - ACR CT/MRI
# =============================================================================
with tab2:
    st.subheader("Análise ACR CT/MRI")
    st.markdown("Phantomas de acreditação do American College of Radiology.")

    acr_options = {"ACR CT": ACRCT, "ACR MRI Large": ACRMRILarge}
    if ACR_MRI_SMALL_AVAILABLE:
        acr_options["ACR MRI Small"] = ACRMRISmall

    selected_acr = st.selectbox(
        "Selecione o phantom ACR",
        options=list(acr_options.keys()),
        key="acr_select"
    )

    uploaded_acr = st.file_uploader(
        "Upload do arquivo ZIP com os DICOMs",
        type=['zip'],
        key="acr_upload"
    )

    with st.expander("⚙️ Parâmetros de Análise"):
        col1, col2 = st.columns(2)
        with col1:
            acr_hu_tol = st.number_input("Tolerância HU", 10, 100, 40, key="acr_hu")
        with col2:
            acr_scale_tol = st.number_input("Tolerância Escala (mm)", 0.1, 2.0, 1.0, 0.1, key="acr_scale")

    if uploaded_acr:
        if st.button("🔬 Analisar ACR", key="analyze_acr", type="primary"):
            temp_paths = []

            try:
                with st.spinner(f"Analisando {selected_acr}..."):
                    temp_dir = extract_zip_to_temp(uploaded_acr)
                    temp_paths.append(temp_dir)

                    phantom_class = acr_options[selected_acr]
                    phantom = phantom_class(temp_dir)
                    phantom.analyze()

                st.success("✅ Análise concluída!")

                # Resultados
                results = phantom.results_data()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Phantom", selected_acr)
                    st.metric("Imagens", results.num_images if hasattr(results, 'num_images') else "N/A")

                # Visualização
                st.subheader("🖼️ Visualização")
                fig = phantom.plot_analyzed_image(show=False)
                st.pyplot(fig)
                plt.close(fig)

                # PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    phantom.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, f"acr_{selected_acr.lower().replace(' ', '_')}_report.pdf")
                    temp_paths.append(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                st.exception(e)
            finally:
                cleanup_temp_files(temp_paths)

# =============================================================================
# TAB 3 - QUART DVT
# =============================================================================
with tab3:
    st.subheader("Análise Quart DVT")
    st.markdown("Phantom Quart DVT para sistemas de tomografia dental e CBCT de pequeno campo.")

    uploaded_quart = st.file_uploader(
        "Upload do arquivo ZIP com os DICOMs",
        type=['zip'],
        key="quart_upload"
    )

    with st.expander("⚙️ Parâmetros de Análise"):
        col1, col2 = st.columns(2)
        with col1:
            quart_hu_tol = st.number_input("Tolerância HU", 10, 100, 40, key="quart_hu")
        with col2:
            quart_scale_tol = st.number_input("Tolerância Escala (mm)", 0.1, 2.0, 1.0, 0.1, key="quart_scale")

    if uploaded_quart:
        if st.button("🔬 Analisar Quart DVT", key="analyze_quart", type="primary"):
            temp_paths = []

            try:
                with st.spinner("Analisando Quart DVT..."):
                    temp_dir = extract_zip_to_temp(uploaded_quart)
                    temp_paths.append(temp_dir)

                    phantom = QuartDVT(temp_dir)
                    phantom.analyze(
                        hu_tolerance=quart_hu_tol,
                        scaling_tolerance=quart_scale_tol
                    )

                st.success("✅ Análise concluída!")

                # Visualização
                st.subheader("🖼️ Visualização")
                fig = phantom.plot_analyzed_image(show=False)
                st.pyplot(fig)
                plt.close(fig)

                # PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    phantom.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, "quart_dvt_report.pdf")
                    temp_paths.append(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
                st.exception(e)
            finally:
                cleanup_temp_files(temp_paths)

# =============================================================================
# TAB 4 - CHEESE PHANTOM (TOMOTHERAPY)
# =============================================================================
with tab4:
    st.subheader("🧀 Cheese Phantom (TomoTherapy)")

    if not CHEESE_AVAILABLE:
        st.warning("""
        ⚠️ O módulo Cheese Phantom requer pylinac >= 3.10.

        O Cheese Phantom é usado para QA de TomoTherapy e sistemas helicoidais.
        Instale a versão mais recente do pylinac para habilitar esta funcionalidade.
        """)

        st.markdown("""
        ### Sobre o Cheese Phantom

        O Cheese Phantom é um phantom cilíndrico com furos para inserção de
        câmaras de ionização ou detectores, usado principalmente para:

        - Verificação de dose em TomoTherapy
        - QA de distribuição de dose helicoidal
        - Comissionamento de sistemas de entrega

        **Características:**
        - Formato cilíndrico ("queijo suíço")
        - Múltiplos furos para detectores
        - Análise de uniformidade e simetria
        """)
    else:
        st.markdown("""
        Análise do Cheese Phantom para QA de TomoTherapy e sistemas helicoidais.
        """)

        uploaded_cheese = st.file_uploader(
            "Upload do arquivo ZIP com os DICOMs",
            type=['zip'],
            key="cheese_upload"
        )

        with st.expander("⚙️ Parâmetros de Análise"):
            col1, col2 = st.columns(2)
            with col1:
                cheese_roi_size = st.number_input(
                    "Tamanho ROI (mm)",
                    min_value=1.0,
                    max_value=20.0,
                    value=5.0,
                    step=0.5,
                    key="cheese_roi"
                )
            with col2:
                cheese_tolerance = st.number_input(
                    "Tolerância (%)",
                    min_value=1.0,
                    max_value=10.0,
                    value=3.0,
                    step=0.5,
                    key="cheese_tol"
                )

        if uploaded_cheese:
            if st.button("🔬 Analisar Cheese", key="analyze_cheese", type="primary"):
                temp_paths = []

                try:
                    with st.spinner("Analisando Cheese Phantom..."):
                        temp_dir = extract_zip_to_temp(uploaded_cheese)
                        temp_paths.append(temp_dir)

                        phantom = TomoCheese(temp_dir)
                        phantom.analyze()

                    st.success("✅ Análise concluída!")

                    # Resultados
                    st.subheader("📊 Resultados")

                    if hasattr(phantom, 'results_data'):
                        results = phantom.results_data()
                        st.json(results)

                    # Visualização
                    st.subheader("🖼️ Visualização")
                    fig = phantom.plot_analyzed_image(show=False)
                    st.pyplot(fig)
                    plt.close(fig)

                    # PDF
                    st.subheader("📄 Relatório")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                        phantom.publish_pdf(tmp_pdf.name)
                        get_pdf_download_button(tmp_pdf.name, "cheese_phantom_report.pdf")
                        temp_paths.append(tmp_pdf.name)

                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                    st.exception(e)
                finally:
                    cleanup_temp_files(temp_paths)

# Instruções gerais
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar análise de QA CBCT/CT:

    1. **Preparação**:
       - Posicione o phantom no centro do campo
       - Alinhe conforme marcações do phantom

    2. **Aquisição**:
       - Execute o scan CBCT/CT com protocolo padrão
       - Exporte os slices em formato DICOM
       - Comprima em arquivo ZIP

    3. **Análise**:
       - Selecione o tipo correto de phantom
       - Configure as tolerâncias
       - Execute a análise

    ### Módulos Analisados:

    | Módulo | Parâmetros |
    |--------|------------|
    | CTP404 | Números HU, geometria, espessura |
    | CTP486 | Uniformidade |
    | CTP528 | Resolução de alto contraste (MTF) |
    | CTP515 | Resolução de baixo contraste (CNR) |

    ### Tolerâncias Típicas:

    | Parâmetro | Tolerância |
    |-----------|------------|
    | Números HU | ± 40 HU (água) |
    | Uniformidade | ≤ 2% variação |
    | Geometria | ≤ 1 mm |
    | Espessura slice | ± 0.5 mm |

    ### Phantoms Suportados:

    - **CatPhan 503/504/600/604**: Análise completa CT
    - **Quart DVT**: Sistemas dental/pequeno campo
    - **ACR CT/MRI**: Acreditação ACR
    - **Cheese Phantom**: TomoTherapy QA
    """)
