"""
TG-142 Checklists Completo
Checklists baseados no AAPM TG-142 para QA de aceleradores lineares
"""

import streamlit as st
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import pandas as pd

st.set_page_config(page_title="TG-142 Checklists", page_icon="📋", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info

create_sidebar_info(
    module_name="📋 TG-142 Checklists",
    description="""
    Checklists completos baseados no AAPM TG-142.

    **Frequências:**
    - Diário
    - Mensal
    - Anual

    **Categorias:**
    - Dosimetria
    - Mecânica
    - Segurança
    - Imagem

    Rastreamento automático de pendências e vencimentos.
    """,
    references=[
        ("AAPM TG-142 (2009)", "https://www.aapm.org/pubs/reports/detail.asp?docid=104")
    ]
)

st.title("📋 TG-142 Checklists")
st.markdown("### Quality Assurance of Medical Accelerators")

# Definição completa dos testes TG-142
TG142_TESTS = {
    "daily": {
        "dosimetry": [
            {"id": "D1", "test": "Constância de output - fótons", "tolerance": "±3%", "method": "Câmara ou diodo"},
            {"id": "D2", "test": "Constância de output - elétrons", "tolerance": "±3%", "method": "Câmara ou diodo"},
        ],
        "mechanical": [
            {"id": "M1", "test": "Lasers", "tolerance": "±2 mm", "method": "Visual"},
            {"id": "M2", "test": "Indicador de distância (ODI)", "tolerance": "±2 mm", "method": "Régua"},
            {"id": "M3", "test": "Coincidência luz/radiação", "tolerance": "±2 mm ou 1%", "method": "Visual/filme"},
        ],
        "safety": [
            {"id": "S1", "test": "Portas interlocks", "tolerance": "Funcional", "method": "Teste funcional"},
            {"id": "S2", "test": "Alarmes audiovisuais", "tolerance": "Funcional", "method": "Verificação"},
            {"id": "S3", "test": "Monitores de área", "tolerance": "Funcional", "method": "Verificação"},
        ]
    },
    "monthly": {
        "dosimetry": [
            {"id": "D3", "test": "Constância de output - todas energias", "tolerance": "±2%", "method": "Câmara calibrada"},
            {"id": "D4", "test": "Backup monitor", "tolerance": "±2%", "method": "Câmara calibrada"},
            {"id": "D5", "test": "Constância de energia - fótons (PDD ou TMR)", "tolerance": "±1%", "method": "Tanque/câmara"},
            {"id": "D6", "test": "Constância de energia - elétrons (R50)", "tolerance": "±1 mm", "method": "Tanque/câmara"},
            {"id": "D7", "test": "Flatness constância", "tolerance": "±1%", "method": "Perfil/array"},
            {"id": "D8", "test": "Simetria constância", "tolerance": "±1%", "method": "Perfil/array"},
        ],
        "mechanical": [
            {"id": "M4", "test": "Indicadores de gantry", "tolerance": "±1°", "method": "Nível/inclinômetro"},
            {"id": "M5", "test": "Indicadores de colimador", "tolerance": "±1°", "method": "Nível/inclinômetro"},
            {"id": "M6", "test": "Indicadores de mesa", "tolerance": "±1°", "method": "Nível/inclinômetro"},
            {"id": "M7", "test": "Campo de luz vs jaws", "tolerance": "±2 mm", "method": "Régua"},
            {"id": "M8", "test": "Crosshair centralização", "tolerance": "±1 mm", "method": "Papel milimetrado"},
            {"id": "M9", "test": "Posição de tratamento (lat/long/vert)", "tolerance": "±1 mm", "method": "Régua"},
            {"id": "M10", "test": "Movimento da mesa", "tolerance": "±2 mm", "method": "Régua"},
            {"id": "M11", "test": "MLC posição", "tolerance": "±1 mm", "method": "Picket fence/filme"},
            {"id": "M12", "test": "Wedge posição", "tolerance": "±2 mm", "method": "Visual"},
        ],
        "safety": [
            {"id": "S4", "test": "Interlock de gantry/colimador", "tolerance": "Funcional", "method": "Teste funcional"},
            {"id": "S5", "test": "Botão de emergência", "tolerance": "Funcional", "method": "Teste funcional"},
        ],
        "imaging": [
            {"id": "I1", "test": "Coincidência isocentro kV-MV", "tolerance": "±2 mm", "method": "Phantom BB"},
            {"id": "I2", "test": "Qualidade de imagem kV", "tolerance": "Baseline", "method": "Phantom QA"},
            {"id": "I3", "test": "Qualidade de imagem CBCT", "tolerance": "Baseline", "method": "Phantom CatPhan"},
        ]
    },
    "annual": {
        "dosimetry": [
            {"id": "D9", "test": "Calibração absoluta de dose", "tolerance": "±1%", "method": "TG-51/TRS-398"},
            {"id": "D10", "test": "Output vs taxa de dose", "tolerance": "±2%", "method": "Câmara calibrada"},
            {"id": "D11", "test": "Linearidade do monitor", "tolerance": "±1%", "method": "Múltiplas MU"},
            {"id": "D12", "test": "Fatores de output (Sc,p)", "tolerance": "±2%", "method": "Múltiplos campos"},
            {"id": "D13", "test": "PDD/TMR completo", "tolerance": "±2% ou 2mm", "method": "Tanque 3D"},
            {"id": "D14", "test": "Perfis de feixe", "tolerance": "±1%", "method": "Tanque 3D"},
            {"id": "D15", "test": "Wedge factors", "tolerance": "±2%", "method": "Câmara calibrada"},
            {"id": "D16", "test": "Transmissão MLC", "tolerance": "±0.5%", "method": "Câmara/filme"},
            {"id": "D17", "test": "Aplicadores de elétrons", "tolerance": "±2%", "method": "Output por aplicador"},
        ],
        "mechanical": [
            {"id": "M13", "test": "Isocentro de radiação (star shot)", "tolerance": "±1 mm", "method": "Star shot"},
            {"id": "M14", "test": "Coincidência colimador/gantry/mesa", "tolerance": "±1 mm", "method": "Winston-Lutz"},
            {"id": "M15", "test": "Velocidade do gantry", "tolerance": "Especificação", "method": "Cronômetro"},
            {"id": "M16", "test": "Velocidade do MLC", "tolerance": "Especificação", "method": "Cronômetro"},
            {"id": "M17", "test": "Tamanhos de campo jaw", "tolerance": "±1 mm", "method": "Filme/régua"},
            {"id": "M18", "test": "Coincidência luz/radiação completa", "tolerance": "±1 mm", "method": "Filme"},
        ],
        "safety": [
            {"id": "S6", "test": "Revisão completa de interlocks", "tolerance": "Funcional", "method": "Teste completo"},
            {"id": "S7", "test": "Backup de energia", "tolerance": "Funcional", "method": "Teste"},
            {"id": "S8", "test": "Teste de terminação do feixe", "tolerance": "±0.5 MU", "method": "Câmara"},
        ],
        "imaging": [
            {"id": "I4", "test": "Calibração geométrica CBCT", "tolerance": "±1 mm", "method": "Phantom geométrico"},
            {"id": "I5", "test": "Números CT CBCT", "tolerance": "Baseline ±20 HU", "method": "CatPhan"},
            {"id": "I6", "test": "Dose CBCT", "tolerance": "Baseline ±20%", "method": "Dosímetro"},
            {"id": "I7", "test": "EPID calibração dosimétrica", "tolerance": "±3%", "method": "Câmara ref"},
        ]
    }
}

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌅 Diário",
    "📆 Mensal",
    "📅 Anual",
    "📊 Rastreamento",
    "📈 Relatórios"
])

# Configurações comuns
with st.sidebar:
    st.subheader("Configurações")

    if DB_AVAILABLE:
        db = get_database()
        machines = db.get_machines()
        machine_names = [m['name'] for m in machines] if machines else ["Não cadastrada"]
        machine = st.selectbox("Máquina", options=machine_names, key="tg142_machine")
    else:
        machine = st.text_input("Máquina", value="Clinac iX", key="tg142_machine")

    operator = st.text_input("Operador", key="tg142_operator")
    test_date = st.date_input("Data", value=date.today(), key="tg142_date")

def render_checklist(tests_dict, frequency):
    """Renderiza um checklist completo com categorias"""

    results = {}
    total_tests = 0
    passed_tests = 0

    for category, tests in tests_dict.items():
        category_names = {
            "dosimetry": "📊 Dosimetria",
            "mechanical": "⚙️ Mecânica",
            "safety": "🛡️ Segurança",
            "imaging": "📷 Imagem"
        }

        st.markdown(f"### {category_names.get(category, category)}")

        results[category] = []

        for test in tests:
            total_tests += 1

            col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1.5, 1.5, 1])

            with col1:
                st.markdown(f"**{test['id']}**")

            with col2:
                st.markdown(test['test'])

            with col3:
                st.caption(f"Tol: {test['tolerance']}")

            with col4:
                status = st.selectbox(
                    "Status",
                    ["Pendente", "Aprovado", "Reprovado", "N/A"],
                    key=f"{frequency}_{test['id']}",
                    label_visibility="collapsed"
                )

            with col5:
                if status == "Aprovado":
                    st.success("✅")
                    passed_tests += 1
                elif status == "Reprovado":
                    st.error("❌")
                elif status == "N/A":
                    st.info("➖")
                else:
                    st.warning("⏳")

            results[category].append({
                "id": test['id'],
                "test": test['test'],
                "status": status,
                "tolerance": test['tolerance']
            })

        st.divider()

    return results, total_tests, passed_tests

# =============================================================================
# TAB 1: DIÁRIO
# =============================================================================
with tab1:
    st.subheader("🌅 Checklist Diário TG-142")

    st.markdown(f"**Data:** {test_date.strftime('%d/%m/%Y')} | **Máquina:** {machine}")

    daily_results, daily_total, daily_passed = render_checklist(TG142_TESTS["daily"], "daily")

    # Resumo
    st.markdown("### Resumo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Testes", daily_total)
    with col2:
        st.metric("Aprovados", daily_passed)
    with col3:
        rate = (daily_passed / daily_total * 100) if daily_total > 0 else 0
        st.metric("Taxa de Aprovação", f"{rate:.0f}%")

    daily_notes = st.text_area("Observações", key="daily_notes_tg142")

    if st.button("💾 Salvar Checklist Diário", type="primary", key="save_daily_tg142"):
        if DB_AVAILABLE and operator:
            results = {
                "frequency": "daily",
                "categories": daily_results,
                "summary": {
                    "total": daily_total,
                    "passed": daily_passed,
                    "rate": rate
                },
                "notes": daily_notes
            }

            db.save_result(
                test_type="tg142_daily",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=(daily_passed == daily_total),
                notes=daily_notes,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ Checklist diário salvo!")
        else:
            st.warning("Informe o operador ou banco não disponível.")

# =============================================================================
# TAB 2: MENSAL
# =============================================================================
with tab2:
    st.subheader("📆 Checklist Mensal TG-142")

    st.markdown(f"**Mês:** {test_date.strftime('%B/%Y')} | **Máquina:** {machine}")

    monthly_results, monthly_total, monthly_passed = render_checklist(TG142_TESTS["monthly"], "monthly")

    # Resumo
    st.markdown("### Resumo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Testes", monthly_total)
    with col2:
        st.metric("Aprovados", monthly_passed)
    with col3:
        rate = (monthly_passed / monthly_total * 100) if monthly_total > 0 else 0
        st.metric("Taxa de Aprovação", f"{rate:.0f}%")

    monthly_notes = st.text_area("Observações", key="monthly_notes_tg142")

    if st.button("💾 Salvar Checklist Mensal", type="primary", key="save_monthly_tg142"):
        if DB_AVAILABLE and operator:
            results = {
                "frequency": "monthly",
                "categories": monthly_results,
                "summary": {
                    "total": monthly_total,
                    "passed": monthly_passed,
                    "rate": rate
                },
                "notes": monthly_notes
            }

            db.save_result(
                test_type="tg142_monthly",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=(monthly_passed == monthly_total),
                notes=monthly_notes,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ Checklist mensal salvo!")
        else:
            st.warning("Informe o operador ou banco não disponível.")

# =============================================================================
# TAB 3: ANUAL
# =============================================================================
with tab3:
    st.subheader("📅 Checklist Anual TG-142")

    st.markdown(f"**Ano:** {test_date.year} | **Máquina:** {machine}")

    annual_results, annual_total, annual_passed = render_checklist(TG142_TESTS["annual"], "annual")

    # Resumo
    st.markdown("### Resumo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Testes", annual_total)
    with col2:
        st.metric("Aprovados", annual_passed)
    with col3:
        rate = (annual_passed / annual_total * 100) if annual_total > 0 else 0
        st.metric("Taxa de Aprovação", f"{rate:.0f}%")

    annual_notes = st.text_area("Observações", key="annual_notes_tg142")

    if st.button("💾 Salvar Checklist Anual", type="primary", key="save_annual_tg142"):
        if DB_AVAILABLE and operator:
            results = {
                "frequency": "annual",
                "categories": annual_results,
                "summary": {
                    "total": annual_total,
                    "passed": annual_passed,
                    "rate": rate
                },
                "notes": annual_notes
            }

            db.save_result(
                test_type="tg142_annual",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=(annual_passed == annual_total),
                notes=annual_notes,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ Checklist anual salvo!")
        else:
            st.warning("Informe o operador ou banco não disponível.")

# =============================================================================
# TAB 4: RASTREAMENTO
# =============================================================================
with tab4:
    st.subheader("📊 Rastreamento de QA")

    if DB_AVAILABLE:
        st.markdown("### Status de Conformidade")

        # Verificar últimos testes realizados
        today = datetime.now()

        # Último diário
        daily_results = db.get_results(test_type="tg142_daily", limit=1)
        last_daily = daily_results[0]['test_date'][:10] if daily_results else "Nunca"

        # Último mensal
        monthly_results = db.get_results(test_type="tg142_monthly", limit=1)
        last_monthly = monthly_results[0]['test_date'][:10] if monthly_results else "Nunca"

        # Último anual
        annual_results = db.get_results(test_type="tg142_annual", limit=1)
        last_annual = annual_results[0]['test_date'][:10] if annual_results else "Nunca"

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### Diário")
            st.metric("Último Teste", last_daily)

            if last_daily != "Nunca":
                last_date = datetime.strptime(last_daily, "%Y-%m-%d")
                days_since = (today - last_date).days

                if days_since == 0:
                    st.success("✅ Em dia")
                elif days_since == 1:
                    st.warning("⚠️ 1 dia atrás")
                else:
                    st.error(f"❌ {days_since} dias atrás")
            else:
                st.error("❌ Nunca realizado")

        with col2:
            st.markdown("#### Mensal")
            st.metric("Último Teste", last_monthly)

            if last_monthly != "Nunca":
                last_date = datetime.strptime(last_monthly, "%Y-%m-%d")
                days_since = (today - last_date).days

                if days_since <= 30:
                    st.success("✅ Em dia")
                elif days_since <= 45:
                    st.warning(f"⚠️ {days_since} dias atrás")
                else:
                    st.error(f"❌ {days_since} dias atrás")
            else:
                st.error("❌ Nunca realizado")

        with col3:
            st.markdown("#### Anual")
            st.metric("Último Teste", last_annual)

            if last_annual != "Nunca":
                last_date = datetime.strptime(last_annual, "%Y-%m-%d")
                days_since = (today - last_date).days

                if days_since <= 365:
                    st.success("✅ Em dia")
                elif days_since <= 400:
                    st.warning(f"⚠️ {days_since} dias atrás")
                else:
                    st.error(f"❌ {days_since} dias atrás (VENCIDO)")
            else:
                st.error("❌ Nunca realizado")

        st.divider()

        # Calendário de próximos testes
        st.markdown("### Próximos Testes")

        next_tests = []

        if last_daily != "Nunca":
            next_daily = datetime.strptime(last_daily, "%Y-%m-%d") + timedelta(days=1)
            next_tests.append({"Tipo": "Diário", "Data Prevista": next_daily.strftime("%d/%m/%Y"), "Status": "Pendente" if next_daily.date() <= today.date() else "Programado"})
        else:
            next_tests.append({"Tipo": "Diário", "Data Prevista": "Imediatamente", "Status": "URGENTE"})

        if last_monthly != "Nunca":
            next_monthly = datetime.strptime(last_monthly, "%Y-%m-%d") + timedelta(days=30)
            next_tests.append({"Tipo": "Mensal", "Data Prevista": next_monthly.strftime("%d/%m/%Y"), "Status": "Pendente" if next_monthly.date() <= today.date() else "Programado"})
        else:
            next_tests.append({"Tipo": "Mensal", "Data Prevista": "Imediatamente", "Status": "URGENTE"})

        if last_annual != "Nunca":
            next_annual = datetime.strptime(last_annual, "%Y-%m-%d") + timedelta(days=365)
            next_tests.append({"Tipo": "Anual", "Data Prevista": next_annual.strftime("%d/%m/%Y"), "Status": "Pendente" if next_annual.date() <= today.date() else "Programado"})
        else:
            next_tests.append({"Tipo": "Anual", "Data Prevista": "Imediatamente", "Status": "URGENTE"})

        st.dataframe(next_tests, use_container_width=True, hide_index=True)

        st.divider()

        # Histórico de falhas
        st.markdown("### Testes Reprovados Recentes")

        failed_daily = db.get_results(test_type="tg142_daily", limit=30)
        failed_monthly = db.get_results(test_type="tg142_monthly", limit=12)
        failed_annual = db.get_results(test_type="tg142_annual", limit=3)

        failed_tests = []
        for r in failed_daily + failed_monthly + failed_annual:
            if not r['passed']:
                failed_tests.append({
                    "Data": r['test_date'][:10] if r['test_date'] else "N/A",
                    "Tipo": r['test_type'].replace("tg142_", "").title(),
                    "Máquina": r['machine_name'] or "N/A",
                    "Operador": r['performed_by'] or "N/A"
                })

        if failed_tests:
            st.dataframe(failed_tests, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Nenhum teste reprovado nos registros recentes!")

    else:
        st.warning("Banco de dados não disponível.")

# =============================================================================
# TAB 5: RELATÓRIOS
# =============================================================================
with tab5:
    st.subheader("📈 Relatórios TG-142")

    if DB_AVAILABLE:
        col1, col2 = st.columns(2)

        with col1:
            report_type = st.selectbox(
                "Tipo de Relatório",
                ["Resumo Mensal", "Resumo Anual", "Conformidade"],
                key="report_type"
            )

        with col2:
            if report_type == "Resumo Mensal":
                report_month = st.date_input("Mês", value=date.today().replace(day=1), key="report_month")
            elif report_type == "Resumo Anual":
                report_year = st.selectbox("Ano", [2024, 2025, 2026], index=1, key="report_year")

        if st.button("📄 Gerar Relatório", type="primary"):
            st.markdown("---")

            if report_type == "Resumo Mensal":
                st.markdown(f"## Relatório Mensal TG-142 - {report_month.strftime('%B/%Y')}")

                # Buscar dados do mês
                start = datetime(report_month.year, report_month.month, 1)
                if report_month.month == 12:
                    end = datetime(report_month.year + 1, 1, 1)
                else:
                    end = datetime(report_month.year, report_month.month + 1, 1)

                daily = db.get_results(test_type="tg142_daily", start_date=start, end_date=end, limit=50)
                monthly = db.get_results(test_type="tg142_monthly", start_date=start, end_date=end, limit=5)

                st.markdown("### Testes Diários")
                st.write(f"- Total realizado: {len(daily)}")
                st.write(f"- Aprovados: {sum(1 for d in daily if d['passed'])}")
                st.write(f"- Reprovados: {sum(1 for d in daily if not d['passed'])}")

                st.markdown("### Teste Mensal")
                if monthly:
                    st.write(f"- Realizado em: {monthly[0]['test_date'][:10]}")
                    st.write(f"- Status: {'Aprovado' if monthly[0]['passed'] else 'Reprovado'}")
                else:
                    st.warning("Teste mensal não realizado neste mês!")

            elif report_type == "Resumo Anual":
                st.markdown(f"## Relatório Anual TG-142 - {report_year}")

                start = datetime(report_year, 1, 1)
                end = datetime(report_year + 1, 1, 1)

                daily = db.get_results(test_type="tg142_daily", start_date=start, end_date=end, limit=400)
                monthly = db.get_results(test_type="tg142_monthly", start_date=start, end_date=end, limit=15)
                annual = db.get_results(test_type="tg142_annual", start_date=start, end_date=end, limit=3)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("### Diários")
                    st.metric("Realizados", len(daily))
                    st.metric("Aprovados", sum(1 for d in daily if d['passed']))

                with col2:
                    st.markdown("### Mensais")
                    st.metric("Realizados", len(monthly))
                    st.metric("Aprovados", sum(1 for d in monthly if d['passed']))

                with col3:
                    st.markdown("### Anual")
                    st.metric("Realizado", "Sim" if annual else "Não")
                    if annual:
                        st.metric("Status", "Aprovado" if annual[0]['passed'] else "Reprovado")

            else:  # Conformidade
                st.markdown("## Relatório de Conformidade TG-142")

                # Calcular métricas de conformidade
                today = datetime.now()
                year_start = datetime(today.year, 1, 1)

                daily = db.get_results(test_type="tg142_daily", start_date=year_start, limit=400)
                monthly = db.get_results(test_type="tg142_monthly", start_date=year_start, limit=15)
                annual = db.get_results(test_type="tg142_annual", start_date=year_start, limit=3)

                # Dias úteis esperados (aproximado)
                days_in_year = (today - year_start).days
                expected_daily = days_in_year  # Assumindo operação diária

                st.markdown("### Taxa de Conformidade")

                col1, col2, col3 = st.columns(3)

                with col1:
                    daily_rate = (len(daily) / expected_daily * 100) if expected_daily > 0 else 0
                    st.metric("Diário", f"{daily_rate:.0f}%")

                with col2:
                    months_passed = today.month
                    monthly_rate = (len(monthly) / months_passed * 100) if months_passed > 0 else 0
                    st.metric("Mensal", f"{monthly_rate:.0f}%")

                with col3:
                    annual_rate = 100 if annual else 0
                    st.metric("Anual", f"{annual_rate:.0f}%")

    else:
        st.warning("Banco de dados não disponível.")
