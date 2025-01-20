import streamlit as st
from streamlit.runtime.scriptrunner import RerunException, RerunData
import json
import os
import pandas as pd
import math
from datetime import datetime, date
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
EMPLOYEE_COSTS_FILE = os.path.join(CONFIG_DIR, 'employee_costs.json')  # NEW FILE FOR STORING EMPLOYEE COSTS

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

# NEW: DEFAULT EMPLOYEE COSTS (for demonstration)
# Note: You can adjust or expand these roles as needed.
DEFAULT_EMPLOYEE_COSTS = {
    "C-Level Management": {
        "CEO - RCS Executive": {"annual_salary": 1200000, "annual_increase_pct": 5},
        "CTO - RCS Executive": {"annual_salary": 1100000, "annual_increase_pct": 5},
        "CMO - RCS Executive": {"annual_salary": 1000000, "annual_increase_pct": 5},
    },
    "Operational Management": {
        "Operations Manager": {"annual_salary": 600000, "annual_increase_pct": 5},
        "Sales & Marketing Manager": {"annual_salary": 650000, "annual_increase_pct": 5},
        "Accountant": {"annual_salary": 400000, "annual_increase_pct": 5},
    },
    "R&D / Development / Technical Support Management": {
        "Full Stack Developer": {"annual_salary": 550000, "annual_increase_pct": 5},
        "Cloud Infrastructure Engineer": {"annual_salary": 700000, "annual_increase_pct": 5},
        "Chief Product Officer (CPO)": {"annual_salary": 900000, "annual_increase_pct": 5},
        "Development Operations Engineer (DEV OP)": {"annual_salary": 650000, "annual_increase_pct": 5},
        "Programmer - UI & UX Designer": {"annual_salary": 500000, "annual_increase_pct": 5},
        "AI Machine Learning Engineer (AI/ML)": {"annual_salary": 900000, "annual_increase_pct": 5},
        "Technical Support Programmers": {"annual_salary": 450000, "annual_increase_pct": 5},
    },
    "Tech - Soft & Hardware": {
        "Software Subscriptions": {"annual_salary": 100000, "annual_increase_pct": 10},  # Interpreting as annual budget
        "Software": {"annual_salary": 100000, "annual_increase_pct": 10},               # Interpreting as annual budget
    },
    "Operations": {
        "Office Rental": {"annual_salary": 360000, "annual_increase_pct": 6},
        "Communications": {"annual_salary": 120000, "annual_increase_pct": 6},
        "Administration": {"annual_salary": 240000, "annual_increase_pct": 6},
        "Insurance": {"annual_salary": 100000, "annual_increase_pct": 6},
        "Logistics": {"annual_salary": 120000, "annual_increase_pct": 6},
        "Transport": {"annual_salary": 90000, "annual_increase_pct": 6},
        "Legal": {"annual_salary": 100000, "annual_increase_pct": 6},
        "Sundry": {"annual_salary": 50000, "annual_increase_pct": 6},
    },
    # Additional staff that vary with plan usage
    # We'll keep them separate so we can do partial FTE calculations
    "Variable Roles": {
        "Onboarding Specialist": {"monthly_salary": 25000, "annual_increase_pct": 5},
        "Technical Support Manager": {"monthly_salary": 30000, "annual_increase_pct": 5},
    }
}

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

    # Employee Costs
    # We will store the default structure in a file if it doesn't exist
    if not os.path.isfile(EMPLOYEE_COSTS_FILE):
        with open(EMPLOYEE_COSTS_FILE, 'w') as f:
            json.dump(DEFAULT_EMPLOYEE_COSTS, f, indent=4)
    else:
        try:
            with open(EMPLOYEE_COSTS_FILE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            st.error("Employee costs config invalid JSON. Re-creating with defaults.")
            with open(EMPLOYEE_COSTS_FILE, 'w') as f:
                json.dump(DEFAULT_EMPLOYEE_COSTS, f, indent=4)

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

def calculate_employee_annual_salary(base_salary, annual_increase_pct, year_index):
    """
    Returns the salary for the given year_index (1-based).
    year_index=1 -> base year,
    year_index=2 -> base salary with first increment, etc.
    """
    return base_salary * ((1 + annual_increase_pct / 100) ** (year_index - 1))

def calculate_onboarding_hours_for_year(base_onboarding_hours, year_index):
    """
    50% reduction each year in onboarding time.
    year_index=1 -> full base_onboarding_hours
    year_index=2 -> base_onboarding_hours * 0.5
    year_index=3 -> base_onboarding_hours * 0.25, etc.
    """
    return base_onboarding_hours * (0.5 ** (year_index - 1))

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
    """
    This function calculates the monthly cost, setup cost, and total cost
    for a specific plan, taking into account usage, add-ons, exchange rates, etc.
    """
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

    # Communication type conversion logic
    if communication_type == "Just Messages":
        # Convert included_mins to extra messages
        cost_of_included_mins_zar = included_mins * final_min_cost_zar
        extra_msgs_from_mins = 0
        if final_msg_cost_zar != 0:
            extra_msgs_from_mins = int(cost_of_included_mins_zar / final_msg_cost_zar)
        included_msgs += extra_msgs_from_mins
        included_mins = 0
    elif communication_type == "Just Minutes":
        # Convert included_msgs to extra minutes
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

    # Contingency
    monthly_cost_zar *= (1 + contingency_percent)

    total_setup_cost_zar = total_base_setup_fee_zar + setup_cost_assistants_zar

    # International mode
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

    # Currency conversion
    exchange_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        # Hard-coded further multipliers
        final_factor = 1.3 * 1.15

    monthly_cost_converted = (monthly_cost_zar / exchange_rate) * final_factor
    setup_cost_converted = (total_setup_cost_zar / exchange_rate) * final_factor

    # Add-ons
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

# -----------------------------------------------------------------------------
# Streamlit App starts here
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(layout="wide")
    apply_custom_css()
    initialize_configs()

    pricing = load_config(PRICING_FILE)
    usage_limits = load_config(USAGE_LIMITS_FILE)
    exchange_rates = load_config(EXCHANGE_RATES_FILE)

    # Load (or create) employee costs config
    employee_costs_data = load_config(EMPLOYEE_COSTS_FILE)
    if employee_costs_data is None:
        employee_costs_data = DEFAULT_EMPLOYEE_COSTS

    tabs = st.tabs(["Plan Assignment", "Client Summary", "Admin Dashboard (Internal)", "Investor Dashboard"])

    # NOTE: We do not see the user's code for "Plan Assignment" or "Client Summary" tabs here,
    # but we replicate the final snippet for the "Admin Dashboard (Internal)" (tabs[2]) plus a new
    # tab for the Investor Dashboard (tabs[3]).

    with tabs[2]:
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

    # -----------------------------------------------------------------------------
    # NEW TAB: INVESTOR DASHBOARD
    # -----------------------------------------------------------------------------
    with tabs[3]:
        st.title("Investor Dashboard")
        st.write("Plan your long-term financial projections, including:")
        st.write(" - **Operational Expenses**")
        st.write(" - **Staffing Costs** (with annual increases)")
        st.write(" - **Projected Clients** (growth over time)")
        st.write(" - **Onboarding & Technical Support** partial-FTE calculations")
        st.write(" - **Revenue & Profit Projections**")

        st.markdown("---")

        # --------------------
        # 1. ALLOW EDITING OF EMPLOYEE COSTS
        # --------------------
        st.subheader("1. Operational Expenses & Salary Costs Configuration")

        if "edited_employee_costs" not in st.session_state:
            st.session_state["edited_employee_costs"] = employee_costs_data

        # We let the user expand each category and edit salaries / annual inc.
        for cat_name, roles_dict in st.session_state["edited_employee_costs"].items():
            with st.expander(f"{cat_name}", expanded=(cat_name == "C-Level Management")):
                to_remove = []
                for role_name, cost_info in roles_dict.items():
                    if "monthly_salary" in cost_info:
                        # This is a monthly-based role
                        col1, col2 = st.columns([2,1])
                        with col1:
                            new_monthly_sal = st.number_input(
                                f"{role_name} - Monthly Salary (ZAR)",
                                value=float(cost_info["monthly_salary"]),
                                step=1000.0,
                                key=f"{cat_name}_{role_name}_monthly_sal"
                            )
                        with col2:
                            new_annual_inc = st.number_input(
                                f"{role_name} - Annual Increase (%)",
                                value=float(cost_info["annual_increase_pct"]),
                                step=1.0,
                                key=f"{cat_name}_{role_name}_annual_inc"
                            )
                        cost_info["monthly_salary"] = new_monthly_sal
                        cost_info["annual_increase_pct"] = new_annual_inc
                    else:
                        # Assume annual-based role
                        col1, col2 = st.columns([2,1])
                        with col1:
                            new_annual_sal = st.number_input(
                                f"{role_name} - Annual Salary/Budget (ZAR)",
                                value=float(cost_info["annual_salary"]),
                                step=10000.0,
                                key=f"{cat_name}_{role_name}_annual_sal"
                            )
                        with col2:
                            new_annual_inc = st.number_input(
                                f"{role_name} - Annual Increase (%)",
                                value=float(cost_info["annual_increase_pct"]),
                                step=1.0,
                                key=f"{cat_name}_{role_name}_annual_inc"
                            )
                        cost_info["annual_salary"] = new_annual_sal
                        cost_info["annual_increase_pct"] = new_annual_inc

                    remove_key = f"remove_{cat_name}_{role_name}".replace(" ", "_")
                    if st.checkbox(f"Remove {role_name}", key=remove_key):
                        to_remove.append(role_name)

                # Remove roles if user requested
                for rm in to_remove:
                    del roles_dict[rm]

                # Option to add a new role
                new_role_name = st.text_input(f"Add new role to {cat_name}", value="", key=f"new_role_{cat_name}")
                if new_role_name.strip():
                    add_salary = st.number_input(
                        f"{new_role_name} - Salary/Budget (ZAR)",
                        value=0.0,
                        step=1000.0,
                        key=f"{new_role_name}_{cat_name}_salary_input"
                    )
                    add_inc = st.number_input(
                        f"{new_role_name} - Annual Increase (%)",
                        value=0.0,
                        step=1.0,
                        key=f"{new_role_name}_{cat_name}_inc_input"
                    )
                    monthly_or_annual = st.selectbox(
                        f"{new_role_name} Salary Type",
                        ["Annual", "Monthly"],
                        key=f"{new_role_name}_{cat_name}_salary_type"
                    )
                    if st.button(f"Confirm Add {new_role_name}", key=f"confirm_add_{cat_name}_{new_role_name}"):
                        if monthly_or_annual == "Monthly":
                            roles_dict[new_role_name] = {
                                "monthly_salary": add_salary,
                                "annual_increase_pct": add_inc
                            }
                        else:
                            roles_dict[new_role_name] = {
                                "annual_salary": add_salary,
                                "annual_increase_pct": add_inc
                            }
                        st.success(f"Added {new_role_name} to {cat_name}")

        # Save all changes to file
        if st.button("Save All Employee/Expense Changes"):
            # Overwrite the JSON file
            with open(EMPLOYEE_COSTS_FILE, 'w') as f:
                json.dump(st.session_state["edited_employee_costs"], f, indent=4)
            st.success("Employee & expenses data saved successfully!")

        st.markdown("---")

        # --------------------
        # 2. GROWTH & PROJECTION INPUTS
        # --------------------
        st.subheader("2. Projection Period & Client Growth")

        projection_start = st.date_input("Projection Start Date", value=date.today())
        projection_end = st.date_input("Projection End Date", value=date( date.today().year+2, date.today().month, date.today().day ))
        if projection_end < projection_start:
            st.warning("End date cannot be before start date. Adjusting.")
            projection_end = projection_start

        growth_period_choice = st.selectbox("Growth Period Step", ["Monthly", "Quarterly", "Yearly"])
        monthly_growth_pct = st.number_input("Projected Growth per Step (%)", value=5.0, step=1.0)

        # We'll assume some base number of clients at the start
        base_clients = st.number_input("Base # of Clients at Start", value=10, step=1)
        plan_selected_for_projection = st.selectbox("Select Plan for Projections", list(pricing["plans"].keys()))

        # Onboarding / Technical partial staff logic
        st.markdown("""
        **Onboarding & Technical Support Staff**:  
        We want to calculate how many Onboarding Specialists & Technical Support Managers we need
        based on partial FTE. We'll assume 160 hours/month capacity per specialist/manager.
        """)
        hours_capacity_per_fte = 160

        # We prepare a table of months (or quarters/years), client count, new clients, total staff needed, etc.
        st.markdown("Click 'Calculate Projection' to generate a financial summary.")
        if st.button("Calculate Projection"):
            # Build date range
            all_periods = []
            current_date = projection_start

            # Convert the plan's base_onboarding_hours for Year 1, Year 2, etc.
            plan_onboarding_hrs = pricing["plans"][plan_selected_for_projection].get("onboarding_support_hours", 0)
            plan_tech_hrs       = pricing["plans"][plan_selected_for_projection].get("technical_support_hours", 0)

            # Helper to advance current_date by chosen step
            def add_step(dt, step):
                if step == "Monthly":
                    month = dt.month + 1
                    year = dt.year
                    if month > 12:
                        month = 1
                        year += 1
                    return date(year, month, dt.day)
                elif step == "Quarterly":
                    month = dt.month + 3
                    year = dt.year
                    if month > 12:
                        month -= 12
                        year += 1
                    # If day is out of range, just adjust to end-of-month
                    day = min(dt.day, 28)  # a slight hack
                    return date(year, month, day)
                else:  # Yearly
                    return date(dt.year + 1, dt.month, dt.day)

            period_index = 1
            current_clients = base_clients
            result_data = []

            while current_date <= projection_end:
                # Figure out how many new clients or total clients
                # We'll assume each step, we multiply current clients by (1 + monthly_growth_pct/100).
                if period_index == 1:
                    new_clients = current_clients
                else:
                    old_clients = current_clients
                    current_clients = int(old_clients * (1 + monthly_growth_pct / 100))
                    new_clients = current_clients - old_clients

                # Onboarding hours needed for year_index
                # We'll approximate year_index from the difference in years from start
                # i.e. year_index=1 for the first 12 months, year_index=2 for the next, etc.
                year_diff = (current_date.year - projection_start.year)
                # a simpler approach: each 12 steps = a new year
                if growth_period_choice == "Monthly":
                    year_index = (period_index - 1) // 12 + 1
                elif growth_period_choice == "Quarterly":
                    year_index = (period_index - 1) // 4 + 1
                else:
                    year_index = period_index

                onboarding_hrs_for_period = calculate_onboarding_hours_for_year(plan_onboarding_hrs, year_index) * new_clients
                tech_hrs_for_period = plan_tech_hrs * current_clients  # or new_clients, depending on logic

                # partial FTE
                onboarding_fte = onboarding_hrs_for_period / hours_capacity_per_fte
                technical_fte = tech_hrs_for_period / hours_capacity_per_fte

                result_data.append({
                    "Date": current_date.isoformat(),
                    "Period": period_index,
                    "Total Clients": current_clients,
                    "New Clients": new_clients,
                    "Onboarding Hours This Period": round(onboarding_hrs_for_period, 2),
                    "Onboarding FTE": round(onboarding_fte, 3),
                    "Technical Hours This Period": round(tech_hrs_for_period, 2),
                    "Technical FTE": round(technical_fte, 3),
                    "Year Index": year_index
                })

                current_date = add_step(current_date, growth_period_choice)
                period_index += 1

            df_projection = pd.DataFrame(result_data)
            st.dataframe(df_projection)

            # Summaries
            total_onboarding_fte = df_projection["Onboarding FTE"].sum()
            total_technical_fte = df_projection["Technical FTE"].sum()

            st.markdown(f"**Total Onboarding FTE (summed across periods):** {total_onboarding_fte:,.2f}")
            st.markdown(f"**Total Technical FTE (summed across periods):** {total_technical_fte:,.2f}")

            # Next, we estimate cost of these variable roles
            # We sum up period by period, calculating the monthly cost for that fraction of an FTE
            # and then sum all periods. For simplicity, we treat each period as 1 month if "Monthly",
            # 3 months if "Quarterly", 12 if "Yearly", etc.
            def period_length_in_months(step):
                if step == "Monthly":
                    return 1
                elif step == "Quarterly":
                    return 3
                else:
                    return 12

            var_roles = st.session_state["edited_employee_costs"].get("Variable Roles", {})
            onboarding_specialist = var_roles.get("Onboarding Specialist", {})
            tech_support_manager = var_roles.get("Technical Support Manager", {})

            def monthly_salary_for_year(base_monthly, annual_increase_pct, year_index):
                # Year 1 = base_monthly,
                # Year 2 = base_monthly * (1 + inc)^1, etc.
                return base_monthly * ((1 + annual_increase_pct / 100) ** (year_index - 1))

            total_onboarding_cost = 0.0
            total_technical_cost = 0.0

            for idx, row in df_projection.iterrows():
                # For each row, figure out the monthly salary for that "Year Index"
                per_len = period_length_in_months(growth_period_choice)
                # Onboarding cost
                if "monthly_salary" in onboarding_specialist:
                    yoy_onb_sal = monthly_salary_for_year(
                        onboarding_specialist["monthly_salary"],
                        onboarding_specialist["annual_increase_pct"],
                        row["Year Index"]
                    )
                    cost_onb = yoy_onb_sal * row["Onboarding FTE"] * per_len
                else:
                    cost_onb = 0

                # Tech cost
                if "monthly_salary" in tech_support_manager:
                    yoy_tech_sal = monthly_salary_for_year(
                        tech_support_manager["monthly_salary"],
                        tech_support_manager["annual_increase_pct"],
                        row["Year Index"]
                    )
                    cost_tech = yoy_tech_sal * row["Technical FTE"] * per_len
                else:
                    cost_tech = 0

                total_onboarding_cost += cost_onb
                total_technical_cost += cost_tech

            st.markdown(f"**Variable Onboarding Specialist Cost (Total Over Projection):** R{total_onboarding_cost:,.2f}")
            st.markdown(f"**Variable Technical Support Manager Cost (Total Over Projection):** R{total_technical_cost:,.2f}")

            # Next, we add fixed costs (C-level, Operational, R&D, Tech SW/HW, etc.)
            # We'll do year-by-year calculation. We'll find how many "distinct years" are in the projection.
            # We'll accumulate the cost for each year. Then sum it.

            # Distinct set of years in the df
            distinct_years = df_projection["Year Index"].unique()
            fixed_cost_total = 0.0
            for yidx in distinct_years:
                # For each year index, we sum annual cost of each role with yoy increase
                # Then we figure out how many periods in that year. Or simpler: we assume
                # if "annual_salary" we just add once for that year.
                # If the user gave us monthly, we multiply monthly * 12 for that year.
                # For partial: the date-based approach can get complicated, but let's keep it simpler.

                # The number of periods that belong to this year_index:
                # we can do df_projection[df_projection["Year Index"]==yidx].shape[0]
                # For a monthly role, we do monthly * 12 for that entire year. This is a high-level approximation.
                # More precise would be to see if the end date is partial-year, but let's keep it simpler for now.

                for cat_n, roles_d in st.session_state["edited_employee_costs"].items():
                    if cat_n == "Variable Roles":
                        continue  # Already handled
                    for rname, rcost in roles_d.items():
                        if "annual_salary" in rcost:
                            yoy_annual = calculate_employee_annual_salary(
                                rcost["annual_salary"],
                                rcost["annual_increase_pct"],
                                yidx
                            )
                            fixed_cost_total += yoy_annual
                        elif "monthly_salary" in rcost:
                            yoy_monthly = monthly_salary_for_year(
                                rcost["monthly_salary"],
                                rcost["annual_increase_pct"],
                                yidx
                            )
                            # Multiply by 12 for that year
                            fixed_cost_total += (yoy_monthly * 12)

            st.markdown(f"**Fixed Cost (All Non-Variable Roles) Over Projection Period:** R{fixed_cost_total:,.2f}")

            grand_total_cost = fixed_cost_total + total_onboarding_cost + total_technical_cost
            st.markdown(f"## **Grand Total Expense Over {len(distinct_years)} Year(s): R{grand_total_cost:,.2f}**")

            st.info("Revenue Projection could also be computed similarly by applying the plan cost per client each period. That would give us a complete P&L statement.")

        st.markdown("---")
        show_footer()

if __name__ == "__main__":
    main()
