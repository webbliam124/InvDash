import streamlit as st
from streamlit.runtime.scriptrunner import RerunException, RerunData
import json
import os
import pandas as pd
import math
from datetime import datetime
import random
from io import BytesIO
import matplotlib.pyplot as plt

# =============================================================================
# CONFIGURATION PATHS
# =============================================================================
CONFIG_DIR = 'config'
PRICING_FILE = os.path.join(CONFIG_DIR, 'pricing.json')
USAGE_LIMITS_FILE = os.path.join(CONFIG_DIR, 'usage_limits.json')
EXCHANGE_RATES_FILE = os.path.join(CONFIG_DIR, 'exchange_rates.json')
CLIENT_CONFIGS_FILE = os.path.join(CONFIG_DIR, 'client_configurations.json')

# =============================================================================
# DEFAULT DATA
# =============================================================================
DEFAULT_PRICING = {
    "plans": {
        "Basic": {
            "setup_hours": 12,
            "setup_hourly_rate": 850,
            "messages": 5000,
            "voice_minutes": 300,
            "crm_access": True,
            "platforms": "All Platforms",
            "onboarding_support_hours": 3,
            "technical_support_hours": 2,
            "technical_support_hourly_rate": 300,
            "limitations": {
                "use_cases": 1,
                "assistants": 0
            },
            "optional_addons": {
                "white_label_setup": 12600,
                "custom_voices": {
                    "enabled": False,
                    "cost_per_voice": 0
                },
                "additional_languages": {
                    "enabled": False,
                    "cost_per_language": 3400
                }
            },
            "base_fee": 6500,
            "base_msg_cost": 0.05,
            "msg_markup": 2.0,
            "base_min_cost": 0.50,
            "min_markup": 2.0,
            "float_cost": 500,
            "contingency_percent": 2.5,
            "top_up_msg_multiplier": 1.0,
            "top_up_min_multiplier": 1.0
        },
        "Advanced": {
            "setup_hours": 24,
            "setup_hourly_rate": 850,
            "messages": 10000,
            "voice_minutes": 500,
            "crm_integration": True,
            "api_integrations_fee": 9800,
            "platforms": "All Platforms",
            "onboarding_support_hours": 6,
            "technical_support_hours": 4,
            "technical_support_hourly_rate": 350,
            "limitations": {
                "use_cases": 1,
                "assistants": 0
            },
            "optional_addons": {
                "white_label_setup": 14550,
                "custom_voices": {
                    "enabled": False,
                    "cost_per_voice": 0
                },
                "additional_languages": {
                    "enabled": False,
                    "cost_per_language": 3400
                }
            },
            "base_fee": 15000,
            "base_msg_cost": 0.04,
            "msg_markup": 2.0,
            "base_min_cost": 0.45,
            "min_markup": 2.0,
            "float_cost": 1000,
            "contingency_percent": 2.5,
            "top_up_msg_multiplier": 1.0,
            "top_up_min_multiplier": 1.0
        },
        "Enterprise": {
            "setup_hours": 48,
            "setup_hourly_rate": 850,
            "messages": 60000,
            "voice_minutes": 6000,
            "crm_integration": True,
            "api_integrations_fee": 9800,
            "platforms": "All Platforms",
            "onboarding_support_hours": 9,
            "technical_support_hours": 6,
            "technical_support_hourly_rate": 400,
            "setup_cost_per_assistant": 5000,
            "limitations": {
                "use_cases": 1,
                "assistants": 1
            },
            "additional_options": {
                "add_use_case_fee": 25000,
                "extra_messages_per_additional_assistant": 15000,
                "extra_minutes_per_additional_assistant": 1500
            },
            "optional_addons": {
                "white_label_setup": 15850,
                "custom_voices": {
                    "enabled": False,
                    "cost_per_voice": 0
                },
                "additional_languages": {
                    "enabled": False,
                    "cost_per_language": 3400
                }
            },
            "base_fee": 45000,
            "base_msg_cost": 0.03,
            "msg_markup": 2.0,
            "base_min_cost": 0.40,
            "min_markup": 2.0,
            "float_cost": 3000,
            "contingency_percent": 2.5,
            "top_up_msg_multiplier": 1.0,
            "top_up_min_multiplier": 1.0
        }
    },
    "discounts_enabled": True,
    "international_mode": False,
    "whitelabel_waved": False,
    "global_discount_rate": 10,
    "fees_waived": {
        "setup_fee": False,
        "technical_support_fee": False
    }
}

DEFAULT_USAGE_LIMITS = {
    "Basic": {
        "base_messages": 5000,
        "base_minutes": 300,
        "cost_per_additional_message": 0.09,
        "cost_per_additional_minute": 3.33
    },
    "Advanced": {
        "base_messages": 10000,
        "base_minutes": 500,
        "cost_per_additional_message": 0.07,
        "cost_per_additional_minute": 3.00
    },
    "Enterprise": {
        "base_messages": 60000,
        "base_minutes": 6000,
        "cost_per_additional_message": 0.05,
        "cost_per_additional_minute": 2.50
    }
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
MIN_PLAN_DURATION = {"Basic": 3, "Advanced": 3, "Enterprise": 3}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
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
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    # Pricing file
    if not os.path.isfile(PRICING_FILE):
        with open(PRICING_FILE, 'w') as f:
            DEFAULT_PRICING["plans"]["Basic"]["setup_cost_per_assistant"] = 0
            DEFAULT_PRICING["plans"]["Basic"]["assistant_monthly_fee"] = 0
            DEFAULT_PRICING["plans"]["Advanced"]["setup_cost_per_assistant"] = 0
            DEFAULT_PRICING["plans"]["Advanced"]["assistant_monthly_fee"] = 0
            DEFAULT_PRICING["plans"]["Enterprise"]["assistant_monthly_fee"] = 0
            json.dump(DEFAULT_PRICING, f, indent=4)
    else:
        try:
            with open(PRICING_FILE, 'r') as f:
                pricing = json.load(f)
        except json.JSONDecodeError:
            st.error("Pricing config invalid JSON. Re-creating with defaults.")
            DEFAULT_PRICING["plans"]["Basic"]["setup_cost_per_assistant"] = 0
            DEFAULT_PRICING["plans"]["Basic"]["assistant_monthly_fee"] = 0
            DEFAULT_PRICING["plans"]["Advanced"]["setup_cost_per_assistant"] = 0
            DEFAULT_PRICING["plans"]["Advanced"]["assistant_monthly_fee"] = 0
            DEFAULT_PRICING["plans"]["Enterprise"]["assistant_monthly_fee"] = 0
            pricing = DEFAULT_PRICING

        if not isinstance(pricing, dict):
            st.error("Pricing config is malformed. Replacing with defaults.")
            DEFAULT_PRICING["plans"]["Basic"]["setup_cost_per_assistant"] = 0
            DEFAULT_PRICING["plans"]["Basic"]["assistant_monthly_fee"] = 0
            DEFAULT_PRICING["plans"]["Advanced"]["setup_cost_per_assistant"] = 0
            DEFAULT_PRICING["plans"]["Advanced"]["assistant_monthly_fee"] = 0
            DEFAULT_PRICING["plans"]["Enterprise"]["assistant_monthly_fee"] = 0
            pricing = DEFAULT_PRICING

        updated = False
        if "plans" not in pricing:
            pricing["plans"] = {}
            updated = True
        for plan_name, defaults in DEFAULT_PRICING["plans"].items():
            if plan_name not in pricing["plans"]:
                pricing["plans"][plan_name] = defaults
                updated = True
            else:
                for k, v in defaults.items():
                    if k not in pricing["plans"][plan_name]:
                        pricing["plans"][plan_name][k] = v
                        updated = True
                    elif isinstance(v, dict):
                        for subk, subv in v.items():
                            if subk not in pricing["plans"][plan_name][k]:
                                pricing["plans"][plan_name][k][subk] = subv
                                updated = True

        for k in ["discounts_enabled", "international_mode", "whitelabel_waved", "global_discount_rate", "fees_waived"]:
            if k not in pricing:
                pricing[k] = DEFAULT_PRICING[k]
                updated = True

        if "international_markups" not in pricing:
            pricing["international_markups"] = {}

        for p in ["Basic", "Advanced", "Enterprise"]:
            if p in pricing["plans"]:
                if "setup_cost_per_assistant" not in pricing["plans"][p]:
                    pricing["plans"][p]["setup_cost_per_assistant"] = 0
                if "assistant_monthly_fee" not in pricing["plans"][p]:
                    pricing["plans"][p]["assistant_monthly_fee"] = 0

        if updated:
            try:
                with open(PRICING_FILE, 'w') as f:
                    json.dump(pricing, f, indent=4)
            except IOError as e:
                st.error(f"Unable to update pricing config: {e}")

    # Usage Limits
    if not os.path.isfile(USAGE_LIMITS_FILE):
        with open(USAGE_LIMITS_FILE, 'w') as f:
            json.dump(DEFAULT_USAGE_LIMITS, f, indent=4)
    else:
        try:
            with open(USAGE_LIMITS_FILE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            st.error("Usage limits config invalid JSON. Re-creating with defaults.")
            with open(USAGE_LIMITS_FILE, 'w') as f:
                json.dump(DEFAULT_USAGE_LIMITS, f, indent=4)

    # Exchange Rates
    if not os.path.isfile(EXCHANGE_RATES_FILE):
        with open(EXCHANGE_RATES_FILE, 'w') as f:
            json.dump(DEFAULT_EXCHANGE_RATES, f, indent=4)
    else:
        try:
            with open(EXCHANGE_RATES_FILE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            st.error("Exchange rates config invalid JSON. Re-creating with defaults.")
            with open(EXCHANGE_RATES_FILE, 'w') as f:
                json.dump(DEFAULT_EXCHANGE_RATES, f, indent=4)

    # Client Configs
    if not os.path.isfile(CLIENT_CONFIGS_FILE):
        with open(CLIENT_CONFIGS_FILE, 'w') as f:
            json.dump({}, f, indent=4)

def load_config(file_path):
    if not os.path.isfile(file_path):
        st.error(f"Config file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"Invalid JSON in {file_path}.")
        return None
    except Exception as e:
        st.error(f"Error reading {file_path}: {e}")
        return None

def load_client_configs():
    if not os.path.isfile(CLIENT_CONFIGS_FILE):
        return {}
    with open(CLIENT_CONFIGS_FILE, 'r') as f:
        return json.load(f)

def save_client_config(ref_id, config_data):
    all_configs = load_client_configs()
    all_configs[ref_id] = config_data
    try:
        with open(CLIENT_CONFIGS_FILE, 'w') as f:
            json.dump(all_configs, f, indent=4)
    except IOError as e:
        st.error(f"Error saving client config: {e}")

def custom_rerun():
    raise RerunException(RerunData(query_string=""))

def save_config(file_path, data):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        st.error(f"Error saving config to {file_path}: {e}")
    custom_rerun()

def apply_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAFAFA;
            color: #1D1D1F;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stTabBar"] button {
            background-color: #F0F2F6 !important;
            color: #4CAF50 !important;
            border-radius: 0 !important;
            font-size: 16px;
            font-weight: bold;
        }
        div[data-testid="stTabBar"] button[data-selected="true"] {
            border-bottom: 4px solid #4CAF50 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #4CAF50;
            font-family: 'Arial Black', Gadget, sans-serif;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            border-radius: 6px;
            transition: background-color 0.3s ease;
            margin: 2px;
        }
        .stButton > button:hover {
            background-color: #43A047;
        }
        label {
            color: #1D1D1F !important;
            font-weight: bold;
        }
        .dataframe {
            color: #1D1D1F;
            border-collapse: collapse;
            width: 100%;
        }
        .dataframe th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            padding: 8px;
            text-align: left;
        }
        .dataframe td {
            background-color: #F7F7F7;
            padding: 8px;
            border: 1px solid #ddd;
        }
        .card {
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
        }
        .card h4 {
            color: #4CAF50;
            margin-top: 0px; 
            margin-bottom: 10px;
        }
        .stMetric {
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }
        .steve-jobs-style {
            font-size: 1.2rem;
            color: #333;
            margin: 20px 0;
            line-height: 1.6;
        }
        .steve-jobs-style .highlight {
            font-weight: bold;
            color: #4CAF50;
        }
        .footer-text {
            text-align: center;
            font-size: 0.85em;
            margin-top: 50px;
            color: #888;
        }
        .chosen-plan {
            background-color: #e1fbe1 !important;
            border: 2px solid #4CAF50 !important;
        }
        .subtle-text {
            font-size: 0.9em;
            color: #555;
        }
        .pl-table {
            width: 70%;
            margin: 0 auto;
            border-collapse: collapse;
        }
        .pl-table th {
            background-color: #4CAF50;
            color: #fff;
            padding: 8px;
            text-align: left;
        }
        .pl-table td {
            background-color: #F7F7F7;
            padding: 8px;
            border: 1px solid #ddd;
        }
        .pl-table caption {
            caption-side: top;
            font-weight: bold;
            margin-bottom: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def authenticate_admin():
    def check_password():
        def password_entered():
            if st.session_state.get("password", "") == "RCS_18112@":
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

def assign_plan_based_on_inputs(messages_needed, minutes_needed, wants_own_crm, number_of_agents):
    if wants_own_crm:
        if messages_needed > 10000 or minutes_needed > 500:
            return "Enterprise"
        else:
            return "Advanced"
    else:
        if messages_needed > 5000 or minutes_needed > 300:
            if messages_needed > 10000 or minutes_needed > 500:
                return "Enterprise"
            else:
                return "Advanced"
        else:
            return "Basic"

def show_footer():
    currency = st.session_state.get("selected_currency", "ZAR")
    vat_note = "Excluding VAT" if currency == "ZAR" else "Including VAT"
    st.markdown(
        f"""
        <div class="footer-text">
            <p>{vat_note}</p>
            © 2024 Retail Communication Solutions (Pty) Ltd - The RCS Group
        </div>
        """,
        unsafe_allow_html=True
    )

def usage_exceeds_threshold(used_m, used_min, plan_m, plan_min):
    return (used_m >= 0.9 * plan_m) or (used_min >= 0.9 * plan_min)

def round_up_to_even_10(value):
    return math.ceil(value / 20.0) * 20

def calculate_plan_cost(
    plan_name, 
    num_agents,
    usage, 
    addons, 
    exchange_rates, 
    selected_currency, 
    pricing,
    usage_limits,
    communication_type
):
    plan_config = pricing["plans"][plan_name]
    fees_waived = pricing.get("fees_waived", {})
    setup_fee_waived = fees_waived.get("setup_fee", False)
    technical_support_fee_waived = fees_waived.get("technical_support_fee", False)

    base_fee_zar = plan_config.get("base_fee", 0)
    base_msg_cost_zar = plan_config.get("base_msg_cost", 0.05)
    msg_markup = plan_config.get("msg_markup", 2.0)
    base_min_cost_zar = plan_config.get("base_min_cost", 0.40)
    min_markup = plan_config.get("min_markup", 2.0)
    float_cost_zar = plan_config.get("float_cost", 0)
    contingency_percent = plan_config.get("contingency_percent", 2.5) / 100.0
    technical_support_hours = plan_config.get("technical_support_hours", 0)
    tech_rate_zar = plan_config.get("technical_support_hourly_rate", 0)

    final_msg_cost_zar = base_msg_cost_zar * msg_markup
    final_min_cost_zar = base_min_cost_zar * min_markup

    if technical_support_fee_waived:
        technical_support_cost_zar = 0
    else:
        technical_support_cost_zar = technical_support_hours * tech_rate_zar

    total_base_setup_fee_zar = plan_config.get("setup_hours", 0) * plan_config.get("setup_hourly_rate", 850)
    if setup_fee_waived:
        total_base_setup_fee_zar = 0

    setup_cost_per_assistant_zar = plan_config.get("setup_cost_per_assistant", 0)
    assistant_monthly_fee_zar = plan_config.get("assistant_monthly_fee", 0)

    included_msgs = plan_config.get("messages", 0)
    included_mins = plan_config.get("voice_minutes", 0)

    if plan_name == "Enterprise":
        extra_opts = plan_config.get("additional_options", {})
        extra_msgs = extra_opts.get("extra_messages_per_additional_assistant", 0)
        extra_mins = extra_opts.get("extra_minutes_per_additional_assistant", 0)
        included_msgs = included_msgs + extra_msgs * num_agents
        included_mins = included_mins + extra_mins * num_agents

    additional_agents_needed = num_agents
    setup_cost_assistants_zar = additional_agents_needed * setup_cost_per_assistant_zar
    assistant_monthly_cost_zar = additional_agents_needed * assistant_monthly_fee_zar

    if communication_type == "Just Messages":
        cost_of_included_mins_zar = included_mins * final_min_cost_zar
        extra_msgs_from_mins = 0
        if final_msg_cost_zar != 0:
            extra_msgs_from_mins = int(cost_of_included_mins_zar / final_msg_cost_zar)
        included_msgs += extra_msgs_from_mins
        included_mins = 0
    elif communication_type == "Just Minutes":
        cost_of_included_msgs_zar = included_msgs * final_msg_cost_zar
        extra_mins_from_msgs = 0
        if final_min_cost_zar != 0:
            extra_mins_from_msgs = int(cost_of_included_msgs_zar / final_min_cost_zar)
        included_mins += extra_mins_from_msgs
        included_msgs = 0

    cost_of_msgs_zar = included_msgs * final_msg_cost_zar
    cost_of_mins_zar = included_mins * final_min_cost_zar

    monthly_cost_zar = (
        base_fee_zar
        + cost_of_msgs_zar
        + cost_of_mins_zar
        + float_cost_zar
        + technical_support_cost_zar
        + assistant_monthly_cost_zar
    )

    base_included_messages = usage_limits[plan_name]["base_messages"]
    base_included_minutes = usage_limits[plan_name]["base_minutes"]
    top_up_msg_multiplier = plan_config.get("top_up_msg_multiplier", 1.0)
    top_up_min_multiplier = plan_config.get("top_up_min_multiplier", 1.0)
    cost_per_extra_message = usage_limits[plan_name]["cost_per_additional_message"] * top_up_msg_multiplier
    cost_per_extra_minute = usage_limits[plan_name]["cost_per_additional_minute"] * top_up_min_multiplier

    extra_messages_used = max(0, usage["used_messages"] - base_included_messages)
    extra_minutes_used = max(0, usage["used_minutes"] - base_included_minutes)
    extra_msg_cost_zar = extra_messages_used * cost_per_extra_message
    extra_min_cost_zar = extra_minutes_used * cost_per_extra_minute
    monthly_cost_zar += (extra_msg_cost_zar + extra_min_cost_zar)

    monthly_cost_zar *= (1 + contingency_percent)

    total_setup_cost_zar = total_base_setup_fee_zar + setup_cost_assistants_zar

    if pricing.get("international_mode", False):
        int_markup_dict = pricing.get("international_markups", {})
        int_markup = int_markup_dict.get(selected_currency, 30)
        factor = 1 + int_markup / 100.0
        monthly_cost_zar *= factor
        extra_msg_cost_zar *= factor
        extra_min_cost_zar *= factor
        total_base_setup_fee_zar *= factor
        technical_support_cost_zar *= factor
        setup_cost_assistants_zar *= factor
        assistant_monthly_cost_zar *= factor
        total_setup_cost_zar = total_base_setup_fee_zar + setup_cost_assistants_zar

    exchange_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        final_factor = 1.3 * 1.15

    monthly_cost_converted = (monthly_cost_zar / exchange_rate) * final_factor
    setup_cost_converted = (total_setup_cost_zar / exchange_rate) * final_factor

    whitelabel_fee_zar = plan_config["optional_addons"].get("white_label_setup", 0) if addons.get("white_labeling") else 0
    if pricing.get("whitelabel_waved", False) and whitelabel_fee_zar > 0:
        whitelabel_fee_zar = 0

    custom_voices_cost_zar = 0
    if addons.get("custom_voices", {}).get("enabled"):
        q = addons["custom_voices"]["quantity"]
        cost_per_v = addons["custom_voices"]["cost_per_voice"]
        custom_voices_cost_zar = q * cost_per_v

    additional_languages_cost_zar = 0
    if addons.get("additional_languages", {}).get("enabled"):
        q = addons["additional_languages"]["quantity"]
        cost_per_lang = addons["additional_languages"]["cost_per_language"]
        additional_languages_cost_zar = q * cost_per_lang

    if pricing.get("international_mode", False):
        whitelabel_fee_zar *= factor
        custom_voices_cost_zar *= factor
        additional_languages_cost_zar *= factor

    total_monthly_addons_zar = custom_voices_cost_zar + additional_languages_cost_zar
    final_monthly_cost_zar = monthly_cost_zar + total_monthly_addons_zar
    final_monthly_cost_converted = (final_monthly_cost_zar / exchange_rate) * final_factor

    total_setup_cost_zar += whitelabel_fee_zar
    overall_total_cost_zar = (final_monthly_cost_zar * 12) + total_setup_cost_zar
    overall_total_cost_converted = (overall_total_cost_zar / exchange_rate) * final_factor

    return {
        "final_monthly_cost_zar": monthly_cost_zar,
        "total_monthly_cost_zar": final_monthly_cost_zar,
        "total_setup_cost_zar": total_setup_cost_zar,
        "overall_total_cost_zar": overall_total_cost_zar,
        "total_monthly_cost": final_monthly_cost_converted,
        "total_setup_cost": setup_cost_converted,
        "overall_total_cost": overall_total_cost_converted,
        "included_msgs_after_conversion": included_msgs,
        "included_mins_after_conversion": included_mins,
        "extra_messages_used": extra_messages_used,
        "extra_minutes_used": extra_minutes_used,
        "extra_msg_cost_zar": extra_msg_cost_zar,
        "extra_min_cost_zar": extra_min_cost_zar,
        "whitelabel_fee_zar": whitelabel_fee_zar,
        "custom_voices_cost_zar": custom_voices_cost_zar,
        "additional_languages_cost_zar": additional_languages_cost_zar,
        "setup_fee_zar": total_base_setup_fee_zar,
        "setup_cost_assistants_zar": setup_cost_assistants_zar,
        "assistant_monthly_cost_zar": assistant_monthly_cost_zar,
        "technical_support_hours": technical_support_hours,
        "technical_support_hourly_rate": tech_rate_zar,
        "technical_support_cost_zar": technical_support_cost_zar,
        "base_fee_zar": base_fee_zar,
        "final_msg_cost_zar": final_msg_cost_zar,
        "final_min_cost_zar": final_min_cost_zar,
        "cost_of_included_messages_zar": cost_of_msgs_zar,
        "cost_of_included_minutes_zar": cost_of_mins_zar,
        "absorbed_msgs_for_assistants": 0,
        "absorbed_mins_for_assistants": 0
    }

# =============================================================================
# RUN INITIAL CONFIG LOAD
# =============================================================================
initialize_configs()
pricing = load_config(PRICING_FILE) or DEFAULT_PRICING
usage_limits = load_config(USAGE_LIMITS_FILE) or DEFAULT_USAGE_LIMITS
exchange_rates = load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES

st.set_page_config(page_title="askAYYI Cost Calculator", layout="wide")
apply_custom_css()

# =============================================================================
# CREATE APP TABS
# =============================================================================
tabs = st.tabs([
    "Plan Assignment",
    "Main Dashboard",
    "Quotation",
    "Saved Configurations",
    "Admin Dashboard",
    "Your Current Costs",
    "Cost & Sales Breakdown",
])

# =============================================================================
# TAB 0: Plan Assignment
# =============================================================================
with tabs[0]:
    st.title("Plan Assignment")
    st.write("""
        Determine which plan (Basic, Advanced, or Enterprise) 
        might best fit your needs. 
        Hover over the “?” icons to see more details and examples.
    """)

    selected_currency = st.session_state.get("selected_currency", "ZAR")

    # ---------------------------------------------------
    # ESTIMATE YOUR MONTHLY USAGE
    # ---------------------------------------------------
    with st.expander("Estimate Your Monthly Usage", expanded=True):
        st.write("Enter your monthly expected usage of messages and calls. Hover over the '?' for extra guidance.")

        if "estimated_messages" not in st.session_state:
            st.session_state["estimated_messages"] = 3000
        if "estimated_minutes" not in st.session_state:
            st.session_state["estimated_minutes"] = 200

        st.markdown("#### Messages")
        colA, _ = st.columns([3, 1])
        with colA:
            msg_conversations_per_month = st.number_input(
                "Monthly Messaging Conversations",
                min_value=0,
                value=3000,
                step=500,
                help="""
**What does this mean?**  
How many conversation threads you expect each month.  

**Detailed Example:**  
- If you usually have three thousand chat sessions (customer questions, leads, etc.) each month, 
  type in "3000".  
- A "conversation thread" is basically one chat session started by your user or customer.  

**Tips:**  
- If you're unsure, you can estimate to the nearest thousand. 
- Remember this can vary by season, but we're looking for a good monthly average.
                """
            )

        colA, _ = st.columns([3, 1])
        with colA:
            avg_msgs_per_convo = st.number_input(
                "Average Messages per Conversation",
                min_value=1,
                value=5,
                step=1,
                help="""
**What does this mean?**  
Roughly how many messages get exchanged in one conversation?

**Detailed Example:**  
- If a typical chat has five or six messages total (from "Hello" to "Thank you"), 
  you can type in "5".  
- That means if a user sends three messages and your agent replies twice, 
  that counts as five total messages.

**Tips:**  
- You can include both user and agent messages. 
- Keep it simple; just use an average you usually see in your business.
                """
            )

        st.markdown("#### Minutes")
        colA, _ = st.columns([3, 1])
        with colA:
            calls_per_month = st.number_input(
                "Number of Calls per Month",
                min_value=0,
                value=500,
                step=100,
                help="""
**What does this mean?**  
How many voice calls you expect in total every month.

**Detailed Example:**  
- If you handle five hundred phone calls (inbound or outbound) each month, 
  type in "500".  
- Each call can be with a customer, lead, or any other caller.

**Tips:**  
- If you have both inbound (from the customer to you) 
  and outbound (from you to the customer), 
  add them together for a total.
                """
            )

        colA, _ = st.columns([3, 1])
        with colA:
            avg_call_duration = st.number_input(
                "Average Call Duration (minutes)",
                min_value=0.0,
                value=3.0,
                step=0.5,
                help="""
**What does this mean?**  
How many minutes, on average, does each call last?

**Detailed Example:**  
- If your typical calls last about three minutes, type "3.0".  
- If you notice calls usually go from two to four minutes, 
  averaging at three, that's fine to put here.

**Tips:**  
- Include talk time only. 
- Rounding up or down by half a minute is okay.
                """
            )

        total_minutes_needed = calls_per_month * avg_call_duration
        total_messages_needed = msg_conversations_per_month * avg_msgs_per_convo
        st.session_state["estimated_minutes"] = total_minutes_needed
        st.session_state["estimated_messages"] = total_messages_needed

    # ---------------------------------------------------
    # CONFIGURE AGENTS
    # ---------------------------------------------------
    with st.expander("Configure Assistants", expanded=False):
        st.write("How many extra AI assistants do you want, besides the main one included in some plans?")

        colA, _ = st.columns([3, 1])
        with colA:
            desired_agents = st.number_input(
                "Number of Additional Assistants",
                min_value=0,
                value=0,
                step=1,
                help="""
**What does this mean?**  
If you need more than the default number of AI-driven assistants, 
enter how many additional ones.

**Detailed Example:**  
- If the plan includes one assistant by default, 
  and you want two more, type "2" here.

**Tips:**  
- Some plans (Basic or Advanced) may not allow multiple additional assistants. 
- Enterprise often suits large teams or multiple specialized bots.
                """
            )
        st.session_state["client_desired_agents"] = desired_agents

    # ---------------------------------------------------
    # CRM PREFERENCE
    # ---------------------------------------------------
    with st.expander("CRM Preference", expanded=False):
        st.write("Choose whether you want to use the built-in askAYYI CRM or your own existing CRM system.")
        colA, _ = st.columns([3, 1])
        with colA:
            crm_choice = st.radio(
                "CRM Preference",
                ["askAYYI CRM", "Your Own CRM"],
                help="""
**askAYYI CRM**  
- Our ready-to-use CRM solution with minimal setup required.

**Your Own CRM**  
- If you have your own (like Salesforce or HubSpot), 
  integration usually requires an advanced plan or higher.

**Example:**  
- If you have no CRM right now, "askAYYI CRM" might be simpler.  
- If you already use a robust CRM, choose "Your Own CRM."
                """
            )
        st.session_state["client_crm_choice"] = crm_choice

    # ---------------------------------------------------
    # COMMUNICATION TYPE
    # ---------------------------------------------------
    with st.expander("Communication Type", expanded=False):
        st.write("Do you plan to use both messaging and voice calls, or focus on only one type of interaction?")
        colA, _ = st.columns([3, 1])
        with colA:
            communication_type = st.radio(
                "Communication Type",
                ["Both Messages & Voice", "Just Messages", "Just Minutes"],
                index=0,
                help="""
**What does this mean?**  
- "Both Messages & Voice": If your business handles text chats and phone calls.  
- "Just Messages": If you only need texting/chat functionalities.  
- "Just Minutes": If you only want to handle voice calls, 
  with no chat.

**Example:**  
- If your support is mostly chat-based, pick "Just Messages."  
- If your main focus is voice calls, pick "Just Minutes."
                """
            )
        st.session_state["client_communication_type"] = communication_type

    # ---------------------------------------------------
    # OPTIONAL ADD-ONS
    # ---------------------------------------------------
    with st.expander("Optional Add-Ons", expanded=False):
        st.write("Customize your plan with White Labeling, Custom Voices, or Additional Languages.")
        if "temp_addons_whitelabel" not in st.session_state:
            st.session_state["temp_addons_whitelabel"] = False
        if "temp_addons_cv_enabled" not in st.session_state:
            st.session_state["temp_addons_cv_enabled"] = False
        if "temp_addons_cv_qty" not in st.session_state:
            st.session_state["temp_addons_cv_qty"] = 0
        if "temp_addons_lang_enabled" not in st.session_state:
            st.session_state["temp_addons_lang_enabled"] = False
        if "temp_addons_lang_qty" not in st.session_state:
            st.session_state["temp_addons_lang_qty"] = 0

        wl_col, _ = st.columns([3,1])
        with wl_col:
            white_labeling = st.checkbox(
                "White Labeling?", 
                value=st.session_state["temp_addons_whitelabel"],
                help="""
**What is White Labeling?**  
Remove the askAYYI branding and replace it with your own company logos and text.

**Example:**  
- If you want full brand control, check this. 
- If you don't mind seeing "askAYYI" as part of the interface, leave it unchecked.
                """
            )

        cv_col, _ = st.columns([3,1])
        with cv_col:
            custom_voices = st.checkbox(
                "Custom Voices?", 
                value=st.session_state["temp_addons_cv_enabled"],
                help="""
**What are Custom Voices?**  
Create specialized voices tailored to your brand or department.

**Example:**  
- If you want your chatbot to speak like a specific character or brand persona, check this. 
- If standard voice options are enough, you can leave it unchecked.
                """
            )
        num_custom_voices = 0
        if custom_voices:
            cv2_col, _ = st.columns([3,1])
            with cv2_col:
                num_custom_voices = st.number_input(
                    "Quantity of Custom Voices",
                    min_value=0,
                    value=st.session_state["temp_addons_cv_qty"],
                    step=1,
                    help="""
**How many unique voices do you need?**  
- Enter the exact number of different custom voices you plan to have.

**Example:**  
- If you want two distinct voices (one for sales, one for support), type "2".
                    """
                )

        al_col, _ = st.columns([3,1])
        with al_col:
            additional_languages = st.checkbox(
                "Additional Languages?",
                value=st.session_state["temp_addons_lang_enabled"],
                help="""
**What are Additional Languages?**  
Offer support and interactions in more languages than the default plan includes.

**Example:**  
- If you already have English but also need Spanish and French, 
  check this box to add those languages.
                """
            )
        num_additional_languages = 0
        if additional_languages:
            al2_col, _ = st.columns([3,1])
            with al2_col:
                num_additional_languages = st.number_input(
                    "Quantity of Additional Languages",
                    min_value=0,
                    value=st.session_state["temp_addons_lang_qty"],
                    step=1,
                    help="""
**How many extra languages do you want?**  
- Enter the total number of new languages you need, beyond what's included.

**Example:**  
- If you're adding Spanish and French, that is two languages.
                    """
                )

        st.session_state["temp_addons_whitelabel"] = white_labeling
        st.session_state["temp_addons_cv_enabled"] = custom_voices
        st.session_state["temp_addons_cv_qty"] = num_custom_voices
        st.session_state["temp_addons_lang_enabled"] = additional_languages
        st.session_state["temp_addons_lang_qty"] = num_additional_languages

    # ---------------------------------------------------
    # PAYMENT PREFERENCE & PLAN ASSIGNMENT
    # ---------------------------------------------------
    with st.expander("Payment & Plan Assignment", expanded=False):
        st.write("Select a payment schedule and see which plan we recommend.")
        discount_enabled = pricing.get("discounts_enabled", True)
        global_discount_rate = pricing.get("global_discount_rate", 10)
        plan_options_label = ["3 Months (Monthly)", "12 Months Upfront"]

        pay_col, _ = st.columns([3,1])
        with pay_col:
            payment_option = st.radio(
                "Select Payment Period",
                plan_options_label,
                help="""
**What does this mean?**  
- "3 Months (Monthly)": A shorter-term commitment; you pay monthly with a three-month minimum.  
- "12 Months Upfront": Pay for a full year in one go, usually at a discounted rate.

**Example:**  
- If you prefer flexibility, choose "3 Months (Monthly)".  
- If you want to save costs overall and don't mind paying upfront, choose "12 Months Upfront."
                """
            )
        st.session_state["client_payment_option"] = payment_option

        wants_own_crm = (st.session_state["client_crm_choice"] == "Your Own CRM")
        assigned_plan = assign_plan_based_on_inputs(
            messages_needed=st.session_state["estimated_messages"],
            minutes_needed=st.session_state["estimated_minutes"],
            wants_own_crm=wants_own_crm,
            number_of_agents=st.session_state["client_desired_agents"]
        )
        st.session_state["client_assigned_plan"] = assigned_plan

        if assigned_plan in ["Basic", "Advanced"] and st.session_state["client_desired_agents"] > 0:
            st.warning(
                f"'{assigned_plan}' does not officially support multiple additional assistants. "
                "Consider upgrading to Enterprise."
            )
        if assigned_plan == "Basic" and wants_own_crm:
            st.warning("Basic plan cannot accommodate Your Own CRM. (Needs an upgrade.)")

        if not pricing.get("international_mode", False):
            st.session_state["selected_currency"] = "ZAR"
        else:
            currency_options = SUPPORTED_CURRENCIES.copy()
            if "selected_currency" not in st.session_state:
                st.session_state["selected_currency"] = "USD"
            sc_col, _ = st.columns([3,1])
            with sc_col:
                selected_currency_box = st.selectbox(
                    "Choose Currency (for reference)",
                    options=currency_options,
                    index=currency_options.index(st.session_state["selected_currency"])
                       if st.session_state["selected_currency"] in currency_options else 0,
                    help="""
**What does this mean?**  
Pick the currency you want your amounts to be shown in.  

**Example:**  
- If you operate in the United States, choose "USD". 
- If you work in Europe, choose "EUR".
                    """
                )
            st.session_state["selected_currency"] = selected_currency_box

        plan_data = pricing["plans"].get(assigned_plan, {})
        usage = {
            "used_messages": st.session_state["estimated_messages"],
            "used_minutes": st.session_state["estimated_minutes"]
        }
        addons = {
            "white_labeling": st.session_state["temp_addons_whitelabel"],
            "custom_voices": {
                "enabled": st.session_state["temp_addons_cv_enabled"],
                "quantity": st.session_state["temp_addons_cv_qty"],
                "cost_per_voice": plan_data.get("optional_addons", {})
                                     .get("custom_voices", {})
                                     .get("cost_per_voice", 0)
            },
            "additional_languages": {
                "enabled": st.session_state["temp_addons_lang_enabled"],
                "quantity": st.session_state["temp_addons_lang_qty"],
                "cost_per_language": plan_data.get("optional_addons", {})
                                           .get("additional_languages", {})
                                           .get("cost_per_language", 0)
            }
        }
        cost_details = calculate_plan_cost(
            plan_name=assigned_plan,
            num_agents=st.session_state["client_desired_agents"],
            usage=usage,
            addons=addons,
            exchange_rates=exchange_rates,
            selected_currency=st.session_state["selected_currency"],
            pricing=pricing,
            usage_limits=usage_limits,
            communication_type=st.session_state["client_communication_type"]
        )
        st.session_state["client_cost_details"] = cost_details

        symbol = CURRENCY_SYMBOLS.get(st.session_state["selected_currency"], "R")
        monthly_cost = cost_details["total_monthly_cost"]
        setup_cost = cost_details["total_setup_cost"]

        if payment_option == "12 Months Upfront" and discount_enabled:
            discount_factor = 1 - (global_discount_rate / 100.0)
        else:
            discount_factor = 1.0

        monthly_cost_rounded = round_up_to_even_10(monthly_cost * discount_factor)
        setup_cost_rounded = round_up_to_even_10(setup_cost)

        if payment_option == "12 Months Upfront":
            commit_cost_val = (monthly_cost * 12 + setup_cost) * discount_factor
            commit_label = "twelve months"
        else:
            commit_cost_val = monthly_cost * 3 + setup_cost
            commit_label = "three months"

        commit_cost_rounded = round_up_to_even_10(commit_cost_val)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='card'><h4>Plan</h4><p>{assigned_plan}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<div class='card'><h4>Monthly Cost</h4><p>{symbol}{monthly_cost_rounded:,}</p></div>", 
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f"<div class='card'><h4>Commitment Cost</h4><p>{symbol}{commit_cost_rounded:,} Over {commit_label}</p></div>",
                unsafe_allow_html=True
            )

        if payment_option == "12 Months Upfront" and discount_enabled:
            original_upfront = round_up_to_even_10(monthly_cost * 12 + setup_cost)
            discount_saved = original_upfront - commit_cost_rounded
            if original_upfront > 0:
                discount_pct = (discount_saved / original_upfront) * 100
            else:
                discount_pct = 0
            st.markdown(
                f"<p style='font-weight:bold;'>You are saving {symbol}{discount_saved:,} "
                f"({discount_pct:.2f}% off) due to the discount.</p>",
                unsafe_allow_html=True
            )

        st.write("---")
        st.markdown("### Cost Breakdown")
        ex_rate = exchange_rates.get(st.session_state["selected_currency"], 1.0)
        if st.session_state["selected_currency"] == "ZAR":
            final_factor = 1.0
        else:
            final_factor = 1.3 * 1.15

        def conv_zar_to_rounded_display(zar_amount):
            unrounded = (zar_amount / ex_rate) * final_factor
            return round_up_to_even_10(unrounded)

        final_monthly_without_cont = cost_details["final_monthly_cost_zar"] / (1 + plan_data.get('contingency_percent', 2.5)/100)
        assistant_monthly_cost = cost_details["assistant_monthly_cost_zar"]
        one_time_main_setup = cost_details["setup_fee_zar"]
        one_time_assistants_setup = cost_details["setup_cost_assistants_zar"]
        addons_total = (
            cost_details["whitelabel_fee_zar"] +
            cost_details["custom_voices_cost_zar"] +
            cost_details["additional_languages_cost_zar"]
        )
        overage_total = cost_details["extra_msg_cost_zar"] + cost_details["extra_min_cost_zar"]

        line_items = [{
            "Item": "Monthly Plan Cost", 
            "Explanation": "Includes base plan, messages, and minutes", 
            "Value": f"{symbol}{conv_zar_to_rounded_display(cost_details['final_monthly_cost_zar']):,}"
        }]

        if assistant_monthly_cost > 0:
            line_items.append({
                "Item": "Monthly Additional Assistants",
                "Explanation": f"Cost for {st.session_state['client_desired_agents']} extra assistants each month.",
                "Value": f"{symbol}{conv_zar_to_rounded_display(assistant_monthly_cost):,}"
            })
        if one_time_main_setup > 0:
            line_items.append({
                "Item": "One-Time Setup (Main Assistant)",
                "Explanation": "Setup fee for the primary assistant.",
                "Value": f"{symbol}{conv_zar_to_rounded_display(one_time_main_setup):,}"
            })
        if one_time_assistants_setup > 0:
            line_items.append({
                "Item": "One-Time Setup (Additional Assistants)",
                "Explanation": f"Setup cost for {st.session_state['client_desired_agents']} extra assistants.",
                "Value": f"{symbol}{conv_zar_to_rounded_display(one_time_assistants_setup):,}"
            })
        if addons_total > 0:
            line_items.append({
                "Item": "Add-Ons",
                "Explanation": "White Labeling, Custom Voices, Additional Languages",
                "Value": f"{symbol}{conv_zar_to_rounded_display(addons_total):,}"
            })
        if overage_total > 0:
            line_items.append({
                "Item": "Overage",
                "Explanation": "Charged if usage exceeds included plan amounts.",
                "Value": f"{symbol}{conv_zar_to_rounded_display(overage_total):,}"
            })

        df_line_items = pd.DataFrame(line_items)
        st.table(df_line_items[["Item", "Explanation", "Value"]])

        st.markdown(f"""
            <div class="card chosen-plan">
                <h4>{assigned_plan}</h4>
                <p>You've been assigned <strong>{assigned_plan}</strong> based on your inputs.</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("**Compare All Plans:**")
        plan_names = list(pricing["plans"].keys())
        colA, colB, colC = st.columns(3)
        for i, pn in enumerate(plan_names):
            if i > 2:
                break
            col = [colA, colB, colC][i]
            plan_class = "card chosen-plan" if pn == assigned_plan else "card"
            p_data = pricing["plans"][pn]
            with col:
                st.markdown(f"<div class='{plan_class}'><h4>{pn} Plan</h4>", unsafe_allow_html=True)
                st.markdown(
                    f"<strong>Included Messages:</strong> {p_data.get('messages', 0):,}<br/>"
                    f"<strong>Included Minutes:</strong> {p_data.get('voice_minutes', 0):,}",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

        if "client_reference_id" not in st.session_state:
            reference_id = "REF" + str(random.randint(100000, 999999))
            st.session_state["client_reference_id"] = reference_id
            config_data = {
                "assigned_plan": assigned_plan,
                "estimated_messages": st.session_state["estimated_messages"],
                "estimated_minutes": st.session_state["estimated_minutes"],
                "desired_agents": st.session_state["client_desired_agents"],
                "crm_choice": st.session_state["client_crm_choice"],
                "communication_type": st.session_state["client_communication_type"]
            }
            save_client_config(reference_id, config_data)

        st.info(f"Your Quote reference: **{st.session_state['client_reference_id']}**")
        show_footer()

# =============================================================================
# TAB 1: Main Dashboard
# =============================================================================
with tabs[1]:
    st.title("Main Dashboard")
    st.write("A quick overview of your current selections and usage details.")
    st.write("---")

    assigned_plan = st.session_state.get("client_assigned_plan", "Not Assigned")
    usage_msgs = st.session_state.get("estimated_messages", 0)
    usage_mins = st.session_state.get("estimated_minutes", 0)
    currency_used = st.session_state.get("selected_currency", "ZAR")
    reference_id = st.session_state.get("client_reference_id", "N/A")

    st.markdown(f"**Reference ID**: {reference_id}")
    st.markdown(f"**Assigned Plan**: {assigned_plan}")
    st.markdown(f"**Estimated Monthly Messages**: {usage_msgs:,}")
    st.markdown(f"**Estimated Monthly Minutes**: {usage_mins:,}")
    st.markdown(f"**Currency**: {currency_used}")

    show_footer()

# =============================================================================
# TAB 2: Quotation
# =============================================================================
with tabs[2]:
    st.title("Quotation")

    cost_details = st.session_state.get("client_cost_details", None)
    if cost_details is None:
        st.warning("Use 'Plan Assignment' first for a quote.")
        show_footer()
        st.stop()

    assigned_plan = st.session_state.get("client_assigned_plan", "Basic")
    payment_option = st.session_state.get("client_payment_option", "3 Months (Monthly)")
    if payment_option == "12 Months Upfront":
        plan_min_duration = 12
    else:
        plan_min_duration = MIN_PLAN_DURATION.get(assigned_plan, 3)

    comm_type = st.session_state.get("client_communication_type", "Both Messages & Voice")
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    symbol = CURRENCY_SYMBOLS.get(selected_currency, "R")

    monthly_cost_conv = cost_details["total_monthly_cost"]
    setup_cost_conv = cost_details["total_setup_cost"]
    plan_duration_total_conv = (monthly_cost_conv * plan_min_duration) + setup_cost_conv
    included_msgs = cost_details["included_msgs_after_conversion"]
    included_mins = cost_details["included_mins_after_conversion"]

    discount_enabled = pricing.get("discounts_enabled", True)
    global_discount_rate = pricing.get("global_discount_rate", 10)
    if payment_option == "12 Months Upfront" and discount_enabled:
        discount_factor = 1 - (global_discount_rate / 100.0)
    else:
        discount_factor = 1.0

    def round_up_to_even_10_local(val):
        return math.ceil(val / 20.0) * 20

    monthly_cost_rounded = round_up_to_even_10_local(monthly_cost_conv * discount_factor)
    setup_cost_rounded = round_up_to_even_10_local(setup_cost_conv)
    total_plan_duration_rounded = round_up_to_even_10_local(plan_duration_total_conv * discount_factor)

    extra_messages_used = cost_details["extra_messages_used"]
    extra_minutes_used = cost_details["extra_minutes_used"]
    extra_msg_cost_zar = cost_details["extra_msg_cost_zar"]
    extra_min_cost_zar = cost_details["extra_min_cost_zar"]

    ex_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        final_factor = 1.3 * 1.15

    extra_msg_cost_conv = (extra_msg_cost_zar / ex_rate) * final_factor
    extra_min_cost_conv = (extra_min_cost_zar / ex_rate) * final_factor
    disp_extra_msg_cost = round_up_to_even_10_local(extra_msg_cost_conv)
    disp_extra_min_cost = round_up_to_even_10_local(extra_min_cost_conv)

    num_agents = st.session_state.get("client_desired_agents", 0)

    st.markdown(f"""
    <div class="steve-jobs-style">
        <p>Hello <span class="highlight">Client</span>,</p>
        <p>We appreciate your interest in askAYYI. Below is your quotation.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h4>Monthly Cost</h4>
        <p style="font-size:1.2em;">
            {symbol}{monthly_cost_rounded:,}
            <br/><span style="font-size:0.85em;">(Messages, minutes, and tech support hours)</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h4>One-Time Setup</h4>
        <p style="font-size:1.2em;">
            {symbol}{setup_cost_rounded:,}
            <br/><span style="font-size:0.85em;">(Covers necessary setup)</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Additional Assistants info
    plan_config = pricing["plans"].get(assigned_plan, {})
    if num_agents > 0 and assigned_plan == "Enterprise":
        additional_opts = plan_config.get("additional_options", {})
        extra_per_agent_msg = additional_opts.get("extra_messages_per_additional_assistant", 0) * num_agents
        extra_per_agent_min = additional_opts.get("extra_minutes_per_additional_assistant", 0) * num_agents
        st.markdown(f"""
        <div class="card">
            <h4>Additional Assistant(s)</h4>
            <p style="font-size:1.2em;">
                {num_agents} total<br/>
                +{extra_per_agent_msg} messages & +{extra_per_agent_min} minutes<br/>
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Overage
    if extra_messages_used > 0 or extra_minutes_used > 0:
        st.markdown(f"""
        <div class="card">
            <h4>Possible Overage Charges</h4>
            <p style="font-size:1.1em;">
        """, unsafe_allow_html=True)
        if extra_messages_used > 0:
            st.markdown(f"- Extra Messages: {extra_messages_used:,} => {symbol}{disp_extra_msg_cost:,}<br/>", unsafe_allow_html=True)
        if extra_minutes_used > 0:
            st.markdown(f"- Extra Minutes: {extra_minutes_used:,} => {symbol}{disp_extra_min_cost:,}", unsafe_allow_html=True)
        st.markdown("</p></div>", unsafe_allow_html=True)

    st.write("---")
    st.markdown(f"""
    <div class="card">
        <h4>Total Commitment</h4>
        <p style="font-size:1.2em;">
            {symbol}{total_plan_duration_rounded:,} <br/>
            Over {plan_min_duration} months + Setup
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="steve-jobs-style">
        <p>You have ~<span class="highlight">{included_msgs:,}</span> messages 
           and <span class="highlight">{included_mins:,}</span> minutes included each month.</p>
    </div>
    """, unsafe_allow_html=True)

    st.success("Quotation is ready! Thank you for choosing askAYYI.")
    show_footer()

# =============================================================================
# TAB 3: Saved Configurations
# =============================================================================
with tabs[3]:
    st.title("Saved Client Configurations by Reference")
    st.write("Load previously saved configs here.")

    all_client_configs = load_client_configs()
    if not all_client_configs:
        st.info("No configurations saved yet.")
        show_footer()
        st.stop()

    references = list(all_client_configs.keys())
    selected_ref = st.selectbox("Choose a reference to load", options=references)

    if st.button("Load Configuration"):
        config_data = all_client_configs[selected_ref]
        st.session_state["client_assigned_plan"] = config_data.get("assigned_plan", "Basic")
        st.session_state["estimated_messages"] = config_data.get("estimated_messages", 0)
        st.session_state["estimated_minutes"] = config_data.get("estimated_minutes", 0)
        st.session_state["client_desired_agents"] = config_data.get("desired_agents", 0)
        st.session_state["client_crm_choice"] = config_data.get("crm_choice", "askAYYI CRM")
        st.session_state["client_communication_type"] = config_data.get("communication_type", "Both Messages & Voice")
        if "cost_details" in config_data:
            st.session_state["client_cost_details"] = config_data["cost_details"]
            st.session_state["client_selected_plan"] = config_data.get("assigned_plan")
        st.success(f"Configuration for reference {selected_ref} loaded. Go to Main Dashboard / Quotation to view details.")

    st.write("---")
    st.subheader("Save Current Session with a New Reference")
    with st.form("save_current_config"):
        new_ref_to_save = st.text_input("Enter any custom reference (e.g. 'REF123456')")
        save_btn = st.form_submit_button("Save Current Config")
    if save_btn and new_ref_to_save:
        config_data = {
            "assigned_plan": st.session_state.get("client_assigned_plan", ""),
            "estimated_messages": st.session_state.get("estimated_messages", 0),
            "estimated_minutes": st.session_state.get("estimated_minutes", 0),
            "desired_agents": st.session_state.get("client_desired_agents", 0),
            "crm_choice": st.session_state.get("client_crm_choice", "askAYYI CRM"),
            "communication_type": st.session_state.get("client_communication_type", "Both Messages & Voice"),
            "cost_details": st.session_state.get("client_cost_details", {})
        }
        save_client_config(new_ref_to_save, config_data)
        st.success(f"Configuration saved under reference {new_ref_to_save}!")

    show_footer()

# =============================================================================
# TAB 4: Admin Dashboard
# =============================================================================
with tabs[4]:
    if not authenticate_admin():
        st.stop()

    st.title("Admin Dashboard (Internal)")
    st.write("Advanced configuration & profit details. **Internal Only.**")
    st.markdown("---")

    with st.expander("Global Settings", expanded=True):
        col_int1, col_int2 = st.columns([1,1])
        with col_int1:
            st.write("**International Mode**")
            if pricing.get("international_mode", False):
                st.success("International Mode: **ON**")
                if st.button("Disable International Mode"):
                    pricing["international_mode"] = False
                    save_config(PRICING_FILE, pricing)
            else:
                st.warning("International Mode: OFF")
                if st.button("Enable International Mode"):
                    pricing["international_mode"] = True
                    save_config(PRICING_FILE, pricing)

        with col_int2:
            st.write("**Whitelabel Fee Waiver**")
            if pricing.get("whitelabel_waved", False):
                st.success("Whitelabel is currently WAIVED.")
                if st.button("Stop Waiving Whitelabel"):
                    pricing["whitelabel_waved"] = False
                    save_config(PRICING_FILE, pricing)
            else:
                st.warning("Whitelabel is NOT waived.")
                if st.button("Waive Whitelabel Fee"):
                    pricing["whitelabel_waved"] = True
                    save_config(PRICING_FILE, pricing)

    with st.expander("Fee Waivers (Individual)", expanded=False):
        fees_waived = pricing.get("fees_waived", {})
        cfee1, cfee2 = st.columns(2)
        with cfee1:
            setup_fee_waived_chk = st.checkbox("Waive Setup Fee?", value=fees_waived.get("setup_fee", False))
        with cfee2:
            tech_support_fee_waived_chk = st.checkbox("Waive Technical Support Fee?", value=fees_waived.get("technical_support_fee", False))

        if st.button("Save Individual Fee Waivers"):
            fees_waived["setup_fee"] = setup_fee_waived_chk
            fees_waived["technical_support_fee"] = tech_support_fee_waived_chk
            pricing["fees_waived"] = fees_waived
            save_config(PRICING_FILE, pricing)

    with st.expander("Discounts Configuration", expanded=False):
        cdisc1, cdisc2 = st.columns([2,2])
        with cdisc1:
            if pricing.get("discounts_enabled", True):
                st.success("Discounts: ENABLED")
                if st.button("Disable Discounts"):
                    pricing["discounts_enabled"] = False
                    save_config(PRICING_FILE, pricing)
            else:
                st.warning("Discounts: DISABLED")
                if st.button("Enable Discounts"):
                    pricing["discounts_enabled"] = True
                    save_config(PRICING_FILE, pricing)

        with cdisc2:
            current_global_discount = pricing.get("global_discount_rate", 0)
            new_global_discount = st.number_input("Global discount for upfront (%)",
                                                  value=float(current_global_discount),
                                                  min_value=0.0, max_value=100.0, step=1.0)
            if st.button("Update Global Discount"):
                pricing["global_discount_rate"] = new_global_discount
                save_config(PRICING_FILE, pricing)
                st.success(f"Global discount is now {new_global_discount}%")

    with st.expander("Exchange Rates", expanded=False):
        with st.form("exchange_rates_form"):
            exchange_rate_inputs = {}
            for currency_ in SUPPORTED_CURRENCIES:
                current_rate = float(exchange_rates.get(currency_, DEFAULT_EXCHANGE_RATES.get(currency_, 1.0))) if currency_ != "ZAR" else 1.0
                exchange_rate_inputs[currency_] = st.number_input(f"1 {currency_} = X ZAR", value=current_rate, step=0.001)
            save_exchange_rates_btn = st.form_submit_button("Save Exchange Rates")
            if save_exchange_rates_btn:
                for ccy, rate in exchange_rate_inputs.items():
                    exchange_rates[ccy] = rate
                save_config(EXCHANGE_RATES_FILE, exchange_rates)
                st.success("Exchange rates updated.")

    with st.expander("International Markups", expanded=False):
        with st.form("intl_markup_form"):
            st.write("Percentage markup for each currency when International Mode is ON.")
            new_markups = {}
            for currency_ in SUPPORTED_CURRENCIES:
                if currency_ == "ZAR":
                    continue
                current_markup = pricing.get("international_markups", {}).get(currency_, 30)
                new_markups[currency_] = st.number_input(
                    f"Markup for {currency_} (%)",
                    value=float(current_markup), min_value=0.0, max_value=1000.0, step=1.0
                )
            save_intl_markups_btn = st.form_submit_button("Save International Markups")
            if save_intl_markups_btn:
                if "international_markups" not in pricing:
                    pricing["international_markups"] = {}
                for ccy, val in new_markups.items():
                    pricing["international_markups"][ccy] = val
                save_config(PRICING_FILE, pricing)
                st.success("International markups updated successfully.")

    with st.expander("Plans Configuration", expanded=False):
        st.header("Plan Configurations")
        plan_options = list(pricing["plans"].keys())
        selected_plan = st.selectbox("Select Plan to Edit", options=plan_options)
        plan_details = pricing["plans"][selected_plan]

        st.markdown(f"### {selected_plan} - Basic Parameters")
        colp1, colp2, colp3 = st.columns(3)
        with colp1:
            new_base_fee = st.number_input("Base Fee (ZAR)", value=plan_details.get("base_fee", 0), step=1000)
        with colp2:
            new_incl_msgs = st.number_input("Included Messages", value=plan_details.get("messages", 0), step=1000)
            new_incl_mins = st.number_input("Included Minutes", value=plan_details.get("voice_minutes", 0), step=100)
        with colp3:
            new_tech_support_hours = st.number_input("Tech Support (Monthly Hrs)", value=plan_details.get("technical_support_hours", 0), step=1)
            new_tech_support_rate = st.number_input("Tech Support Rate (ZAR/hr)", value=plan_details.get("technical_support_hourly_rate", 0), step=50)

        st.markdown("### Usage Cost Multipliers")
        colp4, colp5, colp6 = st.columns(3)
        with colp4:
            new_base_msg_cost = st.number_input("Base Msg Cost (ZAR)", value=float(plan_details.get("base_msg_cost", 0.05)), step=0.01)
            new_msg_markup = st.number_input("Msg Markup (x)", value=float(plan_details.get("msg_markup", 2.0)), step=0.1)
        with colp5:
            new_base_min_cost = st.number_input("Base Min Cost (ZAR)", value=float(plan_details.get("base_min_cost", 0.40)), step=0.01)
            new_min_markup = st.number_input("Min Markup (x)", value=float(plan_details.get("min_markup", 2.0)), step=0.1)
        with colp6:
            new_contingency = st.number_input("Contingency (%)", value=float(plan_details.get("contingency_percent", 2.5)), step=0.1)
            new_float_cost = st.number_input("Float Cost (ZAR)", value=plan_details.get("float_cost", 0), step=500)

        st.markdown("### Setup Calculation")
        colp7, colp8 = st.columns(2)
        with colp7:
            new_setup_hours = st.number_input("Setup Hours", value=plan_details.get("setup_hours", 0), step=1)
            new_setup_hourly_rate = st.number_input("Setup Hourly Rate (ZAR/hr)", value=plan_details.get("setup_hourly_rate", 850), step=50)
        with colp8:
            new_crm_access = st.checkbox("CRM Access?", value=plan_details.get("crm_access", False))

        st.markdown("### Limitations & Platform")
        colp9, colp10 = st.columns(2)
        with colp9:
            new_use_cases = plan_details.get("limitations", {}).get("use_cases", 1)
            new_use_cases = st.number_input("Base # AI Agents", value=new_use_cases, step=1)
        with colp10:
            new_platforms = st.text_input("Supported Platforms", value=plan_details.get("platforms", "All Platforms"))
        new_onboarding_hrs = st.number_input("Onboarding Hrs", value=plan_details.get("onboarding_support_hours", 0), step=1)

        st.markdown("### Optional Add-Ons")
        colp11, colp12 = st.columns(2)
        with colp11:
            white_label_setup_cost = plan_details["optional_addons"].get("white_label_setup", 0)
            new_white_label_setup = st.number_input("Whitelabel Setup Fee (Once Off) (ZAR)", value=white_label_setup_cost, step=500)
        with colp12:
            cvoices_enabled = plan_details["optional_addons"].get("custom_voices", {}).get("enabled", False)
            new_cvoices_enabled = st.checkbox("Enable Custom Voices?", value=cvoices_enabled)
            cvoices_rate = plan_details["optional_addons"].get("custom_voices", {}).get("cost_per_voice", 0)
            new_cvoices_rate = 0
            if new_cvoices_enabled:
                new_cvoices_rate = st.number_input("Cost/Custom Voice (ZAR)", value=cvoices_rate, step=500)

        al_enabled = plan_details["optional_addons"].get("additional_languages", {}).get("enabled", False)
        new_al_enabled = st.checkbox("Enable Additional Languages?", value=al_enabled)
        al_cost = plan_details["optional_addons"].get("additional_languages", {}).get("cost_per_language", 0)
        new_al_cost = 0
        if new_al_enabled:
            new_al_cost = st.number_input("Cost/Language (ZAR)", value=al_cost, step=500)

        # Enterprise extras
        if selected_plan == "Enterprise":
            eopts = plan_details.get("additional_options", {})
            cex1, cex2 = st.columns(2)
            with cex1:
                new_extra_msgs = st.number_input("Extra Msg/Additional Assistant", value=eopts.get("extra_messages_per_additional_assistant", 0), step=100)
            with cex2:
                new_extra_mins = st.number_input("Extra Min/Additional Assistant", value=eopts.get("extra_minutes_per_additional_assistant", 0), step=50)
            new_setup_cost_per_assistant = st.number_input("Setup Cost/Assistant (ZAR)", value=plan_details.get("setup_cost_per_assistant", 0), step=500)
            new_assistant_monthly_fee = st.number_input("Monthly Fee/Assistant (ZAR)", value=plan_details.get("assistant_monthly_fee", 0), step=500)
        else:
            new_extra_msgs = 0
            new_extra_mins = 0
            new_setup_cost_per_assistant = st.number_input("Setup Cost/Assistant (ZAR)",
                                                           value=plan_details.get("setup_cost_per_assistant", 0),
                                                           step=500)
            new_assistant_monthly_fee = st.number_input("Monthly Fee/Assistant (ZAR)",
                                                        value=plan_details.get("assistant_monthly_fee", 0), step=500)

        st.markdown("### Top Up Multipliers")
        colp13, colp14 = st.columns(2)
        with colp13:
            new_top_up_msg_multiplier = st.number_input("Top Up Msg Multiplier", value=float(plan_details.get("top_up_msg_multiplier", 1.0)), step=0.1)
        with colp14:
            new_top_up_min_multiplier = st.number_input("Top Up Min Multiplier", value=float(plan_details.get("top_up_min_multiplier", 1.0)), step=0.1)

        if st.button("Save Plan Configuration"):
            p = pricing["plans"][selected_plan]
            p["base_fee"] = new_base_fee
            p["messages"] = new_incl_msgs
            p["voice_minutes"] = new_incl_mins
            p["technical_support_hours"] = new_tech_support_hours
            p["technical_support_hourly_rate"] = new_tech_support_rate
            p["base_msg_cost"] = new_base_msg_cost
            p["msg_markup"] = new_msg_markup
            p["base_min_cost"] = new_base_min_cost
            p["min_markup"] = new_min_markup
            p["contingency_percent"] = new_contingency
            p["float_cost"] = new_float_cost
            p["setup_hours"] = new_setup_hours
            p["setup_hourly_rate"] = new_setup_hourly_rate
            p["crm_access"] = new_crm_access
            p["platforms"] = new_platforms
            p["onboarding_support_hours"] = new_onboarding_hrs
            if "limitations" not in p:
                p["limitations"] = {}
            p["limitations"]["use_cases"] = new_use_cases
            p["limitations"]["assistants"] = new_use_cases
            p["optional_addons"]["white_label_setup"] = new_white_label_setup
            p["optional_addons"]["custom_voices"]["enabled"] = new_cvoices_enabled
            p["optional_addons"]["custom_voices"]["cost_per_voice"] = new_cvoices_rate
            p["optional_addons"]["additional_languages"]["enabled"] = new_al_enabled
            p["optional_addons"]["additional_languages"]["cost_per_language"] = new_al_cost

            if selected_plan == "Enterprise":
                if "additional_options" not in p:
                    p["additional_options"] = {}
                p["additional_options"]["extra_messages_per_additional_assistant"] = new_extra_msgs
                p["additional_options"]["extra_minutes_per_additional_assistant"] = new_extra_mins
                p["setup_cost_per_assistant"] = new_setup_cost_per_assistant
                p["assistant_monthly_fee"] = new_assistant_monthly_fee
            else:
                p["setup_cost_per_assistant"] = new_setup_cost_per_assistant
                p["assistant_monthly_fee"] = new_assistant_monthly_fee

            p["top_up_msg_multiplier"] = new_top_up_msg_multiplier
            p["top_up_min_multiplier"] = new_top_up_min_multiplier

            save_config(PRICING_FILE, pricing)
            st.success(f"Settings for {selected_plan} saved successfully!")

    with st.expander("Custom Payment Plans", expanded=False):
        st.write("Define custom payment plans (e.g., 6-month) with special discounts.")
        if "custom_payment_plans" not in pricing:
            pricing["custom_payment_plans"] = {}

        existing_plans = pricing["custom_payment_plans"]
        if existing_plans:
            st.write("**Existing Custom Plans:**")
            for plan_name, plan_info in existing_plans.items():
                st.markdown(f"- **{plan_name}**: {plan_info}")

        st.write("---")
        st.write("**Add / Update a Custom Plan**")
        custom_name = st.text_input("Plan Name", value="")
        custom_months = st.number_input("Number of Months", min_value=1, value=6)
        custom_discount = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
        if st.button("Save Custom Plan"):
            pricing["custom_payment_plans"][custom_name] = {
                "months": custom_months,
                "discount": custom_discount
            }
            save_config(PRICING_FILE, pricing)
            st.success(f"Custom plan '{custom_name}' saved/updated!")

    st.markdown("---")
    st.subheader("Profit & Cost Dashboard (Internal Only)")
    st.write("Margin breakdown based on the most recent usage scenario.")

    cost_details = st.session_state.get("client_cost_details", None)
    if cost_details is None:
        st.warning("No recent client cost details found. Please run 'Plan Assignment' first.")
        show_footer()
        st.stop()

    discount_percentage = 0
    if pricing.get("discounts_enabled", True):
        discount_percentage = pricing.get("global_discount_rate", 0)

    final_monthly_cost_with_discount_zar = cost_details["final_monthly_cost_zar"]
    discount_saved_zar = 0
    if discount_percentage > 0:
        original_revenue_zar = final_monthly_cost_with_discount_zar
        final_monthly_cost_with_discount_zar *= (1 - discount_percentage / 100)
        discount_saved_zar = original_revenue_zar - final_monthly_cost_with_discount_zar

    revenue_zar = final_monthly_cost_with_discount_zar
    plan_name = st.session_state.get("client_selected_plan", None) or st.session_state.get("client_assigned_plan", "Basic")

    try:
        plan_conf = pricing["plans"][plan_name]
    except KeyError:
        st.error(f"Plan '{plan_name}' not found.")
        show_footer()
        st.stop()

    included_msgs = cost_details["included_msgs_after_conversion"]
    included_mins = cost_details["included_mins_after_conversion"]
    base_msg_cost_zar = plan_conf.get("base_msg_cost", 0.05)
    base_min_cost_zar = plan_conf.get("base_min_cost", 0.40)
    float_cost_zar = plan_conf.get("float_cost", 0)
    tech_hours = plan_conf.get("technical_support_hours", 0)
    tech_rate = plan_conf.get("technical_support_hourly_rate", 0)

    # Estimate internal cost
    our_estimated_direct_cost_zar = (
        (base_msg_cost_zar * included_msgs) +
        (base_min_cost_zar * included_mins) +
        float_cost_zar +
        (tech_hours * tech_rate)
    )
    profit_zar = revenue_zar - our_estimated_direct_cost_zar if revenue_zar else 0
    profit_margin_pct = (profit_zar / revenue_zar * 100) if revenue_zar > 0 else 0

    if cost_details["final_monthly_cost_zar"] > 0:
        discount_ratio = (discount_saved_zar / cost_details["final_monthly_cost_zar"]) * 100
    else:
        discount_ratio = 0

    st.markdown(f"""
    <table class="pl-table">
        <caption>Profit & Loss (Internal View)</caption>
        <tr><th>Metric</th><th>Value (ZAR)</th></tr>
        <tr><td>Revenue (After Discount)</td><td>{revenue_zar:,.2f}</td></tr>
        <tr><td>Estimated Direct Cost</td><td>{our_estimated_direct_cost_zar:,.2f}</td></tr>
        <tr><td>Profit</td><td>{profit_zar:,.2f}</td></tr>
        <tr><td>Profit Margin (%)</td><td>{profit_margin_pct:,.2f}%</td></tr>
        <tr><td>Discount Saved</td><td>{discount_saved_zar:,.2f}</td></tr>
        <tr><td>Discount Percentage</td><td>{discount_ratio:,.2f}%</td></tr>
    </table>
    """, unsafe_allow_html=True)

    with st.expander("Detailed Cost Breakdown (Internal)", expanded=True):
        st.markdown("Below is the full cost breakdown to the cent.")
        def red_zar(val):
            return f"<span style='color:red'>R{val:,.2f}</span>"

        # Setup costs
        st.markdown("**Setup Costs (One-Time)**")
        setup_items = []
        setup_items.append(f"- **Setup Fee**: {red_zar(cost_details['setup_fee_zar'])}")
        if cost_details["setup_cost_assistants_zar"] > 0:
            setup_items.append(f"- **Setup for Additional Assistants**: {red_zar(cost_details['setup_cost_assistants_zar'])}")
        if cost_details["whitelabel_fee_zar"] > 0:
            setup_items.append(f"- **Whitelabel Setup**: {red_zar(cost_details['whitelabel_fee_zar'])}")
        setup_items.append(f"- **Total Setup Cost**: {red_zar(cost_details['total_setup_cost_zar'])}")
        for item in setup_items:
            st.markdown(item, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Monthly Costs**")
        monthly_items = []
        monthly_items.append(f"- **Base Fee**: {red_zar(cost_details['base_fee_zar'])}")
        monthly_items.append(
            f"- **Included Messages** ({cost_details['included_msgs_after_conversion']:,} msgs): "
            f"{red_zar(cost_details['cost_of_included_messages_zar'])} (@ R{cost_details['final_msg_cost_zar']:.2f}/msg)"
        )
        monthly_items.append(
            f"- **Included Minutes** ({cost_details['included_mins_after_conversion']:,} mins): "
            f"{red_zar(cost_details['cost_of_included_minutes_zar'])} (@ R{cost_details['final_min_cost_zar']:.2f}/min)"
        )
        if cost_details["extra_msg_cost_zar"] > 0:
            monthly_items.append(f"- **Top Up - Extra Messages**: {red_zar(cost_details['extra_msg_cost_zar'])}")
        if cost_details["extra_min_cost_zar"] > 0:
            monthly_items.append(f"- **Top Up - Extra Minutes**: {red_zar(cost_details['extra_min_cost_zar'])}")
        if cost_details["technical_support_cost_zar"] > 0:
            monthly_items.append(
                f"- **Technical Support**: {red_zar(cost_details['technical_support_cost_zar'])} "
                f"({cost_details['technical_support_hours']} hrs @ R{cost_details['technical_support_hourly_rate']:,}/hr)"
            )
        if plan_conf.get("float_cost", 0) > 0:
            monthly_items.append(f"- **Float Cost**: {red_zar(plan_conf['float_cost'])}")
        if cost_details["custom_voices_cost_zar"] > 0:
            monthly_items.append(f"- **Custom Voices**: {red_zar(cost_details['custom_voices_cost_zar'])}")
        if cost_details["additional_languages_cost_zar"] > 0:
            monthly_items.append(f"- **Additional Languages**: {red_zar(cost_details['additional_languages_cost_zar'])}")
        if cost_details["assistant_monthly_cost_zar"] > 0:
            monthly_items.append(f"- **Monthly Additional Assistants**: {red_zar(cost_details['assistant_monthly_cost_zar'])}")

        contingency_base = cost_details["final_monthly_cost_zar"] / (1 + plan_conf.get('contingency_percent', 2.5)/100)
        monthly_items.append(f"- **Subtotal (Before Contingency)**: {red_zar(contingency_base)}")
        monthly_items.append(f"- **Contingency** ({plan_conf.get('contingency_percent', 2.5)}%): included")
        monthly_items.append(f"- **Final Monthly Cost**: {red_zar(cost_details['final_monthly_cost_zar'])}")
        monthly_items.append(f"- **Monthly + Add-Ons**: {red_zar(cost_details['total_monthly_cost_zar'])}")

        for mitem in monthly_items:
            st.markdown(mitem, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            f"**Total Setup + 1 Month**: {red_zar(cost_details['total_setup_cost_zar'] + cost_details['total_monthly_cost_zar'])}",
            unsafe_allow_html=True
        )

    show_footer()

###############################################################################
# TAB 5: Your Current Costs (exactly as you provided)
###############################################################################
with tabs[5]:
    # ---------------------------
    # Title: "Your Current Costs"
    # ---------------------------
    st.title("Your Current Costs")

    # Grab the current setting from your pricing config:
    international_mode = pricing.get("international_mode", False)

    # -------------------------------------------------------------------------
    # (A) Decide which currencies to show (if any), and set st.session_state
    # -------------------------------------------------------------------------
    if international_mode:
        # If international mode is ON, hide references to ZAR entirely; remove "ZAR" from currency list
        currency_choices = [c for c in SUPPORTED_CURRENCIES if c != "ZAR"]

        if "selected_currency" not in st.session_state or st.session_state["selected_currency"] == "ZAR":
            st.session_state["selected_currency"] = currency_choices[0] if currency_choices else "USD"

        selected_currency = st.selectbox(
            "Select Currency",
            options=currency_choices,
            index=currency_choices.index(st.session_state["selected_currency"])
            if st.session_state["selected_currency"] in currency_choices else 0,
        )
        st.session_state["selected_currency"] = selected_currency

    else:
        # If international mode is OFF, everything is forced to ZAR
        st.session_state["selected_currency"] = "ZAR"

    selected_currency = st.session_state["selected_currency"]

    # Symbol lookup
    symbol = CURRENCY_SYMBOLS.get(selected_currency, "")

    # -------------------------------------------------------------------------
    # (B) Expanders for capturing Current Costs
    # -------------------------------------------------------------------------
    with st.expander("A. Staffing, Salaries, & Messages", expanded=True):
        default_staff_count = st.session_state.get("callcentre_staff_count", 10)
        default_salary_per_agent = st.session_state.get("callcentre_salary_per_agent", 8000)
        default_medical_aid_per_agent = st.session_state.get("callcentre_medical_aid_per_agent", 2000)
        default_pension_percent = st.session_state.get("callcentre_pension_percent", 7)
        default_bonus_per_agent = st.session_state.get("callcentre_bonus_per_agent", 1500)
        default_benefits_per_agent = st.session_state.get("callcentre_benefits_per_agent", 500)
        default_recruitment_per_agent = st.session_state.get("callcentre_recruitment_per_agent", 3000)
        default_training_per_agent = st.session_state.get("callcentre_training_per_agent", 1000)
        default_trainer_salary = st.session_state.get("callcentre_trainer_salary", 25000)
        default_msgs_per_agent_day = st.session_state.get("callcentre_msgs_per_agent_day", 150)
        default_work_days_month = st.session_state.get("callcentre_work_days_month", 22)

        def cost_suffix():
            # If int'l mode is off -> show "ZAR", else show the symbol
            return f"({symbol})" if international_mode else "(ZAR)"

        colA1, colA2, colA3 = st.columns(3)
        with colA1:
            staff_count = st.number_input(
                "Number of Agents",
                min_value=0,
                value=default_staff_count,
                step=1,
                help="How many agents or support staff do you employ currently?"
            )
            salary_per_agent = st.number_input(
                f"Monthly Salary/Agent {cost_suffix()}",
                min_value=0,
                value=default_salary_per_agent,
                step=500,
                help="Base monthly salary per agent."
            )
            pension_percent = st.number_input(
                "Pension Contribution (%)",
                min_value=0,
                max_value=100,
                value=default_pension_percent,
                step=1,
                help="What % of each salary goes to pension/retirement?"
            )

        with colA2:
            medical_aid_per_agent = st.number_input(
                f"Medical Aid/Agent {cost_suffix()}",
                min_value=0,
                value=default_medical_aid_per_agent,
                step=500,
                help="Monthly healthcare or medical aid per agent."
            )
            bonus_incentive_per_agent = st.number_input(
                f"Annual Bonus/Agent {cost_suffix()}",
                min_value=0,
                value=default_bonus_per_agent,
                step=500,
                help="Yearly bonus per agent (we'll average it monthly)."
            )
            monthly_benefits_per_agent = st.number_input(
                f"Other Benefits/Agent {cost_suffix()}",
                min_value=0,
                value=default_benefits_per_agent,
                step=100,
                help="Any additional monthly benefits or perks per agent."
            )

        with colA3:
            recruitment_cost_per_agent = st.number_input(
                f"Recruitment/Agent (Once-Off) {cost_suffix()}",
                min_value=0,
                value=default_recruitment_per_agent,
                step=500,
                help="One-time cost for hiring each new agent."
            )
            training_cost_per_agent = st.number_input(
                f"Training/Agent (Once-Off) {cost_suffix()}",
                min_value=0,
                value=default_training_per_agent,
                step=500,
                help="One-time training cost per agent."
            )
            trainer_salary = st.number_input(
                f"Trainer Salary {cost_suffix()}",
                min_value=0,
                value=default_trainer_salary,
                step=500,
                help="Monthly salary for a trainer or supervisor."
            )

        st.markdown("---")
        st.markdown("**Messages Handled Per Agent**")
        colMsg1, colMsg2 = st.columns(2)
        with colMsg1:
            msgs_per_agent_day = st.number_input(
                "Messages/Agent/Day",
                min_value=0,
                value=default_msgs_per_agent_day,
                step=10,
                help="How many messages can one agent typically handle in a day?"
            )
        with colMsg2:
            work_days_month = st.number_input(
                "Working Days/Month",
                min_value=1,
                value=default_work_days_month,
                step=1,
                help="How many days per month do agents work on average?"
            )

    with st.expander("B. Technology & Telephony", expanded=False):
        default_callcenter_software = st.session_state.get("callcentre_callcenter_software", 5000)
        default_licensing_per_user = st.session_state.get("callcentre_licensing_per_user", 500)
        default_crm_sub_per_user = st.session_state.get("callcentre_crm_sub_per_user", 1500)
        default_hardware_cost_station = st.session_state.get("callcentre_hardware_cost_station", 15000)
        default_depreciation_years = st.session_state.get("callcentre_depreciation_years", 3)
        default_repair_per_device = st.session_state.get("callcentre_repair_per_device", 800)
        default_phone_bill_per_agent = st.session_state.get("callcentre_phone_bill_per_agent", 1000)
        default_call_cost_per_minute = st.session_state.get("callcentre_call_cost_per_minute", 0.75)
        default_internet_services = st.session_state.get("callcentre_internet_services", 8000)

        cT1, cT2, cT3 = st.columns(3)
        with cT1:
            call_center_software = st.number_input(
                f"Call Centre Software {cost_suffix()}/m",
                min_value=0,
                value=default_callcenter_software,
                step=500
            )
            licensing_per_user = st.number_input(
                f"Licensing/Agent {cost_suffix()}/m",
                min_value=0,
                value=default_licensing_per_user,
                step=50
            )
            crm_subscription_per_user = st.number_input(
                f"CRM/Agent {cost_suffix()}/m",
                min_value=0,
                value=default_crm_sub_per_user,
                step=100
            )
        with cT2:
            hardware_cost_per_station = st.number_input(
                f"Hardware Cost/Station {cost_suffix()}",
                min_value=0,
                value=default_hardware_cost_station,
                step=1000
            )
            depreciation_years = st.number_input(
                "HW Depreciation (yrs)",
                min_value=1,
                value=default_depreciation_years,
                step=1
            )
            repair_maintenance_per_device = st.number_input(
                f"Repair/Device {cost_suffix()}/yr",
                min_value=0,
                value=default_repair_per_device,
                step=100
            )
        with cT3:
            monthly_phone_bill_per_agent = st.number_input(
                f"Telco/Agent {cost_suffix()}/m",
                min_value=0,
                value=default_phone_bill_per_agent,
                step=100
            )
            call_cost_per_minute = st.number_input(
                f"Cost/Call Minute {cost_suffix()}",
                min_value=0.0,
                value=default_call_cost_per_minute,
                step=0.05
            )
            internet_services = st.number_input(
                f"Internet {cost_suffix()}/m",
                min_value=0,
                value=default_internet_services,
                step=500
            )

    with st.expander("C. Facility & Overhead", expanded=False):
        default_office_rent_month = st.session_state.get("callcentre_office_rent_month", 7500)
        default_electricity_cost_month = st.session_state.get("callcentre_electricity_cost_month", 6000)
        default_water_cost_month = st.session_state.get("callcentre_water_cost_month", 2000)
        default_hvac_cost_month = st.session_state.get("callcentre_hvac_cost_month", 3000)
        default_stationery_month = st.session_state.get("callcentre_stationery_month", 1000)
        default_cleaning_services_month = st.session_state.get("callcentre_cleaning_services_month", 3000)
        default_office_repairs_annual = st.session_state.get("callcentre_office_repairs_annual", 8000)

        cF1, cF2, cF3 = st.columns(3)
        with cF1:
            office_rent_month = st.number_input(
                f"Office Rent {cost_suffix()}/m",
                min_value=0,
                value=default_office_rent_month,
                step=1000
            )
            electricity_cost_month = st.number_input(
                f"Electricity {cost_suffix()}/m",
                min_value=0,
                value=default_electricity_cost_month,
                step=500
            )
            water_cost_month = st.number_input(
                f"Water {cost_suffix()}/m",
                min_value=0,
                value=default_water_cost_month,
                step=500
            )
        cF4, cF5, cF6 = st.columns(3)
        with cF4:
            hvac_cost_month = st.number_input(
                f"HVAC {cost_suffix()}/m",
                min_value=0,
                value=default_hvac_cost_month,
                step=500
            )
        with cF5:
            stationery_month = st.number_input(
                f"Stationery {cost_suffix()}/m",
                min_value=0,
                value=default_stationery_month,
                step=100
            )
        with cF6:
            cleaning_services_month = st.number_input(
                f"Cleaning {cost_suffix()}/m",
                min_value=0,
                value=default_cleaning_services_month,
                step=500
            )

        st.markdown("**Annual Repairs**")
        office_repairs_annual = st.number_input(
            f"Office Repairs {cost_suffix()}/yr",
            min_value=0,
            value=default_office_repairs_annual,
            step=1000
        )

    with st.expander("D. Miscellaneous", expanded=False):
        default_marketing_annual = st.session_state.get("callcentre_marketing_annual", 20000)
        default_retention_campaigns_annual = st.session_state.get("callcentre_retention_campaigns_annual", 15000)
        default_engagement_events_annual = st.session_state.get("callcentre_engagement_events_annual", 10000)
        default_liability_insurance_annual = st.session_state.get("callcentre_liability_insurance_annual", 30000)
        default_equipment_insurance_percent = st.session_state.get("callcentre_equipment_insurance_percent", 5)

        cM1, cM2 = st.columns(2)
        with cM1:
            marketing_annual = st.number_input(
                f"Marketing {cost_suffix()}/yr",
                min_value=0,
                value=default_marketing_annual,
                step=2000
            )
            retention_campaigns_annual = st.number_input(
                f"Customer Retention {cost_suffix()}/yr",
                min_value=0,
                value=default_retention_campaigns_annual,
                step=1000
            )
            engagement_events_annual = st.number_input(
                f"Team Engagement {cost_suffix()}/yr",
                min_value=0,
                value=default_engagement_events_annual,
                step=1000
            )
        with cM2:
            liability_insurance_annual = st.number_input(
                f"Insurance {cost_suffix()}/yr",
                min_value=0,
                value=default_liability_insurance_annual,
                step=2000
            )
            equipment_insurance_percent = st.number_input(
                "Equipment Insurance (%)",
                min_value=0,
                max_value=100,
                value=default_equipment_insurance_percent,
                step=1
            )

    # -------------------------------------------------------------------------
    # (F) Calculate & Compare
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Calculate Your Current Costs & Compare to askAYYI")

    calc_btn = st.button("Calculate & Compare Now")
    if calc_btn:
        # Store inputs in session
        st.session_state["callcentre_staff_count"] = staff_count
        st.session_state["callcentre_salary_per_agent"] = salary_per_agent
        st.session_state["callcentre_medical_aid_per_agent"] = medical_aid_per_agent
        st.session_state["callcentre_pension_percent"] = pension_percent
        st.session_state["callcentre_bonus_per_agent"] = bonus_incentive_per_agent
        st.session_state["callcentre_benefits_per_agent"] = monthly_benefits_per_agent
        st.session_state["callcentre_recruitment_per_agent"] = recruitment_cost_per_agent
        st.session_state["callcentre_training_per_agent"] = training_cost_per_agent
        st.session_state["callcentre_trainer_salary"] = trainer_salary
        st.session_state["callcentre_msgs_per_agent_day"] = msgs_per_agent_day
        st.session_state["callcentre_work_days_month"] = work_days_month

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

        # 1) Monthly Personnel
        monthly_salary_total = staff_count * salary_per_agent
        monthly_pension_total = monthly_salary_total * (pension_percent / 100)
        monthly_medical_total = staff_count * medical_aid_per_agent
        monthly_bonus_total = (staff_count * bonus_incentive_per_agent) / 12.0
        monthly_benefits_total = staff_count * monthly_benefits_per_agent
        trainer_monthly = trainer_salary
        monthly_personnel = (
            monthly_salary_total
            + monthly_pension_total
            + monthly_medical_total
            + monthly_bonus_total
            + monthly_benefits_total
            + trainer_monthly
        )

        # 2) Once-Off Recruitment & Training
        once_off_recruitment = staff_count * recruitment_cost_per_agent
        once_off_training = staff_count * training_cost_per_agent
        once_off_current_zar = once_off_recruitment + once_off_training

        # 3) Technology Monthly
        monthly_software = (
            call_center_software
            + (licensing_per_user * staff_count)
            + (crm_subscription_per_user * staff_count)
        )
        monthly_hardware_amort = (hardware_cost_per_station * staff_count) / (depreciation_years * 12)
        monthly_repair_maint = (repair_maintenance_per_device * staff_count) / 12
        monthly_telco = (monthly_phone_bill_per_agent * staff_count) + internet_services
        monthly_technology = monthly_software + monthly_hardware_amort + monthly_repair_maint + monthly_telco

        # 4) Facility Monthly
        monthly_facility = (
            office_rent_month
            + electricity_cost_month
            + water_cost_month
            + hvac_cost_month
            + stationery_month
            + cleaning_services_month
            + (office_repairs_annual / 12)
        )

        # 5) Misc Monthly
        monthly_marketing = (marketing_annual / 12) + (retention_campaigns_annual / 12)
        monthly_engagement = engagement_events_annual / 12
        monthly_liability_insur = liability_insurance_annual / 12
        total_hardware_value = hardware_cost_per_station * staff_count
        monthly_equipment_ins = (total_hardware_value * (equipment_insurance_percent / 100)) / 12
        monthly_misc = monthly_marketing + monthly_engagement + monthly_liability_insur + monthly_equipment_ins

        # 6) Grand Total (ZAR)
        monthly_total_current_zar = monthly_personnel + monthly_technology + monthly_facility + monthly_misc

        # Conversion factor
        ex_rate = exchange_rates.get(selected_currency, 1.0)
        if not international_mode:
            final_factor = 1.0
        else:
            final_factor = 1.3 * 1.15

        monthly_total_current_converted = (monthly_total_current_zar / ex_rate) * final_factor
        once_off_current_converted = (once_off_current_zar / ex_rate) * final_factor

        # Store final results
        st.session_state["cc_monthly_total_callcentre_zar"] = monthly_total_current_zar
        st.session_state["cc_once_off_costs_callcentre_zar"] = once_off_current_zar
        st.session_state["cc_monthly_total_callcentre"] = monthly_total_current_converted
        st.session_state["cc_once_off_costs_callcentre"] = once_off_current_converted

        from math import ceil
        def round_up_custom(x):
            return ceil(x / 10.0) * 10

        disp_monthly_cur = round_up_custom(monthly_total_current_converted)
        disp_onceoff_cur = round_up_custom(once_off_current_converted)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class='card'>
                    <h4>Current Monthly Total</h4>
                    <p style="font-size:1.2em;">
                        {symbol}{disp_monthly_cur:,} / month
                    </p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class='card'>
                    <h4>One-Off Costs (Recruit/Train)</h4>
                    <p style="font-size:1.2em;">
                        {symbol}{disp_onceoff_cur:,} total
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # Capacity Estimates
        st.markdown("---")
        st.subheader("Capacity Estimates: Calls & Messages")

        calls_per_agent_day = 70  # Example assumption
        days_month = 22
        calls_per_agent_month = calls_per_agent_day * days_month
        total_calls_capacity = calls_per_agent_month * staff_count

        st.markdown(
            f"- **Staff-based Call Capacity**: ~{calls_per_agent_day} calls/day x {days_month} days x {staff_count} agents "
            f"= ~**{total_calls_capacity:,} calls/month**"
        )

        monthly_telco_budget = (monthly_phone_bill_per_agent * staff_count)
        if call_cost_per_minute > 0:
            cost_based_minutes = monthly_telco_budget / call_cost_per_minute
        else:
            cost_based_minutes = float('inf')
        st.markdown(
            f"- **Telco Budget**: {symbol}{round_up_custom(monthly_telco_budget / ex_rate * final_factor):,}/month "
            f" => ~{int(cost_based_minutes):,} minutes (cost-based limit)"
        )

        monthly_msgs_per_agent = msgs_per_agent_day * work_days_month
        total_msgs_capacity = monthly_msgs_per_agent * staff_count
        st.markdown(
            f"- **Staff-based Message Capacity**: ~{msgs_per_agent_day} msgs/day x {work_days_month} days "
            f"x {staff_count} agents = ~**{total_msgs_capacity:,} messages/month**"
        )
        st.info(
            "Actual capacity may vary with break times, scheduling, etc. "
            "This is just a ballpark figure for comparison."
        )

        # Compare to askAYYI
        askAYYI_details = st.session_state.get("client_cost_details", None)
        if not askAYYI_details:
            st.warning("No askAYYI plan info found. Go to 'Plan Assignment' first.")
        else:
            included_msgs_ask = askAYYI_details.get("included_msgs_after_conversion", 0)
            included_mins_ask = askAYYI_details.get("included_mins_after_conversion", 0)

            st.markdown("---")
            st.subheader("Comparison with askAYYI")

            msgs_per_convo = 5
            mins_per_call = 3.0
            askAYYI_conversations = included_msgs_ask / msgs_per_convo if msgs_per_convo else 0
            askAYYI_call_capacity = included_mins_ask / mins_per_call if mins_per_call else 0

            st.markdown(f"""
                <div class="card">
                    <h4>askAYYI Included Usage</h4>
                    <ul>
                        <li><strong>Messages:</strong> {included_msgs_ask:,} (~{int(askAYYI_conversations):,} convos @ {msgs_per_convo} msgs each)</li>
                        <li><strong>Minutes:</strong> {included_mins_ask:,} (~{int(askAYYI_call_capacity):,} calls @ {mins_per_call} min each)</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

            askAYYI_monthly = askAYYI_details.get("total_monthly_cost", 0)
            askAYYI_setup = askAYYI_details.get("total_setup_cost", 0)
            disp_askAYYI_monthly = round_up_custom(askAYYI_monthly)
            disp_askAYYI_setup = round_up_custom(askAYYI_setup)

            st.markdown("---")
            cComp1, cComp2 = st.columns(2)
            with cComp1:
                st.markdown(f"""
                    <div class='card'>
                        <h4>Your Current Setup</h4>
                        <p>
                            <strong>Monthly:</strong> {symbol}{disp_monthly_cur:,}<br/>
                            <strong>One-Time:</strong> {symbol}{disp_onceoff_cur:,}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            with cComp2:
                st.markdown(f"""
                    <div class='card'>
                        <h4>askAYYI</h4>
                        <p>
                            <strong>Monthly:</strong> {symbol}{disp_askAYYI_monthly:,}<br/>
                            <strong>Setup:</strong> {symbol}{disp_askAYYI_setup:,}
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            monthly_diff = disp_monthly_cur - disp_askAYYI_monthly
            if monthly_diff > 0:
                st.success(f"Potential Monthly Savings: {symbol}{monthly_diff:,} with askAYYI!")
            elif monthly_diff < 0:
                st.warning(
                    f"askAYYI is about {symbol}{abs(monthly_diff):,} more per month, "
                    "but consider 24/7 automation & no HR overhead."
                )
            else:
                st.info("Your monthly costs match askAYYI’s plan quite closely.")

            st.markdown(
                "Even if costs are close, remember that **askAYYI** automates a large portion of interactions, "
                "which can reduce the hassle of staffing overhead and let you scale more quickly."
            )

        st.success("Calculation & comparison complete. Scroll up to see results.")

    show_footer()

###############################################################################
# TAB 6: Cost & Sales Breakdown (extremely comprehensive)
###############################################################################
with tabs[6]:
    st.title("Cost & Sales Breakdown (Comprehensive)")

    # 1. Grab your usage from session
    usage_msgs = st.session_state.get("estimated_messages", 0)
    usage_mins = st.session_state.get("estimated_minutes", 0)
    assigned_plan = st.session_state.get("client_assigned_plan", "Not Assigned")
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    symbol = CURRENCY_SYMBOLS.get(selected_currency, "R")

    # 2. Grab current cost_details from plan assignment
    cost_details = st.session_state.get("client_cost_details", None)
    if not cost_details:
        st.warning("No cost details found. Please go to 'Plan Assignment' first.")
        st.stop()

    # 3. Also fetch the call centre cost info if calculated
    cc_monthly_zar = st.session_state.get("cc_monthly_total_callcentre_zar", 0)
    cc_onceoff_zar = st.session_state.get("cc_once_off_costs_callcentre_zar", 0)

    # 4. Show summary of usage:
    st.subheader("Your Usage Summary")
    st.write(f"- **Messages**: {usage_msgs:,}")
    st.write(f"- **Voice Minutes**: {usage_mins:,}")
    st.write(f"- **Assigned Plan**: {assigned_plan}")
    st.write("---")

    # 5. Show the final monthly & setup from askAYYI (the assigned plan)
    askAYYI_monthly_cost = cost_details.get("total_monthly_cost", 0)
    askAYYI_setup_cost = cost_details.get("total_setup_cost", 0)

    # Round them for display
    from math import ceil
    def round_up_10(x):
        return ceil(x / 10) * 10

    disp_ask_monthly = round_up_10(askAYYI_monthly_cost)
    disp_ask_setup = round_up_10(askAYYI_setup_cost)

    st.subheader("askAYYI Costs")
    colAM1, colAM2 = st.columns(2)
    with colAM1:
        st.metric("Monthly (approx)", f"{symbol}{disp_ask_monthly:,}")
    with colAM2:
        st.metric("Setup (approx)", f"{symbol}{disp_ask_setup:,}")

    # 6. Compare to your "Current Costs" if available
    final_factor = 1.3 * 1.15 if pricing.get("international_mode", False) else 1.0
    ex_rate = exchange_rates.get(selected_currency, 1.0)
    cc_monthly_converted = (cc_monthly_zar / ex_rate) * final_factor
    cc_onceoff_converted = (cc_onceoff_zar / ex_rate) * final_factor
    disp_cc_monthly = round_up_10(cc_monthly_converted)
    disp_cc_onceoff = round_up_10(cc_onceoff_converted)

    st.subheader("Your Current Setup (if calculated)")
    c3, c4 = st.columns(2)
    with c3:
        st.metric("Monthly (approx)", f"{symbol}{disp_cc_monthly:,}")
    with c4:
        st.metric("One-Off (Recruit/Train)", f"{symbol}{disp_cc_onceoff:,}")

    st.write("---")
    # 7. Show a plan-by-plan breakdown for additional context
    st.subheader("Plan-by-Plan Breakdown (All Plans)")

    # We'll replicate the cost calculation for each plan, using the same usage & addons = none
    # (or minimal) for a universal comparison. 
    # If you want to include actual add-ons from session, pass them in as we do in plan assignment.
    dummy_addons = {"white_labeling": False,
                    "custom_voices": {"enabled": False, "quantity": 0, "cost_per_voice": 0},
                    "additional_languages": {"enabled": False, "quantity": 0, "cost_per_language": 0}}

    def plan_cost_short(plan_name):
        # Re-use your existing `calculate_plan_cost` function (assume we have it in scope)
        # Or replicate minimal logic here. We'll assume you have the function imported.
        result = calculate_plan_cost(
            plan_name=plan_name,
            num_agents=0,  # for quick comparison
            usage={"used_messages": usage_msgs, "used_minutes": usage_mins},
            addons=dummy_addons,
            exchange_rates=exchange_rates,
            selected_currency=selected_currency,
            pricing=pricing,
            usage_limits=usage_limits,
            communication_type="Both Messages & Voice"
        )
        mcost = result["total_monthly_cost"]
        scost = result["total_setup_cost"]
        return (mcost, scost, result["included_msgs_after_conversion"], result["included_mins_after_conversion"])

    # Build a table-like display
    plan_rows = []
    for pnm in pricing["plans"].keys():
        mcost, scost, incl_msgs, incl_mins = plan_cost_short(pnm)
        plan_rows.append({
            "Plan": pnm,
            "Included Msgs": incl_msgs,
            "Included Mins": incl_mins,
            "Monthly": round_up_10(mcost),
            "Setup": round_up_10(scost)
        })

    df_plans = pd.DataFrame(plan_rows)
    st.dataframe(df_plans.style.format({"Monthly": f"{symbol}{{:,.0f}}",
                                        "Setup": f"{symbol}{{:,.0f}}"}))

    st.write("---")
    st.markdown("""
    **Notes**:
    - The table above uses your current usage (messages/minutes) to estimate overage. 
      For each plan, we've assumed 0 additional agents & no add-ons for a fair baseline comparison. 
    - If your usage exceeds the included amounts for a given plan, top-up costs are baked into that "Monthly" column.
    """)

    # 8. Show approximate "Humans needed" for the chosen usage
    # E.g., how many total messages/calls => how many staff or hours needed
    st.subheader("Approximate Human Staffing Equivalent for Your Usage")
    # Example: each human can handle X messages/day or Y calls/day, use the logic from tab 5
    staff_msgs_day = st.session_state.get("callcentre_msgs_per_agent_day", 100)
    staff_workdays = st.session_state.get("callcentre_work_days_month", 20)
    if staff_msgs_day < 1: staff_msgs_day = 1
    if staff_workdays < 1: staff_workdays = 1

    monthly_agent_capacity_msgs = staff_msgs_day * staff_workdays
    if monthly_agent_capacity_msgs < 1:
        monthly_agent_capacity_msgs = 1

    # If usage_msgs is X, how many agents are needed to handle that?
    needed_for_msgs = usage_msgs / monthly_agent_capacity_msgs
    staff_calls_day = 70  # or from user input above
    monthly_agent_capacity_calls = staff_calls_day * staff_workdays

    # If usage_mins is ~ calls? Let's assume each call is 3 mins
    estimated_calls = usage_mins / 3.0
    needed_for_calls = estimated_calls / monthly_agent_capacity_calls if monthly_agent_capacity_calls else 0

    # total staff needed
    total_staff_needed = max(needed_for_msgs, needed_for_calls)

    st.write(f"- You have ~**{usage_msgs:,}** messages & ~**{usage_mins:,}** voice minutes monthly.")
    st.write(f"- If each agent handles ~{staff_msgs_day} msgs/day for {staff_workdays} days => ~{int(monthly_agent_capacity_msgs):,} msgs/month per agent.")
    st.write(f"- For **messages**, you'd need ~**{needed_for_msgs:.1f}** agents.")
    st.write(f"- For **calls**, if each call = 3 mins, that's ~{int(estimated_calls):,} calls => ~**{needed_for_calls:.1f}** agents.")
    st.info(f"Overall, you'd likely need ~**{total_staff_needed:.1f}** agents for both messages & calls (some cross-training).")

    # 9. Provide concluding statements or next steps
    st.markdown("---")
    st.success("This comprehensive breakdown should help you decide on the best plan & evaluate cost savings.")
    st.markdown("""
    - You can further refine calculations by adjusting staff capacity, work days, average call durations, and more in the **"Your Current Costs"** tab.
    - Revisit the **"Plan Assignment"** tab to fine-tune usage or add-ons.
    """)

    show_footer()