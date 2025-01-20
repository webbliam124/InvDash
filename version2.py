# ======================================
# IMPORTS
# ======================================
import streamlit as st
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

# ======================================
# CONFIGURATION FILES (JSON)
#  - Manages file paths for pricing, usage, and exchange rate configurations
# ======================================
CONFIG_DIR = 'config'
PRICING_FILE = os.path.join(CONFIG_DIR, 'pricing.json')
USAGE_LIMITS_FILE = os.path.join(CONFIG_DIR, 'usage_limits.json')
EXCHANGE_RATES_FILE = os.path.join(CONFIG_DIR, 'exchange_rates.json')

# ======================================
# DEFAULT CONFIGURATIONS
# ======================================
DEFAULT_PRICING = {
    "base_monthly_cost": 94600,       # Up to 5 assistants (Enterprise)
    "setup_cost": 20000,              # One-time universal setup (Enterprise)
    "assistant_base_cost": 10000,     # R10k per assistant (Enterprise)
    "discount_3_5": 8,                # 8% discount for #3-5 assistants
    "discount_6_10": 12,              # 12% discount for #6-10 assistants

    "pay_3month_discount": 15,
    "pay_12month_discount": 18,

    "voice_customization_cost": 0,    
    "setup_cost_per_assistant": 7800,
    "whitelabel_fee": 14550,
    "whitelabel_fee_charged": False,
    "whitelabel_fee_waived": False,
    "monthly_support_hours": 0,

    "custom_voice_cost_per_voice": 0,

    # NEW: Discounts Enabled Flag
    "discounts_enabled": True
}

DEFAULT_USAGE_LIMITS = {
    "base_messages": 100000,
    "base_minutes": 10000,
    "assistant_extra_messages": 8000,
    "assistant_extra_minutes": 300,
    "cost_per_additional_message": 0.09,
    "cost_per_additional_minute": 3.33
}

DEFAULT_EXCHANGE_RATES = {
    "EUR": 19.0,
    "USD": 16.0,
    "AED": 4.4
}

CURRENCY_SYMBOLS = {
    "ZAR": "R",
    "EUR": "€",
    "USD": "$",
    "AED": "د.إ"
}

SUPPORTED_CURRENCIES = ["ZAR", "EUR", "USD", "AED"]

# ======================================
# HELPER FUNCTIONS
# ======================================
def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def initialize_configs():
    """Create default JSON configs if missing."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    # Pricing
    if not os.path.isfile(PRICING_FILE):
        with open(PRICING_FILE, 'w') as f:
            json.dump(DEFAULT_PRICING, f, indent=4)
    else:
        # Ensure new keys exist
        with open(PRICING_FILE, 'r') as f:
            try:
                pricing = json.load(f)
            except json.JSONDecodeError:
                pricing = DEFAULT_PRICING
        updated = False
        for key, value in DEFAULT_PRICING.items():
            if key not in pricing:
                pricing[key] = value
                updated = True
        if updated:
            with open(PRICING_FILE, 'w') as f:
                json.dump(pricing, f, indent=4)
    
    # Usage
    if not os.path.isfile(USAGE_LIMITS_FILE):
        with open(USAGE_LIMITS_FILE, 'w') as f:
            json.dump(DEFAULT_USAGE_LIMITS, f, indent=4)
    
    # Exchange Rates
    if not os.path.isfile(EXCHANGE_RATES_FILE):
        with open(EXCHANGE_RATES_FILE, 'w') as f:
            json.dump(DEFAULT_EXCHANGE_RATES, f, indent=4)

def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading config: {e}")
        return None

def save_config(file_path, data):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        st.error(f"Error saving config: {e}")

def apply_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FFFFFF;
            color: #191937;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .sidebar .sidebar-content {
            background-color: #F0F2F6;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #5fba6a;
            font-family: 'Arial Black', Gadget, sans-serif;
        }
        .stButton > button {
            background-color: #CCCCCC;
            color: #000000;
            border: none;
            padding: 10px 24px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #AAAAAA;
        }
        label {
            color: #191937 !important;
            font-weight: bold;
        }
        .stCheckbox > label > div > div, .stRadio > label > div {
            color: #191937;
        }
        .stSlider > label {
            color: #191937;
            font-weight: bold;
        }
        .dataframe {
            color: #191937;
            border-collapse: collapse;
            width: 100%;
        }
        .dataframe th {
            background-color: #5fba6a;
            color: white;
            font-weight: bold;
            padding: 8px;
            text-align: left;
        }
        .dataframe td {
            background-color: #F0F2F6;
            padding: 8px;
            border: 1px solid #ddd;
        }
        .card {
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .card h4 {
            color: #5fba6a;
            margin-bottom: 0.5em;
        }
        .card p {
            font-size: 1.2em;
            font-weight: bold;
            margin: 0;
        }
        .highlighted-total {
            background-color: #ffeb3b;
            color: #000000;
            font-weight: bold;
            border-radius: 5px;
            padding: 10px;
            display: inline-block;
            font-size: 1.2em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def get_exchange_rates():
    return load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES

def save_exchange_rates(rates):
    save_config(EXCHANGE_RATES_FILE, rates)

def convert_currency(amount_zar, currency, exchange_rates):
    """Convert ZAR to selected currency with +30% if not ZAR."""
    if currency == "ZAR":
        return amount_zar
    rate = exchange_rates.get(currency, 1)
    return (amount_zar / rate) * 1.3

def get_currency_symbol(currency):
    return CURRENCY_SYMBOLS.get(currency, "R")

def calculate_assistant_cost(num_assistants, base_per_assistant, discount_3_5, discount_6_10, discounts_enabled=True):
    total_cost = 0
    num_assistants = max(num_assistants, 0)
    base_per_assistant = max(base_per_assistant, 0)
    if not discounts_enabled:
        discount_3_5 = 0
        discount_6_10 = 0

    for i in range(1, num_assistants + 1):
        if i <= 2:
            discount_rate = 0.0
        elif 3 <= i <= 5:
            discount_rate = discount_3_5 / 100.0
        else:
            discount_rate = discount_6_10 / 100.0
        cost_for_this_assistant = base_per_assistant * (1 - discount_rate)
        total_cost += cost_for_this_assistant

    return total_cost

def calculate_usage(num_assistants, usage_limits):
    num_assistants = max(num_assistants, 0)
    base_messages = max(usage_limits.get("base_messages", 100000), 0)
    base_minutes = max(usage_limits.get("base_minutes", 10000), 0)
    assistant_extra_messages = max(usage_limits.get("assistant_extra_messages", 8000), 0)
    assistant_extra_minutes = max(usage_limits.get("assistant_extra_minutes", 300), 0)

    if num_assistants <= 5:
        total_messages = base_messages
        total_minutes = base_minutes
    else:
        extra_assistants = num_assistants - 5
        total_messages = base_messages + extra_assistants * assistant_extra_messages
        total_minutes = base_minutes + extra_assistants * assistant_extra_minutes
    
    return total_messages, total_minutes

# ======================================
# INIT
# ======================================
initialize_configs()
pricing = load_config(PRICING_FILE) or DEFAULT_PRICING
usage_limits = load_config(USAGE_LIMITS_FILE) or DEFAULT_USAGE_LIMITS
exchange_rates = get_exchange_rates()

# ======================================
# STREAMLIT APP
# ======================================
st.set_page_config(page_title="askAYYI Cost Calculator", layout="wide")
apply_custom_css()

st.sidebar.image(
    "https://static.wixstatic.com/media/bde46d_5c23110f863c4083b92f963a4bcd6b31~mv2.png/v1/fill/w_202,h_64,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/ASkAYYI.png",
    width=200
)

# Create a top-level radio to navigate
menu = st.sidebar.radio(
    "Navigation",
    [
        "Plan & Questions",
        "Client Calculator",
        "Call Centre Cost Calculation",
        "Main Dashboard",
        "Quotation",
        "Admin Dashboard"
    ]
)

# ======================================
# ADMIN DASHBOARD
# ======================================
def authenticate_admin():
    def check_password():
        def password_entered():
            if st.session_state.get("password", "") == "RCS_18112":
                st.session_state["password_correct"] = True
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="password")
            return False
        elif not st.session_state["password_correct"]:
            st.text_input("Enter Admin Password", type="password", on_change=password_entered, key="password")
            st.error("Incorrect Password")
            return False
        else:
            return True

    return check_password()

if menu == "Admin Dashboard":
    if authenticate_admin():
        st.title("Admin Dashboard")

        # 1) Pricing Config
        st.header("Pricing Configuration")
        with st.form("pricing_form"):
            col1, col2 = st.columns(2)
            with col1:
                base_monthly_cost = st.number_input(
                    "Base Monthly Cost (ZAR)",
                    value=pricing.get('base_monthly_cost', 94600),
                    step=1000
                )
                setup_cost = st.number_input(
                    "Universal Setup Cost (ZAR)",
                    value=pricing.get('setup_cost', 20000),
                    step=1000
                )
                assistant_base_cost = st.number_input(
                    "Assistant Base Monthly Cost (ZAR)",
                    value=pricing.get('assistant_base_cost', 10000),
                    step=1000
                )
                setup_cost_per_assistant = st.number_input(
                    "Setup Cost Per Assistant (ZAR)",
                    value=pricing.get('setup_cost_per_assistant', 7800),
                    step=1000
                )
            with col2:
                discount_3_5 = st.number_input(
                    "Discount for Assistants #3-5 (%)",
                    value=pricing.get('discount_3_5', 8),
                    min_value=0, max_value=100
                )
                discount_6_10 = st.number_input(
                    "Discount for Assistants #6-10 (%)",
                    value=pricing.get('discount_6_10', 12),
                    min_value=0, max_value=100
                )
                voice_customization_cost = st.number_input(
                    "Voice Customization Monthly (ZAR)",
                    value=pricing.get('voice_customization_cost', 0),
                    step=500
                )

            st.markdown("*(Legacy references for record only)*")
            pay_3month_discount = st.number_input(
                "Legacy 3-Month (%)",
                value=pricing.get('pay_3month_discount', 15),
                min_value=0, max_value=100
            )
            pay_12month_discount = st.number_input(
                "Legacy 12-Month (%)",
                value=pricing.get('pay_12month_discount', 18),
                min_value=0, max_value=100
            )

            st.markdown("---")
            st.subheader("Whitelabel Fee Configuration")
            whitelabel_fee_charged = st.checkbox(
                "Charge Whitelabel Fee (ZAR 14,550)?",
                value=pricing.get("whitelabel_fee_charged", False)
            )
            whitelabel_fee_waived = st.checkbox(
                "Waive Whitelabel Fee?",
                value=pricing.get("whitelabel_fee_waived", False)
            )

            st.markdown("---")
            st.subheader("Technical Support Hours Included")
            monthly_support_hours = st.number_input(
                "Monthly Support Hours",
                value=pricing.get("monthly_support_hours", 0),
                min_value=0
            )

            st.markdown("---")
            st.subheader("Custom Voice Configuration")
            custom_voice_cost_per_voice = st.number_input(
                "Custom Voice Cost (Monthly Per Voice) (ZAR)",
                value=pricing.get("custom_voice_cost_per_voice", 0),
                step=500
            )

            # Submit
            save_pricing_btn = st.form_submit_button("Save Pricing Configuration")
            if save_pricing_btn:
                pricing.update({
                    "base_monthly_cost": base_monthly_cost,
                    "setup_cost": setup_cost,
                    "assistant_base_cost": assistant_base_cost,
                    "discount_3_5": discount_3_5,
                    "discount_6_10": discount_6_10,
                    "voice_customization_cost": voice_customization_cost,
                    "pay_3month_discount": pay_3month_discount,
                    "pay_12month_discount": pay_12month_discount,
                    "whitelabel_fee_charged": whitelabel_fee_charged,
                    "whitelabel_fee_waived": whitelabel_fee_waived,
                    "monthly_support_hours": monthly_support_hours,
                    "custom_voice_cost_per_voice": custom_voice_cost_per_voice
                })
                save_config(PRICING_FILE, pricing)
                st.success("Pricing configuration saved successfully!")

        st.markdown("---")
        st.header("Exchange Rates Configuration")
        with st.form("exchange_rates_form"):
            exchange_rate_inputs = {}
            for currency in SUPPORTED_CURRENCIES:
                if currency == "ZAR":
                    continue
                exchange_rate_inputs[currency] = st.number_input(
                    f"Exchange Rate for {currency} (1 {currency} = X ZAR)",
                    value=exchange_rates.get(currency, DEFAULT_EXCHANGE_RATES.get(currency, 1)),
                    step=0.001,
                    format="%.3f"
                )
            save_exchange_rates_btn = st.form_submit_button("Save Exchange Rates")
            if save_exchange_rates_btn:
                for currency, rate in exchange_rate_inputs.items():
                    exchange_rates[currency] = rate
                save_exchange_rates(exchange_rates)
                st.success("Exchange rates updated successfully!")

        st.markdown("---")
        st.header("Discounts Configuration")

        discounts_enabled = pricing.get("discounts_enabled", True)
        if discounts_enabled:
            st.success("Discounts are currently **enabled**.")
            if st.button("Disable Discounts"):
                pricing["discounts_enabled"] = False
                save_config(PRICING_FILE, pricing)
                st.success("Discounts have been disabled.")
        else:
            st.warning("Discounts are currently **disabled**.")
            if st.button("Enable Discounts"):
                pricing["discounts_enabled"] = True
                save_config(PRICING_FILE, pricing)
                st.success("Discounts have been enabled.")


# ======================================
# PAGE: Plan & Questions
#  - Let the user pick a plan (Enterprise / Advanced / Basic)
#  - Ask the 4 questions
# ======================================
elif menu == "Plan & Questions":
    st.title("Welcome to askAYYI!")
    st.write("Please select a plan and answer a few short questions to begin.")

    # 1) Which plan do you want?
    plan_choice = st.selectbox(
        "Which plan do you want?",
        ["Enterprise", "Advanced", "Basic"],
        help="Select a plan. Enterprise for larger usage, or Advanced/Basic for smaller usage."
    )
    st.session_state["selected_plan"] = plan_choice

    # 2) Would you like to use our CRM or your CRM?
    crm_choice = st.radio(
        "Would you like to use our CRM or your CRM?",
        ["Our CRM", "Your CRM"]
    )
    st.session_state["crm_choice"] = crm_choice

    # 3) External integrations
    if plan_choice == "Basic":
        st.markdown("External Integrations: **Basic plan does not allow external integrations.**")
        ext_integrations = 0
    else:
        ext_integrations = st.number_input(
            "How many external integrations (APIs) would you like?",
            min_value=0, step=1,
            help="Number of external APIs or integrations."
        )
    st.session_state["external_integrations"] = ext_integrations

    # 4) Estimated calls & minutes
    st.write("**What is your estimated calls and minutes per month?**")
    est_monthly_calls = st.number_input(
        "Estimated monthly calls (approx.)",
        min_value=0, step=100,
        help="Used to approximate usage costs."
    )
    est_minutes_per_call = st.number_input(
        "Approx. average minutes per call",
        min_value=0.0, step=0.5,
        value=5.0
    )
    st.session_state["est_monthly_calls"] = est_monthly_calls
    st.session_state["est_minutes_per_call"] = est_minutes_per_call

    # 5) Number of use cases
    st.write("**How many use cases do you want?** (e.g. HR, Customer Care, Marketing, etc.)")
    num_use_cases = st.number_input(
        "Number of use cases",
        min_value=1, step=1
    )
    st.session_state["num_use_cases"] = num_use_cases

    # CRM contradiction warning if applicable
    if crm_choice == "Your CRM" and plan_choice == "Basic":
        st.warning(
            "Heads up! **Basic** plan does not allow using your CRM. "
            "If you truly need your own CRM, please select Advanced or Enterprise."
        )

    # If advanced + your CRM, mention enterprise might be a better fit
    if plan_choice == "Advanced" and crm_choice == "Your CRM":
        st.info(
            "If your monthly messages exceed 10k or you have multiple complex use cases, "
            "consider upgrading to Enterprise."
        )

    st.success("Your answers are recorded. Next, go to **Client Calculator**.")


# ======================================
# PAGE: Client Calculator
#  - Apply overrides for Basic / Advanced / Enterprise
#  - Then do usage cost logic
# ======================================
elif menu == "Client Calculator":
    st.title("Client Calculator")

    # 1) Grab plan selection
    plan_chosen = st.session_state.get("selected_plan", "Enterprise")  # default if not set
    crm_choice = st.session_state.get("crm_choice", "Our CRM")

    # We'll create copies so we can override for Basic/Advanced
    effective_pricing = dict(pricing)
    effective_usage_limits = dict(usage_limits)

    if plan_chosen == "Advanced":
        effective_pricing["base_monthly_cost"] = 21709
        effective_pricing["setup_cost"] = 19200
        effective_pricing["assistant_base_cost"] = 0  # no additional assistants
        effective_usage_limits["base_messages"] = 10000
        effective_usage_limits["base_minutes"] = 600
        effective_usage_limits["cost_per_additional_message"] = 0.11
        effective_usage_limits["cost_per_additional_minute"] = 4.44
        st.session_state["force_num_assistants"] = 1

    elif plan_chosen == "Basic":
        effective_pricing["base_monthly_cost"] = 9869
        effective_pricing["setup_cost"] = 7800
        effective_pricing["assistant_base_cost"] = 0
        effective_usage_limits["base_messages"] = 5000
        effective_usage_limits["base_minutes"] = 300
        effective_usage_limits["cost_per_additional_message"] = 0.11
        effective_usage_limits["cost_per_additional_minute"] = 4.44
        st.session_state["force_num_assistants"] = 1

    else:
        # Enterprise => no overrides
        if "force_num_assistants" in st.session_state:
            del st.session_state["force_num_assistants"]

    # 2) Select currency
    if "selected_currency" not in st.session_state:
        st.session_state["selected_currency"] = "ZAR"
    currency = st.selectbox(
        "Select Currency",
        options=SUPPORTED_CURRENCIES,
        index=SUPPORTED_CURRENCIES.index(st.session_state["selected_currency"]),
        key="currency_selection"
    )
    st.session_state["selected_currency"] = currency

    # 3) Number of Assistants
    default_num_assts = st.session_state.get("client_num_assistants", 1)
    if plan_chosen == "Enterprise":
        num_assistants = st.number_input(
            "Number of Assistants",
            min_value=1, max_value=100,
            value=default_num_assts
        )
    else:
        num_assistants = 1
        st.write(f"**For {plan_chosen} plan, you have 1 Assistant.**")

    # 4) Chat usage
    default_msg_per_chat = st.session_state.get("cc_avg_msg_chat", 10)
    default_monthly_chatters = st.session_state.get("cc_chatters", 0)

    st.subheader("Estimated Monthly Chat Usage")
    colA, colB = st.columns(2)
    with colA:
        avg_messages_chat = st.number_input(
            "Avg Messages/Conversation",
            min_value=0, step=1,
            value=default_msg_per_chat
        )
    with colB:
        people_message = st.number_input(
            "Monthly Chatters",
            min_value=0, step=1,
            value=default_monthly_chatters
        )

    # Calls usage from "Plan & Questions"
    est_monthly_calls = st.session_state.get("est_monthly_calls", 0)
    est_minutes_per_call = st.session_state.get("est_minutes_per_call", 5.0)

    st.write("**From your earlier answers**:")
    st.write(f"- Estimated Monthly Calls: {est_monthly_calls}")
    st.write(f"- Average Minutes per Call: {est_minutes_per_call}")

    # 5) Payment Option (discount logic)
    discounts_enabled = effective_pricing.get("discounts_enabled", True)
    if discounts_enabled:
        payment_plans = [
            "Pay 3 Months Upfront (15% Discount)",
            "3 Month Commitment, Pay Monthly",
            "Pay 12 Months Upfront (18% Discount)",
            "12 Month Commitment, Pay Monthly (5% Discount)"
        ]
    else:
        payment_plans = [
            "3 Month Commitment, Pay Monthly",
            "12 Month Commitment, Pay Monthly"
        ]

    default_payment_option = st.session_state.get("client_payment_option", payment_plans[0])
    payment_option = st.radio(
        "Choose Payment Plan",
        payment_plans,
        index=payment_plans.index(default_payment_option) if default_payment_option in payment_plans else 0
    )

    # 6) Optional Features
    with st.expander("Optional Features"):
        voice_customization_selected = st.checkbox(
            "Include Voice Customization?",
            value=st.session_state.get("client_voice_customization_selected", False)
        )
        want_custom_voices = st.checkbox(
            "Add Additional Custom Voices (beyond English)?",
            value=st.session_state.get("client_want_custom_voices", False)
        )
        if want_custom_voices:
            num_custom_voices = st.number_input(
                "Number of Additional Custom Voices",
                min_value=1, step=1,
                value=st.session_state.get("client_num_custom_voices", 1)
            )
        else:
            num_custom_voices = 0

    # Calculate button
    if st.button("Calculate"):
        # Store in session
        st.session_state["client_num_assistants"] = num_assistants
        st.session_state["cc_avg_msg_chat"] = avg_messages_chat
        st.session_state["cc_chatters"] = people_message
        st.session_state["client_payment_option"] = payment_option
        st.session_state["client_voice_customization_selected"] = voice_customization_selected
        st.session_state["client_want_custom_voices"] = want_custom_voices
        st.session_state["client_num_custom_voices"] = num_custom_voices

        total_used_minutes = est_monthly_calls * est_minutes_per_call
        total_used_messages = people_message * avg_messages_chat

        total_included_messages, total_included_minutes = calculate_usage(num_assistants, effective_usage_limits)
        additional_messages = max(0, total_used_messages - total_included_messages)
        additional_minutes = max(0, total_used_minutes - total_included_minutes)
        overage_cost_msg_zar = additional_messages * effective_usage_limits["cost_per_additional_message"]
        overage_cost_min_zar = additional_minutes * effective_usage_limits["cost_per_additional_minute"]
        total_overage_cost_zar = overage_cost_msg_zar + overage_cost_min_zar

        # Assistants cost
        discount_3_5 = effective_pricing["discount_3_5"]
        discount_6_10 = effective_pricing["discount_6_10"]
        base_per_assistant = effective_pricing["assistant_base_cost"]

        assistant_total_cost_zar = calculate_assistant_cost(
            num_assistants,
            base_per_assistant,
            discount_3_5,
            discount_6_10,
            discounts_enabled
        )

        # Base monthly cost
        base_monthly_cost_zar = effective_pricing["base_monthly_cost"]
        universal_setup_cost_zar = effective_pricing["setup_cost"]

        # Voice customization
        extra_voice_cost_zar = effective_pricing["voice_customization_cost"] if voice_customization_selected else 0
        custom_voice_cost_zar = effective_pricing["custom_voice_cost_per_voice"] * num_custom_voices

        # Monthly Subtotal
        monthly_subtotal_zar = (
            base_monthly_cost_zar
            + assistant_total_cost_zar
            + total_overage_cost_zar
            + extra_voice_cost_zar
            + custom_voice_cost_zar
        )

        # Discount by payment plan
        discount_percentage = 0
        if discounts_enabled:
            if payment_option == "Pay 3 Months Upfront (15% Discount)":
                discount_percentage = 15
            elif payment_option == "Pay 12 Months Upfront (18% Discount)":
                discount_percentage = 18
            elif payment_option == "12 Month Commitment, Pay Monthly (5% Discount)":
                discount_percentage = 5
        final_monthly_rate_zar = monthly_subtotal_zar * (1 - discount_percentage / 100.0)

        # Whitelabel
        whitelabel_fee_zar = 0
        if effective_pricing.get("whitelabel_fee_charged", False):
            if effective_pricing.get("whitelabel_fee_waived", False):
                whitelabel_fee_zar = 0
            else:
                whitelabel_fee_zar = effective_pricing.get("whitelabel_fee", 14550)

        # Setup cost for assistants
        setup_cost_assistants_zar = effective_pricing["setup_cost_per_assistant"] * num_assistants

        # Plan duration
        if "3 Month" in payment_option:
            months_to_pay = 3
        elif "12 Month" in payment_option:
            months_to_pay = 12
        else:
            months_to_pay = 3

        total_cost_zar = (
            final_monthly_rate_zar * months_to_pay
            + universal_setup_cost_zar
            + whitelabel_fee_zar
            + setup_cost_assistants_zar
        )

        # Store final results in session
        st.session_state["client_assistant_total_cost_zar"] = assistant_total_cost_zar
        st.session_state["client_base_monthly_cost_zar"] = base_monthly_cost_zar
        st.session_state["client_universal_setup_cost_zar"] = universal_setup_cost_zar
        st.session_state["client_monthly_subtotal_excl_vat_zar"] = monthly_subtotal_zar
        st.session_state["client_discount_percentage"] = discount_percentage
        st.session_state["client_final_monthly_rate_excl_vat_zar"] = final_monthly_rate_zar
        st.session_state["client_total_overage_cost_zar"] = total_overage_cost_zar
        st.session_state["client_total_cost_excl_vat_zar"] = total_cost_zar
        st.session_state["client_total_included_messages"] = total_included_messages
        st.session_state["client_total_included_minutes"] = total_included_minutes
        st.session_state["client_total_used_messages"] = total_used_messages
        st.session_state["client_total_used_minutes"] = total_used_minutes
        st.session_state["client_extra_messages"] = additional_messages
        st.session_state["client_extra_minutes"] = additional_minutes
        st.session_state["client_whitelabel_fee_zar"] = whitelabel_fee_zar
        st.session_state["client_setup_cost_per_assistant_zar"] = setup_cost_assistants_zar
        st.session_state["client_voice_customization_selected"] = voice_customization_selected
        st.session_state["client_num_custom_voices"] = num_custom_voices
        st.session_state["client_custom_voices_cost_zar"] = custom_voice_cost_zar
        st.session_state["client_monthly_support_hours"] = effective_pricing.get("monthly_support_hours", 0)

        st.success("Calculation done! Visit 'Main Dashboard' or 'Quotation' to see your results.")


# ======================================
# PAGE: Call Centre Cost Calculation
# ======================================
elif menu == "Call Centre Cost Calculation":
    st.title("Call Centre Cost Calculation (Excl. VAT)")
    st.write("Compare your current call centre costs with askAYYI.")

    # Example placeholders: adapt to your usage.
    with st.form("call_centre_form"):
        st.markdown("### Enter your current call centre's monthly costs:")
        
        # A. Personnel
        staff_count = st.number_input("Number of Agents", min_value=0, value=10)
        salary_per_agent = st.number_input("Salary/Agent (ZAR)", min_value=0, value=8000)
        
        # Additional fields as needed...
        # e.g. st.number_input("Medical Aid", ...)
        
        submit_cc = st.form_submit_button("Calculate Call Centre Costs")
        
    if submit_cc:
        # Simple example: monthly_total_callcentre
        monthly_total_callcentre_zar = staff_count * salary_per_agent
        # Store in session
        st.session_state["cc_monthly_total_callcentre_zar"] = monthly_total_callcentre_zar
        # If there are one-time costs, store them as well
        st.session_state["cc_once_off_costs_callcentre_zar"] = 0

        st.success(f"Call centre monthly cost = R{monthly_total_callcentre_zar:,.2f}. Now see Main Dashboard or Quotation.")


# ======================================
# PAGE: Main Dashboard
# ======================================
elif menu == "Main Dashboard":
    st.title("Main Dashboard: Your askAYYI Overview")

    final_monthly_rate_excl_vat_zar = st.session_state.get("client_final_monthly_rate_excl_vat_zar", None)
    if final_monthly_rate_excl_vat_zar is None:
        st.warning("Please calculate your plan under 'Client Calculator' first.")
        st.stop()

    # Retrieve all session data
    num_assistants = safe_int(st.session_state.get("client_num_assistants", 0))
    monthly_subtotal_excl_vat_zar = safe_float(st.session_state.get("client_monthly_subtotal_excl_vat_zar", 0))
    final_monthly_rate_excl_vat_zar = safe_float(st.session_state.get("client_final_monthly_rate_excl_vat_zar", 0))
    total_cost_excl_vat_zar = safe_float(st.session_state.get("client_total_cost_excl_vat_zar", 0))

    total_included_messages = safe_int(st.session_state.get("client_total_included_messages", 0))
    total_used_messages = safe_int(st.session_state.get("client_total_used_messages", 0))
    additional_messages = safe_int(st.session_state.get("client_extra_messages", 0))

    total_included_minutes = safe_int(st.session_state.get("client_total_included_minutes", 0))
    total_used_minutes = safe_int(st.session_state.get("client_total_used_minutes", 0))
    additional_minutes = safe_int(st.session_state.get("client_extra_minutes", 0))

    total_overage_cost_zar = safe_float(st.session_state.get("client_total_overage_cost_zar", 0))
    monthly_support_hours = safe_float(st.session_state.get("client_monthly_support_hours", 0))

    monthly_total_callcentre_zar = safe_float(st.session_state.get("cc_monthly_total_callcentre_zar", None))
    once_off_costs_callcentre_zar = safe_float(st.session_state.get("cc_once_off_costs_callcentre_zar", None))

    selected_currency = st.session_state.get("selected_currency", "ZAR")
    symbol = get_currency_symbol(selected_currency)

    # Convert certain values for display
    final_monthly_rate_excl_vat = convert_currency(final_monthly_rate_excl_vat_zar, selected_currency, exchange_rates)
    total_cost_excl_vat = convert_currency(total_cost_excl_vat_zar, selected_currency, exchange_rates)

    st.subheader("Your askAYYI Costs (Excl. VAT)")
    st.write(f"**Monthly Rate:** {symbol}{final_monthly_rate_excl_vat:,.2f}")
    st.write(f"**Plan Total:** {symbol}{total_cost_excl_vat:,.2f} (includes setup fees, if any)")

    st.subheader("Usage Overview")
    st.write(f"Included Messages: {total_included_messages:,}")
    st.write(f"Included Minutes: {total_included_minutes:,}")
    st.write(f"Extra Messages above plan: {additional_messages:,}")
    st.write(f"Extra Minutes above plan: {additional_minutes:,}")

    if monthly_support_hours > 0:
        st.info(f"Monthly Support Hours Included: {monthly_support_hours:.1f}")

    if monthly_total_callcentre_zar is not None:
        monthly_total_callcentre = convert_currency(monthly_total_callcentre_zar, selected_currency, exchange_rates)
        st.subheader("Call Centre Comparison")
        st.write(f"Your existing call centre monthly cost: {symbol}{monthly_total_callcentre:,.2f}")
        if once_off_costs_callcentre_zar:
            once_off_costs_callcentre = convert_currency(once_off_costs_callcentre_zar, selected_currency, exchange_rates)
            st.write(f"Call Centre one-time costs: {symbol}{once_off_costs_callcentre:,.2f}")

        monthly_savings = monthly_total_callcentre - final_monthly_rate_excl_vat
        if monthly_savings > 0:
            st.success(f"You could save about {symbol}{monthly_savings:,.2f} per month with askAYYI.")
        else:
            st.warning(f"It appears you'd spend {-monthly_savings:,.2f} more with askAYYI (negative savings).")

    else:
        st.info("No call centre data yet. Calculate that under 'Call Centre Cost Calculation'.")


# ======================================
# PAGE: Quotation
# ======================================
elif menu == "Quotation":
    st.title("Quotation: Detailed Breakdown")

    final_monthly_rate_excl_vat_zar = st.session_state.get("client_final_monthly_rate_excl_vat_zar", None)
    if final_monthly_rate_excl_vat_zar is None:
        st.warning("Please complete 'Client Calculator' first to generate details.")
        st.stop()

    # Gather details
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    exchange_rate = exchange_rates.get(selected_currency, 1)
    symbol = get_currency_symbol(selected_currency)

    num_assistants = st.session_state.get("client_num_assistants", 0)
    base_monthly_cost_zar = st.session_state.get("client_base_monthly_cost_zar", 0)
    assistant_cost_zar = st.session_state.get("client_assistant_total_cost_zar", 0)
    universal_setup_cost_zar = st.session_state.get("client_universal_setup_cost_zar", 0)
    payment_option = st.session_state.get("client_payment_option", "Not Specified")
    discount_percentage = st.session_state.get("client_discount_percentage", 0)
    monthly_subtotal_excl_vat_zar = st.session_state.get("client_monthly_subtotal_excl_vat_zar", 0)
    final_monthly_rate_excl_vat_zar = st.session_state.get("client_final_monthly_rate_excl_vat_zar", 0)
    total_cost_excl_vat_zar = st.session_state.get("client_total_cost_excl_vat_zar", 0)

    total_included_messages = st.session_state.get("client_total_included_messages", 0)
    total_included_minutes = st.session_state.get("client_total_included_minutes", 0)
    total_used_messages = st.session_state.get("client_total_used_messages", 0)
    total_used_minutes = st.session_state.get("client_total_used_minutes", 0)
    additional_messages = st.session_state.get("client_extra_messages", 0)
    additional_minutes = st.session_state.get("client_extra_minutes", 0)
    total_overage_cost_zar = st.session_state.get("client_total_overage_cost_zar", 0)

    whitelabel_fee_charged = st.session_state.get("client_whitelabel_fee_charged", False)
    whitelabel_fee_waived = st.session_state.get("client_whitelabel_fee_waived", False)
    whitelabel_fee_zar = st.session_state.get("client_whitelabel_fee_zar", 0)
    setup_cost_for_assistants_zar = st.session_state.get("client_setup_cost_per_assistant_zar", 0)
    monthly_support_hours = st.session_state.get("client_monthly_support_hours", 0)

    voice_customization_selected = st.session_state.get("client_voice_customization_selected", False)
    voice_customization_cost_zar = pricing.get("voice_customization_cost", 0) if voice_customization_selected else 0

    num_custom_voices = st.session_state.get("client_num_custom_voices", 0)
    custom_voices_cost_zar = st.session_state.get("client_custom_voices_cost_zar", 0)

    # Determine plan length
    if "3 Month" in payment_option:
        plan_months = 3
    elif "12 Month" in payment_option:
        plan_months = 12
    else:
        plan_months = 3

    # Convert to selected currency
    assistant_cost = convert_currency(assistant_cost_zar, selected_currency, exchange_rates)
    base_monthly_cost = convert_currency(base_monthly_cost_zar, selected_currency, exchange_rates)
    universal_setup_cost = convert_currency(universal_setup_cost_zar, selected_currency, exchange_rates)
    setup_cost_for_assistants = convert_currency(setup_cost_for_assistants_zar, selected_currency, exchange_rates)
    whitelabel_fee = convert_currency(whitelabel_fee_zar, selected_currency, exchange_rates)
    monthly_subtotal_excl_vat = convert_currency(monthly_subtotal_excl_vat_zar, selected_currency, exchange_rates)
    final_monthly_rate_excl_vat = convert_currency(final_monthly_rate_excl_vat_zar, selected_currency, exchange_rates)
    total_cost_excl_vat = convert_currency(total_cost_excl_vat_zar, selected_currency, exchange_rates)
    total_overage_cost = convert_currency(total_overage_cost_zar, selected_currency, exchange_rates)
    custom_voices_cost = convert_currency(custom_voices_cost_zar, selected_currency, exchange_rates)
    voice_customization_cost = convert_currency(voice_customization_cost_zar, selected_currency, exchange_rates)

    # Build an itemized list
    invoice_items = []

    # 1) Base Monthly Cost
    invoice_items.append({
        "Description": "Base Monthly Cost",
        "Amount": f"{symbol}{base_monthly_cost:,.2f}",
        "Explanation": "A flat monthly fee for the Master Assistant."
    })
    # 2) Assistant(s) Monthly
    invoice_items.append({
        "Description": f"Assistant Monthly Cost (for {num_assistants} assistant(s))",
        "Amount": f"{symbol}{assistant_cost:,.2f}",
        "Explanation": "Sum of each assistant cost, including any volume discounts (if enabled)."
    })
    # 3) Voice Customization
    if voice_customization_selected:
        invoice_items.append({
            "Description": "Voice Customization Monthly",
            "Amount": f"{symbol}{voice_customization_cost:,.2f}",
            "Explanation": "Optional feature if you chose voice customization."
        })
    # 4) Custom Voices
    if num_custom_voices > 0:
        invoice_items.append({
            "Description": "Custom Voices Monthly",
            "Amount": f"{symbol}{custom_voices_cost:,.2f}",
            "Explanation": f"{num_custom_voices} voice(s) beyond standard English."
        })
    # 5) Overage
    if total_overage_cost > 0:
        invoice_items.append({
            "Description": "Overage Cost (Messages/Minutes)",
            "Amount": f"{symbol}{total_overage_cost:,.2f}",
            "Explanation": "Usage above included messages/minutes."
        })
    # 6) Subtotal monthly
    invoice_items.append({
        "Description": "Monthly Subtotal",
        "Amount": f"{symbol}{monthly_subtotal_excl_vat:,.2f}",
        "Explanation": "Sum of base, assistants, voice, custom voices, overages, etc."
    })
    # 7) Discount
    discounts_enabled = pricing.get("discounts_enabled", True)
    if discounts_enabled and discount_percentage > 0:
        discount_amount = monthly_subtotal_excl_vat * (discount_percentage / 100.0)
        invoice_items.append({
            "Description": f"Discount ({discount_percentage}%)",
            "Amount": f"-{symbol}{discount_amount:,.2f}",
            "Explanation": "Reduced rate from your selected payment plan."
        })
    # 8) Final monthly rate
    invoice_items.append({
        "Description": "Final Monthly askAYYI Cost",
        "Amount": f"{symbol}{final_monthly_rate_excl_vat:,.2f}",
        "Explanation": "What you'll pay monthly under the plan."
    })
    # 9) Plan Duration
    invoice_items.append({
        "Description": "Plan Duration (months)",
        "Amount": f"{plan_months}",
        "Explanation": "Chosen plan commits you for this many months."
    })
    # 10) Universal Setup
    invoice_items.append({
        "Description": "Universal Setup Cost (one-time)",
        "Amount": f"{symbol}{universal_setup_cost:,.2f}",
        "Explanation": "A one-time cost to configure the system."
    })
    # 11) Setup per Assistant
    invoice_items.append({
        "Description": f"Setup Cost for {num_assistants} Assistant(s)",
        "Amount": f"{symbol}{setup_cost_for_assistants:,.2f}",
        "Explanation": "One-time cost (setup_cost_per_assistant × number_of_assistants)."
    })
    # 12) Whitelabel Fee
    if whitelabel_fee_charged:
        if whitelabel_fee_waived:
            standard_whitelabel_fee_converted = convert_currency(pricing.get("whitelabel_fee", 14550), selected_currency, exchange_rates)
            invoice_items.append({
                "Description": "Whitelabel Fee (Waived)",
                "Amount": f"{symbol}0.00",
                "Explanation": f"Normally {symbol}{standard_whitelabel_fee_converted:,.2f}, but waived."
            })
        else:
            invoice_items.append({
                "Description": "Whitelabel Fee",
                "Amount": f"{symbol}{whitelabel_fee:,.2f}",
                "Explanation": "A one-time branding fee for whitelabeling."
            })
    # 13) Overall Plan Total
    invoice_items.append({
        "Description": "Overall Plan Total (Excl. VAT)",
        "Amount": f"{symbol}{total_cost_excl_vat:,.2f}",
        "Explanation": "(Monthly Final Rate × Plan Months) + Setup(s) + Whitelabel Fee."
    })

    df_invoice = pd.DataFrame(invoice_items)

    st.write("**Quotation Items**")
    st.table(df_invoice)

    # Usage details
    st.markdown("---")
    st.write("### Usage Details")
    usage_details = [
        {"Metric": "Included Messages", "Value": f"{total_included_messages:,}"},
        {"Metric": "Used Messages", "Value": f"{total_used_messages:,}"},
        {"Metric": "Additional (Over) Messages", "Value": f"{additional_messages:,}"},
        {"Metric": "Included Minutes", "Value": f"{total_included_minutes:,}"},
        {"Metric": "Used Minutes", "Value": f"{total_used_minutes:,}"},
        {"Metric": "Additional (Over) Minutes", "Value": f"{additional_minutes:,}"},
    ]
    df_usage = pd.DataFrame(usage_details)
    st.table(df_usage)

    if monthly_support_hours > 0:
        st.info(f"Monthly Support Hours Included: {monthly_support_hours} hrs")

    st.success("This concludes the full itemized breakdown of your askAYYI invoice!")
