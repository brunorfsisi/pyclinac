"""
Módulo Winston-Lutz - Análise de Isocentro
Inclui Winston-Lutz padrão, 2D e Multi-Target Multi-Field (MTWL)
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Winston-Lutz", page_icon="🎯", layout="wide")

# Importações do pylinac
try:
    from pylinac import WinstonLutz
    from pylinac.winston_lutz import WinstonLutz2D, WinstonLutzMultiTargetMultiField
    PYLINAC_AVAILABLE = True
    MTWL_AVAILABLE = True
except ImportError:
    try:
        from pylinac import WinstonLutz
        from pylinac.winston_lutz import WinstonLutz2D
        PYLINAC_AVAILABLE = True
        MTWL_AVAILABLE = False
    except ImportError:
        PYLINAC_AVAILABLE = False
        MTWL_AVAILABLE = False

# Adiciona path do utils
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, save_uploaded_files, extract_zip_to_temp,
    cleanup_temp_files, get_pdf_download_button, create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="🎯 Winston-Lutz",
    description="""
    O teste Winston-Lutz determina a precisão do isocentro do acelerador
    medindo a distância entre o centro do campo de radiação e um marcador
    BB em múltiplas posições de gantry, colimador e mesa.

    **Modos disponíveis:**
    - Análise Completa (múltiplas imagens)
    - Análise 2D (imagem única)
    - Multi-Target Multi-Field (SRS/SBRT)
    """,
    references=[
        "Lutz W, Winston KR, Maleki N. A system for stereotactic radiosurgery with a linear accelerator. Int J Radiat Oncol Biol Phys. 1988",
        "AAPM TG-142: Quality assurance of medical accelerators",
        "AAPM TG-198: An MLC-based linac QA"
    ]
)

st.title("🎯 Análise Winston-Lutz")
st.markdown("""
Análise de precisão do isocentro através de imagens de campo com marcador BB.
""")

if not PYLINAC_AVAILABLE:
    st.error("❌ Pylinac não está instalado. Execute: `pip install pylinac`")
    st.stop()

# Tabs para diferentes modos
if MTWL_AVAILABLE:
    tab1, tab2, tab3 = st.tabs([
        "📁 Análise Completa",
        "📷 Análise 2D",
        "🎯 Multi-Target (SRS/SBRT)"
    ])
else:
    tab1, tab2 = st.tabs(["📁 Análise Completa", "📷 Análise 2D"])

# =============================================================================
# TAB 1 - ANÁLISE COMPLETA
# =============================================================================
with tab1:
    st.subheader("Análise Winston-Lutz Completa")
    st.markdown("""
    Faça upload de múltiplas imagens DICOM de diferentes ângulos de gantry,
    colimador e/ou mesa para uma análise completa do isocentro.
    """)

    upload_option = st.radio(
        "Selecione o método de upload:",
        ["Múltiplos arquivos DICOM", "Arquivo ZIP"],
        horizontal=True,
        key="wl_upload_method"
    )

    uploaded_files = None
    zip_file = None

    if upload_option == "Múltiplos arquivos DICOM":
        uploaded_files = st.file_uploader(
            "Selecione as imagens DICOM",
            type=['dcm', 'DCM'],
            accept_multiple_files=True,
            key="wl_multi"
        )
    else:
        zip_file = st.file_uploader(
            "Selecione o arquivo ZIP contendo as imagens",
            type=['zip'],
            key="wl_zip"
        )

    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            use_filenames = st.checkbox(
                "Usar nomes de arquivos para ângulos",
                value=False,
                help="Extrai informações de gantry/colimador dos nomes dos arquivos"
            )
            low_density_bb = st.checkbox(
                "BB de baixa densidade",
                value=False,
                help="Marque se usar um BB de baixa densidade (ar)"
            )

        with col2:
            open_field = st.checkbox(
                "Campo aberto (sem BB)",
                value=False,
                help="Marque se as imagens são de campo aberto sem BB"
            )
            bb_size = st.number_input(
                "Tamanho do BB (mm)",
                min_value=1.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                key="bb_size_full"
            )

        with col3:
            sid_value = st.number_input(
                "SID (mm)",
                min_value=500.0,
                max_value=2000.0,
                value=1000.0,
                step=10.0
            )

    tolerance = st.slider(
        "Tolerância (mm)",
        min_value=0.5,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help="Tolerância máxima para desvio do isocentro"
    )

    if st.button("🔬 Executar Análise", key="wl_analyze", type="primary"):
        temp_paths = []

        try:
            with st.spinner("Processando imagens..."):
                if uploaded_files:
                    temp_paths = save_uploaded_files(uploaded_files)
                    wl = WinstonLutz(temp_paths, use_filenames=use_filenames,
                                    low_density_bb=low_density_bb, open_field=open_field)
                elif zip_file:
                    temp_dir = extract_zip_to_temp(zip_file)
                    temp_paths = [temp_dir]
                    wl = WinstonLutz(temp_dir, use_filenames=use_filenames,
                                    low_density_bb=low_density_bb, open_field=open_field)
                else:
                    st.warning("Por favor, faça upload das imagens primeiro.")
                    st.stop()

                wl.analyze(bb_size_mm=bb_size)

            st.success("✅ Análise concluída!")

            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)

            gantry_iso = wl.gantry_iso_size
            coll_iso = wl.collimator_iso_size
            couch_iso = wl.couch_iso_size
            max_2d_cax = wl.max_2d_cax_to_bb_mm

            with col1:
                delta_color = "normal" if gantry_iso <= tolerance else "off"
                st.metric("Iso Gantry", f"{gantry_iso:.2f} mm",
                         delta=f"Tol: {tolerance} mm", delta_color=delta_color)

            with col2:
                delta_color = "normal" if coll_iso <= tolerance else "off"
                st.metric("Iso Colimador", f"{coll_iso:.2f} mm",
                         delta=f"Tol: {tolerance} mm", delta_color=delta_color)

            with col3:
                delta_color = "normal" if couch_iso <= tolerance else "off"
                st.metric("Iso Mesa", f"{couch_iso:.2f} mm",
                         delta=f"Tol: {tolerance} mm", delta_color=delta_color)

            with col4:
                delta_color = "normal" if max_2d_cax <= tolerance else "off"
                st.metric("Máx 2D CAX-BB", f"{max_2d_cax:.2f} mm",
                         delta=f"Tol: {tolerance} mm", delta_color=delta_color)

            # Shift do BB
            st.subheader("📍 Shift Recomendado do BB")
            shift = wl.bb_shift_instructions()
            st.info(shift)

            # Estatísticas adicionais
            with st.expander("📊 Estatísticas Detalhadas"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Média CAX-BB", f"{wl.cax2bb_distance('mean'):.3f} mm")
                    st.metric("Mediana CAX-BB", f"{wl.cax2bb_distance('median'):.3f} mm")
                with col2:
                    st.metric("Máximo CAX-BB", f"{wl.cax2bb_distance('max'):.3f} mm")
                    st.metric("Número de Imagens", len(wl.images))

            # Visualização
            st.subheader("📊 Visualizações")
            fig_summary = wl.plot_summary(show=False)
            st.pyplot(fig_summary)
            plt.close(fig_summary)

            # Gráficos por eixo
            with st.expander("📈 Gráficos por Eixo"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Gantry**")
                    try:
                        fig_g = wl.plot_axis_images(axis='gantry', show=False)
                        st.pyplot(fig_g)
                        plt.close(fig_g)
                    except:
                        st.info("Dados de gantry insuficientes")

                with col2:
                    st.markdown("**Colimador**")
                    try:
                        fig_c = wl.plot_axis_images(axis='collimator', show=False)
                        st.pyplot(fig_c)
                        plt.close(fig_c)
                    except:
                        st.info("Dados de colimador insuficientes")

                with col3:
                    st.markdown("**Mesa**")
                    try:
                        fig_t = wl.plot_axis_images(axis='couch', show=False)
                        st.pyplot(fig_t)
                        plt.close(fig_t)
                    except:
                        st.info("Dados de mesa insuficientes")

            # Imagens individuais
            with st.expander("🖼️ Imagens Individuais"):
                num_images = len(wl.images)
                cols_per_row = 4
                for i in range(0, num_images, cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx < num_images:
                            with col:
                                fig, ax = plt.subplots(figsize=(4, 4))
                                wl.images[idx].plot(ax=ax)
                                ax.set_title(f"G{wl.images[idx].gantry_angle:.0f} C{wl.images[idx].collimator_angle:.0f}")
                                st.pyplot(fig)
                                plt.close(fig)

            # Tabela de resultados
            with st.expander("📋 Tabela de Resultados"):
                results_data = []
                for img in wl.images:
                    results_data.append({
                        "Gantry (°)": f"{img.gantry_angle:.1f}",
                        "Colimador (°)": f"{img.collimator_angle:.1f}",
                        "Mesa (°)": f"{img.couch_angle:.1f}",
                        "CAX-BB (mm)": f"{img.cax2bb_distance:.3f}",
                        "Status": "✅" if img.cax2bb_distance <= tolerance else "❌"
                    })
                st.dataframe(results_data, use_container_width=True)

            # Relatório PDF
            st.subheader("📄 Relatório")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                wl.publish_pdf(tmp_pdf.name)
                get_pdf_download_button(tmp_pdf.name, "winston_lutz_report.pdf")
                temp_paths.append(tmp_pdf.name)

        except Exception as e:
            st.error(f"❌ Erro durante a análise: {str(e)}")
            st.exception(e)

        finally:
            cleanup_temp_files(temp_paths)

# =============================================================================
# TAB 2 - ANÁLISE 2D
# =============================================================================
with tab2:
    st.subheader("Análise Winston-Lutz 2D")
    st.markdown("Análise de uma única imagem para verificação rápida.")

    uploaded_file_2d = st.file_uploader(
        "Selecione a imagem DICOM",
        type=['dcm', 'DCM', 'tif', 'tiff'],
        key="wl_2d"
    )

    if uploaded_file_2d:
        col1, col2 = st.columns(2)
        with col1:
            bb_size_2d = st.number_input(
                "Tamanho do BB (mm)",
                min_value=1.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                key="bb_size_2d"
            )
        with col2:
            low_density_2d = st.checkbox(
                "BB de baixa densidade",
                value=False,
                key="low_density_2d"
            )

        if st.button("🔬 Analisar Imagem", key="wl_2d_analyze", type="primary"):
            temp_path = save_uploaded_file(uploaded_file_2d)

            try:
                with st.spinner("Analisando imagem..."):
                    wl2d = WinstonLutz2D(temp_path, low_density_bb=low_density_2d)
                    wl2d.analyze(bb_size_mm=bb_size_2d)

                st.success("✅ Análise concluída!")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Distância CAX-BB", f"{wl2d.cax2bb_distance:.3f} mm")

                with col2:
                    st.metric("Centro Campo", f"({wl2d.field_cax.x:.1f}, {wl2d.field_cax.y:.1f}) px")

                with col3:
                    st.metric("Centro BB", f"({wl2d.bb.x:.1f}, {wl2d.bb.y:.1f}) px")

                # Visualização
                st.subheader("📊 Visualização")
                fig, ax = plt.subplots(figsize=(8, 8))
                wl2d.plot(ax=ax)
                st.pyplot(fig)
                plt.close(fig)

            except Exception as e:
                st.error(f"❌ Erro durante a análise: {str(e)}")

            finally:
                cleanup_temp_files([temp_path])

# =============================================================================
# TAB 3 - MULTI-TARGET MULTI-FIELD (SRS/SBRT)
# =============================================================================
if MTWL_AVAILABLE:
    with tab3:
        st.subheader("🎯 Winston-Lutz Multi-Target Multi-Field")
        st.markdown("""
        Análise avançada para SRS/SBRT com múltiplos alvos e campos.
        Ideal para verificação de sistemas com múltiplos isocentros ou alvos de tratamento.
        """)

        st.info("""
        **Requisitos:**
        - Imagens DICOM com metadados de posição
        - Múltiplos BBs ou alvos identificáveis
        - Configuração de arranjo de BBs conhecida
        """)

        upload_mtwl = st.file_uploader(
            "Selecione o arquivo ZIP com as imagens",
            type=['zip'],
            key="mtwl_zip"
        )

        with st.expander("⚙️ Configuração de Alvos", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                num_targets = st.number_input(
                    "Número de alvos/BBs",
                    min_value=1,
                    max_value=10,
                    value=4,
                    help="Número de BBs no phantom multi-target"
                )

                bb_size_mtwl = st.number_input(
                    "Tamanho dos BBs (mm)",
                    min_value=1.0,
                    max_value=10.0,
                    value=5.0,
                    step=0.5,
                    key="bb_size_mtwl"
                )

            with col2:
                arrangement = st.selectbox(
                    "Arranjo dos BBs",
                    options=["Isocêntrico", "Quadrado", "Linear", "Customizado"],
                    help="Configuração geométrica dos BBs"
                )

                mtwl_tolerance = st.number_input(
                    "Tolerância (mm)",
                    min_value=0.1,
                    max_value=2.0,
                    value=1.0,
                    step=0.1,
                    key="mtwl_tol"
                )

        if upload_mtwl:
            if st.button("🔬 Analisar Multi-Target", key="mtwl_analyze", type="primary"):
                temp_paths = []

                try:
                    with st.spinner("Analisando imagens multi-target..."):
                        temp_dir = extract_zip_to_temp(upload_mtwl)
                        temp_paths.append(temp_dir)

                        # Usa a classe MTWL
                        mtwl = WinstonLutzMultiTargetMultiField(temp_dir)
                        mtwl.analyze(bb_size_mm=bb_size_mtwl)

                    st.success("✅ Análise Multi-Target concluída!")

                    # Resultados
                    st.subheader("📊 Resultados por Alvo")

                    # Métricas gerais
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        max_error = mtwl.max_bb_deviation_mm
                        delta_color = "normal" if max_error <= mtwl_tolerance else "off"
                        st.metric("Erro Máximo", f"{max_error:.3f} mm",
                                 delta=f"Tol: {mtwl_tolerance} mm", delta_color=delta_color)

                    with col2:
                        mean_error = mtwl.mean_bb_deviation_mm
                        st.metric("Erro Médio", f"{mean_error:.3f} mm")

                    with col3:
                        st.metric("Número de Alvos", f"{len(mtwl.bbs)}")

                    # Visualização
                    st.subheader("🖼️ Visualização")
                    fig = mtwl.plot(show=False)
                    st.pyplot(fig)
                    plt.close(fig)

                    # Tabela de resultados por BB
                    with st.expander("📋 Resultados por BB"):
                        bb_results = []
                        for i, bb in enumerate(mtwl.bbs):
                            bb_results.append({
                                "BB": i + 1,
                                "Posição X (mm)": f"{bb.x:.2f}",
                                "Posição Y (mm)": f"{bb.y:.2f}",
                                "Desvio (mm)": f"{bb.deviation:.3f}",
                                "Status": "✅" if bb.deviation <= mtwl_tolerance else "❌"
                            })
                        st.dataframe(bb_results, use_container_width=True)

                    # Relatório PDF
                    st.subheader("📄 Relatório")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                        mtwl.publish_pdf(tmp_pdf.name)
                        get_pdf_download_button(tmp_pdf.name, "winston_lutz_mtwl_report.pdf")
                        temp_paths.append(tmp_pdf.name)

                except Exception as e:
                    st.error(f"❌ Erro durante a análise: {str(e)}")
                    st.exception(e)

                finally:
                    cleanup_temp_files(temp_paths)

        else:
            st.info("👆 Faça upload de um arquivo ZIP com as imagens multi-target.")

# Instruções
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Análise Winston-Lutz Completa

    1. **Preparação**:
       - Posicione o phantom Winston-Lutz (BB) no isocentro nominal
       - Configure o campo de radiação (tipicamente 2x2 cm ou 1x1 cm para SRS)

    2. **Aquisição de Imagens**:
       - Adquira imagens em múltiplos ângulos de gantry (ex: 0°, 90°, 180°, 270°)
       - Opcionalmente, varie o ângulo do colimador e da mesa
       - Use o sistema EPID para captura das imagens

    3. **Análise e Interpretação**:
       - O tamanho do isocentro deve estar dentro da tolerância
       - Siga as instruções de shift do BB se necessário

    ### Análise Multi-Target (SRS/SBRT)

    Para sistemas com múltiplos isocentros ou tratamentos SRS:
    - Use phantom com múltiplos BBs
    - Verifique a precisão de cada alvo individualmente
    - Ideal para verificação de sistemas frameless

    ### Tolerâncias Típicas (TG-142):

    | Aplicação | Tolerância |
    |-----------|------------|
    | Radioterapia convencional | ≤ 2 mm |
    | SRS/SBRT | ≤ 1 mm |
    | SRS cranial | ≤ 0.75 mm |
    | Multi-target SRS | ≤ 1 mm por alvo |
    """)
