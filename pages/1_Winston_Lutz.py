"""
Módulo Winston-Lutz - Análise de Isocentro
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="Winston-Lutz", page_icon="🎯", layout="wide")

# Importações do pylinac
try:
    from pylinac import WinstonLutz
    from pylinac.winston_lutz import WinstonLutz2D
    PYLINAC_AVAILABLE = True
except ImportError:
    PYLINAC_AVAILABLE = False

# Adiciona path do utils
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import (
    save_uploaded_file, save_uploaded_files, extract_zip_to_temp,
    cleanup_temp_files, display_results_table, get_pdf_download_button,
    show_analysis_status, create_sidebar_info
)

# Sidebar info
create_sidebar_info(
    module_name="🎯 Winston-Lutz",
    description="""
    O teste Winston-Lutz determina a precisão do isocentro do acelerador
    medindo a distância entre o centro do campo de radiação e um marcador
    BB em múltiplas posições de gantry, colimador e mesa.
    """,
    references=[
        "Lutz W, Winston KR, Maleki N. A system for stereotactic radiosurgery with a linear accelerator. Int J Radiat Oncol Biol Phys. 1988",
        "AAPM TG-142: Quality assurance of medical accelerators"
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
tab1, tab2 = st.tabs(["📁 Análise Completa (Múltiplas Imagens)", "📷 Análise 2D (Imagem Única)"])

with tab1:
    st.subheader("Análise Winston-Lutz Completa")
    st.markdown("""
    Faça upload de múltiplas imagens DICOM de diferentes ângulos de gantry,
    colimador e/ou mesa para uma análise completa do isocentro.
    """)

    # Opções de upload
    upload_option = st.radio(
        "Selecione o método de upload:",
        ["Múltiplos arquivos DICOM", "Arquivo ZIP"],
        horizontal=True
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

    # Parâmetros de análise
    with st.expander("⚙️ Parâmetros de Análise", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            use_filenames = st.checkbox(
                "Usar nomes de arquivos para ângulos",
                value=False,
                help="Se marcado, extrai informações de gantry/colimador dos nomes dos arquivos"
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
            sid_value = st.number_input(
                "SID (mm)",
                min_value=500.0,
                max_value=2000.0,
                value=1000.0,
                step=10.0,
                help="Distância fonte-imagem"
            )

    # Tolerância
    tolerance = st.slider(
        "Tolerância (mm)",
        min_value=0.5,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help="Tolerância máxima permitida para desvio do isocentro"
    )

    # Botão de análise
    if st.button("🔬 Executar Análise", key="wl_analyze", type="primary"):
        temp_paths = []

        try:
            with st.spinner("Processando imagens..."):
                # Prepara os arquivos
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

                # Analisa
                wl.analyze(bb_size_mm=5)

            # Resultados
            st.success("✅ Análise concluída!")

            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)

            gantry_iso = wl.gantry_iso_size
            coll_iso = wl.collimator_iso_size
            couch_iso = wl.couch_iso_size
            max_2d_cax = wl.max_2d_cax_to_bb_mm

            with col1:
                status = "normal" if gantry_iso <= tolerance else "off"
                st.metric(
                    "Tamanho Iso Gantry",
                    f"{gantry_iso:.2f} mm",
                    delta=f"Tol: {tolerance} mm",
                    delta_color=status
                )

            with col2:
                status = "normal" if coll_iso <= tolerance else "off"
                st.metric(
                    "Tamanho Iso Colimador",
                    f"{coll_iso:.2f} mm",
                    delta=f"Tol: {tolerance} mm",
                    delta_color=status
                )

            with col3:
                status = "normal" if couch_iso <= tolerance else "off"
                st.metric(
                    "Tamanho Iso Mesa",
                    f"{couch_iso:.2f} mm",
                    delta=f"Tol: {tolerance} mm",
                    delta_color=status
                )

            with col4:
                status = "normal" if max_2d_cax <= tolerance else "off"
                st.metric(
                    "Máx 2D CAX-BB",
                    f"{max_2d_cax:.2f} mm",
                    delta=f"Tol: {tolerance} mm",
                    delta_color=status
                )

            # Shift do BB
            st.subheader("📍 Shift Recomendado do BB")
            shift = wl.bb_shift_instructions()
            st.info(shift)

            # Gráficos
            st.subheader("📊 Visualizações")

            # Plot resumo
            fig_summary, ax_summary = plt.subplots(figsize=(10, 8))
            wl.plot_summary(fig=fig_summary)
            st.pyplot(fig_summary)
            plt.close(fig_summary)

            # Imagens individuais
            with st.expander("🖼️ Ver Imagens Individuais"):
                num_images = len(wl.images)
                cols_per_row = 4
                for i in range(0, num_images, cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx < num_images:
                            with col:
                                fig, ax = plt.subplots(figsize=(5, 5))
                                wl.images[idx].plot(ax=ax)
                                st.pyplot(fig)
                                plt.close(fig)

            # Gráfico de eixos
            with st.expander("📈 Gráficos por Eixo"):
                fig_axis = plt.figure(figsize=(12, 4))
                wl.plot_axis_images(axis='gantry', fig=fig_axis)
                st.pyplot(fig_axis)
                plt.close(fig_axis)

            # Tabela de resultados
            with st.expander("📋 Tabela de Resultados Detalhados"):
                results_data = []
                for img in wl.images:
                    results_data.append({
                        "Gantry": f"{img.gantry_angle:.1f}°",
                        "Colimador": f"{img.collimator_angle:.1f}°",
                        "Mesa": f"{img.couch_angle:.1f}°",
                        "CAX-BB (mm)": f"{img.cax2bb_distance:.3f}",
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


with tab2:
    st.subheader("Análise Winston-Lutz 2D")
    st.markdown("""
    Análise de uma única imagem Winston-Lutz para verificação rápida.
    """)

    uploaded_file_2d = st.file_uploader(
        "Selecione a imagem DICOM",
        type=['dcm', 'DCM'],
        key="wl_2d"
    )

    if uploaded_file_2d:
        # Parâmetros 2D
        col1, col2 = st.columns(2)
        with col1:
            bb_size = st.number_input(
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
                    wl2d.analyze(bb_size_mm=bb_size)

                st.success("✅ Análise concluída!")

                # Resultados
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Distância CAX-BB", f"{wl2d.cax2bb_distance:.3f} mm")
                    st.metric("Centro do Campo X", f"{wl2d.field_cax.x:.2f} px")
                    st.metric("Centro do Campo Y", f"{wl2d.field_cax.y:.2f} px")

                with col2:
                    st.metric("Centro do BB X", f"{wl2d.bb.x:.2f} px")
                    st.metric("Centro do BB Y", f"{wl2d.bb.y:.2f} px")

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

# Instruções de uso
with st.expander("📖 Instruções de Uso"):
    st.markdown("""
    ### Como realizar o teste Winston-Lutz:

    1. **Preparação**:
       - Posicione o phantom Winston-Lutz (BB) no isocentro nominal
       - Configure o campo de radiação (tipicamente 2x2 cm ou 1x1 cm para SRS)

    2. **Aquisição de Imagens**:
       - Adquira imagens em múltiplos ângulos de gantry (ex: 0°, 90°, 180°, 270°)
       - Opcionalmente, varie também o ângulo do colimador e da mesa
       - Use o sistema EPID ou CR para captura das imagens

    3. **Análise**:
       - Faça upload de todas as imagens
       - Ajuste os parâmetros conforme necessário
       - Execute a análise

    4. **Interpretação**:
       - O tamanho do isocentro deve estar dentro da tolerância (tipicamente ≤ 1mm)
       - Siga as instruções de shift do BB se necessário
       - Gere o relatório PDF para documentação

    ### Tolerâncias Típicas (TG-142):
    - **Radioterapia convencional**: ≤ 2 mm
    - **SRS/SBRT**: ≤ 1 mm
    - **SRS cranial**: ≤ 0.75 mm
    """)
