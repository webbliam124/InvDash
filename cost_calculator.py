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
EXCHANGE_RATES_FILE = os.path.join(CONFIG_DIR, 'exchange_rates.json')  # New Configuration File

# ======================================
# DEFAULT CONFIGURATIONS
#  - Provides baseline settings if no custom config is found
# ======================================
DEFAULT_PRICING = {
    "base_monthly_cost": 94600,       # Up to 5 assistants
    "setup_cost": 20000,              # One-time universal setup
    "assistant_base_cost": 10000,     # R10k per assistant
    "discount_3_5": 8,                # 8% discount for #3-5
    "discount_6_10": 12,              # 12% discount for #6-10

    # Legacy references (not used directly, kept for reference)
    "pay_3month_discount": 15,
    "pay_12month_discount": 18,

    # Renamed fields for clarity:
    "voice_customization_cost": 0,       # Monthly voice customization
    "setup_cost_per_assistant": 7800,    # One-time cost per assistant
    "whitelabel_fee": 14550,             # One-time whitelabel fee
    "whitelabel_fee_charged": False,    
    "whitelabel_fee_waived": False,     
    "monthly_support_hours": 0,

    # NEW: Cost for each additional custom voice (beyond English)
    "custom_voice_cost_per_voice": 0,

    # NEW: Discounts Enabled Flag
    "discounts_enabled": True  # Indicates if discounts are active
}

DEFAULT_USAGE_LIMITS = {
    "base_messages": 100000,          
    "base_minutes": 10000,            
    "assistant_extra_messages": 8000, 
    "assistant_extra_minutes": 300,   
    "cost_per_additional_message": 0.09,
    "cost_per_additional_minute": 3.33
}

# UPDATED: Exchange Rates as "Currency to ZAR"
DEFAULT_EXCHANGE_RATES = {
    "EUR": 19.0,  # Example rate: 1 EUR = 19 ZAR
    "USD": 16.0,  # Example rate: 1 USD = 16 ZAR
    "AED": 4.4    # Example rate: 1 AED = 4.4 ZAR
}

# Currency Symbols
CURRENCY_SYMBOLS = {
    "ZAR": "R",
    "EUR": "€",
    "USD": "$",
    "AED": "د.إ"
}

# Supported Currencies
SUPPORTED_CURRENCIES = ["ZAR", "EUR", "USD", "AED"]

# ======================================
# HELPER FUNCTIONS
#  - Each function is 10 words or less in description
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
    
    # Initialize Pricing Config
    if not os.path.isfile(PRICING_FILE):
        with open(PRICING_FILE, 'w') as f:
            json.dump(DEFAULT_PRICING, f, indent=4)
    else:
        # Load existing pricing and ensure 'discounts_enabled' is present
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
    
    # Initialize Usage Limits Config
    if not os.path.isfile(USAGE_LIMITS_FILE):
        with open(USAGE_LIMITS_FILE, 'w') as f:
            json.dump(DEFAULT_USAGE_LIMITS, f, indent=4)
    
    # Initialize Exchange Rates Config
    if not os.path.isfile(EXCHANGE_RATES_FILE):
        with open(EXCHANGE_RATES_FILE, 'w') as f:
            json.dump(DEFAULT_EXCHANGE_RATES, f, indent=4)  # Initialize Exchange Rates

def load_config(file_path):
    """Load JSON config or raise error."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading config: {e}")
        return None

def save_config(file_path, data):
    """Save config data to JSON safely."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        st.error(f"Error saving config: {e}")

def apply_custom_css():
    """Apply consistent app styling."""
    st.markdown(
        """
        <style>
        /* Overall App */
        .stApp {
            background-color: #FFFFFF;
            color: #191937;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        /* Sidebar */
        .sidebar .sidebar-content {
            background-color: #F0F2F6;
        }
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #5fba6a;
            font-family: 'Arial Black', Gadget, sans-serif;
        }
        /* NEUTRAL Buttons */
        .stButton > button {
            background-color: #CCCCCC;
            color: #000000;
            border: none;
            padding: 10px 24px;
            text-align: center;
            font-size: 16px;
            cursor: pointer;
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #AAAAAA;
        }
        /* Input Label */
        label {
            color: #191937 !important;
            font-weight: bold;
        }
        /* Radio/Checkbox text */
        .stCheckbox > label > div > div, .stRadio > label > div {
            color: #191937;
            font-weight: normal;
        }
        /* Sliders */
        .stSlider > label {
            color: #191937;
            font-weight: bold;
        }
        /* Simple tooltips */
        [data-tooltip] {
            position: relative;
            cursor: help;
        }
        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            background-color: #191937;
            color: #FFFFFF;
            padding: 5px 10px;
            border-radius: 5px;
            top: -5px;
            left: 105%;
            white-space: nowrap;
            z-index: 1000;
            font-size: 12px;
        }
        /* Table */
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
        /* Card-like containers */
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
        /* Highlight style for total */
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

def authenticate_admin():
    """Simple password check for admin."""
    def check_password():
        def password_entered():
            if st.session_state.get("password", "") == "RCS_18112":
                st.session_state["password_correct"] = True
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            st.text_input(
                "Enter Admin Password",
                type="password",
                on_change=password_entered,
                key="password",
            )
            return False
        elif not st.session_state["password_correct"]:
            st.text_input(
                "Enter Admin Password",
                type="password",
                on_change=password_entered,
                key="password",
            )
            st.error("Incorrect Password")
            return False
        else:
            return True

    return check_password()

def calculate_assistant_cost(num_assistants, base_per_assistant, discount_3_5, discount_6_10, discounts_enabled=True):
    """Compute total monthly cost for assistants with discounts."""
    total_cost = 0
    breakdown = []
    # Defensive: ensure no negative inputs
    num_assistants = max(num_assistants, 0)
    base_per_assistant = max(base_per_assistant, 0)

    # If discounts are disabled, set discount to 0
    if not discounts_enabled:
        discount_3_5 = 0
        discount_6_10 = 0

    discount_3_5 = max(discount_3_5, 0)
    discount_6_10 = max(discount_6_10, 0)

    for i in range(1, num_assistants + 1):
        if i <= 2:
            discount_rate = 0.0
        elif 3 <= i <= 5:
            discount_rate = discount_3_5 / 100.0
        else:  # 6 to 10
            discount_rate = discount_6_10 / 100.0
        
        cost_for_this_assistant = base_per_assistant * (1 - discount_rate)
        total_cost += cost_for_this_assistant
        breakdown.append({
            "assistant_num": i,
            "base_cost": base_per_assistant,
            "discount_rate": discount_rate,
            "discounted_cost": cost_for_this_assistant
        })
    return total_cost, breakdown

def calculate_usage(num_assistants, usage_limits):
    """Calculate included messages/minutes based on assistant count."""
    # Defensive: ensure no negative inputs
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

def get_exchange_rates():
    """Load exchange rates from config."""
    return load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES

def save_exchange_rates(rates):
    """Save exchange rates to config."""
    save_config(EXCHANGE_RATES_FILE, rates)

def convert_currency(amount_zar, currency, exchange_rates):
    """Convert ZAR to selected currency with 30% increase if not ZAR."""
    if currency == "ZAR":
        return amount_zar
    rate = exchange_rates.get(currency, 1)  # ZAR per 1 Currency
    return (amount_zar / rate) * 1.3  # Apply 30% increase

def get_currency_symbol(currency):
    """Get symbol for the selected currency."""
    return CURRENCY_SYMBOLS.get(currency, "R")

# ======================================
# INIT CONFIGS
#  - Load or create JSON files
# ======================================
initialize_configs()
pricing = load_config(PRICING_FILE) or DEFAULT_PRICING
usage_limits = load_config(USAGE_LIMITS_FILE) or DEFAULT_USAGE_LIMITS
exchange_rates = get_exchange_rates()

# ======================================
# STREAMLIT APP
#  - Main UI and navigation
# ======================================
st.set_page_config(page_title="askAYYI Cost Calculator", layout="wide")
apply_custom_css()

# ======================================
# SIDEBAR NAVIGATION
#  - Displays logo and menu
# ======================================
st.sidebar.image(
    "https://static.wixstatic.com/media/bde46d_5c23110f863c4083b92f963a4bcd6b31~mv2.png/v1/fill/w_202,h_64,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/ASkAYYI.png",
    width=200
)

menu = st.sidebar.radio(
    "Navigation",
    [
        "Admin Dashboard", 
        "Client Calculator", 
        "Call Centre Cost Calculation",
        "Main Dashboard",
        "Quotation"  # <-- ADDED a new tab for the itemized invoice
    ]
)

# ======================================
# PAGE: Admin Dashboard
#  - Adjust all pricing/usage/exchange rate settings
# ======================================
if menu == "Admin Dashboard":
    if authenticate_admin():
        st.title("Admin Dashboard")

        # ----------------------------------
        # Pricing Configuration Form
        # ----------------------------------
        st.header("Pricing Configuration")
        with st.form("pricing_form"):
            col1, col2 = st.columns(2)
            with col1:
                base_monthly_cost = st.number_input(
                    "Base Monthly Cost (ZAR)",
                    value=pricing.get('base_monthly_cost', 94600),
                    step=1000,
                    format="%i",
                    help="Covers up to 5 assistants"
                )
                setup_cost = st.number_input(
                    "Universal Setup Cost (ZAR)",
                    value=pricing.get('setup_cost', 20000),
                    step=1000,
                    format="%i",
                    help="One-time universal cost"
                )
                assistant_base_cost = st.number_input(
                    "Assistant Base Monthly Cost (ZAR)",
                    value=pricing.get('assistant_base_cost', 10000),
                    step=1000,
                    format="%i",
                    help="Before any volume discounts"
                )
                setup_cost_per_assistant = st.number_input(
                    "Setup Cost Per Assistant (ZAR)",
                    value=pricing.get('setup_cost_per_assistant', 7800),
                    step=1000,
                    format="%i",
                    help="One-time cost per assistant"
                )
            with col2:
                discount_3_5 = st.number_input(
                    "Discount for Assistants #3-5 (%)",
                    value=pricing.get('discount_3_5', 8),
                    min_value=0,
                    max_value=100,
                    step=1,
                    help="Applies to 3rd to 5th assistant"
                )
                discount_6_10 = st.number_input(
                    "Discount for Assistants #6-10 (%)",
                    value=pricing.get('discount_6_10', 12),
                    min_value=0,
                    max_value=100,
                    step=1,
                    help="Applies to 6th to 10th assistant"
                )
                voice_customization_cost = st.number_input(
                    "Voice Customization Monthly (ZAR)",
                    value=pricing.get('voice_customization_cost', 0),
                    step=500,
                    format="%i",
                    help="Extra monthly if voice chosen"
                )

            st.markdown("*(Legacy references for record only)*")
            pay_3month_discount = st.number_input(
                "Legacy 3-Month (%)",
                value=pricing.get('pay_3month_discount', 15),
                min_value=0,
                max_value=100,
                step=1
            )
            pay_12month_discount = st.number_input(
                "Legacy 12-Month (%)",
                value=pricing.get('pay_12month_discount', 18),
                min_value=0,
                max_value=100,
                step=1
            )

            st.markdown("---")
            st.subheader("Whitelabel Fee Configuration")
            whitelabel_fee_charged = st.checkbox(
                "Charge Whitelabel Fee (ZAR 14,550)?", 
                value=pricing.get("whitelabel_fee_charged", False),
                help="If checked, add ZAR 14,550 once-off (unless waived)."
            )
            whitelabel_fee_waived = st.checkbox(
                "Waive Whitelabel Fee?",
                value=pricing.get("whitelabel_fee_waived", False),
                help="If checked, show fee but charge ZAR 0."
            )

            st.markdown("---")
            st.subheader("Technical Support Hours Included")
            monthly_support_hours = st.number_input(
                "Monthly Support Hours",
                value=pricing.get("monthly_support_hours", 0),
                min_value=0,
                step=1,
                help="Hours included for support"
            )

            st.markdown("---")
            st.subheader("Custom Voice Configuration")
            custom_voice_cost_per_voice = st.number_input(
                "Custom Voice Cost (Monthly Per Voice) (ZAR)",
                value=pricing.get("custom_voice_cost_per_voice", 0),
                step=500,
                format="%i",
                help="Monthly cost for each additional custom voice (beyond English)."
            )

            # Submit button for Pricing Form
            save_pricing_btn = st.form_submit_button("Save Pricing Configuration")
            if save_pricing_btn:
                # Update pricing dictionary
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
                    continue  # ZAR is the base currency
                exchange_rate_inputs[currency] = st.number_input(
                    f"Exchange Rate for {currency} (1 {currency} = X ZAR)",
                    value=exchange_rates.get(currency, DEFAULT_EXCHANGE_RATES.get(currency, 1)),
                    step=0.001,
                    format="%.3f",
                    help=f"Current exchange rate: 1 {currency} = X ZAR"
                )
            save_exchange_rates_btn = st.form_submit_button("Save Exchange Rates")
            if save_exchange_rates_btn:
                # Update exchange rates
                for currency, rate in exchange_rate_inputs.items():
                    exchange_rates[currency] = rate
                save_exchange_rates(exchange_rates)
                st.success("Exchange rates updated successfully!")

        st.markdown("---")
        st.header("Discounts Configuration")

        # Display current discount status
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
# PAGE: Client Calculator
#  - Main cost calculation for askAYYI solution
# ======================================
elif menu == "Client Calculator":
    st.title("Client Calculator")
    st.write("Fill in your details and click **Calculate**.")

    # Currency Selection
    if "selected_currency" not in st.session_state:
        st.session_state["selected_currency"] = "ZAR"  # Default Currency

    currency = st.selectbox(
        "Select Currency",
        options=SUPPORTED_CURRENCIES,
        index=SUPPORTED_CURRENCIES.index(st.session_state["selected_currency"]) if st.session_state["selected_currency"] in SUPPORTED_CURRENCIES else 0,
        key="currency_selection",
        help="Choose the currency for your pricing."
    )
    st.session_state["selected_currency"] = currency

    # Option to load last inputs if available
    if "client_num_assistants" in st.session_state:
        if st.button("Load Last Inputs"):
            st.info("Loaded previous session data. Verify then recalculate.")

    with st.form("client_calculator_form"):
        st.subheader("askAYYI Inputs")

        default_num_assts = st.session_state.get("client_num_assistants", 1)
        default_avg_call_len = st.session_state.get("cc_avg_call_len", 5.0)
        default_callers = st.session_state.get("cc_callers", 0)
        default_avg_msg_chat = st.session_state.get("cc_avg_msg_chat", 10)
        default_chatters = st.session_state.get("cc_chatters", 0)

        num_assistants = st.number_input(
            label="Number of Assistants",
            min_value=0,  # allow zero for robust handling
            max_value=100,
            value=default_num_assts,
            step=1,
            help="How many AI Assistants needed?"
        )

        st.subheader("Estimated Monthly Usage")
        colA, colB = st.columns(2)
        with colA:
            avg_minutes_call = st.number_input(
                label="Avg Call Length (min)",
                min_value=0.0,
                value=default_avg_call_len,
                step=0.5,
                format="%.1f",
                help="Approx average call duration"
            )
            people_call = st.number_input(
                label="Monthly Callers",
                min_value=0,
                value=st.session_state.get("cc_callers", default_callers),
                step=1,
                help="Estimated number of monthly callers"
            )
        with colB:
            avg_messages_chat = st.number_input(
                label="Avg Messages/Conversation",
                min_value=0,
                value=default_avg_msg_chat,
                step=1,
                format="%i",
                help="Approx messages in a typical text conversation"
            )
            people_message = st.number_input(
                label="Monthly Chatters",
                min_value=0,
                value=st.session_state.get("cc_chatters", default_chatters),
                step=1,
                help="Estimated number of monthly chatters"
            )

        # Voice Customization Option
        voice_customization_selected = st.checkbox(
            "Include Voice Customization?",
            value=st.session_state.get("client_voice_customization_selected", False),
            help="Adds monthly cost if enabled."
        )

        # Multi Lingual Support Option
        Multi_Lingual_Support = st.checkbox(
            "Include Multi Lingual Support?",
            value=False,
            help="Adds monthly cost if enabled."
        )
        
        # NEW: Custom Voices
        st.subheader("Custom Voices (Beyond English)")
        want_custom_voices = st.checkbox(
            "Add Custom Voices?",
            value=st.session_state.get("client_want_custom_voices", False),
            help="If you need voices beyond standard English."
        )
        if want_custom_voices:
            num_custom_voices = st.number_input(
                "Number of Additional Custom Voices",
                min_value=0,
                step=1,
                value=st.session_state.get("client_num_custom_voices", 0)
            )
        else:
            num_custom_voices = 0

        # Retrieve discounts_enabled flag
        discounts_enabled = pricing.get("discounts_enabled", True)

        # Payment or Plan Options
        if discounts_enabled:
            st.subheader("Payment Option")
            payment_plans = [
                "Pay 3 Months Upfront (15% Discount)",
                "3 Month Commitment, Pay Monthly",
                "Pay 12 Months Upfront (18% Discount)",
                "12 Month Commitment, Pay Monthly (5% Discount)"
            ]
        else:
            # If discounts are disabled, remove all mention of discounts
            st.subheader("Payment Option")
            payment_plans = [
                "3 Month Commitment, Pay Monthly",
                "12 Month Commitment, Pay Monthly"
            ]

        default_pay_option = st.session_state.get("client_payment_option", payment_plans[-1])
        try:
            default_plan_index = payment_plans.index(default_pay_option)
        except ValueError:
            default_plan_index = 0

        payment_option = st.radio(
            "Choose Plan",
            payment_plans,
            index=default_plan_index
        )

        calc_btn = st.form_submit_button("Calculate")

    if calc_btn:
        # Store form inputs in session
        st.session_state["client_num_assistants"] = num_assistants
        st.session_state["cc_avg_call_len"] = avg_minutes_call
        st.session_state["cc_callers"] = people_call
        st.session_state["cc_avg_msg_chat"] = avg_messages_chat
        st.session_state["cc_chatters"] = people_message
        st.session_state["client_payment_option"] = payment_option
        st.session_state["client_voice_customization_selected"] = voice_customization_selected
        st.session_state["client_want_custom_voices"] = want_custom_voices
        st.session_state["client_num_custom_voices"] = num_custom_voices

        # 1) Assistant cost (MONTHLY)
        assistant_total_cost_zar, _ = calculate_assistant_cost(
            num_assistants,
            pricing.get("assistant_base_cost", 0),
            pricing.get("discount_3_5", 0),
            pricing.get("discount_6_10", 0),
            discounts_enabled=discounts_enabled
        )

        # 2) Base monthly cost
        base_monthly_cost_zar = max(pricing.get("base_monthly_cost", 0), 0)
        universal_setup_cost_zar = max(pricing.get("setup_cost", 0), 0)

        # 3) Usage included
        total_included_messages, total_included_minutes = calculate_usage(num_assistants, usage_limits)

        # 4) Actual usage (rough estimate)
        total_used_messages = (people_message * avg_messages_chat)
        total_used_minutes = (people_call * avg_minutes_call)

        # 5) Overages
        additional_messages = max(0, total_used_messages - total_included_messages)
        additional_minutes = max(0, total_used_minutes - total_included_minutes)
        overage_cost_msg_zar = additional_messages * max(usage_limits.get("cost_per_additional_message", 0), 0)
        overage_cost_min_zar = additional_minutes * max(usage_limits.get("cost_per_additional_minute", 0), 0)
        total_overage_cost_zar = overage_cost_msg_zar + overage_cost_min_zar

        # 6) Voice customization monthly
        extra_voice_cost_zar = pricing.get("voice_customization_cost", 0) if voice_customization_selected else 0

        # 6a) Custom voices monthly cost
        custom_voice_cost_per_voice_zar = pricing.get("custom_voice_cost_per_voice", 0)
        total_custom_voice_cost_zar = num_custom_voices * custom_voice_cost_per_voice_zar

        # 7) Monthly Subtotal
        monthly_subtotal_excl_vat_zar = (
            base_monthly_cost_zar 
            + assistant_total_cost_zar 
            + total_overage_cost_zar 
            + extra_voice_cost_zar
            + total_custom_voice_cost_zar
        )

        # 8) Payment plan discount (only if discounts are enabled)
        discount_percentage = 0
        if discounts_enabled:
            if payment_option == "Pay 3 Months Upfront (15% Discount)":
                discount_percentage = 15
            elif payment_option == "3 Month Commitment, Pay Monthly":
                discount_percentage = 0
            elif payment_option == "Pay 12 Months Upfront (18% Discount)":
                discount_percentage = 18
            elif payment_option == "12 Month Commitment, Pay Monthly (5% Discount)":
                discount_percentage = 5
        else:
            discount_percentage = 0  # no discount at all

        final_monthly_rate_excl_vat_zar = monthly_subtotal_excl_vat_zar * (1 - discount_percentage / 100.0)

        # 9) Whitelabel fee
        whitelabel_fee_zar = 0
        if pricing.get("whitelabel_fee_charged", False):
            if pricing.get("whitelabel_fee_waived", False):
                whitelabel_fee_zar = 0  # Show but do not charge
            else:
                whitelabel_fee_zar = pricing.get("whitelabel_fee", 14550)

        # 10) Setup cost for all assistants
        setup_cost_per_asst_zar = max(pricing.get("setup_cost_per_assistant", 0), 0) * num_assistants

        # 11) Plan length
        if "3 Month" in payment_option:
            months_to_pay = 3
        elif "12 Month" in payment_option:
            months_to_pay = 12
        else:
            months_to_pay = 3  # fallback

        # 12) Final total
        total_cost_excl_vat_zar = (
            final_monthly_rate_excl_vat_zar * months_to_pay 
            + universal_setup_cost_zar 
            + whitelabel_fee_zar 
            + setup_cost_per_asst_zar
        )

        # Store all final results
        st.session_state["client_assistant_total_cost_zar"] = assistant_total_cost_zar
        st.session_state["client_base_monthly_cost_zar"] = base_monthly_cost_zar
        st.session_state["client_universal_setup_cost_zar"] = universal_setup_cost_zar
        st.session_state["client_discount_percentage"] = discount_percentage
        st.session_state["client_monthly_subtotal_excl_vat_zar"] = monthly_subtotal_excl_vat_zar
        st.session_state["client_final_monthly_rate_excl_vat_zar"] = final_monthly_rate_excl_vat_zar
        st.session_state["client_total_cost_excl_vat_zar"] = total_cost_excl_vat_zar

        st.session_state["client_total_included_messages"] = total_included_messages
        st.session_state["client_total_included_minutes"] = total_included_minutes
        st.session_state["client_total_used_messages"] = total_used_messages
        st.session_state["client_total_used_minutes"] = total_used_minutes
        st.session_state["client_extra_messages"] = additional_messages
        st.session_state["client_extra_minutes"] = additional_minutes
        st.session_state["client_total_overage_cost_zar"] = total_overage_cost_zar

        st.session_state["client_whitelabel_fee_charged"] = pricing.get("whitelabel_fee_charged", False)
        st.session_state["client_whitelabel_fee_waived"] = pricing.get("whitelabel_fee_waived", False)
        st.session_state["client_whitelabel_fee_zar"] = whitelabel_fee_zar
        st.session_state["client_setup_cost_per_assistant_zar"] = setup_cost_per_asst_zar
        st.session_state["client_monthly_support_hours"] = pricing.get("monthly_support_hours", 0)

        # Store custom voices cost
        st.session_state["client_custom_voices_cost_zar"] = total_custom_voice_cost_zar

        # Convert all relevant amounts to selected currency
        selected_currency = st.session_state["selected_currency"]
        symbol = get_currency_symbol(selected_currency)
        st.session_state["client_assistant_total_cost"] = convert_currency(assistant_total_cost_zar, selected_currency, exchange_rates)
        st.session_state["client_base_monthly_cost"] = convert_currency(base_monthly_cost_zar, selected_currency, exchange_rates)
        st.session_state["client_universal_setup_cost"] = convert_currency(universal_setup_cost_zar, selected_currency, exchange_rates)
        st.session_state["client_monthly_subtotal_excl_vat"] = convert_currency(monthly_subtotal_excl_vat_zar, selected_currency, exchange_rates)
        st.session_state["client_final_monthly_rate_excl_vat"] = convert_currency(final_monthly_rate_excl_vat_zar, selected_currency, exchange_rates)
        st.session_state["client_total_cost_excl_vat"] = convert_currency(total_cost_excl_vat_zar, selected_currency, exchange_rates)

        st.session_state["client_total_overage_cost"] = convert_currency(total_overage_cost_zar, selected_currency, exchange_rates)

        st.session_state["client_whitelabel_fee"] = convert_currency(whitelabel_fee_zar, selected_currency, exchange_rates)
        st.session_state["client_setup_cost_per_assistant"] = convert_currency(setup_cost_per_asst_zar, selected_currency, exchange_rates)

        # Store custom voices cost
        st.session_state["client_custom_voices_cost"] = convert_currency(total_custom_voice_cost_zar, selected_currency, exchange_rates)

        st.success("Calculation done! Go to **Call Centre Cost Calculation**, **Main Dashboard**, or **Quotation** next.")

# ======================================
# PAGE: Call Centre Cost Calculation
#  - Compare existing center costs to askAYYI
# ======================================
elif menu == "Call Centre Cost Calculation":
    st.title("Call Centre Cost Calculation (Excl. VAT)")
    st.write("Compare your current call centre costs with askAYYI.")

    if "callcentre_staff_count" in st.session_state:
        if st.button("Load Last Call Centre Inputs"):
            st.info("Loaded previous data. Verify then recalculate.")

    with st.form("call_centre_form"):
        st.markdown("### A. Personnel Costs")
        c1, c2, c3, c4 = st.columns(4)

        default_staff_count = st.session_state.get("callcentre_staff_count", 10)
        default_salary_per_agent = st.session_state.get("callcentre_salary_per_agent", 8000)
        default_medical_aid_per_agent = st.session_state.get("callcentre_medical_aid_per_agent", 2000)
        default_pension_percent = st.session_state.get("callcentre_pension_percent", 7)
        default_bonus_per_agent = st.session_state.get("callcentre_bonus_per_agent", 1500)
        default_benefits_per_agent = st.session_state.get("callcentre_benefits_per_agent", 500)
        default_recruitment_per_agent = st.session_state.get("callcentre_recruitment_per_agent", 3000)
        default_training_per_agent = st.session_state.get("callcentre_training_per_agent", 1000)
        default_trainer_salary = st.session_state.get("callcentre_trainer_salary", 25000)

        with c1:
            staff_count = st.number_input("Number of Agents", min_value=0, value=default_staff_count, step=1)
            salary_per_agent = st.number_input("Salary/Agent (ZAR)", min_value=0, value=default_salary_per_agent, step=500)
        with c2:
            medical_aid_per_agent = st.number_input("Medical Aid (ZAR/agent)", min_value=0, value=default_medical_aid_per_agent, step=500)
            pension_percent = st.number_input("Pension %", min_value=0, max_value=100, value=default_pension_percent, step=1)
        with c3:
            bonus_incentive_per_agent = st.number_input("Bonus/Agent (ZAR)", min_value=0, value=default_bonus_per_agent, step=500)
            monthly_benefits_per_agent = st.number_input("Other Benefits/Agent (ZAR)", min_value=0, value=default_benefits_per_agent, step=100)
        with c4:
            recruitment_cost_per_agent = st.number_input("Recruitment/Agent (ZAR)", min_value=0, value=default_recruitment_per_agent, step=500)
            training_cost_per_agent = st.number_input("Training/Agent (ZAR)", min_value=0, value=default_training_per_agent, step=500)
            trainer_salary = st.number_input("Trainer Salary (ZAR/mo)", min_value=0, value=default_trainer_salary, step=500)

        st.markdown("### B. Technology Costs")
        tc1, tc2, tc3 = st.columns(3)

        default_callcenter_software = st.session_state.get("callcentre_callcenter_software", 5000)
        default_licensing_per_user = st.session_state.get("callcentre_licensing_per_user", 500)
        default_crm_sub_per_user = st.session_state.get("callcentre_crm_sub_per_user", 1500)
        default_hardware_cost_station = st.session_state.get("callcentre_hardware_cost_station", 15000)
        default_depreciation_years = st.session_state.get("callcentre_depreciation_years", 3)
        default_repair_per_device = st.session_state.get("callcentre_repair_per_device", 800)
        default_phone_bill_per_agent = st.session_state.get("callcentre_phone_bill_per_agent", 1000)
        default_call_cost_per_minute = st.session_state.get("callcentre_call_cost_per_minute", 0.75)
        default_internet_services = st.session_state.get("callcentre_internet_services", 8000)

        with tc1:
            call_center_software = st.number_input("Call Centre Software (ZAR/mo)", min_value=0, value=default_callcenter_software, step=500)
            licensing_per_user = st.number_input("Licensing/Agent (ZAR/mo)", min_value=0, value=default_licensing_per_user, step=50)
            crm_subscription_per_user = st.number_input("CRM/Agent (ZAR/mo)", min_value=0, value=default_crm_sub_per_user, step=100)
        with tc2:
            hardware_cost_per_station = st.number_input("Hardware/Station (ZAR)", min_value=0, value=default_hardware_cost_station, step=1000)
            depreciation_years = st.number_input("Hardware Depreciation (yrs)", min_value=1, value=default_depreciation_years, step=1)
            repair_maintenance_per_device = st.number_input("Repair/Device (ZAR/yr)", min_value=0, value=default_repair_per_device, step=100)
        with tc3:
            monthly_phone_bill_per_agent = st.number_input("Telco Bill/Agent (ZAR/mo)", min_value=0, value=default_phone_bill_per_agent, step=100)
            call_cost_per_minute = st.number_input("Cost/call minute (ZAR)", min_value=0.0, value=default_call_cost_per_minute, step=0.05)
            internet_services = st.number_input("Internet (ZAR/mo)", min_value=0, value=default_internet_services, step=500)

        st.markdown("### C. Facility Costs")
        fc1, fc2, fc3 = st.columns(3)

        default_office_rent_month = st.session_state.get("callcentre_office_rent_month", 20000)
        default_electricity_cost_month = st.session_state.get("callcentre_electricity_cost_month", 6000)
        default_water_cost_month = st.session_state.get("callcentre_water_cost_month", 2000)
        default_hvac_cost_month = st.session_state.get("callcentre_hvac_cost_month", 3000)
        default_stationery_month = st.session_state.get("callcentre_stationery_month", 1000)
        default_cleaning_services_month = st.session_state.get("callcentre_cleaning_services_month", 3000)
        default_office_repairs_annual = st.session_state.get("callcentre_office_repairs_annual", 8000)

        with fc1:
            office_rent_month = st.number_input("Office Rent (ZAR/mo)", min_value=0, value=default_office_rent_month, step=1000)
            electricity_cost_month = st.number_input("Electricity (ZAR/mo)", min_value=0, value=default_electricity_cost_month, step=500)
            water_cost_month = st.number_input("Water (ZAR/mo)", min_value=0, value=default_water_cost_month, step=500)
        with fc2:
            hvac_cost_month = st.number_input("HVAC (ZAR/mo)", min_value=0, value=default_hvac_cost_month, step=500)
            stationery_month = st.number_input("Stationery (ZAR/mo)", min_value=0, value=default_stationery_month, step=100)
            cleaning_services_month = st.number_input("Cleaning (ZAR/mo)", min_value=0, value=default_cleaning_services_month, step=500)
        with fc3:
            office_repairs_annual = st.number_input("Office Repairs (ZAR/yr)", min_value=0, value=default_office_repairs_annual, step=1000)

        st.markdown("### D. Miscellaneous Costs")
        mc1, mc2 = st.columns(2)

        default_marketing_annual = st.session_state.get("callcentre_marketing_annual", 20000)
        default_retention_campaigns_annual = st.session_state.get("callcentre_retention_campaigns_annual", 15000)
        default_engagement_events_annual = st.session_state.get("callcentre_engagement_events_annual", 10000)
        default_liability_insurance_annual = st.session_state.get("callcentre_liability_insurance_annual", 30000)
        default_equipment_insurance_percent = st.session_state.get("callcentre_equipment_insurance_percent", 5)

        with mc1:
            marketing_annual = st.number_input("Marketing (ZAR/yr)", min_value=0, value=default_marketing_annual, step=2000)
            retention_campaigns_annual = st.number_input("Retention (ZAR/yr)", min_value=0, value=default_retention_campaigns_annual, step=1000)
            engagement_events_annual = st.number_input("Events (ZAR/yr)", min_value=0, value=default_engagement_events_annual, step=1000)
        with mc2:
            liability_insurance_annual = st.number_input("Liability Insurance (ZAR/yr)", min_value=0, value=default_liability_insurance_annual, step=2000)
            equipment_insurance_percent = st.number_input("Equip Insurance %", min_value=0, max_value=100, value=default_equipment_insurance_percent, step=1)

        callcentre_calc_btn = st.form_submit_button("Calculate Call Centre Costs")

    if callcentre_calc_btn:
        # Store these in session for reuse
        st.session_state["callcentre_staff_count"] = staff_count
        st.session_state["callcentre_salary_per_agent"] = salary_per_agent
        st.session_state["callcentre_medical_aid_per_agent"] = medical_aid_per_agent
        st.session_state["callcentre_pension_percent"] = pension_percent
        st.session_state["callcentre_bonus_per_agent"] = bonus_incentive_per_agent
        st.session_state["callcentre_benefits_per_agent"] = monthly_benefits_per_agent
        st.session_state["callcentre_recruitment_per_agent"] = recruitment_cost_per_agent
        st.session_state["callcentre_training_per_agent"] = training_cost_per_agent
        st.session_state["callcentre_trainer_salary"] = trainer_salary

        st.session_state["callcentre_callcenter_software"] = call_center_software
        st.session_state["callcentre_licensing_per_user"] = licensing_per_user
        st.session_state["callcentre_crm_sub_per_user"] = crm_subscription_per_user
        st.session_state["callcentre_hardware_cost_station"] = hardware_cost_per_station
        st.session_state["callcentre_depreciation_years"] = depreciation_years
        st.session_state["callcentre_repair_per_device"] = repair_maintenance_per_device
        st.session_state["callcentre_phone_bill_per_agent"] = monthly_phone_bill_per_agent
        st.session_state["callcentre_call_cost_per_minute"] = call_cost_per_minute
        st.session_state["callcentre_internet_services"] = internet_services

        st.session_state["callcentre_office_rent_month"] = office_rent_month
        st.session_state["callcentre_electricity_cost_month"] = electricity_cost_month
        st.session_state["callcentre_water_cost_month"] = water_cost_month
        st.session_state["callcentre_hvac_cost_month"] = hvac_cost_month
        st.session_state["callcentre_stationery_month"] = stationery_month
        st.session_state["callcentre_cleaning_services_month"] = cleaning_services_month
        st.session_state["callcentre_office_repairs_annual"] = office_repairs_annual

        st.session_state["callcentre_marketing_annual"] = marketing_annual
        st.session_state["callcentre_retention_campaigns_annual"] = retention_campaigns_annual
        st.session_state["callcentre_engagement_events_annual"] = engagement_events_annual
        st.session_state["callcentre_liability_insurance_annual"] = liability_insurance_annual
        st.session_state["callcentre_equipment_insurance_percent"] = equipment_insurance_percent

        # Calculate call centre monthly costs
        monthly_salary_total = staff_count * salary_per_agent
        monthly_pension_total = monthly_salary_total * (pension_percent / 100)
        monthly_medical_total = staff_count * medical_aid_per_agent
        monthly_bonus_total = staff_count * bonus_incentive_per_agent
        monthly_benefits_total = staff_count * monthly_benefits_per_agent
        total_recruitment = staff_count * recruitment_cost_per_agent
        total_training = staff_count * training_cost_per_agent

        monthly_personnel = (
            monthly_salary_total
            + monthly_pension_total
            + monthly_medical_total
            + monthly_bonus_total
            + monthly_benefits_total
            + trainer_salary
        )

        monthly_software = (
            call_center_software
            + (licensing_per_user * staff_count)
            + (crm_subscription_per_user * staff_count)
        )
        monthly_hardware_amort = (hardware_cost_per_station * staff_count) / (depreciation_years * 12)
        monthly_repair_maint = (repair_maintenance_per_device * staff_count) / 12
        monthly_telco = (monthly_phone_bill_per_agent * staff_count) + internet_services

        monthly_technology = monthly_software + monthly_hardware_amort + monthly_repair_maint + monthly_telco

        monthly_facility = (
            office_rent_month
            + electricity_cost_month
            + water_cost_month
            + hvac_cost_month
            + stationery_month
            + cleaning_services_month
            + (office_repairs_annual / 12)
        )

        monthly_marketing = (marketing_annual / 12) + (retention_campaigns_annual / 12)
        monthly_engagement = engagement_events_annual / 12
        monthly_liability_insur = liability_insurance_annual / 12
        total_hardware_value = hardware_cost_per_station * staff_count
        monthly_equip_insur = (total_hardware_value * (equipment_insurance_percent / 100)) / 12

        monthly_misc = monthly_marketing + monthly_engagement + monthly_liability_insur + monthly_equip_insur

        monthly_total_callcentre_zar = monthly_personnel + monthly_technology + monthly_facility + monthly_misc
        once_off_costs_callcentre_zar = total_recruitment + total_training

        st.session_state["cc_monthly_total_callcentre_zar"] = monthly_total_callcentre_zar
        st.session_state["cc_once_off_costs_callcentre_zar"] = once_off_costs_callcentre_zar

        # Convert to selected currency
        selected_currency = st.session_state.get("selected_currency", "ZAR")
        st.session_state["cc_monthly_total_callcentre"] = convert_currency(monthly_total_callcentre_zar, selected_currency, exchange_rates)
        st.session_state["cc_once_off_costs_callcentre"] = convert_currency(once_off_costs_callcentre_zar, selected_currency, exchange_rates)

        st.success("Calculated Call Centre costs successfully! Check Main Dashboard or Quotation next.")

# --------------------------------------------------
# Main Dashboard Menu
# --------------------------------------------------
elif menu == "Main Dashboard":
    st.title("Main Dashboard: Your askAYYI Overview")

    # Make sure we have calculation results from Client Calculator
    final_monthly_rate_excl_vat = st.session_state.get("client_final_monthly_rate_excl_vat_zar", None)
    if final_monthly_rate_excl_vat is None:
        st.warning("Please use 'Client Calculator' to compute your askAYYI costs first.")
        st.stop()

    # Retrieve Key Values from Session
    num_assistants = safe_int(st.session_state.get("client_num_assistants", 0))
    assistant_label = "Assistant" if num_assistants == 1 else "Assistants"

    universal_setup_cost_zar = safe_float(st.session_state.get("client_universal_setup_cost_zar", 0.0))
    setup_cost_for_assistants_zar = safe_float(st.session_state.get("client_setup_cost_per_assistant_zar", 0.0))

    whitelabel_fee_charged = st.session_state.get("client_whitelabel_fee_charged", False)
    whitelabel_fee_waived = st.session_state.get("client_whitelabel_fee_waived", False)
    whitelabel_fee_zar = safe_float(st.session_state.get("client_whitelabel_fee_zar", 0.0))

    payment_option = st.session_state.get("client_payment_option", "Not Specified")
    discount_percentage = safe_int(st.session_state.get("client_discount_percentage", 0))
    monthly_subtotal_excl_vat_zar = safe_float(st.session_state.get("client_monthly_subtotal_excl_vat_zar", 0.0))
    final_monthly_rate_excl_vat_zar = safe_float(st.session_state.get("client_final_monthly_rate_excl_vat_zar", 0.0))
    total_cost_excl_vat_zar = safe_float(st.session_state.get("client_total_cost_excl_vat_zar", 0.0))

    total_included_messages = safe_int(st.session_state.get("client_total_included_messages", 0))
    total_used_messages = safe_int(st.session_state.get("client_total_used_messages", 0))
    additional_messages = safe_int(st.session_state.get("client_extra_messages", 0))

    total_included_minutes = safe_int(st.session_state.get("client_total_included_minutes", 0))
    total_used_minutes = safe_int(st.session_state.get("client_total_used_minutes", 0))
    additional_minutes = safe_int(st.session_state.get("client_extra_minutes", 0))

    total_overage_cost_zar = safe_float(st.session_state.get("client_total_overage_cost_zar", 0.0))
    monthly_support_hours = safe_float(st.session_state.get("client_monthly_support_hours", 0))

    monthly_total_callcentre_zar = safe_float(st.session_state.get("cc_monthly_total_callcentre_zar", None))
    once_off_costs_callcentre_zar = safe_float(st.session_state.get("cc_once_off_costs_callcentre_zar", None))

    # NEW: Custom Voices
    num_custom_voices = safe_int(st.session_state.get("client_num_custom_voices", 0))
    custom_voices_cost_zar = safe_float(st.session_state.get("client_custom_voices_cost_zar", 0.0))

    # Determine selected currency
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    symbol = get_currency_symbol(selected_currency)

    # Convert amounts to selected currency
    assistant_total_cost = convert_currency(st.session_state.get("client_assistant_total_cost_zar", 0.0), selected_currency, exchange_rates)
    base_monthly_cost = convert_currency(st.session_state.get("client_base_monthly_cost_zar", 0.0), selected_currency, exchange_rates)
    universal_setup_cost = convert_currency(universal_setup_cost_zar, selected_currency, exchange_rates)
    setup_cost_for_assistants = convert_currency(setup_cost_for_assistants_zar, selected_currency, exchange_rates)
    whitelabel_fee = convert_currency(whitelabel_fee_zar, selected_currency, exchange_rates)
    monthly_subtotal_excl_vat = convert_currency(monthly_subtotal_excl_vat_zar, selected_currency, exchange_rates)
    final_monthly_rate_excl_vat = convert_currency(final_monthly_rate_excl_vat_zar, selected_currency, exchange_rates)
    total_cost_excl_vat = convert_currency(total_cost_excl_vat_zar, selected_currency, exchange_rates)
    total_overage_cost = convert_currency(total_overage_cost_zar, selected_currency, exchange_rates)
    custom_voices_cost = convert_currency(custom_voices_cost_zar, selected_currency, exchange_rates)

    # Custom CSS for Cards
    st.markdown(
        """
        <style>
        /* Card styling */
        .card {
            background-color: #f9f9f9; 
            border: 1px solid #ddd;
            padding: 1em;
            border-radius: 5px;
            margin-bottom: 1em;
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

    # --------------------------------------------------
    # One-Time Setup Costs
    # --------------------------------------------------
    st.subheader("One-Time Setup Costs (Excl. VAT)")
    setup_html = f"""
    <div style="display:flex; flex-wrap:wrap; gap:2em;">
      <div class="card" style="flex:1; min-width:250px;">
        <h4 data-tooltip="A one-time universal fee to configure askAYYI.">
          Universal Setup Cost
        </h4>
        <p>{symbol}{universal_setup_cost:,.2f}</p>
      </div>
      <div class="card" style="flex:1; min-width:250px;">
        <h4 data-tooltip="Setup cost for {num_assistants} {assistant_label} (quantity × cost per assistant).">
          Setup Cost for {num_assistants} {assistant_label}
        </h4>
        <p>{symbol}{setup_cost_for_assistants:,.2f}</p>
      </div>
    </div>
    """
    st.markdown(setup_html, unsafe_allow_html=True)

    # Whitelabel Fee (if relevant)
    if whitelabel_fee_charged:
        if whitelabel_fee_waived:
            # Convert the standard whitelabel fee for display
            standard_whitelabel_fee_converted = convert_currency(pricing.get("whitelabel_fee", 14550), selected_currency, exchange_rates)
            st.markdown(
                f"""
                <div class="card" style="max-width:400px;">
                  <h4 data-tooltip="Whitelabel fee is displayed but effectively R0.">
                    Whitelabel Fee
                  </h4>
                  <p>{symbol}{standard_whitelabel_fee_converted:,.2f} (Waived, so {symbol}0 charged)</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="card" style="max-width:400px;">
                  <h4 data-tooltip="A one-time branding fee for whitelabeling.">
                    Whitelabel Fee
                  </h4>
                  <p>{symbol}{whitelabel_fee:,.2f}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------
    # Payment Plan & (Possible) Discounts
    # --------------------------------------------------
    discounts_enabled = pricing.get("discounts_enabled", True)

    if discounts_enabled:
        st.subheader("Payment Plan & Discounts")
        payment_html = f"""
        <div style="display:flex; flex-wrap:wrap; gap:2em;">
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Number of AI Assistants in this plan.">Number of Assistants</h4>
            <p>{num_assistants}</p>
          </div>
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Your selected payment arrangement.">Payment Plan</h4>
            <p>{payment_option}</p>
          </div>
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Discount percentage based on your plan.">Discount Percentage</h4>
            <p>{discount_percentage}%</p>
          </div>
        </div>
        """
        st.markdown(payment_html, unsafe_allow_html=True)
    else:
        # If discounts are disabled, just show the plan with no mention of discount
        st.subheader("Payment Plan")
        plan_html = f"""
        <div style="display:flex; flex-wrap:wrap; gap:2em;">
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Number of AI Assistants in this plan.">Number of Assistants</h4>
            <p>{num_assistants}</p>
          </div>
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Your selected payment arrangement.">Payment Plan</h4>
            <p>{payment_option}</p>
          </div>
        </div>
        """
        st.markdown(plan_html, unsafe_allow_html=True)

    # NEW: Additional "Custom Voices" blocks
    if num_custom_voices > 0:
        st.markdown("#### Custom Voices")
        custom_voice_html = f"""
        <div style="display:flex; flex-wrap:wrap; gap:2em;">
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Number of extra voices beyond English.">Custom Voices</h4>
            <p>{num_custom_voices}</p>
          </div>
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Monthly cost for these custom voices.">Custom Voice Monthly Cost</h4>
            <p>{symbol}{custom_voices_cost:,.2f}</p>
          </div>
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="English is included at no extra cost.">English is Standard</h4>
            <p>Yes</p>
          </div>
        </div>
        """
        st.markdown(custom_voice_html, unsafe_allow_html=True)
    else:
        st.info("English is included as standard (no additional custom voices).")

    # --------------------------------------------------
    # Monthly Usage Overview
    # --------------------------------------------------
    st.subheader("Monthly Usage Overview")
    st.write(
        "Here is a snapshot of your included vs. used messages and call minutes, "
        "plus any additional usage."
    )

    usage_cards_html = ""

    # 1) Included Messages
    usage_cards_html += f"""
    <div class="card" style="flex:1; min-width:250px;">
        <h4>Included Messages</h4>
        <p>{total_included_messages:,}</p>
    </div>
    """
    # 2) Included Minutes
    usage_cards_html += f"""
    <div class="card" style="flex:1; min-width:250px;">
        <h4>Included Minutes</h4>
        <p>{total_included_minutes:,}</p>
    </div>
    """
    # 3) Above Plan - Messages
    usage_cards_html += f"""
    <div class="card" style="flex:1; min-width:250px;">
        <h4>Messages Above Plan</h4>
        <p>{additional_messages:,}</p>
    </div>
    """
    # 4) Above Plan - Minutes
    usage_cards_html += f"""
    <div class="card" style="flex:1; min-width:250px;">
        <h4>Minutes Above Plan</h4>
        <p>{additional_minutes:,}</p>
    </div>
    """
    # 5) Extra Usage Cost
    usage_cards_html += f"""
    <div class="card" style="flex:1; min-width:250px;">
        <h4>Extra Usage Cost</h4>
        <p>{symbol}{total_overage_cost:,.2f}</p>
    </div>
    """

    final_usage_html = f"""
    <div style="display:flex; flex-wrap:wrap; gap:2em; margin-top:1em;">
    {usage_cards_html}
    </div>
    """
    st.markdown(final_usage_html, unsafe_allow_html=True)

    if monthly_support_hours > 0:
        st.info(f"Monthly Support Hours Included: {monthly_support_hours:.1f} hour(s)")

    # --------------------------------------------------
    # Monthly Costs
    # --------------------------------------------------
    st.subheader("Monthly Costs (Excl. VAT)")
    if discounts_enabled:
        st.write(
            "Below is your monthly subtotal (before any discount) and the final monthly rate."
        )
    else:
        st.write("Below is your monthly subtotal (no discounts applied).")

    monthly_html = f"""
    <div style="display:flex; flex-wrap:wrap; gap:2em;">
    <div class="card" style="flex:1; min-width:250px;">
        <h4 data-tooltip="Base cost + assistant cost + extras.">
        Monthly Subtotal
        </h4>
        <p>{symbol}{monthly_subtotal_excl_vat:,.2f}</p>
    </div>
    <div class="card" style="flex:1; min-width:250px;">
        <h4 data-tooltip="Actual monthly payment under the selected plan.">
        Final Monthly Cost
        </h4>
        <p>{symbol}{final_monthly_rate_excl_vat:,.2f}</p>
    </div>
    </div> 
    """
    st.markdown(monthly_html, unsafe_allow_html=True)

    # --------------------------------------------------
    # Overall Plan Total
    # --------------------------------------------------
    st.subheader("Plan Total (Excl. VAT)")
    st.write(
        "This total is your monthly cost × plan duration, plus setup fees and any whitelabel fees."
    )
    plan_total_html = f"""
    <div class="card" style="max-width:600px;">
    <h4>Overall Plan Total</h4>
    <span class="highlighted-total">{symbol}{total_cost_excl_vat:,.2f}</span>
    </div>
    """
    st.markdown(plan_total_html, unsafe_allow_html=True)

    # --------------------------------------------------
    # Call Centre Comparison
    # --------------------------------------------------
    if (monthly_total_callcentre_zar is not None) and (once_off_costs_callcentre_zar is not None):
        st.markdown("---")
        st.subheader("Call Centre Comparison")
        st.write(
            "Below are the monthly and one-time costs of your existing call centre."
        )
        monthly_total_callcentre = convert_currency(monthly_total_callcentre_zar, selected_currency, exchange_rates)
        once_off_costs_callcentre = convert_currency(once_off_costs_callcentre_zar, selected_currency, exchange_rates)

        callcentre_html = f"""
        <div style="display:flex; flex-wrap:wrap; gap:2em;">
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Your current call centre's total monthly expense.">
              Call Centre (Monthly)
            </h4>
            <p>{symbol}{monthly_total_callcentre:,.2f}</p>
          </div>
          <div class="card" style="flex:1; min-width:250px;">
            <h4 data-tooltip="Combined recruitment and training for your call centre.">
              Call Centre (One-Time)
            </h4>
            <p>{symbol}{once_off_costs_callcentre:,.2f}</p>
          </div>
        </div>
        """
        st.markdown(callcentre_html, unsafe_allow_html=True)

        monthly_savings = monthly_total_callcentre - final_monthly_rate_excl_vat
        if monthly_savings > 0:
            st.success(
                f"You could save ~ {symbol}{monthly_savings:,.2f} per month "
                "using askAYYI compared to your call centre."
            )
        elif monthly_savings < 0:
            st.warning(
                f"It appears you'd spend ~ {symbol}{abs(monthly_savings):,.2f} more "
                "per month with askAYYI."
            )
        else:
            st.info(
                "Your monthly cost is about the same as your call centre’s current expenses."
            )
    else:
        st.write(
            "No call centre cost data is available. If you want a comparison, "
            "please fill out the 'Call Centre Cost Calculation' section first."
        )

    st.info(
        "All values shown above are **EXCLUDING VAT**.\n\n"
        "Your session data (and these calculations) will persist "
        "while this browser tab remains open."
    )

# ======================================
# PAGE: Detailed Invoice
#  - Provide an itemized breakdown of all calculations
# ======================================
elif menu == "Quotation":
    st.title("Quotation")
    st.write("Below is a very detailed breakdown:")

    final_monthly_rate_excl_vat_zar = st.session_state.get("client_final_monthly_rate_excl_vat_zar", None)
    if final_monthly_rate_excl_vat_zar is None:
        st.warning("Please complete the 'Client Calculator' first to generate the invoice details.")
    else:
        # Gather all relevant session state items
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

        # Check if discounts are enabled
        discounts_enabled = pricing.get("discounts_enabled", True)

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
        # 3) Voice Customization if selected
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
                "Explanation": "Charges for usage that exceeded the included messages/minutes."
            })
        # 6) Subtotal monthly
        invoice_items.append({
            "Description": "Monthly Subtotal",
            "Amount": f"{symbol}{monthly_subtotal_excl_vat:,.2f}",
            "Explanation": "Sum of base, assistants, voice cost, custom voices, and any overages."
        })
        # 7) Discount (only if discounts are enabled and discount > 0)
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
            "Explanation": "This is what you'll pay monthly under the plan."
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
            "Explanation": "A one-time cost to configure the system for your business."
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
                    "Explanation": f"Standard {symbol}{standard_whitelabel_fee_converted:,.2f} shown but waived."
                })
            else:
                invoice_items.append({
                    "Description": "Whitelabel Fee",
                    "Amount": f"{symbol}{whitelabel_fee:,.2f}",
                    "Explanation": "A one-time branding fee if whitelabeling is needed."
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

        # Show usage details
        st.markdown("---")
        st.write("### Usage Details")
        usage_details = [
            {
                "Metric": "Included Messages",
                "Value": f"{total_included_messages:,.0f}"
            },
            {
                "Metric": "Used Messages",
                "Value": f"{total_used_messages:,.0f}"
            },
            {
                "Metric": "Additional (Over) Messages",
                "Value": f"{additional_messages:,.0f}"
            },
            {
                "Metric": "Included Minutes",
                "Value": f"{total_included_minutes:,.0f}"
            },
            {
                "Metric": "Used Minutes",
                "Value": f"{total_used_minutes:,.0f}"
            },
            {
                "Metric": "Additional (Over) Minutes",
                "Value": f"{additional_minutes:,.0f}"
            },
        ]
        df_usage = pd.DataFrame(usage_details)
        st.table(df_usage)

        if monthly_support_hours > 0:
            st.info(f"Monthly Support Hours Included: {monthly_support_hours} hrs")

        st.success("This concludes the full itemized breakdown of your askAYYI invoice!")
