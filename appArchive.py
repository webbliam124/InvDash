import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="RCS Cost Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Helper function to format currency
def format_currency(amount):
    return f"R{amount:,.2f}"

# Sidebar for global settings
st.sidebar.header("Global Settings")

# Referral Percentage
referral_pct = st.sidebar.number_input(
    "Referral Percentage (%)",
    min_value=0.0,
    max_value=100.0,
    value=10.0,
    step=0.5,
)

# Float Cost
float_cost = st.sidebar.number_input(
    "Float Cost (R)",
    min_value=0.0,
    value=70.0,
    step=5.0,
)

# Base Cost for Minutes and Messages
st.sidebar.header("Base Costs")
base_min_cost = st.sidebar.number_input(
    "Base Cost per Minute (R)",
    min_value=0.0,
    value=1.0,
    step=0.1,
)
base_msg_cost = st.sidebar.number_input(
    "Base Cost per Message (R)",
    min_value=0.0,
    value=0.5,
    step=0.1,
)

# Plan Duration and Discount
st.sidebar.header("Plan Duration Discounts")
plan_duration = st.sidebar.selectbox(
    "Select Plan Duration",
    options=["1 Month", "3 Months", "12 Months"],
)
if plan_duration == "1 Month":
    discount_pct = 0.0
elif plan_duration == "3 Months":
    discount_pct = 5.0
else:
    discount_pct = 10.0

st.sidebar.write(f"**Discount Applied:** {discount_pct}%")

# Base Contingency
base_contingency = st.sidebar.number_input(
    "Base Contingency (R)",
    min_value=0.0,
    value=500.0,
    step=50.0,
)

# Advanced Contingency
advanced_contingency = st.sidebar.number_input(
    "Advanced Contingency (R)",
    min_value=0.0,
    value=1000.0,
    step=50.0,
)

# Referral Adjustment
def apply_referral(base_cost, referral_pct):
    return base_cost * (1 + referral_pct / 100)

# Cost Calculations
def calculate_plan_cost(base_cost):
    return apply_referral(base_cost, referral_pct)

# Plan Data
plans = {
    "Basic": {
        "Base Cost": 1000.0,
        "Minutes Included": 500,
        "Messages Included": 1000,
        "Once-off Cost": 200.0,
        "Setup Cost": 300.0,
        "Hours Worked": 20,
        "Price per Hour": 150.0,
        "Contingency": base_contingency,
    },
    "Advanced": {
        "Base Cost": 2000.0,
        "Minutes Included": 1000,
        "Messages Included": 2000,
        "Once-off Cost": 400.0,
        "Setup Cost": 600.0,
        "Hours Worked": 40,
        "Price per Hour": 140.0,
        "Contingency": advanced_contingency,
    },
    "Enterprise": {
        "Base Cost": 5000.0,
        "Minutes Included": 5000,
        "Messages Included": 10000,
        "Once-off Cost": 1000.0,
        "Setup Cost": 1500.0,
        "Hours Worked": 100,
        "Price per Hour": 130.0,
        "Contingency": advanced_contingency * 2,  # Example adjustment
    },
}

# Editable Plan Inputs
st.header("RCS Cost Calculator")

for plan_name, details in plans.items():
    st.subheader(f"{plan_name} Plan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Base Cost with Referral
        base_cost = calculate_plan_cost(details["Base Cost"])
        st.write(f"**RCS {plan_name} Cost:** {format_currency(base_cost)}")
        
        # Minutes and Messages
        minutes = st.number_input(
            f"{plan_name} Minutes Included",
            min_value=0,
            value=details["Minutes Included"],
            key=f"{plan_name}_minutes",
        )
        messages = st.number_input(
            f"{plan_name} Messages Included",
            min_value=0,
            value=details["Messages Included"],
            key=f"{plan_name}_messages",
        )
        
        # Once-off and Setup Costs
        once_off = st.number_input(
            f"{plan_name} Once-off Cost (R)",
            min_value=0.0,
            value=details["Once-off Cost"],
            step=50.0,
            key=f"{plan_name}_once_off",
        )
        setup_cost = st.number_input(
            f"{plan_name} Setup Cost (R)",
            min_value=0.0,
            value=details["Setup Cost"],
            step=50.0,
            key=f"{plan_name}_setup_cost",
        )
        
    with col2:
        # Hours and Price per Hour
        hours = st.number_input(
            f"{plan_name} Hours Worked",
            min_value=0,
            value=details["Hours Worked"],
            key=f"{plan_name}_hours",
        )
        price_per_hour = st.number_input(
            f"{plan_name} Price per Hour (R)",
            min_value=0.0,
            value=details["Price per Hour"],
            step=10.0,
            key=f"{plan_name}_price_per_hour",
        )
        
        # Contingency
        contingency = st.number_input(
            f"{plan_name} Contingency (R)",
            min_value=0.0,
            value=details["Contingency"],
            step=50.0,
            key=f"{plan_name}_contingency",
        )
        
    # Calculations
    total_hours_cost = hours * price_per_hour
    total_cost = base_cost + once_off + setup_cost + total_hours_cost + contingency
    discount = total_cost * (discount_pct / 100)
    final_cost = total_cost - discount
    
    st.markdown(f"**Total Cost:** {format_currency(total_cost)}")
    st.markdown(f"**Discount ({discount_pct}%):** -{format_currency(discount)}")
    st.markdown(f"**Final Cost:** {format_currency(final_cost)}")
    st.markdown("---")

# Main Cost Calculations
st.header("Main Cost Overview")

# Calculating total base cost for minutes and messages
total_min_cost = base_min_cost * sum([details["Minutes Included"] for details in plans.values()])
total_msg_cost = base_msg_cost * sum([details["Messages Included"] for details in plans.values()])

main_cost_df = pd.DataFrame({
    "Description": ["Total Minutes Cost", "Total Messages Cost"],
    "Amount": [format_currency(total_min_cost), format_currency(total_msg_cost)]
})

st.table(main_cost_df)

# Editable Float Cost
st.header("Float Cost")
st.write(f"**Current Float Cost:** {format_currency(float_cost)}")
new_float_cost = st.number_input(
    "Edit Float Cost (R)",
    min_value=0.0,
    value=float_cost,
    step=10.0,
)
st.write(f"**Updated Float Cost:** {format_currency(new_float_cost)}")

# Matrix for Setup and Once-off Costs
st.header("Setup and Once-off Costs Matrix")

matrix_data = {
    "Plan": [],
    "Once-off Cost (R)": [],
    "Setup Cost (R)": [],
    "Hours Worked": [],
    "Price per Hour (R)": [],
    "Contingency (R)": [],
}
for plan_name, details in plans.items():
    matrix_data["Plan"].append(plan_name)
    matrix_data["Once-off Cost (R)"].append(details["Once-off Cost"])
    matrix_data["Setup Cost (R)"].append(details["Setup Cost"])
    matrix_data["Hours Worked"].append(details["Hours Worked"])
    matrix_data["Price per Hour (R)"].append(details["Price per Hour"])
    matrix_data["Contingency (R)"].append(details["Contingency"])

matrix_df = pd.DataFrame(matrix_data)
st.dataframe(matrix_df.style.format({
    "Once-off Cost (R)": format_currency,
    "Setup Cost (R)": format_currency,
    "Price per Hour (R)": format_currency,
    "Contingency (R)": format_currency,
}))

# Summary
st.header("Summary")

summary_data = []
for plan_name, details in plans.items():
    summary = {
        "Plan": plan_name,
        "Base Cost": format_currency(calculate_plan_cost(details["Base Cost"])),
        "Once-off": format_currency(details["Once-off Cost"]),
        "Setup Cost": format_currency(details["Setup Cost"]),
        "Hours Cost": format_currency(details["Hours Worked"] * details["Price per Hour"]),
        "Contingency": format_currency(details["Contingency"]),
        "Total Cost": format_currency(
            calculate_plan_cost(details["Base Cost"]) +
            details["Once-off Cost"] +
            details["Setup Cost"] +
            (details["Hours Worked"] * details["Price per Hour"]) +
            details["Contingency"]
        )
    }
    summary_data.append(summary)

summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

# Apply Discount
st.header("Final Costs with Discount")

final_summary = []
for plan in summary_data:
    total_cost = float(plan["Total Cost"][1:].replace(',', ''))
    discount = total_cost * (discount_pct / 100)
    final_cost = total_cost - discount
    final_summary.append({
        "Plan": plan["Plan"],
        "Final Cost (R)": format_currency(final_cost),
        "Discount Applied (R)": format_currency(discount)
    })

final_df = pd.DataFrame(final_summary)
st.table(final_df)

# Footer
st.markdown("---")
st.markdown("© 2024 Your Company Name. All rights reserved.")
