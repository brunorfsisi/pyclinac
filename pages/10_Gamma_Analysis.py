"""
Módulo Gamma Analysis - Análise Gamma 2D para comparação de distribuições de dose
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Gamma Analysis", page_icon="🎯", layout="wide")

# Importações
try:
    from pylinac.core.gamma import gamma_2d
    from pylinac.core.image import DicomImage, ArrayImage
    import pydicom
    GAMMA_AVAILABLE = True
except ImportError:
    try:
        # Alternativa para versões mais antigas
        from pylinac.core.image import DicomImage
        import pydicom
        GAMMA_AVAILABLE = False
    except ImportError:
        GAMMA_AVAILABLE = False

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, cleanup_temp_files, get_pdf_download_button,
    create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="🎯 Gamma Analysis",
    description="""
    Análise Gamma 2D para comparação de distribuições de dose.

    Compara uma distribuição de referência com uma avaliada usando
    critérios de distância (DTA) e diferença de dose.

    **Critérios comuns:**
    - 3%/3mm (padrão IMRT)
    - 2%/2mm (alta precisão)
    - 3%/2mm, 2%/3mm
    """,
    references=[
        "Low DA, et al. A technique for the quantitative evaluation of dose distributions. Med Phys. 1998",
        "AAPM TG-218: Tolerance limits and methodologies for IMRT QA",
        "Miften M, et al. Tolerance limits and methodologies for IMRT measurement-based verification QA. Med Phys. 2018"
    ]
)

st.title("🎯 Análise Gamma 2D")
st.markdown("""
Comparação quantitativa de distribuições de dose usando o critério Gamma.
""")

# Explicação do método Gamma
with st.expander("ℹ️ Sobre a Análise Gamma"):
    st.markdown("""
    ### O que é Análise Gamma?

    A análise Gamma é um método quantitativo para comparar duas distribuições de dose,
    tipicamente uma calculada pelo TPS e uma medida experimentalmente.

    ### Critérios Gamma

    O índice Gamma combina dois critérios:
    - **Diferença de Dose (DD)**: Diferença percentual em relação à dose máxima
    - **Distância para Concordância (DTA)**: Distância espacial mínima para encontrar concordância

    ### Interpretação

    - **γ ≤ 1**: Ponto passa nos critérios
    - **γ > 1**: Ponto falha nos critérios
    - **Taxa de Aprovação**: Porcentagem de pontos com γ ≤ 1

    ### Critérios Típicos:

    | Aplicação | Critério | Taxa Aprovação |
    |-----------|----------|----------------|
    | IMRT padrão | 3%/3mm | ≥ 95% |
    | IMRT alta precisão | 2%/2mm | ≥ 90% |
    | SRS/SBRT | 2%/1mm | ≥ 90% |
    | Verificação diária | 3%/3mm | ≥ 90% |
    """)

# Modo de entrada
st.subheader("Configuração de Entrada")

input_mode = st.radio(
    "Selecione o tipo de dados:",
    ["Imagens DICOM", "Arrays NumPy (.npy)", "Dados de Log/Fluência"],
    horizontal=True
)

# =============================================================================
# ENTRADA VIA DICOM
# =============================================================================
if input_mode == "Imagens DICOM":
    st.markdown("### Upload de Imagens DICOM")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Distribuição de Referência**")
        ref_file = st.file_uploader(
            "Imagem de referência (planejada)",
            type=['dcm', 'DCM'],
            key="gamma_ref"
        )

    with col2:
        st.markdown("**Distribuição Avaliada**")
        eval_file = st.file_uploader(
            "Imagem avaliada (medida)",
            type=['dcm', 'DCM'],
            key="gamma_eval"
        )

# =============================================================================
# ENTRADA VIA NUMPY
# =============================================================================
elif input_mode == "Arrays NumPy (.npy)":
    st.markdown("### Upload de Arrays NumPy")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Distribuição de Referência**")
        ref_file = st.file_uploader(
            "Array de referência (.npy)",
            type=['npy'],
            key="gamma_ref_npy"
        )

    with col2:
        st.markdown("**Distribuição Avaliada**")
        eval_file = st.file_uploader(
            "Array avaliado (.npy)",
            type=['npy'],
            key="gamma_eval_npy"
        )

    # Resolução espacial
    st.markdown("**Resolução Espacial**")
    col1, col2 = st.columns(2)
    with col1:
        pixel_size_x = st.number_input("Tamanho pixel X (mm)", 0.1, 5.0, 1.0, 0.1)
    with col2:
        pixel_size_y = st.number_input("Tamanho pixel Y (mm)", 0.1, 5.0, 1.0, 0.1)

# =============================================================================
# ENTRADA VIA LOG/FLUÊNCIA
# =============================================================================
else:
    st.markdown("### Análise de Fluência de Log")
    st.info("""
    Esta opção analisa a fluência planejada vs. entregue a partir de arquivos de log.
    Use o módulo Log Analyzer para carregar arquivos de log e gerar mapas de fluência.
    """)

    ref_file = None
    eval_file = None

# =============================================================================
# PARÂMETROS GAMMA
# =============================================================================
st.divider()
st.subheader("⚙️ Parâmetros Gamma")

col1, col2, col3 = st.columns(3)

with col1:
    dose_tolerance = st.number_input(
        "Tolerância de Dose (%)",
        min_value=0.5,
        max_value=10.0,
        value=3.0,
        step=0.5,
        help="Critério de diferença de dose (DD)"
    )

with col2:
    distance_tolerance = st.number_input(
        "Tolerância de Distância (mm)",
        min_value=0.5,
        max_value=10.0,
        value=3.0,
        step=0.5,
        help="Critério de distância para concordância (DTA)"
    )

with col3:
    threshold = st.number_input(
        "Limiar de Dose (%)",
        min_value=0.0,
        max_value=50.0,
        value=10.0,
        step=5.0,
        help="Pontos abaixo deste % da dose máxima são ignorados"
    )

# Parâmetros avançados
with st.expander("🔧 Parâmetros Avançados"):
    col1, col2 = st.columns(2)

    with col1:
        global_dose = st.checkbox(
            "Normalização Global",
            value=True,
            help="Usa a dose máxima global como referência"
        )

        dose_ta_only = st.checkbox(
            "Apenas Diferença de Dose",
            value=False,
            help="Ignora critério de distância"
        )

    with col2:
        interp_fraction = st.number_input(
            "Fração de Interpolação",
            min_value=1,
            max_value=10,
            value=10,
            help="Fator de superamostragem para cálculo"
        )

        max_gamma = st.number_input(
            "Gamma Máximo",
            min_value=1.0,
            max_value=5.0,
            value=2.0,
            step=0.5,
            help="Valor máximo de gamma a reportar"
        )

# =============================================================================
# ANÁLISE
# =============================================================================
st.divider()

if input_mode in ["Imagens DICOM", "Arrays NumPy (.npy)"]:
    if st.button("🔬 Calcular Análise Gamma", type="primary"):

        if input_mode == "Imagens DICOM" and ref_file and eval_file:
            ref_path = save_uploaded_file(ref_file)
            eval_path = save_uploaded_file(eval_file)
            temp_paths = [ref_path, eval_path]

            try:
                with st.spinner("Calculando análise Gamma..."):
                    # Carrega imagens DICOM
                    ref_dcm = pydicom.dcmread(ref_path)
                    eval_dcm = pydicom.dcmread(eval_path)

                    ref_array = ref_dcm.pixel_array.astype(float)
                    eval_array = eval_dcm.pixel_array.astype(float)

                    # Obtém resolução espacial do DICOM
                    if hasattr(ref_dcm, 'PixelSpacing'):
                        dpmm = 1.0 / float(ref_dcm.PixelSpacing[0])
                    else:
                        dpmm = 1.0  # 1 pixel = 1 mm como padrão

                    # Normaliza para dose máxima
                    if global_dose:
                        max_dose = max(ref_array.max(), eval_array.max())
                        ref_norm = ref_array / max_dose * 100
                        eval_norm = eval_array / max_dose * 100
                    else:
                        ref_norm = ref_array / ref_array.max() * 100
                        eval_norm = eval_array / eval_array.max() * 100

                    # Calcula Gamma manualmente se função não disponível
                    if GAMMA_AVAILABLE:
                        gamma_map = gamma_2d(
                            reference=ref_norm,
                            evaluation=eval_norm,
                            dose_to_agreement=dose_tolerance,
                            distance_to_agreement=distance_tolerance,
                            gamma_cap_value=max_gamma,
                            dose_threshold=threshold,
                            fill_value=np.nan
                        )
                    else:
                        # Implementação simplificada de Gamma
                        gamma_map = calculate_gamma_simple(
                            ref_norm, eval_norm,
                            dose_tolerance, distance_tolerance,
                            threshold, dpmm
                        )

                # Resultados
                st.success("✅ Análise Gamma concluída!")

                # Métricas
                valid_gamma = gamma_map[~np.isnan(gamma_map)]
                passing_rate = np.sum(valid_gamma <= 1.0) / len(valid_gamma) * 100 if len(valid_gamma) > 0 else 0

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    color = "normal" if passing_rate >= 95 else "off"
                    st.metric(
                        "Taxa de Aprovação",
                        f"{passing_rate:.1f}%",
                        delta=f"Critério: {dose_tolerance}%/{distance_tolerance}mm",
                        delta_color=color
                    )

                with col2:
                    st.metric("Gamma Médio", f"{np.nanmean(gamma_map):.3f}")

                with col3:
                    st.metric("Gamma Máximo", f"{np.nanmax(gamma_map):.3f}")

                with col4:
                    st.metric("Pontos Analisados", f"{len(valid_gamma)}")

                # Visualização
                st.subheader("🖼️ Visualização")

                fig, axes = plt.subplots(2, 2, figsize=(14, 12))

                # Referência
                im1 = axes[0, 0].imshow(ref_norm, cmap='jet')
                axes[0, 0].set_title('Distribuição de Referência')
                plt.colorbar(im1, ax=axes[0, 0], label='Dose (%)')

                # Avaliada
                im2 = axes[0, 1].imshow(eval_norm, cmap='jet')
                axes[0, 1].set_title('Distribuição Avaliada')
                plt.colorbar(im2, ax=axes[0, 1], label='Dose (%)')

                # Diferença
                diff = eval_norm - ref_norm
                im3 = axes[1, 0].imshow(diff, cmap='RdBu_r', vmin=-10, vmax=10)
                axes[1, 0].set_title('Diferença (Avaliada - Referência)')
                plt.colorbar(im3, ax=axes[1, 0], label='Diferença (%)')

                # Mapa Gamma
                im4 = axes[1, 1].imshow(gamma_map, cmap='RdYlGn_r', vmin=0, vmax=max_gamma)
                axes[1, 1].set_title(f'Mapa Gamma ({dose_tolerance}%/{distance_tolerance}mm)')
                plt.colorbar(im4, ax=axes[1, 1], label='Índice Gamma')

                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                # Histograma Gamma
                with st.expander("📊 Histograma Gamma"):
                    fig_hist, ax_hist = plt.subplots(figsize=(10, 5))

                    ax_hist.hist(valid_gamma, bins=50, edgecolor='black', alpha=0.7)
                    ax_hist.axvline(x=1.0, color='r', linestyle='--', linewidth=2, label='γ = 1')
                    ax_hist.set_xlabel('Índice Gamma')
                    ax_hist.set_ylabel('Frequência')
                    ax_hist.set_title('Distribuição dos Valores Gamma')
                    ax_hist.legend()
                    ax_hist.grid(True, alpha=0.3)

                    st.pyplot(fig_hist)
                    plt.close(fig_hist)

                # Estatísticas detalhadas
                with st.expander("📋 Estatísticas Detalhadas"):
                    stats_data = {
                        "Parâmetro": [
                            "Critério de Dose",
                            "Critério de Distância",
                            "Limiar de Dose",
                            "Taxa de Aprovação",
                            "Gamma Médio",
                            "Gamma Mediano",
                            "Gamma Máximo",
                            "Gamma P95",
                            "Gamma P99",
                            "Pontos Analisados",
                            "Pontos Aprovados",
                            "Pontos Reprovados"
                        ],
                        "Valor": [
                            f"{dose_tolerance}%",
                            f"{distance_tolerance} mm",
                            f"{threshold}%",
                            f"{passing_rate:.2f}%",
                            f"{np.nanmean(gamma_map):.4f}",
                            f"{np.nanmedian(gamma_map):.4f}",
                            f"{np.nanmax(gamma_map):.4f}",
                            f"{np.nanpercentile(valid_gamma, 95):.4f}" if len(valid_gamma) > 0 else "N/A",
                            f"{np.nanpercentile(valid_gamma, 99):.4f}" if len(valid_gamma) > 0 else "N/A",
                            f"{len(valid_gamma)}",
                            f"{np.sum(valid_gamma <= 1.0)}",
                            f"{np.sum(valid_gamma > 1.0)}"
                        ]
                    }
                    st.dataframe(stats_data, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files(temp_paths)

        elif input_mode == "Arrays NumPy (.npy)" and ref_file and eval_file:
            # Carrega arrays NumPy
            ref_array = np.load(ref_file)
            eval_array = np.load(eval_file)

            st.info("Análise de arrays NumPy - implemente conforme necessário")

        else:
            st.warning("Por favor, faça upload de ambas as distribuições (referência e avaliada).")


def calculate_gamma_simple(ref, eval_arr, dose_tol, dist_tol, threshold, dpmm=1.0):
    """
    Implementação simplificada do cálculo Gamma 2D.
    Para uso quando a função gamma_2d do pylinac não está disponível.
    """
    # Máscara de threshold
    mask = ref >= threshold

    # Inicializa mapa gamma
    gamma = np.full_like(ref, np.nan, dtype=float)

    # Raio de busca em pixels
    search_radius = int(np.ceil(dist_tol * dpmm)) + 1

    for i in range(ref.shape[0]):
        for j in range(ref.shape[1]):
            if not mask[i, j]:
                continue

            ref_val = ref[i, j]
            eval_val = eval_arr[i, j]

            # Diferença de dose no mesmo ponto
            dose_diff = abs(eval_val - ref_val) / dose_tol

            # Busca em vizinhança
            min_gamma = dose_diff

            for di in range(-search_radius, search_radius + 1):
                for dj in range(-search_radius, search_radius + 1):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < ref.shape[0] and 0 <= nj < ref.shape[1]:
                        dist = np.sqrt(di**2 + dj**2) / dpmm
                        if dist <= dist_tol:
                            dd = abs(eval_arr[ni, nj] - ref_val) / dose_tol
                            dta = dist / dist_tol
                            g = np.sqrt(dd**2 + dta**2)
                            min_gamma = min(min_gamma, g)

            gamma[i, j] = min_gamma

    return gamma


# Presets comuns
st.divider()
st.subheader("📋 Presets de Critérios")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("3%/3mm (IMRT)", use_container_width=True):
        st.session_state['dose_tol'] = 3.0
        st.session_state['dist_tol'] = 3.0
        st.rerun()

with col2:
    if st.button("2%/2mm (Alta Precisão)", use_container_width=True):
        st.session_state['dose_tol'] = 2.0
        st.session_state['dist_tol'] = 2.0
        st.rerun()

with col3:
    if st.button("3%/2mm", use_container_width=True):
        st.session_state['dose_tol'] = 3.0
        st.session_state['dist_tol'] = 2.0
        st.rerun()

with col4:
    if st.button("2%/1mm (SRS)", use_container_width=True):
        st.session_state['dose_tol'] = 2.0
        st.session_state['dist_tol'] = 1.0
        st.rerun()

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar análise Gamma:

    1. **Preparação**:
       - Exporte a distribuição de dose planejada do TPS
       - Adquira a medição experimental (EPID, filme, etc.)
       - Converta para formato DICOM ou array NumPy

    2. **Configuração**:
       - Selecione critérios adequados (dose % / distância mm)
       - Configure o limiar de dose
       - Ajuste parâmetros avançados se necessário

    3. **Análise**:
       - Faça upload das distribuições
       - Execute a análise
       - Avalie a taxa de aprovação

    ### Critérios Recomendados (TG-218):

    | Técnica | Critério | Taxa Mínima |
    |---------|----------|-------------|
    | IMRT | 3%/2mm global | 95% |
    | VMAT | 3%/2mm global | 95% |
    | SRS | 3%/1mm ou 2%/1mm | 90% |
    | SBRT | 3%/2mm | 90% |

    ### Notas:
    - Use normalização global para comparação absoluta
    - Limiar de 10% exclui regiões de baixa dose
    - Taxa ≥ 95% é típica para aprovação clínica
    """)
