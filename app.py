import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="HPDC Industry Forecaster", layout="wide")

# Constants for HPDC lbs per vehicle type
HPDC_per_ICE = 190
HPDC_per_HEV = 240
HPDC_per_EV = 300

# Material shares per vehicle type
Al_Share = {'ICE': 0.92, 'HEV': 0.90, 'EV': 0.95}
Zn_Share = {'ICE': 0.04, 'HEV': 0.03, 'EV': 0.01}
Mg_Share = {'ICE': 0.02, 'HEV': 0.03, 'EV': 0.03}

# Base values for economic model
BASE_YEAR_GDP = 25.44  # Trillion USD
BASE_OTHER_HPDC = 3.2e9  # lbs

# Function to estimate national HPDC demand
def estimate_hpdc_production(annual_housing_starts, annual_vehicle_production, vehicle_mix,
                              base_year_gdp, current_gdp, base_year_other_hpdc, gdp_elasticity):
    gdp_growth_factor = (current_gdp / base_year_gdp) ** gdp_elasticity
    est_other_hpdc = base_year_other_hpdc * gdp_growth_factor

    hpdc_auto = (
        vehicle_mix['ICE'] / 100 * annual_vehicle_production * HPDC_per_ICE +
        vehicle_mix['HEV'] / 100 * annual_vehicle_production * HPDC_per_HEV +
        vehicle_mix['EV'] / 100 * annual_vehicle_production * HPDC_per_EV
    )

    hpdc_housing = annual_housing_starts * 100  # Placeholder conversion
    total_hpdc = hpdc_auto + hpdc_housing + est_other_hpdc

    shares = {
        'Auto': hpdc_auto / total_hpdc,
        'Housing': hpdc_housing / total_hpdc,
        'Other': est_other_hpdc / total_hpdc
    }
    return total_hpdc, shares

# Function to predict company-level revenue
def predict_annual_revenue(machines, employees, avg_tonnage, markets):
    automotive_weight = 1.8 if "Automotive" in markets else 1.0
    clamping_force = machines * avg_tonnage
    revenue_per_ton = 3000
    base_revenue = clamping_force * revenue_per_ton
    employee_efficiency = employees * 250000
    return (base_revenue + employee_efficiency) * automotive_weight, clamping_force

# Layout with tabs
tabs = st.tabs(["📈 National HPDC Forecast", "🏭 Company Revenue Estimator"])

# === TAB 1: NATIONAL FORECAST === #
with tabs[0]:
    st.header("📈 National HPDC Forecast")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Vehicle Production")
        annual_vehicle_production = st.number_input("Total Annual Vehicle Production", value=11_200_000)
        vehicle_mix_ice = st.slider("ICE Vehicle %", 0, 100, 45)
        vehicle_mix_hev = st.slider("HEV Vehicle %", 0, 100, 25)
        vehicle_mix_ev = st.slider("EV Vehicle %", 0, 100, 30)

    with col2:
        st.subheader("Economic Data")
        housing_starts = st.number_input("Annual Housing Starts", value=1_400_000)
        gdp_current = st.number_input("Current Year GDP (Trillion USD)", value=27.10)
        gdp_elasticity = st.slider("GDP Elasticity", 0.0, 2.0, 0.92)

    total_mix = vehicle_mix_ice + vehicle_mix_hev + vehicle_mix_ev

    if total_mix != 100:
        st.warning("Vehicle mix percentages must sum to 100%.")
    else:
        vehicle_mix = {
            'ICE': vehicle_mix_ice,
            'HEV': vehicle_mix_hev,
            'EV': vehicle_mix_ev
        }

        if st.button("📊 Estimate National HPDC Demand"):
            total_hpdc, shares = estimate_hpdc_production(
                housing_starts, annual_vehicle_production, vehicle_mix,
                BASE_YEAR_GDP, gdp_current, BASE_OTHER_HPDC, gdp_elasticity
            )

            st.metric("Total Estimated HPDC", f"{total_hpdc / 1e9:.2f} billion lbs")

            share_df = pd.DataFrame.from_dict(shares, orient='index', columns=['Share'])
            fig = px.pie(share_df.reset_index(), values='Share', names='index',
                         title="Sector Share of HPDC Demand", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

# === TAB 2: COMPANY MODELER === #
with tabs[1]:
    st.header("🏭 Company Revenue Estimator")
    col1, col2 = st.columns(2)

    with col1:
        machines = st.number_input("Number of Machines", min_value=0, value=10)
        avg_tonnage = st.number_input("Average Tonnage per Machine", min_value=0, value=200)

    with col2:
        employees = st.number_input("Number of Employees", min_value=0, value=50)
        markets = st.multiselect(
            "Markets Served",
            ["Automotive", "Medical", "Consumer", "Industrial", "Aerospace"],
            default=["Automotive"]
        )

    if st.button("💰 Estimate Revenue"):
        revenue, total_clamping_force = predict_annual_revenue(machines, employees, avg_tonnage, markets)
        st.metric("Estimated Annual Revenue", f"${revenue:,.0f}")
        st.metric("Total Clamping Force", f"{total_clamping_force:,} tons")
        if employees:
            st.metric("Revenue per Employee", f"${revenue / employees:,.0f}")
