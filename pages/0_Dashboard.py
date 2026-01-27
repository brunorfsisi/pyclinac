"""
Dashboard - Visão geral do sistema de QA
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info

create_sidebar_info(
    module_name="📊 Dashboard",
    description="""
    Painel de controle com visão geral de todos os testes de QA realizados.

    - Estatísticas de aprovação/reprovação
    - Tendências ao longo do tempo
    - Resumo por máquina e tipo de teste
    """,
    references=[]
)

st.title("📊 Dashboard de Controle de Qualidade")

if not DB_AVAILABLE:
    st.warning("⚠️ Banco de dados não disponível. Os dados de histórico não serão salvos.")

    # Dashboard de demonstração
    st.markdown("### Demonstração do Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Testes Realizados", "0", delta="Último mês")

    with col2:
        st.metric("Taxa de Aprovação", "N/A", delta="")

    with col3:
        st.metric("Máquinas Cadastradas", "0")

    with col4:
        st.metric("Próxima Calibração", "N/A")

    st.info("Configure uma máquina e realize alguns testes para ver os dados no dashboard.")

else:
    db = get_database()

    # Período de análise
    period = st.selectbox(
        "Período de análise",
        options=[7, 14, 30, 60, 90, 180, 365],
        index=2,
        format_func=lambda x: f"Últimos {x} dias"
    )

    # Obtém estatísticas
    stats = db.get_summary_stats(days=period)

    # Métricas principais
    st.subheader("Resumo Geral")

    col1, col2, col3, col4 = st.columns(4)

    total = stats['overall']['total'] or 0
    passed = stats['overall']['passed'] or 0
    failed = stats['overall']['failed'] or 0
    pass_rate = (passed / total * 100) if total > 0 else 0

    with col1:
        st.metric(
            "Total de Testes",
            f"{total}",
            delta=f"Período: {period} dias"
        )

    with col2:
        delta_color = "normal" if pass_rate >= 90 else "off"
        st.metric(
            "Taxa de Aprovação",
            f"{pass_rate:.1f}%",
            delta="Meta: 95%"
        )

    with col3:
        st.metric("Aprovados", f"{passed}", delta="✅")

    with col4:
        st.metric("Reprovados", f"{failed}", delta="❌" if failed > 0 else None)

    st.divider()

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Testes por Tipo")

        if stats['by_type']:
            test_types = [t['test_type'] for t in stats['by_type']]
            totals = [t['total'] for t in stats['by_type']]

            fig1, ax1 = plt.subplots(figsize=(8, 5))
            colors = plt.cm.Set3(np.linspace(0, 1, len(test_types)))
            bars = ax1.barh(test_types, totals, color=colors)
            ax1.set_xlabel('Quantidade')
            ax1.set_title('Testes Realizados por Tipo')

            for bar, total in zip(bars, totals):
                ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                        f'{total}', va='center')

            plt.tight_layout()
            st.pyplot(fig1)
            plt.close(fig1)
        else:
            st.info("Nenhum teste realizado no período.")

    with col2:
        st.subheader("🏥 Testes por Máquina")

        if stats['by_machine']:
            machines = [m['name'] for m in stats['by_machine']]
            totals = [m['total'] for m in stats['by_machine']]
            passed_list = [m['passed'] or 0 for m in stats['by_machine']]

            fig2, ax2 = plt.subplots(figsize=(8, 5))

            x = np.arange(len(machines))
            width = 0.35

            bars1 = ax2.bar(x - width/2, totals, width, label='Total', color='steelblue')
            bars2 = ax2.bar(x + width/2, passed_list, width, label='Aprovados', color='forestgreen')

            ax2.set_ylabel('Quantidade')
            ax2.set_title('Testes por Máquina')
            ax2.set_xticks(x)
            ax2.set_xticklabels(machines, rotation=45, ha='right')
            ax2.legend()

            plt.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)
        else:
            st.info("Nenhuma máquina cadastrada.")

    st.divider()

    # Resultados recentes
    st.subheader("📋 Resultados Recentes")

    recent_results = db.get_results(limit=10)

    if recent_results:
        results_table = []
        for r in recent_results:
            results_table.append({
                "Data": r['test_date'][:10] if r['test_date'] else "N/A",
                "Tipo": r['test_type'],
                "Máquina": r['machine_name'] or "N/A",
                "Status": "✅ Aprovado" if r['passed'] else "❌ Reprovado" if r['passed'] is not None else "⚪ N/A",
                "Operador": r['performed_by'] or "N/A"
            })

        st.dataframe(results_table, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum resultado registrado ainda.")

    st.divider()

    # Tendências
    st.subheader("📉 Análise de Tendências")

    col1, col2 = st.columns(2)

    with col1:
        trend_test = st.selectbox(
            "Tipo de Teste",
            options=["winston_lutz", "picket_fence", "starshot", "vmat_drgs",
                    "vmat_drmlc", "field_analysis", "catphan", "gamma"],
            format_func=lambda x: x.replace("_", " ").title()
        )

    with col2:
        trend_param = st.text_input(
            "Parâmetro",
            value="max_error" if trend_test == "picket_fence" else "gantry_iso_size",
            help="Nome do parâmetro nos resultados JSON"
        )

    # Obtém dados de tendência
    trend_data = db.get_trend_data(trend_test, trend_param, days=period)

    if trend_data:
        dates = [datetime.fromisoformat(d['date']) for d in trend_data]
        values = [d['value'] for d in trend_data]

        # Obtém tolerância
        tolerances = db.get_tolerances(trend_test)
        tol_value = None
        for t in tolerances:
            if t['parameter'] == trend_param:
                tol_value = t['tolerance_value']
                break

        fig3, ax3 = plt.subplots(figsize=(12, 5))

        ax3.plot(dates, values, 'b-o', linewidth=2, markersize=6, label=trend_param)

        if tol_value:
            ax3.axhline(y=tol_value, color='r', linestyle='--',
                       linewidth=2, label=f'Tolerância ({tol_value})')

        ax3.set_xlabel('Data')
        ax3.set_ylabel('Valor')
        ax3.set_title(f'Tendência: {trend_param} - {trend_test.replace("_", " ").title()}')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Média", f"{np.mean(values):.3f}")
        with col2:
            st.metric("Desvio Padrão", f"{np.std(values):.3f}")
        with col3:
            st.metric("Mínimo", f"{np.min(values):.3f}")
        with col4:
            st.metric("Máximo", f"{np.max(values):.3f}")

    else:
        st.info(f"Nenhum dado de tendência disponível para {trend_test} - {trend_param}")

    st.divider()

    # Máquinas cadastradas
    st.subheader("🏭 Máquinas Cadastradas")

    machines = db.get_machines()

    if machines:
        st.dataframe(machines, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma máquina cadastrada.")

    # Formulário para adicionar máquina
    with st.expander("➕ Adicionar Nova Máquina"):
        with st.form("add_machine"):
            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Nome *", placeholder="Clinac iX - Sala 1")
                new_manufacturer = st.text_input("Fabricante", placeholder="Varian")
                new_model = st.text_input("Modelo", placeholder="Clinac iX")

            with col2:
                new_serial = st.text_input("Número de Série", placeholder="123456")
                new_location = st.text_input("Localização", placeholder="Ala B - Térreo")

            if st.form_submit_button("Adicionar Máquina", type="primary"):
                if new_name:
                    try:
                        db.add_machine(
                            name=new_name,
                            manufacturer=new_manufacturer,
                            model=new_model,
                            serial_number=new_serial,
                            location=new_location
                        )
                        st.success(f"✅ Máquina '{new_name}' adicionada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao adicionar máquina: {str(e)}")
                else:
                    st.warning("Nome da máquina é obrigatório.")
