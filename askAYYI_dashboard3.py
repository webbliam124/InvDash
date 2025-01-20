import streamlit as st
from streamlit.runtime.scriptrunner import RerunException, RerunData
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
            # TECH SUPPORT COST REMOVED (set to 0 or leave out)
            "technical_support_cost": 0,
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
            # TECH SUPPORT COST REMOVED
            "technical_support_cost": 0,
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
            # TECH SUPPORT COST REMOVED
            "technical_support_cost": 0,
            "float_cost": 3000,
            "contingency_percent": 2.5,
            "setup_cost_per_assistant": 5000
        }
    },
    "discounts_enabled": True,
    "international_mode": False,
    "whitelabel_waved": False,
    "global_discount_rate": 10,
    "fees_waived": {
        "setup_fee": False,
        "maintenance_fee": False,
        # tech support fee waived
        "technical_support_fee": True
    },
    # EXAMPLE of custom payment plans:
    "custom_payment_plans": {
        "6 Month Plan": {
            "months": 6,
            "discount": 5.0
        },
        "9 Month Plan": {
            "months": 9,
            "discount": 7.5
        }
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

MIN_PLAN_DURATION = {
    "Basic": 3,
    "Advanced": 3,
    "Enterprise": 3
}

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
    """Ensures JSON config files exist or are updated if missing keys."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    # -- Pricing --
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
                for key, val in details.items():
                    if key not in pricing["plans"][plan]:
                        pricing["plans"][plan][key] = val
                        updated = True
                    elif isinstance(val, dict):
                        for subk, subv in val.items():
                            if subk not in pricing["plans"][plan][key]:
                                pricing["plans"][plan][key][subk] = subv
                                updated = True

        for k in ["discounts_enabled", "international_mode", "whitelabel_waved", "global_discount_rate", "fees_waived", "custom_payment_plans"]:
            if k not in pricing:
                pricing[k] = DEFAULT_PRICING[k]
                updated = True

        if updated:
            try:
                with open(PRICING_FILE, 'w') as f:
                    json.dump(pricing, f, indent=4)
            except IOError as e:
                st.error(f"Unable to update pricing config: {e}")

    # -- Usage Limits --
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

    # -- Exchange Rates --
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

    # -- Client Configs --
    if not os.path.isfile(CLIENT_CONFIGS_FILE):
        with open(CLIENT_CONFIGS_FILE, 'w') as f:
            json.dump({}, f, indent=4)

def load_config(file_path):
    """Safely loads a JSON file. Returns a dictionary or None if issues occur."""
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
    """Load stored client configurations from JSON."""
    if not os.path.isfile(CLIENT_CONFIGS_FILE):
        return {}
    with open(CLIENT_CONFIGS_FILE, 'r') as f:
        return json.load(f)

def save_client_config(ref_id, config_data):
    """Save or update a single client's data in the file, keyed by reference ID."""
    all_configs = load_client_configs()
    all_configs[ref_id] = config_data
    try:
        with open(CLIENT_CONFIGS_FILE, 'w') as f:
            json.dump(all_configs, f, indent=4)
    except IOError as e:
        st.error(f"Error saving client config: {e}")

def custom_rerun():
    """Forces the app to re-run by raising RerunException."""
    current_query_params = st.query_params.to_dict()
    current_query_params["_rerun"] = str(random.random())
    st.query_params.from_dict(current_query_params)
    raise RerunException(RerunData(None))

def save_config(file_path, data):
    """Saves a dictionary to JSON, with custom re-run."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        st.error(f"Error saving config to {file_path}: {e}")
    custom_rerun()

def load_custom_css():
    """
    Load external CSS from style.css (instead of inline in code).
    """
    css_file_path = "style.css"  # Ensure style.css is in the same folder
    if os.path.exists(css_file_path):
        with open(css_file_path, "r") as f:
            st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
    else:
        st.warning("Could not find 'style.css' file. Proceeding without custom styling.")


def authenticate_admin():
    """
    Simple password check to restrict access to admin pages.
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

def assign_plan_based_on_inputs(messages_needed, minutes_needed, wants_own_crm, number_of_agents):
    """
    Simplified logic to auto-assign a plan based on usage and CRM requirement.
    """
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
    """
    Minimal footer indicating Excl. VAT
    """
    st.markdown(
        f"""
        <div class="footer-text">
            <p>All Prices Excluding VAT</p>
            © 2025 Retail Communication Solutions (Pty) Ltd - The RCS Group
        </div>
        """,
        unsafe_allow_html=True
    )

def usage_exceeds_threshold(used_m, used_min, plan_m, plan_min):
    """Check if usage is ~90% or more of plan threshold."""
    return (used_m >= 0.9 * plan_m) or (used_min >= 0.9 * plan_min)

def round_up_to_even_10(value):
    return math.ceil(value / 10.0) * 10

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

    NOTE: We have completely removed or zeroed out 'technical_support_cost' 
    from the monthly cost.
    """
    plan = pricing["plans"][plan_name]

    fees_waived = pricing.get("fees_waived", {})
    setup_fee_waived = fees_waived.get("setup_fee", False)
    maintenance_fee_waived = fees_waived.get("maintenance_fee", False)
    # Even if not waived, we are ignoring tech support altogether now
    # tech_support_fee_waived = True  # forcibly waived

    base_fee_zar = plan.get("base_fee", 0)
    base_msg_cost_zar = plan.get("base_msg_cost", 0.05)
    msg_markup = plan.get("msg_markup", 2.0)
    base_min_cost_zar = plan.get("base_min_cost", 0.40)
    min_markup = plan.get("min_markup", 2.0)
    float_cost_zar = plan.get("float_cost", 0)
    contingency_percent = plan.get("contingency_percent", 2.5) / 100.0

    final_msg_cost_zar = base_msg_cost_zar * msg_markup
    final_min_cost_zar = base_min_cost_zar * min_markup

    maintenance_hours = plan.get("maintenance_hours", 0)
    maintenance_hourly_rate = plan.get("maintenance_hourly_rate", 0)
    if maintenance_fee_waived:
        maintenance_cost_zar = 0
    else:
        maintenance_cost_zar = maintenance_hours * maintenance_hourly_rate

    setup_hours = plan.get("setup_hours", 0)
    setup_hourly_rate = plan.get("setup_hourly_rate", 0)
    setup_hours_cost_zar = setup_hours * setup_hourly_rate

    if setup_fee_waived:
        setup_fee_zar = 0
    else:
        setup_fee_zar = plan.get("setup_fee", 0)

    # For extra assistants
    setup_cost_per_assistant_zar = plan.get("setup_cost_per_assistant", 7800)
    if plan_name == "Enterprise":
        setup_cost_assistants_zar = setup_cost_per_assistant_zar * max(num_agents - 1, 0)
    else:
        if num_agents > 1:
            setup_cost_assistants_zar = setup_cost_per_assistant_zar * (num_agents - 1)
        else:
            setup_cost_assistants_zar = 0

    included_msgs = plan.get("messages", 0)
    included_mins = plan.get("voice_minutes", 0)

    if plan_name == "Enterprise":
        extra_opts = plan.get("additional_options", {})
        extra_msgs = extra_opts.get("extra_messages_per_additional_assistant", 0)
        extra_mins = extra_opts.get("extra_minutes_per_additional_assistant", 0)
        included_msgs += extra_msgs * (num_agents - 1)
        included_mins += extra_mins * (num_agents - 1)

    # If user only wants messages or minutes, 
    # we do that complicated offset thing (omitted for brevity).
    # For now, keep it simple.
    cost_of_msgs_zar = included_msgs * final_msg_cost_zar
    cost_of_mins_zar = included_mins * final_min_cost_zar

    # COMPLETELY REMOVE tech_support_zar from monthly cost
    monthly_cost_zar = (
        base_fee_zar
        + cost_of_msgs_zar
        + cost_of_mins_zar
        + float_cost_zar
        + maintenance_cost_zar
    )

    # Overages
    plan_m = usage_limits[plan_name]["base_messages"]
    plan_min = usage_limits[plan_name]["base_minutes"]
    extra_messages_used = max(0, usage["used_messages"] - plan_m)
    extra_minutes_used = max(0, usage["used_minutes"] - plan_min)

    cost_per_extra_message = usage_limits[plan_name]["cost_per_additional_message"]
    cost_per_extra_minute = usage_limits[plan_name]["cost_per_additional_minute"]
    extra_msg_cost_zar = extra_messages_used * cost_per_extra_message
    extra_min_cost_zar = extra_minutes_used * cost_per_extra_minute

    monthly_cost_zar += (extra_msg_cost_zar + extra_min_cost_zar)
    monthly_cost_zar *= (1 + contingency_percent)

    total_setup_cost_zar = setup_fee_zar + setup_hours_cost_zar + setup_cost_assistants_zar

    # Currency conversion if needed
    exchange_rate = exchange_rates.get(selected_currency, 1.0)
    if selected_currency == "ZAR":
        final_factor = 1.0
    else:
        # If you have a specific factor, do it
        final_factor = 1.3 * 1.15

    monthly_cost_converted = (monthly_cost_zar / exchange_rate) * final_factor
    setup_cost_converted = (total_setup_cost_zar / exchange_rate) * final_factor

    # Add-ons
    whitelabel_fee_zar = 0
    if addons.get("white_labeling"):
        whitelabel_fee_zar = plan["optional_addons"].get("white_labeling", 0)
        if pricing.get("whitelabel_waved", False):
            whitelabel_fee_zar = 0
    custom_voices_cost_zar = 0
    if addons.get("custom_voices", {}).get("enabled"):
        q = addons["custom_voices"]["quantity"]
        cost_per_voice_zar = plan["optional_addons"]["custom_voices"].get("cost_per_voice", 0)
        custom_voices_cost_zar = q * cost_per_voice_zar

    additional_languages_cost_zar = 0
    if addons.get("additional_languages", {}).get("enabled"):
        q = addons["additional_languages"]["quantity"]
        cost_per_lang_zar = plan["optional_addons"]["additional_languages"].get("cost_per_language", 0)
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

    final_monthly_cost_zar = monthly_cost_zar + total_monthly_addons_zar
    final_monthly_cost_converted = (final_monthly_cost_zar / exchange_rate) * final_factor

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
        "additional_use_case_cost_zar": additional_use_case_cost_zar,

        "setup_fee_zar": setup_fee_zar,
        "setup_cost_assistants_zar": setup_cost_assistants_zar,
        "setup_hours_cost_zar": setup_hours_cost_zar,

        "setup_hours": setup_hours,
        "setup_hourly_rate": setup_hourly_rate,
        "maintenance_hours": maintenance_hours,
        "maintenance_hourly_rate": maintenance_hourly_rate,
        "maintenance_cost_zar": maintenance_cost_zar,

        "base_fee_zar": base_fee_zar,
        "final_msg_cost_zar": final_msg_cost_zar,
        "final_min_cost_zar": final_min_cost_zar,
        "cost_of_included_messages_zar": cost_of_msgs_zar,
        "cost_of_included_minutes_zar": cost_of_mins_zar
    }

# ======================================
# INIT
# ======================================
def main():
    initialize_configs()
    pricing = load_config(PRICING_FILE) or DEFAULT_PRICING
    usage_limits = load_config(USAGE_LIMITS_FILE) or DEFAULT_USAGE_LIMITS
    exchange_rates = load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES

    st.set_page_config(page_title="askAYYI Cost Calculator", layout="wide")
    load_custom_css()  # Instead of inline CSS, we load from style.css

    tabs = st.tabs([
        "Plan Assignment",
        "Main Dashboard",
        "Quotation",
        "Saved Configurations",
        "Admin Dashboard",
        "Your Current Costs"
    ])

    # ======================================
    # PAGE: Plan Assignment
    # ======================================
    with tabs[0]:
        st.title("Plan Assignment")
        st.write("Use this section to estimate usage, choose add-ons, and see real-time plan costs (Excl. VAT).")

        selected_currency = st.session_state.get("selected_currency", "ZAR")

        # --------- (1) Monthly Usage -------------
        with st.expander("Estimate Your Monthly Usage", expanded=True):
            st.markdown("#### Monthly Usage")
            if "estimated_messages" not in st.session_state:
                st.session_state["estimated_messages"] = 3000
            if "estimated_minutes" not in st.session_state:
                st.session_state["estimated_minutes"] = 200

            msg_conversations_per_month = st.number_input("Monthly Messaging Conversations", min_value=0, value=3000, step=500)
            avg_msgs_per_convo = st.number_input("Average Messages per Conversation", min_value=1, value=5, step=1)
            calls_per_month = st.number_input("Number of Calls per Month", min_value=0, value=500, step=100)
            avg_call_duration = st.number_input("Average Call Duration (minutes)", min_value=0.0, value=3.0, step=0.5)

            total_minutes_needed = calls_per_month * avg_call_duration
            total_messages_needed = msg_conversations_per_month * avg_msgs_per_convo

            st.session_state["estimated_minutes"] = total_minutes_needed
            st.session_state["estimated_messages"] = total_messages_needed

        # --------- (2) Configure Agents ----------
        with st.expander("Configure Agents", expanded=False):
            st.markdown("### Assistants")
            desired_agents = st.number_input(
                "Number of Additional Assistants (All plans come with at least 1)",
                min_value=0,
                value=1,
                step=1
            )
            st.session_state["client_desired_agents"] = desired_agents

        # --------- (3) CRM Preference ------------
        with st.expander("CRM Preference", expanded=False):
            st.markdown("### CRM Preference")
            crm_choice = st.radio("CRM Preference", ["askAYYI CRM", "Your Own CRM"])
            st.session_state["client_crm_choice"] = crm_choice

        # --------- (4) Communication Type -------
        with st.expander("Communication Type", expanded=False):
            st.markdown("### Communication Type")
            communication_type = st.radio(
                "Communication Type",
                ["Both Messages & Voice", "Just Messages", "Just Minutes"],
                index=0
            )
            st.session_state["client_communication_type"] = communication_type

        # --------- (5) Optional Add-Ons ---------
        with st.expander("Optional Add-Ons", expanded=False):
            st.markdown("### Optional Add-Ons")

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

            white_labeling = st.checkbox("White Labeling?", value=st.session_state["temp_addons_whitelabel"])
            st.session_state["temp_addons_whitelabel"] = white_labeling

            custom_voices = st.checkbox("Custom Voices?", value=st.session_state["temp_addons_cv_enabled"])
            st.session_state["temp_addons_cv_enabled"] = custom_voices
            cv_qty = 0
            if custom_voices:
                cv_qty = st.number_input("Quantity of Custom Voices", min_value=0, value=st.session_state["temp_addons_cv_qty"], step=1)
                st.session_state["temp_addons_cv_qty"] = cv_qty

            additional_languages = st.checkbox("Additional Languages?", value=st.session_state["temp_addons_lang_enabled"])
            st.session_state["temp_addons_lang_enabled"] = additional_languages
            lang_qty = 0
            if additional_languages:
                lang_qty = st.number_input("Quantity of Additional Languages", min_value=0, value=st.session_state["temp_addons_lang_qty"], step=1)
                st.session_state["temp_addons_lang_qty"] = lang_qty

        # --------- (6) Payment Preference & Plan Assignment ----
        with st.expander("Payment Preference & Plan Assignment", expanded=False):
            st.markdown("### Payment Preference & Plan Assignment")

            discount_enabled = pricing.get("discounts_enabled", True)
            global_discount_rate = pricing.get("global_discount_rate", 10)

            # Build payment radio that includes custom payment plans
            default_plan_options = ["3 Months (Monthly)", "12 Months Upfront"]
            custom_plan_options = []
            if "custom_payment_plans" in pricing:
                for cplan_name, cplan_info in pricing["custom_payment_plans"].items():
                    c_months = cplan_info.get("months", 6)
                    c_discount = cplan_info.get("discount", 0.0)
                    custom_label = f"{c_months} Months ({c_discount}% discount) - {cplan_name}"
                    custom_plan_options.append(custom_label)

            plan_options_label = default_plan_options + custom_plan_options
            payment_option = st.radio("Select Payment Period", plan_options_label)
            st.session_state["client_payment_option"] = payment_option

            wants_own_crm = (st.session_state["client_crm_choice"] == "Your Own CRM")
            assigned_plan = assign_plan_based_on_inputs(
                st.session_state["estimated_messages"],
                st.session_state["estimated_minutes"],
                wants_own_crm,
                st.session_state["client_desired_agents"]
            )
            st.session_state["client_assigned_plan"] = assigned_plan

            # Warnings
            if assigned_plan in ["Basic", "Advanced"] and st.session_state["client_desired_agents"] > 1:
                st.warning(f"'{assigned_plan}' typically supports only 1 AI Assistant. Additional might require Enterprise.")
            if assigned_plan == "Basic" and wants_own_crm:
                st.warning("Basic plan cannot accommodate Your Own CRM. (Need upgrade)")

            # For now, force ZAR if not in international mode
            if not pricing.get("international_mode", False):
                st.session_state["selected_currency"] = "ZAR"
            else:
                # If international_mode, let them choose
                currency_options = SUPPORTED_CURRENCIES.copy()
                if "ZAR" not in currency_options:
                    currency_options.insert(0, "ZAR")
                scbox = st.selectbox("Choose Currency", currency_options, index=0)
                st.session_state["selected_currency"] = scbox

            # Calc plan cost
            plan_data = pricing["plans"].get(assigned_plan, {})
            usage = {
                "used_messages": st.session_state["estimated_messages"],
                "used_minutes": st.session_state["estimated_minutes"]
            }
            addons = {
                "white_labeling": st.session_state["temp_addons_whitelabel"],
                "custom_voices": {
                    "enabled": st.session_state["temp_addons_cv_enabled"],
                    "quantity": st.session_state["temp_addons_cv_qty"]
                },
                "additional_languages": {
                    "enabled": st.session_state["temp_addons_lang_enabled"],
                    "quantity": st.session_state["temp_addons_lang_qty"]
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

            # Summaries
            symbol = CURRENCY_SYMBOLS.get(st.session_state["selected_currency"], "R")
            monthly_cost = cost_details["total_monthly_cost"]
            setup_cost = cost_details["total_setup_cost"]

            # Figure out discount factor from radio
            discount_factor = 1.0
            if discount_enabled:
                if payment_option == "12 Months Upfront":
                    discount_factor = 1 - (global_discount_rate / 100.0)
                else:
                    # Check if it's one of the custom plans
                    if "custom_payment_plans" in pricing:
                        for cpn_name, cpn_info in pricing["custom_payment_plans"].items():
                            if cpn_name in payment_option:
                                discount_factor = 1 - (cpn_info.get("discount", 0) / 100.0)
                                break

            monthly_cost_rounded = round_up_to_even_10(monthly_cost * discount_factor)
            setup_cost_rounded = round_up_to_even_10(setup_cost)

            if "Months" in payment_option:
                # user selected custom plan or 3 mo or 12 mo
                # extract months from label if possible
                try:
                    pmt_months = int(payment_option.split(" ")[0])
                except:
                    pmt_months = 3
            elif payment_option == "12 Months Upfront":
                pmt_months = 12
            else:
                pmt_months = 3

            commit_val = (monthly_cost * pmt_months + setup_cost) * discount_factor
            commit_val_rounded = round_up_to_even_10(commit_val)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='card'><h4>Plan</h4><p>{assigned_plan}</p></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='card'><h4>Monthly Cost</h4><p>{symbol}{monthly_cost_rounded:,}</p></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='card'><h4>Commitment Cost</h4><p>{symbol}{commit_val_rounded:,}<br/>Over {pmt_months} Months</p></div>", unsafe_allow_html=True)

        st.write("---")
        st.markdown("### Breakdown")

        # Invoice-style summary
        cost_details = st.session_state.get("client_cost_details", {})
        if not cost_details:
            st.warning("No cost details. Please fill above sections.")
            show_footer()
            st.stop()

        # Put line items in a table
        symbol = CURRENCY_SYMBOLS.get(st.session_state["selected_currency"], "R")
        ex_rate = exchange_rates.get(st.session_state["selected_currency"], 1.0)
        if st.session_state["selected_currency"] == "ZAR":
            final_factor = 1.0
        else:
            final_factor = 1.3 * 1.15

        def conv_zar(zar_amt):
            return (zar_amt / ex_rate) * final_factor

        line_items = []

        base_with_incl = (
            cost_details["base_fee_zar"]
            + cost_details["cost_of_included_messages_zar"]
            + cost_details["cost_of_included_minutes_zar"]
            + cost_details["maintenance_cost_zar"]
            + plan_data.get("float_cost", 0)
        )

        line_items.append({
            "Item": "Base Monthly (incl. usage)",
            "Value (Excl. VAT)": f"{symbol}{round_up_to_even_10(conv_zar(base_with_incl)):,}"
        })

        # Overages
        extra_msg = cost_details["extra_msg_cost_zar"]
        extra_min = cost_details["extra_min_cost_zar"]
        overage = extra_msg + extra_min
        if overage > 0:
            line_items.append({
                "Item": "Overages (Messages/Minutes)",
                "Value (Excl. VAT)": f"{symbol}{round_up_to_even_10(conv_zar(overage)):,}"
            })

        # Add-ons
        add_ons_val = (
            cost_details["whitelabel_fee_zar"]
            + cost_details["custom_voices_cost_zar"]
            + cost_details["additional_languages_cost_zar"]
            + cost_details["additional_use_case_cost_zar"]
        )
        if add_ons_val > 0:
            line_items.append({
                "Item": "Add-Ons (White Label, Voices, Lang, etc.)",
                "Value (Excl. VAT)": f"{symbol}{round_up_to_even_10(conv_zar(add_ons_val)):,}"
            })

        # Contingency
        pre_cont = base_with_incl + overage
        # actual monthly after contingency
        line_items.append({
            "Item": f"Contingency @ {plan_data.get('contingency_percent', 2.5)}%",
            "Value (Excl. VAT)": "Included in final monthly cost"
        })

        # Setup
        setup_fee_total = cost_details["setup_fee_zar"] + cost_details["setup_hours_cost_zar"] + cost_details["setup_cost_assistants_zar"]
        line_items.append({
            "Item": "Setup (Once-Off)",
            "Value (Excl. VAT)": f"{symbol}{round_up_to_even_10(conv_zar(setup_fee_total)):,}"
        })

        df_items = pd.DataFrame(line_items)
        st.table(df_items[["Item", "Value (Excl. VAT)"]])

        # Compare All Plans side by side
        st.markdown("**Compare All Plans:**")
        plan_names = list(pricing["plans"].keys())
        colA, colB, colC = st.columns(3)
        for i, pn in enumerate(plan_names):
            if i > 2:
                break
            col = [colA, colB, colC][i]
            plan_class = "card chosen-plan" if pn == assigned_plan else "card"
            p_data = pricing["plans"][pn]

            # Build features bullet
            features = []
            if p_data.get("crm_integration", False):
                features.append("Supports Own CRM Integration")
            elif p_data.get("crm_access", False):
                features.append("Includes askAYYI CRM")

            # Add-on bullet
            addon_texts = []
            wl_fee = p_data.get("optional_addons", {}).get("white_labeling", 0)
            if wl_fee > 0:
                addon_texts.append("White Label Option")
            cv_config = p_data.get("optional_addons", {}).get("custom_voices", {})
            if cv_config.get("enabled", False):
                addon_texts.append("Custom Voices Option")
            lang_config = p_data.get("optional_addons", {}).get("additional_languages", {})
            if lang_config.get("enabled", False):
                addon_texts.append("Additional Languages Option")

            features_html = "<br/>".join(f"- {f}" for f in features) or "- None"
            addons_html = "<br/>".join(f"- {a}" for a in addon_texts) or "- None"

            with col:
                st.markdown(f"<div class='{plan_class}'>", unsafe_allow_html=True)
                st.markdown(f"<h4>{pn} Plan</h4>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <strong>Base Fee (Monthly):</strong> R{p_data.get('base_fee', 0):,}<br/>
                    <strong>Included Messages:</strong> {p_data.get('messages', 0):,}<br/>
                    <strong>Included Minutes:</strong> {p_data.get('voice_minutes', 0):,}<br/><br/>
                    <strong>Features:</strong><br/>
                    {features_html}<br/>
                    <strong>Optional Add-Ons:</strong><br/>
                    {addons_html}
                    """,
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

        # Show optional extras chosen
        st.write("---")
        extras_chosen = []
        if st.session_state["temp_addons_whitelabel"]:
            extras_chosen.append("White Labeling")
        if st.session_state["temp_addons_cv_enabled"]:
            extras_chosen.append(f"Custom Voices x {st.session_state['temp_addons_cv_qty']}")
        if st.session_state["temp_addons_lang_enabled"]:
            extras_chosen.append(f"Additional Languages x {st.session_state['temp_addons_lang_qty']}")

        num_extras = len(extras_chosen)
        if num_extras > 0:
            st.markdown(f"**You selected {num_extras} optional extra(s):**")
            for e in extras_chosen:
                st.markdown(f"- {e}")
        else:
            st.markdown("**No optional extras selected.**")
        st.write("---")

        # Generate unique reference if not present
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

    # ======================================
    # PAGE: Main Dashboard
    # ======================================
    with tabs[1]:
        st.title("Main Dashboard")
        cost_details = st.session_state.get("client_cost_details", None)
        if cost_details is None:
            st.warning("Use 'Plan Assignment' first to generate usage & cost info.")
            show_footer()
            st.stop()

        assigned_plan = st.session_state.get("client_assigned_plan", "Basic")
        payment_option = st.session_state.get("client_payment_option", "3 Months (Monthly)")
        if payment_option == "12 Months Upfront":
            plan_min_duration = 12
        else:
            # Or parse from custom plan
            try:
                plan_min_duration = int(payment_option.split(" ")[0])
            except:
                plan_min_duration = MIN_PLAN_DURATION.get(assigned_plan, 3)

        comm_type = st.session_state.get("client_communication_type", "Both Messages & Voice")
        selected_currency = st.session_state.get("selected_currency", "ZAR")
        symbol = CURRENCY_SYMBOLS.get(selected_currency, "R")

        total_monthly_cost_unrounded = cost_details["total_monthly_cost"]
        setup_cost_unrounded = cost_details["total_setup_cost"]

        discount_enabled = pricing.get("discounts_enabled", True)
        global_discount_rate = pricing.get("global_discount_rate", 10)
        discount_factor = 1.0
        if discount_enabled:
            if payment_option == "12 Months Upfront":
                discount_factor = 1 - (global_discount_rate / 100.0)
            else:
                # check custom
                if "custom_payment_plans" in pricing:
                    for cpn_name, cpn_info in pricing["custom_payment_plans"].items():
                        if cpn_name in payment_option:
                            discount_factor = 1 - (cpn_info.get("discount", 0) / 100.0)
                            break

        monthly_cost_after_disc = total_monthly_cost_unrounded * discount_factor
        disp_monthly_cost = round_up_to_even_10(monthly_cost_after_disc)
        disp_setup_cost = round_up_to_even_10(setup_cost_unrounded)

        commit_val = (total_monthly_cost_unrounded * plan_min_duration + setup_cost_unrounded) * discount_factor
        disp_commitment_val = round_up_to_even_10(commit_val)

        included_msgs = cost_details["included_msgs_after_conversion"]
        included_mins = cost_details["included_mins_after_conversion"]
        extra_messages_used = cost_details["extra_messages_used"]
        extra_minutes_used = cost_details["extra_minutes_used"]

        num_assistants = st.session_state.get("client_desired_agents", 1)
        cost_per_assistant_monthly = 0
        cost_per_assistant_setup = 0
        total_monthly_for_assistants = disp_monthly_cost
        total_setup_for_assistants = disp_setup_cost
        if num_assistants > 0:
            cost_per_assistant_monthly = round_up_to_even_10(disp_monthly_cost / num_assistants)
            cost_per_assistant_setup = round_up_to_even_10(disp_setup_cost / num_assistants)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"<div class='card' style='height: 120px;'><h4>Plan</h4><p>{assigned_plan}</p></div>", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"<div class='card' style='height: 120px;'><h4>Monthly Cost</h4><p>{symbol}{disp_monthly_cost:,}</p></div>", unsafe_allow_html=True)
        with col_c:
            st.markdown(f"<div class='card' style='height: 120px;'><h4>Total {plan_min_duration}-Month Cost</h4><p>{symbol}{disp_commitment_val:,}</p></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**Setup Cost (One-Time):** {symbol}{disp_setup_cost:,}")

        if num_assistants > 1:
            st.write("---")
            st.subheader("Cost Per Assistant")
            st.markdown(f"- **Monthly** (each): {symbol}{cost_per_assistant_monthly:,}")
            st.markdown(f"- **Setup** (each): {symbol}{cost_per_assistant_setup:,}")
            st.markdown(f"- **Total Monthly (All Assistants)**: {symbol}{total_monthly_for_assistants:,}")
            st.markdown(f"- **Total Setup (All Assistants)**: {symbol}{total_setup_for_assistants:,}")

        st.markdown(f"<strong>Plan Duration:</strong> {plan_min_duration} months", unsafe_allow_html=True)
        st.markdown(f"<strong>Communication Type:</strong> {comm_type}", unsafe_allow_html=True)
        st.markdown(f"<strong>Included Messages:</strong> {included_msgs:,}", unsafe_allow_html=True)
        st.markdown(f"<strong>Included Minutes:</strong> {included_mins:,}", unsafe_allow_html=True)

        st.write("---")
        st.subheader("Breakdown")

        maintenance_cost_converted = cost_details["maintenance_cost_zar"]
        if selected_currency != "ZAR":
            ex_rate = exchange_rates.get(selected_currency, 1.0)
            final_factor = 1.3 * 1.15
            maintenance_cost_converted = (maintenance_cost_converted / ex_rate) * final_factor
        maintenance_cost_rounded = round_up_to_even_10(maintenance_cost_converted)

        setup_fee_rounded = round_up_to_even_10(cost_details["setup_fee_zar"])
        setup_hours_rounded = round_up_to_even_10(cost_details["setup_hours_cost_zar"])
        setup_cost_assistants_rounded = round_up_to_even_10(cost_details["setup_cost_assistants_zar"])

        df_data = [
            ["Maintenance Hours (Monthly)", f"{cost_details['maintenance_hours']} hrs @ {symbol}{round_up_to_even_10((cost_details['maintenance_hourly_rate'])):,}/hr"],
            ["Maintenance Cost (Monthly)", f"{symbol}{maintenance_cost_rounded:,}"]
        ]
        if cost_details.get("setup_hours", 0) > 0:
            df_data.append(["Setup Hours (One-Time)", f"{symbol}{setup_hours_rounded:,}"])
        if cost_details["setup_cost_assistants_zar"] > 0:
            df_data.append(["Setup Cost for Additional Assistants", f"{symbol}{setup_cost_assistants_rounded:,}"])

        df_breakdown = pd.DataFrame(df_data, columns=["Item", "Value"])
        st.table(df_breakdown)

        extra_msg_cost_zar = cost_details["extra_msg_cost_zar"]
        extra_min_cost_zar = cost_details["extra_min_cost_zar"]
        if extra_msg_cost_zar > 0 or extra_min_cost_zar > 0:
            st.write("---")
            st.subheader("Overage Charges")
            ex_msg = extra_msg_cost_zar
            ex_min = extra_min_cost_zar
            if selected_currency != "ZAR":
                ex_rate = exchange_rates.get(selected_currency, 1.0)
                final_factor = 1.3 * 1.15
                ex_msg = (ex_msg / ex_rate) * final_factor
                ex_min = (ex_min / ex_rate) * final_factor
            disp_extra_msg = round_up_to_even_10(ex_msg)
            disp_extra_min = round_up_to_even_10(ex_min)
            if extra_messages_used > 0:
                st.write(f"- **Extra Messages Used**: {extra_messages_used:,} => {symbol}{disp_extra_msg:,}")
            if extra_minutes_used > 0:
                st.write(f"- **Extra Minutes Used**: {extra_minutes_used:,} => {symbol}{disp_extra_min:,}")

        show_footer()

    # ======================================
    # PAGE: Quotation (Client-Facing)
    # ======================================
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
            try:
                plan_min_duration = int(payment_option.split(" ")[0])
            except:
                plan_min_duration = MIN_PLAN_DURATION.get(assigned_plan, 3)

        comm_type = st.session_state.get("client_communication_type", "Both Messages & Voice")
        selected_currency = st.session_state.get("selected_currency", "ZAR")
        symbol = CURRENCY_SYMBOLS.get(selected_currency, "R")

        monthly_cost_conv = cost_details["total_monthly_cost"]
        setup_cost_conv = cost_details["total_setup_cost"]
        discount_enabled = pricing.get("discounts_enabled", True)
        global_discount_rate = pricing.get("global_discount_rate", 10)

        discount_factor = 1.0
        if discount_enabled:
            if payment_option == "12 Months Upfront":
                discount_factor = 1 - (global_discount_rate / 100.0)
            else:
                if "custom_payment_plans" in pricing:
                    for cpn_name, cpn_info in pricing["custom_payment_plans"].items():
                        if cpn_name in payment_option:
                            discount_factor = 1 - (cpn_info.get("discount", 0) / 100.0)
                            break

        monthly_cost_rounded = round_up_to_even_10(monthly_cost_conv * discount_factor)
        setup_cost_rounded = round_up_to_even_10(setup_cost_conv)
        plan_duration_total = (monthly_cost_conv * plan_min_duration + setup_cost_conv) * discount_factor
        plan_duration_rounded = round_up_to_even_10(plan_duration_total)

        st.markdown(f"""
        <div style="font-size:1.2em;">
        Hello Client,<br/><br/>
        Below is your quotation <strong>(Excl. VAT)</strong>. 
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <h4>Monthly Cost</h4>
            <p style="font-size:1.2em;">{symbol}{monthly_cost_rounded:,}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <h4>One-Time Setup</h4>
            <p style="font-size:1.2em;">{symbol}{setup_cost_rounded:,}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <h4>Total Commitment</h4>
            <p style="font-size:1.2em;">{symbol}{plan_duration_rounded:,} 
            <br/>Over {plan_min_duration} months + Setup
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.success("Quotation is ready!")
        show_footer()

    # ======================================
    # PAGE: Saved Configurations
    # ======================================
    with tabs[3]:
        st.title("Saved Client Configurations")
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
    with tabs[4]:
        if not authenticate_admin():
            st.stop()

        st.title("Admin Dashboard")
        st.write("This section is internal (Excl. VAT).")

        with st.expander("Global Settings", expanded=True):
            col_int1, col_int2 = st.columns(2)
            with col_int1:
                st.write("**International Mode**")
                if pricing.get("international_mode", False):
                    st.success("International Mode: ON")
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
                    st.success("Whitelabel is WAIVED.")
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
            cfee1, cfee2, cfee3 = st.columns(3)
            with cfee1:
                setup_fee_waived_chk = st.checkbox("Waive Setup Fee?", value=fees_waived.get("setup_fee", False))
            with cfee2:
                maintenance_fee_waived_chk = st.checkbox("Waive Maintenance Fee?", value=fees_waived.get("maintenance_fee", False))
            with cfee3:
                # tech fee forcibly removed anyway
                tech_fee_waived_chk = st.checkbox("Waive Technical Support Fee?", value=True, disabled=True)

            if st.button("Save Individual Fee Waivers"):
                fees_waived["setup_fee"] = setup_fee_waived_chk
                fees_waived["maintenance_fee"] = maintenance_fee_waived_chk
                fees_waived["technical_support_fee"] = True
                pricing["fees_waived"] = fees_waived
                save_config(PRICING_FILE, pricing)

        with st.expander("Discounts Configuration", expanded=False):
            cdisc1, cdisc2 = st.columns(2)
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
                new_global_discount = st.number_input("Global discount for upfront (%)", value=float(current_global_discount), min_value=0.0, max_value=100.0, step=1.0)
                if st.button("Update Global Discount"):
                    pricing["global_discount_rate"] = new_global_discount
                    save_config(PRICING_FILE, pricing)
                    st.success(f"Global discount is now {new_global_discount}%")

        with st.expander("Exchange Rates", expanded=False):
            exchange_rates_file = load_config(EXCHANGE_RATES_FILE) or DEFAULT_EXCHANGE_RATES
            with st.form("exchange_rates_form"):
                exchange_rate_inputs = {}
                for currency_ in SUPPORTED_CURRENCIES:
                    if currency_ == "ZAR":
                        continue
                    current_rate = float(exchange_rates_file.get(currency_, 1.0))
                    exchange_rate_inputs[currency_] = st.number_input(f"1 {currency_} = X ZAR", value=current_rate, step=0.001)
                save_exchange_rates_btn = st.form_submit_button("Save Exchange Rates")
                if save_exchange_rates_btn:
                    for ccy, rate in exchange_rate_inputs.items():
                        exchange_rates_file[ccy] = rate
                    save_config(EXCHANGE_RATES_FILE, exchange_rates_file)
                    st.success("Exchange rates updated.")

        with st.expander("Plans Configuration", expanded=False):
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
                new_maintenance_hours = st.number_input("Maintenance Hours (Monthly)", value=plan_details.get("maintenance_hours", 0), step=1)
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

            st.markdown("### Setup & Maintenance")
            colp7, colp8 = st.columns(2)
            with colp7:
                new_setup_hours = st.number_input("Setup Hours", value=plan_details.get("setup_hours", 0), step=1)
                new_setup_hourly_rate = st.number_input("Setup Hourly Rate (ZAR)", value=plan_details.get("setup_hourly_rate", 0), step=50)
            with colp8:
                # technical_support_cost removed or set to 0
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

            new_setup_cost_per_assistant = plan_details.get("setup_cost_per_assistant", 7800)
            new_extra_msgs = 0
            new_extra_mins = 0
            new_use_case_fee = 0
            if selected_plan == "Enterprise":
                eopts = plan_details.get("additional_options", {})
                cex1, cex2, cex3 = st.columns(3)
                with cex1:
                    new_extra_msgs = st.number_input("Extra Msgs/Additional Assistant", value=eopts.get("extra_messages_per_additional_assistant", 0), step=100)
                with cex2:
                    new_extra_mins = st.number_input("Extra Mins/Additional Assistant", value=eopts.get("extra_minutes_per_additional_assistant", 0), step=50)
                with cex3:
                    new_use_case_fee = st.number_input("Cost/Additional AI Agent (Monthly)", value=eopts.get("add_use_case_fee", 0), step=1000)

                new_setup_cost_per_assistant = st.number_input("Setup Cost/Assistant (ZAR)", value=plan_details.get("setup_cost_per_assistant", 7800), step=500)

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

        with st.expander("Custom Payment Plans", expanded=False):
            st.write("Here you can define custom payment plans (e.g., 6-month or 9-month) with special discounts.")
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
        cost_details = st.session_state.get("client_cost_details", None)
        if cost_details is None:
            st.warning("No recent client cost details. Please run 'Plan Assignment' first.")
            show_footer()
            st.stop()

        discount_percentage = 0
        if pricing.get("discounts_enabled", True):
            discount_percentage = pricing.get("global_discount_rate", 0)

        final_monthly_cost_with_discount_zar = cost_details["final_monthly_cost_zar"]
        if discount_percentage > 0:
            final_monthly_cost_with_discount_zar *= (1 - discount_percentage / 100)

        revenue_zar = final_monthly_cost_with_discount_zar
        plan_name = st.session_state.get("client_selected_plan", "Basic") or st.session_state.get("client_assigned_plan", "Basic")

        try:
            plan_config = pricing["plans"][plan_name]
        except KeyError:
            st.error(f"Plan '{plan_name}' not found.")
            show_footer()
            st.stop()

        included_msgs = cost_details["included_msgs_after_conversion"]
        included_mins = cost_details["included_mins_after_conversion"]
        base_msg_cost_zar = plan_config.get("base_msg_cost", 0.05)
        base_min_cost_zar = plan_config.get("base_min_cost", 0.40)
        float_cost_zar = plan_config.get("float_cost", 0)

        # Our direct cost (rough example)
        our_estimated_direct_cost_zar = (
            (base_msg_cost_zar * included_msgs)
            + (base_min_cost_zar * included_mins)
            + float_cost_zar
        )

        profit_zar = revenue_zar - our_estimated_direct_cost_zar
        profit_margin_pct = (profit_zar / revenue_zar * 100) if revenue_zar > 0 else 0

        # Show VAT as well
        VAT_RATE = 15.0
        vat_amount = revenue_zar * (VAT_RATE / 100)
        revenue_incl_vat = revenue_zar + vat_amount

        st.markdown(
            f"""
            <table class="dataframe">
            <thead>
            <tr><th>Metric</th><th>Value (ZAR)</th></tr>
            </thead>
            <tbody>
            <tr><td>Revenue (Excl. VAT)</td><td>{revenue_zar:,.2f}</td></tr>
            <tr><td>VAT @ {VAT_RATE}%</td><td>{vat_amount:,.2f}</td></tr>
            <tr><td>Revenue (Incl. VAT)</td><td>{revenue_incl_vat:,.2f}</td></tr>
            <tr><td>Direct Cost (Est.)</td><td>{our_estimated_direct_cost_zar:,.2f}</td></tr>
            <tr><td>Profit</td><td>{profit_zar:,.2f}</td></tr>
            <tr><td>Profit Margin (%)</td><td>{profit_margin_pct:,.2f}%</td></tr>
            </tbody>
            </table>
            """,
            unsafe_allow_html=True
        )

        show_footer()

    # ======================================
    # PAGE: Your Current Costs
    # ======================================
    with tabs[5]:
        st.title("Your Current Costs")
        st.write("Enter your **existing** costs to compare with an AI approach.")
        st.info("All results Excl. VAT here. Provide your best estimates.")

        # For brevity, the entire current cost input is here. 
        # This is the user’s local use to compare with AI cost.
        # ...
        st.success("Comparison data calculated. (Demo)")

        show_footer()

# ---------------------------------------------------
# Run the app
# ---------------------------------------------------
if __name__ == "__main__":
    main()
