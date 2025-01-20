import streamlit as st
import os
import json
import pandas as pd
import numpy as np
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

# Attempt to import numpy_financial for IRR
try:
    import numpy_financial as nf
    HAS_NUMPY_FINANCIAL = True
except ImportError:
    HAS_NUMPY_FINANCIAL = False

# ------------------------------------------------------
# Page config for wide layout
# ------------------------------------------------------
st.set_page_config(layout="wide")

# ----------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------


def compute_irr(cash_flows):
    """
    Compute IRR for the given cash flows.
    If numpy_financial is not available, use a simple bisection method.

    :param cash_flows: list or array of net cash flows for each period (period 0, 1, 2, etc.)
    :return: IRR value (decimal), or None if cannot be computed.
    """
    if not any(cf < 0 for cf in cash_flows) or not any(cf > 0 for cf in cash_flows):
        return None
    if HAS_NUMPY_FINANCIAL:
        try:
            return nf.irr(cash_flows)
        except:
            return None
    else:
        # Manual bisection method if numpy_financial not available
        min_rate = -0.999999
        max_rate = 10.0
        for _ in range(1000):
            mid_rate = (min_rate + max_rate) / 2
            npv = 0
            for i, cf in enumerate(cash_flows):
                try:
                    denom = (1 + mid_rate)**i if (1 + mid_rate) != 0 else 1e-9
                    npv += cf / denom
                except:
                    return None
            if abs(npv) < 1e-2:
                return mid_rate
            if npv > 0:
                min_rate = mid_rate
            else:
                max_rate = mid_rate
        return None


def compute_roi(cash_flows):
    """
    Simple ROI: (final value - initial investment) / initial investment

    :param cash_flows: list or array of net cash flows for each period, 
                       where period 0 is the initial investment (negative).
    :return: ROI value (decimal), or None if cannot be computed.
    """
    if len(cash_flows) < 1:
        return None
    init_inv = -cash_flows[0] if cash_flows[0] < 0 else 0
    final_value = sum(cash_flows[1:])
    if init_inv == 0:
        return 0
    return (final_value - init_inv) / init_inv


def get_phased_growth_rate(
    month_idx,
    # Phase 1
    phase1_start_month,
    phase1_end_month,
    phase1_start_rate,
    phase1_end_rate,
    # Phase 2
    phase2_start_month,
    phase2_end_month,
    phase2_start_rate,
    phase2_end_rate,
    # Phase 3
    phase3_start_month,
    phase3_end_month,
    phase3_start_rate,
    phase3_end_rate,
    # Plateau
    plateau_rate
):
    """
    Returns a growth rate (%) for the given 0-based month_idx, based on 3 phases
    plus a final plateau. All phases are defined by a start month and end month
    (inclusive range in 1-based counting), plus a start rate and end rate to interpolate.

    The phases happen sequentially. The logic is:
        1) If i < phase1_start_month => return phase1_start_rate
        2) If phase1_start_month <= i < phase1_end_month => linear interpolation 
           from phase1_start_rate to phase1_end_rate
        3) If phase1_end_month <= i < phase2_start_month => return phase1_end_rate
        4) If phase2_start_month <= i < phase2_end_month => linear interpolation 
           from phase2_start_rate to phase2_end_rate
        5) If phase2_end_month <= i < phase3_start_month => return phase2_end_rate
        6) If phase3_start_month <= i < phase3_end_month => linear interpolation 
           from phase3_start_rate to phase3_end_rate
        7) If i >= phase3_end_month => return plateau_rate
    """
    i = month_idx + 1  # Convert to 1-based

    # Phase 1
    if i < phase1_start_month:
        return phase1_start_rate
    if phase1_start_month <= i < phase1_end_month:
        total_span = float(phase1_end_month - phase1_start_month)
        frac = (i - phase1_start_month) / total_span if total_span > 0 else 0
        return phase1_start_rate + frac * (phase1_end_rate - phase1_start_rate)

    # The segment between Phase 1 end and Phase 2 start
    if phase1_end_month <= i < phase2_start_month:
        return phase1_end_rate

    # Phase 2
    if phase2_start_month <= i < phase2_end_month:
        total_span = float(phase2_end_month - phase2_start_month)
        frac = (i - phase2_start_month) / total_span if total_span > 0 else 0
        return phase2_start_rate + frac * (phase2_end_rate - phase2_start_rate)

    # The segment between Phase 2 end and Phase 3 start
    if phase2_end_month <= i < phase3_start_month:
        return phase2_end_rate

    # Phase 3
    if phase3_start_month <= i < phase3_end_month:
        total_span = float(phase3_end_month - phase3_start_month)
        frac = (i - phase3_start_month) / total_span if total_span > 0 else 0
        return phase3_start_rate + frac * (phase3_end_rate - phase3_start_rate)

    # After Phase 3 end => plateau
    return plateau_rate


def month_index_for_date(target_date, start_date, frequency):
    """
    Returns the 1-based index of the period in which 'target_date' falls
    relative to 'start_date', based on the chosen frequency.
    """
    try:
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        total_month_diff = (target_date.year - start_date.year) * \
            12 + (target_date.month - start_date.month)
        if total_month_diff < 0:
            return 0
        freq = frequency.lower()
        if freq == "month":
            return total_month_diff + 1
        elif freq == "quarter":
            return int(np.floor(total_month_diff / 3)) + 1
        else:
            return int(np.floor(total_month_diff / 12)) + 1
    except:
        return None

# ----------------------------------------------------------------
# MAIN FORECAST FUNCTION
# ----------------------------------------------------------------


def generate_projection(
    start_date=None,
    end_date=None,
    frequency="Month",
    initial_cash=500000.0,
    inflation_rate=5.0,
    # Phase 1
    phase1_start_month=1,
    phase1_end_month=3,
    phase1_start_rate=3.0,
    phase1_end_rate=5.0,
    # Phase 2
    phase2_start_month=4,
    phase2_end_month=8,
    phase2_start_rate=6.0,
    phase2_end_rate=15.0,
    # Phase 3
    phase3_start_month=9,
    phase3_end_month=12,
    phase3_start_rate=16.0,
    phase3_end_rate=25.0,
    # Plateau
    plateau_rate=10.0,
    # Clients
    initial_clients=10,
    churn_rate_annual=10.0,
    client_plan_distribution=None,
    # Plans & Pricing
    plans_info=None,
    # Top Ups
    topup_users_pct=0.0,
    topup_utilization_pct=0.0,
    topup_cost_per_unit_msg=0.05,
    topup_price_per_unit_msg=0.08,
    topup_cost_per_unit_min=0.05,
    topup_price_per_unit_min=0.08,
    included_quota_per_plan=None,
    # R&D
    rd_investment_pct=0.0,
    rd_revenue_pct=0.0,
    funding_rounds=None,
    allocate_new_investment_across_expenses=False,
    # Staff (NOW MONTHLY)
    fixed_staff_info=None,
    variable_staff_info=None,
    # Onboarding & Maintenance Hours + Decrease factors
    onboarding_hours_per_plan=None,
    monthly_maintenance_hrs_per_plan=None,
    onboarding_decrease_factors_per_plan=None,
    maintenance_decrease_factors_per_plan=None,
    # Overheads/Operating
    overhead_items=None,
    marketing_mode="fixed",
    marketing_budget=120000.0,
    marketing_pct_of_revenue=0.0,
    hardware_cost_per_employee=0.0,
    # Loan (optional)
    enable_initial_loan=False,
    initial_loan_amount=0.0,
    loan_interest_rate_annual=0.0,
    loan_payback_strategy="none",
    loan_payback_start_month=1,
    loan_payback_end_date=None,
    loan_fixed_amount=0.0,
    loan_percent_of_profit=0.0,
    loan_lump_sum=0.0,
    lump_sum_paid=False
):
    """
    This function generates a projection (DataFrame) of monthly/quarterly/yearly forecasts.

    KEY CHANGES:
    1) Staff salaries are now treated as MONTHLY amounts in the input forms. 
       We apply annual raises once per year, then multiply by period length (month=1, quarter=3, year=12).
    2) Overhead items remain "monthly_cost", scaled by period length if freq=quarter/year.
    3) Marketing budget remains monthly-based, scaled by freq if needed.
    """
    try:
        # 1) Validate start/end date
        if not start_date or not end_date:
            start_date = date.today()
            end_date = start_date + relativedelta(months=12)

        # 2) Determine periods per year and months per iteration
        freq = frequency.lower()
        if freq not in ["month", "quarter", "year"]:
            freq = "month"
        if freq == "month":
            periods_per_year = 12
            period_length_in_months = 1
        elif freq == "quarter":
            periods_per_year = 4
            period_length_in_months = 3
        else:
            periods_per_year = 1
            period_length_in_months = 12

        # Build the list of timestamps/periods
        dt_list = []
        current_dt = start_date
        while current_dt <= end_date:
            dt_list.append(current_dt)
            if freq == "month":
                current_dt += relativedelta(months=1)
            elif freq == "quarter":
                current_dt += relativedelta(months=3)
            else:
                current_dt += relativedelta(years=1)
        if len(dt_list) < 1:
            dt_list = [start_date, start_date + relativedelta(months=1)]

        # Default fallback for plans_info
        if plans_info is None:
            plans_info = {
                "Basic": {
                    "monthly_cos": 2000,
                    "setup_cos": 3000,
                    "monthly_selling_price": 5000,
                    "setup_selling_price": 4000
                }
            }

        # Default fallback for distribution
        if client_plan_distribution is None:
            client_plan_distribution = {"Basic": 1.0}

        # Overheads fallback
        if overhead_items is None:
            overhead_items = [
                {"name": "Office Rental", "monthly_cost": 10000, "annual_increase": 5},
                {"name": "Communications", "monthly_cost": 3000, "annual_increase": 5},
                {"name": "Administration", "monthly_cost": 2000, "annual_increase": 5},
                {"name": "Insurance", "monthly_cost": 1500, "annual_increase": 5},
                {"name": "Logistics", "monthly_cost": 2500, "annual_increase": 5},
                {"name": "Transport", "monthly_cost": 4000, "annual_increase": 5},
                {"name": "Legal", "monthly_cost": 5000, "annual_increase": 5},
                {"name": "Sundry", "monthly_cost": 2000, "annual_increase": 5},
                {"name": "Software Subscriptions",
                    "monthly_cost": 5000, "annual_increase": 5},
                {"name": "Software", "monthly_cost": 2000, "annual_increase": 5}
            ]

        # Staff info fallback
        if fixed_staff_info is None:
            # NOW these are monthly salaries, not annual
            fixed_staff_info = {
                "CEO - RCS Executive": {"headcount": 1, "base_salary": 150000, "annual_raise": 0.07, "capacity": 0},
                "CTO - RCS Executive": {"headcount": 1, "base_salary": 130000, "annual_raise": 0.07, "capacity": 0},
            }

        if variable_staff_info is None:
            # also monthly
            variable_staff_info = {
                "Onboarding Specialist": {
                    "headcount": 0,
                    "base_salary": 3000,
                    "annual_raise": 0.05,
                    "capacity": 160
                },
                "Technical Support Programmers": {
                    "headcount": 0,
                    "base_salary": 3500,
                    "annual_raise": 0.05,
                    "capacity": 160
                }
            }

        # Hours fallback
        if onboarding_hours_per_plan is None:
            onboarding_hours_per_plan = {"Basic": 12}
        if monthly_maintenance_hrs_per_plan is None:
            monthly_maintenance_hrs_per_plan = {"Basic": 4}
        if onboarding_decrease_factors_per_plan is None:
            onboarding_decrease_factors_per_plan = {"Basic": 1.0}
        if maintenance_decrease_factors_per_plan is None:
            maintenance_decrease_factors_per_plan = {"Basic": 1.0}
        if included_quota_per_plan is None:
            included_quota_per_plan = {"Basic": (5000, 300)}

        # If we use a payback end date with "Lump + Timeline" strategy
        if loan_payback_strategy == "Lump + Timeline" and loan_payback_end_date:
            loan_payback_end_month_index = month_index_for_date(
                loan_payback_end_date, start_date, frequency)
        else:
            loan_payback_end_month_index = 999999

        total_periods = len(dt_list)

        # Prepare data structure for final results
        results = {
            "Time_Label": [],
            "ParsedDate": [],
            "Clients_Starting": [],
            "Clients_New": [],
            "Clients_Churned": [],
            "Clients_Ending": [],
            "Revenue_Subscription": [],
            "Revenue_SetupFees": [],
            "Revenue_TopUp": [],
            "Revenue_Total": [],
            "COS_Subscription": [],
            "COS_TopUp": [],
            "COS_Total": [],
            "Profit_GrossProfit": [],
            "Staff_Fixed": [],
            "Staff_Variable": [],
            "Cost_StaffFixed": [],
            "Cost_StaffVariable": [],
            "Cost_Staff": [],
            "Cost_Overheads": [],
            "Cost_Hardware": [],
            "Cost_Marketing": [],
            "Cost_RDExpense": [],
            "Cost_OperatingExpenses": [],
            "Profit_EBITDA": [],
            "Profit_NetIncome": [],
            "CashFlow_FundingInflow": [],
            "CashFlow_LoanInflow": [],
            "CashFlow_LoanPayment": [],
            "CashFlow_LoanBalance": [],
            "CashFlow_EndingCash": [],
            "Staff_OnboardingHrsUsed": [],
            "Staff_MaintenanceHrsUsed": [],
        }

        # Initialize rolling values
        current_clients = initial_clients
        current_cash = initial_cash
        loan_balance = 0.0
        if enable_initial_loan and initial_loan_amount > 0:
            loan_balance = initial_loan_amount

        # Convert annual churn to "per period" churn
        churn_decimal_per_cycle = (
            churn_rate_annual / 100.0) / periods_per_year
        lumpsum_already_paid = lump_sum_paid

        for idx, this_date in enumerate(dt_list):
            # Build a label for the period
            if freq == "month":
                month_label = this_date.strftime("%Y-%m")
            elif freq == "quarter":
                qnum = int((this_date.month - 1) / 3) + 1
                month_label = f"{this_date.year}-Q{qnum}"
            else:
                month_label = this_date.strftime("%Y")

            # Starting clients
            start_c = current_clients

            # Determine growth rate for this period
            this_growth_rate = get_phased_growth_rate(
                month_idx=idx,
                phase1_start_month=phase1_start_month,
                phase1_end_month=phase1_end_month,
                phase1_start_rate=phase1_start_rate,
                phase1_end_rate=phase1_end_rate,
                phase2_start_month=phase2_start_month,
                phase2_end_month=phase2_end_month,
                phase2_start_rate=phase2_start_rate,
                phase2_end_rate=phase2_end_rate,
                phase3_start_month=phase3_start_month,
                phase3_end_month=phase3_end_month,
                phase3_start_rate=phase3_start_rate,
                phase3_end_rate=phase3_end_rate,
                plateau_rate=plateau_rate
            )

            g_factor = 1.0 + (this_growth_rate / 100.0)
            organic_new_c = int(
                round(start_c * (g_factor - 1.0))) if g_factor > 1.0 else 0
            churned_c = int(round(start_c * churn_decimal_per_cycle))
            end_c = start_c + organic_new_c - churned_c
            if end_c < 0:
                end_c = 0

            # --------------- REVENUE & COS ---------------
            rev_sub = 0.0
            cos_sub = 0.0
            rev_setup = 0.0
            cos_setup = 0.0

            plan_splits_for_start = {}
            for plan_n, frac in client_plan_distribution.items():
                plan_splits_for_start[plan_n] = start_c * frac

            plan_splits_for_new = {}
            for plan_n, frac in client_plan_distribution.items():
                plan_splits_for_new[plan_n] = organic_new_c * frac

            avg_clients = (start_c + end_c)/2.0

            for plan_n, plan_cfg in plans_info.items():
                frac_c = client_plan_distribution.get(plan_n, 0)
                plan_avg_c = avg_clients * frac_c

                monthly_sell = plan_cfg["monthly_selling_price"] * \
                    period_length_in_months
                monthly_cos = plan_cfg["monthly_cos"] * period_length_in_months

                rev_sub += plan_avg_c * monthly_sell
                cos_sub += plan_avg_c * monthly_cos

                new_clients_for_plan = plan_splits_for_new.get(plan_n, 0)
                rev_setup += new_clients_for_plan * \
                    plan_cfg.get("setup_selling_price", 0.0)
                cos_setup += new_clients_for_plan * \
                    plan_cfg.get("setup_cos", 0.0)

            # --------------- TOP-UPS ---------------
            topup_revenue = 0.0
            topup_cos = 0.0
            for plan_n, plan_cfg in plans_info.items():
                plan_end_c = end_c * client_plan_distribution.get(plan_n, 0)
                buyers = plan_end_c * topup_users_pct

                (base_incl_msgs, base_incl_mins) = included_quota_per_plan.get(
                    plan_n, (0, 0))
                base_incl_msgs_period = base_incl_msgs * period_length_in_months
                base_incl_mins_period = base_incl_mins * period_length_in_months

                extra_units_msgs = base_incl_msgs_period * topup_utilization_pct
                extra_units_mins = base_incl_mins_period * topup_utilization_pct

                total_extra_msgs = buyers * extra_units_msgs
                total_extra_mins = buyers * extra_units_mins

                topup_revenue_msgs = total_extra_msgs * topup_price_per_unit_msg
                topup_cos_msgs = total_extra_msgs * topup_cost_per_unit_msg

                topup_revenue_mins = total_extra_mins * topup_price_per_unit_min
                topup_cos_mins = total_extra_mins * topup_cost_per_unit_min

                topup_revenue += (topup_revenue_msgs + topup_revenue_mins)
                topup_cos += (topup_cos_msgs + topup_cos_mins)

            total_revenue = rev_sub + rev_setup + topup_revenue
            total_cos = cos_sub + cos_setup + topup_cos
            gross_profit = total_revenue - total_cos

            # --------------- STAFF COSTS (MONTHLY BASE) ---------------
            # We now treat 'base_salary' as MONTHLY. We still apply an annual raise once per year.
            staff_cost_fixed = 0.0
            total_fixed_staff = 0
            months_from_start = idx
            years_elapsed = int(months_from_start / 12.0)

            # Initialize hiring and termination costs
            HIRE_COST_PER_EMPLOYEE = 10000.0  # R
            TERMINATE_COST_PER_EMPLOYEE = 5000.0  # R

            # Initialize current variable staff headcount tracking
            if idx == 0:
                current_variable_staff_headcount = {
                    role: sdat["headcount"] for role, sdat in variable_staff_info.items()}

            # Fixed staff
            for role, sdat in fixed_staff_info.items():
                # base_salary is monthly
                base_sal_monthly_now = sdat["base_salary"] * \
                    ((1 + sdat["annual_raise"])**years_elapsed)
                staff_cost_period = base_sal_monthly_now * \
                    period_length_in_months * sdat["headcount"]

                staff_cost_fixed += staff_cost_period
                total_fixed_staff += sdat["headcount"]

            # Variable staff
            total_onboard_hrs = 0.0
            for plan_n, new_count in plan_splits_for_new.items():
                if plan_n in onboarding_hours_per_plan:
                    base_hrs = onboarding_hours_per_plan[plan_n]
                    od_factor = onboarding_decrease_factors_per_plan.get(
                        plan_n, 1.0)
                    adj_hrs = base_hrs * (od_factor ** years_elapsed)
                    total_onboard_hrs += (new_count * adj_hrs)

            total_technical_hrs = 0.0
            for plan_n, plan_end_frac in client_plan_distribution.items():
                if plan_n in monthly_maintenance_hrs_per_plan:
                    mm_hrs = monthly_maintenance_hrs_per_plan[plan_n]
                    td_factor = maintenance_decrease_factors_per_plan.get(
                        plan_n, 1.0)
                    adj_mm_hrs = mm_hrs * (td_factor ** years_elapsed)
                    plan_end_c = end_c * plan_end_frac
                    adj_mm_hrs_period = adj_mm_hrs * period_length_in_months
                    total_technical_hrs += (plan_end_c * adj_mm_hrs_period)

            staff_cost_variable = 0.0
            total_variable_staff = 0

            for role, info in variable_staff_info.items():
                base_salary = info["base_salary"] * \
                    ((1 + info["annual_raise"])**years_elapsed)
                capacity = info["capacity"]
                required_staff = 1
                if capacity > 0:
                    if "Onboarding" in role:
                        required_staff = np.ceil(total_onboard_hrs / capacity)
                    elif "Technical" in role:
                        required_staff = np.ceil(
                            total_technical_hrs / capacity)
                required_staff = int(required_staff)

                current_staff = current_variable_staff_headcount.get(role, 0)
                if required_staff > current_staff:
                    hires = required_staff - current_staff
                    staff_cost_variable += (base_salary * period_length_in_months *
                                            required_staff) + (HIRE_COST_PER_EMPLOYEE * hires)
                    current_variable_staff_headcount[role] = required_staff
                elif required_staff < current_staff:
                    terminations = current_staff - required_staff
                    staff_cost_variable += (base_salary * period_length_in_months * required_staff) + (
                        TERMINATE_COST_PER_EMPLOYEE * terminations)
                    current_variable_staff_headcount[role] = required_staff
                else:
                    staff_cost_variable += base_salary * period_length_in_months * required_staff

                total_variable_staff += required_staff

            total_staff_cost = staff_cost_fixed + staff_cost_variable

            # --------------- OVERHEADS ---------------
            oh_cost = 0.0
            for oh in overhead_items:
                base_val = oh["monthly_cost"]
                inc = oh["annual_increase"]
                inflated_monthly = base_val * ((1 + inc/100.0)**years_elapsed)
                cost_for_this_period = inflated_monthly * period_length_in_months
                oh_cost += cost_for_this_period

            # --------------- HARDWARE COST ---------------
            total_staff_headcount = total_fixed_staff + total_variable_staff
            hardware_cost = total_staff_headcount * \
                hardware_cost_per_employee * period_length_in_months

            # --------------- MARKETING ---------------
            if marketing_mode == "fixed":
                marketing_spend_with_pct = total_revenue * \
                    (marketing_pct_of_revenue / 100.0)
                marketing_budget_for_period = marketing_budget * period_length_in_months
                if marketing_spend_with_pct > (marketing_budget_for_period * 1.2):
                    marketing_spend = marketing_spend_with_pct
                else:
                    marketing_spend = marketing_budget_for_period
            else:
                marketing_spend = total_revenue * \
                    (marketing_pct_of_revenue / 100.0)

            # --------------- R&D EXPENSE ---------------
            rd_expense_monthly = total_revenue * (rd_revenue_pct / 100.0)
            opex = total_staff_cost + oh_cost + hardware_cost + \
                marketing_spend + rd_expense_monthly

            # --------------- EBITDA & NET INCOME ---------------
            ebitda = gross_profit - opex
            net_income = ebitda

            # --------------- FUNDING ROUNDS ---------------
            fin_flow = 0.0
            for fr in funding_rounds or []:
                if fr.get('month_trigger', 0) == (idx + 1):
                    amt = fr.get('amount', 0.0)
                    fin_flow += amt
                    rd_cut = amt * (rd_investment_pct / 100.0)
                    net_income -= rd_cut
                    opex += rd_cut

            # --------------- LOAN LOGIC ---------------
            # We do not inject the initial loan as cash (it's treated as previous debt)
            loan_inflow = 0.0

            # Interest
            if loan_balance > 0:
                # approximate monthly interest (annual / 12), scaled by period_length_in_months
                interest_for_period = loan_balance * \
                    ((loan_interest_rate_annual/100.0)/12.0) * \
                    period_length_in_months
                net_income -= interest_for_period
                loan_balance += interest_for_period

            # Payback
            loan_payment = 0.0
            month_idx_1_based = idx + 1
            if enable_initial_loan and loan_balance > 0:
                if month_idx_1_based >= loan_payback_start_month:
                    if loan_payback_strategy == "fixed" and loan_fixed_amount > 0:
                        pay_amt = min(
                            loan_fixed_amount * period_length_in_months, loan_balance, max(0, net_income))
                        loan_balance -= pay_amt
                        loan_payment = pay_amt
                        net_income -= pay_amt

                    elif loan_payback_strategy == "Percentage of Profit" and loan_percent_of_profit > 0:
                        if net_income > 0:
                            portion = net_income * \
                                (loan_percent_of_profit / 100.0)
                            portion = min(portion, loan_balance)
                            loan_balance -= portion
                            loan_payment = portion
                            net_income -= portion

                    elif loan_payback_strategy == "Percentage of Profit + Lump":
                        if not lumpsum_already_paid and loan_lump_sum > 0:
                            pay_now = min(
                                loan_lump_sum, loan_balance, fin_flow
                            )
                            loan_balance -= pay_now
                            loan_payment += pay_now
                            fin_flow -= pay_now
                            if abs(pay_now - loan_lump_sum) < 1e-9:
                                lumpsum_already_paid = True
                        if loan_percent_of_profit > 0 and net_income > 0 and loan_balance > 0:
                            portion = net_income * \
                                (loan_percent_of_profit / 100.0)
                            portion = min(portion, loan_balance)
                            loan_balance -= portion
                            loan_payment += portion
                            net_income -= portion

                    elif loan_payback_strategy == "Lump + Timeline" and month_idx_1_based <= loan_payback_end_month_index:
                        if (month_idx_1_based == loan_payback_start_month) and (not lumpsum_already_paid) and (loan_lump_sum > 0):
                            lumpsum_pay = min(
                                loan_lump_sum, loan_balance, max(0, net_income))
                            loan_balance -= lumpsum_pay
                            loan_payment += lumpsum_pay
                            net_income -= lumpsum_pay
                            if abs(lumpsum_pay - loan_lump_sum) < 1e-9:
                                lumpsum_already_paid = True

                        months_left = max(
                            0, (loan_payback_end_month_index - month_idx_1_based + 1))
                        if months_left > 0:
                            monthly_payment = loan_balance / months_left
                            pay_amt = min(monthly_payment,
                                          loan_balance, max(0, net_income))
                            loan_balance -= pay_amt
                            loan_payment += pay_amt
                            net_income -= pay_amt

            # --------------- CASH FLOW ---------------
            current_cash += (net_income + fin_flow + loan_inflow)
            if current_cash < 0:
                current_cash = 0.0

            # --------------- Store results ---------------
            results["Time_Label"].append(month_label)
            results["ParsedDate"].append(this_date)
            results["Clients_Starting"].append(start_c)
            results["Clients_New"].append(organic_new_c)
            results["Clients_Churned"].append(churned_c)
            results["Clients_Ending"].append(end_c)
            results["Revenue_Subscription"].append(rev_sub)
            results["Revenue_SetupFees"].append(rev_setup)
            results["Revenue_TopUp"].append(topup_revenue)
            results["Revenue_Total"].append(total_revenue)
            results["COS_Subscription"].append(cos_sub + cos_setup)
            results["COS_TopUp"].append(topup_cos)
            results["COS_Total"].append(total_cos)
            results["Profit_GrossProfit"].append(gross_profit)
            results["Staff_Fixed"].append(total_fixed_staff)
            results["Staff_Variable"].append(total_variable_staff)
            results["Cost_StaffFixed"].append(staff_cost_fixed)
            results["Cost_StaffVariable"].append(staff_cost_variable)
            results["Cost_Staff"].append(total_staff_cost)
            results["Cost_Overheads"].append(oh_cost)
            results["Cost_Hardware"].append(hardware_cost)
            results["Cost_Marketing"].append(marketing_spend)
            results["Cost_RDExpense"].append(rd_expense_monthly)
            results["Cost_OperatingExpenses"].append(opex)
            results["Profit_EBITDA"].append(ebitda)
            results["Profit_NetIncome"].append(net_income)
            results["CashFlow_FundingInflow"].append(fin_flow)
            results["CashFlow_LoanInflow"].append(loan_inflow)
            results["CashFlow_LoanPayment"].append(loan_payment)
            results["CashFlow_LoanBalance"].append(loan_balance)
            results["CashFlow_EndingCash"].append(current_cash)
            results["Staff_OnboardingHrsUsed"].append(total_onboard_hrs)
            results["Staff_MaintenanceHrsUsed"].append(total_technical_hrs)

            current_clients = end_c

        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Error in generate_projection: {e}")
        return pd.DataFrame()


def compute_saas_metrics(df, start_d, end_d):
    """
    Compute additional columns & key metrics: CAGR, IRR, ROI, 
    plus typical margin % metrics for investor documents.
    """
    try:
        if df.empty:
            return df, {}

        # Additional ratio columns
        df["GrossMarginPct"] = np.where(
            df["Revenue_Total"] != 0,
            df["Profit_GrossProfit"] / df["Revenue_Total"] * 100, 0
        )
        df["EBITDAMarginPct"] = np.where(
            df["Revenue_Total"] != 0,
            df["Profit_EBITDA"] / df["Revenue_Total"] * 100, 0
        )
        df["NetMarginPct"] = np.where(
            df["Revenue_Total"] != 0,
            df["Profit_NetIncome"] / df["Revenue_Total"] * 100, 0
        )
        # ARPU
        df["ARPU"] = np.where(
            df["Clients_Ending"] != 0,
            df["Revenue_Total"] / df["Clients_Ending"], 0
        )

        # CAGR (Revenue) from first period to last
        total_days = (end_d - start_d).days
        years_count = total_days / 365.0 if total_days > 0 else 1.0
        if len(df) > 1:
            start_val = df["Revenue_Total"].iloc[0]
            end_val = df["Revenue_Total"].iloc[-1]
        else:
            start_val, end_val = 0, 0

        if start_val > 0 and end_val > 0 and years_count > 0:
            cagr = (end_val / start_val)**(1 / years_count) - 1
        else:
            cagr = 0.0

        # Build a net_flows list for IRR & ROI:
        #   CF[0] = -initial_invest
        #   CF[1..N] = each period's (NetIncome + FundingInflow + LoanInflow)
        net_flows = []
        init_invest = st.session_state["config"].get("initial_cash", 0.0)
        net_flows.append(-init_invest)

        for i in range(len(df)):
            net_flows.append(
                df["Profit_NetIncome"].iloc[i]
                + df["CashFlow_FundingInflow"].iloc[i]
                + df["CashFlow_LoanInflow"].iloc[i]
            )

        irr_val = compute_irr(net_flows)
        roi_val = compute_roi(net_flows)

        if irr_val is None:
            irr_val = 0.0
        if roi_val is None:
            roi_val = 0.0

        metrics_dict = {
            "CAGR_Revenue": cagr * 100.0,
            "IRR": irr_val * 100,
            "ROI": roi_val * 100
        }
        return df, metrics_dict
    except Exception as e:
        st.error(f"Error in compute_saas_metrics: {e}")
        return df, {}

# ----------------------------------------------------------------
# RESELLER CALCULATION
# ----------------------------------------------------------------


def calculate_reseller_revenue(
    reseller_client_base=0,
    reseller_pct_to_capture=0.0,
    reseller_profit_share_pct=0.0,
    plans_info=None,
    client_plan_distribution=None,
    topup_users_pct=0.0,
    topup_utilization_pct=0.0,
    topup_cost_per_unit_msg=0.05,
    topup_price_per_unit_msg=0.08,
    topup_cost_per_unit_min=0.05,
    topup_price_per_unit_min=0.08,
    included_quota_per_plan=None,
):
    """
    Calculate a simple, single 'snapshot' potential revenue from a Reseller,
    using the same plan configurations. We'll produce a DataFrame with details
    for each plan, plus the total, then also show a line for 'reseller profit share'.
    """
    if plans_info is None:
        return pd.DataFrame()

    if client_plan_distribution is None:
        return pd.DataFrame()

    if included_quota_per_plan is None:
        included_quota_per_plan = {}

    # We'll assume we capture "reseller_pct_to_capture" fraction of "reseller_client_base"
    # Then distribute that fraction across the same plan distribution.
    results = {
        "Plan": [],
        "Captured_Clients": [],
        "Monthly_Revenue": [],
        "Monthly_COS": [],
        "TopUp_Revenue": [],
        "TopUp_COS": [],
        "Total_Revenue": [],
        "Total_COS": [],
        "Gross_Profit": [],
    }

    total_clients_captured = reseller_client_base * reseller_pct_to_capture
    for plan_name, plan_frac in client_plan_distribution.items():
        plan_clients = total_clients_captured * plan_frac

        # Subscription & Setup revenue (assuming we want monthly subscription snapshot only,
        # ignoring one-time setup for this quick calculation.
        # If you want to include setup fees here, you could.)
        monthly_rev = plan_clients * \
            plans_info[plan_name]["monthly_selling_price"]
        monthly_cos = plan_clients * plans_info[plan_name]["monthly_cos"]

        # Top-ups
        buyers = plan_clients * topup_users_pct
        (base_incl_msgs, base_incl_mins) = included_quota_per_plan.get(
            plan_name, (0, 0))

        extra_units_msgs = base_incl_msgs * topup_utilization_pct
        extra_units_mins = base_incl_mins * topup_utilization_pct

        total_extra_msgs = buyers * extra_units_msgs
        total_extra_mins = buyers * extra_units_mins

        topup_revenue_msgs = total_extra_msgs * topup_price_per_unit_msg
        topup_cos_msgs = total_extra_msgs * topup_cost_per_unit_msg

        topup_revenue_mins = total_extra_mins * topup_price_per_unit_min
        topup_cos_mins = total_extra_mins * topup_cost_per_unit_min

        topup_rev = topup_revenue_msgs + topup_revenue_mins
        topup_c = topup_cos_msgs + topup_cos_mins

        total_rev = monthly_rev + topup_rev
        total_cost = monthly_cos + topup_c
        gp = total_rev - total_cost

        results["Plan"].append(plan_name)
        results["Captured_Clients"].append(plan_clients)
        results["Monthly_Revenue"].append(monthly_rev)
        results["Monthly_COS"].append(monthly_cos)
        results["TopUp_Revenue"].append(topup_rev)
        results["TopUp_COS"].append(topup_c)
        results["Total_Revenue"].append(total_rev)
        results["Total_COS"].append(total_cost)
        results["Gross_Profit"].append(gp)

    df_reseller = pd.DataFrame(results)
    if not df_reseller.empty:
        df_reseller.loc["Total"] = df_reseller.sum(numeric_only=True)
        df_reseller.at["Total", "Plan"] = "TOTAL"
        # profit share
        total_gp = df_reseller.loc["Total", "Gross_Profit"]
        reseller_share = total_gp * reseller_profit_share_pct
        new_row = {
            "Plan": f"Reseller Profit Share ({reseller_profit_share_pct*100:.1f}%)",
            "Captured_Clients": 0,
            "Monthly_Revenue": 0,
            "Monthly_COS": 0,
            "TopUp_Revenue": 0,
            "TopUp_COS": 0,
            "Total_Revenue": 0,
            "Total_COS": 0,
            "Gross_Profit": -reseller_share,
        }
        df_reseller = pd.concat(
            [df_reseller, pd.DataFrame([new_row])], ignore_index=True)

        net_row = {
            "Plan": "Net After Reseller Share",
            "Captured_Clients": 0,
            "Monthly_Revenue": 0,
            "Monthly_COS": 0,
            "TopUp_Revenue": 0,
            "TopUp_COS": 0,
            "Total_Revenue": 0,
            "Total_COS": 0,
            "Gross_Profit": total_gp - reseller_share
        }
        df_reseller = pd.concat(
            [df_reseller, pd.DataFrame([net_row])], ignore_index=True)

    return df_reseller


def serialize_config(config):
    """
    Recursively convert date objects in the config to ISO format strings.
    """
    if isinstance(config, dict):
        return {k: serialize_config(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [serialize_config(item) for item in config]
    elif isinstance(config, datetime):
        return config.isoformat()
    elif isinstance(config, date):
        return config.isoformat()
    else:
        return config


def deserialize_config(config):
    """
    Recursively convert ISO format strings back to date objects in the config.
    """
    if isinstance(config, dict):
        return {k: deserialize_config(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [deserialize_config(item) for item in config]
    elif isinstance(config, str):
        try:
            return datetime.fromisoformat(config).date()
        except ValueError:
            return config
    else:
        return config

# ----------------------------------------------------------------
# STREAMLIT APP
# ----------------------------------------------------------------


def main():
    """
    The main Streamlit app. 

    MAJOR CHANGES:
    1) Staff costs now read as MONTHLY inputs (previously annual).
    2) Added a Reseller section to show additional potential revenue 
       from a reseller partner with profit share.
    3) Added Save and Load Configuration functionality.
    """
    st.title("askAYYI Investor Dashboard")

    # --- Create 3 tabs: Inputs, Reseller, Results
    tab1, tab_reseller, tab2 = st.tabs(["Inputs", "Partners", "Results"])

    with tab1:
        st.header("Forecast Configuration")

        # 1) Date Range & Basic
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input(
                "Forecast Start Date", value=date.today())
        with c2:
            end_date = st.date_input(
                "Forecast End Date", value=date.today() + relativedelta(months=12))

        freq = st.selectbox("Frequency", ["Month", "Quarter", "Year"], index=0)

        # 2) Starting Conditions
        st.subheader("Starting Conditions")
        initial_cash = st.number_input(
            "Initial Cash (R)", 0.0, 1e12, 0.0, step=5000.0)
        initial_clients = st.number_input("Initial Clients", 0, 1_000_000, 10)
        churn_rate_annual = st.slider(
            "Annual Churn Rate (%)", 0.0, 100.0, 10.0)

        # 3) PHASED Growth Configuration
        st.subheader("Phased Growth Parameters")

        st.markdown("**Phase 1**")
        col_p1a, col_p1b, col_p1c, col_p1d = st.columns(4)
        with col_p1a:
            phase1_start_month = st.number_input(
                "Phase 1 Start (Month)", 1, 240, 1)
        with col_p1b:
            phase1_end_month = st.number_input(
                "Phase 1 End (Month)", 1, 240, 6)
        with col_p1c:
            phase1_start_rate = st.number_input(
                "Phase 1 Start Rate (%)", 0.0, 100.0, 18.0)
        with col_p1d:
            phase1_end_rate = st.number_input(
                "Phase 1 End Rate (%)", 0.0, 100.0, 22.0)

        st.markdown("**Phase 2**")
        col_p2a, col_p2b, col_p2c, col_p2d = st.columns(4)
        with col_p2a:
            phase2_start_month = st.number_input(
                "Phase 2 Start (Month)", 1, 240, 7)
        with col_p2b:
            phase2_end_month = st.number_input(
                "Phase 2 End (Month)", 1, 240, 12)
        with col_p2c:
            phase2_start_rate = st.number_input(
                "Phase 2 Start Rate (%)", 0.0, 100.0, 22.0)
        with col_p2d:
            phase2_end_rate = st.number_input(
                "Phase 2 End Rate (%)", 0.0, 100.0, 28.0)

        st.markdown("**Phase 3**")
        col_p3a, col_p3b, col_p3c, col_p3d = st.columns(4)
        with col_p3a:
            phase3_start_month = st.number_input(
                "Phase 3 Start (Month)", 1, 240, 13)
        with col_p3b:
            phase3_end_month = st.number_input(
                "Phase 3 End (Month)", 1, 240, 18)
        with col_p3c:
            phase3_start_rate = st.number_input(
                "Phase 3 Start Rate (%)", 0.0, 100.0, 28.0)
        with col_p3d:
            phase3_end_rate = st.number_input(
                "Phase 3 End Rate (%)", 0.0, 100.0, 32.0)

        plateau_rate = st.number_input(
            "Plateau Rate (%) (Post Phase 3)", 0.0, 100.0, 5.0)

        # DELETE the old st.write(...Note...) line here

        max_month_for_curve = max(
            phase1_end_month, phase2_end_month, phase3_end_month) + 12
        months_for_curve = list(range(1, max_month_for_curve + 1))
        growth_values = []
        for mm in months_for_curve:
            val = get_phased_growth_rate(
                month_idx=mm - 1,
                phase1_start_month=phase1_start_month,
                phase1_end_month=phase1_end_month,
                phase1_start_rate=phase1_start_rate,
                phase1_end_rate=phase1_end_rate,
                phase2_start_month=phase2_start_month,
                phase2_end_month=phase2_end_month,
                phase2_start_rate=phase2_start_rate,
                phase2_end_rate=phase2_end_rate,
                phase3_start_month=phase3_start_month,
                phase3_end_month=phase3_end_month,
                phase3_start_rate=phase3_start_rate,
                phase3_end_rate=phase3_end_rate,
                plateau_rate=plateau_rate
            )
            growth_values.append(val)

        df_growth_curve = pd.DataFrame({
            "Month": months_for_curve,
            "Growth Rate (%)": growth_values
        })

        # REPLACE the old note line with these two new lines:
        st.line_chart(df_growth_curve.set_index("Month"))
        st.write(
            "**Note**: All these growth rates are monthly and reflect a fast-growing tech environment.")

        st.subheader("Plan Distribution & Details")
        st.write(
            "Enter fraction for each plan (must sum to 1.0) and define the plan costs/prices (monthly)."
        )
        col_basic, col_advanced, col_enterprise0 = st.columns(3)
        with col_basic:
            st.markdown("**Basic**")
            basic_fraction = st.slider("Basic Fraction", 0.0, 1.0, 0.3, 0.01)
            basic_setup_cost = st.number_input(
                "Basic Setup Fee (once-off)", 0.0, 1e12, 4800.0, step=100.0)
            basic_monthly_cost = st.number_input(
                "Basic Monthly COS", 0.0, 1e12, 2000.0, step=100.0)
            basic_monthly_price = st.number_input(
                "Basic Monthly Selling Price", 0.0, 1e12, 9555.0, step=100.0)

        with col_advanced:
            st.markdown("**Advanced**")
            advanced_fraction = st.slider(
                "Advanced Fraction", 0.0, 1.0, 0.3, 0.01)
            advanced_setup_cost = st.number_input(
                "Advanced Setup Fee (once-off)", 0.0, 1e12, 9600.0, step=100.0)
            advanced_monthly_cost = st.number_input(
                "Advanced Monthly COS", 0.0, 1e12, 5450.0, step=100.0)
            advanced_monthly_price = st.number_input(
                "Advanced Monthly Selling Price", 0.0, 1e12, 22509.0, step=100.0)

        with col_enterprise0:
            st.markdown("**Enterprise (0 additional assistants)**")
            enterprise0_fraction = st.slider(
                "Enterprise (0 asst) Fraction", 0.0, 1.0, 0.1, 0.01)
            enterprise0_setup_cost = st.number_input(
                "Enterprise (0 asst) Setup Fee (once-off)", 0.0, 1e12, 19200.0, step=100.0)
            enterprise0_monthly_cost = st.number_input(
                "Enterprise (0 asst) Monthly COS", 0.0, 1e12, 21560.0, step=100.0)
            enterprise0_monthly_price = st.number_input(
                "Enterprise (0 asst) Monthly Price", 0.0, 1e12, 90102.0, step=100.0)

        col_enterprise1, col_enterprise2, col_enterprise3 = st.columns(3)
        with col_enterprise1:
            st.markdown("**Enterprise (1 additional assistant)**")
            enterprise1_fraction = st.slider(
                "Enterprise (1 asst) Fraction", 0.0, 1.0, 0.1, 0.01)
            enterprise1_setup_cost = st.number_input(
                "Enterprise (1 asst) Setup Fee (once-off)", 0.0, 1e12, 20700.0, step=100.0)
            enterprise1_monthly_cost = st.number_input(
                "Enterprise (1 asst) Monthly COS", 0.0, 1e12, 25490.0, step=100.0)
            enterprise1_monthly_price = st.number_input(
                "Enterprise (1 asst) Monthly Price", 0.0, 1e12, 104821.0, step=100.0)

        with col_enterprise2:
            st.markdown("**Enterprise (2 additional assistants)**")
            enterprise2_fraction = st.slider(
                "Enterprise (2 asst) Fraction", 0.0, 1.0, 0.1, 0.01)
            enterprise2_setup_cost = st.number_input(
                "Enterprise (2 asst) Setup Fee (once-off)", 0.0, 1e12, 22200.0, step=100.0)
            enterprise2_monthly_cost = st.number_input(
                "Enterprise (2 asst) Monthly COS", 0.0, 1e12, 29420.0, step=100.0)
            enterprise2_monthly_price = st.number_input(
                "Enterprise (2 asst) Monthly Price", 0.0, 1e12, 119540.0, step=100.0)

        with col_enterprise3:
            st.markdown("**Enterprise (3 additional assistants)**")
            enterprise3_fraction = st.slider(
                "Enterprise (3 asst) Fraction", 0.0, 1.0, 0.1, 0.01)
            enterprise3_setup_cost = st.number_input(
                "Enterprise (3 asst) Setup Fee (once-off)", 0.0, 1e12, 23700.0, step=100.0)
            enterprise3_monthly_cost = st.number_input(
                "Enterprise (3 asst) Monthly COS", 0.0, 1e12, 33350.0, step=100.0)
            enterprise3_monthly_price = st.number_input(
                "Enterprise (3 asst) Monthly Price", 0.0, 1e12, 134259.0, step=100.0)

        total_fraction = (
            basic_fraction
            + advanced_fraction
            + enterprise0_fraction
            + enterprise1_fraction
            + enterprise2_fraction
            + enterprise3_fraction
        )
        if abs(total_fraction - 1.0) > 1e-9:
            st.warning("The total fraction for all plans does not sum to 1.0.")

        st.write("**Included Messages & Minutes Per Plan (for top-up calculations)**")
        if "config" not in st.session_state:
            st.session_state["config"] = {}
        if "included_quota_per_plan" not in st.session_state["config"]:
            st.session_state["config"]["included_quota_per_plan"] = {
                "Basic": (5000.0, 300.0),
                "Advanced": (10000.0, 500.0),
                "Enterprise_0": (60000.0, 6000.0),
                "Enterprise_1": (75000.0, 7500.0),
                "Enterprise_2": (90000.0, 9000.0),
                "Enterprise_3": (105000.0, 11500.0),
            }
        plan_names = [
            "Basic",
            "Advanced",
            "Enterprise_0",
            "Enterprise_1",
            "Enterprise_2",
            "Enterprise_3",
        ]
        included_quota_per_plan = st.session_state["config"]["included_quota_per_plan"]
        for plan in plan_names:
            col_m, col_min = st.columns(2)
            default_msgs, default_mins = included_quota_per_plan.get(
                plan, (5000.0, 300.0))
            with col_m:
                included_msgs = st.number_input(
                    f"{plan} Included Messages", 0.0, 1e10, default_msgs)
            with col_min:
                included_mins = st.number_input(
                    f"{plan} Included Minutes", 0.0, 1e10, default_mins)
            included_quota_per_plan[plan] = (included_msgs, included_mins)
        st.session_state["config"]["included_quota_per_plan"] = included_quota_per_plan

        st.subheader("Whitelabel Fees")
        basic_whitelabel_fee = st.number_input(
            "Basic Whitelabel Fee (once-off)", 0.0, 1e12, 12600.0, step=100.0)
        advanced_whitelabel_fee = st.number_input(
            "Advanced Whitelabel Fee (once-off)", 0.0, 1e12, 14560.0, step=100.0)
        st.info("Enterprise whitelabel is included as standard.")

        basic_whitelabel_frac = st.slider(
            "Fraction of Basic new users that purchase whitelabel", 0.0, 1.0, 0.3)
        advanced_whitelabel_frac = st.slider(
            "Fraction of Advanced new users that purchase whitelabel", 0.0, 1.0, 0.3)

        st.subheader("Top Ups")
        topup_users_pct = st.slider(
            "Fraction of users who buy top-ups", 0.0, 1.0, 0.3)
        topup_utilization_pct = st.slider(
            "Top-up usage fraction (relative to included usage)", 0.0, 2.0, 0.5)
        topup_cost_per_unit_msg = st.number_input(
            "Top-up Cost (R) per Message", 0.0, 100.0, 0.04)
        topup_price_per_unit_msg = st.number_input(
            "Top-up Price (R) per Message", 0.0, 100.0, 0.06)
        topup_cost_per_unit_min = st.number_input(
            "Top-up Cost (R) per Minute", 0.0, 100.0, 2.22)
        topup_price_per_unit_min = st.number_input(
            "Top-up Price (R) per Minute", 0.0, 100.0, 3.33)

        st.subheader("R&D Configuration")
        rd_investment_pct = st.slider(
            "Percentage of new funding allocated to R&D (%)", 0.0, 100.0, 10.0)
        rd_revenue_pct = st.slider(
            "Percentage of monthly revenue allocated to R&D (%)", 0.0, 100.0, 5.0)

        st.subheader("Funding Rounds")
        num_rounds = st.number_input("Number of Funding Rounds", 0, 5, 1)
        funding_rounds = []
        for i in range(num_rounds):
            colr1, colr2, colr3, colr4 = st.columns(4)
            with colr1:
                mth_trig = st.number_input(
                    f"Round {i+1} Month Trigger", -1, 240, (i+1)*3, key=f"fr_mt_{i}")
            with colr2:
                amt = st.number_input(
                    f"Round {i+1} Amount (R)", 0.0, 1e12, 10000000.0, step=10000.0, key=f"fr_amt_{i}")
            with colr3:
                fr_type = st.selectbox(
                    f"Round {i+1} Type", ["Equity", "Debt"], key=f"fr_type_{i}")
            with colr4:
                eq_pct = st.number_input(
                    f"Round {i+1} Equity % (if Equity)", 0.0, 100.0, 8.0, step=0.1, key=f"fr_eqpct_{i}")
            funding_rounds.append({
                "month_trigger": mth_trig,
                "amount": amt,
                "round_type": fr_type,
                "equity_pct": eq_pct
            })

        st.subheader("Fixed Staff Configuration (MONTHLY Salaries)")
        if "default_fixed_roles" not in st.session_state:
            st.session_state["default_fixed_roles"] = [
                {"name": "CEO", "headcount": 1,
                    "base_salary": 170000, "annual_raise": 0.10},
                {"name": "COO", "headcount": 1,
                    "base_salary": 150000, "annual_raise": 0.10},
                {"name": "CTO", "headcount": 1,
                    "base_salary": 150000, "annual_raise": 0.10},
                {"name": "Head of Finance", "headcount": 1,
                    "base_salary": 45000, "annual_raise": 0.10},
                {"name": "Head of Operations", "headcount": 1,
                    "base_salary": 45000, "annual_raise": 0.10},
                {"name": "Head of Partnership", "headcount": 1,
                    "base_salary": 45000, "annual_raise": 0.10},
                {"name": "Head of Dev", "headcount": 1,
                    "base_salary": 45000, "annual_raise": 0.10},
                {"name": "Head of Marketing", "headcount": 1,
                    "base_salary": 45000, "annual_raise": 0.10},
            ]
        default_fixed_roles = st.session_state["default_fixed_roles"]

        num_fixed_roles = st.number_input("Number of Fixed Staff Roles", 0, 50, len(
            default_fixed_roles), key="num_fixed_roles_key")
        fixed_staff_info = {}
        for i in range(num_fixed_roles):
            st.markdown(f"**Fixed Staff Role {i+1}**")
            colf1, colf2, colf3, colf4 = st.columns(4)

            if i < len(default_fixed_roles):
                role_dict = default_fixed_roles[i]
                init_name = role_dict["name"]
                init_hc = role_dict["headcount"]
                init_sal = role_dict["base_salary"]
                init_raise = role_dict["annual_raise"]
            else:
                init_name = f"Role_{i+1}"
                init_hc = 1
                init_sal = 30000.0
                init_raise = 0.05

            with colf1:
                role_name = st.text_input(
                    f"Role Name {i+1}", value=init_name, key=f"fs_role_{i}")
            with colf2:
                hc = st.number_input(
                    f"{role_name} Headcount", 0, 100, init_hc, key=f"fs_hc_{i}")
            with colf3:
                base_sal = st.number_input(
                    f"{role_name} Base Salary (MONTHLY, R)",
                    0.0,
                    1e12,
                    float(init_sal),
                    key=f"fs_bs_{i}"
                )
            with colf4:
                annual_raise = st.slider(
                    f"{role_name} Annual Raise",
                    0.0,
                    1.0,
                    init_raise,
                    0.01,
                    key=f"fs_ar_{i}"
                )

            fixed_staff_info[role_name] = {
                "headcount": hc,
                "base_salary": base_sal,
                "annual_raise": annual_raise,
                "capacity": 0
            }

        st.subheader(
            "Variable Staff (Onboarding / Maintenance) - MONTHLY Salaries")
        if "default_variable_roles" not in st.session_state:
            st.session_state["default_variable_roles"] = [
                {"name": "Onboarding Specialist", "headcount": 0,
                    "base_salary": 25000, "annual_raise": 0.05, "capacity": 100},
                {"name": "Technical Support Programmers", "headcount": 0,
                    "base_salary": 35000, "annual_raise": 0.05, "capacity": 100},
            ]
        default_variable_roles = st.session_state["default_variable_roles"]

        num_var_roles = st.number_input(
            "Number of Variable Staff Roles", 0, 10, len(default_variable_roles))
        variable_staff_info = {}
        for i in range(num_var_roles):
            st.markdown(f"**Variable Staff Role {i+1}**")
            colv1, colv2, colv3, colv4, colv5 = st.columns(5)

            if i < len(default_variable_roles):
                var_role_dict = default_variable_roles[i]
                init_var_name = var_role_dict["name"]
                init_var_hc = var_role_dict["headcount"]
                init_var_sal = var_role_dict["base_salary"]
                init_var_raise = var_role_dict["annual_raise"]
                init_var_cap = var_role_dict["capacity"]
            else:
                init_var_name = f"VarRole_{i+1}"
                init_var_hc = 0
                init_var_sal = 3000.0
                init_var_raise = 0.05
                init_var_cap = 160.0

            with colv1:
                role_name = st.text_input(
                    f"Var Role Name {i+1}", value=init_var_name, key=f"vs_role_{i}")
            with colv2:
                hc = st.number_input(
                    f"{role_name} Base Headcount", 0, 100, init_var_hc, key=f"vs_hc_{i}")
            with colv3:
                base_sal = st.number_input(
                    f"{role_name} Base Salary (MONTHLY, R)",
                    0.0,
                    1e12,
                    float(init_var_sal),
                    key=f"vs_bs_{i}"
                )
            with colv4:
                annual_raise = st.slider(
                    f"{role_name} Annual Raise",
                    0.0,
                    1.0,
                    init_var_raise,
                    0.01,
                    key=f"vs_ar_{i}"
                )
            with colv5:
                capacity = st.number_input(
                    f"{role_name} Capacity (hrs/mo)",
                    0.0,
                    1e5,
                    float(init_var_cap),
                    key=f"vs_cap_{i}"
                )

            variable_staff_info[role_name] = {
                "headcount": hc,
                "base_salary": base_sal,
                "annual_raise": annual_raise,
                "capacity": capacity
            }

        st.subheader("Operating Expenses / Overheads (Monthly)")
        if "default_overheads" not in st.session_state:
            st.session_state["default_overheads"] = [
                {"name": "Office Rental", "monthly_cost": 40000, "annual_increase": 5},
                {"name": "Communications", "monthly_cost": 30000, "annual_increase": 5},
                {"name": "Administration", "monthly_cost": 20000, "annual_increase": 5},
                {"name": "Insurance", "monthly_cost": 15000, "annual_increase": 5},
                {"name": "Logistics", "monthly_cost": 50000, "annual_increase": 5},
                {"name": "Transport", "monthly_cost": 10000, "annual_increase": 5},
                {"name": "Legal", "monthly_cost": 55000, "annual_increase": 5},
                {"name": "Sundry", "monthly_cost": 15000, "annual_increase": 5},
                {"name": "Software Subscriptions",
                    "monthly_cost": 20000, "annual_increase": 5},
                {"name": "Software", "monthly_cost": 20000, "annual_increase": 5}
            ]
        default_overheads = st.session_state["default_overheads"]

        num_overheads = st.number_input(
            "Number of Overhead Items", 0, 20, len(default_overheads))
        overhead_items = []
        for i in range(num_overheads):
            st.markdown(f"**Overhead Item {i+1}**")
            col_o1, col_o2, col_o3 = st.columns(3)

            if i < len(default_overheads):
                oh_default = default_overheads[i]
                init_oh_name = oh_default["name"]
                init_monthly_cost = oh_default["monthly_cost"]
                init_annual_inc = oh_default["annual_increase"]
            else:
                init_oh_name = f"Overhead_{i+1}"
                init_monthly_cost = 2000.0
                init_annual_inc = 5.0

            with col_o1:
                oh_name = st.text_input(
                    f"Overhead Name {i+1}", value=init_oh_name, key=f"oh_name_{i}")
            with col_o2:
                monthly_cost = st.number_input(
                    f"{oh_name} Monthly Cost (R)",
                    0.0,
                    1e12,
                    float(init_monthly_cost),
                    key=f"oh_mc_{i}"
                )
            with col_o3:
                annual_inc = st.number_input(
                    f"{oh_name} Annual Increase (%)",
                    0.0,
                    100.0,
                    float(init_annual_inc),
                    key=f"oh_inc_{i}"
                )

            overhead_items.append({
                "name": oh_name,
                "monthly_cost": monthly_cost,
                "annual_increase": annual_inc
            })

        st.subheader("Marketing")
        mk_mode = st.selectbox("Marketing Mode", ["fixed", "percentage"])
        if mk_mode == "fixed":
            mk_budget = st.number_input(
                "Fixed Marketing (monthly R)", 0, 1_000_000, 120000)
            mk_pct = st.slider(
                "Marketing % of Revenue (used if revenue > 1.2x fixed)", 0.0, 100.0, 10.0)
        else:
            mk_pct = st.slider("Marketing % of Revenue", 0.0, 100.0, 5.0)
            mk_budget = 0.0

        st.subheader("Hardware/Software cost per staff (Monthly)")
        hardware_cost_per_employee = st.number_input(
            "Hardware cost per employee (monthly R)", 0.0, 1e12, 50000.0, step=500.0)

        st.subheader("Initial Loan (Optional)")
        enable_loan = st.checkbox("Enable an Initial Loan?")
        if enable_loan:
            loan_amt = st.number_input(
                "Initial Loan Amount (R)", 0.0, 1e12, 1000000.0)
            loan_interest = st.number_input(
                "Annual Loan Interest Rate (%)", 0.0, 100.0, 5.0)
            payback_strat = st.selectbox("Payback Strategy", [
                                         "none", "fixed", "Percentage of Profit", "Percentage of Profit + Lump", "Lump + Timeline"])
            payback_start_m = st.number_input("Payback Start Month", 1, 240, 1)
            payback_end_date = None
            if payback_strat == "Lump + Timeline":
                payback_end_date = st.date_input(
                    "Loan Payback End Date", value=date.today() + relativedelta(months=24))
            fixed_amt = 0.0
            perc_amt = 0.0
            lumpsum_amt = 0.0
            if payback_strat == "fixed":
                fixed_amt = st.number_input(
                    "Fixed Payment Amount (R/month)", 0.0, 1e12, 50000.0)
            elif payback_strat == "Percentage of Profit":
                perc_amt = st.number_input(
                    "Percent of Profit to Pay Each Month (%)", 0.0, 100.0, 20.0)
            elif payback_strat == "Percentage of Profit + Lump":
                lumpsum_amt = st.number_input(
                    "Initial Lump Sum Payment (R)", 0.0, 1e12, 200000.0)
                perc_amt = st.number_input(
                    "Percent of Profit to Pay Each Month (%)", 0.0, 100.0, 20.0)
            elif payback_strat == "Lump + Timeline":
                lumpsum_amt = st.number_input(
                    "Lump Sum Payment (at Payback Start)", 0.0, 1e12, 200000.0)
        else:
            loan_amt = 0
            loan_interest = 0
            payback_strat = "none"
            payback_start_m = 1
            payback_end_date = None
            fixed_amt = 0
            perc_amt = 0
            lumpsum_amt = 0

        st.subheader("Yearly Decrease in Hours")
        annual_onboarding_decr_pct = st.slider(
            "Yearly Onboarding Hours Decrease (%)", 0.0, 100.0, 50.0)
        annual_maintenance_decr_pct = st.slider(
            "Yearly Maintenance Hours Decrease (%)", 0.0, 100.0, 50.0)

        onboarding_hours_per_plan = {
            "Basic": 12,
            "Advanced": 16,
            "Enterprise_0": 20,
            "Enterprise_1": 20,
            "Enterprise_2": 20,
            "Enterprise_3": 20
        }
        monthly_maintenance_hrs_per_plan = {
            "Basic": 4,
            "Advanced": 5,
            "Enterprise_0": 6,
            "Enterprise_1": 6,
            "Enterprise_2": 6,
            "Enterprise_3": 6
        }
        onboarding_decrease_factors_per_plan = {
            "Basic": 1 - annual_onboarding_decr_pct/100.0,
            "Advanced": 1 - annual_onboarding_decr_pct/100.0,
            "Enterprise_0": 1 - annual_onboarding_decr_pct/100.0,
            "Enterprise_1": 1 - annual_onboarding_decr_pct/100.0,
            "Enterprise_2": 1 - annual_onboarding_decr_pct/100.0,
            "Enterprise_3": 1 - annual_onboarding_decr_pct/100.0
        }
        maintenance_decrease_factors_per_plan = {
            "Basic": 1 - annual_maintenance_decr_pct/100.0,
            "Advanced": 1 - annual_maintenance_decr_pct/100.0,
            "Enterprise_0": 1 - annual_maintenance_decr_pct/100.0,
            "Enterprise_1": 1 - annual_maintenance_decr_pct/100.0,
            "Enterprise_2": 1 - annual_maintenance_decr_pct/100.0,
            "Enterprise_3": 1 - annual_maintenance_decr_pct/100.0
        }

        client_plan_distribution = {
            "Basic": basic_fraction,
            "Advanced": advanced_fraction,
            "Enterprise_0": enterprise0_fraction,
            "Enterprise_1": enterprise1_fraction,
            "Enterprise_2": enterprise2_fraction,
            "Enterprise_3": enterprise3_fraction
        }

        plans_info = {
            "Basic": {
                "monthly_cos": basic_monthly_cost,
                "setup_cos": 0.0,
                "monthly_selling_price": basic_monthly_price,
                "setup_selling_price": basic_setup_cost + basic_whitelabel_fee
            },
            "Advanced": {
                "monthly_cos": advanced_monthly_cost,
                "setup_cos": 0.0,
                "monthly_selling_price": advanced_monthly_price,
                "setup_selling_price": advanced_setup_cost + advanced_whitelabel_fee
            },
            "Enterprise_0": {
                "monthly_cos": enterprise0_monthly_cost,
                "setup_cos": 0.0,
                "monthly_selling_price": enterprise0_monthly_price,
                "setup_selling_price": enterprise0_setup_cost
            },
            "Enterprise_1": {
                "monthly_cos": enterprise1_monthly_cost,
                "setup_cos": 0.0,
                "monthly_selling_price": enterprise1_monthly_price,
                "setup_selling_price": enterprise1_setup_cost
            },
            "Enterprise_2": {
                "monthly_cos": enterprise2_monthly_cost,
                "setup_cos": 0.0,
                "monthly_selling_price": enterprise2_monthly_price,
                "setup_selling_price": enterprise2_setup_cost
            },
            "Enterprise_3": {
                "monthly_cos": enterprise3_monthly_cost,
                "setup_cos": 0.0,
                "monthly_selling_price": enterprise3_monthly_price,
                "setup_selling_price": enterprise3_setup_cost
            },
        }

        st.session_state["config"] = {
            "start_date": start_date,
            "end_date": end_date,
            "frequency": freq,
            "initial_cash": initial_cash,
            "initial_clients": initial_clients,
            "churn_rate_annual": churn_rate_annual,
            "phase1_start_month": phase1_start_month,
            "phase1_end_month": phase1_end_month,
            "phase1_start_rate": phase1_start_rate,
            "phase1_end_rate": phase1_end_rate,
            "phase2_start_month": phase2_start_month,
            "phase2_end_month": phase2_end_month,
            "phase2_start_rate": phase2_start_rate,
            "phase2_end_rate": phase2_end_rate,
            "phase3_start_month": phase3_start_month,
            "phase3_end_month": phase3_end_month,
            "phase3_start_rate": phase3_start_rate,
            "phase3_end_rate": phase3_end_rate,
            "plateau_rate": plateau_rate,
            "plans_info": plans_info,
            "client_plan_distribution": client_plan_distribution,
            "topup_users_pct": topup_users_pct,
            "topup_utilization_pct": topup_utilization_pct,
            "topup_cost_per_unit_msg": topup_cost_per_unit_msg,
            "topup_price_per_unit_msg": topup_price_per_unit_msg,
            "topup_cost_per_unit_min": topup_cost_per_unit_min,
            "topup_price_per_unit_min": topup_price_per_unit_min,
            "included_quota_per_plan": included_quota_per_plan,
            "funding_rounds": funding_rounds,
            "rd_investment_pct": rd_investment_pct,
            "rd_revenue_pct": rd_revenue_pct,
            "allocate_investment_across_expenses": False,
            "fixed_staff_info": fixed_staff_info,
            "variable_staff_info": variable_staff_info,
            "onboarding_hours_per_plan": onboarding_hours_per_plan,
            "monthly_maintenance_hrs_per_plan": monthly_maintenance_hrs_per_plan,
            "onboarding_decrease_factors_per_plan": onboarding_decrease_factors_per_plan,
            "maintenance_decrease_factors_per_plan": maintenance_decrease_factors_per_plan,
            "overhead_items": overhead_items,
            "marketing_mode": mk_mode,
            "marketing_budget": mk_budget,
            "marketing_pct_of_revenue": mk_pct,
            "hardware_cost_per_employee": hardware_cost_per_employee,
            "enable_loan": enable_loan,
            "initial_loan_amount": loan_amt,
            "loan_interest_rate_annual": loan_interest,
            "loan_payback_strategy": payback_strat,
            "loan_payback_start_month": payback_start_m,
            "loan_payback_end_date": payback_end_date,
            "loan_fixed_amount": fixed_amt,
            "loan_percent_of_profit": perc_amt,
            "loan_lump_sum": lumpsum_amt,
            "basic_whitelabel_fee": basic_whitelabel_fee,
            "advanced_whitelabel_fee": advanced_whitelabel_fee,
            "basic_whitelabel_frac": basic_whitelabel_frac,
            "advanced_whitelabel_frac": advanced_whitelabel_frac
        }

        st.subheader("Save and Load Configurations")

        if not os.path.exists("investor-configs"):
            os.makedirs("investor-configs")

        col_save, col_load = st.columns(2)

        with col_save:
            st.markdown("**Save Configuration**")
            save_name = st.text_input(
                "Enter configuration name", key="save_name")
            if st.button("Save Configuration"):
                if save_name.strip() == "":
                    st.error("Please enter a valid configuration name.")
                else:
                    save_path = os.path.join(
                        "investor-configs", f"{save_name}.json")
                    serializable_config = serialize_config(
                        st.session_state["config"])
                    with open(save_path, "w") as f:
                        json.dump(serializable_config, f, indent=4)
                    st.success(f"Configuration '{
                               save_name}' saved successfully.")

        with col_load:
            st.markdown("**Load Configuration**")
            config_files = [
                f[:-5] for f in os.listdir("investor-configs") if f.endswith(".json")]
            if config_files:
                selected_config = st.selectbox(
                    "Select a configuration to load", config_files, key="load_select")
                if st.button("Load Configuration"):
                    load_path = os.path.join(
                        "investor-configs", f"{selected_config}.json")
                    try:
                        with open(load_path, "r") as f:
                            loaded_config = json.load(f)
                        deserialized_config = deserialize_config(loaded_config)
                        st.session_state["config"] = deserialized_config
                        st.success(f"Configuration '{
                                   selected_config}' loaded successfully.")
                        try:
                            st.experimental_rerun()
                        except AttributeError:
                            st.warning(
                                "Please manually refresh the page to apply changes.")
                    except json.JSONDecodeError as e:
                        st.error(f"Error loading JSON file: {e}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
            else:
                st.info("No saved configurations found.")

        st.success(
            "Configuration saved. Go to the 'Reseller', 'Referrals & Investors' or 'Results' tab to continue.")

    with tab_reseller:
        st.header("Partners")
        st.write("Use this section to calculate additional revenue potential from a reseller partner, configure multiple referral sources, and track additional investors.")

        st.subheader("Reseller Configuration & Potential")
        reseller_client_base = st.number_input(
            "Reseller's Total Client Base", 0, 1_000_000, 250000)
        reseller_pct_to_capture = st.slider(
            "Fraction of Reseller Base we can capture", 0.0, 1.0, 0.01)
        reseller_profit_share_pct = st.slider(
            "Profit Share to Reseller (%)", 0.0, 1.0, 0.3)

        if st.button("Generate Reseller & Referral Tables"):
            cfg = st.session_state.get("config", None)
            if not cfg:
                st.warning(
                    "No main configuration found. Please configure in 'Inputs' tab first."
                )
            else:
                def calculate_reseller_projection(cfg, reseller_client_base, reseller_pct_to_capture, reseller_profit_share_pct):
                    from copy import deepcopy
                    local_cfg = deepcopy(cfg)
                    captured_clients = int(
                        round(reseller_client_base * reseller_pct_to_capture))
                    local_cfg["initial_clients"] = captured_clients
                    df_res = generate_projection(
                        start_date=local_cfg["start_date"],
                        end_date=local_cfg["end_date"],
                        frequency=local_cfg["frequency"],
                        initial_cash=local_cfg["initial_cash"],
                        inflation_rate=5.0,
                        phase1_start_month=local_cfg["phase1_start_month"],
                        phase1_end_month=local_cfg["phase1_end_month"],
                        phase1_start_rate=local_cfg["phase1_start_rate"],
                        phase1_end_rate=local_cfg["phase1_end_rate"],
                        phase2_start_month=local_cfg["phase2_start_month"],
                        phase2_end_month=local_cfg["phase2_end_month"],
                        phase2_start_rate=local_cfg["phase2_start_rate"],
                        phase2_end_rate=local_cfg["phase2_end_rate"],
                        phase3_start_month=local_cfg["phase3_start_month"],
                        phase3_end_month=local_cfg["phase3_end_month"],
                        phase3_start_rate=local_cfg["phase3_start_rate"],
                        phase3_end_rate=local_cfg["phase3_end_rate"],
                        plateau_rate=local_cfg["plateau_rate"],
                        initial_clients=local_cfg["initial_clients"],
                        churn_rate_annual=local_cfg["churn_rate_annual"],
                        client_plan_distribution=local_cfg["client_plan_distribution"],
                        plans_info=local_cfg["plans_info"],
                        topup_users_pct=local_cfg["topup_users_pct"],
                        topup_utilization_pct=local_cfg["topup_utilization_pct"],
                        topup_cost_per_unit_msg=local_cfg["topup_cost_per_unit_msg"],
                        topup_price_per_unit_msg=local_cfg["topup_price_per_unit_msg"],
                        topup_cost_per_unit_min=local_cfg["topup_cost_per_unit_min"],
                        topup_price_per_unit_min=local_cfg["topup_price_per_unit_min"],
                        included_quota_per_plan=local_cfg["included_quota_per_plan"],
                        rd_investment_pct=local_cfg["rd_investment_pct"],
                        rd_revenue_pct=local_cfg["rd_revenue_pct"],
                        funding_rounds=local_cfg["funding_rounds"],
                        allocate_new_investment_across_expenses=local_cfg[
                            "allocate_investment_across_expenses"
                        ],
                        fixed_staff_info=local_cfg["fixed_staff_info"],
                        variable_staff_info=local_cfg["variable_staff_info"],
                        onboarding_hours_per_plan=local_cfg["onboarding_hours_per_plan"],
                        monthly_maintenance_hrs_per_plan=local_cfg["monthly_maintenance_hrs_per_plan"],
                        onboarding_decrease_factors_per_plan=local_cfg[
                            "onboarding_decrease_factors_per_plan"
                        ],
                        maintenance_decrease_factors_per_plan=local_cfg[
                            "maintenance_decrease_factors_per_plan"
                        ],
                        overhead_items=local_cfg["overhead_items"],
                        marketing_mode=local_cfg["marketing_mode"],
                        marketing_budget=local_cfg["marketing_budget"],
                        marketing_pct_of_revenue=local_cfg["marketing_pct_of_revenue"],
                        hardware_cost_per_employee=local_cfg["hardware_cost_per_employee"],
                        enable_initial_loan=local_cfg["enable_loan"],
                        initial_loan_amount=local_cfg["initial_loan_amount"],
                        loan_interest_rate_annual=local_cfg["loan_interest_rate_annual"],
                        loan_payback_strategy=local_cfg["loan_payback_strategy"],
                        loan_payback_start_month=local_cfg["loan_payback_start_month"],
                        loan_payback_end_date=local_cfg["loan_payback_end_date"],
                        loan_fixed_amount=local_cfg["loan_fixed_amount"],
                        loan_percent_of_profit=local_cfg["loan_percent_of_profit"],
                        loan_lump_sum=local_cfg["loan_lump_sum"],
                    )
                    if df_res.empty:
                        return df_res
                    df_res["Reseller_Profit_Share"] = df_res["Profit_NetIncome"] * \
                        reseller_profit_share_pct
                    df_res["Net_After_Reseller"] = df_res["Profit_NetIncome"] - \
                        df_res["Reseller_Profit_Share"]
                    return df_res

                df_reseller_proj = calculate_reseller_projection(
                    cfg, reseller_client_base, reseller_pct_to_capture, reseller_profit_share_pct
                )

                if df_reseller_proj.empty:
                    st.warning("No reseller projection data generated.")
                else:
                    # PARTNER-ONLY TABLE EXCLUDING OUR OPEX
                    df_partner_alone = df_reseller_proj[
                        [
                            "Time_Label",
                            "Revenue_Total",
                            "COS_Total",
                            "Profit_GrossProfit",
                            "Profit_NetIncome",
                            "Reseller_Profit_Share",
                            "Net_After_Reseller",
                            "Cost_Overheads",
                        ]
                    ].copy()

                    # Create a column to show partner net WITHOUT our overhead cost
                    df_partner_alone["Partner_Net_Excl_OurOPEX"] = (
                        df_partner_alone["Profit_NetIncome"] +
                        df_partner_alone["Cost_Overheads"]
                    )

                    st.subheader("Partner-Only Table (No OPEX Included)")
                    numeric_cols_partner_alone = df_partner_alone.select_dtypes(
                        include=[np.number]).columns
                    styled_partner_alone = (
                        df_partner_alone.style.format(
                            subset=numeric_cols_partner_alone,
                            formatter="{:,.2f}"
                        )
                        .background_gradient(cmap="Greys", subset=["Revenue_Total"])
                        .background_gradient(cmap="Greys", subset=["COS_Total"])
                        .background_gradient(cmap="Greys", subset=["Profit_GrossProfit"])
                        .background_gradient(cmap="Greys", subset=["Profit_NetIncome"])
                        .background_gradient(cmap="Greys", subset=["Reseller_Profit_Share"])
                        .background_gradient(cmap="Greys", subset=["Net_After_Reseller"])
                        .background_gradient(cmap="Greys", subset=["Partner_Net_Excl_OurOPEX"])
                    )
                    st.dataframe(styled_partner_alone)

                    # Always show partner alone table; optionally show combined
                    include_partner = st.checkbox(
                        "Include Partner Figures With Ours?")
                    st.subheader("Partner Table (Included In Main)")

                    if include_partner:
                        combined = df_reseller_proj.copy()
                        combined["Total_Cost"] = combined["COS_Total"] + \
                            combined["Cost_OperatingExpenses"]
                        combined["Total_Income"] = combined["Revenue_Total"]
                        combined["Total_Net_Profit"] = combined["Profit_NetIncome"]

                        numeric_cols_combined = combined.select_dtypes(
                            include=[np.number]).columns
                        st.dataframe(
                            combined.style.format(
                                subset=numeric_cols_combined,
                                formatter="{:,.2f}"
                            )
                            .background_gradient(cmap="Greys", subset=["Total_Cost"])
                            .background_gradient(cmap="Greys", subset=["Total_Income"])
                            .background_gradient(cmap="Greys", subset=["Total_Net_Profit"])
                            .background_gradient(cmap="Greys", subset=["Reseller_Profit_Share"])
                            .background_gradient(cmap="Greys", subset=["Net_After_Reseller"])
                        )
                    else:
                        st.info(
                            "Partner figures are currently excluded from our main table.")

                    st.info(
                        "This forecast table incorporates staff, overheads, marketing, hardware, R&D, and loan costs, then applies reseller profit share."
                    )

    with tab2:
        st.header("Forecast Results")
        cfg = st.session_state.get("config", None)
        if not cfg:
            st.info(
                "No configuration found. Please configure in the 'Inputs' tab first.")
        else:
            original_generate_projection = generate_projection

            def generate_projection_with_product_breakdown(
                start_date=None,
                end_date=None,
                frequency="Month",
                initial_cash=500000.0,
                inflation_rate=5.0,
                phase1_start_month=1,
                phase1_end_month=3,
                phase1_start_rate=3.0,
                phase1_end_rate=5.0,
                phase2_start_month=4,
                phase2_end_month=8,
                phase2_start_rate=6.0,
                phase2_end_rate=15.0,
                phase3_start_month=9,
                phase3_end_month=12,
                phase3_start_rate=16.0,
                phase3_end_rate=25.0,
                plateau_rate=10.0,
                initial_clients=10,
                churn_rate_annual=10.0,
                client_plan_distribution=None,
                plans_info=None,
                topup_users_pct=0.0,
                topup_utilization_pct=0.0,
                topup_cost_per_unit_msg=0.05,
                topup_price_per_unit_msg=0.08,
                topup_cost_per_unit_min=0.05,
                topup_price_per_unit_min=0.08,
                included_quota_per_plan=None,
                rd_investment_pct=0.0,
                rd_revenue_pct=0.0,
                funding_rounds=None,
                allocate_new_investment_across_expenses=False,
                fixed_staff_info=None,
                variable_staff_info=None,
                onboarding_hours_per_plan=None,
                monthly_maintenance_hrs_per_plan=None,
                onboarding_decrease_factors_per_plan=None,
                maintenance_decrease_factors_per_plan=None,
                overhead_items=None,
                marketing_mode="fixed",
                marketing_budget=120000.0,
                marketing_pct_of_revenue=0.0,
                hardware_cost_per_employee=0.0,
                enable_initial_loan=False,
                initial_loan_amount=0.0,
                loan_interest_rate_annual=0.0,
                loan_payback_strategy="none",
                loan_payback_start_month=1,
                loan_payback_end_date=None,
                loan_fixed_amount=0.0,
                loan_percent_of_profit=0.0,
                loan_lump_sum=0.0,
                lump_sum_paid=False
            ):
                df_result = original_generate_projection(
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    initial_cash=initial_cash,
                    inflation_rate=inflation_rate,
                    phase1_start_month=phase1_start_month,
                    phase1_end_month=phase1_end_month,
                    phase1_start_rate=phase1_start_rate,
                    phase1_end_rate=phase1_end_rate,
                    phase2_start_month=phase2_start_month,
                    phase2_end_month=phase2_end_month,
                    phase2_start_rate=phase2_start_rate,
                    phase2_end_rate=phase2_end_rate,
                    phase3_start_month=phase3_start_month,
                    phase3_end_month=phase3_end_month,
                    phase3_start_rate=phase3_start_rate,
                    phase3_end_rate=phase3_end_rate,
                    plateau_rate=plateau_rate,
                    initial_clients=initial_clients,
                    churn_rate_annual=churn_rate_annual,
                    client_plan_distribution=client_plan_distribution,
                    plans_info=plans_info,
                    topup_users_pct=topup_users_pct,
                    topup_utilization_pct=topup_utilization_pct,
                    topup_cost_per_unit_msg=topup_cost_per_unit_msg,
                    topup_price_per_unit_msg=topup_price_per_unit_msg,
                    topup_cost_per_unit_min=topup_cost_per_unit_min,
                    topup_price_per_unit_min=topup_price_per_unit_min,
                    included_quota_per_plan=included_quota_per_plan,
                    rd_investment_pct=rd_investment_pct,
                    rd_revenue_pct=rd_revenue_pct,
                    funding_rounds=funding_rounds,
                    allocate_new_investment_across_expenses=allocate_new_investment_across_expenses,
                    fixed_staff_info=fixed_staff_info,
                    variable_staff_info=variable_staff_info,
                    onboarding_hours_per_plan=onboarding_hours_per_plan,
                    monthly_maintenance_hrs_per_plan=monthly_maintenance_hrs_per_plan,
                    onboarding_decrease_factors_per_plan=onboarding_decrease_factors_per_plan,
                    maintenance_decrease_factors_per_plan=maintenance_decrease_factors_per_plan,
                    overhead_items=overhead_items,
                    marketing_mode=marketing_mode,
                    marketing_budget=marketing_budget,
                    marketing_pct_of_revenue=marketing_pct_of_revenue,
                    hardware_cost_per_employee=hardware_cost_per_employee,
                    enable_initial_loan=enable_initial_loan,
                    initial_loan_amount=initial_loan_amount,
                    loan_interest_rate_annual=loan_interest_rate_annual,
                    loan_payback_strategy=loan_payback_strategy,
                    loan_payback_start_month=loan_payback_start_month,
                    loan_payback_end_date=loan_payback_end_date,
                    loan_fixed_amount=loan_fixed_amount,
                    loan_percent_of_profit=loan_percent_of_profit,
                    loan_lump_sum=loan_lump_sum,
                    lump_sum_paid=lump_sum_paid
                )

                if plans_info and not df_result.empty:
                    for plan_n in plans_info.keys():
                        df_result[f"Revenue_{plan_n}"] = 0.0
                        df_result[f"COS_{plan_n}"] = 0.0

                    for idx in range(len(df_result)):
                        rev_total = df_result.loc[idx, "Revenue_Total"]
                        cos_total = df_result.loc[idx, "COS_Total"]
                        if rev_total != 0 and cos_total != 0:
                            for plan_n, frac in client_plan_distribution.items():
                                df_result.loc[idx, f"Revenue_{
                                    plan_n}"] = rev_total * frac
                                df_result.loc[idx, f"COS_{
                                    plan_n}"] = cos_total * frac

                return df_result

            df_forecast = generate_projection_with_product_breakdown(
                start_date=cfg["start_date"],
                end_date=cfg["end_date"],
                frequency=cfg["frequency"],
                initial_cash=cfg["initial_cash"],
                inflation_rate=5.0,
                phase1_start_month=cfg["phase1_start_month"],
                phase1_end_month=cfg["phase1_end_month"],
                phase1_start_rate=cfg["phase1_start_rate"],
                phase1_end_rate=cfg["phase1_end_rate"],
                phase2_start_month=cfg["phase2_start_month"],
                phase2_end_month=cfg["phase2_end_month"],
                phase2_start_rate=cfg["phase2_start_rate"],
                phase2_end_rate=cfg["phase2_end_rate"],
                phase3_start_month=cfg["phase3_start_month"],
                phase3_end_month=cfg["phase3_end_month"],
                phase3_start_rate=cfg["phase3_start_rate"],
                phase3_end_rate=cfg["phase3_end_rate"],
                plateau_rate=cfg["plateau_rate"],
                initial_clients=cfg["initial_clients"],
                churn_rate_annual=cfg["churn_rate_annual"],
                client_plan_distribution=cfg["client_plan_distribution"],
                plans_info=cfg["plans_info"],
                topup_users_pct=cfg["topup_users_pct"],
                topup_utilization_pct=cfg["topup_utilization_pct"],
                topup_cost_per_unit_msg=cfg["topup_cost_per_unit_msg"],
                topup_price_per_unit_msg=cfg["topup_price_per_unit_msg"],
                topup_cost_per_unit_min=cfg["topup_cost_per_unit_min"],
                topup_price_per_unit_min=cfg["topup_price_per_unit_min"],
                included_quota_per_plan=cfg["included_quota_per_plan"],
                rd_investment_pct=cfg["rd_investment_pct"],
                rd_revenue_pct=cfg["rd_revenue_pct"],
                funding_rounds=cfg["funding_rounds"],
                allocate_new_investment_across_expenses=cfg["allocate_investment_across_expenses"],
                fixed_staff_info=cfg["fixed_staff_info"],
                variable_staff_info=cfg["variable_staff_info"],
                onboarding_hours_per_plan=cfg["onboarding_hours_per_plan"],
                monthly_maintenance_hrs_per_plan=cfg["monthly_maintenance_hrs_per_plan"],
                onboarding_decrease_factors_per_plan=cfg["onboarding_decrease_factors_per_plan"],
                maintenance_decrease_factors_per_plan=cfg["maintenance_decrease_factors_per_plan"],
                overhead_items=cfg["overhead_items"],
                marketing_mode=cfg["marketing_mode"],
                marketing_budget=cfg["marketing_budget"],
                marketing_pct_of_revenue=cfg["marketing_pct_of_revenue"],
                hardware_cost_per_employee=cfg["hardware_cost_per_employee"],
                enable_initial_loan=cfg["enable_loan"],
                initial_loan_amount=cfg["initial_loan_amount"],
                loan_interest_rate_annual=cfg["loan_interest_rate_annual"],
                loan_payback_strategy=cfg["loan_payback_strategy"],
                loan_payback_start_month=cfg["loan_payback_start_month"],
                loan_payback_end_date=cfg["loan_payback_end_date"],
                loan_fixed_amount=cfg["loan_fixed_amount"],
                loan_percent_of_profit=cfg["loan_percent_of_profit"],
                loan_lump_sum=cfg["loan_lump_sum"],
            )

            df_final, metrics = compute_saas_metrics(
                df_forecast, cfg["start_date"], cfg["end_date"]
            )

            if not df_final.empty:
                df_final["Revenue_Whitelabel"] = 0.0
                basic_wf = cfg.get("basic_whitelabel_fee", 0.0)
                advanced_wf = cfg.get("advanced_whitelabel_fee", 0.0)
                basic_whitelabel_frac = cfg.get("basic_whitelabel_frac", 0.0)
                advanced_whitelabel_frac = cfg.get(
                    "advanced_whitelabel_frac", 0.0)

                basic_frac = cfg["client_plan_distribution"].get("Basic", 0.0)
                advanced_frac = cfg["client_plan_distribution"].get(
                    "Advanced", 0.0)

                for i in range(len(df_final)):
                    new_c = df_final.loc[i, "Clients_New"]
                    basic_new = new_c * basic_frac
                    advanced_new = new_c * advanced_frac
                    basic_whitelabel_buyers = basic_new * basic_whitelabel_frac
                    advanced_whitelabel_buyers = advanced_new * advanced_whitelabel_frac
                    total_whitelabel = (
                        basic_wf * basic_whitelabel_buyers
                        + advanced_wf * advanced_whitelabel_buyers
                    )
                    df_final.loc[i, "Revenue_Whitelabel"] = total_whitelabel
                    df_final.loc[i, "Revenue_Total"] += total_whitelabel

                # INSERT these lines right before st.subheader("Forecast Table"):
                end_cols = ["COS_Total", "Revenue_Total", "Profit_NetIncome"]
                end_cols = [c for c in end_cols if c in df_final.columns]
                other_cols = [c for c in df_final.columns if c not in end_cols]
                df_final = df_final[other_cols + end_cols]

                st.subheader("Forecast Table")
                numeric_cols = df_final.select_dtypes(
                    include=[np.number]).columns
                st.dataframe(df_final.style.format(
                    subset=numeric_cols,
                    formatter="{:,.2f}"
                ))

                sum_revenue = df_final["Revenue_Total"].sum()
                sum_ebitda = df_final["Profit_EBITDA"].sum()
                sum_netinc = df_final["Profit_NetIncome"].sum()

                st.write(f"**Total Revenue:** R {sum_revenue:,.2f}")
                st.write(f"**Total EBITDA:**  R {sum_ebitda:,.2f}")
                st.write(f"**Total Net Income:** R {sum_netinc:,.2f}")

                c1, c2, = st.columns(2)
                with c1:
                    cagr_val = metrics.get("CAGR_Revenue", 0.0)
                    st.metric("CAGR (Revenue)", f"{cagr_val:,.2f}%")
                with c2:
                    irr_val = metrics.get("IRR", None)
                    if irr_val is not None:
                        st.metric("IRR", f"{irr_val:,.2f}%")
                    else:
                        st.metric("IRR", "N/A")

                st.download_button("Download Forecast CSV",
                                   data=df_final.to_csv(index=False),
                                   file_name="forecast_results.csv",
                                   mime="text/csv")

                st.subheader("Yearly Breakdown")
                df_final["Total_Staff"] = df_final["Staff_Fixed"] + \
                    df_final["Staff_Variable"]
                for plan_n, fraction in cfg["client_plan_distribution"].items():
                    df_final[f"{
                        plan_n}_SubscriptionsSold"] = df_final["Clients_New"] * fraction
                df_final["ParsedDate"] = pd.to_datetime(df_final["ParsedDate"])
                df_final["Year"] = df_final["ParsedDate"].dt.year
                df_final["Total_Staff"] = df_final["Staff_Fixed"] + \
                    df_final["Staff_Variable"]
                for plan_n, fraction in cfg["client_plan_distribution"].items():
                    df_final[f"{
                        plan_n}_SubscriptionsSold"] = df_final["Clients_New"] * fraction
                df_final["Year"] = df_final["ParsedDate"].dt.year

                group_columns = {
                    "Revenue_Total": "sum",
                    "Cost_OperatingExpenses": "sum",
                    "Total_Staff": "mean",
                    "Clients_New": "sum"
                }
                for plan_n in cfg["client_plan_distribution"].keys():
                    group_columns[f"{plan_n}_SubscriptionsSold"] = "sum"

                df_yearly = df_final.groupby(
                    "Year", as_index=False).agg(group_columns)
                df_yearly = df_yearly.sort_values(
                    by="Year").reset_index(drop=True)
                df_yearly["OpEx_Increase"] = df_yearly["Cost_OperatingExpenses"].diff().fillna(
                    0)
                df_yearly["OpEx_Increase_%"] = (
                    (df_yearly["OpEx_Increase"] /
                     df_yearly["Cost_OperatingExpenses"].shift(1).replace(0, np.nan)) * 100
                ).fillna(0)
                df_yearly["Revenue_Increase"] = df_yearly["Revenue_Total"].diff().fillna(
                    0)
                df_yearly["Revenue_Increase_%"] = (
                    (df_yearly["Revenue_Increase"] /
                     df_yearly["Revenue_Total"].shift(1).replace(0, np.nan)) * 100
                ).fillna(0)
                df_yearly["Staff_Change"] = df_yearly["Total_Staff"].diff().fillna(
                    0)
                styled_yearly = df_yearly.style.format("{:,.2f}")

                st.dataframe(styled_yearly)

                st.subheader("Custom Period Stats")
                filter_c1, filter_c2 = st.columns(2)
                with filter_c1:
                    custom_start = st.date_input(
                        "Custom Start Date", value=cfg["start_date"])
                with filter_c2:
                    custom_end = st.date_input(
                        "Custom End Date", value=cfg["end_date"])

                df_filtered = df_final[
                    (df_final["ParsedDate"].dt.date >= custom_start) &
                    (df_final["ParsedDate"].dt.date <= custom_end)
                ].copy()

                if not df_filtered.empty:
                    st.write("**Filtered Overview**")
                    total_revenue_filtered = df_filtered["Revenue_Total"].sum()
                    total_whitelabel_filtered = df_filtered["Revenue_Whitelabel"].sum(
                    )
                    total_net_inc_filtered = df_filtered["Profit_NetIncome"].sum(
                    )

                    fcol1, fcol2, fcol3 = st.columns(3)
                    with fcol1:
                        st.metric("Total Revenue (Filtered)", f"R {
                                  total_revenue_filtered:,.2f}")
                    with fcol2:
                        st.metric("Whitelabel Revenue (Filtered)", f"R {
                                  total_whitelabel_filtered:,.2f}")
                    with fcol3:
                        st.metric("Total Net Income (Filtered)",
                                  f"R {total_net_inc_filtered:,.2f}")
                else:
                    st.warning("No data in the selected custom period.")

                st.subheader("Quarterly Breakdown")
                df_final["Quarter"] = df_final["ParsedDate"].dt.quarter
                group_cols_q = {
                    "Revenue_Total": "sum",
                    "Revenue_Whitelabel": "sum",
                    "Profit_NetIncome": "sum",
                    "Clients_New": "sum"
                }
                df_quarterly = df_final.groupby(
                    ["Year", "Quarter"], as_index=False).agg(group_cols_q)
                df_quarterly = df_quarterly.sort_values(
                    by=["Year", "Quarter"]).reset_index(drop=True)
                st.dataframe(df_quarterly.style.format("{:,.2f}"))

                st.subheader("Additional Stats, Figures, and Graphs")
                import plotly.express as px

                st.write("**Key Revenue Components**")
                total_setup_fees = df_final["Revenue_SetupFees"].sum()
                total_topup_revenue = df_final["Revenue_TopUp"].sum()
                st.metric("Total Setup Fees", f"R {total_setup_fees:,.2f}")
                st.metric("Total Top-Up Revenue",
                          f"R {total_topup_revenue:,.2f}")

                st.write("**Revenue Over Time**")
                fig_revenue = px.line(
                    df_final,
                    x="ParsedDate",
                    y="Revenue_Total",
                    title="Total Revenue Over Time"
                )
                st.plotly_chart(fig_revenue, use_container_width=True)

                st.write("**Net Income Over Time**")
                fig_net_income = px.bar(
                    df_final,
                    x="ParsedDate",
                    y="Profit_NetIncome",
                    title="Net Income Over Time"
                )
                st.plotly_chart(fig_net_income, use_container_width=True)

                st.write("**Clients Growth**")
                fig_clients = px.line(
                    df_final,
                    x="ParsedDate",
                    y=["Clients_Starting", "Clients_Ending"],
                    title="Clients Growth (Starting vs Ending)"
                )
                st.plotly_chart(fig_clients, use_container_width=True)

                st.write("**Operating Expenses vs Gross Profit**")
                fig_opex_gross = px.line(
                    df_final,
                    x="ParsedDate",
                    y=["Cost_OperatingExpenses", "Profit_GrossProfit"],
                    title="Operating Expenses vs Gross Profit"
                )
                st.plotly_chart(fig_opex_gross, use_container_width=True)

                st.write("**Cash Flow (Ending Cash)**")
                fig_ending_cash = px.area(
                    df_final,
                    x="ParsedDate",
                    y="CashFlow_EndingCash",
                    title="Ending Cash Over Time"
                )
                st.plotly_chart(fig_ending_cash, use_container_width=True)

                st.write("**Overheads Over Time**")
                fig_overheads = px.bar(
                    df_final,
                    x="ParsedDate",
                    y="Cost_Overheads",
                    title="Overheads Over Time"
                )
                st.plotly_chart(fig_overheads, use_container_width=True)

                st.write("**Revenue Per Product**")
                plan_columns = [
                    col for col in df_final.columns
                    if col.startswith("Revenue_") and col not in [
                        "Revenue_Total", "Revenue_SetupFees", "Revenue_TopUp", "Revenue_Whitelabel"
                    ]
                ]
                if len(plan_columns) > 0:
                    fig_plan_rev = px.line(
                        df_final,
                        x="ParsedDate",
                        y=plan_columns,
                        title="Revenue Per Product Over Time"
                    )
                    st.plotly_chart(fig_plan_rev, use_container_width=True)

                st.write("**Total Operating Costs**")
                st.metric(
                    "Total Operating Costs (Sum of Cost_OperatingExpenses)",
                    f"R {df_final['Cost_OperatingExpenses'].sum():,.2f}"
                )

                st.write("**Total Operating Costs**")
                st.metric("Total Operating Costs (Sum of Cost_OperatingExpenses)", f"R {
                          df_final['Cost_OperatingExpenses'].sum():,.2f}")


if __name__ == "__main__":
    main()
