import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import pymysql
from pathlib import Path

def create_mysql_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="gokuld1",
            password="guvi",
            database="stock_analysis",
            charset='utf8mb4',
            ssl={'fake_flag_to_enable_tls': True},
            ssl_verify_cert=False
        )
        return connection
    except pymysql.Error as err:
        st.error(f"Error connecting to MySQL: {err}")
        return None

def main():
    st.set_page_config(page_title="Stock Market Analysis", layout="wide")

    tabs = st.tabs([
        "Correlation Matrix",
        "Volatility Analysis",
        "Cumulative Returns", 
        "Monthly Performance",
        "Sector Performance"
    ])

    connection = create_mysql_connection()
    if not connection:
        st.error("Failed to connect to database")
        return

    try:
        with tabs[0]:
            st.title("Stock Returns Correlation Matrix")
            st.subheader("Period: November 2023 - November 2024")

            correlation_data = pd.read_sql("""
                SELECT * FROM correlation_analysis
            """, connection)

            corr_matrix = correlation_data.pivot(
                index='Stock_A',
                columns='Stock_B',
                values='Correlation'
            )

            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale='RdBu',
                zmin=-1,
                zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate='%{text:.2f}'
            ))
            
            fig.update_layout(
                height=800,
                xaxis={'tickangle': 45},
                yaxis={'tickangle': 0},
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            st.title("Top 10 Most Volatile Stocks")
            st.subheader("Period: November 2023 - November 2024")

            volatility_data = pd.read_sql("""
                SELECT Ticker, Annualized_Volatility 
                FROM volatility_analysis 
                ORDER BY Annualized_Volatility DESC 
                LIMIT 10
            """, connection)
            
            fig = px.bar(
                volatility_data,
                x='Ticker',
                y='Annualized_Volatility',
                text=volatility_data['Annualized_Volatility'].apply(lambda x: f"{x:.1f}%")
            )
            
            fig.update_layout(
                height=600,
                yaxis_title="Annualized Volatility",
                xaxis_title="Stock Ticker",
                plot_bgcolor='white',
                yaxis=dict(gridcolor='lightgrey', gridwidth=0.5),
                xaxis=dict(gridcolor='lightgrey', gridwidth=0.5),
                bargap=0.4
            )
            
            fig.update_traces(
                marker_color='#2196F3',
                textposition='outside'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with tabs[2]:
            st.title("Cumulative Returns of Top 5 Performing Stocks")
            st.subheader("Period: November 2023 - November 2024")

            returns_query = """
            SELECT 
                Trading_Date,
                Ticker,
                Cumulative_Return
            FROM cumulative_returns_daily
            WHERE Trading_Date BETWEEN '2023-11-01' AND '2024-11-30'
            ORDER BY Trading_Date
            """
            returns_data = pd.read_sql(returns_query, connection)

            latest_returns = returns_data.loc[returns_data.groupby('Ticker')['Trading_Date'].idxmax()]
            top_5_stocks = latest_returns.nlargest(5, 'Cumulative_Return')

            fig = go.Figure()
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for idx, (_, stock_data) in enumerate(top_5_stocks.iterrows()):
                ticker = stock_data['Ticker']
                stock_returns = returns_data[returns_data['Ticker'] == ticker]
                
                fig.add_trace(go.Scatter(
                    x=stock_returns['Trading_Date'],
                    y=stock_returns['Cumulative_Return'] * 100,
                    name=f"{ticker} ({stock_data['Cumulative_Return']*100:.1f}%)",
                    line=dict(color=colors[idx], width=2)
                ))
            
            fig.update_layout(
                height=600,
                yaxis_title="Cumulative Return (%)",
                xaxis_title="Date",
                plot_bgcolor='white',
                yaxis=dict(gridcolor='lightgrey', gridwidth=0.5),
                xaxis=dict(gridcolor='lightgrey', gridwidth=0.5),
                legend=dict(
                    x=1.02,
                    y=1,
                    title="Stock (Total Return)",
                    bgcolor='rgba(255, 255, 255, 0.8)'
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with tabs[3]:
            st.title("Monthly Top 5 Gainers and Losers")
            st.subheader("Period: November 2023 - November 2024")

            monthly_data = pd.read_sql("""
                SELECT 
                    DATE_FORMAT(Month_Date, '%Y-%m') as Month,
                    Category,
                    Ranking,
                    Ticker,
                    Monthly_Return
                FROM monthly_performance
                ORDER BY Month_Date, Ranking
            """, connection)

            cols = st.columns(3)
            months = sorted(monthly_data['Month'].unique())
            
            for idx, month in enumerate(months):
                with cols[idx % 3]:
                    month_display = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
                    st.subheader(month_display)
                    
                    month_data = monthly_data[monthly_data['Month'] == month]
                    
                    fig = px.bar(
                        month_data,
                        x='Ticker',
                        y='Monthly_Return',
                        text=month_data['Monthly_Return'].apply(lambda x: f"{x:.1f}%"),
                        color='Monthly_Return',
                        color_continuous_scale=['red', 'green']
                    )
                    
                    fig.update_layout(
                        height=300,
                        showlegend=False,
                        plot_bgcolor='white',
                        yaxis=dict(
                            gridcolor='lightgrey',
                            gridwidth=0.5,
                            title="Return (%)"
                        ),
                        xaxis=dict(
                            gridcolor='lightgrey',
                            gridwidth=0.5,
                            title=""
                        ),
                        margin=dict(t=30, l=30, r=20, b=30)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

        with tabs[4]:
            st.title("Sector-wise Performance")
            st.subheader("Period: November 2023 - November 2024")

            sector_data = pd.read_sql("""
                SELECT * FROM sector_performance 
                ORDER BY Average_Return DESC
            """, connection)
            
            fig = px.bar(
                sector_data,
                x='Sector',
                y='Average_Return',
                text=sector_data['Average_Return'].apply(lambda x: f"{x:.1f}%"),
                color='Average_Return',
                color_continuous_scale=['red', 'gray', 'green']
            )
            
            fig.update_layout(
                height=600,
                yaxis_title="Average Return (%)",
                xaxis_title="Sector",
                plot_bgcolor='white',
                yaxis=dict(gridcolor='lightgrey', gridwidth=0.5),
                xaxis=dict(gridcolor='lightgrey', gridwidth=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    finally:
        connection.close()

if __name__ == "__main__":
    main()
