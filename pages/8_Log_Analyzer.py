"""
Módulo Log Analyzer - Análise de Dynalogs e Trajectory Logs
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Log Analyzer", page_icon="📁", layout="wide")

# Importações do pylinac
try:
    from pylinac.log_analyzer import load_log, Dynalog, TrajectoryLog, MachineLogs
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

# Adiciona path do utils
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, save_uploaded_files, extract_zip_to_temp,
    cleanup_temp_files, get_pdf_download_button, create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="📁 Log Analyzer",
    description="""
    Análise de arquivos de log de aceleradores Varian:
    - Dynalogs (.dlg): Logs de posição de MLC
    - Trajectory Logs (.bin): Logs completos de trajetória
    """,
    references=[
        "Varian Medical Systems Dynalog File Reference Guide",
        "AAPM TG-142: Quality assurance of medical accelerators"
    ]
)

st.title("📁 Análise de Logs de Máquina")
st.markdown("""
Análise de arquivos Dynalog e Trajectory Log de aceleradores Varian.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Tabs para diferentes tipos de análise
tab1, tab2, tab3 = st.tabs(["📄 Log Único", "📁 Múltiplos Logs", "📊 Análise de Fluência"])

# =============================================================================
# TAB 1 - LOG ÚNICO
# =============================================================================
with tab1:
    st.subheader("Análise de Log Único")
    st.markdown("""
    Faça upload de um arquivo Dynalog (.dlg) ou Trajectory Log (.bin) para análise detalhada.
    """)

    uploaded_file = st.file_uploader(
        "Selecione o arquivo de log",
        type=['dlg', 'bin'],
        key="single_log",
        help="Dynalog (.dlg) ou Trajectory Log (.bin)"
    )

    # Parâmetros de análise
    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            tolerance = st.number_input(
                "Tolerância de posição (mm)",
                min_value=0.1,
                max_value=5.0,
                value=0.5,
                step=0.1,
                help="Tolerância para erro de posição de MLC"
            )

        with col2:
            resolution = st.number_input(
                "Resolução de fluência (mm)",
                min_value=0.1,
                max_value=2.0,
                value=0.1,
                step=0.1,
                help="Resolução para cálculo de fluência"
            )

    if uploaded_file is not None:
        if st.button("🔬 Analisar Log", key="analyze_single", type="primary"):
            temp_path = save_uploaded_file(uploaded_file)

            try:
                with st.spinner("Analisando arquivo de log..."):
                    log = load_log(temp_path)

                st.success("✅ Log carregado com sucesso!")

                # Informações básicas
                st.subheader("📊 Informações do Log")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Tipo de Log", log.__class__.__name__)
                    if hasattr(log, 'header'):
                        if hasattr(log.header, 'patient_name'):
                            st.metric("Paciente", log.header.patient_name or "N/A")

                with col2:
                    if hasattr(log, 'header'):
                        if hasattr(log.header, 'treatment_datetime'):
                            st.metric("Data/Hora", str(log.header.treatment_datetime) or "N/A")
                        if hasattr(log.header, 'tolerance'):
                            st.metric("Tolerância do Log", f"{log.header.tolerance:.2f} mm")

                with col3:
                    if hasattr(log, 'num_beamholds'):
                        st.metric("Beam Holds", log.num_beamholds)
                    if hasattr(log, 'num_snapshots'):
                        st.metric("Snapshots", log.num_snapshots)

                # Análise de MLC
                st.subheader("📈 Análise de Posição do MLC")

                if hasattr(log, 'axis_data'):
                    # Estatísticas de erro
                    mlc_data = log.axis_data.mlc

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if hasattr(mlc_data, 'get_error_percentile'):
                            st.metric(
                                "Erro Máximo",
                                f"{mlc_data.get_error_percentile(100):.3f} mm"
                            )

                    with col2:
                        if hasattr(mlc_data, 'get_error_percentile'):
                            st.metric(
                                "Erro P95",
                                f"{mlc_data.get_error_percentile(95):.3f} mm"
                            )

                    with col3:
                        if hasattr(mlc_data, 'get_error_percentile'):
                            st.metric(
                                "Erro P50 (Mediana)",
                                f"{mlc_data.get_error_percentile(50):.3f} mm"
                            )

                    with col4:
                        if hasattr(mlc_data, 'num_leaves'):
                            st.metric(
                                "Número de Lâminas",
                                mlc_data.num_leaves
                            )

                # Gráficos
                st.subheader("🖼️ Visualizações")

                # Plot de erro de MLC
                with st.expander("📊 Erro de Posição do MLC", expanded=True):
                    try:
                        fig_mlc, ax_mlc = plt.subplots(figsize=(12, 6))

                        if hasattr(log.axis_data.mlc, 'plot_error'):
                            log.axis_data.mlc.plot_error(ax=ax_mlc)
                        else:
                            ax_mlc.text(0.5, 0.5, 'Gráfico não disponível para este tipo de log',
                                      ha='center', va='center', transform=ax_mlc.transAxes)

                        ax_mlc.set_title('Erro de Posição do MLC ao Longo do Tempo')
                        st.pyplot(fig_mlc)
                        plt.close(fig_mlc)
                    except Exception as e:
                        st.warning(f"Não foi possível gerar o gráfico de erro: {str(e)}")

                # Gantry e outros eixos
                with st.expander("📊 Outros Eixos"):
                    if hasattr(log.axis_data, 'gantry'):
                        try:
                            fig_gantry, ax_gantry = plt.subplots(figsize=(10, 4))
                            ax_gantry.plot(log.axis_data.gantry.actual, label='Atual')
                            ax_gantry.plot(log.axis_data.gantry.expected, label='Esperado', linestyle='--')
                            ax_gantry.set_xlabel('Snapshot')
                            ax_gantry.set_ylabel('Ângulo (°)')
                            ax_gantry.set_title('Posição do Gantry')
                            ax_gantry.legend()
                            st.pyplot(fig_gantry)
                            plt.close(fig_gantry)
                        except Exception:
                            st.info("Dados de gantry não disponíveis.")

                    if hasattr(log.axis_data, 'collimator'):
                        try:
                            fig_coll, ax_coll = plt.subplots(figsize=(10, 4))
                            ax_coll.plot(log.axis_data.collimator.actual, label='Atual')
                            ax_coll.plot(log.axis_data.collimator.expected, label='Esperado', linestyle='--')
                            ax_coll.set_xlabel('Snapshot')
                            ax_coll.set_ylabel('Ângulo (°)')
                            ax_coll.set_title('Posição do Colimador')
                            ax_coll.legend()
                            st.pyplot(fig_coll)
                            plt.close(fig_coll)
                        except Exception:
                            st.info("Dados de colimador não disponíveis.")

                # Histograma de erros
                with st.expander("📊 Histograma de Erros"):
                    try:
                        if hasattr(log.axis_data.mlc, 'leaf_moved'):
                            errors = []
                            for leaf in log.axis_data.mlc.leaf_axes.values():
                                if hasattr(leaf, 'difference'):
                                    errors.extend(leaf.difference.tolist())

                            if errors:
                                fig_hist, ax_hist = plt.subplots(figsize=(10, 5))
                                ax_hist.hist(errors, bins=50, edgecolor='black', alpha=0.7)
                                ax_hist.axvline(x=tolerance, color='r', linestyle='--', label=f'Tolerância ({tolerance} mm)')
                                ax_hist.axvline(x=-tolerance, color='r', linestyle='--')
                                ax_hist.set_xlabel('Erro (mm)')
                                ax_hist.set_ylabel('Frequência')
                                ax_hist.set_title('Distribuição de Erros de Posição do MLC')
                                ax_hist.legend()
                                st.pyplot(fig_hist)
                                plt.close(fig_hist)
                    except Exception as e:
                        st.warning(f"Não foi possível gerar histograma: {str(e)}")

                # Relatório PDF
                st.subheader("📄 Relatório")
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                        log.publish_pdf(tmp_pdf.name)
                        get_pdf_download_button(tmp_pdf.name, "log_analysis_report.pdf")
                        os.unlink(tmp_pdf.name)
                except Exception as e:
                    st.warning(f"Não foi possível gerar PDF: {str(e)}")

            except Exception as e:
                st.error(f"❌ Erro ao analisar log: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files([temp_path])

# =============================================================================
# TAB 2 - MÚLTIPLOS LOGS
# =============================================================================
with tab2:
    st.subheader("Análise de Múltiplos Logs")
    st.markdown("""
    Faça upload de múltiplos arquivos de log ou um diretório compactado
    para análise estatística agregada.
    """)

    upload_method = st.radio(
        "Método de upload:",
        ["Múltiplos arquivos", "Arquivo ZIP"],
        horizontal=True,
        key="multi_method"
    )

    if upload_method == "Múltiplos arquivos":
        uploaded_files = st.file_uploader(
            "Selecione os arquivos de log",
            type=['dlg', 'bin'],
            accept_multiple_files=True,
            key="multi_logs"
        )
    else:
        uploaded_files = st.file_uploader(
            "Selecione o arquivo ZIP",
            type=['zip'],
            key="zip_logs"
        )

    if uploaded_files:
        if st.button("🔬 Analisar Logs", key="analyze_multi", type="primary"):
            temp_paths = []

            try:
                with st.spinner("Processando logs..."):
                    if upload_method == "Arquivo ZIP":
                        temp_dir = extract_zip_to_temp(uploaded_files)
                        temp_paths.append(temp_dir)
                        machine_logs = MachineLogs(temp_dir)
                    else:
                        temp_dir = tempfile.mkdtemp()
                        temp_paths.append(temp_dir)
                        for uf in uploaded_files:
                            file_path = os.path.join(temp_dir, uf.name)
                            with open(file_path, 'wb') as f:
                                f.write(uf.getvalue())
                        machine_logs = MachineLogs(temp_dir)

                st.success(f"✅ {len(machine_logs)} logs carregados!")

                # Estatísticas agregadas
                st.subheader("📊 Estatísticas Agregadas")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total de Logs", len(machine_logs))

                with col2:
                    if hasattr(machine_logs, 'num_logs_with_gamma_issues'):
                        st.metric("Logs com Problemas", machine_logs.num_logs_with_gamma_issues())

                with col3:
                    if hasattr(machine_logs, 'avg_gamma'):
                        st.metric("Gamma Médio", f"{machine_logs.avg_gamma():.3f}")

                # Tabela de resumo
                st.subheader("📋 Resumo dos Logs")

                log_summary = []
                for log in machine_logs:
                    try:
                        summary = {
                            "Arquivo": Path(log.path).name if hasattr(log, 'path') else "N/A",
                            "Tipo": log.__class__.__name__,
                        }

                        if hasattr(log, 'axis_data') and hasattr(log.axis_data, 'mlc'):
                            mlc = log.axis_data.mlc
                            if hasattr(mlc, 'get_error_percentile'):
                                summary["Erro Máx (mm)"] = f"{mlc.get_error_percentile(100):.3f}"
                                summary["Erro P95 (mm)"] = f"{mlc.get_error_percentile(95):.3f}"

                        log_summary.append(summary)
                    except Exception:
                        continue

                if log_summary:
                    st.dataframe(log_summary, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Erro ao processar logs: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files(temp_paths)

# =============================================================================
# TAB 3 - ANÁLISE DE FLUÊNCIA
# =============================================================================
with tab3:
    st.subheader("Análise de Fluência")
    st.markdown("""
    Calcula e compara mapas de fluência planejada vs. entregue a partir de logs.
    """)

    fluence_file = st.file_uploader(
        "Selecione o arquivo de log para análise de fluência",
        type=['dlg', 'bin'],
        key="fluence_log"
    )

    if fluence_file:
        col1, col2 = st.columns(2)

        with col1:
            fluence_resolution = st.number_input(
                "Resolução (mm)",
                min_value=0.1,
                max_value=2.0,
                value=0.1,
                step=0.1,
                key="fluence_res"
            )

        with col2:
            gamma_threshold = st.number_input(
                "Limiar Gamma (%)",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5
            )

        if st.button("🔬 Calcular Fluência", key="calc_fluence", type="primary"):
            temp_path = save_uploaded_file(fluence_file)

            try:
                with st.spinner("Calculando mapas de fluência..."):
                    log = load_log(temp_path)

                    if hasattr(log, 'fluence'):
                        # Calcula fluência
                        actual_fluence = log.fluence.actual
                        expected_fluence = log.fluence.expected

                        st.success("✅ Fluência calculada!")

                        # Visualização
                        st.subheader("🖼️ Mapas de Fluência")

                        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

                        # Fluência esperada
                        im1 = axes[0].imshow(expected_fluence.array, cmap='jet')
                        axes[0].set_title('Fluência Esperada')
                        plt.colorbar(im1, ax=axes[0])

                        # Fluência atual
                        im2 = axes[1].imshow(actual_fluence.array, cmap='jet')
                        axes[1].set_title('Fluência Entregue')
                        plt.colorbar(im2, ax=axes[1])

                        # Diferença
                        diff = actual_fluence.array - expected_fluence.array
                        im3 = axes[2].imshow(diff, cmap='RdBu_r')
                        axes[2].set_title('Diferença')
                        plt.colorbar(im3, ax=axes[2])

                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)

                        # Estatísticas
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Diferença Máxima", f"{diff.max():.3f}")

                        with col2:
                            st.metric("Diferença Mínima", f"{diff.min():.3f}")

                        with col3:
                            st.metric("Diferença Média", f"{diff.mean():.3f}")

                    else:
                        st.warning("Este tipo de log não suporta análise de fluência.")

            except Exception as e:
                st.error(f"❌ Erro ao calcular fluência: {str(e)}")
                st.exception(e)

            finally:
                cleanup_temp_files([temp_path])

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Tipos de Logs Suportados:

    #### Dynalog (.dlg)
    - Formato antigo da Varian
    - Um arquivo por banco de MLC (A e B)
    - Contém posições de MLC em intervalos de 50 ms

    #### Trajectory Log (.bin)
    - Formato atual da Varian
    - Arquivo único com todos os dados
    - Alta resolução temporal (20 ms)
    - Inclui dados de gantry, colimador, MU, etc.

    ### Como usar:

    1. **Localize os arquivos de log**:
       - Dynalogs: Geralmente em `D:\\Dynalog\\`
       - Trajectory Logs: Em `D:\\TrajectoryLog\\`

    2. **Faça upload do arquivo**:
       - Para análise individual: upload único
       - Para análise em lote: múltiplos arquivos ou ZIP

    3. **Configure os parâmetros**:
       - Tolerância típica: 0.5 mm
       - Resolução de fluência: 0.1 mm

    4. **Interprete os resultados**:
       - Erro máximo de MLC: deve ser < tolerância
       - Beam holds: indicam interrupções de feixe
       - Fluência: compare visual e quantitativamente

    ### Tolerâncias Típicas:

    | Parâmetro | Tolerância |
    |-----------|------------|
    | Posição MLC | ≤ 0.5 mm |
    | Velocidade MLC | Por design |
    | Ângulo Gantry | ≤ 1° |
    | Taxa de Dose | ± 2% |

    ### Notas:

    - Logs de tratamento real contêm informações de paciente
    - Para análise de QA, use logs de testes dedicados
    - A análise de fluência requer logs completos (não truncados)
    """)
