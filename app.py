import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# Page configuration
st.set_page_config(
    page_title="Sri Lanka Economic & Demographic Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data():
    data = pd.read_csv('lka_processed.csv')
    # Convert column names to lowercase for consistency
    data.columns = [col.lower() for col in data.columns]
    return data

df = load_data()

# Dashboard title
st.title("Sri Lanka Economic & Demographic Dashboard")
st.markdown("An interactive tool for exploring key indicators for Sri Lanka")

# Create a year column from time_period if it exists
if 'time_period' in df.columns:
    # Extract year from time_period (e.g., "1970-Q1" -> 1970)
    df['year_only'] = df['time_period'].str.split('-').str[0].astype(int)
else:
    # If there's already a year column, use it
    df['year_only'] = df['year']

# Sidebar filters
st.sidebar.title("Filters")

# Time period filter
years = sorted(df['year_only'].unique())
selected_years = st.sidebar.slider(
    "Select Year Range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

# Filter data by year
filtered_df = df[(df['year_only'] >= selected_years[0]) & (df['year_only'] <= selected_years[1])]

# For quarterly data, create a version with annual averages for some charts
annual_df = filtered_df.groupby('year_only').agg({
    'ny.gdp.mktp.cd': 'mean',
    'sp.dyn.le00.in': 'mean',
    'sp.pop.grow': 'mean'
}).reset_index()

# Indicator selector
indicator_map = {
    'GDP (Current US$)': 'ny.gdp.mktp.cd',
    'Life Expectancy': 'sp.dyn.le00.in',
    'Population Growth': 'sp.pop.grow'
}

# Check which indicators are actually in the dataframe
available_indicators = [name for name, col in indicator_map.items() if col in filtered_df.columns]

# Default to showing all available indicators, up to 2
default_indicators = available_indicators[:min(2, len(available_indicators))]

selected_indicators = st.sidebar.multiselect(
    "Select Indicators to Display",
    options=available_indicators,
    default=default_indicators
)

# Main content area
st.header("Economic and Demographic Trends")

# Display key metrics in columns
try:
    col1, col2, col3 = st.columns(3)
    
    # Get the most recent year's data
    latest_year = filtered_df['year_only'].max()
    latest_data = filtered_df[filtered_df['year_only'] == latest_year]
    
    # Use the last row of the latest year (e.g., Q4 data)
    latest_row = latest_data.iloc[-1]
    
    with col1:
        if 'ny.gdp.mktp.cd' in filtered_df.columns:
            latest_gdp = latest_row['ny.gdp.mktp.cd']
            st.metric("Latest GDP (US$)", f"${latest_gdp:,.2f}")
    
    with col2:
        if 'sp.dyn.le00.in' in filtered_df.columns:
            latest_life_exp = latest_row['sp.dyn.le00.in']
            st.metric("Life Expectancy", f"{latest_life_exp:.1f} years")
    
    with col3:
        if 'sp.pop.grow' in filtered_df.columns:
            latest_pop_growth = latest_row['sp.pop.grow']
            st.metric("Population Growth", f"{latest_pop_growth:.2f}%")
except Exception as e:
    st.error(f"Error displaying metrics: {e}")
    st.write("Debug info - available columns:", filtered_df.columns.tolist())

# Create tabbed sections for different visualizations
tab1, tab2, tab3 = st.tabs(["Time Trends", "Comparisons", "Data Table"])

with tab1:
    st.subheader("Key Indicator Trends Over Time")
    
    # GDP trend
    if 'GDP (Current US$)' in selected_indicators and indicator_map['GDP (Current US$)'] in annual_df.columns:
        try:
            fig = px.line(
                annual_df, 
                x='year_only', 
                y=indicator_map['GDP (Current US$)'],
                title='GDP (Current US$) Over Time',
                labels={indicator_map['GDP (Current US$)']: 'GDP (US$)', 'year_only': 'Year'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating GDP chart: {e}")
    
    # Life expectancy trend
    if 'Life Expectancy' in selected_indicators and indicator_map['Life Expectancy'] in annual_df.columns:
        try:
            fig = px.line(
                annual_df, 
                x='year_only', 
                y=indicator_map['Life Expectancy'],
                title='Life Expectancy Over Time',
                labels={indicator_map['Life Expectancy']: 'Life Expectancy (years)', 'year_only': 'Year'},
                color_discrete_sequence=['#ff6b6b']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating Life Expectancy chart: {e}")
    
    # Population growth trend
    if 'Population Growth' in selected_indicators and indicator_map['Population Growth'] in annual_df.columns:
        try:
            fig = px.line(
                annual_df, 
                x='year_only', 
                y=indicator_map['Population Growth'],
                title='Population Growth Rate Over Time',
                labels={indicator_map['Population Growth']: 'Population Growth (%)', 'year_only': 'Year'},
                color_discrete_sequence=['#51cf66']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating Population Growth chart: {e}")

with tab2:
    st.subheader("Indicator Relationships")
    
    # Create columns for correlation and scatter plot
    comp_col1, comp_col2 = st.columns(2)
    
    # Get selected columns for comparison
    selected_cols = [indicator_map[ind] for ind in selected_indicators if indicator_map[ind] in annual_df.columns]
    
    with comp_col1:
        # Scatter plot - Make sure we have at least 2 indicators
        if len(selected_cols) >= 2 and 'GDP (Current US$)' in selected_indicators and 'Life Expectancy' in selected_indicators:
            try:
                gdp_col = indicator_map['GDP (Current US$)']
                le_col = indicator_map['Life Expectancy']
                
                fig = px.scatter(
                    annual_df, 
                    x=gdp_col, 
                    y=le_col,
                    size='year_only',  # Size points by year
                    hover_name='year_only',
                    title='GDP vs Life Expectancy',
                    labels={gdp_col: 'GDP (US$)', le_col: 'Life Expectancy (years)'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating scatter plot: {e}")
    
    with comp_col2:
        # Correlation heatmap
        st.subheader("Correlation Between Indicators")
        
        if len(selected_cols) >= 2:
            try:
                # Create correlation matrix
                corr_matrix = annual_df[selected_cols].corr()
                
                # Create a more readable version with proper indicator names
                readable_cols = {col: name for name, col in indicator_map.items() if col in selected_cols}
                corr_matrix.index = [readable_cols.get(col, col) for col in corr_matrix.index]
                corr_matrix.columns = [readable_cols.get(col, col) for col in corr_matrix.columns]
                
                # Create heatmap
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
                plt.tight_layout()
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Error creating correlation matrix: {e}")
                st.write("Debug info - selected columns:", selected_cols)
        else:
            st.info("Select at least 2 indicators to display correlation matrix")

with tab3:
    st.subheader("Raw Data")
    
    # Show data table with selected indicators
    if selected_indicators:
        display_cols = ['year_only'] + [indicator_map[ind] for ind in selected_indicators if indicator_map[ind] in filtered_df.columns]
        st.dataframe(filtered_df[display_cols].sort_values('year_only', ascending=False))
    else:
        st.info("Select indicators to display data")

# Footer
st.markdown("---")
st.markdown("Data source: World Bank indicators for Sri Lanka")