"""
Configurações - Preferências e Gerenciamento do Sistema
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import json
import os

st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info

create_sidebar_info(
    module_name="⚙️ Configurações",
    description="""
    Gerenciamento de configurações e preferências do sistema.

    - Tolerâncias padrão para cada teste
    - Configurações de relatórios
    - Informações da instituição
    - Backup e exportação de dados
    """,
    references=[]
)

st.title("⚙️ Configurações do Sistema")

# Tabs para diferentes seções de configuração
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📏 Tolerâncias",
    "📄 Relatórios",
    "🏥 Instituição",
    "💾 Dados",
    "ℹ️ Sistema"
])

# =============================================================================
# TAB 1: TOLERÂNCIAS
# =============================================================================
with tab1:
    st.subheader("Tolerâncias Padrão")

    st.markdown("""
    Configure as tolerâncias padrão para cada tipo de teste de QA.
    Estes valores são usados para determinar aprovação/reprovação automática.
    """)

    if DB_AVAILABLE:
        db = get_database()
        tolerances = db.get_tolerances()

        # Agrupa por tipo de teste
        test_types = {}
        for tol in tolerances:
            tt = tol['test_type']
            if tt not in test_types:
                test_types[tt] = []
            test_types[tt].append(tol)

        # Nomes amigáveis
        test_names = {
            "winston_lutz": "Winston-Lutz",
            "picket_fence": "Picket Fence",
            "starshot": "Starshot",
            "vmat_drgs": "VMAT DRGS",
            "vmat_drmlc": "VMAT DRMLC",
            "field_analysis": "Análise de Campo",
            "catphan": "CatPhan",
            "gamma": "Análise Gamma"
        }

        for test_type, tols in test_types.items():
            with st.expander(f"📋 {test_names.get(test_type, test_type.replace('_', ' ').title())}"):
                for tol in tols:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                    with col1:
                        st.text(f"Parâmetro: {tol['parameter']}")

                    with col2:
                        new_tol = st.number_input(
                            "Tolerância",
                            value=float(tol['tolerance_value']),
                            step=0.1,
                            key=f"tol_{tol['id']}"
                        )

                    with col3:
                        new_action = st.number_input(
                            "Nível de Ação",
                            value=float(tol['action_level']) if tol['action_level'] else 0.0,
                            step=0.1,
                            key=f"action_{tol['id']}"
                        )

                    with col4:
                        st.text(f"Unidade: {tol['unit'] or 'N/A'}")

                        if st.button("💾", key=f"save_{tol['id']}", help="Salvar"):
                            db.update_tolerance(
                                tol['test_type'],
                                tol['parameter'],
                                new_tol,
                                new_action
                            )
                            st.success("✅ Salvo!")
                            st.rerun()

        st.divider()

        # Adicionar nova tolerância
        st.subheader("Adicionar Nova Tolerância")

        with st.form("add_tolerance"):
            col1, col2 = st.columns(2)

            with col1:
                new_test_type = st.selectbox(
                    "Tipo de Teste",
                    options=list(test_names.keys()),
                    format_func=lambda x: test_names.get(x, x)
                )
                new_param = st.text_input("Nome do Parâmetro", placeholder="novo_parametro")

            with col2:
                new_tol_value = st.number_input("Valor da Tolerância", value=1.0, step=0.1)
                new_action_value = st.number_input("Nível de Ação", value=0.75, step=0.1)
                new_unit = st.text_input("Unidade", placeholder="mm, %, etc.")

            if st.form_submit_button("➕ Adicionar Tolerância", type="primary"):
                if new_param:
                    cursor = db.conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO tolerances (test_type, parameter, tolerance_value, unit, action_level)
                            VALUES (?, ?, ?, ?, ?)
                        """, (new_test_type, new_param, new_tol_value, new_unit, new_action_value))
                        db.conn.commit()
                        st.success(f"✅ Tolerância '{new_param}' adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
                else:
                    st.warning("Nome do parâmetro é obrigatório.")

    else:
        st.warning("⚠️ Banco de dados não disponível. Configure o banco de dados para gerenciar tolerâncias.")

# =============================================================================
# TAB 2: RELATÓRIOS
# =============================================================================
with tab2:
    st.subheader("Configurações de Relatórios")

    st.markdown("Configure como os relatórios PDF serão gerados.")

    if DB_AVAILABLE:
        db = get_database()

        col1, col2 = st.columns(2)

        with col1:
            report_title = st.text_input(
                "Título do Relatório",
                value=db.get_setting("report_title", "Relatório de Controle de Qualidade"),
                help="Título padrão para todos os relatórios"
            )

            include_images = st.checkbox(
                "Incluir Imagens nos Relatórios",
                value=db.get_setting("include_images", "true") == "true"
            )

            include_raw_data = st.checkbox(
                "Incluir Dados Brutos",
                value=db.get_setting("include_raw_data", "false") == "true"
            )

        with col2:
            report_format = st.selectbox(
                "Formato Padrão",
                options=["PDF", "HTML", "Ambos"],
                index=["PDF", "HTML", "Ambos"].index(
                    db.get_setting("report_format", "PDF")
                )
            )

            show_tolerance_lines = st.checkbox(
                "Mostrar Linhas de Tolerância nos Gráficos",
                value=db.get_setting("show_tolerance_lines", "true") == "true"
            )

            auto_save_results = st.checkbox(
                "Salvar Resultados Automaticamente",
                value=db.get_setting("auto_save_results", "true") == "true"
            )

        st.divider()

        st.subheader("Cabeçalho do Relatório")

        header_text = st.text_area(
            "Texto do Cabeçalho",
            value=db.get_setting("report_header", "Este relatório foi gerado automaticamente pelo Sistema de QA."),
            height=100
        )

        footer_text = st.text_area(
            "Texto do Rodapé",
            value=db.get_setting("report_footer", "Documento gerado por PyClinac QA System"),
            height=100
        )

        if st.button("💾 Salvar Configurações de Relatório", type="primary"):
            db.set_setting("report_title", report_title)
            db.set_setting("include_images", "true" if include_images else "false")
            db.set_setting("include_raw_data", "true" if include_raw_data else "false")
            db.set_setting("report_format", report_format)
            db.set_setting("show_tolerance_lines", "true" if show_tolerance_lines else "false")
            db.set_setting("auto_save_results", "true" if auto_save_results else "false")
            db.set_setting("report_header", header_text)
            db.set_setting("report_footer", footer_text)
            st.success("✅ Configurações de relatório salvas!")

    else:
        st.warning("⚠️ Banco de dados não disponível.")

# =============================================================================
# TAB 3: INSTITUIÇÃO
# =============================================================================
with tab3:
    st.subheader("Informações da Instituição")

    st.markdown("Configure as informações da sua instituição para os relatórios.")

    if DB_AVAILABLE:
        db = get_database()

        col1, col2 = st.columns(2)

        with col1:
            inst_name = st.text_input(
                "Nome da Instituição",
                value=db.get_setting("institution_name", ""),
                placeholder="Hospital / Clínica"
            )

            inst_department = st.text_input(
                "Departamento",
                value=db.get_setting("institution_department", ""),
                placeholder="Serviço de Radioterapia"
            )

            inst_address = st.text_area(
                "Endereço",
                value=db.get_setting("institution_address", ""),
                placeholder="Rua, Número, Cidade - Estado",
                height=100
            )

        with col2:
            inst_phone = st.text_input(
                "Telefone",
                value=db.get_setting("institution_phone", ""),
                placeholder="(00) 0000-0000"
            )

            inst_email = st.text_input(
                "E-mail",
                value=db.get_setting("institution_email", ""),
                placeholder="contato@instituicao.com"
            )

            inst_website = st.text_input(
                "Website",
                value=db.get_setting("institution_website", ""),
                placeholder="www.instituicao.com"
            )

        st.divider()

        st.subheader("Equipe de Física Médica")

        physicist_name = st.text_input(
            "Físico Médico Responsável",
            value=db.get_setting("physicist_name", ""),
            placeholder="Dr. Nome Sobrenome"
        )

        physicist_register = st.text_input(
            "Registro Profissional",
            value=db.get_setting("physicist_register", ""),
            placeholder="CNEN / CREA / etc."
        )

        # Lista de operadores autorizados
        st.subheader("Operadores Autorizados")

        operators_json = db.get_setting("authorized_operators", "[]")
        try:
            operators = json.loads(operators_json)
        except:
            operators = []

        # Mostrar operadores existentes
        if operators:
            for i, op in enumerate(operators):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(op.get("name", "N/A"))
                with col2:
                    st.text(op.get("role", "Operador"))
                with col3:
                    if st.button("🗑️", key=f"del_op_{i}"):
                        operators.pop(i)
                        db.set_setting("authorized_operators", json.dumps(operators))
                        st.rerun()
        else:
            st.info("Nenhum operador cadastrado.")

        # Adicionar operador
        with st.expander("➕ Adicionar Operador"):
            col1, col2 = st.columns(2)
            with col1:
                new_op_name = st.text_input("Nome do Operador", key="new_op_name")
            with col2:
                new_op_role = st.selectbox(
                    "Função",
                    ["Físico Médico", "Técnico", "Dosimetrista", "Residente", "Estagiário"],
                    key="new_op_role"
                )

            if st.button("Adicionar Operador"):
                if new_op_name:
                    operators.append({"name": new_op_name, "role": new_op_role})
                    db.set_setting("authorized_operators", json.dumps(operators))
                    st.success(f"✅ Operador '{new_op_name}' adicionado!")
                    st.rerun()

        st.divider()

        if st.button("💾 Salvar Informações da Instituição", type="primary"):
            db.set_setting("institution_name", inst_name)
            db.set_setting("institution_department", inst_department)
            db.set_setting("institution_address", inst_address)
            db.set_setting("institution_phone", inst_phone)
            db.set_setting("institution_email", inst_email)
            db.set_setting("institution_website", inst_website)
            db.set_setting("physicist_name", physicist_name)
            db.set_setting("physicist_register", physicist_register)
            st.success("✅ Informações da instituição salvas!")

    else:
        st.warning("⚠️ Banco de dados não disponível.")

# =============================================================================
# TAB 4: DADOS
# =============================================================================
with tab4:
    st.subheader("Gerenciamento de Dados")

    if DB_AVAILABLE:
        db = get_database()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Estatísticas do Banco")

            cursor = db.conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM qa_results")
            total_results = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM machines")
            total_machines = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tolerances")
            total_tolerances = cursor.fetchone()[0]

            st.metric("Total de Resultados", total_results)
            st.metric("Máquinas Cadastradas", total_machines)
            st.metric("Tolerâncias Configuradas", total_tolerances)

            # Tamanho do banco
            if os.path.exists(db.db_path):
                db_size = os.path.getsize(db.db_path) / 1024  # KB
                if db_size > 1024:
                    st.metric("Tamanho do Banco", f"{db_size/1024:.2f} MB")
                else:
                    st.metric("Tamanho do Banco", f"{db_size:.2f} KB")

        with col2:
            st.markdown("### 💾 Backup e Exportação")

            # Exportar dados
            if st.button("📥 Exportar Todos os Dados (JSON)"):
                export_data = {
                    "export_date": datetime.now().isoformat(),
                    "machines": db.get_machines(),
                    "results": db.get_results(limit=10000),
                    "tolerances": db.get_tolerances()
                }

                # Converter para JSON
                json_str = json.dumps(export_data, indent=2, default=str)

                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_str,
                    file_name=f"qa_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            # Backup do banco
            if st.button("💾 Criar Backup do Banco"):
                import shutil
                backup_path = db.db_path.replace(".db", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                try:
                    shutil.copy2(db.db_path, backup_path)
                    st.success(f"✅ Backup criado: {backup_path}")
                except Exception as e:
                    st.error(f"Erro ao criar backup: {str(e)}")

        st.divider()

        st.markdown("### ⚠️ Operações Destrutivas")

        st.warning("As operações abaixo são irreversíveis. Use com cuidado!")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Limpar Resultados Antigos", type="secondary"):
                st.session_state.show_clear_old = True

        with col2:
            if st.button("🗑️ Limpar Todos os Resultados", type="secondary"):
                st.session_state.show_clear_all = True

        with col3:
            if st.button("🔄 Resetar Tolerâncias", type="secondary"):
                st.session_state.show_reset_tol = True

        # Confirmações
        if st.session_state.get("show_clear_old", False):
            with st.form("clear_old_form"):
                days = st.number_input("Remover resultados mais antigos que (dias):", min_value=30, value=365)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Confirmar"):
                        cursor = db.conn.cursor()
                        from datetime import timedelta
                        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
                        cursor.execute("DELETE FROM qa_results WHERE test_date < ?", (cutoff,))
                        deleted = cursor.rowcount
                        db.conn.commit()
                        st.success(f"✅ {deleted} resultados removidos!")
                        st.session_state.show_clear_old = False
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        st.session_state.show_clear_old = False
                        st.rerun()

        if st.session_state.get("show_clear_all", False):
            with st.form("clear_all_form"):
                st.error("⚠️ Isso removerá TODOS os resultados de QA!")
                confirm = st.text_input("Digite 'CONFIRMAR' para prosseguir:")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Confirmar"):
                        if confirm == "CONFIRMAR":
                            cursor = db.conn.cursor()
                            cursor.execute("DELETE FROM qa_results")
                            db.conn.commit()
                            st.success("✅ Todos os resultados foram removidos!")
                            st.session_state.show_clear_all = False
                            st.rerun()
                        else:
                            st.error("Confirmação incorreta.")
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        st.session_state.show_clear_all = False
                        st.rerun()

        if st.session_state.get("show_reset_tol", False):
            with st.form("reset_tol_form"):
                st.warning("Isso restaurará todas as tolerâncias para os valores padrão.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Confirmar"):
                        cursor = db.conn.cursor()
                        cursor.execute("DELETE FROM tolerances")
                        # Reinserir padrões
                        default_tolerances = [
                            ("winston_lutz", "gantry_iso_size", 1.0, "mm", 0.75),
                            ("winston_lutz", "coll_iso_size", 1.0, "mm", 0.75),
                            ("winston_lutz", "couch_iso_size", 1.0, "mm", 0.75),
                            ("picket_fence", "max_error", 0.5, "mm", 0.3),
                            ("starshot", "wobble_radius", 1.0, "mm", 0.75),
                            ("vmat_drgs", "max_deviation", 1.5, "%", 1.0),
                            ("vmat_drmlc", "max_deviation", 1.5, "%", 1.0),
                            ("field_analysis", "flatness", 3.0, "%", 2.0),
                            ("field_analysis", "symmetry", 3.0, "%", 2.0),
                            ("catphan", "hu_tolerance", 40.0, "HU", 30.0),
                            ("gamma", "passing_rate", 95.0, "%", 90.0),
                        ]
                        for tol in default_tolerances:
                            cursor.execute("""
                                INSERT INTO tolerances (test_type, parameter, tolerance_value, unit, action_level)
                                VALUES (?, ?, ?, ?, ?)
                            """, tol)
                        db.conn.commit()
                        st.success("✅ Tolerâncias restauradas!")
                        st.session_state.show_reset_tol = False
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        st.session_state.show_reset_tol = False
                        st.rerun()

    else:
        st.warning("⚠️ Banco de dados não disponível.")

# =============================================================================
# TAB 5: SISTEMA
# =============================================================================
with tab5:
    st.subheader("Informações do Sistema")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📦 Versões de Pacotes")

        import importlib

        packages = [
            ("streamlit", "Streamlit"),
            ("pylinac", "Pylinac"),
            ("pydicom", "Pydicom"),
            ("numpy", "NumPy"),
            ("matplotlib", "Matplotlib"),
            ("scipy", "SciPy"),
            ("PIL", "Pillow"),
            ("skimage", "Scikit-image"),
        ]

        versions = []
        for pkg, name in packages:
            try:
                mod = importlib.import_module(pkg)
                version = getattr(mod, "__version__", "N/A")
                versions.append({"Pacote": name, "Versão": version, "Status": "✅"})
            except ImportError:
                versions.append({"Pacote": name, "Versão": "N/A", "Status": "❌"})

        st.dataframe(versions, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("### 🐍 Informações Python")

        import platform

        st.text(f"Python: {platform.python_version()}")
        st.text(f"Sistema: {platform.system()} {platform.release()}")
        st.text(f"Arquitetura: {platform.machine()}")

        if DB_AVAILABLE:
            st.text(f"Banco de Dados: {db.db_path}")

        st.divider()

        st.markdown("### 📚 Documentação")

        st.markdown("""
        - [Pylinac Documentation](https://pylinac.readthedocs.io/)
        - [Streamlit Documentation](https://docs.streamlit.io/)
        - [AAPM TG-51](https://www.aapm.org/pubs/reports/detail.asp?docid=54)
        - [IAEA TRS-398](https://www.iaea.org/publications/5954/absorbed-dose-determination-in-external-beam-radiotherapy)
        """)

    st.divider()

    st.markdown("### 🔧 Diagnóstico do Sistema")

    if st.button("🔍 Executar Diagnóstico"):
        with st.spinner("Executando diagnóstico..."):
            issues = []

            # Verificar pylinac
            try:
                import pylinac
                st.success(f"✅ Pylinac {pylinac.__version__} instalado corretamente")
            except ImportError:
                issues.append("Pylinac não instalado")
                st.error("❌ Pylinac não encontrado")

            # Verificar DICOM
            try:
                import pydicom
                st.success(f"✅ Pydicom {pydicom.__version__} instalado corretamente")
            except ImportError:
                issues.append("Pydicom não instalado")
                st.error("❌ Pydicom não encontrado")

            # Verificar banco de dados
            if DB_AVAILABLE:
                try:
                    db = get_database()
                    cursor = db.conn.cursor()
                    cursor.execute("SELECT 1")
                    st.success("✅ Banco de dados funcionando")
                except Exception as e:
                    issues.append(f"Erro no banco: {str(e)}")
                    st.error(f"❌ Erro no banco de dados: {str(e)}")
            else:
                issues.append("Banco de dados não disponível")
                st.warning("⚠️ Banco de dados não configurado")

            # Verificar diretórios temporários
            import tempfile
            try:
                with tempfile.NamedTemporaryFile(delete=True) as f:
                    f.write(b"test")
                st.success("✅ Diretório temporário acessível")
            except Exception as e:
                issues.append(f"Erro em temporários: {str(e)}")
                st.error(f"❌ Erro no diretório temporário: {str(e)}")

            if not issues:
                st.balloons()
                st.success("🎉 Sistema funcionando perfeitamente!")
            else:
                st.warning(f"⚠️ {len(issues)} problema(s) encontrado(s)")

    st.divider()

    st.markdown("### ℹ️ Sobre")

    st.markdown("""
    **PyClinac QA System** - Sistema de Controle de Qualidade para Radioterapia

    Este sistema utiliza a biblioteca [Pylinac](https://pylinac.readthedocs.io/) para análise
    de testes de controle de qualidade em equipamentos de radioterapia.

    **Módulos Disponíveis:**
    - Winston-Lutz (incluindo Multi-Target)
    - Picket Fence
    - Starshot
    - VMAT (DRGS e DRMLC)
    - Calibração de Dose (TG-51 / TRS-398)
    - Planar Imaging (QC-3, Las Vegas, Leeds TOR)
    - CBCT (CatPhan, ACR, Quart, Cheese)
    - Log Analyzer
    - Field Analysis
    - Análise Gamma 2D

    **Desenvolvido com:**
    - Python + Streamlit
    - Pylinac + Pydicom
    - SQLite para persistência

    ---

    *Sistema desenvolvido para fins educacionais e de pesquisa.
    Sempre verifique os resultados com as ferramentas oficiais do fabricante.*
    """)
