import streamlit as st
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
import random
import math  # For ceiling

# ======================================
# CONFIGURATION FILES (JSON)
# ======================================
CONFIG_DIR = 'config'
PRICING_FILE = os.path.join(CONFIG_DIR, 'pricing.json')
USAGE_LIMITS_FILE = os.path.join(CONFIG_DIR, 'usage_limits.json')
EXCHANGE_RATES_FILE = os.path.join(CONFIG_DIR, 'exchange_rates.json')

# We'll store user submissions here (now keyed by random reference)
CLIENT_CONFIGS_FILE = os.path.join(CONFIG_DIR, 'client_configurations.json')

# ======================================
# DEFAULT CONFIGURATIONS
# ======================================
DEFAULT_PRICING = {
    "plans": {
        "Basic": {
            "setup_fee": 7800,
            "messages": 5000,
            "voice_minutes": 300,
            "crm_access": True,
            "platforms": "All Platforms",
            "onboarding_support_hours": 3,
            "maintenance_hours": 2,
            "maintenance_hourly_rate": 300,
            "setup_hours": 5,
            "setup_hourly_rate": 500,
            "limitations": {
                "use_cases": 1,
                "assistants": 1
            },
            "optional_addons": {
                "white_labeling": 14500,
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
            "technical_support_cost": 1000,
            "float_cost": 500,
            "contingency_percent": 2.5
        },
        "Advanced": {
            "setup_fee": 19200,
            "messages": 10000,
            "voice_minutes": 500,
            "crm_integration": True,
            "api_integrations_fee": 9800,
            "platforms": "All Platforms",
            "onboarding_support_hours": 6,
            "maintenance_hours": 4,
            "maintenance_hourly_rate": 350,
            "setup_hours": 8,
            "setup_hourly_rate": 650,
            "limitations": {
                "use_cases": 1,
                "assistants": 1
            },
            "optional_addons": {
                "white_labeling": 14500,
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
            "technical_support_cost": 3000,
            "float_cost": 1000,
            "contingency_percent": 2.5
        },
        "Enterprise": {
            "setup_fee": 33300,
            "messages": 60000,
            "voice_minutes": 6000,
            "crm_integration": True,
            "api_integrations_fee": 9800,
            "platforms": "All Platforms",
            "onboarding_support_hours": 9,
            "maintenance_hours": 6,
            "maintenance_hourly_rate": 400,
            "setup_hours": 12,
            "setup_hourly_rate": 800,
            "limitations": {
                "use_cases": 1,
                "assistants": 1
            },
            "additional_options": {
                "add_use_case_fee": 25000,
                "extra_messages_per_additional_assistant": 3000,
                "extra_minutes_per_additional_assistant": 300
            },
            "optional_addons": {
                "white_labeling": 14500,
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
            "technical_support_cost": 8000,
            "float_cost": 3000,
            "contingency_percent": 2.5,
            "setup_cost_per_assistant": 5000
        }
    },
    "discounts_enabled": True,
    "international_mode": False,   # Removed "Legacy Toggle" phrasing
    "whitelabel_waved": False,
    "global_discount_rate": 10
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

MIN_PLAN_DURATION = {
    "Basic": 3,
    "Advanced": 3,
    "Enterprise": 3
}

# ======================================
# HELPER FUNCTIONS
# ======================================
def safe_int(value, default=0):
    """Attempt integer conversion; fallback to default on error."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def safe_float(value, default=0.0):
    """Attempt float conversion; fallback to default on error."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def initialize_configs():
    """
    Ensures JSON config files exist or are updated if missing keys.
    This helps prevent KeyErrors or missing-file issues.
    """
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    # -- P R I C I N G --
    if not os.path.isfile(PRICING_FILE):
        with open(PRICING_FILE, 'w') as f:
            json.dump(DEFAULT_PRICING, f, indent=4)
    else:
        try:
            with open(PRICING_FILE, 'r') as f:
                pricing = json.load(f)
        except json.JSONDecodeError:
            st.error("Pricing config invalid JSON. Re-creating with defaults.")
            pricing = DEFAULT_PRICING
        
        if not isinstance(pricing, dict):
            st.error("Pricing config is malformed. Replacing with defaults.")
            pricing = DEFAULT_PRICING
        
        updated = False
        if "plans" not in pricing:
            pricing["plans"] = {}
            updated = True
        for plan, details in DEFAULT_PRICING["plans"].items():
            if plan not in pricing["plans"]:
                pricing["plans"][plan] = details
                updated = True
            else:
                # Ensure each key in DEFAULT_PRICING is present
                for key, val in details.items():
                    if key not in pricing["plans"][plan]:
                        pricing["plans"][plan][key] = val
                        updated = True
                    elif isinstance(val, dict):
                        # If it's a nested dict, ensure sub-keys exist
                        for subk, subv in val.items():
                            if subk not in pricing["plans"][plan][key]:
                                pricing["plans"][plan][key][subk] = subv
                                updated = True

        for k in ["discounts_enabled", "international_mode", "whitelabel_waved", "global_discount_rate"]:
            if k not in pricing:
                pricing[k] = DEFAULT_PRICING[k]
                updated = True

        if updated:
            try:
                with open(PRICING_FILE, 'w') as f:
                    json.dump(pricing, f, indent=4)
            except IOError as e:
                st.error(f"Unable to update pricing config: {e}")

    # -- U S A G E   L I M I T S --
    if not os.path.isfile(USAGE_LIMITS_FILE):
        with open(USAGE_LIMITS_FILE, 'w') as f:
            json.dump(DEFAULT_USAGE_LIMITS, f, indent=4)
    else:
        try:
            with open(USAGE_LIMITS_FILE, 'r') as f:
                json.load(f)  # confirm valid JSON
        except json.JSONDecodeError:
            st.error("Usage limits config invalid JSON. Re-creating with defaults.")
            with open(USAGE_LIMITS_FILE, 'w') as f:
                json.dump(DEFAULT_USAGE_LIMITS, f, indent=4)

    # -- E X C H A N G E   R A T E S --
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

    # -- C L I E N T   C O N F I G S --
    if not os.path.isfile(CLIENT_CONFIGS_FILE):
        with open(CLIENT_CONFIGS_FILE, 'w') as f:
            json.dump({}, f, indent=4)

def load_config(file_path):
    """
    Safely loads a JSON file. Returns a dictionary or None if issues occur.
    """
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

def save_config(file_path, data):
    """
    Saves a dictionary to JSON, catching IO errors if they occur.
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        st.error(f"Error saving config to {file_path}: {e}")

def load_client_configs():
    """
    Load the stored client configurations from JSON, keyed by reference ID.
    """
    if not os.path.isfile(CLIENT_CONFIGS_FILE):
        return {}
    with open(CLIENT_CONFIGS_FILE, 'r') as f:
        return json.load(f)

def save_client_config(ref_id, config_data):
    """
    Save or update a single client's data in the client_configs file, keyed by reference ID.
    """
    all_configs = load_client_configs()
    all_configs[ref_id] = config_data
    try:
        with open(CLIENT_CONFIGS_FILE, 'w') as f:
            json.dump(all_configs, f, indent=4)
    except IOError as e:
        st.error(f"Error saving client config: {e}")

def apply_custom_css():
    """
    Custom style for the app. Hides default Streamlit elements & customizes layout.
    """
    st.markdown(
        """
        <style>
        /* Overall App */
        .stApp {
            background-color: #FAFAFA;
            color: #1D1D1F;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Top tabs styling */
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

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #4CAF50;
            font-family: 'Arial Black', Gadget, sans-serif;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 24px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #43A047;
        }
        
        /* Input Label */
        label {
            color: #1D1D1F !important;
            font-weight: bold;
        }
        
        /* Radio/Checkbox text */
        .stCheckbox > label > div > div, .stRadio > label > div {
            color: #1D1D1F;
            font-weight: normal;
        }
        
        /* Table */
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
        
        /* Card-like containers */
        .card {
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
        }
        .card h4 {
            color: #4CAF50;
            margin-bottom: 0.5em;
        }
        .card p {
            font-size: 1.1em;
            margin: 0;
        }
        
        /* Metric styling */
        .block-container .stMetric {
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #ddd;
            background-color: #f9f9f9;
        }

        /* Minimal style sections */
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
        
        /* Footer styling */
        .footer-text {
            text-align: center;
            font-size: 0.85em;
            margin-top: 50px;
            color: #888;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def authenticate_admin():
    """
    Simple password check to restrict access to admin pages (and saved configs).
    Password is: RCS_18112@
    """
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

def rerun_script():
    """
    Updated to use st.query_params instead of st.experimental_set_query_params.
    This writes a random param to the URL, causing the app to re-run.
    """
    try:
        st.query_params["_random"] = str(random.random())  # triggers re-run
    except Exception as e:
        st.warning(f"Could not update query params: {e}. Please check your Streamlit version.")

def compute_llm_overhead_per_msg():
    """
    Combine all selected LLMs’ costs into a single overhead (USD) per message or minute.
    
    How it's calculated (example logic):
      1. For each selected model, we multiply:
         (input_cost_per_million + output_cost_per_million) 
         * (avg_input_tokens + avg_output_tokens) / 1,000,000
      2. Sum across all checked models.
      3. Convert total USD -> ZAR using exchange rate + overhead factor.
      4. Return that as the “LLM overhead in ZAR” per single message or minute. 
         (You may split them if you want separate overhead for messages vs. minutes.)
    """
    # Defaults
    exchange_rates = load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    ex_rate = exchange_rates.get(selected_currency, 1.0)

    # Overhead factor if not ZAR
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        final_factor = 1.3 * 1.15

    # We'll assume user has saved these in session_state
    # (Make sure to .setdefault them in the main code if not found.)
    llm_input_cost = st.session_state.get("llm_cost_input_per_million", 0.0)   # USD
    llm_output_cost = st.session_state.get("llm_cost_output_per_million", 0.0) # USD
    avg_tokens = st.session_state.get("llm_avg_tokens_per_message", 0.0)
    
    # Models user selected
    models_selected = st.session_state.get("llm_models_used", {
        "perplexity": False,
        "gpt4o-mini": False,
        "gpt4o": False,
        "llama": False,
        "other": False
    })

    # Suppose each selected model uses the same cost. 
    # If you want different costs per model, expand logic accordingly.
    num_models = sum(models_selected.values())

    if num_models == 0:
        return 0.0  # no overhead if no LLM chosen

    # For simplicity: total cost for one message = 
    #   sum(all selected) => model_count * ((llm_input_cost + llm_output_cost) * (avg_tokens / 1e6))
    # Then convert to ZAR with overhead factor.
    total_usd = num_models * (llm_input_cost + llm_output_cost) * (avg_tokens / 1_000_000.0)
    llm_cost_zar = total_usd * ex_rate * final_factor

    return llm_cost_zar

def compute_llm_overhead_per_minute():
    """
    If you want to apply LLM cost to minutes (e.g. for transcription or real-time voice)
    you can do something very similar to `compute_llm_overhead_per_msg()` 
    or treat them differently. 
    For now, let's just reuse the same overhead for demonstration.
    """
    return compute_llm_overhead_per_msg()

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
    Core cost calculation in ZAR internally, then converted.
    Now includes LLM overhead for messages and minutes.
    """
    plan = pricing["plans"][plan_name]

    # 1. Gather plan data from admin config
    base_fee_zar = plan.get("base_fee", 0)
    base_msg_cost_zar = plan.get("base_msg_cost", 0.05)
    msg_markup = plan.get("msg_markup", 2.0)
    base_min_cost_zar = plan.get("base_min_cost", 0.40)
    min_markup = plan.get("min_markup", 2.0)
    tech_support_zar = plan.get("technical_support_cost", 0)
    float_cost_zar = plan.get("float_cost", 0)
    contingency_percent = plan.get("contingency_percent", 2.5) / 100.0

    # --- NEW: LLM Overhead Incorporation ---
    llm_overhead_per_msg_zar = compute_llm_overhead_per_msg()  # cost per single text message
    llm_overhead_per_min_zar = compute_llm_overhead_per_minute()  # cost per voice minute if relevant

    # Adjust plan’s base cost so it includes the LLM overhead
    # e.g. final base for msg = (base_msg_cost + LLM overhead) * markup
    # This is a simplistic demonstration. Tweak as needed.
    final_msg_cost_zar = (base_msg_cost_zar + llm_overhead_per_msg_zar) * msg_markup
    final_min_cost_zar = (base_min_cost_zar + llm_overhead_per_min_zar) * min_markup

    # Maintenance
    maintenance_hours = plan.get("maintenance_hours", 0)
    maintenance_hourly_rate = plan.get("maintenance_hourly_rate", 0)
    maintenance_cost_zar = maintenance_hours * maintenance_hourly_rate

    # Setup
    setup_hours = plan.get("setup_hours", 0)
    setup_hourly_rate = plan.get("setup_hourly_rate", 0)
    setup_hours_cost_zar = setup_hours * setup_hourly_rate
    setup_fee_zar = plan.get("setup_fee", 0)

    # Additional cost if multiple agents (Enterprise or otherwise)
    setup_cost_per_assistant_zar = plan.get("setup_cost_per_assistant", 7800)
    if plan_name == "Enterprise":
        # If user has >1 agent
        setup_cost_assistants_zar = setup_cost_per_assistant_zar * max(num_agents - 1, 0)
    else:
        setup_cost_assistants_zar = setup_cost_per_assistant_zar * (num_agents - 1) if num_agents > 1 else 0

    # Included usage from plan
    included_msgs = plan.get("messages", 0)
    included_mins = plan.get("voice_minutes", 0)

    # For Enterprise, each additional agent also gets some extra usage
    extra_messages_per_assistant = 0
    extra_minutes_per_assistant = 0
    if plan_name == "Enterprise":
        extra_opts = plan.get("additional_options", {})
        extra_msgs = extra_opts.get("extra_messages_per_additional_assistant", 0)
        extra_mins = extra_opts.get("extra_minutes_per_additional_assistant", 0)
        included_msgs += extra_msgs * (num_agents - 1)
        included_mins += extra_mins * (num_agents - 1)
        extra_messages_per_assistant = extra_msgs
        extra_minutes_per_assistant = extra_mins

    # Adjust if user wants "Just Messages" or "Just Minutes"
    # We'll convert leftover usage from one to the other, same approach as original code
    if communication_type == "Just Messages":
        # Convert included minutes to messages based on cost ratio
        cost_of_included_mins_zar = included_mins * final_min_cost_zar
        if final_msg_cost_zar > 0:
            extra_msgs_from_mins = int(cost_of_included_mins_zar / final_msg_cost_zar)
        else:
            extra_msgs_from_mins = 0
        included_msgs += extra_msgs_from_mins
        included_mins = 0

    elif communication_type == "Just Minutes":
        # Convert included messages to minutes
        cost_of_included_msgs_zar = included_msgs * final_msg_cost_zar
        if final_min_cost_zar > 0:
            extra_mins_from_msgs = int(cost_of_included_msgs_zar / final_min_cost_zar)
        else:
            extra_mins_from_msgs = 0
        included_mins += extra_mins_from_msgs
        included_msgs = 0

    # Base monthly cost for included usage
    cost_of_msgs_zar = included_msgs * final_msg_cost_zar
    cost_of_mins_zar = included_mins * final_min_cost_zar

    monthly_cost_zar = (
        base_fee_zar
        + cost_of_msgs_zar
        + cost_of_mins_zar
        + tech_support_zar
        + float_cost_zar
        + maintenance_cost_zar
    )
    
    # Overages
    base_included_messages = usage_limits[plan_name]["base_messages"]
    base_included_minutes = usage_limits[plan_name]["base_minutes"]
    extra_messages_used = max(0, usage["used_messages"] - base_included_messages)
    extra_minutes_used = max(0, usage["used_minutes"] - base_included_minutes)

    cost_per_extra_message = usage_limits[plan_name]["cost_per_additional_message"]
    cost_per_extra_minute = usage_limits[plan_name]["cost_per_additional_minute"]
    extra_msg_cost_zar = extra_messages_used * cost_per_extra_message
    extra_min_cost_zar = extra_minutes_used * cost_per_extra_minute
    
    monthly_cost_zar += (extra_msg_cost_zar + extra_min_cost_zar)

    # Add contingency
    monthly_cost_zar *= (1 + contingency_percent)

    total_setup_cost_zar = setup_fee_zar + setup_hours_cost_zar + setup_cost_assistants_zar

    # Currency conversion overhead if needed
    exchange_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        # 30% overhead + 15% extra
        final_factor = 1.3 * 1.15

    monthly_cost_converted = (monthly_cost_zar / exchange_rate) * final_factor
    total_setup_cost_converted = (total_setup_cost_zar / exchange_rate) * final_factor

    # Add-Ons
    whitelabel_fee_zar = plan["optional_addons"]["white_labeling"] if addons.get("white_labeling") else 0
    if pricing.get("whitelabel_waved", False) and whitelabel_fee_zar > 0:
        whitelabel_fee_zar = 0

    custom_voices_cost_zar = 0
    if addons.get("custom_voices", {}).get("enabled"):
        q = addons["custom_voices"]["quantity"]
        cost_per_voice_zar = addons["custom_voices"]["cost_per_voice"]
        custom_voices_cost_zar = q * cost_per_voice_zar

    additional_languages_cost_zar = 0
    if addons.get("additional_languages", {}).get("enabled"):
        q = addons["additional_languages"]["quantity"]
        cost_per_lang_zar = addons["additional_languages"]["cost_per_language"]
        additional_languages_cost_zar = q * cost_per_lang_zar

    additional_use_case_cost_zar = 0
    if plan_name == "Enterprise":
        base_included_agents = plan["limitations"].get("assistants", 1)
        add_use_case_fee_zar = plan.get("additional_options", {}).get("add_use_case_fee", 0)
        additional_agents_needed = max(num_agents - base_included_agents, 0)
        additional_use_case_cost_zar = additional_agents_needed * add_use_case_fee_zar

    total_monthly_addons_zar = (
        whitelabel_fee_zar
        + custom_voices_cost_zar
        + additional_languages_cost_zar
        + additional_use_case_cost_zar
    )

    total_monthly_cost_zar = monthly_cost_zar + total_monthly_addons_zar
    total_monthly_cost_converted = (total_monthly_cost_zar / exchange_rate) * final_factor

    # Overall total cost for an extended perspective
    overall_total_cost_zar = (total_monthly_cost_zar * 12) + total_setup_cost_zar
    overall_total_cost_converted = (overall_total_cost_zar / exchange_rate) * final_factor

    return {
        # Main ZAR figures
        "final_monthly_cost_zar": monthly_cost_zar,
        "total_monthly_cost_zar": total_monthly_cost_zar,
        "total_setup_cost_zar": total_setup_cost_zar,
        "overall_total_cost_zar": overall_total_cost_zar,

        # Converted / Display amounts
        "total_monthly_cost": total_monthly_cost_converted,
        "total_setup_cost": total_setup_cost_converted,
        "overall_total_cost": overall_total_cost_converted,

        # Included usage
        "included_msgs_after_conversion": included_msgs,
        "included_mins_after_conversion": included_mins,

        # Overage details
        "extra_messages_used": extra_messages_used,
        "extra_minutes_used": extra_minutes_used,
        "extra_msg_cost_zar": extra_msg_cost_zar,
        "extra_min_cost_zar": extra_min_cost_zar,

        # Agents usage
        "extra_msgs_per_assistant": extra_messages_per_assistant,
        "extra_mins_per_assistant": extra_minutes_per_assistant,

        # Addon costs in ZAR
        "whitelabel_fee_zar": whitelabel_fee_zar,
        "custom_voices_cost_zar": custom_voices_cost_zar,
        "additional_languages_cost_zar": additional_languages_cost_zar,
        "additional_use_case_cost_zar": additional_use_case_cost_zar,

        # Setup breakdown
        "setup_fee_zar": setup_fee_zar,
        "setup_cost_assistants_zar": setup_cost_assistants_zar,
        "setup_hours_cost_zar": setup_hours_cost_zar,
        
        # Hours info
        "setup_hours": setup_hours,
        "maintenance_hours": maintenance_hours,
        "maintenance_hourly_rate": maintenance_hourly_rate,
        "maintenance_cost_zar": maintenance_cost_zar
    }

def usage_exceeds_threshold(used_m, used_min, plan_m, plan_min):
    """Check if usage is ~90% or more of plan threshold."""
    return (used_m >= 0.9 * plan_m) or (used_min >= 0.9 * plan_min)

def assign_plan_based_on_inputs(messages_needed, minutes_needed, wants_own_crm, number_of_agents):
    """
    Logic to auto-assign a plan based on usage and CRM requirement.
    This is just a simplistic approach.
    """
    if number_of_agents > 1:
        return "Enterprise"

    if wants_own_crm:
        # Can't be Basic
        if usage_exceeds_threshold(messages_needed, minutes_needed, 10000, 500):
            if messages_needed > 10000 or minutes_needed > 500:
                return "Enterprise"
            else:
                return "Advanced"
        else:
            if messages_needed > 10000 or minutes_needed > 500:
                return "Enterprise"
            else:
                return "Advanced"
    else:
        # can be Basic
        if usage_exceeds_threshold(messages_needed, minutes_needed, 5000, 300):
            if usage_exceeds_threshold(messages_needed, minutes_needed, 10000, 500):
                return "Enterprise"
            else:
                if messages_needed > 10000 or minutes_needed > 500:
                    return "Enterprise"
                else:
                    return "Advanced"
        else:
            return "Basic"

def show_footer():
    """
    Minimal footer.  
    *Displays 'Excluding VAT' if currency is ZAR, else 'Including VAT' if international.*  
    """
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

# ======================================
# INIT
# ======================================
initialize_configs()
pricing = load_config(PRICING_FILE) or DEFAULT_PRICING
usage_limits = load_config(USAGE_LIMITS_FILE) or DEFAULT_USAGE_LIMITS
exchange_rates = load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES

# Streamlit Settings
st.set_page_config(page_title="askAYYI Cost Calculator", layout="wide")
apply_custom_css()

# ======================================
# TABS NAVIGATION
# ======================================
tabs = st.tabs([
    "Plan Assignment",
    "Client Calculator",
    "Call Centre Cost Calculation",
    "Main Dashboard",
    "Quotation",
    "Saved Configurations",
    "Admin Dashboard"
])

# ======================================
# PAGE: Plan Assignment
# ======================================
with tabs[0]:
    st.title("Plan Assignment")
    st.write("Use this section to estimate your usage, and we'll assign a recommended plan.")
    with st.expander("Guide & Explanation", expanded=True):
        st.write("""
            **Instructions**:
            1. Enter how many calls you have each month and the average duration.
            2. Enter how many messaging conversations per month, and the average messages per conversation.
            3. Specify the number of AI Agents (use cases).
            4. Indicate if you want to use your own CRM or askAYYI's CRM.
            5. Indicate if you want both messaging & voice, or just one option.
            
            We'll generate a **Reference Number** for you.  
            Use that reference in 'Saved Configurations' if you want to recall this setup later.
        """)

    with st.form("plan_assignment_form_new"):
        calls_per_month = st.number_input("Number of Calls per Month", min_value=0, value=500, step=100, format="%d")
        avg_call_duration = st.number_input("Average Call Duration (mins)", min_value=0.0, value=3.0, step=0.5)
        msg_conversations_per_month = st.number_input("Monthly Messaging Conversations", min_value=0, value=3000, step=500, format="%d")
        avg_msgs_per_convo = st.number_input("Avg. Messages/Conversation", min_value=1, value=5, step=1, format="%d")

        desired_agents = st.number_input("Number of AI Agents (Use Cases)", min_value=1, value=1, step=1, format="%d")
        crm_choice = st.radio(
            "CRM Preference",
            ["askAYYI CRM", "Your Own CRM"],
            help="Note: Basic plan cannot use 'Your Own CRM'."
        )
        communication_type = st.radio(
            "Communication Type",
            ["Both Messages & Voice", "Just Messages", "Just Minutes"],
            index=0
        )

        plan_assign_btn = st.form_submit_button("Recommend My Plan")

    if plan_assign_btn:
        total_minutes_needed = calls_per_month * avg_call_duration
        total_messages_needed = msg_conversations_per_month * avg_msgs_per_convo
        wants_own_crm = (crm_choice == "Your Own CRM")

        assigned_plan = assign_plan_based_on_inputs(
            total_messages_needed,
            total_minutes_needed,
            wants_own_crm,
            desired_agents
        )

        st.session_state["client_assigned_plan"] = assigned_plan
        st.session_state["estimated_messages"] = total_messages_needed
        st.session_state["estimated_minutes"] = total_minutes_needed
        st.session_state["client_desired_agents"] = desired_agents
        st.session_state["client_crm_choice"] = crm_choice
        st.session_state["client_communication_type"] = communication_type

        # Adjust if assigned plan is Basic or Advanced but user wants >1 agent
        if assigned_plan in ["Basic", "Advanced"] and desired_agents > 1:
            st.session_state["client_desired_agents"] = 1
            st.warning(f"'{assigned_plan}' supports only 1 AI Agent. Agents reset to 1 automatically.")

        if assigned_plan == "Basic" and wants_own_crm:
            st.warning("Basic plan cannot accommodate 'Your Own CRM'. Please confirm if this is acceptable.")

        st.success(f"**Recommended Plan:** {assigned_plan}")
        st.info(f"**Estimated Monthly Usage**: ~{int(total_messages_needed):,} messages, ~{int(total_minutes_needed):,} minutes.")

        # Generate and save config by random reference
        reference_id = "REF" + str(random.randint(100000, 999999))
        st.session_state["client_reference_id"] = reference_id

        # Build config data (excluding personal details)
        config_data = {
            "assigned_plan": assigned_plan,
            "estimated_messages": total_messages_needed,
            "estimated_minutes": total_minutes_needed,
            "desired_agents": st.session_state["client_desired_agents"],
            "crm_choice": st.session_state["client_crm_choice"],
            "communication_type": st.session_state["client_communication_type"]
        }
        save_client_config(reference_id, config_data)

        st.success(f"Your configuration has been saved! **Reference:** {reference_id}")

    show_footer()

# ======================================
# PAGE: Client Calculator
# ======================================
with tabs[1]:
    st.title("Client Calculator")
    st.write("Refine usage details and optional add-ons to get an approximate cost for your chosen plan.")

    ccol1, ccol2 = st.columns([1,3])
    with ccol1:
        if st.button("Refresh from Plan Assignment"):
            # Overwrite the usage fields from Plan Assignment
            st.session_state["temp_messages"] = st.session_state.get("estimated_messages", 0)
            st.session_state["temp_minutes"] = st.session_state.get("estimated_minutes", 0)
            # Force a page reload
            rerun_script()

    # Let the user pick currency (or remove ZAR if 'international_mode' is True)
    currency_options = SUPPORTED_CURRENCIES.copy()
    if pricing.get("international_mode", False) and "ZAR" in currency_options:
        currency_options.remove("ZAR")

    if "selected_currency" not in st.session_state:
        if (not pricing.get("international_mode", False)) and "ZAR" in currency_options:
            st.session_state["selected_currency"] = "ZAR"
        else:
            st.session_state["selected_currency"] = currency_options[0] if currency_options else "USD"

    currency = st.selectbox(
        "Choose Currency (for reference)",
        options=currency_options,
        index=currency_options.index(st.session_state["selected_currency"])
               if st.session_state["selected_currency"] in currency_options else 0,
        help="Select the currency for cost references."
    )
    st.session_state["selected_currency"] = currency

    assigned_plan = st.session_state.get("client_assigned_plan", "Basic")
    comm_type = st.session_state.get("client_communication_type", "Both Messages & Voice")
    st.info(f"**Current Plan:** {assigned_plan} | **Communication:** {comm_type}")

    st.session_state.setdefault("temp_messages", st.session_state.get("estimated_messages", 4000))
    st.session_state.setdefault("temp_minutes", st.session_state.get("estimated_minutes", 200))
    st.session_state.setdefault("temp_addons_whitelabel", False)
    st.session_state.setdefault("temp_addons_cv_enabled", False)
    st.session_state.setdefault("temp_addons_cv_qty", 0)
    st.session_state.setdefault("temp_addons_lang_enabled", False)
    st.session_state.setdefault("temp_addons_lang_qty", 0)

    with st.form("client_calc_form"):
        st.subheader("Confirm Your Usage")
        default_agents = st.session_state.get("client_desired_agents", 1)
        st.write(f"**AI Agents (Use Cases)**: {default_agents}")

        used_messages = st.number_input(
            "Total Monthly Messages",
            min_value=0,
            value=int(st.session_state["temp_messages"]),
            step=500,
            format="%d"
        )
        used_minutes = st.number_input(
            "Total Monthly Voice Minutes",
            min_value=0,
            value=int(st.session_state["temp_minutes"]),
            step=50,
            format="%d"
        )
        chosen_crm = st.session_state.get("client_crm_choice", "askAYYI CRM")
        st.write(f"**CRM Chosen**: {chosen_crm}")

        st.subheader("Optional Add-Ons")
        white_labeling = st.checkbox(
            "White Labeling?",
            value=st.session_state["temp_addons_whitelabel"]
        )
        custom_voices = st.checkbox(
            "Custom Voices?",
            value=st.session_state["temp_addons_cv_enabled"]
        )
        num_custom_voices = 0
        if custom_voices:
            num_custom_voices = st.number_input(
                "Quantity of Custom Voices",
                min_value=0,
                value=st.session_state["temp_addons_cv_qty"],
                step=1,
                format="%d"
            )

        additional_languages = st.checkbox(
            "Additional Languages?",
            value=st.session_state["temp_addons_lang_enabled"]
        )
        num_additional_languages = 0
        if additional_languages:
            num_additional_languages = st.number_input(
                "Quantity of Additional Languages",
                min_value=0,
                value=st.session_state["temp_addons_lang_qty"],
                step=1,
                format="%d"
            )

        payment_option = st.radio(
            "Payment Preference",
            [f"Pay Monthly", f"Pay Upfront ({MIN_PLAN_DURATION.get(assigned_plan, 3)} months)"],
            index=0
        )

        calc_btn = st.form_submit_button("Recalculate Costs")

    if calc_btn:
        st.session_state["client_desired_agents"] = default_agents
        st.session_state["client_whitelabeling"] = white_labeling
        st.session_state["client_custom_voices_enabled"] = custom_voices
        st.session_state["client_num_custom_voices"] = num_custom_voices
        st.session_state["client_additional_languages_enabled"] = additional_languages
        st.session_state["client_num_additional_languages"] = num_additional_languages
        st.session_state["client_payment_option"] = payment_option
        st.session_state["estimated_messages"] = used_messages
        st.session_state["estimated_minutes"] = used_minutes

        usage = {
            "used_messages": used_messages,
            "used_minutes": used_minutes
        }

        try:
            plan_data = pricing["plans"][assigned_plan]
        except KeyError:
            st.error(f"Plan '{assigned_plan}' not found in pricing configuration.")
            show_footer()
            st.stop()

        addons = {
            "white_labeling": white_labeling,
            "custom_voices": {
                "enabled": custom_voices,
                "quantity": num_custom_voices,
                "cost_per_voice": plan_data["optional_addons"]["custom_voices"].get("cost_per_voice", 0)
            },
            "additional_languages": {
                "enabled": additional_languages,
                "quantity": num_additional_languages,
                "cost_per_language": plan_data["optional_addons"]["additional_languages"].get("cost_per_language", 0)
            }
        }

        cost_details = calculate_plan_cost(
            plan_name=assigned_plan,
            num_agents=default_agents,
            usage=usage,
            addons=addons,
            exchange_rates=exchange_rates,
            selected_currency=currency,
            pricing=pricing,
            usage_limits=usage_limits,
            communication_type=comm_type
        )

        st.session_state["client_cost_details"] = cost_details
        st.session_state["client_selected_plan"] = assigned_plan

        st.success("Recalculation done. Cost details updated. Visit 'Main Dashboard' or 'Quotation' to see the final breakdown.")

    show_footer()

# ======================================
# PAGE: Call Centre Cost Calculation
# ======================================
with tabs[2]:
    st.title("Call Centre Cost Calculation")
    st.write("Enter your existing call centre costs to compare them with an AI-based approach.")
    
    # ---------------------------------------
    # QUICK-SET DEFAULTS FOR EACH SECTION A/B/C
    # We store your provided defaults in dictionaries for easy referencing.
    # ---------------------------------------
    # A. PERSONNEL DEFAULTS
    personnel_defaults = {
        "agents": {"avg": 10, "low": 10, "high": 10, "zero": 0},  # # of Agents is typically the same
        "salary": {"avg": 8823, "low": 6572, "high": 12920, "zero": 0},
        "pension_pct": {"avg": 7, "low": 7, "high": 7, "zero": 0},  # The % is the same, but to mimic "0" means no pension
        "medical": {"avg": 2000, "low": 1000, "high": 3000, "zero": 0},
        "bonus": {"avg": 1500, "low": 1000, "high": 2000, "zero": 0},  # annual
        "benefits": {"avg": 500, "low": 300, "high": 700, "zero": 0},
        "recruitment": {"avg": 3000, "low": 2000, "high": 4000, "zero": 0},
        "training": {"avg": 1000, "low": 800, "high": 1200, "zero": 0},
        "trainer_salary": {"avg": 25000, "low": 20000, "high": 30000, "zero": 0}
    }
    # B. TECHNOLOGY DEFAULTS
    tech_defaults = {
        "software": {"avg": 5000, "low": 3500, "high": 6500, "zero": 0},
        "licensing": {"avg": 500, "low": 400, "high": 600, "zero": 0},
        "crm_sub": {"avg": 1500, "low": 1200, "high": 1800, "zero": 0},
        "hardware_station": {"avg": 15000, "low": 12000, "high": 18000, "zero": 0},
        "depreciation_yrs": {"avg": 3, "low": 3, "high": 3, "zero": 1},  # can't do zero years
        "repair_device": {"avg": 800, "low": 600, "high": 1000, "zero": 0},
        "telco_bill": {"avg": 1000, "low": 800, "high": 1200, "zero": 0},
        "call_cost_min": {"avg": 0.75, "low": 0.60, "high": 0.90, "zero": 0},
        "internet": {"avg": 8000, "low": 6000, "high": 10000, "zero": 0}
    }
    # C. FACILITY DEFAULTS
    facility_defaults = {
        "office_rent": {"avg": 7500, "low": 5000, "high": 10900, "zero": 0},  # e.g. 218*50=10900 for high
        "electricity": {"avg": 6000, "low": 4500, "high": 7500, "zero": 0},
        "water": {"avg": 2000, "low": 2000, "high": 2000, "zero": 0}  # only one stated default
    }

    # Helper function to quickly set values
    def set_personnel_defaults(choice):
        st.session_state["callcentre_staff_count"] = personnel_defaults["agents"][choice]
        st.session_state["callcentre_salary_per_agent"] = personnel_defaults["salary"][choice]
        st.session_state["callcentre_pension_percent"] = personnel_defaults["pension_pct"][choice]
        st.session_state["callcentre_medical_aid_per_agent"] = personnel_defaults["medical"][choice]
        st.session_state["callcentre_bonus_per_agent"] = personnel_defaults["bonus"][choice]
        st.session_state["callcentre_benefits_per_agent"] = personnel_defaults["benefits"][choice]
        st.session_state["callcentre_recruitment_per_agent"] = personnel_defaults["recruitment"][choice]
        st.session_state["callcentre_training_per_agent"] = personnel_defaults["training"][choice]
        st.session_state["callcentre_trainer_salary"] = personnel_defaults["trainer_salary"][choice]

    def set_tech_defaults(choice):
        st.session_state["callcentre_callcenter_software"] = tech_defaults["software"][choice]
        st.session_state["callcentre_licensing_per_user"] = tech_defaults["licensing"][choice]
        st.session_state["callcentre_crm_sub_per_user"] = tech_defaults["crm_sub"][choice]
        st.session_state["callcentre_hardware_cost_station"] = tech_defaults["hardware_station"][choice]
        st.session_state["callcentre_depreciation_years"] = tech_defaults["depreciation_yrs"][choice]
        st.session_state["callcentre_repair_per_device"] = tech_defaults["repair_device"][choice]
        st.session_state["callcentre_phone_bill_per_agent"] = tech_defaults["telco_bill"][choice]
        st.session_state["callcentre_call_cost_per_minute"] = tech_defaults["call_cost_min"][choice]
        st.session_state["callcentre_internet_services"] = tech_defaults["internet"][choice]

    def set_facility_defaults(choice):
        st.session_state["callcentre_office_rent_month"] = facility_defaults["office_rent"][choice]
        st.session_state["callcentre_electricity_cost_month"] = facility_defaults["electricity"][choice]
        st.session_state["callcentre_water_cost_month"] = facility_defaults["water"][choice]

    # -----------
    # SECTION A
    # -----------
    st.markdown("### A. Personnel Costs")
    # Add quick-set buttons
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    if bcol1.button("Set to 0 (A)"):
        set_personnel_defaults("zero")
        rerun_script()
    if bcol2.button("Low Cost (A)"):
        set_personnel_defaults("low")
        rerun_script()
    if bcol3.button("High Cost (A)"):
        set_personnel_defaults("high")
        rerun_script()
    if bcol4.button("Average Cost (A)"):
        set_personnel_defaults("avg")
        rerun_script()

    c1, c2, c3 = st.columns(3)
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
        staff_count = st.number_input("Number of Agents", min_value=0, value=default_staff_count, step=1, format="%d")
        salary_per_agent = st.number_input("Salary/Agent (ZAR)", min_value=0, value=default_salary_per_agent, step=500)
        pension_percent = st.number_input("Pension (%)", min_value=0, max_value=100, value=default_pension_percent, step=1)
    with c2:
        medical_aid_per_agent = st.number_input("Medical Aid/Agent (ZAR)", min_value=0, value=default_medical_aid_per_agent, step=500)
        bonus_incentive_per_agent = st.number_input("Bonus/Agent (ZAR Ann.)", min_value=0, value=default_bonus_per_agent, step=500)
        monthly_benefits_per_agent = st.number_input("Other Benefits/Agent (ZAR)", min_value=0, value=default_benefits_per_agent, step=100)
    with c3:
        recruitment_cost_per_agent = st.number_input("Recruitment/Agent (ZAR)", min_value=0, value=default_recruitment_per_agent, step=500)
        training_cost_per_agent = st.number_input("Training/Agent (ZAR)", min_value=0, value=default_training_per_agent, step=500)
        trainer_salary = st.number_input("Trainer Salary (ZAR/mo)", min_value=0, value=default_trainer_salary, step=500)

    # -----------
    # SECTION B
    # -----------
    st.markdown("### B. Technology Costs")
    # Add quick-set buttons
    tbcol1, tbcol2, tbcol3, tbcol4 = st.columns(4)
    if tbcol1.button("Set to 0 (B)"):
        set_tech_defaults("zero")
        rerun_script()
    if tbcol2.button("Low Cost (B)"):
        set_tech_defaults("low")
        rerun_script()
    if tbcol3.button("High Cost (B)"):
        set_tech_defaults("high")
        rerun_script()
    if tbcol4.button("Average Cost (B)"):
        set_tech_defaults("avg")
        rerun_script()

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

    # -----------
    # SECTION C
    # -----------
    st.markdown("### C. Facility Costs")
    fc_b1, fc_b2, fc_b3, fc_b4 = st.columns(4)
    if fc_b1.button("Set to 0 (C)"):
        set_facility_defaults("zero")
        rerun_script()
    if fc_b2.button("Low Cost (C)"):
        set_facility_defaults("low")
        rerun_script()
    if fc_b3.button("High Cost (C)"):
        set_facility_defaults("high")
        rerun_script()
    if fc_b4.button("Average Cost (C)"):
        set_facility_defaults("avg")
        rerun_script()

    fc1, fc2, fc3 = st.columns(3)

    default_office_rent_month = st.session_state.get("callcentre_office_rent_month", 7500)
    default_electricity_cost_month = st.session_state.get("callcentre_electricity_cost_month", 6000)
    default_water_cost_month = st.session_state.get("callcentre_water_cost_month", 2000)

    with fc1:
        office_rent_month = st.number_input("Office Rent (ZAR/mo)", min_value=0, value=default_office_rent_month, step=1000)
        electricity_cost_month = st.number_input("Electricity (ZAR/mo)", min_value=0, value=default_electricity_cost_month, step=500)
        water_cost_month = st.number_input("Water (ZAR/mo)", min_value=0, value=default_water_cost_month, step=500)

    # Additional fields not specified in your default list:
    fc2, fc3 = st.columns(2)
    default_hvac_cost_month = st.session_state.get("callcentre_hvac_cost_month", 3000)
    default_stationery_month = st.session_state.get("callcentre_stationery_month", 1000)
    default_cleaning_services_month = st.session_state.get("callcentre_cleaning_services_month", 3000)
    default_office_repairs_annual = st.session_state.get("callcentre_office_repairs_annual", 8000)

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
        engagement_events_annual = st.number_input("Engagement Events (ZAR/yr)", min_value=0, value=default_engagement_events_annual, step=1000)
    with mc2:
        liability_insurance_annual = st.number_input("Liability Insurance (ZAR/yr)", min_value=0, value=default_liability_insurance_annual, step=2000)
        equipment_insurance_percent = st.number_input("Equipment Insurance (%)", min_value=0, max_value=100, value=default_equipment_insurance_percent, step=1)

    callcentre_calc_btn = st.button("Calculate Internal Call Centre Costs")

    if callcentre_calc_btn:
        # Store these in session_state so we can compare in the Main Dashboard
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

        # Simple monthly approximation in ZAR
        monthly_salary_total = staff_count * salary_per_agent
        monthly_pension_total = monthly_salary_total * (pension_percent / 100)
        monthly_medical_total = staff_count * medical_aid_per_agent

        # Bonus is annual, so monthly portion:
        monthly_bonus_total = (staff_count * bonus_incentive_per_agent) / 12.0
        monthly_benefits_total = staff_count * monthly_benefits_per_agent

        total_recruitment = staff_count * recruitment_cost_per_agent  # once-off
        total_training = staff_count * training_cost_per_agent        # once-off

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

        # Convert to selected currency
        selected_currency = st.session_state.get("selected_currency", "ZAR")
        ex_rate = exchange_rates.get(selected_currency, 1.0)
        if selected_currency == "ZAR":
            final_factor = 1.0
        else:
            final_factor = 1.3 * 1.15

        st.session_state["cc_monthly_total_callcentre_zar"] = monthly_total_callcentre_zar
        st.session_state["cc_once_off_costs_callcentre_zar"] = once_off_costs_callcentre_zar
        st.session_state["cc_monthly_total_callcentre"] = (monthly_total_callcentre_zar / ex_rate) * final_factor
        st.session_state["cc_once_off_costs_callcentre"] = (once_off_costs_callcentre_zar / ex_rate) * final_factor

        st.success("Comparison data calculated. Visit 'Main Dashboard' or 'Quotation' to see results.")

    show_footer()

# ======================================
# PAGE: Main Dashboard
# ======================================
with tabs[3]:
    st.title("Main Dashboard")

    cost_details = st.session_state.get("client_cost_details", None)
    if cost_details is None:
        st.warning("Use 'Plan Assignment' and 'Client Calculator' first to generate usage & cost info.")
        show_footer()
        st.stop()

    assigned_plan = st.session_state.get("client_selected_plan", "Basic")
    plan_min_duration = MIN_PLAN_DURATION.get(assigned_plan, 3)
    comm_type = st.session_state.get("client_communication_type", "Both Messages & Voice")
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    symbol = CURRENCY_SYMBOLS.get(selected_currency, "R")

    # Grab unrounded calculations
    total_monthly_cost_converted = cost_details["total_monthly_cost"]
    total_setup_cost_converted = cost_details["total_setup_cost"]
    included_msgs = cost_details["included_msgs_after_conversion"]
    included_mins = cost_details["included_mins_after_conversion"]
    extra_messages_used = cost_details["extra_messages_used"]
    extra_minutes_used = cost_details["extra_minutes_used"]

    # Overages in chosen currency
    ex_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        final_factor = 1.3 * 1.15
    extra_msg_cost_converted = (cost_details["extra_msg_cost_zar"] / ex_rate) * final_factor
    extra_min_cost_converted = (cost_details["extra_min_cost_zar"] / ex_rate) * final_factor

    # Round for display
    disp_monthly_cost = math.ceil(total_monthly_cost_converted)
    disp_setup_cost = math.ceil(total_setup_cost_converted)
    plan_duration_total = math.ceil(total_monthly_cost_converted * plan_min_duration + total_setup_cost_converted)
    disp_extra_msg_cost = math.ceil(extra_msg_cost_converted)
    disp_extra_min_cost = math.ceil(extra_min_cost_converted)

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.markdown(f"""
        <div class='card' style='height: 130px;'>
            <h4>Plan</h4>
            <p>{assigned_plan}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class='card' style='height: 130px;'>
            <h4>Monthly Cost</h4>
            <p>{symbol}{disp_monthly_cost:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown(f"""
        <div class='card' style='height: 130px;'>
            <h4>Setup Cost</h4>
            <p>{symbol}{disp_setup_cost:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_d:
        st.markdown(f"""
        <div class='card' style='height: 130px;'>
            <h4>Commit. Cost</h4>
            <p>{symbol}{plan_duration_total:,} over {plan_min_duration} months</p>
        </div>
        """, unsafe_allow_html=True)

    st.write(f"### Plan Duration: {plan_min_duration} months minimum")
    st.write(f"### Communication Type: {comm_type}")
    st.write(f"### Included Messages: {included_msgs:,}")
    st.write(f"### Included Minutes: {included_mins:,}")

    st.write("---")
    st.subheader("Maintenance & Setup Breakdown")

    # Convert the maintenance & setup items to chosen currency
    maintenance_cost_converted = (cost_details["maintenance_cost_zar"] / ex_rate) * final_factor
    setup_fee_converted = (cost_details["setup_fee_zar"] / ex_rate) * final_factor
    setup_hours_converted = (cost_details["setup_hours_cost_zar"] / ex_rate) * final_factor
    setup_cost_assistants_converted = (cost_details["setup_cost_assistants_zar"] / ex_rate) * final_factor

    df_data = [
        [
            "Maintenance Hours (Monthly)",
            f"{cost_details['maintenance_hours']} hrs @ {symbol}{math.ceil((cost_details['maintenance_hourly_rate']/ex_rate)*final_factor):,}/hr"
        ],
        [
            "Maintenance Cost (Monthly)",
            f"{symbol}{math.ceil(maintenance_cost_converted):,}"
        ],
        [
            "Plan's Base Setup Fee (One-Time)",
            f"{symbol}{math.ceil(setup_fee_converted):,}"
        ],
    ]

    # Safely check for setup_hours  
    if cost_details.get("setup_hours", 0) > 0:
        df_data.append([
            "Setup Hours (One-Time)",
            f"{symbol}{math.ceil(setup_hours_converted):,}"
        ])
    # If there's any extra assistant setup
    if cost_details["setup_cost_assistants_zar"] > 0:
        df_data.append([
            "Setup Cost for Assistants",
            f"{symbol}{math.ceil(setup_cost_assistants_converted):,}"
        ])

    df_breakdown = pd.DataFrame(df_data, columns=["Item", "Value"])
    st.table(df_breakdown)

    # Overages
    if extra_messages_used > 0 or extra_minutes_used > 0:
        st.write("---")
        st.subheader("Overage Charges")
        st.write(f"- **Extra Messages Used**: {extra_messages_used:,} => {symbol}{disp_extra_msg_cost:,}")
        st.write(f"- **Extra Minutes Used**: {extra_minutes_used:,} => {symbol}{disp_extra_min_cost:,}")

    # Compare with call centre cost
    monthly_total_callcentre_zar = st.session_state.get("cc_monthly_total_callcentre_zar", None)
    once_off_callcentre_zar = st.session_state.get("cc_once_off_costs_callcentre_zar", None)
    if monthly_total_callcentre_zar is not None:
        st.write("---")
        st.subheader("Comparison with Existing Call Centre")
        monthly_total_callcentre_converted = st.session_state.get("cc_monthly_total_callcentre", 0)
        once_off_callcentre_converted = st.session_state.get("cc_once_off_costs_callcentre", 0)
        disp_callcentre_cost = math.ceil(monthly_total_callcentre_converted)
        disp_callcentre_onceoff = math.ceil(once_off_callcentre_converted)

        st.write(f"**Your Current Call Centre** ~ {symbol}{disp_callcentre_cost:,}/mo")
        st.write(f"One-Time Onboarding & Recruitment: {symbol}{disp_callcentre_onceoff:,}")
        st.write(f"**askAYYI**: {symbol}{disp_monthly_cost:,}/mo + {symbol}{disp_setup_cost:,} once-off")

        difference = monthly_total_callcentre_converted - total_monthly_cost_converted
        diff_rounded = math.ceil(abs(difference))
        if difference > 0:
            st.success(f"**Potential Monthly Savings**: ~{symbol}{diff_rounded:,}")
        else:
            st.warning(f"askAYYI is higher by ~{symbol}{diff_rounded:,} per month.")
    else:
        st.info("No Call Centre cost data provided. Fill 'Call Centre Cost Calculation' if you want a comparison.")

    show_footer()

# ======================================
# PAGE: Quotation (Client-Facing)
# ======================================
with tabs[4]:
    st.title("Quotation")

    cost_details = st.session_state.get("client_cost_details", None)
    if cost_details is None:
        st.warning("Use 'Plan Assignment' + 'Client Calculator' first for a quote.")
        show_footer()
        st.stop()

    assigned_plan = st.session_state.get("client_selected_plan", "Basic")
    plan_min_duration = MIN_PLAN_DURATION.get(assigned_plan, 3)
    comm_type = st.session_state.get("client_communication_type", "Both Messages & Voice")
    selected_currency = st.session_state.get("selected_currency", "ZAR")
    symbol = CURRENCY_SYMBOLS.get(selected_currency, "R")

    # Unrounded in selected currency
    monthly_cost_conv = cost_details["total_monthly_cost"]
    setup_cost_conv = cost_details["total_setup_cost"]
    plan_duration_total_conv = (monthly_cost_conv * plan_min_duration) + setup_cost_conv
    included_msgs = cost_details["included_msgs_after_conversion"]
    included_mins = cost_details["included_mins_after_conversion"]

    # Round for display
    disp_monthly_cost = math.ceil(monthly_cost_conv)
    disp_setup_cost = math.ceil(setup_cost_conv)
    disp_plan_duration_cost = math.ceil(plan_duration_total_conv)

    extra_msgs_per_assistant = cost_details.get("extra_msgs_per_assistant", 0)
    extra_mins_per_assistant = cost_details.get("extra_mins_per_assistant", 0)
    num_agents = st.session_state.get("client_desired_agents", 1)
    additional_agents = max(num_agents - 1, 0)

    # Additional agent cost (Enterprise)
    add_use_case_zar = cost_details.get("additional_use_case_cost_zar", 0)
    ex_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        final_factor = 1.3 * 1.15
    add_use_case_conv = (add_use_case_zar / ex_rate) * final_factor
    disp_add_use_case_conv = math.ceil(add_use_case_conv)

    # Overages
    extra_messages_used = cost_details["extra_messages_used"]
    extra_minutes_used = cost_details["extra_minutes_used"]
    extra_msg_cost_zar = cost_details["extra_msg_cost_zar"]
    extra_min_cost_zar = cost_details["extra_min_cost_zar"]
    extra_msg_cost_conv = (extra_msg_cost_zar / ex_rate) * final_factor
    extra_min_cost_conv = (extra_min_cost_zar / ex_rate) * final_factor
    disp_extra_msg_cost = math.ceil(extra_msg_cost_conv)
    disp_extra_min_cost = math.ceil(extra_min_cost_conv)

    st.markdown(f"""
    <div class="steve-jobs-style">
    <p>Hello <span class="highlight">Client</span>,</p>
    <p>We appreciate your interest in askAYYI. Below is a simple breakdown of your monthly and once-off costs.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h4>Monthly Cost</h4>
        <p style="font-size:1.2em;">
            {symbol}{disp_monthly_cost:,}
            <br/><span style="font-size:0.85em;">
            (Includes messages, minutes, and {cost_details['maintenance_hours']} monthly maintenance hrs)
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h4>One-Time Setup</h4>
        <p style="font-size:1.2em;">
            {symbol}{disp_setup_cost:,}
            <br/><span style="font-size:0.85em;">
            (Covers necessary setup & on-boarding)
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Additional Assistants display (only if the user actually has more than 1)
    if additional_agents > 0:
        st.markdown(f"""
        <div class="card">
            <h4>Additional Assistant(s)</h4>
            <p style="font-size:1.2em;">
                {additional_agents} total<br/>
                +{extra_msgs_per_assistant * additional_agents} msgs & +{extra_mins_per_assistant * additional_agents} mins<br/>
        """, unsafe_allow_html=True)
        # If the plan charges a monthly extra use-case fee:
        if disp_add_use_case_conv > 0:
            st.markdown(f"""
                <strong>Monthly Add-On: {symbol}{disp_add_use_case_conv:,}</strong>
            """, unsafe_allow_html=True)
        st.markdown("</p></div>", unsafe_allow_html=True)

    # Overages (show only if they exist)
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
            {symbol}{disp_plan_duration_cost:,} <br/>
            Over {plan_min_duration} months + Setup
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="steve-jobs-style">
    <p>Each month, you'll have ~<span class="highlight">{included_msgs:,}</span> messages 
    and <span class="highlight">{included_mins:,}</span> minutes included.</p>
    </div>
    """, unsafe_allow_html=True)

    st.success("Quotation is ready! Thank you for choosing askAYYI.")
    show_footer()

# ======================================
# PAGE: Saved Configurations
# ======================================
with tabs[5]:
    if not authenticate_admin():
        st.stop()

    st.title("Saved Client Configurations by Reference")
    st.write("Enter or select a reference to load previous settings.")

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
        st.session_state["client_desired_agents"] = config_data.get("desired_agents", 1)
        st.session_state["client_crm_choice"] = config_data.get("crm_choice", "askAYYI CRM")
        st.session_state["client_communication_type"] = config_data.get("communication_type", "Both Messages & Voice")

        if "cost_details" in config_data:
            st.session_state["client_cost_details"] = config_data["cost_details"]
            st.session_state["client_selected_plan"] = config_data.get("assigned_plan")
        st.success(f"Configuration for reference {selected_ref} loaded.")
        st.info("Go to Main Dashboard / Quotation to view details.")

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
            "desired_agents": st.session_state.get("client_desired_agents", 1),
            "crm_choice": st.session_state.get("client_crm_choice", "askAYYI CRM"),
            "communication_type": st.session_state.get("client_communication_type", "Both Messages & Voice"),
            "cost_details": st.session_state.get("client_cost_details", {})
        }
        save_client_config(new_ref_to_save, config_data)
        st.success(f"Configuration saved under reference {new_ref_to_save}!")

    show_footer()

# ======================================
# PAGE: Admin Dashboard
# ======================================
with tabs[6]:
    # Force admin password check FIRST
    if not authenticate_admin():
        st.stop()

    st.title("Admin Dashboard")
    st.write("This section is **internal** and shows advanced configuration & profit details.")
    st.markdown("---")

    # -- GLOBAL SETTINGS --
    st.subheader("Global Settings")

    col_int1, col_int2 = st.columns([2,2])
    with col_int1:
        st.write("**International Mode**")
        if pricing.get("international_mode", False):
            st.success("International Mode: **ON**")
            if st.button("Disable International Mode"):
                pricing["international_mode"] = False
                save_config(PRICING_FILE, pricing)
                st.success("International mode disabled.")
        else:
            st.warning("International Mode: OFF")
            if st.button("Enable International Mode"):
                pricing["international_mode"] = True
                save_config(PRICING_FILE, pricing)
                st.success("International mode enabled.")

    with col_int2:
        st.write("**Whitelabel Fee Waiver**")
        if pricing.get("whitelabel_waved", False):
            st.success("Whitelabel is currently WAIVED (no cost).")
            if st.button("Stop Waving Whitelabel"):
                pricing["whitelabel_waved"] = False
                save_config(PRICING_FILE, pricing)
                st.success("Whitelabel waving turned OFF.")
        else:
            st.warning("Whitelabel is NOT waived. Clients pay if selected.")
            if st.button("Wave Whitelabel Fee"):
                pricing["whitelabel_waved"] = True
                save_config(PRICING_FILE, pricing)
                st.success("Whitelabel fee is now waived.")

    st.markdown("---")

    # DISCOUNTS
    st.subheader("Discounts Configuration (Hidden from Clients)")
    cdisc1, cdisc2 = st.columns([2,2])
    with cdisc1:
        if pricing.get("discounts_enabled", True):
            st.success("Discounts: ENABLED (internal only)")
            if st.button("Disable Discounts"):
                pricing["discounts_enabled"] = False
                save_config(PRICING_FILE, pricing)
                st.success("Discounts disabled.")
        else:
            st.warning("Discounts: DISABLED")
            if st.button("Enable Discounts"):
                pricing["discounts_enabled"] = True
                save_config(PRICING_FILE, pricing)
                st.success("Discounts enabled.")

    with cdisc2:
        current_global_discount = pricing.get("global_discount_rate", 0)
        new_global_discount = st.number_input(
            "Global discount for upfront (%)",
            value=float(current_global_discount),
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )
        if st.button("Update Global Discount"):
            pricing["global_discount_rate"] = new_global_discount
            save_config(PRICING_FILE, pricing)
            st.success(f"Global discount is now {new_global_discount}%")

    st.markdown("---")

    # EXCHANGE RATES
    st.subheader("Exchange Rates")
    with st.form("exchange_rates_form"):
        exchange_rate_inputs = {}
        for currency_ in SUPPORTED_CURRENCIES:
            if currency_ == "ZAR":
                continue
            # Ensure existing is float
            current_rate = float(exchange_rates.get(currency_, DEFAULT_EXCHANGE_RATES.get(currency_, 1.0)))
            exchange_rate_inputs[currency_] = st.number_input(
                f"1 {currency_} = X ZAR",
                value=current_rate,
                step=0.001
            )
        save_exchange_rates_btn = st.form_submit_button("Save Exchange Rates")
        if save_exchange_rates_btn:
            for ccy, rate in exchange_rate_inputs.items():
                exchange_rates[ccy] = rate
            save_config(EXCHANGE_RATES_FILE, exchange_rates)
            st.success("Exchange rates updated.")

    st.markdown("---")

    # -- PLAN CONFIGURATIONS --
    st.header("Plan Configurations")
    plan_options = list(pricing["plans"].keys())
    selected_plan = st.selectbox("Select Plan to Edit", options=plan_options)

    plan_details = pricing["plans"][selected_plan]

    st.markdown(f"### {selected_plan} - Basic Parameters")
    colp1, colp2, colp3 = st.columns(3)
    with colp1:
        new_setup_fee = st.number_input("Setup Fee (ZAR)", value=plan_details.get("setup_fee", 0), step=1000)
        new_base_fee = st.number_input("Base Fee (ZAR)", value=plan_details.get("base_fee", 0), step=1000)
    with colp2:
        new_incl_msgs = st.number_input("Included Messages", value=plan_details.get("messages", 0), step=1000)
        new_incl_mins = st.number_input("Included Minutes", value=plan_details.get("voice_minutes", 0), step=100)
    with colp3:
        new_maintenance_hours = st.number_input("Maintenance Hours (Mo.)", value=plan_details.get("maintenance_hours", 0), step=1)
        new_maintenance_rate = st.number_input("Maintenance Rate (ZAR/hr)", value=plan_details.get("maintenance_hourly_rate", 0), step=50)

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

    st.markdown("### Setup & Technical Support")
    colp7, colp8 = st.columns(2)
    with colp7:
        new_setup_hours = st.number_input("Setup Hours", value=plan_details.get("setup_hours", 0), step=1)
        new_setup_hourly_rate = st.number_input("Setup Hourly Rate (ZAR)", value=plan_details.get("setup_hourly_rate", 0), step=50)
    with colp8:
        new_tech_support = st.number_input("Technical Support (ZAR)", value=plan_details.get("technical_support_cost", 0), step=500)
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
        white_labeling_cost = plan_details["optional_addons"].get("white_labeling", 0)
        new_white_label = st.number_input("Whitelabel Fee (ZAR)", value=white_labeling_cost, step=1000)
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
        cex1, cex2, cex3 = st.columns(3)
        with cex1:
            new_extra_msgs = st.number_input("Extra Msgs/Addl Agent", value=eopts.get("extra_messages_per_additional_assistant", 0), step=100)
        with cex2:
            new_extra_mins = st.number_input("Extra Mins/Addl Agent", value=eopts.get("extra_minutes_per_additional_assistant", 0), step=50)
        with cex3:
            new_use_case_fee = st.number_input("Cost/Additional AI Agent (Monthly)", value=eopts.get("add_use_case_fee", 0), step=1000)

        new_setup_cost_per_assistant = st.number_input(
            "Setup Cost/Assistant (ZAR)",
            value=plan_details.get("setup_cost_per_assistant", 7800),
            step=500
        )
    else:
        new_extra_msgs = 0
        new_extra_mins = 0
        new_use_case_fee = 0
        new_setup_cost_per_assistant = plan_details.get("setup_cost_per_assistant", 7800)

    if st.button("Save Plan Configuration"):
        p = pricing["plans"][selected_plan]
        p["setup_fee"] = new_setup_fee
        p["base_fee"] = new_base_fee
        p["messages"] = new_incl_msgs
        p["voice_minutes"] = new_incl_mins
        p["maintenance_hours"] = new_maintenance_hours
        p["maintenance_hourly_rate"] = new_maintenance_rate

        p["base_msg_cost"] = new_base_msg_cost
        p["msg_markup"] = new_msg_markup
        p["base_min_cost"] = new_base_min_cost
        p["min_markup"] = new_min_markup
        p["contingency_percent"] = new_contingency
        p["float_cost"] = new_float_cost

        p["setup_hours"] = new_setup_hours
        p["setup_hourly_rate"] = new_setup_hourly_rate
        p["technical_support_cost"] = new_tech_support
        p["crm_access"] = new_crm_access

        p["platforms"] = new_platforms
        p["onboarding_support_hours"] = new_onboarding_hrs
        if "limitations" not in p:
            p["limitations"] = {}
        p["limitations"]["use_cases"] = new_use_cases
        p["limitations"]["assistants"] = new_use_cases

        p["optional_addons"]["white_labeling"] = new_white_label
        p["optional_addons"]["custom_voices"]["enabled"] = new_cvoices_enabled
        p["optional_addons"]["custom_voices"]["cost_per_voice"] = new_cvoices_rate
        p["optional_addons"]["additional_languages"]["enabled"] = new_al_enabled
        p["optional_addons"]["additional_languages"]["cost_per_language"] = new_al_cost

        if selected_plan == "Enterprise":
            if "additional_options" not in p:
                p["additional_options"] = {}
            p["additional_options"]["extra_messages_per_additional_assistant"] = new_extra_msgs
            p["additional_options"]["extra_minutes_per_additional_assistant"] = new_extra_mins
            p["additional_options"]["add_use_case_fee"] = new_use_case_fee
            p["setup_cost_per_assistant"] = new_setup_cost_per_assistant

        save_config(PRICING_FILE, pricing)
        st.success(f"Settings for {selected_plan} saved successfully!")

    st.markdown("---")

    # ======================
    # LLM & Voice Cost Configuration
    # ======================
    st.subheader("LLM & Voice Cost Configuration (in USD)")

    # Ensure placeholders in session_state
    st.session_state.setdefault("llm_cost_input_per_million", 0.0)
    st.session_state.setdefault("llm_cost_output_per_million", 0.0)
    st.session_state.setdefault("llm_avg_tokens_per_message", 750.0)
    st.session_state.setdefault("llm_models_used", {
        "perplexity": False,
        "gpt4o-mini": False,
        "gpt4o": False,
        "llama": False,
        "other": False
    })
    st.session_state.setdefault("voice_cost_twilio", 0.0)
    st.session_state.setdefault("voice_cost_fixed", 0.0)
    st.session_state.setdefault("voice_cost_transcriber", 0.0)
    st.session_state.setdefault("voice_cost_model", 0.0)
    st.session_state.setdefault("voice_cost_elevenlabs", 0.0)
    st.session_state.setdefault("voice_cost_other", 0.0)

    # --- LLM Config ---
    with st.expander("Configure LLM Usage Cost", expanded=False):
        st.write("**LLM Token Costs** (cost per 1M tokens)")
        llm_cost_input = st.number_input(
            "Cost per million input tokens ($)",
            value=float(st.session_state["llm_cost_input_per_million"]),
            step=0.001
        )
        llm_cost_output = st.number_input(
            "Cost per million output tokens ($)",
            value=float(st.session_state["llm_cost_output_per_million"]),
            step=0.001
        )
        avg_tokens = st.number_input(
            "Average tokens used per message",
            value=float(st.session_state["llm_avg_tokens_per_message"]),
            step=50.0
        )

        st.write("**Models** - Check all that apply:")
        col_models_1, col_models_2 = st.columns([1,1])
        with col_models_1:
            perplexity_check = st.checkbox("Perplexity", value=st.session_state["llm_models_used"]["perplexity"])
            gpt4o_mini_check = st.checkbox("gpt4o-mini", value=st.session_state["llm_models_used"]["gpt4o-mini"])
            gpt4o_check = st.checkbox("gpt4o", value=st.session_state["llm_models_used"]["gpt4o"])
        with col_models_2:
            llama_check = st.checkbox("llama", value=st.session_state["llm_models_used"]["llama"])
            other_check = st.checkbox("other LLM", value=st.session_state["llm_models_used"]["other"])

        if st.button("Save LLM Costs"):
            st.session_state["llm_cost_input_per_million"] = llm_cost_input
            st.session_state["llm_cost_output_per_million"] = llm_cost_output
            st.session_state["llm_avg_tokens_per_message"] = avg_tokens
            st.session_state["llm_models_used"] = {
                "perplexity": perplexity_check,
                "gpt4o-mini": gpt4o_mini_check,
                "gpt4o": gpt4o_check,
                "llama": llama_check,
                "other": other_check
            }
            st.success("LLM token cost configuration saved. All new calculations will include it automatically.")

    # --- Voice Config ---
    with st.expander("Configure Voice Minutes Cost", expanded=False):
        voice_twilio = st.number_input("Twilio Cost ($/min)", value=float(st.session_state["voice_cost_twilio"]), step=0.001)
        voice_fixed = st.number_input("Fixed Cost ($/min)", value=float(st.session_state["voice_cost_fixed"]), step=0.001)
        voice_transcriber = st.number_input("Transcriber Cost ($/min)", value=float(st.session_state["voice_cost_transcriber"]), step=0.001)
        voice_model = st.number_input("Model Cost ($/min)", value=float(st.session_state["voice_cost_model"]), step=0.001)
        voice_elevenlabs = st.number_input("ElevenLabs Cost ($/min)", value=float(st.session_state["voice_cost_elevenlabs"]), step=0.001)
        voice_other = st.number_input("Other Voice Cost ($/min)", value=float(st.session_state["voice_cost_other"]), step=0.001)

        if st.button("Save Voice Costs"):
            st.session_state["voice_cost_twilio"] = voice_twilio
            st.session_state["voice_cost_fixed"] = voice_fixed
            st.session_state["voice_cost_transcriber"] = voice_transcriber
            st.session_state["voice_cost_model"] = voice_model
            st.session_state["voice_cost_elevenlabs"] = voice_elevenlabs
            st.session_state["voice_cost_other"] = voice_other
            st.success("Voice minute cost configuration saved. You can integrate it into your plan cost as needed.")

    st.info(
        """
        **Note**: These new LLM and Voice configurations are now in `st.session_state`.
        The sample code in `calculate_plan_cost()` demonstrates how LLM overhead is added to 
        `base_msg_cost` / `base_min_cost`. You can do something similar for voice 
        if you want to layer that cost in as well.
        """
    )

    st.markdown("---")

    # Profit Dashboard
    st.subheader("Profit & Cost Dashboard (Internal Only)")
    st.write("This margin breakdown is based on the last usage scenario from 'Client Calculator'.")

    cost_details = st.session_state.get("client_cost_details", None)
    if cost_details is None:
        st.warning("No recent client cost details. Please run 'Client Calculator' first.")
        show_footer()
        st.stop()

    # Turn the cost_details into a DataFrame and remove underscores in column names
    items_list = list(cost_details.items())
    df_cost_details = pd.DataFrame(items_list, columns=["Parameter", "Amount"])
    # Example transformation: "extra_minutes_used" -> "Extra Minutes Used"
    df_cost_details["Parameter"] = df_cost_details["Parameter"].apply(
        lambda x: x.replace("_", " ").title()
    )
    st.dataframe(df_cost_details, height=400)

    # Approx profit analysis
    final_monthly_cost_with_discount_zar = cost_details["final_monthly_cost_zar"]
    discount_percentage = 0
    if pricing.get("discounts_enabled", True):
        discount_percentage = pricing.get("global_discount_rate", 0)
    if discount_percentage > 0:
        final_monthly_cost_with_discount_zar *= (1 - discount_percentage / 100)

    revenue_zar = final_monthly_cost_with_discount_zar

    plan_name = st.session_state.get("client_selected_plan", "Basic")
    try:
        plan_config = pricing["plans"][plan_name]
    except KeyError:
        st.error(f"Plan '{plan_name}' not found.")
        show_footer()
        st.stop()

    included_msgs = cost_details["included_msgs_after_conversion"]
    included_mins = cost_details["included_mins_after_conversion"]

    # Our direct cost approximation:
    base_msg_cost_zar = plan_config.get("base_msg_cost", 0.05)
    base_min_cost_zar = plan_config.get("base_min_cost", 0.40)
    tech_support_zar = plan_config.get("technical_support_cost", 0)
    float_cost_zar = plan_config.get("float_cost", 0)

    # Minimal approximation ignoring the LLM overhead here 
    # (You can replicate the LLM overhead logic if you want to see "our cost" with LLM.)
    our_estimated_direct_cost_zar = (
        (base_msg_cost_zar * included_msgs)
        + (base_min_cost_zar * included_mins)
        + tech_support_zar
        + float_cost_zar
    )

    profit_zar = revenue_zar - our_estimated_direct_cost_zar
    profit_margin_pct = (profit_zar / revenue_zar * 100) if revenue_zar > 0 else 0

    st.write("**(Internal)** Revenue (ZAR after discount):", f"{revenue_zar:,.2f}")
    st.write("**(Internal)** Direct Cost (ZAR):", f"{our_estimated_direct_cost_zar:,.2f}")
    st.write("**(Internal)** Profit (ZAR):", f"{profit_zar:,.2f}")
    st.write("**(Internal)** Profit Margin:", f"{profit_margin_pct:,.2f}%")

    show_footer()
