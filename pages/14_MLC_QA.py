"""
MLC QA Avançado - Controle de Qualidade do Colimador Multi-Lâminas
"""

import streamlit as st
from datetime import datetime, date
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="MLC QA", page_icon="🔧", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info, save_uploaded_file

create_sidebar_info(
    module_name="🔧 MLC QA Avançado",
    description="""
    Controle de qualidade completo para MLC.

    **Testes disponíveis:**
    - Posição das lâminas (Leaf Position)
    - Velocidade das lâminas
    - Transmissão inter/intra-leaf
    - Garden Fence
    - Gap Test
    - Leaf Travel Speed

    **Complementa:**
    - Picket Fence (módulo separado)

    **Referências:**
    - AAPM TG-142
    - TG-50
    """,
    references=[
        ("AAPM TG-50 (MLC)", "https://www.aapm.org/pubs/reports/detail.asp?docid=47"),
        ("AAPM TG-142", "https://www.aapm.org/pubs/reports/detail.asp?docid=104")
    ]
)

st.title("🔧 MLC QA Avançado")
st.markdown("### Controle de Qualidade do Colimador Multi-Lâminas")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📏 Posição",
    "⚡ Velocidade",
    "🔍 Transmissão",
    "🌿 Garden Fence",
    "📊 Resumo"
])

# Configurações comuns
with st.sidebar:
    st.subheader("Configuração do MLC")

    mlc_type = st.selectbox(
        "Tipo de MLC",
        ["Varian Millennium 120", "Varian HD120", "Elekta Agility",
         "Elekta MLCi2", "Siemens 160 MLC", "Outro"]
    )

    if mlc_type == "Varian Millennium 120":
        n_leaves = 120
        leaf_width_inner = 5.0  # mm
        leaf_width_outer = 10.0  # mm
    elif mlc_type == "Varian HD120":
        n_leaves = 120
        leaf_width_inner = 2.5  # mm
        leaf_width_outer = 5.0  # mm
    elif mlc_type == "Elekta Agility":
        n_leaves = 160
        leaf_width_inner = 5.0  # mm
        leaf_width_outer = 5.0  # mm
    else:
        n_leaves = st.number_input("Número de lâminas", value=120, step=2)
        leaf_width_inner = st.number_input("Largura lâminas internas (mm)", value=5.0, step=0.5)
        leaf_width_outer = st.number_input("Largura lâminas externas (mm)", value=10.0, step=0.5)

    st.divider()

    if DB_AVAILABLE:
        db = get_database()
        machines = db.get_machines()
        machine_names = [m['name'] for m in machines] if machines else ["Não cadastrada"]
        machine = st.selectbox("Máquina", options=machine_names, key="mlc_machine")
    else:
        machine = st.text_input("Máquina", value="Clinac iX", key="mlc_machine")

    operator = st.text_input("Operador", key="mlc_operator")
    test_date = st.date_input("Data", value=date.today(), key="mlc_date")

# =============================================================================
# TAB 1: POSIÇÃO DAS LÂMINAS
# =============================================================================
with tab1:
    st.subheader("📏 Precisão de Posição das Lâminas")

    st.markdown("""
    Teste de precisão posicional das lâminas do MLC.

    **Tolerâncias TG-142:**
    - Posição: ±1 mm
    - Ação: ±0.5 mm
    """)

    test_method = st.radio(
        "Método de teste",
        ["Entrada manual", "Análise de imagem EPID"],
        horizontal=True,
        key="pos_method"
    )

    if test_method == "Entrada manual":
        st.markdown("#### Teste de Posição Individual")

        n_leaves_test = st.number_input(
            "Número de lâminas a testar",
            min_value=1,
            max_value=n_leaves // 2,
            value=10,
            key="n_leaves_pos"
        )

        # Posições de teste
        test_positions = st.multiselect(
            "Posições de teste (cm do isocentro)",
            [-10, -5, 0, 5, 10],
            default=[0, 5, 10],
            key="pos_test_positions"
        )

        st.markdown("#### Resultados por Posição")

        position_results = {}

        for pos in test_positions:
            with st.expander(f"Posição programada: {pos} cm"):
                col1, col2, col3 = st.columns(3)

                leaf_errors = []

                for i in range(n_leaves_test):
                    col_idx = i % 3
                    with [col1, col2, col3][col_idx]:
                        measured = st.number_input(
                            f"Lâmina {i+1}",
                            value=float(pos),
                            step=0.01,
                            format="%.2f",
                            key=f"leaf_{pos}_{i}"
                        )
                        error = measured - pos
                        leaf_errors.append(error)

                position_results[pos] = leaf_errors

        # Análise
        if position_results:
            st.markdown("#### Análise de Erros")

            all_errors = []
            analysis_data = []

            for pos, errors in position_results.items():
                all_errors.extend(errors)
                analysis_data.append({
                    "Posição (cm)": pos,
                    "Erro Médio (mm)": f"{np.mean(errors)*10:.2f}",
                    "Erro Máx (mm)": f"{np.max(np.abs(errors))*10:.2f}",
                    "Desvio Padrão (mm)": f"{np.std(errors)*10:.2f}"
                })

            st.dataframe(analysis_data, use_container_width=True, hide_index=True)

            # Gráfico de erros
            fig, ax = plt.subplots(figsize=(10, 5))

            for pos, errors in position_results.items():
                errors_mm = [e * 10 for e in errors]  # Converter para mm
                ax.scatter([pos] * len(errors_mm), errors_mm, label=f'{pos} cm', alpha=0.7)

            ax.axhline(y=1.0, color='r', linestyle='--', label='Tolerância (+1mm)')
            ax.axhline(y=-1.0, color='r', linestyle='--')
            ax.axhline(y=0.5, color='orange', linestyle=':', label='Ação (+0.5mm)')
            ax.axhline(y=-0.5, color='orange', linestyle=':')
            ax.axhline(y=0, color='g', linestyle='-', alpha=0.3)

            ax.set_xlabel('Posição Programada (cm)')
            ax.set_ylabel('Erro (mm)')
            ax.set_title('Erros de Posição das Lâminas')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # Resultado final
            max_error_mm = np.max(np.abs(all_errors)) * 10
            tolerance = 1.0  # mm

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Erro Máximo", f"{max_error_mm:.2f} mm")
            with col2:
                if max_error_mm <= tolerance:
                    st.success(f"✅ APROVADO (Tolerância: ±{tolerance} mm)")
                    pos_passed = True
                else:
                    st.error(f"❌ REPROVADO (Tolerância: ±{tolerance} mm)")
                    pos_passed = False

    else:  # Análise de imagem EPID
        st.markdown("#### Upload de Imagem EPID")

        uploaded_img = st.file_uploader(
            "Carregar imagem EPID do teste de posição",
            type=['dcm', 'tif', 'tiff', 'png'],
            key="epid_pos_img"
        )

        if uploaded_img:
            st.info("Para análise automática de posição de lâminas, use o módulo Picket Fence.")
            st.markdown("[Ir para Picket Fence →](/Picket_Fence)")

# =============================================================================
# TAB 2: VELOCIDADE DAS LÂMINAS
# =============================================================================
with tab2:
    st.subheader("⚡ Teste de Velocidade das Lâminas")

    st.markdown("""
    Verificação da velocidade e tempo de resposta do MLC.

    **Especificações típicas:**
    - Velocidade máxima: 2-3 cm/s
    - Aceleração adequada para IMRT/VMAT

    **Tolerâncias TG-142:**
    - Velocidade: Especificação do fabricante ±10%
    """)

    st.markdown("#### Parâmetros do Teste")

    col1, col2 = st.columns(2)

    with col1:
        travel_distance = st.number_input(
            "Distância de viagem (cm)",
            value=14.0,
            step=1.0,
            key="travel_dist"
        )

        expected_speed = st.number_input(
            "Velocidade esperada (cm/s)",
            value=2.5,
            step=0.1,
            key="expected_speed"
        )

    with col2:
        dose_rate = st.number_input(
            "Taxa de dose (MU/min)",
            value=600,
            step=50,
            key="dose_rate_speed"
        )

        mu_delivered = st.number_input(
            "MU entregues",
            value=100,
            step=10,
            key="mu_speed"
        )

    st.markdown("#### Medições de Tempo")

    n_tests = st.number_input("Número de repetições", min_value=1, max_value=10, value=3, key="n_speed_tests")

    travel_times = []
    cols = st.columns(min(n_tests, 5))

    for i in range(n_tests):
        col_idx = i % 5
        with cols[col_idx]:
            t = st.number_input(
                f"Tempo {i+1} (s)",
                value=5.6,
                step=0.1,
                format="%.2f",
                key=f"time_{i}"
            )
            travel_times.append(t)

    if travel_times:
        st.markdown("#### Análise")

        # Calcular velocidades
        speeds = [travel_distance / t for t in travel_times]
        mean_speed = np.mean(speeds)
        std_speed = np.std(speeds)

        # Desvio da especificação
        deviation = ((mean_speed - expected_speed) / expected_speed) * 100

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Velocidade Média", f"{mean_speed:.2f} cm/s")

        with col2:
            st.metric("Desvio Padrão", f"{std_speed:.3f} cm/s")

        with col3:
            st.metric("Desvio da Especificação", f"{deviation:+.1f}%")

        with col4:
            tolerance = 10  # %
            if abs(deviation) <= tolerance:
                st.success("✅ APROVADO")
                speed_passed = True
            else:
                st.error("❌ REPROVADO")
                speed_passed = False

        # Gráfico
        fig, ax = plt.subplots(figsize=(8, 4))

        ax.bar(range(1, n_tests+1), speeds, color='steelblue', alpha=0.7)
        ax.axhline(y=expected_speed, color='g', linestyle='-', linewidth=2, label='Especificação')
        ax.axhline(y=expected_speed * 1.1, color='r', linestyle='--', label='+10%')
        ax.axhline(y=expected_speed * 0.9, color='r', linestyle='--', label='-10%')

        ax.set_xlabel('Medição')
        ax.set_ylabel('Velocidade (cm/s)')
        ax.set_title('Velocidade das Lâminas')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

# =============================================================================
# TAB 3: TRANSMISSÃO
# =============================================================================
with tab3:
    st.subheader("🔍 Transmissão do MLC")

    st.markdown("""
    Medição da transmissão de radiação através das lâminas fechadas.

    **Tipos de transmissão:**
    - **Intra-leaf**: Através do corpo da lâmina
    - **Inter-leaf**: Entre lâminas adjacentes
    - **Tongue-and-groove**: Efeito de encaixe

    **Tolerâncias típicas:**
    - Transmissão total: < 2-3%
    """)

    transmission_type = st.radio(
        "Tipo de medição",
        ["Transmissão Total (MLC fechado)", "Transmissão Inter-leaf", "Perfil de Transmissão"],
        key="trans_type"
    )

    if transmission_type == "Transmissão Total (MLC fechado)":
        st.markdown("#### Medição com MLC Totalmente Fechado")

        col1, col2 = st.columns(2)

        with col1:
            open_reading = st.number_input(
                "Leitura com campo aberto (nC ou cGy)",
                value=100.0,
                step=0.1,
                format="%.3f",
                key="open_trans"
            )

        with col2:
            closed_reading = st.number_input(
                "Leitura com MLC fechado (nC ou cGy)",
                value=1.5,
                step=0.01,
                format="%.3f",
                key="closed_trans"
            )

        if open_reading > 0:
            transmission = (closed_reading / open_reading) * 100

            st.markdown("#### Resultado")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Transmissão", f"{transmission:.2f}%")

            with col2:
                tolerance = 2.5  # %
                if transmission <= tolerance:
                    st.success(f"✅ APROVADO (Tolerância: < {tolerance}%)")
                    trans_passed = True
                else:
                    st.error(f"❌ REPROVADO (Tolerância: < {tolerance}%)")
                    trans_passed = False

    elif transmission_type == "Transmissão Inter-leaf":
        st.markdown("#### Medição em Diferentes Posições")

        n_positions = st.number_input("Número de posições", min_value=1, max_value=10, value=5, key="n_pos_trans")

        open_ref = st.number_input(
            "Leitura de referência (campo aberto)",
            value=100.0,
            step=0.1,
            key="open_ref_interleaf"
        )

        st.markdown("**Leituras por posição:**")

        interleaf_readings = []
        cols = st.columns(min(n_positions, 5))

        for i in range(n_positions):
            col_idx = i % 5
            with cols[col_idx]:
                reading = st.number_input(
                    f"Pos {i+1}",
                    value=1.8,
                    step=0.01,
                    format="%.3f",
                    key=f"interleaf_{i}"
                )
                interleaf_readings.append(reading)

        if interleaf_readings and open_ref > 0:
            transmissions = [(r / open_ref) * 100 for r in interleaf_readings]

            st.markdown("#### Análise")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Transmissão Média", f"{np.mean(transmissions):.2f}%")
            with col2:
                st.metric("Transmissão Máxima", f"{np.max(transmissions):.2f}%")
            with col3:
                st.metric("Desvio Padrão", f"{np.std(transmissions):.3f}%")

    else:  # Perfil de Transmissão
        st.markdown("#### Upload de Perfil de Transmissão")

        uploaded_profile = st.file_uploader(
            "Carregar arquivo de perfil (.csv)",
            type=['csv', 'txt'],
            key="trans_profile"
        )

        if uploaded_profile:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded_profile, header=None)
                positions = df[0].values
                values = df[1].values

                # Normalizar
                max_val = np.max(values)
                normalized = (values / max_val) * 100

                fig, ax = plt.subplots(figsize=(12, 5))

                ax.plot(positions, normalized, 'b-', linewidth=1)
                ax.axhline(y=2.5, color='r', linestyle='--', label='Tolerância (2.5%)')

                ax.set_xlabel('Posição (mm)')
                ax.set_ylabel('Transmissão Relativa (%)')
                ax.set_title('Perfil de Transmissão do MLC')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_ylim(0, max(5, np.max(normalized) * 1.1))

                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

                st.success(f"✅ Perfil carregado: {len(positions)} pontos")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {str(e)}")

# =============================================================================
# TAB 4: GARDEN FENCE
# =============================================================================
with tab4:
    st.subheader("🌿 Teste Garden Fence")

    st.markdown("""
    O teste Garden Fence verifica a precisão de posicionamento das lâminas
    através de uma série de faixas (strips) irradiadas.

    **Procedimento:**
    1. Criar plano com gaps estreitos entre lâminas
    2. Irradiar em filme ou EPID
    3. Analisar uniformidade das faixas
    """)

    fence_method = st.radio(
        "Método de análise",
        ["Medição manual (régua)", "Análise de imagem"],
        key="fence_method"
    )

    if fence_method == "Medição manual (régua)":
        st.markdown("#### Configuração do Teste")

        col1, col2 = st.columns(2)

        with col1:
            n_strips = st.number_input("Número de faixas", min_value=2, max_value=20, value=10, key="n_strips")
            expected_width = st.number_input("Largura esperada (mm)", value=2.0, step=0.1, key="exp_width")

        with col2:
            expected_spacing = st.number_input("Espaçamento esperado (mm)", value=20.0, step=1.0, key="exp_spacing")

        st.markdown("#### Medições das Faixas")

        strip_widths = []
        strip_positions = []

        cols = st.columns(min(n_strips, 5))

        for i in range(n_strips):
            col_idx = i % 5
            with cols[col_idx]:
                width = st.number_input(
                    f"Faixa {i+1} (mm)",
                    value=expected_width,
                    step=0.1,
                    format="%.2f",
                    key=f"strip_w_{i}"
                )
                strip_widths.append(width)

        if strip_widths:
            st.markdown("#### Análise")

            width_errors = [w - expected_width for w in strip_widths]
            max_error = np.max(np.abs(width_errors))

            # Gráfico
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

            # Larguras
            ax1.bar(range(1, n_strips+1), strip_widths, color='forestgreen', alpha=0.7)
            ax1.axhline(y=expected_width, color='r', linestyle='--', label='Esperado')
            ax1.axhline(y=expected_width + 0.5, color='orange', linestyle=':', label='±0.5mm')
            ax1.axhline(y=expected_width - 0.5, color='orange', linestyle=':')
            ax1.set_xlabel('Faixa')
            ax1.set_ylabel('Largura (mm)')
            ax1.set_title('Largura das Faixas')
            ax1.legend()
            ax1.grid(True, alpha=0.3, axis='y')

            # Erros
            colors = ['green' if abs(e) <= 0.5 else 'red' for e in width_errors]
            ax2.bar(range(1, n_strips+1), width_errors, color=colors, alpha=0.7)
            ax2.axhline(y=0.5, color='orange', linestyle='--', label='Tolerância')
            ax2.axhline(y=-0.5, color='orange', linestyle='--')
            ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax2.set_xlabel('Faixa')
            ax2.set_ylabel('Erro (mm)')
            ax2.set_title('Erros de Largura')
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # Resultados
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Largura Média", f"{np.mean(strip_widths):.2f} mm")
            with col2:
                st.metric("Desvio Padrão", f"{np.std(strip_widths):.3f} mm")
            with col3:
                st.metric("Erro Máximo", f"{max_error:.2f} mm")
            with col4:
                tolerance = 0.5  # mm
                if max_error <= tolerance:
                    st.success("✅ APROVADO")
                    fence_passed = True
                else:
                    st.error("❌ REPROVADO")
                    fence_passed = False

    else:  # Análise de imagem
        st.markdown("#### Upload de Imagem Garden Fence")

        uploaded_fence = st.file_uploader(
            "Carregar imagem do teste Garden Fence",
            type=['dcm', 'tif', 'tiff', 'png', 'jpg'],
            key="fence_img"
        )

        if uploaded_fence:
            st.info("Análise automática de Garden Fence em desenvolvimento.")
            st.markdown("Use medição manual ou o módulo Picket Fence para análise similar.")

# =============================================================================
# TAB 5: RESUMO
# =============================================================================
with tab5:
    st.subheader("📊 Resumo do QA de MLC")

    st.markdown("#### Status dos Testes")

    tests_status = {
        "Posição das Lâminas": pos_passed if 'pos_passed' in dir() else None,
        "Velocidade": speed_passed if 'speed_passed' in dir() else None,
        "Transmissão": trans_passed if 'trans_passed' in dir() else None,
        "Garden Fence": fence_passed if 'fence_passed' in dir() else None,
    }

    status_table = []
    for test, passed in tests_status.items():
        if passed is None:
            status = "⚪ Não realizado"
        elif passed:
            status = "✅ Aprovado"
        else:
            status = "❌ Reprovado"
        status_table.append({"Teste": test, "Status": status})

    st.dataframe(status_table, use_container_width=True, hide_index=True)

    # Resumo geral
    completed = sum(1 for v in tests_status.values() if v is not None)
    passed = sum(1 for v in tests_status.values() if v is True)
    failed = sum(1 for v in tests_status.values() if v is False)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Testes Realizados", f"{completed}/{len(tests_status)}")

    with col2:
        st.metric("Aprovados", passed)

    with col3:
        st.metric("Reprovados", failed)

    # Observações
    mlc_notes = st.text_area(
        "Observações do QA de MLC",
        placeholder="Registre observações relevantes...",
        key="mlc_notes"
    )

    # Salvar
    if st.button("💾 Salvar QA de MLC", type="primary", key="save_mlc"):
        if DB_AVAILABLE and operator:
            results = {
                "mlc_type": mlc_type,
                "n_leaves": n_leaves,
                "tests_status": {k: v for k, v in tests_status.items()},
                "notes": mlc_notes
            }

            overall_passed = failed == 0 and completed > 0

            db.save_result(
                test_type="mlc_qa",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=overall_passed,
                notes=mlc_notes,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ QA de MLC salvo com sucesso!")
        elif not operator:
            st.warning("Informe o operador.")
        else:
            st.warning("Banco de dados não disponível.")

    st.divider()

    st.markdown("#### Referências TG-142 para MLC")

    tg142_mlc = [
        {"Teste": "Precisão de posição", "Frequência": "Mensal", "Tolerância": "±1 mm"},
        {"Teste": "Velocidade das lâminas", "Frequência": "Anual", "Tolerância": "Fabricante ±10%"},
        {"Teste": "Transmissão", "Frequência": "Anual", "Tolerância": "Baseline ±0.5%"},
        {"Teste": "Gap estreito (leaf gap)", "Frequência": "Mensal", "Tolerância": "±0.5 mm"},
        {"Teste": "Coincidência luz/radiação MLC", "Frequência": "Mensal", "Tolerância": "±2 mm"},
    ]

    st.dataframe(tg142_mlc, use_container_width=True, hide_index=True)
