import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

def get_connection():
    return sqlite3.connect('monitoring.sqlite', check_same_thread=False)

def render_monitoring_dashboard():
    st.markdown("""
        <div style='background: rgba(114, 103, 239, 0.1); padding: 20px; border-radius: 10px; border-left: 5px solid #7267EF; margin-bottom: 20px;'>
            <h2 style='margin: 0; color: #ffff;'>📊 Integrated Monitoring & Observability Hub</h2>
            <p style='margin: 5px 0 0 0; color: #e2e8f0;'>Real-time tracking of agent performance, costs, and system accuracy metrics.</p>
        </div>
    """, unsafe_allow_html=True)

    try:
        conn = get_connection()
        
        # 1. Global Metrics (Top Row)
        col1, col2, col3, col4 = st.columns(4)
        
        # Total Requests
        total_reqs = pd.read_sql("SELECT COUNT(*) FROM request_metrics", conn).iloc[0,0]
        col1.metric("Total Requests", total_reqs)
        
        # Success Rate
        success_rate = pd.read_sql("SELECT AVG(success) * 100 FROM request_metrics", conn).iloc[0,0] or 0
        col2.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Cache Hit Rate
        cache_rate = pd.read_sql("SELECT AVG(from_vault) * 100 FROM request_metrics", conn).iloc[0,0] or 0
        col3.metric("Vault Hit Rate", f"{cache_rate:.1f}%")
        
        # Avg Latency
        avg_lat = pd.read_sql("SELECT AVG(total_latency) FROM request_metrics", conn).iloc[0,0] or 0
        col4.metric("Avg Latency", f"{avg_lat:.2f}s")

        st.markdown("---")

        # 2. Latency Breakdown by Agent
        st.subheader("⏱️ Agent Performance Breakdown")
        agent_stats = pd.read_sql("""
            SELECT node_name, AVG(latency) as avg_lat, COUNT(*) as call_count 
            FROM agent_traces 
            GROUP BY node_name 
            ORDER BY avg_lat DESC
        """, conn)
        
        if not agent_stats.empty:
            fig_lat = px.bar(
                agent_stats, 
                x="node_name", 
                y="avg_lat", 
                title="Average Latency per Agent Node (Seconds)",
                color="avg_lat",
                color_continuous_scale="Viridis",
                labels={"avg_lat": "Latency (s)", "node_name": "Agent Node"}
            )
            st.plotly_chart(fig_lat, use_container_width=True)
        else:
            st.info("No agent traces recorded yet. Run some queries to see the charts!")

        # 3. Evaluation History
        st.markdown("---")
        st.subheader("🎯 Offline Evaluation Metrics (SQL Accuracy)")
        eval_df = pd.read_sql("SELECT * FROM eval_history ORDER BY timestamp DESC", conn)
        
        if not eval_df.empty:
            # Latency over time
            fig_eval = px.line(
                eval_df, 
                x="timestamp", 
                y=["exact_match_score", "execution_match_score"],
                title="SQL Accuracy Trends (Offline Evals)",
                markers=True,
                labels={"value": "Score (%)", "timestamp": "Deployment Date"}
            )
            st.plotly_chart(fig_eval, use_container_width=True)
            
            with st.expander("📂 View Full Evaluation History"):
                st.dataframe(eval_df, use_container_width=True)
        else:
            st.warning("No offline evaluation runs found. Run 'python tests/evals/eval_runner.py' to generate initial benchmarks.")

        # 4. Recent Traces Table
        st.markdown("---")
        st.subheader("🔍 Recent Request Traces")
        recent_traces = pd.read_sql("""
            SELECT r.request_id, r.timestamp, r.total_latency, r.success, r.retry_count, 
                   (SELECT COUNT(*) FROM agent_traces a WHERE a.request_id = r.request_id) as steps
            FROM request_metrics r
            ORDER BY r.timestamp DESC
            LIMIT 10
        """, conn)
        
        if not recent_traces.empty:
            st.dataframe(recent_traces, use_container_width=True)
            
            selected_rid = st.selectbox("Select Request ID to Inspect Agent Path:", recent_traces['request_id'].tolist())
            if selected_rid:
                path_df = pd.read_sql(f"""
                    SELECT node_name, status, latency, error_message, metadata 
                    FROM agent_traces 
                    WHERE request_id = '{selected_rid}' 
                    ORDER BY start_time ASC
                """, conn)
                st.table(path_df)
        
        # --- DANGER ZONE ---
        st.markdown("---")
        with st.expander("🗑️ Admin: Reset Monitoring Hub", expanded=False):
            st.warning("This will permanently delete all agent traces, request metrics, and evaluation history.")
            if st.button("🔴 Wipe All Hub Statistics", use_container_width=True, help="Clears monitoring.sqlite tables"):
                try:
                    import requests
                    res = requests.post("http://localhost:8000/monitoring/reset")
                    if res.status_code == 200:
                        st.success("✅ Monitoring Hub Reset Successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to reset monitoring.")
                except Exception as e:
                    st.error(f"Error: {e}")

        conn.close()

    except Exception as e:
        st.error(f"Monitoring DB Error: {e}")
        st.info("The monitoring database will be created automatically after the first query execution.")

if __name__ == "__main__":
    render_monitoring_dashboard()
