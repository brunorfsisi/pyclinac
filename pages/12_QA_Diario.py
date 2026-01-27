"""
QA Diário e Semanal - Baseado no TG-142
Testes de rotina para aceleradores lineares
"""

import streamlit as st
from datetime import datetime, date
from pathlib import Path
import json
import numpy as np

st.set_page_config(page_title="QA Diário", page_icon="📅", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info

create_sidebar_info(
    module_name="📅 QA Diário/Semanal",
    description="""
    Testes de rotina baseados no AAPM TG-142.

    **Testes Diários:**
    - Constância de output (dose)
    - Lasers de alinhamento
    - Indicadores de distância
    - Coincidência luz/radiação
    - Portas de segurança

    **Testes Semanais:**
    - Backup de monitor
    - Energia do feixe
    - Indicadores de ângulo
    """,
    references=[
        ("AAPM TG-142", "https://www.aapm.org/pubs/reports/detail.asp?docid=104")
    ]
)

st.title("📅 QA Diário e Semanal")
st.markdown("### Controle de Qualidade de Rotina - AAPM TG-142")

# Tabs para diferentes frequências
tab1, tab2, tab3 = st.tabs(["🌅 Diário", "📆 Semanal", "📊 Histórico"])

# =============================================================================
# CONFIGURAÇÕES COMUNS
# =============================================================================
col1, col2, col3 = st.columns(3)

with col1:
    test_date = st.date_input("Data do Teste", value=date.today())

with col2:
    if DB_AVAILABLE:
        db = get_database()
        machines = db.get_machines()
        machine_names = [m['name'] for m in machines] if machines else ["Não cadastrada"]
        machine = st.selectbox("Máquina", options=machine_names)
    else:
        machine = st.text_input("Máquina", value="Clinac iX")

with col3:
    operator = st.text_input("Operador", value="")

st.divider()

# =============================================================================
# TAB 1: QA DIÁRIO
# =============================================================================
with tab1:
    st.subheader("🌅 Checklist Diário - TG-142")

    st.markdown("""
    Complete todos os itens abaixo antes do início dos tratamentos.
    Tolerâncias baseadas no AAPM TG-142.
    """)

    # Seção 1: Dosimetria
    st.markdown("#### 1. Dosimetria")

    col1, col2 = st.columns(2)

    with col1:
        # Constância de Output X-ray
        st.markdown("**Constância de Output - Fótons**")
        baseline_photon = st.number_input(
            "Valor de Referência (cGy)",
            value=100.0,
            step=0.1,
            key="baseline_photon"
        )
        measured_photon = st.number_input(
            "Valor Medido (cGy)",
            value=100.0,
            step=0.1,
            key="measured_photon"
        )

        if baseline_photon > 0:
            diff_photon = ((measured_photon - baseline_photon) / baseline_photon) * 100
            tolerance_photon = 3.0  # TG-142: ±3%

            if abs(diff_photon) <= tolerance_photon:
                st.success(f"✅ Diferença: {diff_photon:+.2f}% (Tolerância: ±{tolerance_photon}%)")
                photon_pass = True
            else:
                st.error(f"❌ Diferença: {diff_photon:+.2f}% (Tolerância: ±{tolerance_photon}%)")
                photon_pass = False

    with col2:
        # Constância de Output Elétrons
        st.markdown("**Constância de Output - Elétrons**")
        baseline_electron = st.number_input(
            "Valor de Referência (cGy)",
            value=100.0,
            step=0.1,
            key="baseline_electron"
        )
        measured_electron = st.number_input(
            "Valor Medido (cGy)",
            value=100.0,
            step=0.1,
            key="measured_electron"
        )

        if baseline_electron > 0:
            diff_electron = ((measured_electron - baseline_electron) / baseline_electron) * 100
            tolerance_electron = 3.0  # TG-142: ±3%

            if abs(diff_electron) <= tolerance_electron:
                st.success(f"✅ Diferença: {diff_electron:+.2f}% (Tolerância: ±{tolerance_electron}%)")
                electron_pass = True
            else:
                st.error(f"❌ Diferença: {diff_electron:+.2f}% (Tolerância: ±{tolerance_electron}%)")
                electron_pass = False

    st.divider()

    # Seção 2: Mecânica
    st.markdown("#### 2. Verificações Mecânicas")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Lasers de Alinhamento**")
        laser_lateral = st.checkbox("Laser Lateral OK", key="laser_lat")
        laser_sagital = st.checkbox("Laser Sagital OK", key="laser_sag")
        laser_teto = st.checkbox("Laser de Teto OK", key="laser_teto")

        laser_tolerance = 2.0  # mm
        laser_deviation = st.number_input(
            f"Maior desvio observado (mm) - Tol: ±{laser_tolerance}mm",
            value=0.0,
            step=0.1,
            key="laser_dev"
        )
        laser_pass = abs(laser_deviation) <= laser_tolerance and laser_lateral and laser_sagital and laser_teto

        if laser_pass:
            st.success("✅ Lasers dentro da tolerância")
        else:
            st.error("❌ Verificar alinhamento dos lasers")

    with col2:
        st.markdown("**Indicadores de Distância**")
        odi_baseline = st.number_input("ODI Referência (cm)", value=100.0, step=0.1, key="odi_ref")
        odi_measured = st.number_input("ODI Medido (cm)", value=100.0, step=0.1, key="odi_meas")

        odi_tolerance = 0.2  # cm = 2mm
        odi_diff = abs(odi_measured - odi_baseline)
        odi_pass = odi_diff <= odi_tolerance

        if odi_pass:
            st.success(f"✅ Diferença: {odi_diff:.1f} cm (Tol: ±{odi_tolerance} cm)")
        else:
            st.error(f"❌ Diferença: {odi_diff:.1f} cm (Tol: ±{odi_tolerance} cm)")

    with col3:
        st.markdown("**Coincidência Luz/Radiação**")
        light_rad_tolerance = 2.0  # mm
        light_rad_diff = st.number_input(
            f"Maior diferença (mm) - Tol: ±{light_rad_tolerance}mm",
            value=0.0,
            step=0.1,
            key="light_rad"
        )
        light_rad_pass = abs(light_rad_diff) <= light_rad_tolerance

        if light_rad_pass:
            st.success("✅ Coincidência OK")
        else:
            st.error("❌ Verificar campo de luz")

    st.divider()

    # Seção 3: Segurança
    st.markdown("#### 3. Verificações de Segurança")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Portas e Interlocks**")
        door_interlock = st.checkbox("Interlock de porta funcionando", key="door")
        emergency_off = st.checkbox("Botão de emergência testado", key="emerg")
        audio_visual = st.checkbox("Alarmes audiovisuais OK", key="av")

        safety_pass = door_interlock and emergency_off and audio_visual

        if safety_pass:
            st.success("✅ Sistemas de segurança OK")
        else:
            st.error("❌ VERIFICAR SISTEMAS DE SEGURANÇA!")

    with col2:
        st.markdown("**Monitores de Radiação**")
        room_monitor = st.checkbox("Monitor de área funcionando", key="room_mon")
        personal_dosimeter = st.checkbox("Dosímetros pessoais verificados", key="pers_dos")

        monitor_pass = room_monitor and personal_dosimeter

        if monitor_pass:
            st.success("✅ Monitores OK")
        else:
            st.warning("⚠️ Verificar monitores de radiação")

    with col3:
        st.markdown("**Outros**")
        cctv_ok = st.checkbox("CCTV funcionando", key="cctv")
        intercom_ok = st.checkbox("Intercomunicador OK", key="intercom")

        other_pass = cctv_ok and intercom_ok

        if other_pass:
            st.success("✅ Sistemas auxiliares OK")
        else:
            st.warning("⚠️ Verificar sistemas auxiliares")

    st.divider()

    # Resumo e salvamento
    st.markdown("#### Resumo do QA Diário")

    all_checks = {
        "Output Fótons": photon_pass if 'photon_pass' in dir() else False,
        "Output Elétrons": electron_pass if 'electron_pass' in dir() else False,
        "Lasers": laser_pass if 'laser_pass' in dir() else False,
        "ODI": odi_pass if 'odi_pass' in dir() else False,
        "Luz/Radiação": light_rad_pass if 'light_rad_pass' in dir() else False,
        "Segurança": safety_pass if 'safety_pass' in dir() else False,
        "Monitores": monitor_pass if 'monitor_pass' in dir() else False,
        "Sistemas Aux": other_pass if 'other_pass' in dir() else False,
    }

    passed_count = sum(all_checks.values())
    total_count = len(all_checks)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Aprovados", f"{passed_count}/{total_count}")

    with col2:
        pass_rate = (passed_count / total_count) * 100
        st.metric("Taxa de Aprovação", f"{pass_rate:.0f}%")

    with col3:
        overall_status = "APROVADO" if passed_count == total_count else "REPROVADO"
        if overall_status == "APROVADO":
            st.success(f"Status: {overall_status}")
        else:
            st.error(f"Status: {overall_status}")

    with col4:
        if st.button("📷 Capturar Imagem", key="capture_daily"):
            st.info("Funcionalidade para anexar foto/screenshot do setup")

    # Observações
    daily_notes = st.text_area(
        "Observações",
        placeholder="Registre qualquer observação relevante...",
        key="daily_notes"
    )

    # Salvar resultados
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Salvar QA Diário", type="primary", key="save_daily"):
            if DB_AVAILABLE and operator:
                results = {
                    "checks": all_checks,
                    "measurements": {
                        "photon_output": {"baseline": baseline_photon, "measured": measured_photon, "diff_percent": diff_photon if 'diff_photon' in dir() else 0},
                        "electron_output": {"baseline": baseline_electron, "measured": measured_electron, "diff_percent": diff_electron if 'diff_electron' in dir() else 0},
                        "laser_deviation_mm": laser_deviation,
                        "odi_diff_cm": odi_diff if 'odi_diff' in dir() else 0,
                        "light_rad_diff_mm": light_rad_diff,
                    },
                    "notes": daily_notes
                }

                db.save_result(
                    test_type="daily_qa",
                    results=results,
                    machine_name=machine,
                    performed_by=operator,
                    passed=(passed_count == total_count),
                    notes=daily_notes,
                    test_date=datetime.combine(test_date, datetime.min.time())
                )
                st.success("✅ QA Diário salvo com sucesso!")
                st.balloons()
            elif not operator:
                st.warning("Por favor, informe o nome do operador.")
            else:
                st.warning("Banco de dados não disponível.")

    with col2:
        if st.button("📄 Gerar Relatório PDF", key="pdf_daily"):
            st.info("Gerando relatório PDF...")

# =============================================================================
# TAB 2: QA SEMANAL
# =============================================================================
with tab2:
    st.subheader("📆 Checklist Semanal - TG-142")

    st.markdown("""
    Testes semanais complementares ao QA diário.
    """)

    # Seção 1: Backup de Monitor
    st.markdown("#### 1. Sistema de Backup de Monitor")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Teste de Trip do Monitor 2**")
        mu_set = st.number_input("MU Programadas", value=100, step=1, key="mu_set")
        mu_delivered = st.number_input("MU Entregues (antes do trip)", value=100, step=1, key="mu_del")

        backup_tolerance = 2.0  # MU ou %
        backup_diff = abs(mu_delivered - mu_set)
        backup_pass = backup_diff <= backup_tolerance

        if backup_pass:
            st.success(f"✅ Diferença: {backup_diff:.1f} MU (Tol: ±{backup_tolerance} MU)")
        else:
            st.error(f"❌ Diferença: {backup_diff:.1f} MU (Tol: ±{backup_tolerance} MU)")

    with col2:
        st.markdown("**Linearidade do Monitor**")
        linearity_ok = st.checkbox("Linearidade verificada (10-400 MU)", key="linearity")

        if linearity_ok:
            st.success("✅ Linearidade OK")
        else:
            st.warning("⚠️ Verificar linearidade")

    st.divider()

    # Seção 2: Verificação de Energia
    st.markdown("#### 2. Verificação de Energia do Feixe")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Fótons - PDD ou TMR**")
        energy_photon = st.selectbox(
            "Energia",
            ["6 MV", "10 MV", "15 MV", "6 MV FFF", "10 MV FFF"],
            key="energy_photon"
        )
        pdd_baseline = st.number_input("PDD(10) Referência (%)", value=67.0, step=0.1, key="pdd_ref")
        pdd_measured = st.number_input("PDD(10) Medido (%)", value=67.0, step=0.1, key="pdd_meas")

        pdd_tolerance = 1.0  # %
        pdd_diff = abs(pdd_measured - pdd_baseline)
        pdd_pass = pdd_diff <= pdd_tolerance

        if pdd_pass:
            st.success(f"✅ Diferença: {pdd_diff:.2f}% (Tol: ±{pdd_tolerance}%)")
        else:
            st.error(f"❌ Diferença: {pdd_diff:.2f}% (Tol: ±{pdd_tolerance}%)")

    with col2:
        st.markdown("**Elétrons - R50 ou PDD**")
        energy_electron = st.selectbox(
            "Energia",
            ["6 MeV", "9 MeV", "12 MeV", "15 MeV", "18 MeV", "20 MeV"],
            key="energy_electron"
        )
        r50_baseline = st.number_input("R50 Referência (cm)", value=2.5, step=0.1, key="r50_ref")
        r50_measured = st.number_input("R50 Medido (cm)", value=2.5, step=0.1, key="r50_meas")

        r50_tolerance = 0.2  # cm = 2mm
        r50_diff = abs(r50_measured - r50_baseline)
        r50_pass = r50_diff <= r50_tolerance

        if r50_pass:
            st.success(f"✅ Diferença: {r50_diff:.2f} cm (Tol: ±{r50_tolerance} cm)")
        else:
            st.error(f"❌ Diferença: {r50_diff:.2f} cm (Tol: ±{r50_tolerance} cm)")

    st.divider()

    # Seção 3: Indicadores de Ângulo
    st.markdown("#### 3. Indicadores de Ângulo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Gantry**")
        gantry_angles = [0, 90, 180, 270]
        gantry_results = []

        for angle in gantry_angles:
            measured = st.number_input(
                f"Ângulo {angle}° - Medido",
                value=float(angle),
                step=0.1,
                key=f"gantry_{angle}"
            )
            gantry_results.append(abs(measured - angle))

        gantry_tolerance = 1.0  # grau
        gantry_pass = all(d <= gantry_tolerance for d in gantry_results)

        if gantry_pass:
            st.success(f"✅ Máx desvio: {max(gantry_results):.2f}° (Tol: ±{gantry_tolerance}°)")
        else:
            st.error(f"❌ Máx desvio: {max(gantry_results):.2f}° (Tol: ±{gantry_tolerance}°)")

    with col2:
        st.markdown("**Colimador**")
        coll_angles = [0, 90, 180, 270]
        coll_results = []

        for angle in coll_angles:
            measured = st.number_input(
                f"Ângulo {angle}° - Medido",
                value=float(angle),
                step=0.1,
                key=f"coll_{angle}"
            )
            coll_results.append(abs(measured - angle))

        coll_tolerance = 1.0  # grau
        coll_pass = all(d <= coll_tolerance for d in coll_results)

        if coll_pass:
            st.success(f"✅ Máx desvio: {max(coll_results):.2f}° (Tol: ±{coll_tolerance}°)")
        else:
            st.error(f"❌ Máx desvio: {max(coll_results):.2f}° (Tol: ±{coll_tolerance}°)")

    with col3:
        st.markdown("**Mesa**")
        couch_angles = [0, 90, 270]
        couch_results = []

        for angle in couch_angles:
            measured = st.number_input(
                f"Ângulo {angle}° - Medido",
                value=float(angle),
                step=0.1,
                key=f"couch_{angle}"
            )
            couch_results.append(abs(measured - angle))

        couch_tolerance = 1.0  # grau
        couch_pass = all(d <= couch_tolerance for d in couch_results)

        if couch_pass:
            st.success(f"✅ Máx desvio: {max(couch_results):.2f}° (Tol: ±{couch_tolerance}°)")
        else:
            st.error(f"❌ Máx desvio: {max(couch_results):.2f}° (Tol: ±{couch_tolerance}°)")

    st.divider()

    # Seção 4: Tamanho de Campo
    st.markdown("#### 4. Tamanho de Campo")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Jaws - Campo 10x10**")
        jaw_x_set = st.number_input("X Programado (cm)", value=10.0, step=0.1, key="jaw_x_set")
        jaw_x_meas = st.number_input("X Medido (cm)", value=10.0, step=0.1, key="jaw_x_meas")
        jaw_y_set = st.number_input("Y Programado (cm)", value=10.0, step=0.1, key="jaw_y_set")
        jaw_y_meas = st.number_input("Y Medido (cm)", value=10.0, step=0.1, key="jaw_y_meas")

        jaw_tolerance = 0.2  # cm = 2mm
        jaw_x_diff = abs(jaw_x_meas - jaw_x_set)
        jaw_y_diff = abs(jaw_y_meas - jaw_y_set)
        jaw_pass = jaw_x_diff <= jaw_tolerance and jaw_y_diff <= jaw_tolerance

        if jaw_pass:
            st.success(f"✅ Dif X: {jaw_x_diff:.2f} cm, Y: {jaw_y_diff:.2f} cm (Tol: ±{jaw_tolerance} cm)")
        else:
            st.error(f"❌ Dif X: {jaw_x_diff:.2f} cm, Y: {jaw_y_diff:.2f} cm (Tol: ±{jaw_tolerance} cm)")

    with col2:
        st.markdown("**Aplicador de Elétrons**")
        applicator_size = st.selectbox(
            "Tamanho do Aplicador",
            ["6x6", "10x10", "15x15", "20x20", "25x25"],
            key="applicator"
        )
        applicator_ok = st.checkbox("Campo coincidente com aplicador", key="app_ok")

        if applicator_ok:
            st.success("✅ Aplicador OK")
        else:
            st.warning("⚠️ Verificar aplicador")

    st.divider()

    # Resumo Semanal
    st.markdown("#### Resumo do QA Semanal")

    weekly_checks = {
        "Backup Monitor": backup_pass if 'backup_pass' in dir() else False,
        "PDD Fótons": pdd_pass if 'pdd_pass' in dir() else False,
        "R50 Elétrons": r50_pass if 'r50_pass' in dir() else False,
        "Gantry": gantry_pass if 'gantry_pass' in dir() else False,
        "Colimador": coll_pass if 'coll_pass' in dir() else False,
        "Mesa": couch_pass if 'couch_pass' in dir() else False,
        "Jaws": jaw_pass if 'jaw_pass' in dir() else False,
    }

    weekly_passed = sum(weekly_checks.values())
    weekly_total = len(weekly_checks)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Aprovados", f"{weekly_passed}/{weekly_total}")

    with col2:
        weekly_rate = (weekly_passed / weekly_total) * 100
        st.metric("Taxa de Aprovação", f"{weekly_rate:.0f}%")

    with col3:
        weekly_status = "APROVADO" if weekly_passed == weekly_total else "REPROVADO"
        if weekly_status == "APROVADO":
            st.success(f"Status: {weekly_status}")
        else:
            st.error(f"Status: {weekly_status}")

    weekly_notes = st.text_area(
        "Observações",
        placeholder="Registre observações do QA semanal...",
        key="weekly_notes"
    )

    if st.button("💾 Salvar QA Semanal", type="primary", key="save_weekly"):
        if DB_AVAILABLE and operator:
            results = {
                "checks": weekly_checks,
                "measurements": {
                    "backup_monitor": {"set": mu_set, "delivered": mu_delivered},
                    "pdd": {"baseline": pdd_baseline, "measured": pdd_measured, "energy": energy_photon},
                    "r50": {"baseline": r50_baseline, "measured": r50_measured, "energy": energy_electron},
                    "gantry_deviations": gantry_results,
                    "coll_deviations": coll_results,
                    "couch_deviations": couch_results,
                    "jaw_x": {"set": jaw_x_set, "measured": jaw_x_meas},
                    "jaw_y": {"set": jaw_y_set, "measured": jaw_y_meas},
                },
                "notes": weekly_notes
            }

            db.save_result(
                test_type="weekly_qa",
                results=results,
                machine_name=machine,
                performed_by=operator,
                passed=(weekly_passed == weekly_total),
                notes=weekly_notes,
                test_date=datetime.combine(test_date, datetime.min.time())
            )
            st.success("✅ QA Semanal salvo com sucesso!")
        elif not operator:
            st.warning("Por favor, informe o nome do operador.")
        else:
            st.warning("Banco de dados não disponível.")

# =============================================================================
# TAB 3: HISTÓRICO
# =============================================================================
with tab3:
    st.subheader("📊 Histórico de QA Diário/Semanal")

    if DB_AVAILABLE:
        col1, col2 = st.columns(2)

        with col1:
            qa_type = st.selectbox(
                "Tipo de QA",
                ["daily_qa", "weekly_qa"],
                format_func=lambda x: "Diário" if x == "daily_qa" else "Semanal"
            )

        with col2:
            period = st.selectbox(
                "Período",
                [7, 14, 30, 60, 90],
                format_func=lambda x: f"Últimos {x} dias"
            )

        # Buscar resultados
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=period)
        results = db.get_results(
            test_type=qa_type,
            start_date=start_date,
            limit=100
        )

        if results:
            # Tabela de resultados
            table_data = []
            for r in results:
                table_data.append({
                    "Data": r['test_date'][:10] if r['test_date'] else "N/A",
                    "Máquina": r['machine_name'] or "N/A",
                    "Operador": r['performed_by'] or "N/A",
                    "Status": "✅ Aprovado" if r['passed'] else "❌ Reprovado",
                })

            st.dataframe(table_data, use_container_width=True, hide_index=True)

            # Gráfico de tendência
            st.markdown("#### Tendência de Aprovação")

            import matplotlib.pyplot as plt

            dates = [r['test_date'][:10] for r in results]
            passed = [1 if r['passed'] else 0 for r in results]

            fig, ax = plt.subplots(figsize=(12, 4))
            ax.bar(range(len(dates)), passed, color=['green' if p else 'red' for p in passed])
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=45, ha='right')
            ax.set_ylabel('Aprovado (1) / Reprovado (0)')
            ax.set_title(f'Histórico de QA {"Diário" if qa_type == "daily_qa" else "Semanal"}')
            ax.set_ylim(-0.1, 1.1)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # Estatísticas
            total = len(results)
            approved = sum(1 for r in results if r['passed'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Testes", total)
            with col2:
                st.metric("Aprovados", approved)
            with col3:
                st.metric("Taxa de Aprovação", f"{(approved/total*100):.1f}%" if total > 0 else "N/A")
        else:
            st.info("Nenhum resultado encontrado no período selecionado.")
    else:
        st.warning("⚠️ Banco de dados não disponível.")
