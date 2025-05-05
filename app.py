import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Set page configuration
st.set_page_config(
    page_title="Sri Lanka Economic & Demographic Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve UI
st.markdown("""
<style>
    .main-header {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
}
.section-header {
    font-size: 1.8rem;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}
.subsection-header {
    font-size: 1.4rem;
    font-weight: 500;
    color: #374151;  /* Darker gray for better contrast */
    margin-top: 0.8rem;
    margin-bottom: 0.3rem;
}
.card {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.18), 0 1px 2px rgba(0,0,0,0.32);  /* Slightly stronger shadow */
}
.insight-card {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid #2563EB;  /* Keeping this blue as it's already high contrast */
}
.stMetric {
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.6);  /* Slightly stronger shadow */
}
.stSelectbox, .stSlider {
    margin-bottom: 1rem;
}
.stPlotlyChart {
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);  /* Slightly stronger shadow */
    padding: 0.5rem;
    background-color: white;
}
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    data = pd.read_csv('lka_processed.csv')
    # Convert column names to lowercase for consistency
    data.columns = [col.lower() for col in data.columns]
    return data

df = load_data()

# Create a year column from time_period if it exists
if 'time_period' in df.columns:
    # Extract year from time_period (e.g., "1970-Q1" -> 1970)
    df['year_only'] = df['time_period'].str.split('-').str[0].astype(int)
else:
    # If there's already a year column, use it
    df['year_only'] = df['year']

# Create a sidebar for navigation
st.sidebar.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Navigation</h1>", unsafe_allow_html=True)
pages = st.sidebar.radio("", ["Overview", "Economic Indicators", "Demographic Indicators", "Correlations & Relationships", "Data Explorer", "About"])

# Time period filter
st.sidebar.markdown("<div class='section-header'>Filters</div>", unsafe_allow_html=True)
years = sorted(df['year_only'].unique())
selected_years = st.sidebar.slider(
    "Select Year Range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

# Apply year filter to all dataframes
filtered_df = df[(df['year_only'] >= selected_years[0]) & (df['year_only'] <= selected_years[1])]

# For quarterly data, create a version with annual averages for annual charts
annual_df = filtered_df.groupby('year_only').agg({
    'ny.gdp.mktp.cd': 'mean',
    'sp.dyn.le00.in': 'mean',
    'sp.pop.grow': 'mean',
    'sp.dyn.tfrt.in': 'mean', 
    'sp.rur.totl.zs': 'mean',  # Rural population
    'sh.dyn.aids.zs': 'mean',  # HIV prevalence
    'ny.gdp.defl.zs': 'mean',  # GDP deflator
    'dt.tds.dect.gn.zs': 'mean',  # Debt service
    'pa.nus.fcrf': 'mean'  # Exchange rate
}).reset_index()

# Calculate GDP growth rate
if 'ny.gdp.mktp.cd' in annual_df.columns:
    annual_df['gdp_growth_pct'] = annual_df['ny.gdp.mktp.cd'].pct_change() * 100

# Dashboard title and description section
def show_overview():
    st.markdown("<div class='main-header'>Sri Lanka Economic & Demographic Dashboard</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    This interactive dashboard provides comprehensive insights into Sri Lanka's economic and demographic 
    indicators from 1970 to 2022, allowing you to analyze trends, correlations, and key development metrics.
    
    Navigate through different sections using the sidebar menu, and apply filters to focus on specific time periods.
    Each visualization is interactive - hover for details, click legends to filter, and use the toolbar to zoom or download charts.
    </div>
    """, unsafe_allow_html=True)
    
    # Get the latest year's data for key metrics
    latest_year = filtered_df['year_only'].max()
    latest_data = filtered_df[filtered_df['year_only'] == latest_year]
    
    # Handle possibility of empty data
    if len(latest_data) > 0:
        latest_row = latest_data.iloc[-1]
        
        # Key metrics
        st.markdown("<div class='section-header'>Key Metrics (Latest Available Data)</div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'ny.gdp.mktp.cd' in filtered_df.columns:
                latest_gdp = latest_row['ny.gdp.mktp.cd']
                st.metric("GDP (US$)", f"${latest_gdp/1e9:.2f} billion")
        
        with col2:
            if 'sp.dyn.le00.in' in filtered_df.columns:
                latest_life_exp = latest_row['sp.dyn.le00.in']
                st.metric("Life Expectancy", f"{latest_life_exp:.1f} years")
        
        with col3:
            if 'sp.pop.grow' in filtered_df.columns:
                latest_pop_growth = latest_row['sp.pop.grow']
                st.metric("Population Growth", f"{latest_pop_growth:.2f}%")
                
        with col4:
            if 'sp.dyn.tfrt.in' in filtered_df.columns:
                latest_fertility = latest_row['sp.dyn.tfrt.in']
                st.metric("Fertility Rate", f"{latest_fertility:.2f} births per woman")
    else:
        st.warning("No data available for the selected time period.")
    
    # Key insights section
    st.markdown("<div class='section-header'>Key Insights</div>", unsafe_allow_html=True)
    
    # Calculate insights from the data if data is available
    if len(annual_df) > 1:  # Need at least 2 data points for growth
        # Only calculate if column exists
        if 'ny.gdp.mktp.cd' in annual_df.columns:
            gdp_growth = annual_df['ny.gdp.mktp.cd'].pct_change().dropna()
            avg_gdp_growth = gdp_growth.mean() * 100
        else:
            avg_gdp_growth = "N/A"
        
        # Only calculate if columns exist
        if 'sp.dyn.le00.in' in annual_df.columns and len(annual_df['sp.dyn.le00.in']) > 0:
            life_exp_change = annual_df['sp.dyn.le00.in'].iloc[-1] - annual_df['sp.dyn.le00.in'].iloc[0]
        else:
            life_exp_change = "N/A"
        
        # Only calculate if columns exist
        if 'sp.dyn.tfrt.in' in annual_df.columns and len(annual_df['sp.dyn.tfrt.in']) > 0:
            fertility_change = annual_df['sp.dyn.tfrt.in'].iloc[-1] - annual_df['sp.dyn.tfrt.in'].iloc[0]
        else:
            fertility_change = "N/A"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class='insight-card'>
                <strong>Economic Development:</strong> Sri Lanka's GDP has grown at an average rate of {avg_gdp_growth if isinstance(avg_gdp_growth, str) else f"{avg_gdp_growth:.2f}%"} annually 
                over the selected period, with significant volatility during economic crises and the civil war period.
            </div>
            
            <div class='insight-card'>
                <strong>Life Expectancy Gains:</strong> Life expectancy has increased by {life_exp_change if isinstance(life_exp_change, str) else f"{life_exp_change:.1f} years"}
                over the selected period, reflecting improvements in healthcare and living conditions.
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='insight-card'>
                <strong>Demographic Transition:</strong> The fertility rate has {f"decreased by {abs(fertility_change):.1f} births per woman" if isinstance(fertility_change, float) and fertility_change < 0 else f"changed by {fertility_change if isinstance(fertility_change, str) else f'{fertility_change:.1f}'} births per woman"},
                indicating Sri Lanka's progression through the demographic transition.
            </div>
            
            <div class='insight-card'>
                <strong>Economic Challenges:</strong> Recent data shows signs of economic stress, with fluctuating exchange rates
                and increasing debt service as a percentage of GNI, particularly evident since 2019.
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Insufficient data available for analysis. Please expand the selected time period.")
    
    # Overall economic trend visualization - only if data exists
    if 'ny.gdp.mktp.cd' in annual_df.columns:
        st.markdown("<div class='section-header'>Economic Overview (1970-Present)</div>", unsafe_allow_html=True)
        
        # Create GDP trend plot with recession highlights
        fig = px.line(
            annual_df, 
            x='year_only', 
            y='ny.gdp.mktp.cd',
            title='Sri Lanka GDP Trend (Current US$)',
            labels={'ny.gdp.mktp.cd': 'GDP (US$)', 'year_only': 'Year'}
        )
        
        # Highlight key economic events
        events = [
            {"year": 1977, "event": "Economic liberalization"},
            {"year": 1983, "event": "Start of civil conflict"},
            {"year": 2004, "event": "Indian Ocean tsunami"},
            {"year": 2009, "event": "End of civil war"},
            {"year": 2019, "event": "Easter bombings"},
            {"year": 2020, "event": "COVID-19 pandemic"},
            {"year": 2022, "event": "Economic crisis"}
        ]
        
        for event in events:
            if event["year"] >= selected_years[0] and event["year"] <= selected_years[1]:
                fig.add_vline(
                    x=event["year"], 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text=event["event"],
                    annotation_position="top right"
                )
        
        fig.update_layout(
            height=500,
            hovermode="x unified",
            xaxis_title="Year",
            yaxis_title="GDP (Current US$)",
            legend_title="Indicator",
            font=dict(family="Arial", size=12),
            plot_bgcolor='rgba(255,255,255,1)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(230,230,230,1)',
                showline=True,
                linewidth=1,
                linecolor='rgba(0,0,0,0.5)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(230,230,230,1)',
                showline=True,
                linewidth=1,
                linecolor='rgba(0,0,0,0.5)'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Economic indicators section
def show_economic_indicators():
    st.markdown("<div class='main-header'>Economic Indicators</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    Explore Sri Lanka's key economic indicators including GDP growth, exchange rates, and debt service ratios.
    These metrics provide insights into the country's economic development, challenges, and opportunities over time.
    </div>
    """, unsafe_allow_html=True)
    
    # GDP Growth Rate Analysis
    st.markdown("<div class='section-header'>GDP Growth & Volatility</div>", unsafe_allow_html=True)
    
    # Add GDP Growth Rate calculation if it doesn't exist
    if 'gdp_growth_pct' not in annual_df.columns and 'ny.gdp.mktp.cd' in annual_df.columns:
        annual_df['gdp_growth_pct'] = annual_df['ny.gdp.mktp.cd'].pct_change() * 100
    
    # Create subplot with GDP growth and its volatility
    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=("Annual GDP Growth Rate (%)", "5-Year Rolling Volatility (Std Dev)"),
        shared_xaxes=True,
        vertical_spacing=0.15
    )
    
    # Add GDP growth trace
    fig.add_trace(
        go.Bar(
            x=annual_df['year_only'], 
            y=annual_df['gdp_growth_pct'],
            name="GDP Growth (%)",
            marker_color=annual_df['gdp_growth_pct'].apply(
                lambda x: 'rgba(55, 126, 184, 0.7)' if x >= 0 else 'rgba(228, 26, 28, 0.7)'
            )
        ),
        row=1, col=1
    )
    
    # Add rolling volatility line
    rolling_std = annual_df['gdp_growth_pct'].rolling(window=5).std()
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'],
            y=rolling_std,
            name="5-Year Volatility",
            line=dict(color='rgba(77, 175, 74, 1)', width=2)
        ),
        row=2, col=1
    )
    
    # Add horizontal line at zero for growth chart
    fig.add_shape(
        type="line", 
        x0=annual_df['year_only'].min(), 
        x1=annual_df['year_only'].max(),
        y0=0, y1=0,
        line=dict(color="black", width=1, dash="dot"),
        row=1, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=700,
        hovermode="x unified",
        showlegend=False,
        title_text="GDP Growth Rate and Economic Volatility",
        plot_bgcolor='rgba(255,255,255,1)'
    )
    
    # Update axes
    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_yaxes(title_text="Growth (%)", row=1, col=1)
    fig.update_yaxes(title_text="Standard Deviation", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Exchange Rate & Inflation
    st.markdown("<div class='section-header'>Exchange Rate & Inflation</div>", unsafe_allow_html=True)
    
    # Create subplot with Exchange Rate and GDP Deflator
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add exchange rate line
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'], 
            y=annual_df['pa.nus.fcrf'],
            name="Exchange Rate (LKR/USD)",
            line=dict(color='rgba(55, 126, 184, 1)', width=2)
        ),
        secondary_y=False
    )
    
    # Add GDP deflator line
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'], 
            y=annual_df['ny.gdp.defl.zs'],
            name="GDP Deflator (Base Year Varies)",
            line=dict(color='rgba(228, 26, 28, 1)', width=2)
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        hovermode="x unified",
        title_text="Exchange Rate and Inflation (GDP Deflator)",
        plot_bgcolor='rgba(255,255,255,1)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Update axes titles
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Exchange Rate (LKR per USD)", secondary_y=False)
    fig.update_yaxes(title_text="GDP Deflator", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Debt Service Analysis
    st.markdown("<div class='section-header'>Debt Service Ratio</div>", unsafe_allow_html=True)
    
    # Create debt service chart
    fig = px.area(
        annual_df, 
        x='year_only', 
        y='dt.tds.dect.gn.zs',
        title='Debt Service (% of GNI)',
        labels={'dt.tds.dect.gn.zs': 'Debt Service', 'year_only': 'Year'}
    )
    
    # Add a threshold line for warning level
    fig.add_hline(
        y=5, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Warning Level",
        annotation_position="bottom right"
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        hovermode="x unified",
        xaxis_title="Year",
        yaxis_title="Debt Service (% of GNI)",
        plot_bgcolor='rgba(255,255,255,1)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class='insight-card'>
        <strong>Economic Insight:</strong> Sri Lanka's debt service ratio has shown significant fluctuations 
        over time, with notable increases during periods of economic stress. When this ratio exceeds 5% 
        of GNI, it often indicates potential debt sustainability issues, as a larger portion of national income 
        is being directed to servicing debt rather than development priorities.
    </div>
    """, unsafe_allow_html=True)

# Demographic indicators section
def show_demographic_indicators():
    st.markdown("<div class='main-header'>Demographic Indicators</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    Explore Sri Lanka's demographic transition through key indicators like life expectancy, fertility rate, 
    population growth, and urbanization. These metrics reveal how the country's population structure has evolved over time.
    </div>
    """, unsafe_allow_html=True)
    
    # Life Expectancy & Fertility Rate
    st.markdown("<div class='section-header'>Life Expectancy & Fertility Rate</div>", unsafe_allow_html=True)
    
    # Create subplot with life expectancy and fertility rate
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add life expectancy line
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'], 
            y=annual_df['sp.dyn.le00.in'],
            name="Life Expectancy (years)",
            line=dict(color='rgba(55, 126, 184, 1)', width=2)
        ),
        secondary_y=False
    )
    
    # Add fertility rate line
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'], 
            y=annual_df['sp.dyn.tfrt.in'],
            name="Fertility Rate (births per woman)",
            line=dict(color='rgba(228, 26, 28, 1)', width=2)
        ),
        secondary_y=True
    )
    
    # Add replacement level fertility line
    fig.add_hline(
        y=2.1, 
        line_dash="dash", 
        line_color="orange",
        secondary_y=True,
        annotation_text="Replacement Level",
        annotation_position="bottom right"
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        hovermode="x unified",
        title_text="Life Expectancy and Fertility Rate Trends",
        plot_bgcolor='rgba(255,255,255,1)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Update axes titles
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Life Expectancy (years)", secondary_y=False)
    fig.update_yaxes(title_text="Fertility Rate (births per woman)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class='insight-card'>
        <strong>Demographic Insight:</strong> Sri Lanka has undergone a remarkable demographic transition, 
        with life expectancy steadily increasing while fertility rates have declined. The fertility rate has 
        now fallen below the replacement level of 2.1 births per woman, suggesting that Sri Lanka may face 
        challenges related to an aging population in the coming decades.
    </div>
    """, unsafe_allow_html=True)
    
    # Population Growth & Urbanization
    st.markdown("<div class='section-header'>Population Growth & Urbanization</div>", unsafe_allow_html=True)
    
    # Calculate urban population percentage
    annual_df['urban_population_pct'] = 100 - annual_df['sp.rur.totl.zs']
    
    # Create subplot with population growth and urbanization
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add population growth line
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'], 
            y=annual_df['sp.pop.grow'],
            name="Population Growth (%)",
            line=dict(color='rgba(55, 126, 184, 1)', width=2)
        ),
        secondary_y=False
    )
    
    # Add urbanization line
    fig.add_trace(
        go.Scatter(
            x=annual_df['year_only'], 
            y=annual_df['urban_population_pct'],
            name="Urban Population (%)",
            line=dict(color='rgba(77, 175, 74, 1)', width=2)
        ),
        secondary_y=True
    )
    
    # Add zero population growth line
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="red",
        secondary_y=False,
        annotation_text="Zero Growth",
        annotation_position="bottom right"
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        hovermode="x unified",
        title_text="Population Growth and Urbanization Trends",
        plot_bgcolor='rgba(255,255,255,1)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    # Update axes titles
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Population Growth (%)", secondary_y=False)
    fig.update_yaxes(title_text="Urban Population (%)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Health Indicators
    st.markdown("<div class='section-header'>Health Indicators</div>", unsafe_allow_html=True)
    
    # Calculate infant mortality rate trend
    if 'sp.dyn.imrt.in' in annual_df.columns:
        # Create infant mortality rate chart
        fig = px.line(
            annual_df, 
            x='year_only', 
            y='sp.dyn.imrt.in',
            title='Infant Mortality Rate (per 1,000 live births)',
            labels={'sp.dyn.imrt.in': 'Infant Mortality Rate', 'year_only': 'Year'}
        )
        
        # Update layout
        fig.update_layout(
            height=500,
            hovermode="x unified",
            xaxis_title="Year",
            yaxis_title="Infant Mortality Rate",
            plot_bgcolor='rgba(255,255,255,1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class='insight-card'>
            <strong>Health Insight:</strong> Sri Lanka has achieved remarkable progress in reducing infant mortality rates,
            which is often considered a key indicator of a country's healthcare system quality and overall development.
            This improvement aligns with the country's increased life expectancy and reflects successful public health initiatives.
        </div>
        """, unsafe_allow_html=True)

# Correlations and relationships section
def show_correlations():
    st.markdown("<div class='main-header'>Correlations & Relationships</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    Explore the relationships between key economic and demographic indicators to understand how different aspects
    of Sri Lanka's development interact with each other over time.
    </div>
    """, unsafe_allow_html=True)
    
    # Add GDP Growth Rate calculation if it doesn't exist
    if 'gdp_growth_pct' not in annual_df.columns and 'ny.gdp.mktp.cd' in annual_df.columns:
        annual_df['gdp_growth_pct'] = annual_df['ny.gdp.mktp.cd'].pct_change() * 100
        
    # Add smoothed growth rate if it doesn't exist
    if 'gdp_growth_smoothed' not in annual_df.columns and 'gdp_growth_pct' in annual_df.columns:
        annual_df['gdp_growth_smoothed'] = annual_df['gdp_growth_pct'].rolling(window=3).mean()
    
    # Create GDP per capita vs Life Expectancy scatter plot
    if 'ny.gdp.pcap.cd' in annual_df.columns and 'sp.dyn.le00.in' in annual_df.columns:
        fig = px.scatter(
            annual_df, 
            x='ny.gdp.pcap.cd', 
            y='sp.dyn.le00.in',
            size='year_only',  # Size points by year
            color='year_only',  # Color points by year
            hover_name='year_only',
            title='GDP per Capita vs Life Expectancy',
            labels={
                'ny.gdp.pcap.cd': 'GDP per Capita (US$)',
                'sp.dyn.le00.in': 'Life Expectancy (years)',
                'year_only': 'Year'
            }
        )
        
        # Add trendline
        fig.update_layout(
            height=600,
            hovermode="closest",
            plot_bgcolor='rgba(255,255,255,1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class='insight-card'>
            <strong>Development Insight:</strong> There is a positive correlation between GDP per capita and life expectancy,
            suggesting that economic growth has contributed to improved health outcomes in Sri Lanka. However, the relationship
            is not perfectly linear, indicating that other factors such as healthcare policies and public health interventions
            also play significant roles.
        </div>
        """, unsafe_allow_html=True)
    
    # Correlation Heatmap
    st.markdown("<div class='section-header'>Correlation Matrix</div>", unsafe_allow_html=True)
    
    # Select key indicators for correlation
    key_indicators = [
        'ny.gdp.mktp.cd', 'ny.gdp.pcap.cd', 'sp.dyn.le00.in', 
        'sp.dyn.tfrt.in', 'sp.pop.grow', 'pa.nus.fcrf', 
        'dt.tds.dect.gn.zs', 'ny.gdp.defl.zs'
    ]
    
    available_indicators = [col for col in key_indicators if col in annual_df.columns]
    
    if len(available_indicators) >= 2:
        # Create correlation matrix
        corr_matrix = annual_df[available_indicators].corr()
        
        # Create readable column names for display
        readable_cols = {
            'ny.gdp.mktp.cd': 'GDP',
            'ny.gdp.pcap.cd': 'GDP per Capita',
            'sp.dyn.le00.in': 'Life Expectancy',
            'sp.dyn.tfrt.in': 'Fertility Rate',
            'sp.pop.grow': 'Population Growth',
            'pa.nus.fcrf': 'Exchange Rate',
            'dt.tds.dect.gn.zs': 'Debt Service',
            'ny.gdp.defl.zs': 'GDP Deflator'
        }
        
        # Rename for display
        corr_display = corr_matrix.copy()
        corr_display.index = [readable_cols.get(col, col) for col in corr_display.index]
        corr_display.columns = [readable_cols.get(col, col) for col in corr_display.columns]
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        heatmap = sns.heatmap(
            corr_display, 
            annot=True, 
            cmap='coolwarm', 
            mask=mask,
            vmin=-1, vmax=1, 
            center=0,
            square=True,
            linewidths=.5,
            cbar_kws={"shrink": .8},
            fmt=".2f",
            ax=ax
        )
        
        plt.title('Correlation Matrix of Key Indicators', fontsize=16)
        plt.tight_layout()
        st.pyplot(fig)
        
        st.markdown("""
        <div class='insight-card'>
            <strong>Correlation Insight:</strong> The correlation matrix reveals the complex interrelationships between
            Sri Lanka's economic and demographic indicators. Strong positive correlations often exist between GDP and life expectancy,
            while negative correlations typically appear between fertility rates and economic development measures, reflecting
            the demographic transition process.
        </div>
        """, unsafe_allow_html=True)
    
    # GDP Components Stacked Area Chart
    st.markdown("<div class='section-header'>Economic Growth Patterns</div>", unsafe_allow_html=True)
    
    # Create economic growth patterns chart (Growth rate vs GDP per capita)
    annual_df['gdp_growth_smoothed'] = annual_df['gdp_growth_pct'].rolling(window=3).mean()
    
    if 'gdp_growth_smoothed' in annual_df.columns and 'ny.gdp.pcap.cd' in annual_df.columns:
        fig = px.scatter(
            annual_df.dropna(subset=['gdp_growth_smoothed', 'ny.gdp.pcap.cd']), 
            x='ny.gdp.pcap.cd', 
            y='gdp_growth_smoothed',
            color='year_only',
            size=[30] * len(annual_df),  # Consistent size
            hover_name='year_only',
            title='Economic Growth Pattern: GDP Growth vs GDP per Capita',
            labels={
                'ny.gdp.pcap.cd': 'GDP per Capita (US$)',
                'gdp_growth_smoothed': 'GDP Growth Rate (%, 3-year moving average)',
                'year_only': 'Year'
            },
            color_continuous_scale=px.colors.sequential.Viridis,
        )
        
        # Add trendline
        fig.update_layout(
            height=600,
            hovermode="closest",
            plot_bgcolor='rgba(255,255,255,1)'
        )
        
        # Add quadrant lines
        gdp_mean = annual_df['ny.gdp.pcap.cd'].mean()
        growth_mean = annual_df['gdp_growth_smoothed'].dropna().mean()
        
        fig.add_vline(x=gdp_mean, line_dash="dash", line_color="gray")
        fig.add_hline(y=growth_mean, line_dash="dash", line_color="gray")
        
        # Add quadrant annotations
        fig.add_annotation(
            x=gdp_mean/2, 
            y=growth_mean*1.5,
            text="Low Income,<br>High Growth",
            showarrow=False,
            font=dict(size=12)
        )
        
        fig.add_annotation(
            x=gdp_mean*1.5, 
            y=growth_mean*1.5,
            text="High Income,<br>High Growth",
            showarrow=False,
            font=dict(size=12)
        )
        
        fig.add_annotation(
            x=gdp_mean/2, 
            y=growth_mean/2,
            text="Low Income,<br>Low Growth",
            showarrow=False,
            font=dict(size=12)
        )
        
        fig.add_annotation(
            x=gdp_mean*1.5, 
            y=growth_mean/2,
            text="High Income,<br>Low Growth",
            showarrow=False,
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div class='insight-card'>
            <strong>Growth Pattern Insight:</strong> This visualization helps identify different economic growth phases.
            Countries typically move from low income/high growth (early development) to high income/high growth (economic boom),
            and eventually to high income/low growth (developed economy). Periods in the low income/low growth quadrant
            often represent economic challenges or crises.
        </div>
        """, unsafe_allow_html=True)

# Data explorer section
def show_data_explorer():
    st.markdown("<div class='main-header'>Data Explorer</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    Explore the raw data and create custom visualizations by selecting your variables of interest.
    You can also download the filtered dataset for further analysis.
    </div>
    """, unsafe_allow_html=True)
    
    # Custom visualization
    st.markdown("<div class='section-header'>Custom Visualization</div>", unsafe_allow_html=True)
    
    # Create mappings for readable names
    indicator_map = {
        'GDP (Current US$)': 'ny.gdp.mktp.cd',
        'GDP per Capita (Current US$)': 'ny.gdp.pcap.cd',
        'Life Expectancy': 'sp.dyn.le00.in',
        'Fertility Rate': 'sp.dyn.tfrt.in',
        'Population Growth (%)': 'sp.pop.grow',
        'Exchange Rate (LKR/USD)': 'pa.nus.fcrf',
        'Debt Service (% of GNI)': 'dt.tds.dect.gn.zs',
        'GDP Deflator': 'ny.gdp.defl.zs',
        'Rural Population (%)': 'sp.rur.totl.zs',
        'HIV Prevalence (%)': 'sh.dyn.aids.zs'
    }
    
    # Create a list of available indicators
    available_indicators = []
    for name, col in indicator_map.items():
        if col in filtered_df.columns:
            available_indicators.append(name)
    
    # Select options for visualization
    col1, col2 = st.columns(2)
    
    with col1:
        x_variable = st.selectbox(
            "Select X-Axis Variable",
            options=available_indicators,
            index=0
        )
    
    with col2:
        y_variable = st.selectbox(
            "Select Y-Axis Variable",
            options=available_indicators,
            index=1 if len(available_indicators) > 1 else 0
        )
    
    # Create visualization types (line or scatter)
    viz_type = st.radio(
        "Select Visualization Type",
        options=["Line Chart", "Scatter Plot"],
        horizontal=True
    )
    
    # Generate the selected visualization
    if viz_type == "Line Chart":
        # Create separate lines for each selected variable
        fig = go.Figure()
        
        # Add x_variable line
        if indicator_map[x_variable] in annual_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=annual_df['year_only'], 
                    y=annual_df[indicator_map[x_variable]],
                    name=x_variable,
                    line=dict(color='rgba(55, 126, 184, 1)', width=2)
                )
            )
        
        # Add y_variable line
        if indicator_map[y_variable] in annual_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=annual_df['year_only'], 
                    y=annual_df[indicator_map[y_variable]],
                    name=y_variable,
                    line=dict(color='rgba(228, 26, 28, 1)', width=2)
                )
            )
        
        # Update layout
        fig.update_layout(
            title=f'{x_variable} and {y_variable} over Time',
            xaxis_title='Year',
            yaxis_title='Value',
        )
        
    else:  # Scatter plot
        # Make sure both variables exist in the dataframe
        if indicator_map[x_variable] in annual_df.columns and indicator_map[y_variable] in annual_df.columns:
            fig = px.scatter(
                annual_df, 
                x=indicator_map[x_variable], 
                y=indicator_map[y_variable],
                color='year_only',
                size=[30] * len(annual_df),
                hover_name='year_only',
                title=f'{x_variable} vs {y_variable}',
                labels={
                    indicator_map[x_variable]: x_variable,
                    indicator_map[y_variable]: y_variable,
                    'year_only': 'Year'
                }
            )
        else:
            # Create a placeholder figure if data doesn't exist
            fig = go.Figure()
            fig.update_layout(
                title="Data not available for selected variables",
                annotations=[
                    dict(
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        text="One or both of the selected variables are not available in the dataset",
                        showarrow=False,
                        font=dict(size=14)
                    )
                ]
            )
    
    # Update layout
    fig.update_layout(
        height=600,
        hovermode="closest" if viz_type == "Scatter Plot" else "x unified",
        plot_bgcolor='rgba(255,255,255,1)',
        legend_title="Indicator" if viz_type == "Line Chart" else "Year"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data Table
    st.markdown("<div class='section-header'>Data Table</div>", unsafe_allow_html=True)
    
    # Display the filtered data
    select_columns = st.multiselect(
        "Select Columns to Display",
        options=available_indicators,
        default=available_indicators[:3]
    )
    
    # Convert selected columns to actual column names
    display_cols = ['year_only'] + [indicator_map[ind] for ind in select_columns if indicator_map[ind] in filtered_df.columns]
    
    if display_cols:
        # Prepare data for display with more readable column names
        display_df = filtered_df[display_cols].copy()
        
        # Rename columns for display
        column_map = {'year_only': 'Year'}
        for name, col in indicator_map.items():
            if col in display_cols:
                column_map[col] = name
        
        display_df = display_df.rename(columns=column_map)
        
        # Display the data
        st.dataframe(display_df.sort_values('Year', ascending=False), height=400)
        
        # Download button
        csv = display_df.to_csv(index=False)
        
        def get_csv_download_link(csv, filename):
            """Generate a download link for the CSV file"""
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="btn" style="background-color:#4CAF50;color:white;padding:8px 12px;text-decoration:none;border-radius:4px;">Download CSV File</a>'
            return href
        
        st.markdown(get_csv_download_link(csv, "sri_lanka_data.csv"), unsafe_allow_html=True)
    else:
        st.info("Please select at least one column to display.")

# About section
def show_about():
    st.markdown("<div class='main-header'>About</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card'>
    <h3>Sri Lanka Economic & Demographic Dashboard</h3>
    <p>This dashboard was created to visualize and analyze key economic and demographic indicators for Sri Lanka from 1970 to the present day. It provides insights into the country's development trajectory, challenges, and achievements over this period.</p>
    
    <h3>Data Sources</h3>
    <p>The data used in this dashboard is primarily sourced from the World Bank's World Development Indicators (WDI) database, which provides comprehensive, high-quality data on global development. The dataset includes economic indicators like GDP, exchange rates, and debt service, as well as demographic metrics such as life expectancy, fertility rates, and population growth.</p>
    
    <h3>Methodology</h3>
    <p>The dashboard transforms raw data into interactive visualizations to facilitate analysis and understanding. Where applicable, data is presented on both quarterly and annual bases, with appropriate aggregations and transformations applied. For some indicators, additional calculations such as growth rates, moving averages, and percentage changes have been computed to provide deeper insights.</p>
    
    <h3>Limitations</h3>
    <p>While this dashboard strives for accuracy and comprehensiveness, users should be aware of certain limitations:</p>
    <ul>
        <li>Data gaps may exist for certain years or indicators</li>
        <li>Some indicators may have changed in definition or measurement methodology over time</li>
        <li>The dashboard presents correlation analyses, which should not be interpreted as causal relationships</li>
    </ul>
    
    <h3>Credits</h3>
    <p>This dashboard was developed using Python with the Streamlit, Pandas, Plotly, Matplotlib, and Seaborn libraries.</p>
    </div>
    """, unsafe_allow_html=True)

# Main application flow
if pages == "Overview":
    show_overview()
elif pages == "Economic Indicators":
    show_economic_indicators()
elif pages == "Demographic Indicators":
    show_demographic_indicators()
elif pages == "Correlations & Relationships":
    show_correlations()
elif pages == "Data Explorer":
    show_data_explorer()
elif pages == "About":
    show_about()

# Add footer
st.markdown("""
<div style="text-align:center; margin-top:40px; padding:10px; background-color:#f0f2f6; border-radius:5px;">
    <p style="color:#6c757d; font-size:0.8rem;">Sri Lanka Economic & Demographic Dashboard | Created with Streamlit</p>
</div>
""", unsafe_allow_html=True)