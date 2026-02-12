import streamlit as st
import pandas as pd
import plotly.express as px
from src.database import db
from datetime import datetime

def render():
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        div[data-testid="stMetricValue"] { font-size: 24px; color: #002D58; }
        .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Business Intelligence - Gestão de Custos Extras")
    st.caption("Linea Alimentos | Visão Estratégica e Controle de SLA")

    # --- 1. CARREGAMENTO DE DADOS ---
    try:
        res_sol = db.table("solicitacoes").select("*").execute()
        df = pd.DataFrame(res_sol.data)

        if df.empty:
            st.info("Aguardando dados para consolidar indicadores.")
            return

        df['created_at'] = pd.to_datetime(df['created_at'])
        df['data_validacao'] = pd.to_datetime(df['data_validacao'])
        
        # --- 2. FILTROS ESTRATÉGICOS ---
        st.sidebar.header("🎯 Filtros de Gestão")
        data_inicio = st.sidebar.date_input("Início", df['created_at'].min())
        data_fim = st.sidebar.date_input("Fim", datetime.now())
        
        transp_lista = ["Todos"] + sorted(df['solicitante_email'].unique().tolist())
        transp_sel = st.sidebar.selectbox("Transportador", transp_lista)

        mask = (df['created_at'].dt.date >= data_inicio) & (df['created_at'].dt.date <= data_fim)
        if transp_sel != "Todos":
            mask &= (df['solicitante_email'] == transp_sel)
        
        df_view = df.loc[mask].copy()

        # --- 3. KPIs DE ALTO NÍVEL ---
        c1, c2, c3, c4 = st.columns(4)
        
        total_aprovado = df_view[df_view['status'].isin(['Aprovado', 'Finalizado'])]['valor'].sum()
        c1.metric("Total Aprovado", f"R$ {total_aprovado:,.2f}")

        # Cálculo de SLA
        df_view['sla_hrs'] = (df_view['data_validacao'] - df_view['created_at']).dt.total_seconds() / 3600
        sla_medio = df_view['sla_hrs'].mean()
        c2.metric("SLA Médio (Ciclo)", f"{sla_medio:.1f} hrs" if not pd.isna(sla_medio) else "---")

        pendentes = len(df_view[df_view['status'] == 'Aberto'])
        c3.metric("Notas em Fila", pendentes, delta=f"{pendentes} aguardando", delta_color="inverse")
        
        taxa_recusa = (len(df_view[df_view['status'] == 'Recusada']) / len(df_view)) * 100 if len(df_view) > 0 else 0
        c4.metric("Taxa de Recusa", f"{taxa_recusa:.1f}%")

        st.divider()

        # --- 4. TOP 5 GARGALOS (SINTETIZAÇÃO) ---
        st.subheader("⚠️ Top 5 Gargalos (Transportadores com mais Recusas)")
        df_recusadas = df_view[df_view['status'] == 'Recusada']
        if not df_recusadas.empty:
            top_recusas = df_recusadas['solicitante_email'].value_counts().head(5).reset_index()
            top_recusas.columns = ['Transportador', 'Qtd Recusas']
            st.table(top_recusas)
        else:
            st.success("Nenhuma recusa crítica identificada no período.")

        # --- 5. VISÃO FINANCEIRA ---
        col_fin1, col_fin2 = st.columns([2, 1])
        with col_fin1:
            fig_bar = px.bar(df_view, x="solicitante_email", y="valor", color="tipo_custo",
                            title="Volume Financeiro Acumulado", barmode="stack",
                            color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_bar, use_container_width=True)
        with col_fin2:
            fig_pie = px.pie(df_view, values='valor', names='tipo_custo', hole=0.5, title="Mix de Custos")
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- 6. TORRE DE CONTROLE INTERATIVA (SLA) ---
        st.divider()
        st.subheader("⏱️ Torre de Controle - SLA por Solicitação")
        
        fig_sla = px.scatter(df_view, x="created_at", y="sla_hrs", color="status",
                            size="valor", hover_name="numero_nf",
                            title="Análise de Lead Time (Bolinha acima da linha = Fora da Meta)")
        fig_sla.add_hline(y=24, line_dash="dot", line_color="red", annotation_text="Meta 24h")
        st.plotly_chart(fig_sla, use_container_width=True)

        # --- 7. DRILL-DOWN: SELEÇÃO E HISTÓRICO ---
        st.subheader("📑 Detalhamento Interativo")
        st.caption("Clique em uma linha para investigar o histórico da NF.")
        
        col_list, col_hist = st.columns([1.5, 1])
        
        with col_list:
            selecao = st.dataframe(
                df_view[['id', 'numero_nf', 'solicitante_email', 'valor', 'status']],
                column_config={
                    "id": None,
                    "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
                },
                hide_index=True, use_container_width=True,
                on_select="rerun", selection_mode="single-row"
            )

        with col_hist:
            if selecao.selection.rows:
                idx = selecao.selection.rows[0]
                row = df_view.iloc[idx]
                st.markdown(f"**NF: {row['numero_nf']}**")
                
                # Busca Histórico Real no Banco
                hist = db.table("historico").select("*").eq("solicitacao_id", row['id']).order("created_at").execute()
                if hist.data:
                    for h in hist.data:
                        st.write(f"🕒 {pd.to_datetime(h['created_at']).strftime('%d/%m %H:%M')}")
                        st.caption(f"**{h['status']}**: {h['descricao']}")
                        st.divider()
                else:
                    st.info("Sem histórico registrado.")
            else:
                st.info("👈 Selecione uma nota para ver a trilha de auditoria.")

    except Exception as e:
        st.error(f"Erro na gestão: {e}")