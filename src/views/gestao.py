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
    st.caption("Linea Alimentos | Visão Estratégica e Controle de SLA em Dias")

    # --- 1. CARREGAMENTO DE DADOS ---
    try:
        res_sol = db.table("solicitacoes").select("*").execute()
        df = pd.DataFrame(res_sol.data)

        if df.empty:
            st.info("Aguardando dados para consolidar indicadores.")
            return

        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        df['data_validacao'] = pd.to_datetime(df['data_validacao'], utc=True)
        
        # --- 2. FILTROS ESTRATÉGICOS ---
        st.sidebar.header("🎯 Filtros de Gestão")
        min_date = df['created_at'].min().date() if not df.empty else datetime.now().date()
        data_inicio = st.sidebar.date_input("Início", min_date)
        data_fim = st.sidebar.date_input("Fim", datetime.now().date())
        
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

        # ALTERAÇÃO: Cálculo de SLA em DIAS (divisor 86400)
        df_view['sla_dias'] = (df_view['data_validacao'] - df_view['created_at']).dt.total_seconds() / 86400
        sla_medio = df_view['sla_dias'].mean()
        c2.metric("SLA Médio (Ciclo)", f"{sla_medio:.2f} dias" if not pd.isna(sla_medio) else "---")

        pendentes = len(df_view[df_view['status'] == 'Aberto'])
        c3.metric("Notas em Fila", pendentes, delta=f"{pendentes} aguardando", delta_color="inverse")
        
        taxa_recusa = (len(df_view[df_view['status'] == 'Recusada']) / len(df_view)) * 100 if len(df_view) > 0 else 0
        c4.metric("Taxa de Recusa", f"{taxa_recusa:.1f}%")

        st.divider()

        # --- 4. TOP 5 GARGALOS ---
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

        # --- 6. TORRE DE CONTROLE INTERATIVA (SLA EM DIAS) ---
        st.divider()
        st.subheader("⏱️ Torre de Controle - SLA por Solicitação (Escala em Dias)")
        
        # Eixo Y agora usa 'sla_dias'
        fig_sla = px.scatter(df_view, x="created_at", y="sla_dias", color="status",
                            size="valor", hover_name="numero_nf",
                            labels={"sla_dias": "Dias para Conclusão", "created_at": "Data de Abertura"},
                            title="Análise de Lead Time (Alvo: 2 dias)")
        
        # ALTERAÇÃO: Meta agora é 2 dias (48 horas)
        fig_sla.add_hline(y=2, line_dash="dot", line_color="red", 
                          annotation_text="Meta 48h (2 dias)", annotation_position="top left")
        
        # ALTERAÇÃO: Forçando o eixo X a mostrar marcações diárias
        fig_sla.update_xaxes(
            dtick="D1",  # Marcação a cada 1 dia
            tickformat="%d/%m", # Formato Dia/Mês
            title="Dias de Operação"
        )
        
        fig_sla.update_yaxes(title="Dias Decorridos")
        
        st.plotly_chart(fig_sla, use_container_width=True)

        # --- 7. DRILL-DOWN ---
        st.subheader("📑 Detalhamento Interativo")
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
                st.markdown(f"### 📜 Histórico da NF: {row['numero_nf']}")
                
                # Busca Histórico Real no Banco
                hist = db.table("historico").select("*").eq("solicitacao_id", row['id']).order("created_at").execute()
                
                if hist.data:
                    for h in hist.data:
                        # Converte data para fuso local (Brasília)
                        data_local = pd.to_datetime(h['created_at'], utc=True).tz_convert('America/Sao_Paulo')
                        
                        st.write(f"🕒 {data_local.strftime('%d/%m %H:%M')}")
                        
                        # USANDO OS NOMES REAIS DAS COLUNAS: status_na_epoca e observacao
                        status = h.get('status_na_epoca', 'N/A')
                        obs = h.get('observacao', 'Sem observação')
                        user = h.get('usuario_email', 'Sistema')

                        st.markdown(f"**{status}**")
                        st.caption(f"💬 {obs}")
                        st.caption(f"👤 *Por: {user}*")
                        st.divider()
                else:
                    st.info("Sem trilha de auditoria para esta nota.")
            else:
                st.info("👈 Selecione uma nota na tabela para ver a linha do tempo.")

    except Exception as e:
        st.error(f"Erro na gestão: {e}")