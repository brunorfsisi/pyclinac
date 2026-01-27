"""
Output Factors e PDD - Medições dosimétricas fundamentais
"""

import streamlit as st
from datetime import datetime, date
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Output Factors", page_icon="📈", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info

create_sidebar_info(
    module_name="📈 Output Factors & PDD",
    description="""
    Medições dosimétricas fundamentais para comissionamento e QA.

    **Funcionalidades:**
    - Output Factors (Sc,p) por tamanho de campo
    - Curvas de PDD (Percentage Depth Dose)
    - TMR/TPR
    - Perfis de feixe (Profiles)
    - Comparação com baseline

    **Referências:**
    - AAPM TG-51, TG-106
    - BJR Supplement 25
    """,
    references=[
        ("AAPM TG-106", "https://www.aapm.org/pubs/reports/detail.asp?docid=89")
    ]
)

st.title("📈 Output Factors & PDD")
st.markdown("### Medições Dosimétricas Fundamentais")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Output Factors",
    "📉 PDD/TMR",
    "📐 Perfis",
    "📋 Histórico"
])

# Configurações comuns
with st.sidebar:
    st.subheader("Configurações")

    if DB_AVAILABLE:
        db = get_database()
        machines = db.get_machines()
        machine_names = [m['name'] for m in machines] if machines else ["Não cadastrada"]
        machine = st.selectbox("Máquina", options=machine_names, key="sidebar_machine")
    else:
        machine = st.text_input("Máquina", value="Clinac iX", key="sidebar_machine")

    energy_type = st.radio("Tipo de Feixe", ["Fótons", "Elétrons"])

    if energy_type == "Fótons":
        energy = st.selectbox(
            "Energia",
            ["6 MV", "10 MV", "15 MV", "18 MV", "6 MV FFF", "10 MV FFF"]
        )
    else:
        energy = st.selectbox(
            "Energia",
            ["6 MeV", "9 MeV", "12 MeV", "15 MeV", "18 MeV", "20 MeV", "22 MeV"]
        )

    ssd = st.number_input("SSD (cm)", value=100.0, step=1.0)
    operator = st.text_input("Operador", value="")
    test_date = st.date_input("Data", value=date.today())

# =============================================================================
# TAB 1: OUTPUT FACTORS
# =============================================================================
with tab1:
    st.subheader("📊 Output Factors (Sc,p)")

    st.markdown("""
    Fatores de output relativos ao campo de referência (10x10 cm²).

    **Procedimento:**
    1. Configure o feixe e SSD de referência
    2. Meça a dose para cada tamanho de campo
    3. Normalize pelo valor do campo 10x10
    """)

    # Tamanhos de campo padrão
    default_field_sizes = [3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 25, 30, 35, 40]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Medições")

        # Campo de referência
        ref_reading = st.number_input(
            "Leitura 10x10 cm² (nC ou cGy)",
            value=1.000,
            format="%.4f",
            step=0.001,
            key="ref_reading"
        )

        st.markdown("**Leituras por tamanho de campo:**")

        # Seleção de tamanhos de campo a medir
        selected_sizes = st.multiselect(
            "Tamanhos de campo (cm)",
            options=default_field_sizes,
            default=[4, 5, 6, 8, 10, 12, 15, 20, 25, 30]
        )

        # Entrada de valores
        measurements = {}
        cols = st.columns(5)

        for i, size in enumerate(sorted(selected_sizes)):
            col_idx = i % 5
            with cols[col_idx]:
                if size == 10:
                    measurements[size] = ref_reading
                    st.text_input(
                        f"{size}x{size}",
                        value=f"{ref_reading:.4f}",
                        disabled=True,
                        key=f"field_{size}"
                    )
                else:
                    val = st.number_input(
                        f"{size}x{size}",
                        value=1.000,
                        format="%.4f",
                        step=0.001,
                        key=f"field_{size}"
                    )
                    measurements[size] = val

    with col2:
        st.markdown("#### Output Factors Calculados")

        if ref_reading > 0 and measurements:
            of_data = []
            for size in sorted(measurements.keys()):
                of = measurements[size] / ref_reading
                of_data.append({
                    "Campo (cm²)": f"{size}x{size}",
                    "Leitura": f"{measurements[size]:.4f}",
                    "OF": f"{of:.4f}"
                })

            st.dataframe(of_data, use_container_width=True, hide_index=True)

    # Gráfico de Output Factors
    if measurements and ref_reading > 0:
        st.markdown("#### Curva de Output Factor")

        sizes = sorted(measurements.keys())
        of_values = [measurements[s] / ref_reading for s in sizes]

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(sizes, of_values, 'b-o', linewidth=2, markersize=8, label='Medido')
        ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Referência (10x10)')

        ax.set_xlabel('Tamanho de Campo (cm)')
        ax.set_ylabel('Output Factor (Sc,p)')
        ax.set_title(f'Output Factors - {energy} @ SSD {ssd} cm')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(sizes) + 2)
        ax.set_ylim(min(of_values) * 0.95, max(of_values) * 1.05)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Comparação com baseline
    st.markdown("#### Comparação com Baseline")

    use_baseline = st.checkbox("Comparar com valores de baseline", key="use_of_baseline")

    if use_baseline:
        st.markdown("**Insira os valores de baseline (comissionamento):**")

        baseline_values = {}
        cols = st.columns(5)

        for i, size in enumerate(sorted(selected_sizes)):
            col_idx = i % 5
            with cols[col_idx]:
                baseline_values[size] = st.number_input(
                    f"BL {size}x{size}",
                    value=1.000 if size == 10 else 0.950,
                    format="%.4f",
                    step=0.001,
                    key=f"baseline_{size}"
                )

        if baseline_values and measurements and ref_reading > 0:
            st.markdown("**Diferenças:**")

            diff_data = []
            max_diff = 0

            for size in sorted(selected_sizes):
                measured_of = measurements[size] / ref_reading
                baseline_of = baseline_values[size]
                diff_percent = ((measured_of - baseline_of) / baseline_of) * 100

                max_diff = max(max_diff, abs(diff_percent))

                status = "✅" if abs(diff_percent) <= 2.0 else "⚠️" if abs(diff_percent) <= 3.0 else "❌"

                diff_data.append({
                    "Campo": f"{size}x{size}",
                    "Baseline": f"{baseline_of:.4f}",
                    "Medido": f"{measured_of:.4f}",
                    "Diferença": f"{diff_percent:+.2f}%",
                    "Status": status
                })

            st.dataframe(diff_data, use_container_width=True, hide_index=True)

            tolerance = 2.0  # %
            if max_diff <= tolerance:
                st.success(f"✅ Máxima diferença: {max_diff:.2f}% (Tolerância: ±{tolerance}%)")
            else:
                st.error(f"❌ Máxima diferença: {max_diff:.2f}% (Tolerância: ±{tolerance}%)")

    # Salvar
    if st.button("💾 Salvar Output Factors", type="primary", key="save_of"):
        if DB_AVAILABLE and operator:
            of_results = {}
            for size in sorted(measurements.keys()):
                of_results[f"{size}x{size}"] = measurements[size] / ref_reading

            results = {
                "energy": energy,
                "ssd": ssd,
                "reference_reading": ref_reading,
                "measurements": measurements,
                "output_factors": of_results
            }

            db.save_result(
                test_type="output_factors",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=True,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ Output Factors salvos!")
        elif not operator:
            st.warning("Informe o operador.")
        else:
            st.warning("Banco de dados não disponível.")

# =============================================================================
# TAB 2: PDD/TMR
# =============================================================================
with tab2:
    st.subheader("📉 PDD e TMR")

    pdd_mode = st.radio(
        "Tipo de Medição",
        ["PDD (Percentage Depth Dose)", "TMR (Tissue Maximum Ratio)"],
        horizontal=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Parâmetros de Medição")

        field_size = st.selectbox(
            "Tamanho de Campo (cm²)",
            ["5x5", "10x10", "15x15", "20x20", "25x25", "30x30"],
            index=1,
            key="pdd_field"
        )

        if pdd_mode == "PDD (Percentage Depth Dose)":
            depth_max = st.number_input("Profundidade de dmax (cm)", value=1.5, step=0.1)
        else:
            reference_depth = st.number_input("Profundidade de referência (cm)", value=10.0, step=0.1)

    with col2:
        st.markdown("#### Profundidades")

        default_depths = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0]

        selected_depths = st.multiselect(
            "Profundidades a medir (cm)",
            options=default_depths,
            default=[1.5, 5.0, 10.0, 15.0, 20.0]
        )

    st.markdown("#### Leituras")

    # Entrada de leituras
    depth_readings = {}

    if pdd_mode == "PDD (Percentage Depth Dose)":
        dmax_reading = st.number_input(
            f"Leitura em dmax ({depth_max} cm)",
            value=1.000,
            format="%.4f",
            step=0.001,
            key="dmax_reading"
        )

    cols = st.columns(5)
    for i, depth in enumerate(sorted(selected_depths)):
        col_idx = i % 5
        with cols[col_idx]:
            depth_readings[depth] = st.number_input(
                f"d = {depth} cm",
                value=1.000,
                format="%.4f",
                step=0.001,
                key=f"depth_{depth}"
            )

    # Calcular e plotar
    if depth_readings:
        st.markdown("#### Curva de Dose em Profundidade")

        depths = sorted(depth_readings.keys())

        if pdd_mode == "PDD (Percentage Depth Dose)" and dmax_reading > 0:
            values = [(depth_readings[d] / dmax_reading) * 100 for d in depths]
            ylabel = "PDD (%)"
            title = f"PDD - {energy}, Campo {field_size}, SSD {ssd} cm"
        else:
            ref_reading_tmr = depth_readings.get(10.0, 1.0)
            values = [depth_readings[d] / ref_reading_tmr if ref_reading_tmr > 0 else 0 for d in depths]
            ylabel = "TMR"
            title = f"TMR - {energy}, Campo {field_size}"

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(depths, values, 'b-o', linewidth=2, markersize=8)

        if pdd_mode == "PDD (Percentage Depth Dose)":
            # Adicionar pontos de referência
            ax.axhline(y=100, color='r', linestyle='--', alpha=0.3, label='dmax (100%)')
            ax.axhline(y=50, color='g', linestyle='--', alpha=0.3, label='D50')

            # Encontrar D50
            for i in range(len(values) - 1):
                if values[i] >= 50 and values[i+1] < 50:
                    # Interpolação linear
                    d50 = depths[i] + (depths[i+1] - depths[i]) * (values[i] - 50) / (values[i] - values[i+1])
                    ax.axvline(x=d50, color='g', linestyle=':', alpha=0.5)
                    ax.text(d50, 52, f'D50={d50:.1f}cm', ha='center')
                    break

        ax.set_xlabel('Profundidade (cm)')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(depths) + 1)

        if pdd_mode == "PDD (Percentage Depth Dose)":
            ax.set_ylim(0, 110)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Tabela de resultados
        st.markdown("#### Tabela de Valores")

        pdd_table = []
        for d, v in zip(depths, values):
            pdd_table.append({
                "Profundidade (cm)": f"{d:.1f}",
                "Leitura": f"{depth_readings[d]:.4f}",
                ylabel: f"{v:.2f}" if pdd_mode == "PDD (Percentage Depth Dose)" else f"{v:.4f}"
            })

        st.dataframe(pdd_table, use_container_width=True, hide_index=True)

        # Parâmetros derivados para fótons
        if energy_type == "Fótons" and pdd_mode == "PDD (Percentage Depth Dose)":
            st.markdown("#### Parâmetros Derivados")

            col1, col2, col3 = st.columns(3)

            # PDD(10)
            pdd_10 = None
            for i, d in enumerate(depths):
                if d == 10.0:
                    pdd_10 = values[i]
                    break

            with col1:
                if pdd_10:
                    st.metric("PDD(10)", f"{pdd_10:.2f}%")

            # PDD(20)
            pdd_20 = None
            for i, d in enumerate(depths):
                if d == 20.0:
                    pdd_20 = values[i]
                    break

            with col2:
                if pdd_20:
                    st.metric("PDD(20)", f"{pdd_20:.2f}%")

            # Quality Index
            with col3:
                if pdd_10 and pdd_20:
                    qi = pdd_20 / pdd_10
                    st.metric("Quality Index (QI)", f"{qi:.4f}")

    # Salvar PDD
    if st.button("💾 Salvar PDD/TMR", type="primary", key="save_pdd"):
        if DB_AVAILABLE and operator:
            results = {
                "type": "PDD" if pdd_mode.startswith("PDD") else "TMR",
                "energy": energy,
                "ssd": ssd,
                "field_size": field_size,
                "depths": depths,
                "values": values,
                "raw_readings": depth_readings
            }

            db.save_result(
                test_type="pdd_tmr",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=True,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ Dados de PDD/TMR salvos!")
        else:
            st.warning("Informe o operador ou banco de dados não disponível.")

# =============================================================================
# TAB 3: PERFIS
# =============================================================================
with tab3:
    st.subheader("📐 Perfis de Feixe (Profiles)")

    st.markdown("""
    Análise de perfis transversais do feixe para verificação de
    simetria e flatness.
    """)

    col1, col2 = st.columns(2)

    with col1:
        profile_field = st.selectbox(
            "Tamanho de Campo",
            ["10x10", "20x20", "30x30", "40x40"],
            key="profile_field"
        )

        profile_depth = st.number_input(
            "Profundidade (cm)",
            value=10.0,
            step=0.5,
            key="profile_depth"
        )

    with col2:
        profile_direction = st.radio(
            "Direção",
            ["Crossplane (Gun-Target)", "Inplane (Left-Right)", "Diagonal"],
            key="profile_direction"
        )

    st.markdown("#### Dados do Perfil")

    input_method = st.radio(
        "Método de entrada",
        ["Manual", "Importar arquivo"],
        horizontal=True
    )

    if input_method == "Manual":
        # Posições padrão para um campo 10x10 ou maior
        default_positions = [-15, -12, -10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12, 15]

        st.markdown("**Posições (cm) e Leituras:**")

        profile_data = {}

        cols = st.columns(5)
        for i, pos in enumerate(default_positions):
            col_idx = i % 5
            with cols[col_idx]:
                reading = st.number_input(
                    f"x = {pos:+.0f}",
                    value=100.0 if abs(pos) <= 4 else 80.0,
                    step=0.1,
                    key=f"profile_pos_{pos}"
                )
                profile_data[pos] = reading

    else:
        uploaded_file = st.file_uploader(
            "Carregar arquivo de perfil (.csv, .txt)",
            type=['csv', 'txt'],
            key="profile_file"
        )

        if uploaded_file:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded_file, header=None)
                profile_data = dict(zip(df[0], df[1]))
                st.success(f"✅ Carregados {len(profile_data)} pontos")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {str(e)}")
                profile_data = {}
        else:
            profile_data = {}

    # Análise do perfil
    if profile_data:
        positions = sorted(profile_data.keys())
        readings = [profile_data[p] for p in positions]

        # Normalizar pelo centro (ou máximo)
        center_value = profile_data.get(0, max(readings))
        normalized = [r / center_value * 100 for r in readings]

        # Plot do perfil
        st.markdown("#### Perfil Normalizado")

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(positions, normalized, 'b-o', linewidth=2, markersize=6, label='Perfil')
        ax.axhline(y=100, color='r', linestyle='--', alpha=0.3)
        ax.axhline(y=80, color='g', linestyle='--', alpha=0.3, label='80% (borda)')

        # Limites do campo (assumindo 80%)
        field_edges = []
        for i in range(len(normalized) - 1):
            if (normalized[i] >= 80 and normalized[i+1] < 80) or (normalized[i] < 80 and normalized[i+1] >= 80):
                # Interpolação
                edge = positions[i] + (positions[i+1] - positions[i]) * (normalized[i] - 80) / (normalized[i] - normalized[i+1])
                field_edges.append(edge)
                ax.axvline(x=edge, color='orange', linestyle=':', alpha=0.5)

        ax.set_xlabel('Posição (cm)')
        ax.set_ylabel('Dose Relativa (%)')
        ax.set_title(f'Perfil {profile_direction} - {energy}, Campo {profile_field}, d={profile_depth}cm')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Cálculo de Flatness e Simetria
        st.markdown("#### Análise de Qualidade do Perfil")

        # Região central (80% do tamanho do campo)
        if len(field_edges) >= 2:
            left_edge = min(field_edges)
            right_edge = max(field_edges)
            field_width = right_edge - left_edge

            # Região de flatness (80% central)
            flat_region = 0.8 * field_width / 2
            flat_left = -flat_region
            flat_right = flat_region

            # Filtrar pontos na região central
            central_values = [normalized[i] for i, p in enumerate(positions)
                           if flat_left <= p <= flat_right]

            if central_values:
                # Flatness (CAX protocol)
                d_max = max(central_values)
                d_min = min(central_values)
                flatness = ((d_max - d_min) / (d_max + d_min)) * 100

                # Simetria
                # Comparar pontos simétricos
                symmetry_diffs = []
                for p in positions:
                    if p > 0 and -p in profile_data:
                        left_val = profile_data[-p]
                        right_val = profile_data[p]
                        avg = (left_val + right_val) / 2
                        if avg > 0:
                            sym_diff = abs(left_val - right_val) / avg * 100
                            symmetry_diffs.append(sym_diff)

                symmetry = max(symmetry_diffs) if symmetry_diffs else 0

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Tamanho do Campo", f"{field_width:.2f} cm")

                with col2:
                    flatness_tol = 3.0  # %
                    if flatness <= flatness_tol:
                        st.metric("Flatness", f"{flatness:.2f}%", delta="✅ OK")
                    else:
                        st.metric("Flatness", f"{flatness:.2f}%", delta="❌ Fora")

                with col3:
                    symmetry_tol = 3.0  # %
                    if symmetry <= symmetry_tol:
                        st.metric("Simetria", f"{symmetry:.2f}%", delta="✅ OK")
                    else:
                        st.metric("Simetria", f"{symmetry:.2f}%", delta="❌ Fora")

                with col4:
                    penumbra_left = None
                    penumbra_right = None
                    # Calcular penumbra (80% a 20%)
                    # Simplificado - apenas indicativo
                    st.metric("Penumbra (típica)", "5-8 mm")

        # Salvar perfil
        if st.button("💾 Salvar Perfil", type="primary", key="save_profile"):
            if DB_AVAILABLE and operator:
                results = {
                    "direction": profile_direction,
                    "energy": energy,
                    "field_size": profile_field,
                    "depth": profile_depth,
                    "positions": positions,
                    "normalized_values": normalized,
                    "flatness": flatness if 'flatness' in dir() else None,
                    "symmetry": symmetry if 'symmetry' in dir() else None,
                    "field_width": field_width if 'field_width' in dir() else None
                }

                db.save_result(
                    test_type="beam_profile",
                    results=results,
                    machine_name=machine,
                    performed_by=operator,
                    passed=True,
                    test_date=datetime.combine(test_date, datetime.min.time())
                )
                st.success("✅ Perfil salvo!")
            else:
                st.warning("Informe o operador ou banco de dados não disponível.")

# =============================================================================
# TAB 4: HISTÓRICO
# =============================================================================
with tab4:
    st.subheader("📋 Histórico de Medições")

    if DB_AVAILABLE:
        data_type = st.selectbox(
            "Tipo de Dados",
            ["output_factors", "pdd_tmr", "beam_profile"],
            format_func=lambda x: {
                "output_factors": "Output Factors",
                "pdd_tmr": "PDD/TMR",
                "beam_profile": "Perfis"
            }.get(x, x)
        )

        from datetime import timedelta
        period = st.selectbox(
            "Período",
            [30, 60, 90, 180, 365],
            format_func=lambda x: f"Últimos {x} dias"
        )

        start_date = datetime.now() - timedelta(days=period)
        results = db.get_results(
            test_type=data_type,
            start_date=start_date,
            limit=50
        )

        if results:
            table_data = []
            for r in results:
                row = {
                    "Data": r['test_date'][:10] if r['test_date'] else "N/A",
                    "Máquina": r['machine_name'] or "N/A",
                    "Operador": r['performed_by'] or "N/A",
                }

                if r.get('results'):
                    res = r['results']
                    row["Energia"] = res.get('energy', 'N/A')

                    if data_type == "output_factors":
                        row["Campos"] = len(res.get('output_factors', {}))
                    elif data_type == "pdd_tmr":
                        row["Tipo"] = res.get('type', 'N/A')
                        row["Campo"] = res.get('field_size', 'N/A')
                    elif data_type == "beam_profile":
                        row["Direção"] = res.get('direction', 'N/A')[:20] if res.get('direction') else 'N/A'
                        row["Flatness"] = f"{res.get('flatness', 0):.2f}%" if res.get('flatness') else 'N/A'

                table_data.append(row)

            st.dataframe(table_data, use_container_width=True, hide_index=True)

            # Opção para visualizar detalhes
            if st.checkbox("Mostrar detalhes do resultado selecionado"):
                idx = st.number_input("Índice do resultado", min_value=0, max_value=len(results)-1, value=0)
                st.json(results[idx].get('results', {}))
        else:
            st.info("Nenhum resultado encontrado no período.")
    else:
        st.warning("Banco de dados não disponível.")
