"""
SPC - Controle Estatístico de Processo
Cartas de controle e análise de tendências para QA
"""

import streamlit as st
from datetime import datetime, date, timedelta
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="SPC", page_icon="📈", layout="wide")

import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.database import get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from utils.helpers import create_sidebar_info

create_sidebar_info(
    module_name="📈 SPC - Controle Estatístico",
    description="""
    Controle Estatístico de Processo para QA de radioterapia.

    **Funcionalidades:**
    - Cartas de controle (Shewhart)
    - Limites de alerta e ação
    - Detecção de tendências
    - Regras de Western Electric
    - CUSUM (soma acumulada)

    **Aplicações:**
    - Monitorar estabilidade do equipamento
    - Detectar desvios antes da falha
    - Documentar performance ao longo do tempo
    """,
    references=[
        ("SPC in Radiotherapy", "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3667344/")
    ]
)

st.title("📈 SPC - Controle Estatístico de Processo")
st.markdown("### Análise de Tendências e Cartas de Controle")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Carta de Controle",
    "📉 CUSUM",
    "🔍 Análise de Tendências",
    "⚙️ Configuração"
])

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def calculate_control_limits(data, sigma=3):
    """Calcula limites de controle para carta Shewhart"""
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    ucl = mean + sigma * std  # Upper Control Limit
    lcl = mean - sigma * std  # Lower Control Limit
    uwl = mean + 2 * std      # Upper Warning Limit
    lwl = mean - 2 * std      # Lower Warning Limit

    return {
        'mean': mean,
        'std': std,
        'ucl': ucl,
        'lcl': lcl,
        'uwl': uwl,
        'lwl': lwl
    }

def check_western_electric_rules(data, limits):
    """Verifica regras de Western Electric para detecção de anomalias"""
    mean = limits['mean']
    std = limits['std']
    violations = []

    n = len(data)

    for i in range(n):
        point_violations = []

        # Regra 1: Um ponto além de 3 sigma
        if data[i] > limits['ucl'] or data[i] < limits['lcl']:
            point_violations.append("R1: Ponto além de 3σ")

        # Regra 2: 2 de 3 pontos consecutivos além de 2 sigma
        if i >= 2:
            beyond_2sigma = sum(1 for j in range(i-2, i+1)
                               if abs(data[j] - mean) > 2 * std)
            if beyond_2sigma >= 2:
                point_violations.append("R2: 2/3 pontos além de 2σ")

        # Regra 3: 4 de 5 pontos consecutivos além de 1 sigma
        if i >= 4:
            beyond_1sigma = sum(1 for j in range(i-4, i+1)
                               if abs(data[j] - mean) > std)
            if beyond_1sigma >= 4:
                point_violations.append("R3: 4/5 pontos além de 1σ")

        # Regra 4: 8 pontos consecutivos do mesmo lado da média
        if i >= 7:
            same_side = all(data[j] > mean for j in range(i-7, i+1)) or \
                       all(data[j] < mean for j in range(i-7, i+1))
            if same_side:
                point_violations.append("R4: 8 pontos do mesmo lado")

        # Regra 5: 6 pontos consecutivos crescentes ou decrescentes
        if i >= 5:
            increasing = all(data[j] < data[j+1] for j in range(i-5, i))
            decreasing = all(data[j] > data[j+1] for j in range(i-5, i))
            if increasing or decreasing:
                point_violations.append("R5: 6 pontos em tendência")

        if point_violations:
            violations.append((i, point_violations))

    return violations

def calculate_cusum(data, target, k=0.5, h=5):
    """Calcula CUSUM (Cumulative Sum) para detecção de mudança"""
    n = len(data)
    std = np.std(data, ddof=1)

    cusum_pos = np.zeros(n)
    cusum_neg = np.zeros(n)

    k_scaled = k * std
    h_scaled = h * std

    for i in range(n):
        if i == 0:
            cusum_pos[i] = max(0, data[i] - target - k_scaled)
            cusum_neg[i] = max(0, target - data[i] - k_scaled)
        else:
            cusum_pos[i] = max(0, cusum_pos[i-1] + data[i] - target - k_scaled)
            cusum_neg[i] = max(0, cusum_neg[i-1] + target - data[i] - k_scaled)

    return cusum_pos, cusum_neg, h_scaled

# Configurações comuns
with st.sidebar:
    st.subheader("Configurações")

    if DB_AVAILABLE:
        db = get_database()
        machines = db.get_machines()
        machine_names = [m['name'] for m in machines] if machines else ["Todas"]
        machine = st.selectbox("Máquina", options=["Todas"] + machine_names, key="spc_machine")
    else:
        machine = st.text_input("Máquina", value="Todas", key="spc_machine")

    st.divider()

    data_source = st.selectbox(
        "Fonte de Dados",
        ["Banco de dados", "Entrada manual", "Upload CSV"]
    )

    if data_source == "Banco de dados" and DB_AVAILABLE:
        test_type = st.selectbox(
            "Tipo de Teste",
            ["daily_qa", "weekly_qa", "output_factors", "pdd_tmr", "winston_lutz"],
            format_func=lambda x: {
                "daily_qa": "QA Diário",
                "weekly_qa": "QA Semanal",
                "output_factors": "Output Factors",
                "pdd_tmr": "PDD/TMR",
                "winston_lutz": "Winston-Lutz"
            }.get(x, x)
        )

        parameter = st.text_input("Parâmetro", value="diff_percent")
        period = st.slider("Período (dias)", 30, 365, 90)

# =============================================================================
# TAB 1: CARTA DE CONTROLE
# =============================================================================
with tab1:
    st.subheader("📊 Carta de Controle de Shewhart")

    st.markdown("""
    Carta de controle para monitoramento estatístico de processos.
    Inclui verificação das regras de Western Electric para detecção de anomalias.
    """)

    # Obter ou inserir dados
    data = None
    dates = None

    if data_source == "Banco de dados" and DB_AVAILABLE:
        start_date = datetime.now() - timedelta(days=period)

        machine_filter = machine if machine != "Todas" else None
        results = db.get_results(
            test_type=test_type,
            machine_name=machine_filter,
            start_date=start_date,
            limit=500
        )

        if results:
            # Extrair valores do parâmetro
            values = []
            date_list = []

            for r in results:
                if r.get('results') and parameter in r['results']:
                    values.append(r['results'][parameter])
                    date_list.append(r['test_date'][:10] if r['test_date'] else "")

            if values:
                data = np.array(values)
                dates = date_list
                st.success(f"Carregados {len(data)} pontos de dados")
            else:
                st.warning(f"Parâmetro '{parameter}' não encontrado nos resultados")

    elif data_source == "Entrada manual":
        st.markdown("#### Entrada Manual de Dados")

        manual_data = st.text_area(
            "Insira os valores (um por linha ou separados por vírgula)",
            value="100.0, 99.8, 100.2, 99.5, 100.1, 100.3, 99.7, 100.0, 99.9, 100.1",
            height=100
        )

        try:
            # Tentar separar por vírgula ou nova linha
            if ',' in manual_data:
                data = np.array([float(x.strip()) for x in manual_data.split(',') if x.strip()])
            else:
                data = np.array([float(x.strip()) for x in manual_data.split('\n') if x.strip()])

            dates = [f"Ponto {i+1}" for i in range(len(data))]
            st.success(f"Carregados {len(data)} pontos")
        except ValueError:
            st.error("Erro ao processar dados. Verifique o formato.")

    elif data_source == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV (colunas: data, valor)", type=['csv'])

        if uploaded_file:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded_file)
                data = df.iloc[:, 1].values  # Segunda coluna = valores
                dates = df.iloc[:, 0].astype(str).tolist()  # Primeira coluna = datas
                st.success(f"Carregados {len(data)} pontos")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {str(e)}")

    # Gerar carta de controle
    if data is not None and len(data) >= 5:
        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col2:
            st.markdown("#### Configuração")

            use_baseline = st.checkbox("Usar baseline personalizado", value=False)

            if use_baseline:
                baseline_mean = st.number_input("Média baseline", value=float(np.mean(data)), format="%.4f")
                baseline_std = st.number_input("Desvio padrão baseline", value=float(np.std(data, ddof=1)), format="%.4f")
                limits = {
                    'mean': baseline_mean,
                    'std': baseline_std,
                    'ucl': baseline_mean + 3 * baseline_std,
                    'lcl': baseline_mean - 3 * baseline_std,
                    'uwl': baseline_mean + 2 * baseline_std,
                    'lwl': baseline_mean - 2 * baseline_std
                }
            else:
                limits = calculate_control_limits(data)

            show_warning = st.checkbox("Mostrar limites de alerta (2σ)", value=True)
            show_rules = st.checkbox("Verificar regras Western Electric", value=True)

        with col1:
            # Verificar violações
            violations = check_western_electric_rules(data, limits) if show_rules else []
            violation_indices = [v[0] for v in violations]

            # Criar gráfico
            fig, ax = plt.subplots(figsize=(12, 6))

            # Plotar dados
            x = range(len(data))

            # Cores baseadas em violações
            colors = ['red' if i in violation_indices else 'blue' for i in x]

            ax.scatter(x, data, c=colors, s=50, zorder=5)
            ax.plot(x, data, 'b-', alpha=0.3, linewidth=1)

            # Limites
            ax.axhline(y=limits['mean'], color='green', linestyle='-', linewidth=2, label=f"Média ({limits['mean']:.3f})")
            ax.axhline(y=limits['ucl'], color='red', linestyle='--', linewidth=2, label=f"UCL ({limits['ucl']:.3f})")
            ax.axhline(y=limits['lcl'], color='red', linestyle='--', linewidth=2, label=f"LCL ({limits['lcl']:.3f})")

            if show_warning:
                ax.axhline(y=limits['uwl'], color='orange', linestyle=':', linewidth=1.5, label=f"UWL ({limits['uwl']:.3f})")
                ax.axhline(y=limits['lwl'], color='orange', linestyle=':', linewidth=1.5, label=f"LWL ({limits['lwl']:.3f})")

            # Preencher zonas
            ax.fill_between(x, limits['lcl'], limits['ucl'], alpha=0.1, color='green')

            ax.set_xlabel('Amostra')
            ax.set_ylabel('Valor')
            ax.set_title('Carta de Controle de Shewhart')
            ax.legend(loc='upper right', fontsize=8)
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # Estatísticas
        st.markdown("#### Estatísticas")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Média", f"{limits['mean']:.4f}")
        with col2:
            st.metric("Desvio Padrão", f"{limits['std']:.4f}")
        with col3:
            st.metric("Pontos", len(data))
        with col4:
            st.metric("Violações", len(violations))

        # Mostrar violações
        if violations and show_rules:
            st.markdown("#### Violações Detectadas")

            for idx, rules in violations:
                date_str = dates[idx] if dates else f"Ponto {idx+1}"
                value = data[idx]

                with st.expander(f"⚠️ {date_str}: Valor = {value:.4f}"):
                    for rule in rules:
                        st.warning(rule)

        # Status geral
        if len(violations) == 0:
            st.success("✅ Processo sob controle estatístico")
        else:
            st.warning(f"⚠️ Processo com {len(violations)} violações - investigar causas")

# =============================================================================
# TAB 2: CUSUM
# =============================================================================
with tab2:
    st.subheader("📉 Carta CUSUM")

    st.markdown("""
    A carta CUSUM (Cumulative Sum) é mais sensível para detectar pequenas
    mudanças sistemáticas no processo que podem não ser detectadas pela carta Shewhart.
    """)

    if data is not None and len(data) >= 5:
        col1, col2 = st.columns([3, 1])

        with col2:
            st.markdown("#### Parâmetros CUSUM")

            target = st.number_input(
                "Valor alvo",
                value=float(np.mean(data)),
                format="%.4f",
                key="cusum_target"
            )

            k_factor = st.slider("Fator k (sensibilidade)", 0.1, 1.0, 0.5, 0.1)
            h_factor = st.slider("Fator h (limite de decisão)", 2.0, 10.0, 5.0, 0.5)

        # Calcular CUSUM
        cusum_pos, cusum_neg, h_limit = calculate_cusum(data, target, k_factor, h_factor)

        with col1:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

            x = range(len(data))

            # Gráfico superior: Dados originais
            ax1.plot(x, data, 'b-o', markersize=4)
            ax1.axhline(y=target, color='green', linestyle='-', linewidth=2, label=f'Alvo ({target:.3f})')
            ax1.set_ylabel('Valor')
            ax1.set_title('Dados Originais')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Gráfico inferior: CUSUM
            ax2.plot(x, cusum_pos, 'r-', linewidth=2, label='CUSUM+ (aumento)')
            ax2.plot(x, cusum_neg, 'b-', linewidth=2, label='CUSUM- (diminuição)')
            ax2.axhline(y=h_limit, color='red', linestyle='--', linewidth=2, label=f'Limite h ({h_limit:.2f})')
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            ax2.set_xlabel('Amostra')
            ax2.set_ylabel('CUSUM')
            ax2.set_title('Carta CUSUM')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        # Detectar violações
        pos_violations = np.where(cusum_pos > h_limit)[0]
        neg_violations = np.where(cusum_neg > h_limit)[0]

        col1, col2 = st.columns(2)

        with col1:
            if len(pos_violations) > 0:
                st.error(f"⚠️ Detectado aumento sistemático a partir do ponto {pos_violations[0]+1}")
            else:
                st.success("✅ Sem aumento sistemático detectado")

        with col2:
            if len(neg_violations) > 0:
                st.error(f"⚠️ Detectada diminuição sistemática a partir do ponto {neg_violations[0]+1}")
            else:
                st.success("✅ Sem diminuição sistemática detectada")

    else:
        st.info("Carregue dados para gerar a carta CUSUM")

# =============================================================================
# TAB 3: ANÁLISE DE TENDÊNCIAS
# =============================================================================
with tab3:
    st.subheader("🔍 Análise de Tendências")

    if data is not None and len(data) >= 5:
        st.markdown("#### Análise de Regressão Linear")

        x = np.arange(len(data))

        # Ajuste linear
        coeffs = np.polyfit(x, data, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        fit_line = np.polyval(coeffs, x)

        # R²
        ss_res = np.sum((data - fit_line) ** 2)
        ss_tot = np.sum((data - np.mean(data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Gráfico
        fig, ax = plt.subplots(figsize=(12, 5))

        ax.scatter(x, data, s=50, c='blue', alpha=0.6, label='Dados')
        ax.plot(x, fit_line, 'r-', linewidth=2,
               label=f'Tendência: y = {slope:.4f}x + {intercept:.4f}')

        ax.set_xlabel('Amostra')
        ax.set_ylabel('Valor')
        ax.set_title('Análise de Tendência Linear')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # Métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Inclinação", f"{slope:.6f}")
        with col2:
            st.metric("R²", f"{r_squared:.4f}")
        with col3:
            # Variação total no período
            total_change = slope * len(data)
            st.metric("Variação Total", f"{total_change:.4f}")
        with col4:
            # Variação percentual
            if np.mean(data) != 0:
                pct_change = (total_change / np.mean(data)) * 100
                st.metric("Variação %", f"{pct_change:.2f}%")

        # Interpretação
        st.markdown("#### Interpretação")

        if abs(slope) < 0.0001:
            st.success("✅ **Processo estável** - Sem tendência significativa detectada")
        elif slope > 0:
            if pct_change > 1:
                st.warning(f"⚠️ **Tendência de aumento** - O parâmetro está aumentando ~{pct_change:.1f}% no período")
            else:
                st.info(f"ℹ️ **Leve tendência de aumento** - Variação de ~{pct_change:.1f}%")
        else:
            if abs(pct_change) > 1:
                st.warning(f"⚠️ **Tendência de diminuição** - O parâmetro está diminuindo ~{abs(pct_change):.1f}% no período")
            else:
                st.info(f"ℹ️ **Leve tendência de diminuição** - Variação de ~{abs(pct_change):.1f}%")

        # Previsão
        st.markdown("#### Projeção Futura")

        projection_points = st.slider("Pontos de projeção", 5, 50, 20)

        x_future = np.arange(len(data), len(data) + projection_points)
        y_future = np.polyval(coeffs, x_future)

        fig2, ax2 = plt.subplots(figsize=(12, 5))

        ax2.scatter(x, data, s=50, c='blue', alpha=0.6, label='Histórico')
        ax2.plot(x, fit_line, 'b-', linewidth=1, alpha=0.5)
        ax2.plot(x_future, y_future, 'r--', linewidth=2, label='Projeção')

        # Adicionar limites se disponíveis
        if 'limits' in dir() and limits:
            ax2.axhline(y=limits['ucl'], color='red', linestyle=':', alpha=0.5, label='UCL')
            ax2.axhline(y=limits['lcl'], color='red', linestyle=':', alpha=0.5, label='LCL')

        ax2.set_xlabel('Amostra')
        ax2.set_ylabel('Valor')
        ax2.set_title('Projeção de Tendência')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    else:
        st.info("Carregue dados para análise de tendências")

# =============================================================================
# TAB 4: CONFIGURAÇÃO
# =============================================================================
with tab4:
    st.subheader("⚙️ Configuração de Limites")

    st.markdown("""
    Configure limites de alerta e ação para parâmetros específicos.
    Estes limites serão usados no monitoramento contínuo.
    """)

    if DB_AVAILABLE:
        # Carregar tolerâncias existentes
        tolerances = db.get_tolerances()

        st.markdown("#### Tolerâncias por Teste")

        # Agrupar por tipo
        test_types = {}
        for t in tolerances:
            if t['test_type'] not in test_types:
                test_types[t['test_type']] = []
            test_types[t['test_type']].append(t)

        for test_type, params in test_types.items():
            with st.expander(f"📋 {test_type.replace('_', ' ').title()}"):
                for p in params:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                    with col1:
                        st.text(p['parameter'])
                    with col2:
                        st.text(f"Tol: {p['tolerance_value']} {p['unit'] or ''}")
                    with col3:
                        st.text(f"Ação: {p['action_level'] or 'N/A'}")
                    with col4:
                        if st.button("📝", key=f"edit_{p['id']}"):
                            st.session_state[f"editing_{p['id']}"] = True

        st.divider()

        st.markdown("#### Parâmetros SPC Recomendados")

        recommendations = [
            {"Parâmetro": "Output constância (diário)", "Limite Alerta (2σ)": "±2%", "Limite Ação (3σ)": "±3%"},
            {"Parâmetro": "Posição de lasers", "Limite Alerta (2σ)": "±1.5 mm", "Limite Ação (3σ)": "±2 mm"},
            {"Parâmetro": "MLC posição", "Limite Alerta (2σ)": "±0.7 mm", "Limite Ação (3σ)": "±1 mm"},
            {"Parâmetro": "Winston-Lutz", "Limite Alerta (2σ)": "±0.7 mm", "Limite Ação (3σ)": "±1 mm"},
            {"Parâmetro": "Flatness", "Limite Alerta (2σ)": "±2%", "Limite Ação (3σ)": "±3%"},
            {"Parâmetro": "Simetria", "Limite Alerta (2σ)": "±2%", "Limite Ação (3σ)": "±3%"},
        ]

        st.dataframe(recommendations, use_container_width=True, hide_index=True)

    else:
        st.warning("Banco de dados não disponível")

    st.divider()

    st.markdown("#### Regras de Western Electric")

    st.markdown("""
    As regras de Western Electric são usadas para detectar processos fora de controle:

    | Regra | Descrição | Significado |
    |-------|-----------|-------------|
    | R1 | 1 ponto além de 3σ | Causa especial óbvia |
    | R2 | 2 de 3 pontos além de 2σ | Possível mudança no processo |
    | R3 | 4 de 5 pontos além de 1σ | Tendência se formando |
    | R4 | 8 pontos do mesmo lado da média | Mudança de nível |
    | R5 | 6 pontos consecutivos crescentes/decrescentes | Deriva do processo |
    """)

    st.markdown("""
    **Ações recomendadas:**
    - **R1**: Investigar imediatamente - possível erro ou falha
    - **R2-R3**: Monitorar próximos pontos - possível problema em desenvolvimento
    - **R4-R5**: Investigar causa raiz - calibração pode ser necessária
    """)
