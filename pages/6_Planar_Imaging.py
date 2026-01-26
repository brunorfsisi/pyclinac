"""
Módulo Planar Imaging - Análise de Phantomas Planares
Leeds TOR, QC-3, QC-kV, Las Vegas, Doselab MC2, PTW EPID QC
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="Planar Imaging", page_icon="📷", layout="wide")

# Importações do pylinac
try:
    from pylinac import (
        LeedsTOR, LeedsTORBlue,
        StandardImagingQC3, StandardImagingQCkV,
        LasVegas, DoselabMC2kV, DoselabMC2MV,
        PTWEPIDQC, IMTLRad, SNCkV, SNCMV
    )
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
    module_name="📷 Planar Imaging",
    description="""
    Análise de qualidade de imagem planar usando diferentes phantomas:
    Leeds TOR, Standard Imaging QC-3/QC-kV, Las Vegas, Doselab MC2, PTW EPID QC.
    """,
    references=[
        "AAPM TG-142: Quality assurance of medical accelerators",
        "ACR CT Accreditation Program"
    ]
)

st.title("📷 Análise de Imagem Planar")
st.markdown("""
Verificação de qualidade de imagem planar usando phantomas padronizados.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Seleção do phantom
phantom_options = {
    "Leeds TOR 18": "leeds",
    "Leeds TOR Blue": "leeds_blue",
    "Standard Imaging QC-3 (MV)": "qc3",
    "Standard Imaging QC-kV": "qckv",
    "Las Vegas": "lasvegas",
    "Doselab MC2 kV": "mc2kv",
    "Doselab MC2 MV": "mc2mv",
    "PTW EPID QC": "ptw",
    "IMT L'Rad": "imt",
    "SNC kV": "snckv",
    "SNC MV": "sncmv"
}

selected_phantom = st.selectbox(
    "Selecione o tipo de Phantom",
    options=list(phantom_options.keys()),
    help="Escolha o phantom utilizado para a aquisição da imagem"
)

# Descrição do phantom selecionado
phantom_descriptions = {
    "leeds": """
    **Leeds TOR 18**: Phantom para avaliação de contraste de baixa e alta frequência,
    resolução espacial e uniformidade. Contém 18 grupos de contraste circular.
    """,
    "leeds_blue": """
    **Leeds TOR Blue**: Versão azul do Leeds TOR para imagens kV.
    """,
    "qc3": """
    **Standard Imaging QC-3**: Phantom para EPID MV com ROIs de contraste e uniformidade.
    Usado para QC diário de sistemas de imagem portal.
    """,
    "qckv": """
    **Standard Imaging QC-kV**: Versão kV do QC-3 para OBI e outros sistemas kV.
    """,
    "lasvegas": """
    **Las Vegas**: Phantom com padrão de contraste em grade para avaliação
    de detectabilidade de baixo contraste.
    """,
    "mc2kv": """
    **Doselab MC2 kV**: Phantom de controle de qualidade para sistemas kV.
    """,
    "mc2mv": """
    **Doselab MC2 MV**: Phantom de controle de qualidade para sistemas MV (EPID).
    """,
    "ptw": """
    **PTW EPID QC**: Phantom específico da PTW para QC de EPID.
    """,
    "imt": """
    **IMT L'Rad**: Phantom L'Rad da IMT para QC de imagem.
    """,
    "snckv": """
    **SNC kV**: Phantom Sun Nuclear para sistemas kV.
    """,
    "sncmv": """
    **SNC MV**: Phantom Sun Nuclear para sistemas MV.
    """
}

with st.expander("ℹ️ Sobre o phantom selecionado"):
    st.markdown(phantom_descriptions.get(phantom_options[selected_phantom], "Descrição não disponível."))

st.divider()

# Upload de arquivo
uploaded_file = st.file_uploader(
    "Selecione a imagem DICOM",
    type=['dcm', 'DCM', 'tif', 'tiff'],
    help="Imagem DICOM ou TIFF do phantom"
)

# Parâmetros de análise
with st.expander("⚙️ Parâmetros de Análise", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        low_contrast_threshold = st.slider(
            "Limiar de baixo contraste (%)",
            min_value=0.1,
            max_value=5.0,
            value=0.5,
            step=0.1,
            help="Limiar de contraste para detecção de objetos de baixo contraste"
        )

        high_contrast_threshold = st.slider(
            "Limiar de alto contraste (%)",
            min_value=10.0,
            max_value=90.0,
            value=50.0,
            step=5.0,
            help="Limiar de MTF para resolução de alto contraste"
        )

    with col2:
        ssd = st.number_input(
            "SSD (mm)",
            min_value=500.0,
            max_value=2000.0,
            value=1000.0,
            step=10.0,
            help="Distância fonte-superfície"
        )

        invert = st.checkbox(
            "Inverter imagem",
            value=False,
            help="Inverte os valores de pixel da imagem"
        )

# Análise
if uploaded_file is not None:
    if st.button("🔬 Executar Análise", type="primary"):
        temp_path = save_uploaded_file(uploaded_file)

        try:
            with st.spinner(f"Analisando imagem do phantom {selected_phantom}..."):
                # Seleciona a classe apropriada
                phantom_classes = {
                    "leeds": LeedsTOR,
                    "leeds_blue": LeedsTORBlue,
                    "qc3": StandardImagingQC3,
                    "qckv": StandardImagingQCkV,
                    "lasvegas": LasVegas,
                    "mc2kv": DoselabMC2kV,
                    "mc2mv": DoselabMC2MV,
                    "ptw": PTWEPIDQC,
                    "imt": IMTLRad,
                    "snckv": SNCkV,
                    "sncmv": SNCMV
                }

                phantom_class = phantom_classes[phantom_options[selected_phantom]]
                phantom = phantom_class(temp_path)

                # Analisa
                phantom.analyze(
                    low_contrast_threshold=low_contrast_threshold/100,
                    high_contrast_threshold=high_contrast_threshold/100,
                    invert=invert,
                    ssd=ssd
                )

            st.success("✅ Análise concluída!")

            # Resultados principais
            st.subheader("📊 Resultados")

            col1, col2, col3 = st.columns(3)

            # Métricas variam por tipo de phantom
            results = phantom.results_data()

            with col1:
                if hasattr(phantom, 'mtf'):
                    mtf_50 = phantom.mtf.relative_resolution(50)
                    st.metric("MTF 50%", f"{mtf_50:.2f} lp/mm")

                if hasattr(results, 'phantom_center_x_y'):
                    st.metric("Centro do Phantom", f"({results.phantom_center_x_y[0]:.1f}, {results.phantom_center_x_y[1]:.1f})")

            with col2:
                if hasattr(phantom, 'low_contrast_rois'):
                    num_visible = len([r for r in phantom.low_contrast_rois if r.passed])
                    st.metric("ROIs de Baixo Contraste Visíveis", f"{num_visible}")

                if hasattr(results, 'phantom_angle'):
                    st.metric("Ângulo do Phantom", f"{results.phantom_angle:.1f}°")

            with col3:
                if hasattr(results, 'median_contrast'):
                    st.metric("Contraste Mediano", f"{results.median_contrast:.3f}")

                if hasattr(results, 'median_cnr'):
                    st.metric("CNR Mediano", f"{results.median_cnr:.2f}")

            # Visualização principal
            st.subheader("🖼️ Visualização")

            fig, axes = plt.subplots(1, 2, figsize=(14, 7))
            phantom.plot_analyzed_image(ax=axes[0])
            axes[0].set_title("Imagem Analisada")

            # Plot de contraste se disponível
            if hasattr(phantom, 'plot_contrast'):
                phantom.plot_contrast(ax=axes[1])
                axes[1].set_title("Curva de Contraste")
            else:
                axes[1].axis('off')

            st.pyplot(fig)
            plt.close(fig)

            # Detalhes das ROIs
            with st.expander("📋 Detalhes das ROIs"):
                if hasattr(phantom, 'low_contrast_rois'):
                    st.markdown("#### ROIs de Baixo Contraste")
                    roi_data = []
                    for i, roi in enumerate(phantom.low_contrast_rois):
                        roi_data.append({
                            "ROI": i + 1,
                            "Contraste": f"{roi.contrast:.4f}",
                            "CNR": f"{roi.cnr:.2f}" if hasattr(roi, 'cnr') else "N/A",
                            "Passou": "✅" if roi.passed else "❌"
                        })
                    st.dataframe(roi_data, use_container_width=True)

                if hasattr(phantom, 'high_contrast_rois'):
                    st.markdown("#### ROIs de Alto Contraste")
                    hc_data = []
                    for i, roi in enumerate(phantom.high_contrast_rois):
                        hc_data.append({
                            "ROI": i + 1,
                            "MTF": f"{roi.mtf:.3f}" if hasattr(roi, 'mtf') else "N/A",
                            "Frequência (lp/mm)": f"{roi.lp_mm:.2f}" if hasattr(roi, 'lp_mm') else "N/A"
                        })
                    st.dataframe(hc_data, use_container_width=True)

            # MTF se disponível
            if hasattr(phantom, 'mtf'):
                with st.expander("📈 Curva MTF"):
                    fig_mtf, ax_mtf = plt.subplots(figsize=(10, 6))

                    # Plot MTF
                    freqs = phantom.mtf.spacings
                    mtfs = phantom.mtf.values
                    ax_mtf.plot(freqs, mtfs, 'b-o', linewidth=2, markersize=8)
                    ax_mtf.axhline(y=0.5, color='r', linestyle='--', label='50% MTF')
                    ax_mtf.set_xlabel('Frequência Espacial (lp/mm)')
                    ax_mtf.set_ylabel('MTF')
                    ax_mtf.set_title('Função de Transferência de Modulação')
                    ax_mtf.legend()
                    ax_mtf.grid(True, alpha=0.3)
                    ax_mtf.set_ylim(0, 1.1)

                    st.pyplot(fig_mtf)
                    plt.close(fig_mtf)

                    # Valores de MTF
                    st.markdown("#### Valores de MTF")
                    mtf_values = {
                        "MTF 10%": f"{phantom.mtf.relative_resolution(10):.3f} lp/mm",
                        "MTF 30%": f"{phantom.mtf.relative_resolution(30):.3f} lp/mm",
                        "MTF 50%": f"{phantom.mtf.relative_resolution(50):.3f} lp/mm",
                        "MTF 80%": f"{phantom.mtf.relative_resolution(80):.3f} lp/mm"
                    }

                    col1, col2, col3, col4 = st.columns(4)
                    cols = [col1, col2, col3, col4]
                    for i, (key, value) in enumerate(mtf_values.items()):
                        with cols[i]:
                            st.metric(key, value)

            # Uniformidade se disponível
            if hasattr(phantom, 'uniformity_rois'):
                with st.expander("📊 Análise de Uniformidade"):
                    st.markdown("#### ROIs de Uniformidade")
                    unif_data = []
                    for i, roi in enumerate(phantom.uniformity_rois):
                        unif_data.append({
                            "ROI": i + 1,
                            "Valor Médio": f"{roi.pixel_value:.1f}",
                            "Desvio Padrão": f"{roi.std:.1f}" if hasattr(roi, 'std') else "N/A"
                        })
                    st.dataframe(unif_data, use_container_width=True)

            # Relatório PDF
            st.subheader("📄 Relatório")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                phantom.publish_pdf(tmp_pdf.name)
                get_pdf_download_button(tmp_pdf.name, f"planar_imaging_{phantom_options[selected_phantom]}_report.pdf")
                os.unlink(tmp_pdf.name)

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")
            st.exception(e)

        finally:
            cleanup_temp_files([temp_path])

else:
    st.info("👆 Faça upload de uma imagem para começar a análise.")

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar testes de imagem planar:

    1. **Preparação**:
       - Posicione o phantom no feixe
       - Configure o sistema de imagem (EPID, OBI, etc.)

    2. **Aquisição**:
       - Adquira a imagem conforme protocolo do fabricante
       - Salve no formato DICOM

    3. **Análise**:
       - Selecione o tipo correto de phantom
       - Faça upload da imagem
       - Ajuste os parâmetros se necessário
       - Execute a análise

    4. **Interpretação**:
       - Verifique os valores de MTF
       - Avalie os ROIs de baixo contraste
       - Compare com valores de baseline

    ### Métricas Avaliadas:

    | Métrica | Descrição |
    |---------|-----------|
    | MTF | Função de transferência de modulação (resolução espacial) |
    | CNR | Razão contraste-ruído |
    | Uniformidade | Variação de intensidade pelo campo |
    | Baixo Contraste | Detectabilidade de objetos de baixo contraste |

    ### Phantomas Suportados:

    - **Leeds TOR 18**: Análise completa de resolução e contraste
    - **QC-3/QC-kV**: QC diário de EPID e OBI
    - **Las Vegas**: Avaliação de baixo contraste
    - **MC2**: Doselab phantom para kV e MV
    - **PTW EPID QC**: Phantom PTW específico
    """)
