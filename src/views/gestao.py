import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database import db
from datetime import datetime

def render():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        div[data-testid="stMetricValue"] { font-size: 24px; color: #002D58; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Business Intelligence - Gestão de Custos Extras")
    st.caption("Linea Alimentos | Visão Estratégica e Controle de SLA")

    # --- 1. CARREGAMENTO DE DADOS ---
    try:
        # Busca todas as solicitações e o histórico para cálculo de SLA
        res_sol = db.table("solicitacoes").select("*").execute()
        res_hist = db.table("historico").select("*").execute()
        
        df = pd.DataFrame(res_sol.data)
        df_hist = pd.DataFrame(res_hist.data)

        if df.empty:
            st.info("Aguardando dados para consolidar indicadores.")
            return

        # Tratamento de datas
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['data_validacao'] = pd.to_datetime(df['data_validacao'])
        
        # --- 2. FILTROS ESTRATÉGICOS (SIDEBAR) ---
        st.sidebar.header("🎯 Filtros de Gestão")
        
        data_inicio = st.sidebar.date_input("Início", df['created_at'].min())
        data_fim = st.sidebar.date_input("Fim", datetime.now())
        
        transp_lista = ["Todos"] + sorted(df['solicitante_email'].unique().tolist())
        transp_sel = st.sidebar.selectbox("Transportador", transp_lista)

        # Aplicação dos filtros
        mask = (df['created_at'].dt.date >= data_inicio) & (df['created_at'].dt.date <= data_fim)
        if transp_sel != "Todos":
            mask &= (df['solicitante_email'] == transp_sel)
        
        df_view = df.loc[mask].copy()

        # --- 3. KPIs DE ALTO NÍVEL ---
        c1, c2, c3, c4 = st.columns(4)
        
        total_aprovado = df_view[df_view['status'].isin(['Aprovado', 'Finalizado'])]['valor'].sum()
        c1.metric("Total Aprovado", f"R$ {total_aprovado:,.2f}")

        # Cálculo de SLA Médio (Envio -> Validação) em Horas
        df_sla = df_view.dropna(subset=['data_validacao'])
        if not df_sla.empty:
            df_view['sla_hrs'] = (df_view['data_validacao'] - df_view['created_at']).dt.total_seconds() / 3600
            sla_medio = df_view['sla_hrs'].mean()
            c2.metric("SLA Médio (Ciclo)", f"{sla_medio:.1f} horas")
        else:
            c2.metric("SLA Médio (Ciclo)", "---")

        pendentes = len(df_view[df_view['status'] == 'Aberto'])
        c3.metric("Notas em Fila", pendentes, delta=f"{pendentes} aguardando", delta_color="inverse")
        
        taxa_recusa = (len(df_view[df_view['status'] == 'Recusada']) / len(df_view)) * 100
        c4.metric("Taxa de Recusa", f"{taxa_recusa:.1f}%")

        st.divider()

        # --- 4. VISÃO FINANCEIRA (PARETO E DISTRIBUIÇÃO) ---
        col_fin1, col_fin2 = st.columns([2, 1])

        with col_fin1:
            st.subheader("💰 Gastos por Transportador e Tipo")
            fig_bar = px.bar(df_view, x="solicitante_email", y="valor", color="tipo_custo",
                            title="Volume Financeiro Acumulado", barmode="stack",
                            color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_fin2:
            st.subheader("🍕 Mix de Custos")
            fig_pie = px.pie(df_view, values='valor', names='tipo_custo', hole=0.5,
                            color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- 5. VISÃO DE SLA E PERFORMANCE ---
        st.divider()
        st.subheader("⏱️ Torre de Controle - SLA por Solicitação")
        
        # Criando um gráfico de dispersão para identificar outliers de tempo
        if not df_sla.empty:
            fig_sla = px.scatter(df_view.dropna(subset=['sla_hrs']), 
                                x="created_at", y="sla_hrs", color="status",
                                size="valor", hover_name="numero_nf",
                                title="Tempo de Resposta (Hrs) por Data de Criação",
                                labels={"sla_hrs": "Horas para Validar", "created_at": "Data Criada"})
            st.plotly_chart(fig_sla, use_container_width=True)

        # --- 6. TABELA EXECUTIVA (DETALHAMENTO) ---
        with st.expander("📄 Ver Detalhes Consolidados e Exportar"):
            # Preparando DataFrame para Exportação
            df_export = df_view[[
                'numero_nf', 'cliente', 'solicitante_email', 'tipo_custo', 
                'valor', 'status', 'created_at', 'validador_email'
            ]].copy()
            
            st.dataframe(
                df_export,
                column_config={
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "created_at": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm")
                },
                hide_index=True, use_container_width=True
            )
            
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Relatório Excel (CSV)", csv, "relatorio_gestao_linea.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro ao processar indicadores: {e}")