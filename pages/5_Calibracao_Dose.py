"""
Módulo de Calibração de Dose - TG-51 e TRS-398
"""

import streamlit as st
import tempfile
from pathlib import Path

st.set_page_config(page_title="Calibração de Dose", page_icon="⚡", layout="wide")

# Importações do pylinac
try:
    from pylinac.calibration import tg51, trs398
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

# Adiciona path do utils
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import create_sidebar_info, get_pdf_download_button

# Sidebar info
create_sidebar_info(
    module_name="⚡ Calibração de Dose",
    description="""
    Cálculos de calibração absoluta de dose seguindo os protocolos
    AAPM TG-51 e IAEA TRS-398 para feixes de fótons e elétrons.
    """,
    references=[
        "AAPM TG-51: Protocol for clinical reference dosimetry of high-energy photon and electron beams",
        "IAEA TRS-398: Absorbed Dose Determination in External Beam Radiotherapy"
    ]
)

st.title("⚡ Calibração de Dose")
st.markdown("""
Cálculos de calibração absoluta de dose para feixes de fótons e elétrons.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Tabs para diferentes protocolos
tab1, tab2 = st.tabs(["📋 TG-51 (AAPM)", "📋 TRS-398 (IAEA)"])

# =============================================================================
# TAB TG-51
# =============================================================================
with tab1:
    st.subheader("Protocolo AAPM TG-51")

    # Sub-tabs para fótons e elétrons
    tg51_tab1, tg51_tab2 = st.tabs(["☀️ Fótons", "⚡ Elétrons"])

    with tg51_tab1:
        st.markdown("### Calibração TG-51 para Fótons")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Dados do Feixe")
            energy = st.number_input(
                "Energia nominal (MV)",
                min_value=4.0,
                max_value=25.0,
                value=6.0,
                step=1.0,
                key="tg51_energy"
            )

            tpr2010 = st.number_input(
                "TPR20,10",
                min_value=0.5,
                max_value=1.0,
                value=0.667,
                step=0.001,
                format="%.3f",
                help="Razão tecido-fantoma 20/10"
            )

            pdd2010 = st.number_input(
                "PDD(10)x",
                min_value=50.0,
                max_value=100.0,
                value=66.7,
                step=0.1,
                help="PDD a 10cm (%) para qualificação do feixe"
            )

        with col2:
            st.markdown("#### Dados da Câmara")

            chamber_model = st.selectbox(
                "Modelo da câmara",
                options=[
                    "Exradin A12",
                    "Exradin A19",
                    "Exradin A1SL",
                    "PTW 30013",
                    "PTW 31010",
                    "IBA FC65-G",
                    "Outro"
                ],
                key="tg51_chamber"
            )

            n_dw = st.number_input(
                "N_D,w (Gy/nC)",
                min_value=0.01,
                max_value=0.2,
                value=0.05,
                step=0.001,
                format="%.4f",
                help="Fator de calibração da câmara em água"
            )

            p_elec = st.number_input(
                "P_elec",
                min_value=0.99,
                max_value=1.01,
                value=1.000,
                step=0.001,
                format="%.3f",
                help="Fator de correção do eletrômetro"
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Condições de Medição")

            m_raw = st.number_input(
                "Leitura bruta M (nC)",
                min_value=0.0,
                value=25.0,
                step=0.1,
                format="%.2f",
                key="tg51_m_raw"
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
                step=0.1,
                key="tg51_pressure"
            )

        with col2:
            st.markdown("#### Fatores de Correção")

            p_ion = st.number_input(
                "P_ion",
                min_value=0.99,
                max_value=1.05,
                value=1.000,
                step=0.001,
                format="%.3f",
                help="Fator de recombinação iônica"
            )

            p_pol = st.number_input(
                "P_pol",
                min_value=0.99,
                max_value=1.01,
                value=1.000,
                step=0.001,
                format="%.3f",
                help="Fator de polaridade"
            )

            p_tp = st.number_input(
                "P_TP (calculado)",
                min_value=0.9,
                max_value=1.1,
                value=(273.15 + temp) / (273.15 + 22) * (101.33 / pressure),
                step=0.001,
                format="%.4f",
                help="Fator de correção temperatura-pressão",
                disabled=True
            )

        if st.button("🧮 Calcular Dose TG-51", key="calc_tg51_photon", type="primary"):
            try:
                # Cálculo simplificado TG-51 para fótons
                p_tp_calc = (273.15 + temp) / (273.15 + 22) * (101.33 / pressure)

                # Fator kQ aproximado baseado em TPR20,10
                # Esta é uma aproximação - em produção usaria tabelas completas
                kq = 1.0 - 0.0385 * (tpr2010 - 0.667)

                # Leitura corrigida
                m_corr = m_raw * p_tp_calc * p_elec * p_pol * p_ion

                # Dose na profundidade de referência
                dose = m_corr * n_dw * kq

                st.success("✅ Cálculo concluído!")

                st.subheader("📊 Resultados")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Leitura Corrigida", f"{m_corr:.3f} nC")
                    st.metric("P_TP", f"{p_tp_calc:.4f}")

                with col2:
                    st.metric("kQ (estimado)", f"{kq:.4f}")
                    st.metric("N_D,w", f"{n_dw:.4f} Gy/nC")

                with col3:
                    st.metric("**Dose na Referência**", f"{dose:.4f} Gy")
                    st.metric("Dose por UM", f"{dose/100:.6f} Gy/UM")

                # Resumo
                st.markdown("---")
                st.markdown(f"""
                ### Resumo da Calibração

                | Parâmetro | Valor |
                |-----------|-------|
                | Energia | {energy} MV |
                | TPR20,10 | {tpr2010:.3f} |
                | Câmara | {chamber_model} |
                | Leitura bruta | {m_raw:.2f} nC |
                | Leitura corrigida | {m_corr:.3f} nC |
                | kQ | {kq:.4f} |
                | **Dose** | **{dose:.4f} Gy** |
                """)

            except Exception as e:
                st.error(f"❌ Erro no cálculo: {str(e)}")

    with tg51_tab2:
        st.markdown("### Calibração TG-51 para Elétrons")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Dados do Feixe")

            e_energy = st.number_input(
                "Energia nominal (MeV)",
                min_value=4.0,
                max_value=25.0,
                value=9.0,
                step=1.0,
                key="tg51_e_energy"
            )

            r50 = st.number_input(
                "R50 (cm)",
                min_value=1.0,
                max_value=12.0,
                value=3.8,
                step=0.1,
                help="Profundidade de 50% da dose"
            )

            i50 = st.number_input(
                "I50 (cm)",
                min_value=1.0,
                max_value=12.0,
                value=3.9,
                step=0.1,
                help="Profundidade de 50% da ionização"
            )

        with col2:
            st.markdown("#### Parâmetros de Medição")

            e_m_raw = st.number_input(
                "Leitura bruta M (nC)",
                min_value=0.0,
                value=20.0,
                step=0.1,
                key="e_m_raw"
            )

            e_n_dw = st.number_input(
                "N_D,w (Gy/nC)",
                min_value=0.01,
                max_value=0.2,
                value=0.05,
                step=0.001,
                format="%.4f",
                key="e_n_dw"
            )

            d_ref = st.number_input(
                "Profundidade de referência (cm)",
                min_value=0.5,
                max_value=10.0,
                value=0.6 * r50 - 0.1,
                step=0.1,
                help="dref = 0.6*R50 - 0.1 cm"
            )

        if st.button("🧮 Calcular Dose Elétrons", key="calc_tg51_electron", type="primary"):
            try:
                # Cálculo simplificado para elétrons
                # Em produção usaria as tabelas e cálculos completos

                # kQ para elétrons (aproximação)
                k_ecal = 0.90 + 0.006 * e_energy

                dose_e = e_m_raw * e_n_dw * k_ecal

                st.success("✅ Cálculo concluído!")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("kQ,ecal (estimado)", f"{k_ecal:.4f}")
                    st.metric("R50", f"{r50:.2f} cm")

                with col2:
                    st.metric("**Dose na Referência**", f"{dose_e:.4f} Gy")
                    st.metric("Profundidade de ref.", f"{d_ref:.2f} cm")

            except Exception as e:
                st.error(f"❌ Erro no cálculo: {str(e)}")

# =============================================================================
# TAB TRS-398
# =============================================================================
with tab2:
    st.subheader("Protocolo IAEA TRS-398")

    trs_tab1, trs_tab2 = st.tabs(["☀️ Fótons", "⚡ Elétrons"])

    with trs_tab1:
        st.markdown("### Calibração TRS-398 para Fótons")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Qualidade do Feixe")

            trs_energy = st.number_input(
                "Energia nominal (MV)",
                min_value=4.0,
                max_value=25.0,
                value=6.0,
                step=1.0,
                key="trs_energy"
            )

            trs_tpr = st.number_input(
                "TPR20,10",
                min_value=0.5,
                max_value=0.85,
                value=0.667,
                step=0.001,
                format="%.3f",
                key="trs_tpr"
            )

        with col2:
            st.markdown("#### Câmara de Ionização")

            trs_n_dw = st.number_input(
                "N_D,w,Q0 (Gy/nC)",
                min_value=0.01,
                max_value=0.2,
                value=0.050,
                step=0.001,
                format="%.4f",
                key="trs_n_dw"
            )

            trs_kq = st.number_input(
                "kQ,Q0",
                min_value=0.9,
                max_value=1.05,
                value=0.99,
                step=0.001,
                format="%.3f",
                help="Fator de qualidade do feixe"
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Leituras")

            trs_m_raw = st.number_input(
                "Leitura bruta M (nC)",
                min_value=0.0,
                value=25.0,
                step=0.1,
                key="trs_m_raw"
            )

            trs_temp = st.number_input(
                "Temperatura (°C)",
                min_value=15.0,
                max_value=30.0,
                value=22.0,
                step=0.1,
                key="trs_temp"
            )

            trs_pressure = st.number_input(
                "Pressão (kPa)",
                min_value=90.0,
                max_value=110.0,
                value=101.33,
                step=0.1,
                key="trs_pressure"
            )

        with col2:
            st.markdown("#### Fatores de Correção")

            trs_k_s = st.number_input(
                "k_s (recombinação)",
                min_value=0.99,
                max_value=1.05,
                value=1.000,
                step=0.001,
                format="%.3f"
            )

            trs_k_pol = st.number_input(
                "k_pol (polaridade)",
                min_value=0.99,
                max_value=1.01,
                value=1.000,
                step=0.001,
                format="%.3f"
            )

            trs_k_elec = st.number_input(
                "k_elec (eletrômetro)",
                min_value=0.99,
                max_value=1.01,
                value=1.000,
                step=0.001,
                format="%.3f"
            )

        if st.button("🧮 Calcular Dose TRS-398", key="calc_trs", type="primary"):
            try:
                # Fator T/P
                k_tp = (273.15 + trs_temp) / (273.15 + 20) * (101.325 / trs_pressure)

                # Leitura corrigida
                m_corr = trs_m_raw * k_tp * trs_k_s * trs_k_pol * trs_k_elec

                # Dose
                dose_trs = m_corr * trs_n_dw * trs_kq

                st.success("✅ Cálculo concluído!")

                st.subheader("📊 Resultados")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("k_TP", f"{k_tp:.4f}")
                    st.metric("M corrigido", f"{m_corr:.3f} nC")

                with col2:
                    st.metric("kQ,Q0", f"{trs_kq:.4f}")
                    st.metric("N_D,w,Q0", f"{trs_n_dw:.4f} Gy/nC")

                with col3:
                    st.metric("**Dose em água (Dw,Q)**", f"{dose_trs:.4f} Gy")
                    st.metric("Dose por UM", f"{dose_trs/100:.6f} Gy/UM")

                st.markdown("---")
                st.markdown(f"""
                ### Equação TRS-398
                ```
                Dw,Q = MQ · ND,w,Q0 · kQ,Q0
                ```

                Onde:
                - MQ = {m_corr:.3f} nC (leitura corrigida)
                - ND,w,Q0 = {trs_n_dw:.4f} Gy/nC
                - kQ,Q0 = {trs_kq:.4f}
                - **Dw,Q = {dose_trs:.4f} Gy**
                """)

            except Exception as e:
                st.error(f"❌ Erro no cálculo: {str(e)}")

    with trs_tab2:
        st.markdown("### Calibração TRS-398 para Elétrons")
        st.info("Interface similar ao TG-51 para elétrons. Implemente conforme necessário.")

# Instruções e referências
with st.expander("📖 Instruções e Referências"):
    st.markdown("""
    ### Protocolo TG-51

    O TG-51 é o protocolo da AAPM para dosimetria de referência clínica de feixes
    de fótons e elétrons de alta energia. Principais características:

    - Usa fator de calibração ND,w (câmara calibrada em água)
    - Fatores kQ tabelados para diferentes qualidades de feixe
    - Referência em água a 10 cm de profundidade para fótons

    ### Protocolo TRS-398

    O TRS-398 é o código de prática da IAEA baseado em padrões de dose absorvida
    em água. Principais características:

    - Similar ao TG-51, mas com pequenas diferenças nos fatores
    - Amplamente utilizado internacionalmente
    - Inclui protocolos para Co-60, fótons, elétrons e prótons

    ### Fatores de Correção

    | Fator | Descrição |
    |-------|-----------|
    | P_TP / k_TP | Correção temperatura-pressão |
    | P_ion / k_s | Recombinação iônica |
    | P_pol / k_pol | Efeito de polaridade |
    | P_elec / k_elec | Correção do eletrômetro |
    | kQ | Fator de qualidade do feixe |

    ### Notas Importantes

    ⚠️ Esta ferramenta fornece cálculos aproximados para fins educacionais.
    Para calibração clínica real, utilize os valores tabelados oficiais
    dos protocolos e siga todos os procedimentos de QA.
    """)
