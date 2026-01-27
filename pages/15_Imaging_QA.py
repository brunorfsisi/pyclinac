"""
Imaging QA - kV e EPID
Controle de qualidade para sistemas de imagem
"""

import streamlit as st
from datetime import datetime, date
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Imaging QA", page_icon="📷", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info, save_uploaded_file

create_sidebar_info(
    module_name="📷 Imaging QA",
    description="""
    Controle de qualidade para sistemas de imagem.

    **kV Imaging (OBI/XVI):**
    - Qualidade de imagem 2D
    - Coincidência kV-MV
    - Escala e distorção
    - CBCT (ver módulo CBCT)

    **EPID (Portal Imaging):**
    - Uniformidade
    - Resolução espacial
    - Resposta dosimétrica
    - Calibração

    **Referências:**
    - AAPM TG-142
    - TG-179 (IGRT)
    """,
    references=[
        ("AAPM TG-142", "https://www.aapm.org/pubs/reports/detail.asp?docid=104"),
        ("AAPM TG-179", "https://www.aapm.org/pubs/reports/detail.asp?docid=106")
    ]
)

st.title("📷 Imaging QA")
st.markdown("### Controle de Qualidade de Sistemas de Imagem")

# Tabs principais
tab1, tab2, tab3 = st.tabs([
    "🔆 kV Imaging (OBI)",
    "📺 EPID",
    "📊 Histórico"
])

# Configurações comuns
with st.sidebar:
    st.subheader("Configurações")

    if DB_AVAILABLE:
        db = get_database()
        machines = db.get_machines()
        machine_names = [m['name'] for m in machines] if machines else ["Não cadastrada"]
        machine = st.selectbox("Máquina", options=machine_names, key="img_machine")
    else:
        machine = st.text_input("Máquina", value="TrueBeam", key="img_machine")

    operator = st.text_input("Operador", key="img_operator")
    test_date = st.date_input("Data", value=date.today(), key="img_date")

# =============================================================================
# TAB 1: kV IMAGING (OBI)
# =============================================================================
with tab1:
    st.subheader("🔆 kV Imaging QA (OBI/XVI)")

    kv_tabs = st.tabs([
        "📐 Coincidência kV-MV",
        "📏 Escala e Distorção",
        "🎯 Qualidade de Imagem",
        "💡 Dose kV"
    ])

    # --- Coincidência kV-MV ---
    with kv_tabs[0]:
        st.markdown("#### Coincidência do Isocentro kV-MV")

        st.markdown("""
        Verifica se o isocentro do sistema kV coincide com o isocentro MV.

        **Método:**
        1. Posicionar phantom BB no isocentro MV (usando luz/lasers)
        2. Adquirir imagem kV
        3. Medir offset do BB na imagem

        **Tolerância TG-142:** ±2 mm
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Offset kV-MV (Lateral)**")
            kv_offset_lat = st.number_input(
                "Offset Lateral (mm)",
                value=0.0,
                step=0.1,
                format="%.2f",
                key="kv_lat"
            )

            st.markdown("**Offset kV-MV (Longitudinal)**")
            kv_offset_long = st.number_input(
                "Offset Longitudinal (mm)",
                value=0.0,
                step=0.1,
                format="%.2f",
                key="kv_long"
            )

        with col2:
            st.markdown("**Offset kV-MV (Vertical)**")
            kv_offset_vert = st.number_input(
                "Offset Vertical (mm)",
                value=0.0,
                step=0.1,
                format="%.2f",
                key="kv_vert"
            )

            # Calcular offset total 3D
            offset_3d = np.sqrt(kv_offset_lat**2 + kv_offset_long**2 + kv_offset_vert**2)
            st.metric("Offset 3D Total", f"{offset_3d:.2f} mm")

        kv_mv_tolerance = 2.0  # mm
        if offset_3d <= kv_mv_tolerance:
            st.success(f"✅ APROVADO - Offset 3D: {offset_3d:.2f} mm (Tolerância: ±{kv_mv_tolerance} mm)")
            kv_mv_passed = True
        else:
            st.error(f"❌ REPROVADO - Offset 3D: {offset_3d:.2f} mm (Tolerância: ±{kv_mv_tolerance} mm)")
            kv_mv_passed = False

        # Gráfico de offset
        fig, ax = plt.subplots(figsize=(6, 6))

        # Círculo de tolerância
        theta = np.linspace(0, 2*np.pi, 100)
        ax.plot(kv_mv_tolerance * np.cos(theta), kv_mv_tolerance * np.sin(theta),
               'r--', label=f'Tolerância ({kv_mv_tolerance} mm)')

        # Ponto medido
        ax.scatter([kv_offset_lat], [kv_offset_long], s=200, c='blue', marker='x',
                  linewidths=3, label=f'Offset medido')
        ax.scatter([0], [0], s=100, c='green', marker='+', linewidths=2, label='Isocentro')

        ax.set_xlabel('Lateral (mm)')
        ax.set_ylabel('Longitudinal (mm)')
        ax.set_title('Coincidência kV-MV (Vista Superior)')
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        ax.set_aspect('equal')
        ax.legend()
        ax.grid(True, alpha=0.3)

        st.pyplot(fig)
        plt.close()

    # --- Escala e Distorção ---
    with kv_tabs[1]:
        st.markdown("#### Verificação de Escala e Distorção")

        st.markdown("""
        Verifica a precisão das medidas de distância nas imagens kV.

        **Tolerâncias TG-142:**
        - Precisão de escala: ±2%
        - Distorção: < 2%
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Escala Horizontal**")
            known_dist_h = st.number_input(
                "Distância conhecida H (mm)",
                value=100.0,
                step=1.0,
                key="known_h"
            )
            measured_dist_h = st.number_input(
                "Distância medida H (mm)",
                value=100.0,
                step=0.1,
                key="meas_h"
            )

            if known_dist_h > 0:
                scale_error_h = ((measured_dist_h - known_dist_h) / known_dist_h) * 100
                st.metric("Erro de Escala H", f"{scale_error_h:+.2f}%")

        with col2:
            st.markdown("**Escala Vertical**")
            known_dist_v = st.number_input(
                "Distância conhecida V (mm)",
                value=100.0,
                step=1.0,
                key="known_v"
            )
            measured_dist_v = st.number_input(
                "Distância medida V (mm)",
                value=100.0,
                step=0.1,
                key="meas_v"
            )

            if known_dist_v > 0:
                scale_error_v = ((measured_dist_v - known_dist_v) / known_dist_v) * 100
                st.metric("Erro de Escala V", f"{scale_error_v:+.2f}%")

        # Distorção (diferença entre H e V)
        if known_dist_h > 0 and known_dist_v > 0:
            distortion = abs(scale_error_h - scale_error_v)
            st.metric("Distorção", f"{distortion:.2f}%")

            scale_tolerance = 2.0  # %
            max_scale_error = max(abs(scale_error_h), abs(scale_error_v))

            if max_scale_error <= scale_tolerance and distortion <= scale_tolerance:
                st.success(f"✅ APROVADO (Tolerância: ±{scale_tolerance}%)")
                scale_passed = True
            else:
                st.error(f"❌ REPROVADO (Tolerância: ±{scale_tolerance}%)")
                scale_passed = False

    # --- Qualidade de Imagem ---
    with kv_tabs[2]:
        st.markdown("#### Qualidade de Imagem kV")

        st.markdown("""
        Avaliação qualitativa e quantitativa da qualidade de imagem.

        **Parâmetros avaliados:**
        - Resolução espacial (pares de linha/mm)
        - Contraste de baixo contraste
        - Uniformidade
        - Ruído
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Resolução Espacial**")
            resolution_lp = st.selectbox(
                "Resolução visível (lp/mm)",
                [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0],
                index=5,
                key="kv_resolution"
            )

            baseline_resolution = st.number_input(
                "Resolução baseline (lp/mm)",
                value=1.0,
                step=0.1,
                key="baseline_res"
            )

            if baseline_resolution > 0:
                res_diff = resolution_lp - baseline_resolution
                st.metric("Diferença do Baseline", f"{res_diff:+.1f} lp/mm")

        with col2:
            st.markdown("**Contraste**")
            contrast_visible = st.number_input(
                "Menor objeto visível (mm)",
                value=3.0,
                step=0.5,
                key="contrast_obj"
            )

            st.markdown("**Uniformidade**")
            uniformity_ok = st.checkbox("Uniformidade visual OK", key="kv_uniform")

            st.markdown("**Artefatos**")
            artifacts_ok = st.checkbox("Sem artefatos significativos", key="kv_artifacts")

        image_quality_passed = uniformity_ok and artifacts_ok and resolution_lp >= 0.8

        if image_quality_passed:
            st.success("✅ Qualidade de imagem APROVADA")
        else:
            st.warning("⚠️ Verificar qualidade de imagem")

    # --- Dose kV ---
    with kv_tabs[3]:
        st.markdown("#### Dose do Sistema kV")

        st.markdown("""
        Monitoramento da dose de radiação do sistema kV.

        **Importante:** Aumento de dose pode indicar degradação do tubo ou filtros.
        """)

        col1, col2 = st.columns(2)

        with col1:
            kv_dose_mode = st.selectbox(
                "Modo de aquisição",
                ["Pelvis", "Chest", "Head", "CBCT Pelvis", "CBCT Head"],
                key="kv_dose_mode"
            )

            kv_dose_measured = st.number_input(
                "Dose medida (mGy)",
                value=2.0,
                step=0.1,
                key="kv_dose_meas"
            )

        with col2:
            kv_dose_baseline = st.number_input(
                "Dose baseline (mGy)",
                value=2.0,
                step=0.1,
                key="kv_dose_base"
            )

            if kv_dose_baseline > 0:
                dose_diff = ((kv_dose_measured - kv_dose_baseline) / kv_dose_baseline) * 100
                st.metric("Variação do Baseline", f"{dose_diff:+.1f}%")

        dose_tolerance = 20  # %
        if kv_dose_baseline > 0:
            if abs(dose_diff) <= dose_tolerance:
                st.success(f"✅ Dose dentro da tolerância (±{dose_tolerance}%)")
                kv_dose_passed = True
            else:
                st.warning(f"⚠️ Dose fora da tolerância (±{dose_tolerance}%)")
                kv_dose_passed = False

# =============================================================================
# TAB 2: EPID
# =============================================================================
with tab2:
    st.subheader("📺 EPID QA (Electronic Portal Imaging)")

    epid_tabs = st.tabs([
        "📊 Uniformidade",
        "🔍 Resolução",
        "💊 Dosimetria",
        "🔧 Calibração"
    ])

    # --- Uniformidade ---
    with epid_tabs[0]:
        st.markdown("#### Uniformidade do EPID")

        st.markdown("""
        Verifica a uniformidade de resposta do detector EPID.

        **Método:**
        1. Adquirir imagem com campo aberto uniforme
        2. Analisar variação de sinal em ROIs

        **Tolerância:** Uniformidade < 5% (após correção de flood field)
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Valores de ROIs (5 pontos)**")

            roi_center = st.number_input("ROI Centro", value=1000.0, step=1.0, key="roi_c")
            roi_top = st.number_input("ROI Superior", value=998.0, step=1.0, key="roi_t")
            roi_bottom = st.number_input("ROI Inferior", value=1002.0, step=1.0, key="roi_b")
            roi_left = st.number_input("ROI Esquerda", value=999.0, step=1.0, key="roi_l")
            roi_right = st.number_input("ROI Direita", value=1001.0, step=1.0, key="roi_r")

        with col2:
            rois = [roi_center, roi_top, roi_bottom, roi_left, roi_right]
            mean_roi = np.mean(rois)
            max_dev = np.max(np.abs(np.array(rois) - mean_roi))
            uniformity = (max_dev / mean_roi) * 100 if mean_roi > 0 else 0

            st.markdown("**Análise**")
            st.metric("Valor Médio", f"{mean_roi:.1f}")
            st.metric("Desvio Máximo", f"{max_dev:.1f}")
            st.metric("Uniformidade", f"{uniformity:.2f}%")

            uniformity_tol = 5.0  # %
            if uniformity <= uniformity_tol:
                st.success(f"✅ APROVADO (Tolerância: {uniformity_tol}%)")
                epid_uniform_passed = True
            else:
                st.error(f"❌ REPROVADO (Tolerância: {uniformity_tol}%)")
                epid_uniform_passed = False

    # --- Resolução ---
    with epid_tabs[1]:
        st.markdown("#### Resolução Espacial do EPID")

        st.markdown("""
        Verifica a resolução espacial do detector EPID.

        **Método:** Imagem de phantom de resolução ou análise MTF
        """)

        col1, col2 = st.columns(2)

        with col1:
            epid_resolution = st.selectbox(
                "Resolução visível (lp/mm)",
                [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                index=3,
                key="epid_res"
            )

            epid_res_baseline = st.number_input(
                "Baseline (lp/mm)",
                value=0.6,
                step=0.1,
                key="epid_res_base"
            )

        with col2:
            if epid_res_baseline > 0:
                res_ratio = (epid_resolution / epid_res_baseline) * 100
                st.metric("% do Baseline", f"{res_ratio:.0f}%")

                if res_ratio >= 80:
                    st.success("✅ Resolução OK (>80% do baseline)")
                    epid_res_passed = True
                else:
                    st.error("❌ Resolução degradada (<80% do baseline)")
                    epid_res_passed = False

    # --- Dosimetria ---
    with epid_tabs[2]:
        st.markdown("#### Dosimetria EPID")

        st.markdown("""
        Calibração e verificação da resposta dosimétrica do EPID.

        **Aplicações:**
        - QA de IMRT/VMAT (portal dosimetry)
        - Verificação de dose in-vivo
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Resposta vs Dose**")

            doses = [10, 25, 50, 100, 200, 400]
            readings = []

            for dose in doses:
                reading = st.number_input(
                    f"{dose} MU",
                    value=float(dose) * 10,  # Resposta típica
                    step=1.0,
                    key=f"epid_dose_{dose}"
                )
                readings.append(reading)

        with col2:
            if readings:
                # Calcular linearidade
                doses_array = np.array(doses)
                readings_array = np.array(readings)

                # Ajuste linear
                coeffs = np.polyfit(doses_array, readings_array, 1)
                fit_line = np.polyval(coeffs, doses_array)

                # R²
                ss_res = np.sum((readings_array - fit_line) ** 2)
                ss_tot = np.sum((readings_array - np.mean(readings_array)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                st.metric("R² (Linearidade)", f"{r_squared:.6f}")
                st.metric("Sensibilidade", f"{coeffs[0]:.2f} counts/MU")

                if r_squared >= 0.999:
                    st.success("✅ Linearidade excelente")
                    epid_linear_passed = True
                elif r_squared >= 0.995:
                    st.success("✅ Linearidade adequada")
                    epid_linear_passed = True
                else:
                    st.error("❌ Verificar linearidade")
                    epid_linear_passed = False

        # Gráfico de linearidade
        if readings:
            fig, ax = plt.subplots(figsize=(8, 5))

            ax.scatter(doses, readings, s=100, c='blue', label='Medido')
            ax.plot(doses, fit_line, 'r--', linewidth=2, label=f'Ajuste (R²={r_squared:.4f})')

            ax.set_xlabel('Dose (MU)')
            ax.set_ylabel('Resposta EPID')
            ax.set_title('Linearidade EPID')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    # --- Calibração ---
    with epid_tabs[3]:
        st.markdown("#### Status de Calibração")

        st.markdown("""
        Verificação e registro das calibrações do EPID.
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Dark Field**")
            dark_field_date = st.date_input("Data da última calibração", key="dark_date")
            dark_field_ok = st.checkbox("Dark field OK", key="dark_ok")

            st.markdown("**Flood Field**")
            flood_field_date = st.date_input("Data da última calibração", key="flood_date")
            flood_field_ok = st.checkbox("Flood field OK", key="flood_ok")

        with col2:
            st.markdown("**Pixel Defects**")
            bad_pixels = st.number_input("Número de pixels defeituosos", value=0, step=1, key="bad_px")
            bad_pixels_baseline = st.number_input("Baseline", value=50, step=1, key="bad_px_base")

            if bad_pixels <= bad_pixels_baseline * 1.1:
                st.success("✅ Pixels defeituosos estável")
            else:
                st.warning("⚠️ Aumento de pixels defeituosos")

            st.markdown("**Posicionamento**")
            epid_sag = st.number_input("Sag do EPID (mm)", value=0.0, step=0.1, key="epid_sag")

            if abs(epid_sag) <= 2.0:
                st.success("✅ Sag dentro do limite")
            else:
                st.warning("⚠️ Verificar sag do detector")

# =============================================================================
# TAB 3: HISTÓRICO
# =============================================================================
with tab3:
    st.subheader("📊 Histórico de Imaging QA")

    if DB_AVAILABLE:
        col1, col2 = st.columns(2)

        with col1:
            img_type = st.selectbox(
                "Tipo de Teste",
                ["kv_imaging_qa", "epid_qa"],
                format_func=lambda x: "kV Imaging" if x == "kv_imaging_qa" else "EPID"
            )

        with col2:
            from datetime import timedelta
            period = st.selectbox(
                "Período",
                [30, 60, 90, 180, 365],
                format_func=lambda x: f"Últimos {x} dias"
            )

        start_date = datetime.now() - timedelta(days=period)
        results = db.get_results(test_type=img_type, start_date=start_date, limit=50)

        if results:
            table_data = []
            for r in results:
                table_data.append({
                    "Data": r['test_date'][:10] if r['test_date'] else "N/A",
                    "Máquina": r['machine_name'] or "N/A",
                    "Operador": r['performed_by'] or "N/A",
                    "Status": "✅ Aprovado" if r['passed'] else "❌ Reprovado"
                })

            st.dataframe(table_data, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum resultado encontrado.")
    else:
        st.warning("Banco de dados não disponível.")

# Botão de salvar geral
st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Salvar QA kV Imaging", type="primary", key="save_kv"):
        if DB_AVAILABLE and operator:
            results = {
                "kv_mv_coincidence": {
                    "offset_lat": kv_offset_lat if 'kv_offset_lat' in dir() else 0,
                    "offset_long": kv_offset_long if 'kv_offset_long' in dir() else 0,
                    "offset_vert": kv_offset_vert if 'kv_offset_vert' in dir() else 0,
                    "offset_3d": offset_3d if 'offset_3d' in dir() else 0,
                    "passed": kv_mv_passed if 'kv_mv_passed' in dir() else None
                },
                "scale": {
                    "error_h": scale_error_h if 'scale_error_h' in dir() else 0,
                    "error_v": scale_error_v if 'scale_error_v' in dir() else 0,
                    "passed": scale_passed if 'scale_passed' in dir() else None
                },
                "image_quality": {
                    "resolution": resolution_lp if 'resolution_lp' in dir() else 0,
                    "passed": image_quality_passed if 'image_quality_passed' in dir() else None
                }
            }

            overall = all([
                kv_mv_passed if 'kv_mv_passed' in dir() else True,
                scale_passed if 'scale_passed' in dir() else True,
                image_quality_passed if 'image_quality_passed' in dir() else True
            ])

            db.save_result(
                test_type="kv_imaging_qa",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=overall,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ QA kV Imaging salvo!")
        else:
            st.warning("Informe o operador ou banco não disponível.")

with col2:
    if st.button("💾 Salvar QA EPID", type="primary", key="save_epid"):
        if DB_AVAILABLE and operator:
            results = {
                "uniformity": {
                    "value": uniformity if 'uniformity' in dir() else 0,
                    "passed": epid_uniform_passed if 'epid_uniform_passed' in dir() else None
                },
                "resolution": {
                    "value": epid_resolution if 'epid_resolution' in dir() else 0,
                    "passed": epid_res_passed if 'epid_res_passed' in dir() else None
                },
                "linearity": {
                    "r_squared": r_squared if 'r_squared' in dir() else 0,
                    "passed": epid_linear_passed if 'epid_linear_passed' in dir() else None
                }
            }

            overall = all([
                epid_uniform_passed if 'epid_uniform_passed' in dir() else True,
                epid_res_passed if 'epid_res_passed' in dir() else True,
                epid_linear_passed if 'epid_linear_passed' in dir() else True
            ])

            db.save_result(
                test_type="epid_qa",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=overall,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ QA EPID salvo!")
        else:
            st.warning("Informe o operador ou banco não disponível.")
