"""
Funções auxiliares compartilhadas entre os módulos
"""

import streamlit as st
import tempfile
import os
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional
import io


def save_uploaded_file(uploaded_file) -> str:
    """
    Salva um arquivo uploaded em um diretório temporário.
    Retorna o caminho do arquivo salvo.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def save_uploaded_files(uploaded_files) -> List[str]:
    """
    Salva múltiplos arquivos uploaded em um diretório temporário.
    Retorna lista de caminhos dos arquivos salvos.
    """
    paths = []
    for uploaded_file in uploaded_files:
        path = save_uploaded_file(uploaded_file)
        paths.append(path)
    return paths


def extract_zip_to_temp(uploaded_zip) -> str:
    """
    Extrai um arquivo ZIP para um diretório temporário.
    Retorna o caminho do diretório.
    """
    temp_dir = tempfile.mkdtemp()
    zip_path = save_uploaded_file(uploaded_zip)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    os.unlink(zip_path)
    return temp_dir


def cleanup_temp_files(paths: List[str]):
    """Remove arquivos temporários."""
    for path in paths:
        try:
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
        except Exception:
            pass


def display_results_table(results: dict, title: str = "Resultados"):
    """Exibe uma tabela formatada com os resultados."""
    st.subheader(title)

    # Formata os valores para exibição
    formatted_results = {}
    for key, value in results.items():
        if isinstance(value, float):
            formatted_results[key] = f"{value:.4f}"
        else:
            formatted_results[key] = str(value)

    # Cria duas colunas para exibir os resultados
    col1, col2 = st.columns(2)
    items = list(formatted_results.items())
    half = len(items) // 2 + len(items) % 2

    with col1:
        for key, value in items[:half]:
            st.metric(label=key, value=value)

    with col2:
        for key, value in items[half:]:
            st.metric(label=key, value=value)


def create_download_button(data: bytes, filename: str, label: str = "Download"):
    """Cria um botão de download para dados binários."""
    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime="application/octet-stream"
    )


def get_pdf_download_button(pdf_path: str, filename: str = "relatorio.pdf"):
    """Cria botão de download para PDF gerado."""
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()

    st.download_button(
        label="📄 Download Relatório PDF",
        data=pdf_data,
        file_name=filename,
        mime="application/pdf"
    )


def show_analysis_status(status: str, message: str):
    """Exibe status da análise com ícone apropriado."""
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️"
    }
    icon = icons.get(status, "ℹ️")

    if status == "success":
        st.success(f"{icon} {message}")
    elif status == "warning":
        st.warning(f"{icon} {message}")
    elif status == "error":
        st.error(f"{icon} {message}")
    else:
        st.info(f"{icon} {message}")


def format_tolerance_result(value: float, tolerance: float, unit: str = "mm") -> Tuple[str, str]:
    """
    Formata resultado com base na tolerância.
    Retorna (valor_formatado, status).
    """
    formatted_value = f"{value:.3f} {unit}"

    if abs(value) <= tolerance:
        status = "success"
    elif abs(value) <= tolerance * 1.5:
        status = "warning"
    else:
        status = "error"

    return formatted_value, status


def create_sidebar_info(module_name: str, description: str, references: List[str] = None):
    """Cria informações do módulo na sidebar."""
    with st.sidebar:
        st.markdown(f"### {module_name}")
        st.markdown(description)

        if references:
            with st.expander("📚 Referências"):
                for ref in references:
                    st.markdown(f"- {ref}")


def validate_file_type(uploaded_file, allowed_extensions: List[str]) -> bool:
    """Valida se o arquivo tem uma extensão permitida."""
    if uploaded_file is None:
        return False

    file_ext = Path(uploaded_file.name).suffix.lower()
    return file_ext in [ext.lower() for ext in allowed_extensions]
