"""
Módulo Picket Fence - Análise de Posicionamento de MLC
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="Picket Fence", page_icon="🚧", layout="wide")

# Importações do pylinac
try:
    from pylinac import PicketFence
    from pylinac.picketfence import MLC, Orientation
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
    module_name="🚧 Picket Fence",
    description="""
    O teste Picket Fence verifica o posicionamento das lâminas do MLC
    analisando um padrão de "cerca" onde as lâminas formam faixas
    uniformes. Desvios indicam erros de posicionamento.
    """,
    references=[
        "Chui CS, et al. Testing of dynamic MLC. Med Phys. 1996",
        "AAPM TG-142: Quality assurance of medical accelerators"
    ]
)

st.title("🚧 Análise Picket Fence")
st.markdown("""
Verificação do posicionamento das lâminas do MLC através do padrão Picket Fence.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Upload de arquivo
uploaded_file = st.file_uploader(
    "Selecione a imagem DICOM do Picket Fence",
    type=['dcm', 'DCM', 'tif', 'tiff'],
    help="Imagem DICOM ou TIFF do padrão Picket Fence"
)

# Parâmetros de análise
with st.expander("⚙️ Parâmetros de Análise", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        # Tipo de MLC
        mlc_options = {
            "Millennium (Varian)": "millennium",
            "HD Millennium (Varian)": "hd_millennium",
            "Agility (Elekta)": "agility",
            "MLCi (Elekta)": "mlci",
            "MLCi2 (Elekta)": "mlci2",
            "Versa HD (Elekta)": "versa_hd",
            "Halcyon Distal": "halcyon_distal",
            "Halcyon Proximal": "halcyon_proximal",
        }
        mlc_type = st.selectbox(
            "Tipo de MLC",
            options=list(mlc_options.keys()),
            index=0,
            help="Selecione o modelo de MLC do seu acelerador"
        )

        # Orientação
        orientation_options = {
            "Automática": None,
            "Para cima/baixo": "up_down",
            "Esquerda/direita": "left_right"
        }
        orientation = st.selectbox(
            "Orientação das lâminas",
            options=list(orientation_options.keys()),
            index=0,
            help="Direção das lâminas na imagem"
        )

    with col2:
        # Número de pickets
        num_pickets = st.number_input(
            "Número de pickets",
            min_value=1,
            max_value=20,
            value=10,
            help="Número esperado de faixas no padrão"
        )

        # Tolerância de ação
        tolerance = st.number_input(
            "Tolerância de ação (mm)",
            min_value=0.1,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="Erro máximo tolerável para cada lâmina"
        )

        # Tolerância de erro
        action_tolerance = st.number_input(
            "Tolerância de erro (mm)",
            min_value=0.1,
            max_value=3.0,
            value=0.25,
            step=0.05,
            help="Limite para classificar como erro"
        )

# Parâmetros avançados
with st.expander("🔧 Parâmetros Avançados"):
    col1, col2 = st.columns(2)

    with col1:
        crop_mm = st.number_input(
            "Margem de corte (mm)",
            min_value=0,
            max_value=50,
            value=3,
            help="Margem a ser cortada das bordas da imagem"
        )

        sag_adjustment = st.number_input(
            "Ajuste de sag (mm)",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
            help="Compensação para sag do gantry"
        )

    with col2:
        invert = st.checkbox(
            "Inverter imagem",
            value=False,
            help="Inverte os valores de pixel da imagem"
        )

        separate_leaves = st.checkbox(
            "Separar lâminas",
            value=False,
            help="Analisa cada lâmina separadamente"
        )

        nominal_gap = st.number_input(
            "Gap nominal (mm)",
            min_value=1.0,
            max_value=50.0,
            value=3.0,
            step=0.5,
            help="Largura esperada das faixas"
        )

# Análise
if uploaded_file is not None:
    if st.button("🔬 Executar Análise", type="primary"):
        temp_path = save_uploaded_file(uploaded_file)

        try:
            with st.spinner("Analisando imagem Picket Fence..."):
                # Carrega e analisa
                pf = PicketFence(temp_path)

                # Configura orientação se especificada
                if orientation_options[orientation]:
                    orient = Orientation[orientation_options[orientation].upper()]
                else:
                    orient = None

                # Analisa
                pf.analyze(
                    tolerance=tolerance,
                    action_tolerance=action_tolerance,
                    num_pickets=num_pickets,
                    sag_adjustment=sag_adjustment,
                    orientation=orient,
                    invert=invert,
                    separate_leaves=separate_leaves,
                    nominal_gap_mm=nominal_gap
                )

            # Status da análise
            if pf.passed:
                st.success("✅ Teste APROVADO - Todas as lâminas dentro da tolerância")
            else:
                st.error("❌ Teste REPROVADO - Lâminas fora da tolerância detectadas")

            # Métricas principais
            st.subheader("📊 Resultados")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Erro Máximo",
                    f"{pf.max_error:.3f} mm",
                    delta=f"Tol: {tolerance} mm",
                    delta_color="normal" if pf.max_error <= tolerance else "off"
                )

            with col2:
                st.metric(
                    "Erro Médio Absoluto",
                    f"{pf.abs_median_error:.3f} mm"
                )

            with col3:
                st.metric(
                    "Número de Pickets",
                    f"{pf.num_pickets}"
                )

            with col4:
                percent_pass = pf.percent_passing
                st.metric(
                    "Lâminas Aprovadas",
                    f"{percent_pass:.1f}%"
                )

            # Visualização principal
            st.subheader("🖼️ Visualização")
            fig, ax = plt.subplots(figsize=(12, 8))
            pf.plot_analyzed_image(ax=ax)
            st.pyplot(fig)
            plt.close(fig)

            # Histograma de erros
            with st.expander("📈 Histograma de Erros"):
                fig_hist, ax_hist = plt.subplots(figsize=(10, 5))
                pf.plot_histogram(ax=ax_hist)
                st.pyplot(fig_hist)
                plt.close(fig_hist)

            # Detalhes por lâmina
            with st.expander("📋 Detalhes por Lâmina"):
                leaf_results = []
                for i, picket in enumerate(pf.pickets):
                    for mlc_meas in picket.mlc_meas:
                        leaf_results.append({
                            "Picket": i + 1,
                            "Lâmina": mlc_meas.leaf_num if hasattr(mlc_meas, 'leaf_num') else "N/A",
                            "Erro (mm)": f"{mlc_meas.error:.4f}",
                            "Posição": f"{mlc_meas.position:.2f}",
                            "Status": "✅" if abs(mlc_meas.error) <= tolerance else "❌"
                        })

                if leaf_results:
                    st.dataframe(leaf_results, use_container_width=True)

            # Lâminas com erro
            with st.expander("⚠️ Lâminas com Erro Acima da Tolerância"):
                failed_leaves = []
                for i, picket in enumerate(pf.pickets):
                    for mlc_meas in picket.mlc_meas:
                        if abs(mlc_meas.error) > tolerance:
                            failed_leaves.append({
                                "Picket": i + 1,
                                "Posição": f"{mlc_meas.position:.2f}",
                                "Erro (mm)": f"{mlc_meas.error:.4f}"
                            })

                if failed_leaves:
                    st.dataframe(failed_leaves, use_container_width=True)
                else:
                    st.info("Nenhuma lâmina com erro acima da tolerância.")

            # Relatório PDF
            st.subheader("📄 Relatório")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                pf.publish_pdf(tmp_pdf.name)
                get_pdf_download_button(tmp_pdf.name, "picket_fence_report.pdf")
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
    ### Como realizar o teste Picket Fence:

    1. **Preparação do plano de teste**:
       - Crie um plano com múltiplas faixas de MLC uniformes
       - Tipicamente 7-10 faixas de ~3mm de largura
       - Use todos os pares de lâminas

    2. **Aquisição da imagem**:
       - Execute o plano no EPID ou filme
       - Certifique-se de que toda a área de MLC está visível

    3. **Análise**:
       - Faça upload da imagem
       - Selecione o tipo correto de MLC
       - Configure o número de pickets
       - Execute a análise

    4. **Interpretação**:
       - Erro máximo deve ser < tolerância (tipicamente 0.5mm)
       - Identifique lâminas com erros sistemáticos

    ### Tolerâncias Típicas (TG-142):
    - **Posicionamento de MLC**: ≤ 1 mm
    - **Para IMRT de alta precisão**: ≤ 0.5 mm

    ### Padrões de MLC suportados:
    - Varian Millennium (120 lâminas)
    - Varian HD Millennium
    - Elekta Agility, MLCi, MLCi2
    - Varian Halcyon
    """)
