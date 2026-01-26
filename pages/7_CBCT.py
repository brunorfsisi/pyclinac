"""
Módulo CBCT - Análise de Phantomas de Tomografia
CatPhan, Quart DVT, ACR CT, Cheese Phantoms
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt
import zipfile

st.set_page_config(page_title="CBCT Analysis", page_icon="🔬", layout="wide")

# Importações do pylinac
try:
    from pylinac import (
        CatPhan503, CatPhan504, CatPhan600, CatPhan604,
        QuartDVT, ACRCT, ACRMRILarge
    )
    from pylinac.ct import CatPhanBase
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

# Adiciona path do utils
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
    Análise de qualidade de imagem CBCT usando phantomas padronizados:
    CatPhan (503, 504, 600, 604), Quart DVT, ACR CT/MRI.
    """,
    references=[
        "AAPM TG-142: Quality assurance of medical accelerators",
        "ACR CT Accreditation Program",
        "Catphan 500 and 600 Manual"
    ]
)

st.title("🔬 Análise de Qualidade CBCT")
st.markdown("""
Verificação de qualidade de imagem de tomografia computadorizada usando phantomas padronizados.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Seleção do phantom
phantom_options = {
    "CatPhan 503": "catphan503",
    "CatPhan 504": "catphan504",
    "CatPhan 600": "catphan600",
    "CatPhan 604": "catphan604",
    "Quart DVT": "quartdvt",
    "ACR CT": "acrct",
    "ACR MRI Large": "acrmri"
}

selected_phantom = st.selectbox(
    "Selecione o tipo de Phantom",
    options=list(phantom_options.keys()),
    help="Escolha o phantom utilizado para o scan CBCT"
)

# Descrição do phantom
phantom_descriptions = {
    "catphan503": """
    **CatPhan 503**: Phantom básico com módulos para:
    - CTP404: Sensitometria (números HU)
    - CTP486: Uniformidade
    - CTP528: Resolução espacial de alto contraste
    """,
    "catphan504": """
    **CatPhan 504**: Phantom com módulos:
    - CTP404: Sensitometria (números HU)
    - CTP486: Uniformidade
    - CTP528: Resolução espacial
    - CTP515: Baixo contraste
    """,
    "catphan600": """
    **CatPhan 600**: Phantom completo com:
    - CTP404: Sensitometria
    - CTP486: Uniformidade
    - CTP528: Resolução espacial
    - CTP515: Baixo contraste
    - CTP591: Análise de fio fino
    """,
    "catphan604": """
    **CatPhan 604**: Versão compacta do 600 para CBCT.
    """,
    "quartdvt": """
    **Quart DVT**: Phantom específico para sistemas DVT dental e CBCT pequeno campo.
    """,
    "acrct": """
    **ACR CT**: Phantom de acreditação do American College of Radiology para CT.
    """,
    "acrmri": """
    **ACR MRI Large**: Phantom de acreditação ACR para ressonância magnética.
    """
}

with st.expander("ℹ️ Sobre o phantom selecionado"):
    st.markdown(phantom_descriptions.get(phantom_options[selected_phantom], ""))

st.divider()

# Upload de arquivos
st.markdown("### Upload de Imagens DICOM")
st.markdown("""
Faça upload de um arquivo ZIP contendo os slices DICOM do scan CBCT,
ou selecione múltiplos arquivos DICOM diretamente.
""")

upload_method = st.radio(
    "Método de upload:",
    ["Arquivo ZIP", "Múltiplos arquivos DICOM"],
    horizontal=True
)

uploaded_data = None

if upload_method == "Arquivo ZIP":
    uploaded_data = st.file_uploader(
        "Selecione o arquivo ZIP com os DICOMs",
        type=['zip'],
        key="cbct_zip"
    )
else:
    uploaded_data = st.file_uploader(
        "Selecione os arquivos DICOM",
        type=['dcm', 'DCM'],
        accept_multiple_files=True,
        key="cbct_multi"
    )

# Parâmetros de análise
with st.expander("⚙️ Parâmetros de Análise", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        hu_tolerance = st.number_input(
            "Tolerância HU",
            min_value=10,
            max_value=100,
            value=40,
            help="Tolerância para valores de número CT (HU)"
        )

        thickness_tolerance = st.number_input(
            "Tolerância de espessura (mm)",
            min_value=0.1,
            max_value=2.0,
            value=0.2,
            step=0.1,
            help="Tolerância para medição de espessura de corte"
        )

    with col2:
        scaling_tolerance = st.number_input(
            "Tolerância de escala (mm)",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Tolerância para geometria/escala"
        )

        low_contrast_tolerance = st.number_input(
            "Tolerância baixo contraste",
            min_value=1,
            max_value=10,
            value=2,
            help="Número mínimo de ROIs de baixo contraste visíveis"
        )

# Parâmetros avançados
with st.expander("🔧 Parâmetros Avançados"):
    col1, col2 = st.columns(2)

    with col1:
        check_uid = st.checkbox(
            "Verificar UID",
            value=True,
            help="Verifica se todas as imagens pertencem à mesma série"
        )

        expected_roll = st.number_input(
            "Rotação esperada (°)",
            min_value=-180.0,
            max_value=180.0,
            value=0.0,
            step=1.0,
            help="Ângulo de rotação esperado do phantom"
        )

    with col2:
        cnr_threshold = st.number_input(
            "Limiar CNR",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Limiar de CNR para baixo contraste"
        )

# Análise
if uploaded_data is not None:
    # Verifica se há dados para analisar
    has_data = (upload_method == "Arquivo ZIP" and uploaded_data) or \
               (upload_method != "Arquivo ZIP" and uploaded_data and len(uploaded_data) > 1)

    if has_data:
        if st.button("🔬 Executar Análise", type="primary"):
            temp_paths = []

            try:
                with st.spinner(f"Carregando e analisando imagens do {selected_phantom}..."):
                    # Prepara os arquivos
                    if upload_method == "Arquivo ZIP":
                        temp_dir = extract_zip_to_temp(uploaded_data)
                        temp_paths.append(temp_dir)
                        image_path = temp_dir
                    else:
                        temp_dir = tempfile.mkdtemp()
                        temp_paths.append(temp_dir)
                        for uf in uploaded_data:
                            file_path = os.path.join(temp_dir, uf.name)
                            with open(file_path, 'wb') as f:
                                f.write(uf.getvalue())
                        image_path = temp_dir

                    # Seleciona a classe apropriada
                    phantom_classes = {
                        "catphan503": CatPhan503,
                        "catphan504": CatPhan504,
                        "catphan600": CatPhan600,
                        "catphan604": CatPhan604,
                        "quartdvt": QuartDVT,
                        "acrct": ACRCT,
                        "acrmri": ACRMRILarge
                    }

                    phantom_class = phantom_classes[phantom_options[selected_phantom]]

                    # Carrega e analisa
                    phantom = phantom_class(image_path, check_uid=check_uid)
                    phantom.analyze(
                        hu_tolerance=hu_tolerance,
                        scaling_tolerance=scaling_tolerance,
                        thickness_tolerance=thickness_tolerance,
                        low_contrast_tolerance=low_contrast_tolerance,
                        cnr_threshold=cnr_threshold
                    )

                st.success("✅ Análise concluída!")

                # Resultados por módulo
                st.subheader("📊 Resultados")

                # Status geral
                results = phantom.results_data()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Phantom",
                        results.phantom_model
                    )

                with col2:
                    st.metric(
                        "Número de Imagens",
                        f"{results.num_images}"
                    )

                with col3:
                    st.metric(
                        "Ângulo Roll",
                        f"{results.catphan_roll_deg:.1f}°" if hasattr(results, 'catphan_roll_deg') else "N/A"
                    )

                st.divider()

                # Módulo CTP404 - Sensitometria/Geometria
                if hasattr(phantom, 'ctp404'):
                    st.markdown("### 📐 CTP404 - Sensitometria e Geometria")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Geometria
                        st.markdown("#### Geometria")
                        ctp404 = phantom.ctp404

                        geom_data = {
                            "Distância Topo": f"{ctp404.origin_slice:.1f} mm" if hasattr(ctp404, 'origin_slice') else "N/A",
                            "Espessura Slice": f"{ctp404.meas_slice_thickness:.2f} mm" if hasattr(ctp404, 'meas_slice_thickness') else "N/A",
                        }

                        for key, val in geom_data.items():
                            st.metric(key, val)

                    with col2:
                        # Valores HU
                        st.markdown("#### Valores HU")

                        if hasattr(ctp404, 'rois'):
                            hu_data = []
                            for name, roi in ctp404.rois.items():
                                hu_data.append({
                                    "Material": name,
                                    "HU Medido": f"{roi.pixel_value:.1f}",
                                    "HU Nominal": f"{roi.nominal_val:.1f}" if hasattr(roi, 'nominal_val') else "N/A",
                                    "Diferença": f"{abs(roi.pixel_value - roi.nominal_val):.1f}" if hasattr(roi, 'nominal_val') else "N/A",
                                    "Passou": "✅" if roi.passed else "❌"
                                })
                            st.dataframe(hu_data, use_container_width=True)

                # Módulo CTP486 - Uniformidade
                if hasattr(phantom, 'ctp486'):
                    st.markdown("### ⚖️ CTP486 - Uniformidade")

                    ctp486 = phantom.ctp486

                    col1, col2 = st.columns(2)

                    with col1:
                        if hasattr(ctp486, 'uniformity_index'):
                            st.metric("Índice de Uniformidade", f"{ctp486.uniformity_index:.2f}")
                        if hasattr(ctp486, 'integral_non_uniformity'):
                            st.metric("Não-Uniformidade Integral", f"{ctp486.integral_non_uniformity:.4f}")

                    with col2:
                        if hasattr(ctp486, 'rois'):
                            unif_data = []
                            for name, roi in ctp486.rois.items():
                                unif_data.append({
                                    "Região": name,
                                    "HU": f"{roi.pixel_value:.1f}",
                                    "Std": f"{roi.std:.1f}" if hasattr(roi, 'std') else "N/A"
                                })
                            st.dataframe(unif_data, use_container_width=True)

                # Módulo CTP528 - Alto Contraste
                if hasattr(phantom, 'ctp528'):
                    st.markdown("### 🔍 CTP528 - Resolução de Alto Contraste")

                    ctp528 = phantom.ctp528

                    col1, col2 = st.columns(2)

                    with col1:
                        if hasattr(ctp528, 'mtf'):
                            st.metric("MTF 50%", f"{ctp528.mtf.relative_resolution(50):.2f} lp/cm")
                            st.metric("MTF 30%", f"{ctp528.mtf.relative_resolution(30):.2f} lp/cm")
                            st.metric("MTF 10%", f"{ctp528.mtf.relative_resolution(10):.2f} lp/cm")

                    with col2:
                        # Plot MTF
                        if hasattr(ctp528, 'mtf'):
                            fig_mtf, ax_mtf = plt.subplots(figsize=(6, 4))
                            ctp528.mtf.plot(ax=ax_mtf)
                            ax_mtf.set_title('Curva MTF')
                            st.pyplot(fig_mtf)
                            plt.close(fig_mtf)

                # Módulo CTP515 - Baixo Contraste
                if hasattr(phantom, 'ctp515'):
                    st.markdown("### 👁️ CTP515 - Resolução de Baixo Contraste")

                    ctp515 = phantom.ctp515

                    col1, col2 = st.columns(2)

                    with col1:
                        if hasattr(ctp515, 'rois'):
                            num_visible = len([r for r in ctp515.rois.values() if r.passed])
                            st.metric("ROIs Visíveis", f"{num_visible}")
                            st.metric("CNR Limite", f"{cnr_threshold}")

                    with col2:
                        if hasattr(ctp515, 'rois'):
                            lc_data = []
                            for name, roi in ctp515.rois.items():
                                lc_data.append({
                                    "ROI": name,
                                    "CNR": f"{roi.cnr:.2f}" if hasattr(roi, 'cnr') else "N/A",
                                    "Visível": "✅" if roi.passed else "❌"
                                })
                            st.dataframe(lc_data[:10], use_container_width=True)

                # Visualização completa
                st.subheader("🖼️ Visualização dos Módulos")

                # Plot de cada módulo
                fig = phantom.plot_analyzed_image()
                st.pyplot(fig)
                plt.close(fig)

                # Imagens individuais dos módulos
                with st.expander("📸 Imagens Individuais dos Módulos"):
                    modules = []
                    if hasattr(phantom, 'ctp404'):
                        modules.append(('CTP404', phantom.ctp404))
                    if hasattr(phantom, 'ctp486'):
                        modules.append(('CTP486', phantom.ctp486))
                    if hasattr(phantom, 'ctp528'):
                        modules.append(('CTP528', phantom.ctp528))
                    if hasattr(phantom, 'ctp515'):
                        modules.append(('CTP515', phantom.ctp515))

                    for name, module in modules:
                        st.markdown(f"#### {name}")
                        fig_mod, ax_mod = plt.subplots(figsize=(8, 8))
                        module.plot(ax=ax_mod)
                        st.pyplot(fig_mod)
                        plt.close(fig_mod)

                # Relatório PDF
                st.subheader("📄 Relatório")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    phantom.publish_pdf(tmp_pdf.name)
                    get_pdf_download_button(tmp_pdf.name, f"cbct_{phantom_options[selected_phantom]}_report.pdf")
                    temp_paths.append(tmp_pdf.name)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files(temp_paths)

    else:
        if upload_method != "Arquivo ZIP":
            st.warning("⚠️ Selecione múltiplos arquivos DICOM (pelo menos 2).")

else:
    st.info("👆 Faça upload das imagens CBCT para começar a análise.")

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar análise de QA de CBCT:

    1. **Preparação**:
       - Posicione o phantom no centro do campo
       - Alinhe conforme marcações do phantom

    2. **Aquisição**:
       - Execute o scan CBCT com protocolo padrão
       - Exporte os slices em formato DICOM

    3. **Upload**:
       - Comprima os arquivos DICOM em um ZIP
       - Ou selecione múltiplos arquivos DICOM

    4. **Análise**:
       - Selecione o tipo correto de phantom
       - Configure as tolerâncias
       - Execute a análise

    5. **Interpretação**:
       - Verifique os valores HU dos materiais de referência
       - Avalie a uniformidade
       - Verifique a resolução espacial (MTF)
       - Avalie a visibilidade de baixo contraste

    ### Módulos do CatPhan:

    | Módulo | Parâmetros Avaliados |
    |--------|---------------------|
    | CTP404 | Números HU, geometria, espessura de slice |
    | CTP486 | Uniformidade do campo |
    | CTP528 | Resolução de alto contraste (MTF) |
    | CTP515 | Resolução de baixo contraste (CNR) |

    ### Tolerâncias Típicas:

    - **Números HU**: ± 40 HU para água
    - **Uniformidade**: ≤ 2% variação
    - **Geometria**: ≤ 1 mm de erro
    - **Espessura de slice**: ± 0.5 mm
    """)
