from __future__ import annotations

import pandas as pd
import streamlit as st


def render_costs_page(db) -> None:
    st.header("Cost Dashboard")

    rows = db.get_cost_rows()
    cost_df = pd.DataFrame(rows)
    if cost_df.empty:
        st.info("No cost data yet. Process at least one file to see metrics.")
        return

    cost_df["timestamp"] = pd.to_datetime(cost_df["timestamp"], errors="coerce", utc=True)
    cost_df = cost_df.dropna(subset=["timestamp"]).copy()
    if cost_df.empty:
        st.info("No valid cost timestamps found.")
        return

    cost_df["date"] = cost_df["timestamp"].dt.date
    min_date = cost_df["date"].min()
    max_date = cost_df["date"].max()

    start_col, end_col = st.columns(2)
    start_date = start_col.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = end_col.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.error("Start date must be before end date")
        return

    filtered = cost_df[(cost_df["date"] >= start_date) & (cost_df["date"] <= end_date)].copy()

    total_cost = float(filtered["cost_usd"].sum())
    total_tokens = int(filtered["total_tokens"].sum())

    c1, c2 = st.columns(2)
    c1.metric("Total Cost (USD)", f"${total_cost:.6f}")
    c2.metric("Total Tokens", f"{total_tokens}")

    st.subheader("By Operation")
    by_op = (
        filtered.groupby("operation_type", as_index=False)["cost_usd"]
        .sum()
        .rename(columns={"operation_type": "operation"})
    )
    st.dataframe(by_op, use_container_width=True)
    if not by_op.empty:
        st.bar_chart(by_op.set_index("operation")["cost_usd"])

    st.subheader("Cost Per File")
    file_df = pd.DataFrame(db.get_cost_per_file())
    if not file_df.empty:
        st.dataframe(file_df, use_container_width=True)

    st.subheader("Cost Over Time")
    day_df = (
        filtered.groupby(filtered["timestamp"].dt.date, as_index=False)["cost_usd"]
        .sum()
        .rename(columns={"timestamp": "day", "cost_usd": "total_cost_usd"})
    )
    day_df.columns = ["day", "total_cost_usd"]
    if not day_df.empty:
        st.line_chart(day_df.set_index("day")["total_cost_usd"])

    st.subheader("Operation Trend Over Time")
    op_trend = (
        filtered.groupby([filtered["timestamp"].dt.date, "operation_type"], as_index=False)["cost_usd"]
        .sum()
        .rename(columns={"timestamp": "day"})
    )
    op_trend.columns = ["day", "operation_type", "cost_usd"]
    if not op_trend.empty:
        pivot = op_trend.pivot(index="day", columns="operation_type", values="cost_usd").fillna(0.0)
        st.line_chart(pivot)
