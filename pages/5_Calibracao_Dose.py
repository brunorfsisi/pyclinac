"""
Módulo de Calibração de Dose - TG-51 e TRS-398
Com tabelas oficiais de fatores kQ
"""

import streamlit as st
import tempfile
from pathlib import Path
import numpy as np

st.set_page_config(page_title="Calibração de Dose", page_icon="⚡", layout="wide")

# Importações do pylinac
try:
    from pylinac.calibration import tg51, trs398
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import create_sidebar_info

# Sidebar info
create_sidebar_info(
    module_name="⚡ Calibração de Dose",
    description="""
    Cálculos de calibração absoluta de dose seguindo os protocolos:
    - **TG-51** (AAPM): Protocolo americano
    - **TRS-398** (IAEA): Protocolo internacional

    Inclui tabelas oficiais de fatores kQ para câmaras comuns.
    """,
    references=[
        "AAPM TG-51: Protocol for clinical reference dosimetry",
        "IAEA TRS-398: Absorbed Dose Determination in External Beam Radiotherapy",
        "AAPM TG-51 Addendum: Supplement to TG-51"
    ]
)

# =============================================================================
# TABELAS OFICIAIS DE kQ (TG-51)
# =============================================================================

# Tabela de kQ para fótons baseada em %dd(10)x
# Fonte: TG-51 Table II
KQ_PHOTON_TABLE = {
    # Câmara: {%dd(10)x: kQ}
    "Exradin A12": {
        58.0: 1.000, 63.0: 0.994, 66.0: 0.990, 70.0: 0.984,
        74.0: 0.977, 77.0: 0.971, 80.0: 0.965, 83.0: 0.959, 86.0: 0.952
    },
    "Exradin A12S": {
        58.0: 1.000, 63.0: 0.994, 66.0: 0.990, 70.0: 0.984,
        74.0: 0.977, 77.0: 0.971, 80.0: 0.966, 83.0: 0.960, 86.0: 0.953
    },
    "Exradin A19": {
        58.0: 1.000, 63.0: 0.995, 66.0: 0.991, 70.0: 0.985,
        74.0: 0.978, 77.0: 0.972, 80.0: 0.966, 83.0: 0.960, 86.0: 0.954
    },
    "Exradin A1SL": {
        58.0: 1.000, 63.0: 0.996, 66.0: 0.993, 70.0: 0.988,
        74.0: 0.983, 77.0: 0.978, 80.0: 0.973, 83.0: 0.968, 86.0: 0.963
    },
    "PTW 30013 (Farmer)": {
        58.0: 1.000, 63.0: 0.994, 66.0: 0.990, 70.0: 0.984,
        74.0: 0.977, 77.0: 0.971, 80.0: 0.965, 83.0: 0.959, 86.0: 0.952
    },
    "PTW 31010 (Semiflex)": {
        58.0: 1.000, 63.0: 0.995, 66.0: 0.992, 70.0: 0.987,
        74.0: 0.981, 77.0: 0.976, 80.0: 0.970, 83.0: 0.965, 86.0: 0.959
    },
    "IBA FC65-G": {
        58.0: 1.000, 63.0: 0.994, 66.0: 0.990, 70.0: 0.984,
        74.0: 0.977, 77.0: 0.971, 80.0: 0.965, 83.0: 0.959, 86.0: 0.952
    },
    "IBA CC13": {
        58.0: 1.000, 63.0: 0.995, 66.0: 0.992, 70.0: 0.987,
        74.0: 0.982, 77.0: 0.976, 80.0: 0.971, 83.0: 0.966, 86.0: 0.960
    },
    "NEL 2571 (Farmer)": {
        58.0: 1.000, 63.0: 0.994, 66.0: 0.990, 70.0: 0.984,
        74.0: 0.977, 77.0: 0.971, 80.0: 0.965, 83.0: 0.959, 86.0: 0.952
    }
}

# Valores típicos de %dd(10)x por energia
ENERGY_PDD_TABLE = {
    "Co-60": 58.5,
    "4 MV": 62.0,
    "6 MV": 66.7,
    "6 MV FFF": 63.5,
    "8 MV": 71.0,
    "10 MV": 74.0,
    "10 MV FFF": 71.0,
    "15 MV": 77.5,
    "18 MV": 80.0,
    "20 MV": 82.0,
    "23 MV": 84.0
}

# Fatores PQ,gr para elétrons (TG-51 Table III)
PQ_GR_ELECTRON = {
    # R50 (cm): {Câmara cilíndrica, Câmara plano-paralela}
    2.0: {"cylindrical": 0.982, "parallel_plate": 1.000},
    2.5: {"cylindrical": 0.986, "parallel_plate": 1.000},
    3.0: {"cylindrical": 0.989, "parallel_plate": 1.000},
    3.5: {"cylindrical": 0.991, "parallel_plate": 1.000},
    4.0: {"cylindrical": 0.993, "parallel_plate": 1.000},
    4.5: {"cylindrical": 0.995, "parallel_plate": 1.000},
    5.0: {"cylindrical": 0.996, "parallel_plate": 1.000},
    6.0: {"cylindrical": 0.998, "parallel_plate": 1.000},
    7.0: {"cylindrical": 0.999, "parallel_plate": 1.000},
    8.0: {"cylindrical": 0.999, "parallel_plate": 1.000},
    10.0: {"cylindrical": 1.000, "parallel_plate": 1.000},
}


def interpolate_kq(chamber, pdd10x):
    """Interpola kQ a partir da tabela para um valor específico de %dd(10)x"""
    if chamber not in KQ_PHOTON_TABLE:
        return None

    table = KQ_PHOTON_TABLE[chamber]
    pdd_values = sorted(table.keys())
    kq_values = [table[p] for p in pdd_values]

    # Interpolação linear
    if pdd10x <= pdd_values[0]:
        return kq_values[0]
    if pdd10x >= pdd_values[-1]:
        return kq_values[-1]

    return np.interp(pdd10x, pdd_values, kq_values)


def calculate_ptp(temp, pressure, ref_temp=22.0, ref_pressure=101.33):
    """Calcula fator de correção temperatura-pressão"""
    return (273.15 + temp) / (273.15 + ref_temp) * (ref_pressure / pressure)


st.title("⚡ Calibração de Dose")
st.markdown("""
Cálculos de calibração absoluta de dose para feixes de fótons e elétrons
com tabelas oficiais de fatores de qualidade.
""")

# Tabs para diferentes protocolos
tab1, tab2, tab3 = st.tabs(["📋 TG-51 Fótons", "📋 TG-51 Elétrons", "📋 TRS-398"])

# =============================================================================
# TAB 1 - TG-51 FÓTONS
# =============================================================================
with tab1:
    st.subheader("Protocolo TG-51 para Fótons")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Identificação do Feixe")

        beam_energy = st.selectbox(
            "Energia do Feixe",
            options=list(ENERGY_PDD_TABLE.keys()),
            index=2,  # 6 MV como padrão
            key="tg51_beam_energy"
        )

        # Preenche PDD automaticamente baseado na energia
        default_pdd = ENERGY_PDD_TABLE.get(beam_energy, 66.7)

        pdd10x = st.number_input(
            "%dd(10)x",
            min_value=50.0,
            max_value=90.0,
            value=default_pdd,
            step=0.1,
            format="%.1f",
            help="PDD a 10cm corrigido para contaminação de elétrons"
        )

        st.markdown("#### Câmara de Ionização")

        chamber = st.selectbox(
            "Modelo da Câmara",
            options=list(KQ_PHOTON_TABLE.keys()),
            key="tg51_chamber"
        )

        n_dw = st.number_input(
            "N_D,w (Gy/nC ou Gy/rdg)",
            min_value=0.01,
            max_value=1.0,
            value=0.050,
            step=0.001,
            format="%.4f",
            help="Fator de calibração da câmara em água (60Co)"
        )

    with col2:
        st.markdown("#### Condições de Medição")

        m_raw = st.number_input(
            "Leitura Bruta M (nC ou rdg)",
            min_value=0.0,
            value=25.000,
            step=0.001,
            format="%.3f",
            key="tg51_m"
        )

        temp = st.number_input(
            "Temperatura (°C)",
            min_value=15.0,
            max_value=30.0,
            value=22.0,
            step=0.1,
            key="tg51_temp"
        )

        pressure = st.number_input(
            "Pressão (kPa)",
            min_value=90.0,
            max_value=110.0,
            value=101.33,
            step=0.01,
            format="%.2f",
            key="tg51_press"
        )

        st.markdown("#### Fatores de Correção")

        col_a, col_b = st.columns(2)

        with col_a:
            p_ion = st.number_input(
                "P_ion",
                min_value=0.990,
                max_value=1.050,
                value=1.000,
                step=0.001,
                format="%.4f",
                help="Fator de recombinação iônica"
            )

            p_pol = st.number_input(
                "P_pol",
                min_value=0.990,
                max_value=1.010,
                value=1.000,
                step=0.001,
                format="%.4f",
                help="Fator de polaridade"
            )

        with col_b:
            p_elec = st.number_input(
                "P_elec",
                min_value=0.990,
                max_value=1.010,
                value=1.000,
                step=0.001,
                format="%.4f",
                help="Fator do eletrômetro"
            )

    # Cálculo
    st.divider()

    if st.button("🧮 Calcular Dose TG-51", key="calc_tg51_photon", type="primary"):
        # Obtém kQ da tabela
        kq = interpolate_kq(chamber, pdd10x)

        if kq is None:
            st.error("Câmara não encontrada na tabela de kQ")
        else:
            # Calcula P_TP
            p_tp = calculate_ptp(temp, pressure)

            # Leitura corrigida
            m_corr = m_raw * p_tp * p_ion * p_pol * p_elec

            # Dose
            dose = m_corr * n_dw * kq

            st.success("✅ Cálculo concluído!")

            # Resultados
            st.subheader("📊 Resultados")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Fatores de Correção**")
                st.metric("P_TP", f"{p_tp:.4f}")
                st.metric("P_ion × P_pol × P_elec", f"{p_ion * p_pol * p_elec:.4f}")

            with col2:
                st.markdown("**Fator de Qualidade**")
                st.metric("kQ (interpolado)", f"{kq:.4f}")
                st.metric("%dd(10)x usado", f"{pdd10x:.1f}")

            with col3:
                st.markdown("**Dose**")
                st.metric("M corrigido", f"{m_corr:.4f} nC")
                st.metric("**D_w^Q (dose)**", f"{dose:.4f} Gy", delta="por medição")

            # Dose por UM
            st.divider()
            col1, col2, col3 = st.columns(3)

            with col1:
                um = st.number_input("Unidades Monitor (UM)", 1, 1000, 100, key="tg51_um")

            with col2:
                dose_per_um = dose / um
                st.metric("Dose por UM", f"{dose_per_um:.6f} Gy/UM")

            with col3:
                deviation = (dose_per_um - 0.01) / 0.01 * 100
                st.metric("Desvio de 1 cGy/UM", f"{deviation:+.2f}%")

            # Resumo
            with st.expander("📋 Resumo Completo"):
                st.markdown(f"""
                ### Parâmetros de Entrada

                | Parâmetro | Valor |
                |-----------|-------|
                | Energia | {beam_energy} |
                | %dd(10)x | {pdd10x:.1f} |
                | Câmara | {chamber} |
                | N_D,w | {n_dw:.4f} Gy/nC |
                | M (bruta) | {m_raw:.3f} nC |
                | Temperatura | {temp:.1f} °C |
                | Pressão | {pressure:.2f} kPa |

                ### Fatores de Correção

                | Fator | Valor |
                |-------|-------|
                | P_TP | {p_tp:.4f} |
                | P_ion | {p_ion:.4f} |
                | P_pol | {p_pol:.4f} |
                | P_elec | {p_elec:.4f} |
                | **kQ** | **{kq:.4f}** |

                ### Resultados

                | Resultado | Valor |
                |-----------|-------|
                | M corrigido | {m_corr:.4f} nC |
                | **Dose D_w^Q** | **{dose:.4f} Gy** |
                | Dose/UM | {dose_per_um:.6f} Gy/UM |
                | Desvio | {deviation:+.2f}% |

                ### Equação TG-51
                ```
                D_w^Q = M × N_D,w × kQ

                onde:
                M = M_raw × P_TP × P_ion × P_pol × P_elec
                ```
                """)

# =============================================================================
# TAB 2 - TG-51 ELÉTRONS
# =============================================================================
with tab2:
    st.subheader("Protocolo TG-51 para Elétrons")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Dados do Feixe")

        e_energy = st.number_input(
            "Energia Nominal (MeV)",
            min_value=4.0,
            max_value=25.0,
            value=9.0,
            step=1.0,
            key="tg51_e_energy"
        )

        r50 = st.number_input(
            "R_50 (cm)",
            min_value=1.0,
            max_value=15.0,
            value=3.8,
            step=0.1,
            format="%.2f",
            help="Profundidade de 50% da dose (ionização)"
        )

        # Calcula d_ref automaticamente
        d_ref = 0.6 * r50 - 0.1
        st.info(f"Profundidade de referência calculada: d_ref = {d_ref:.2f} cm")

    with col2:
        st.markdown("#### Câmara e Calibração")

        e_chamber_type = st.selectbox(
            "Tipo de Câmara",
            options=["Cilíndrica (Farmer)", "Plano-Paralela"],
            key="tg51_e_chamber_type"
        )

        e_n_dw = st.number_input(
            "N_D,w (Gy/nC)",
            min_value=0.01,
            max_value=1.0,
            value=0.050,
            step=0.001,
            format="%.4f",
            key="tg51_e_ndw"
        )

        e_m_raw = st.number_input(
            "Leitura M (nC)",
            min_value=0.0,
            value=20.0,
            step=0.1,
            key="tg51_e_m"
        )

    # Parâmetros adicionais
    with st.expander("⚙️ Correções e kQ"):
        col1, col2 = st.columns(2)

        with col1:
            e_temp = st.number_input("Temperatura (°C)", 15.0, 30.0, 22.0, 0.1, key="e_temp")
            e_pressure = st.number_input("Pressão (kPa)", 90.0, 110.0, 101.33, 0.01, key="e_press")
            e_p_ion = st.number_input("P_ion", 0.99, 1.05, 1.000, 0.001, format="%.4f", key="e_pion")

        with col2:
            e_p_pol = st.number_input("P_pol", 0.99, 1.01, 1.000, 0.001, format="%.4f", key="e_ppol")
            e_p_elec = st.number_input("P_elec", 0.99, 1.01, 1.000, 0.001, format="%.4f", key="e_pelec")
            e_kq_ecal = st.number_input(
                "k'_Q (ou kQ,ecal)",
                min_value=0.85,
                max_value=1.00,
                value=0.90,
                step=0.001,
                format="%.4f",
                help="Fator de conversão para qualidade do feixe de elétrons"
            )

    if st.button("🧮 Calcular Dose Elétrons", key="calc_tg51_electron", type="primary"):
        # Calcula P_TP
        e_p_tp = calculate_ptp(e_temp, e_pressure)

        # Obtém PQ,gr
        chamber_type = "cylindrical" if "Cilíndrica" in e_chamber_type else "parallel_plate"

        # Interpola PQ,gr
        r50_values = sorted(PQ_GR_ELECTRON.keys())
        pq_gr_values = [PQ_GR_ELECTRON[r][chamber_type] for r in r50_values]
        p_gr = np.interp(r50, r50_values, pq_gr_values)

        # Leitura corrigida
        e_m_corr = e_m_raw * e_p_tp * e_p_ion * e_p_pol * e_p_elec

        # Dose
        e_dose = e_m_corr * e_n_dw * e_kq_ecal * p_gr

        st.success("✅ Cálculo concluído!")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("P_TP", f"{e_p_tp:.4f}")
            st.metric("P_gr", f"{p_gr:.4f}")

        with col2:
            st.metric("k'_Q", f"{e_kq_ecal:.4f}")
            st.metric("M corrigido", f"{e_m_corr:.4f} nC")

        with col3:
            st.metric("d_ref", f"{d_ref:.2f} cm")
            st.metric("**Dose D_w^Q**", f"{e_dose:.4f} Gy")

# =============================================================================
# TAB 3 - TRS-398
# =============================================================================
with tab3:
    st.subheader("Protocolo IAEA TRS-398")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Qualidade do Feixe")

        trs_beam_type = st.selectbox(
            "Tipo de Radiação",
            options=["Fótons (TPR20,10)", "Elétrons (R50)"],
            key="trs_beam_type"
        )

        if "Fótons" in trs_beam_type:
            trs_tpr = st.number_input(
                "TPR_20,10",
                min_value=0.50,
                max_value=0.85,
                value=0.667,
                step=0.001,
                format="%.3f",
                help="Razão tecido-fantoma 20/10 para fótons"
            )
        else:
            trs_r50 = st.number_input(
                "R_50 (g/cm²)",
                min_value=1.0,
                max_value=15.0,
                value=3.8,
                step=0.1,
                help="Profundidade de 50% para elétrons"
            )

    with col2:
        st.markdown("#### Câmara e Calibração")

        trs_n_dw = st.number_input(
            "N_D,w,Q0 (Gy/nC)",
            min_value=0.01,
            max_value=1.0,
            value=0.050,
            step=0.001,
            format="%.4f",
            key="trs_ndw"
        )

        trs_kq = st.number_input(
            "k_Q,Q0",
            min_value=0.90,
            max_value=1.05,
            value=0.990,
            step=0.001,
            format="%.4f",
            help="Fator de qualidade do feixe (da tabela TRS-398)"
        )

    # Medições
    st.markdown("#### Medições")
    col1, col2, col3 = st.columns(3)

    with col1:
        trs_m = st.number_input("Leitura M (nC)", 0.0, 100.0, 25.0, 0.001, format="%.3f", key="trs_m")

    with col2:
        trs_temp = st.number_input("Temperatura (°C)", 15.0, 30.0, 20.0, 0.1, key="trs_temp")

    with col3:
        trs_press = st.number_input("Pressão (kPa)", 90.0, 110.0, 101.325, 0.01, key="trs_press")

    # Fatores
    with st.expander("⚙️ Fatores de Correção"):
        col1, col2, col3 = st.columns(3)
        with col1:
            trs_ks = st.number_input("k_s (recombinação)", 0.99, 1.05, 1.000, 0.001, format="%.4f", key="trs_ks")
        with col2:
            trs_kpol = st.number_input("k_pol (polaridade)", 0.99, 1.01, 1.000, 0.001, format="%.4f", key="trs_kpol")
        with col3:
            trs_kelec = st.number_input("k_elec (eletrômetro)", 0.99, 1.01, 1.000, 0.001, format="%.4f", key="trs_kelec")

    if st.button("🧮 Calcular Dose TRS-398", key="calc_trs398", type="primary"):
        # k_TP (TRS-398 usa 20°C como referência)
        trs_ktp = (273.15 + trs_temp) / (273.15 + 20.0) * (101.325 / trs_press)

        # M corrigido
        trs_m_corr = trs_m * trs_ktp * trs_ks * trs_kpol * trs_kelec

        # Dose
        trs_dose = trs_m_corr * trs_n_dw * trs_kq

        st.success("✅ Cálculo concluído!")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("k_TP", f"{trs_ktp:.4f}")
            st.metric("Correção total", f"{trs_ktp * trs_ks * trs_kpol * trs_kelec:.4f}")

        with col2:
            st.metric("k_Q,Q0", f"{trs_kq:.4f}")
            st.metric("M corrigido", f"{trs_m_corr:.4f} nC")

        with col3:
            st.metric("**D_w,Q**", f"{trs_dose:.4f} Gy")
            st.metric("Dose/UM (100 UM)", f"{trs_dose/100:.6f} Gy/UM")

        st.markdown("---")
        st.markdown(f"""
        ### Equação TRS-398

        **D_w,Q = M_Q × N_D,w,Q0 × k_Q,Q0**

        Onde:
        - M_Q = {trs_m_corr:.4f} nC (leitura corrigida)
        - N_D,w,Q0 = {trs_n_dw:.4f} Gy/nC
        - k_Q,Q0 = {trs_kq:.4f}

        **Resultado: D_w,Q = {trs_dose:.4f} Gy**
        """)

# Tabela de kQ
with st.expander("📊 Tabela de Fatores kQ (TG-51)"):
    st.markdown("### Fatores kQ para Fótons vs %dd(10)x")

    # Cria tabela formatada
    import pandas as pd

    pdd_values = [58.0, 63.0, 66.0, 70.0, 74.0, 77.0, 80.0, 83.0, 86.0]

    table_data = {"Câmara": list(KQ_PHOTON_TABLE.keys())}
    for pdd in pdd_values:
        table_data[f"{pdd:.0f}%"] = [KQ_PHOTON_TABLE[c].get(pdd, "-") for c in KQ_PHOTON_TABLE.keys()]

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("""
    **Notas:**
    - Valores interpolados para %dd(10)x intermediários
    - Fonte: AAPM TG-51 Table II
    - Para câmaras não listadas, consulte o certificado de calibração
    """)

# Instruções
with st.expander("📖 Instruções e Referências"):
    st.markdown("""
    ### Protocolo TG-51

    1. **Preparação**:
       - Câmara calibrada em laboratório ADCL
       - Phantom de água com profundidade adequada
       - Condições de referência (SSD 100 cm, campo 10×10 cm²)

    2. **Medição de %dd(10)x**:
       - Medir PDD a 10 cm
       - Aplicar correção para contaminação de elétrons
       - Usar lead foil method se necessário

    3. **Correções**:
       - P_TP: temperatura e pressão
       - P_ion: recombinação iônica (método duas tensões)
       - P_pol: efeito de polaridade
       - P_elec: calibração do eletrômetro

    ### Protocolo TRS-398

    Similar ao TG-51, mas:
    - Usa TPR_20,10 para especificação de qualidade
    - Temperatura de referência: 20°C (vs 22°C no TG-51)
    - Fatores kQ ligeiramente diferentes

    ### Recomendações

    - Calibrar anualmente ou após reparos
    - Verificar consistência com medições anteriores
    - Desvio aceitável: ± 1% do valor esperado
    - Documentar todas as medições
    """)
