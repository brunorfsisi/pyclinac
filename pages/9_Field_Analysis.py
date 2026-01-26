"""
Módulo Field Analysis - Análise de Campo Aberto e Perfis de Dose
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Field Analysis", page_icon="📈", layout="wide")

# Importações do pylinac
try:
    from pylinac import FieldAnalysis
    from pylinac.field_analysis import Protocol, Centering, Normalization, Edge
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
    module_name="📈 Field Analysis",
    description="""
    Análise de campos de radiação abertos incluindo:
    - Tamanho do campo
    - Flatness (planura)
    - Symmetry (simetria)
    - Penumbra
    - Perfis em linha e crossline
    """,
    references=[
        "AAPM TG-142: Quality assurance of medical accelerators",
        "IEC 60976: Medical electrical equipment - Characteristics"
    ]
)

st.title("📈 Análise de Campo")
st.markdown("""
Análise de campos de radiação abertos para verificação de planura, simetria e penumbra.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Upload de arquivo
uploaded_file = st.file_uploader(
    "Selecione a imagem do campo",
    type=['dcm', 'DCM', 'tif', 'tiff'],
    help="Imagem DICOM ou TIFF de um campo aberto"
)

# Parâmetros de análise
with st.expander("⚙️ Parâmetros de Análise", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        # Protocolo
        protocol_options = {
            "Varian": "varian",
            "Elekta": "elekta",
            "Siemens": "siemens",
            "IEC": "iec"
        }
        protocol = st.selectbox(
            "Protocolo",
            options=list(protocol_options.keys()),
            help="Protocolo para cálculo de flatness e symmetry"
        )

        # Centralização
        centering_options = {
            "Beam Center": "beam_center",
            "Geometric Center": "geometric_center",
            "Manual": "manual"
        }
        centering = st.selectbox(
            "Método de Centralização",
            options=list(centering_options.keys()),
            help="Como determinar o centro do campo"
        )

        # Detecção de borda
        edge_options = {
            "FWXM": "fwxm",
            "Inflection": "inflection",
            "Hill": "hill"
        }
        edge_method = st.selectbox(
            "Método de Detecção de Borda",
            options=list(edge_options.keys()),
            help="Algoritmo para detectar as bordas do campo"
        )

    with col2:
        # Normalização
        norm_options = {
            "Beam Center": "beam_center",
            "Geometric Center": "geometric_center",
            "Max": "max"
        }
        normalization = st.selectbox(
            "Normalização",
            options=list(norm_options.keys()),
            help="Método de normalização dos perfis"
        )

        # FWXM para detecção de borda
        fwxm_height = st.slider(
            "Altura FWXM (%)",
            min_value=10,
            max_value=90,
            value=50,
            help="Porcentagem do máximo para detecção de borda"
        )

        # Porcentagem para cálculo de flatness/symmetry
        in_field_ratio = st.slider(
            "Região In-Field (%)",
            min_value=50,
            max_value=100,
            value=80,
            help="Porcentagem do tamanho do campo para análise de flatness/symmetry"
        )

# Parâmetros avançados
with st.expander("🔧 Parâmetros Avançados"):
    col1, col2 = st.columns(2)

    with col1:
        penumbra_low = st.slider(
            "Penumbra - Limite Inferior (%)",
            min_value=5,
            max_value=40,
            value=20,
            help="Limite inferior para cálculo de penumbra"
        )

        penumbra_high = st.slider(
            "Penumbra - Limite Superior (%)",
            min_value=60,
            max_value=95,
            value=80,
            help="Limite superior para cálculo de penumbra"
        )

    with col2:
        ground = st.checkbox(
            "Subtrair Background",
            value=True,
            help="Subtrai o valor de background da imagem"
        )

        invert = st.checkbox(
            "Inverter Imagem",
            value=False,
            help="Inverte os valores de pixel"
        )

        is_fff = st.checkbox(
            "Campo FFF (Flattening Filter Free)",
            value=False,
            help="Marque se o campo é de um feixe sem filtro aplanador"
        )

# Tolerâncias
st.subheader("Tolerâncias")
col1, col2, col3 = st.columns(3)

with col1:
    flatness_tol = st.number_input(
        "Tolerância de Flatness (%)",
        min_value=1.0,
        max_value=10.0,
        value=3.0,
        step=0.5
    )

with col2:
    symmetry_tol = st.number_input(
        "Tolerância de Symmetry (%)",
        min_value=1.0,
        max_value=10.0,
        value=3.0,
        step=0.5
    )

with col3:
    penumbra_tol = st.number_input(
        "Tolerância de Penumbra (mm)",
        min_value=1.0,
        max_value=20.0,
        value=10.0,
        step=0.5
    )

# Análise
if uploaded_file is not None:
    if st.button("🔬 Analisar Campo", type="primary"):
        temp_path = save_uploaded_file(uploaded_file)

        try:
            with st.spinner("Analisando campo..."):
                # Carrega e analisa
                fa = FieldAnalysis(temp_path)

                # Configura protocolo
                protocol_map = {
                    "varian": Protocol.VARIAN,
                    "elekta": Protocol.ELEKTA,
                    "siemens": Protocol.SIEMENS,
                    "iec": Protocol.IEC
                }

                centering_map = {
                    "beam_center": Centering.BEAM_CENTER,
                    "geometric_center": Centering.GEOMETRIC_CENTER,
                    "manual": Centering.MANUAL
                }

                normalization_map = {
                    "beam_center": Normalization.BEAM_CENTER,
                    "geometric_center": Normalization.GEOMETRIC_CENTER,
                    "max": Normalization.MAX
                }

                edge_map = {
                    "fwxm": Edge.FWXM,
                    "inflection": Edge.INFLECTION,
                    "hill": Edge.HILL
                }

                fa.analyze(
                    protocol=protocol_map[protocol_options[protocol]],
                    centering=centering_map[centering_options[centering]],
                    normalization=normalization_map[norm_options[normalization]],
                    edge_detection_method=edge_map[edge_options[edge_method]],
                    edge_smoothing_ratio=0.003,
                    in_field_ratio=in_field_ratio/100,
                    slope_exclusion_ratio=0.2,
                    invert=invert,
                    ground=ground,
                    is_FFF=is_fff,
                    penumbra=(penumbra_low, penumbra_high)
                )

            st.success("✅ Análise concluída!")

            # Resultados principais
            st.subheader("📊 Resultados")

            results = fa.results_data()

            # Status de Flatness e Symmetry
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                flatness_x = results.protocol_results.get('flatness_horizontal', None)
                if flatness_x is not None:
                    status = "normal" if flatness_x <= flatness_tol else "off"
                    st.metric(
                        "Flatness Horizontal",
                        f"{flatness_x:.2f}%",
                        delta=f"Tol: {flatness_tol}%",
                        delta_color=status
                    )

            with col2:
                flatness_y = results.protocol_results.get('flatness_vertical', None)
                if flatness_y is not None:
                    status = "normal" if flatness_y <= flatness_tol else "off"
                    st.metric(
                        "Flatness Vertical",
                        f"{flatness_y:.2f}%",
                        delta=f"Tol: {flatness_tol}%",
                        delta_color=status
                    )

            with col3:
                symmetry_x = results.protocol_results.get('symmetry_horizontal', None)
                if symmetry_x is not None:
                    status = "normal" if symmetry_x <= symmetry_tol else "off"
                    st.metric(
                        "Symmetry Horizontal",
                        f"{symmetry_x:.2f}%",
                        delta=f"Tol: {symmetry_tol}%",
                        delta_color=status
                    )

            with col4:
                symmetry_y = results.protocol_results.get('symmetry_vertical', None)
                if symmetry_y is not None:
                    status = "normal" if symmetry_y <= symmetry_tol else "off"
                    st.metric(
                        "Symmetry Vertical",
                        f"{symmetry_y:.2f}%",
                        delta=f"Tol: {symmetry_tol}%",
                        delta_color=status
                    )

            # Tamanho do campo e penumbra
            st.divider()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                field_size_x = results.field_size_horizontal_mm
                st.metric("Tamanho Horizontal", f"{field_size_x:.1f} mm")

            with col2:
                field_size_y = results.field_size_vertical_mm
                st.metric("Tamanho Vertical", f"{field_size_y:.1f} mm")

            with col3:
                penumbra_left = results.penumbra_left_mm
                penumbra_right = results.penumbra_right_mm
                avg_penumbra_x = (penumbra_left + penumbra_right) / 2
                st.metric("Penumbra Horizontal (média)", f"{avg_penumbra_x:.2f} mm")

            with col4:
                penumbra_top = results.penumbra_top_mm
                penumbra_bottom = results.penumbra_bottom_mm
                avg_penumbra_y = (penumbra_top + penumbra_bottom) / 2
                st.metric("Penumbra Vertical (média)", f"{avg_penumbra_y:.2f} mm")

            # Centro do campo
            st.subheader("📍 Centro do Campo")
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Centro X (mm)", f"{results.beam_center_to_cax_x_mm:.2f}")

            with col2:
                st.metric("Centro Y (mm)", f"{results.beam_center_to_cax_y_mm:.2f}")

            # Visualização
            st.subheader("🖼️ Visualização")

            # Plot completo
            fig = fa.plot_analyzed_image()
            st.pyplot(fig)
            plt.close(fig)

            # Perfis
            with st.expander("📊 Perfis de Dose", expanded=True):
                fig_profiles, axes = plt.subplots(1, 2, figsize=(14, 5))

                # Perfil horizontal
                fa.plot_analyzed_image(show=False, ax=axes[0])
                axes[0].set_title('Imagem com Perfis')

                # Perfis separados
                fig_prof_sep, (ax_h, ax_v) = plt.subplots(1, 2, figsize=(14, 5))

                # Horizontal
                if hasattr(fa, 'horizontal_profile'):
                    profile_h = fa.horizontal_profile
                    ax_h.plot(profile_h.values, 'b-', linewidth=2)
                    ax_h.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
                    ax_h.set_title('Perfil Horizontal (Crossline)')
                    ax_h.set_xlabel('Posição (pixels)')
                    ax_h.set_ylabel('Dose Relativa (%)')
                    ax_h.grid(True, alpha=0.3)

                # Vertical
                if hasattr(fa, 'vertical_profile'):
                    profile_v = fa.vertical_profile
                    ax_v.plot(profile_v.values, 'r-', linewidth=2)
                    ax_v.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
                    ax_v.set_title('Perfil Vertical (Inline)')
                    ax_v.set_xlabel('Posição (pixels)')
                    ax_v.set_ylabel('Dose Relativa (%)')
                    ax_v.grid(True, alpha=0.3)

                plt.tight_layout()
                st.pyplot(fig_prof_sep)
                plt.close(fig_prof_sep)

            # Detalhes de penumbra
            with st.expander("📐 Detalhes de Penumbra"):
                penumbra_data = {
                    "Lado": ["Esquerda", "Direita", "Superior", "Inferior"],
                    "Penumbra (mm)": [
                        f"{penumbra_left:.2f}",
                        f"{penumbra_right:.2f}",
                        f"{penumbra_top:.2f}",
                        f"{penumbra_bottom:.2f}"
                    ],
                    "Status": [
                        "✅" if penumbra_left <= penumbra_tol else "❌",
                        "✅" if penumbra_right <= penumbra_tol else "❌",
                        "✅" if penumbra_top <= penumbra_tol else "❌",
                        "✅" if penumbra_bottom <= penumbra_tol else "❌"
                    ]
                }
                st.dataframe(penumbra_data, use_container_width=True)

            # Resumo completo
            with st.expander("📋 Resumo Completo"):
                st.markdown(f"""
                ### Configurações de Análise
                - **Protocolo**: {protocol}
                - **Centralização**: {centering}
                - **Normalização**: {normalization}
                - **Detecção de Borda**: {edge_method}
                - **Região In-Field**: {in_field_ratio}%
                - **Campo FFF**: {'Sim' if is_fff else 'Não'}

                ### Resultados
                | Parâmetro | Horizontal | Vertical |
                |-----------|------------|----------|
                | Tamanho do Campo | {field_size_x:.1f} mm | {field_size_y:.1f} mm |
                | Flatness | {flatness_x:.2f}% | {flatness_y:.2f}% |
                | Symmetry | {symmetry_x:.2f}% | {symmetry_y:.2f}% |
                | Penumbra (média) | {avg_penumbra_x:.2f} mm | {avg_penumbra_y:.2f} mm |
                """)

            # Relatório PDF
            st.subheader("📄 Relatório")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                fa.publish_pdf(tmp_pdf.name)
                get_pdf_download_button(tmp_pdf.name, "field_analysis_report.pdf")
                os.unlink(tmp_pdf.name)

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")
            st.exception(e)

        finally:
            cleanup_temp_files([temp_path])

else:
    st.info("👆 Faça upload de uma imagem de campo aberto para começar a análise.")

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar análise de campo:

    1. **Aquisição**:
       - Configure um campo aberto (ex: 10x10 cm, 20x20 cm)
       - Adquira imagem no EPID ou filme

    2. **Upload**:
       - Faça upload da imagem DICOM ou TIFF

    3. **Configuração**:
       - Selecione o protocolo do seu fabricante
       - Configure os métodos de análise
       - Ajuste as tolerâncias

    4. **Análise**:
       - Execute a análise
       - Verifique os resultados de flatness e symmetry
       - Analise os perfis de dose

    ### Definições:

    #### Flatness (Planura)
    Medida da uniformidade do campo na região central.
    - **Varian**: (Dmax - Dmin) / (Dmax + Dmin) × 100
    - **IEC**: (Dmax - Dmin) / Dcax × 100

    #### Symmetry (Simetria)
    Medida da simetria do campo em relação ao centro.
    - **Point Difference**: Máxima diferença entre pontos simétricos

    #### Penumbra
    Região de transição entre alto e baixo nível de dose.
    - Tipicamente medida entre 20% e 80% do máximo

    ### Tolerâncias Típicas (TG-142):

    | Parâmetro | Tolerância |
    |-----------|------------|
    | Flatness | ≤ 3% |
    | Symmetry | ≤ 3% |
    | Tamanho do Campo | ± 2 mm |

    ### Campos FFF:

    Para campos sem filtro aplanador (FFF):
    - O perfil tem formato de "cone"
    - Flatness padrão não se aplica
    - Marque a opção "Campo FFF" para análise apropriada
    """)
