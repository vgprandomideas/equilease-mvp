# ========================================
# equilease.py - Complete EquiLease MVP Application
# ========================================

import streamlit as st
import pandas as pd
import json
import uuid
import numpy as np
from datetime import datetime, timedelta
import os

# Optional plotly import
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly not installed. Charts will be disabled. Install with: pip install plotly")

# Page configuration
st.set_page_config(
    page_title="EquiLease - Smart Rent + Equity Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# DATABASE FUNCTIONS
# ========================================

DATA_DIR = 'data'
DEALS_FILE = os.path.join(DATA_DIR, 'deals.json')

def initialize_database():
    """Initialize the database directory and files"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(DEALS_FILE):
        with open(DEALS_FILE, 'w') as f:
            json.dump([], f)

def load_deals():
    """Load all deals from JSON file"""
    try:
        with open(DEALS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_deals(deals):
    """Save deals to JSON file"""
    with open(DEALS_FILE, 'w') as f:
        json.dump(deals, f, indent=2, default=str)

def save_deal(business_data, deal_terms, proposal):
    """Save a new deal to the database"""
    deals = load_deals()
    
    deal_record = {
        **business_data,
        **deal_terms,
        'proposal': proposal,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    deals.append(deal_record)
    save_deals(deals)
    
    return deal_record

def get_deals():
    """Get all deals"""
    return load_deals()

def get_deal_by_id(deal_id):
    """Get a specific deal by ID"""
    deals = load_deals()
    for deal in deals:
        if deal.get('id') == deal_id:
            return deal
    return None

def update_deal_status(deal_id, new_status):
    """Update the status of a deal"""
    deals = load_deals()
    
    for deal in deals:
        if deal.get('id') == deal_id:
            deal['status'] = new_status
            deal['updated_at'] = datetime.now().isoformat()
            if new_status == 'approved':
                deal['approved_at'] = datetime.now().isoformat()
            elif new_status == 'rejected':
                deal['rejected_at'] = datetime.now().isoformat()
            break
    
    save_deals(deals)

# ========================================
# AI LOGIC FUNCTIONS
# ========================================

def calculate_risk_score(business_data):
    """Calculate AI-based risk score for business"""
    base_score = 50
    
    # Business type risk adjustment
    business_type_risk = {
        'SaaS Startup': -10,
        'E-commerce': -5,
        'Professional Services': -8,
        'Manufacturing': 0,
        'Restaurant': +25,
        'Retail Store': +15,
        'Franchise': -5,
        'Other': +10
    }
    base_score += business_type_risk.get(business_data.get('business_type', 'Other'), 0)
    
    # Industry risk factors
    industry_risk = {
        'Technology': -8,
        'Healthcare': -5,
        'Finance': -3,
        'Education': 0,
        'Food & Beverage': +20,
        'Retail': +12,
        'Real Estate': +5,
        'Other': +8
    }
    base_score += industry_risk.get(business_data.get('industry', 'Other'), 0)
    
    # Revenue indicators
    current_revenue = business_data.get('current_revenue', 0)
    projected_12m = business_data.get('projected_revenue_12m', 0)
    
    if current_revenue > 10000:
        base_score -= 15
    elif current_revenue > 5000:
        base_score -= 10
    elif current_revenue > 1000:
        base_score -= 5
    else:
        base_score += 10
    
    # Team size indicators
    team_size = business_data.get('team_size', 1)
    if team_size > 20:
        base_score -= 10
    elif team_size > 10:
        base_score -= 8
    elif team_size > 5:
        base_score -= 5
    elif team_size < 2:
        base_score += 15
    
    # Funding status
    if business_data.get('has_funding', False):
        funding_amount = business_data.get('funding_raised', 0)
        if funding_amount > 1000000:
            base_score -= 20
        elif funding_amount > 500000:
            base_score -= 15
        elif funding_amount > 100000:
            base_score -= 10
        else:
            base_score -= 5
    
    # Cash runway
    runway = business_data.get('runway_months', 0)
    if runway > 18:
        base_score -= 10
    elif runway > 12:
        base_score -= 5
    elif runway < 6:
        base_score += 15
    elif runway < 3:
        base_score += 25
    
    # Founder experience
    experience_impact = {
        'Previous successful exit': -20,
        'Serial entrepreneur': -15,
        'Industry veteran (10+ years)': -12,
        'First-time founder': +10
    }
    base_score += experience_impact.get(business_data.get('founder_experience', 'First-time founder'), 0)
    
    # Market validation
    if business_data.get('has_customers', False):
        base_score -= 10
    if business_data.get('has_revenue', False):
        base_score -= 8
    
    # Space size risk
    space_size = business_data.get('space_size', 1000)
    if space_size > 5000:
        base_score += 8
    elif space_size > 3000:
        base_score += 5
    elif space_size < 500:
        base_score -= 3
    
    final_score = max(5, min(95, base_score))
    return round(final_score, 1)

def generate_deal_terms(business_data, risk_score):
    """Generate deal terms based on risk score"""
    base_upfront_rent = 30
    base_equity = 5
    base_revenue_share = 3
    base_revenue_years = 3
    
    risk_multiplier = (risk_score - 50) / 50
    
    upfront_rent_percent = base_upfront_rent + (risk_multiplier * 15)
    upfront_rent_percent = max(20, min(50, upfront_rent_percent))
    
    equity_percent = base_equity + (risk_multiplier * 4)
    equity_percent = max(2, min(12, equity_percent))
    
    revenue_share_percent = base_revenue_share + (risk_multiplier * 2)
    revenue_share_percent = max(1, min(6, revenue_share_percent))
    
    revenue_share_years = base_revenue_years
    if business_data.get('business_type') in ['SaaS Startup', 'E-commerce']:
        revenue_share_years = 4
    elif business_data.get('business_type') == 'Restaurant':
        revenue_share_years = 2
    
    space_size = business_data.get('space_size', 1000)
    annual_market_rent = space_size * 25
    monthly_market_rent = annual_market_rent / 12
    monthly_rent = monthly_market_rent * (upfront_rent_percent / 100)
    deferred_amount = monthly_market_rent - monthly_rent
    
    current_revenue = business_data.get('current_revenue', 0)
    revenue_trigger = max(current_revenue * 1.5, 5000)
    
    return {
        'risk_score': risk_score,
        'upfront_rent_percent': round(upfront_rent_percent, 1),
        'equity_percent': round(equity_percent, 1),
        'revenue_share_percent': round(revenue_share_percent, 1),
        'revenue_share_years': revenue_share_years,
        'monthly_rent': round(monthly_rent, 0),
        'monthly_market_rent': round(monthly_market_rent, 0),
        'deferred_amount': round(deferred_amount, 0),
        'annual_market_rent': round(annual_market_rent, 0),
        'revenue_trigger': round(revenue_trigger, 0),
        'space_size': space_size
    }

# ========================================
# DEAL GENERATOR FUNCTIONS
# ========================================

def create_deal_proposal(business_data, deal_terms):
    """Generate a comprehensive deal proposal"""
    projected_revenue = business_data.get('projected_revenue_12m', 0)
    annual_revenue_share = projected_revenue * 12 * (deal_terms['revenue_share_percent'] / 100)
    total_annual_rent = deal_terms['monthly_rent'] * 12
    potential_total_return = total_annual_rent + annual_revenue_share
    
    roi_improvement = ((potential_total_return / deal_terms['annual_market_rent']) - 1) * 100 if deal_terms['annual_market_rent'] > 0 else 0
    roi_difference = int(potential_total_return - deal_terms['annual_market_rent'])
    
    proposal = f"""EQUILEASE DEAL PROPOSAL
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Proposal ID: EQL-{business_data['id'][:8].upper()}
Valid Until: {(datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TENANT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Business Name:        {business_data['business_name']}
Business Type:        {business_data['business_type']}
Industry:            {business_data.get('industry', 'Not specified')}
Desired Location:     {business_data['location']}
Space Requirements:   {business_data['space_size']:,} square feet
Lease Duration:       {business_data.get('lease_duration', 'To be negotiated')}

Team Size:           {business_data['team_size']} employees
Founder Experience:   {business_data.get('founder_experience', 'Not specified')}
Business Model:       {business_data.get('business_model', 'Not specified')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FINANCIAL OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Monthly Revenue:      ${business_data['current_revenue']:,}
12-Month Projection:          ${business_data['projected_revenue_12m']:,}
24-Month Projection:          ${business_data['projected_revenue_24m']:,}
Current Burn Rate:            ${business_data.get('burn_rate', 0):,}/month
Cash Runway:                  {business_data.get('runway_months', 0)} months
Total Funding Raised:         ${business_data.get('funding_raised', 0):,}

Funding Status:               {'✅ Funded' if business_data.get('has_funding') else '❌ Bootstrapped'}
Revenue Status:               {'✅ Revenue Generating' if business_data.get('has_revenue') else '❌ Pre-Revenue'}
Customer Base:                {'✅ Has Customers' if business_data.get('has_customers') else '❌ Pre-Customer'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AI RISK ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Risk Score:           {deal_terms['risk_score']}/100
Risk Category:                {'🟢 LOW RISK' if deal_terms['risk_score'] < 40 else '🟡 MEDIUM RISK' if deal_terms['risk_score'] < 70 else '🔴 HIGH RISK'}
Confidence Level:             {95 - deal_terms['risk_score'] * 0.3:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROPOSED LEASE STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Market Rate Analysis:
Standard Market Rent:         ${deal_terms['monthly_market_rent']:,.0f}/month
Annual Market Value:          ${deal_terms['annual_market_rent']:,.0f}/year

EquiLease Hybrid Structure:

UPFRONT RENT COMPONENT:
Monthly Payment:              ${deal_terms['monthly_rent']:,.0f}
Percentage of Market:         {deal_terms['upfront_rent_percent']:.1f}%
Annual Payment:               ${deal_terms['monthly_rent'] * 12:,.0f}

DEFERRED RENT COMPONENT:
Monthly Deferred Amount:      ${deal_terms['deferred_amount']:,.0f}
Percentage of Market:         {100 - deal_terms['upfront_rent_percent']:.1f}%
Annual Deferred:              ${deal_terms['deferred_amount'] * 12:,.0f}

TOTAL MONTHLY SAVINGS:        ${deal_terms['deferred_amount']:,.0f}
TOTAL ANNUAL SAVINGS:         ${deal_terms['deferred_amount'] * 12:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EQUITY PARTICIPATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Equity Stake:                 {deal_terms['equity_percent']:.1f}% of business
Structure:                    Convertible equity (SAFE-like instrument)
Valuation Method:             Post-money valuation at next funding round
Conversion Events:            Series A, acquisition, or IPO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REVENUE SHARING AGREEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Revenue Share Percentage:     {deal_terms['revenue_share_percent']:.1f}% of gross monthly revenue
Duration:                     {deal_terms['revenue_share_years']} years from lease commencement
Revenue Threshold:            Activated when monthly revenue > ${deal_terms['revenue_trigger']:,}
Reporting Frequency:          Monthly, within 15 days of month-end

Projected Annual Revenue Share: ${annual_revenue_share:,.0f}
Total Revenue Share (Full Term): ${annual_revenue_share * deal_terms['revenue_share_years']:,.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LANDLORD RETURN ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Traditional Lease Model:
Annual Rent Income:           ${deal_terms['annual_market_rent']:,.0f}
Total Return (Year 1):       ${deal_terms['annual_market_rent']:,.0f}

EquiLease Hybrid Model:
Annual Rent Income:           ${deal_terms['monthly_rent'] * 12:,.0f}
Annual Revenue Share:         ${annual_revenue_share:,.0f}
Equity Upside:                Variable (potentially significant)
Total Cash Return (Year 1):   ${potential_total_return:,.0f}

IMPROVEMENT OVER MARKET:      +{roi_improvement:.1f}% (+${roi_difference:,})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Landlord Review & Approval (5-7 business days)
2. Due Diligence Period (10 business days)
3. Legal Documentation (5-10 business days)
4. Lease Execution & Move-in

Contact Information:
EquiLease Platform: hello@equilease.com
Phone: (555) 123-RENT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This proposal is valid for 30 days from generation date.
All terms subject to final due diligence and documentation.

"You're not renting space. You're funding growth. You're inventing an asset class."
"""
    
    return proposal

def create_contract_template(deal):
    """Generate a basic contract template"""
    contract = f"""EQUILEASE HYBRID LEASE AGREEMENT

This Agreement is entered into on {datetime.now().strftime('%B %d, %Y')} between:

LANDLORD: [LANDLORD NAME AND ADDRESS]
TENANT: {deal['business_name']}

PREMISES: {deal['location']}
SPACE: {deal['space_size']:,} square feet

ARTICLE 1: RENT TERMS
1.1 Base Rent: ${deal.get('monthly_rent', 0):,.0f} per month
1.2 Market Rate: ${deal.get('monthly_market_rent', 0):,.0f} per month
1.3 Upfront Percentage: {deal.get('upfront_rent_percent', 30):.1f}% of market rate
1.4 Deferred Amount: ${deal.get('deferred_amount', 0):,.0f} per month

ARTICLE 2: EQUITY PARTICIPATION
2.1 Equity Percentage: {deal.get('equity_percent', 5):.1f}% of Tenant's business
2.2 Structure: Convertible equity instrument
2.3 Conversion Events: Series A funding, acquisition, IPO

ARTICLE 3: REVENUE SHARING
3.1 Revenue Share: {deal.get('revenue_share_percent', 3):.1f}% of gross monthly revenue
3.2 Duration: {deal.get('revenue_share_years', 3)} years from lease commencement
3.3 Threshold: Activated when monthly revenue exceeds ${deal.get('revenue_trigger', 5000):,}

[Additional standard commercial lease terms to be added by legal counsel]

Generated by: EquiLease Platform
Date: {datetime.now().strftime('%B %d, %Y')}
Agreement ID: EQL-{deal['id'][:8].upper()}-CONTRACT

SIGNATURES:
LANDLORD: _________________ DATE: _________
TENANT: __________________ DATE: _________
"""
    
    return contract

# ========================================
# STREAMLIT UI FUNCTIONS
# ========================================

def load_css():
    """Load custom CSS styling"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .deal-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
    }
    
    .risk-low { 
        background: #d4edda; 
        color: #155724; 
        padding: 0.25rem 0.5rem; 
        border-radius: 4px; 
        font-size: 0.8rem;
        font-weight: bold;
    }
    .risk-medium { 
        background: #fff3cd; 
        color: #856404; 
        padding: 0.25rem 0.5rem; 
        border-radius: 4px; 
        font-size: 0.8rem;
        font-weight: bold;
    }
    .risk-high { 
        background: #f8d7da; 
        color: #721c24; 
        padding: 0.25rem 0.5rem; 
        border-radius: 4px; 
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

def show_home():
    """Landing page with value proposition"""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 EquiLease</h1>
        <h3>Where Rent Meets Revenue</h3>
        <p>Revolutionary lease structuring with AI-powered risk assessment</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 For Businesses
        - **Pay only 30% upfront rent**
        - **Share 70% through equity + revenue**
        - **AI-powered fair deal structuring**
        - **Faster approval than traditional leases**
        """)
        
        if st.button("Apply as Business", key="business_btn"):
            st.session_state.page = 'tenant'
            st.rerun()
    
    with col2:
        st.markdown("""
        ### 🏠 For Landlords
        - **Higher total returns than fixed rent**
        - **Equity upside from successful tenants**
        - **AI risk assessment for every deal**
        - **Revenue share from growing businesses**
        """)
        
        if st.button("View Landlord Dashboard", key="landlord_btn"):
            st.session_state.page = 'landlord'
            st.rerun()
    
    # Key metrics
    st.markdown("### 📊 Platform Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Deals", "47", "↗️ +12%")
    with col2:
        st.metric("Total Volume", "$2.3M", "↗️ +23%")
    with col3:
        st.metric("Average ROI", "18.5%", "↗️ +3.2%")
    with col4:
        st.metric("Success Rate", "84%", "↗️ +5%")

def show_tenant_form():
    """Business application form with AI scoring"""
    st.title("🚀 Business Application")
    st.markdown("Complete the form below to get AI-powered lease terms tailored to your business")
    
    with st.container():
        st.subheader("📋 Business Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            business_name = st.text_input("Business Name *", placeholder="e.g., TechStart Solutions")
            business_type = st.selectbox(
                "Business Type *",
                ["SaaS Startup", "E-commerce", "Restaurant", "Retail Store", "Franchise", "Professional Services", "Manufacturing", "Other"]
            )
            industry = st.selectbox(
                "Industry *",
                ["Technology", "Food & Beverage", "Retail", "Healthcare", "Finance", "Education", "Real Estate", "Other"]
            )
            
        with col2:
            location = st.text_input("Desired Location *", placeholder="e.g., Manhattan, NY")
            space_size = st.number_input("Space Size (sq ft) *", min_value=100, max_value=50000, value=1500)
            lease_duration = st.selectbox("Preferred Lease Duration", ["1 year", "2 years", "3 years", "5 years"])
    
    with st.container():
        st.subheader("💰 Financial Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_revenue = st.number_input("Current Monthly Revenue ($)", min_value=0, value=0, step=1000)
            projected_revenue_12m = st.number_input("Projected Revenue (12 months) ($)", min_value=0, value=10000, step=1000)
            projected_revenue_24m = st.number_input("Projected Revenue (24 months) ($)", min_value=0, value=20000, step=1000)
            
        with col2:
            burn_rate = st.number_input("Monthly Burn Rate ($)", min_value=0, value=5000, step=500)
            runway_months = st.number_input("Cash Runway (months)", min_value=0, value=12, step=1)
            funding_raised = st.number_input("Total Funding Raised ($)", min_value=0, value=0, step=10000)
    
    with st.container():
        st.subheader("👥 Team & Experience")
        
        col1, col2 = st.columns(2)
        
        with col1:
            team_size = st.number_input("Current Team Size", min_value=1, max_value=500, value=5)
            founder_experience = st.selectbox(
                "Founder Experience",
                ["First-time founder", "Serial entrepreneur", "Industry veteran (10+ years)", "Previous successful exit"]
            )
            
        with col2:
            has_funding = st.checkbox("Have you raised institutional funding?")
            has_revenue = st.checkbox("Currently generating revenue?")
            has_customers = st.checkbox("Do you have paying customers?")
    
    with st.container():
        st.subheader("📝 Business Details")
        
        business_model = st.selectbox(
            "Business Model",
            ["B2B SaaS", "B2C SaaS", "E-commerce", "Marketplace", "Brick & Mortar", "Franchise", "Service-based", "Other"]
        )
        
        target_market = st.text_area("Target Market Description", placeholder="Describe your target customers...")
        competitive_advantage = st.text_area("Competitive Advantage", placeholder="What makes your business unique?...")
        growth_strategy = st.text_area("Growth Strategy", placeholder="How do you plan to scale?...")
    
    # Form submission
    if st.button("🎯 Calculate My Deal Terms", type="primary"):
        if not business_name or not business_type or not location:
            st.error("Please fill in all required fields marked with *")
            return
        
        # Create business data dictionary
        business_data = {
            'id': str(uuid.uuid4()),
            'business_name': business_name,
            'business_type': business_type,
            'industry': industry,
            'location': location,
            'space_size': space_size,
            'lease_duration': lease_duration,
            'current_revenue': current_revenue,
            'projected_revenue_12m': projected_revenue_12m,
            'projected_revenue_24m': projected_revenue_24m,
            'burn_rate': burn_rate,
            'runway_months': runway_months,
            'funding_raised': funding_raised,
            'team_size': team_size,
            'founder_experience': founder_experience,
            'has_funding': has_funding,
            'has_revenue': has_revenue,
            'has_customers': has_customers,
            'business_model': business_model,
            'target_market': target_market,
            'competitive_advantage': competitive_advantage,
            'growth_strategy': growth_strategy,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Calculate AI score and terms
        with st.spinner("🤖 AI is analyzing your business..."):
            risk_score = calculate_risk_score(business_data)
            deal_terms = generate_deal_terms(business_data, risk_score)
            proposal = create_deal_proposal(business_data, deal_terms)
            
            # Save deal
            save_deal(business_data, deal_terms, proposal)
        
        # Show results
        show_deal_results(business_data, deal_terms, proposal)

def show_deal_results(business_data, deal_terms, proposal):
    """Display AI-generated deal terms"""
    st.success("✅ Your personalized deal terms are ready!")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_color = "🟢" if deal_terms['risk_score'] < 40 else "🟡" if deal_terms['risk_score'] < 70 else "🔴"
        st.metric("Risk Score", f"{risk_color} {deal_terms['risk_score']}/100")
    
    with col2:
        st.metric("Upfront Rent", f"{deal_terms['upfront_rent_percent']:.1f}%")
    
    with col3:
        st.metric("Equity Stake", f"{deal_terms['equity_percent']:.1f}%")
    
    with col4:
        st.metric("Revenue Share", f"{deal_terms['revenue_share_percent']:.1f}%")
    
    # Detailed breakdown
    st.subheader("📊 Deal Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Monthly Payments:**")
        st.write(f"Market Rate: ${deal_terms['monthly_market_rent']:,.0f}")
        st.write(f"Your Payment: ${deal_terms['monthly_rent']:,.0f}")
        st.write(f"Savings: ${deal_terms['deferred_amount']:,.0f}")
        
    with col2:
        st.markdown("**Equity & Revenue Terms:**")
        st.write(f"Equity Stake: {deal_terms['equity_percent']:.1f}%")
        st.write(f"Revenue Share: {deal_terms['revenue_share_percent']:.1f}% for {deal_terms['revenue_share_years']} years")
        st.write(f"Trigger: When monthly revenue > ${business_data['current_revenue'] * 1.5:,.0f}")
    
    # Full proposal
    st.subheader("📋 Complete Proposal")
    with st.expander("View Full Proposal"):
        st.code(proposal, language="text")
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Send to Landlords"):
            st.success("✅ Proposal sent to relevant landlords in your area!")
            st.balloons()
    
    with col2:
        st.download_button(
            label="📄 Download Proposal",
            data=proposal,
            file_name=f"proposal_{business_data['business_name']}.txt",
            mime="text/plain"
        )

def show_landlord_dashboard():
    """Landlord dashboard to review and manage deals"""
    st.title("🏠 Landlord Dashboard")
    st.markdown("Manage incoming deal proposals and track your portfolio performance")
    
    # Load deals
    deals = get_deals()
    
    if not deals:
        st.info("📭 No deal applications yet. Check back soon!")
        st.markdown("### 🎯 To get started:")
        st.markdown("1. Have businesses apply through the Business Application page")
        st.markdown("2. Review and approve deals here")
        st.markdown("3. Generate contracts and track performance")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(deals)
    
    # Dashboard metrics
    show_dashboard_metrics(df)
    
    # Filter section
    st.subheader("🔍 Filter Deals")
    filtered_df = show_filter_section(df)
    
    # Deal management
    st.subheader("📋 Deal Management")
    show_deal_management(filtered_df)
    
    # Portfolio analytics
    st.subheader("📊 Portfolio Analytics")
    show_portfolio_analytics(df)

def show_dashboard_metrics(df):
    """Show key dashboard metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_deals = len(df)
        st.metric("Total Applications", total_deals)
    
    with col2:
        pending_deals = len(df[df['status'] == 'pending'])
        st.metric("Pending Review", pending_deals)
    
    with col3:
        approved_deals = len(df[df['status'] == 'approved'])
        approval_rate = (approved_deals / total_deals * 100) if total_deals > 0 else 0
        st.metric("Approval Rate", f"{approval_rate:.1f}%")
    
    with col4:
        avg_risk = df['risk_score'].mean() if 'risk_score' in df.columns else 0
        st.metric("Avg Risk Score", f"{avg_risk:.1f}/100")

def show_filter_section(df):
    """Show filtering options"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox("Status", ["All"] + df['status'].unique().tolist())
    
    with col2:
        business_type_filter = st.selectbox("Business Type", ["All"] + df['business_type'].unique().tolist())
    
    with col3:
        location_filter = st.selectbox("Location", ["All"] + df['location'].unique().tolist())
    
    with col4:
        risk_filter = st.selectbox("Risk Level", ["All", "Low (0-40)", "Medium (41-70)", "High (71-100)"])
    
    # Apply filters
    filtered_df = filter_deals(df, status_filter, business_type_filter, location_filter, risk_filter)
    return filtered_df

def filter_deals(df, status_filter, business_type_filter, location_filter, risk_filter):
    """Apply filters to deals DataFrame"""
    filtered_df = df.copy()
    
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if business_type_filter != "All":
        filtered_df = filtered_df[filtered_df['business_type'] == business_type_filter]
    
    if location_filter != "All":
        filtered_df = filtered_df[filtered_df['location'] == location_filter]
    
    if risk_filter != "All":
        risk_ranges = {
            "Low (0-40)": (0, 40),
            "Medium (41-70)": (41, 70),
            "High (71-100)": (71, 100)
        }
        min_risk, max_risk = risk_ranges[risk_filter]
        filtered_df = filtered_df[(filtered_df['risk_score'] >= min_risk) & (filtered_df['risk_score'] <= max_risk)]
    
    return filtered_df

def show_deal_management(filtered_df):
    """Show deal management interface"""
    if filtered_df.empty:
        st.info("No deals match your current filters.")
        return
    
    st.write(f"Showing {len(filtered_df)} deals")
    
    # Deal cards
    for idx, deal in filtered_df.iterrows():
        show_deal_card(deal)

def show_deal_card(deal):
    """Display individual deal card"""
    risk_score = deal.get('risk_score', 50)
    risk_emoji = "🟢" if risk_score < 40 else "🟡" if risk_score < 70 else "🔴"
    risk_label = "Low" if risk_score < 40 else "Medium" if risk_score < 70 else "High"
    
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin: 1rem 0; background: white;">
            <h4>{risk_emoji} {deal['business_name']} - {deal['business_type']}</h4>
            <p><strong>Location:</strong> {deal['location']} | <strong>Space:</strong> {deal['space_size']:,} sq ft</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            **Business Details:**
            - Type: {deal['business_type']}
            - Industry: {deal.get('industry', 'N/A')}
            - Team Size: {deal['team_size']} people
            - Current Revenue: ${deal['current_revenue']:,}/month
            - Projected (12m): ${deal['projected_revenue_12m']:,}/month
            """)
        
        with col2:
            st.markdown(f"""
            **Deal Terms:**
            - Risk Score: {risk_score}/100 ({risk_label})
            - Upfront Rent: {deal.get('upfront_rent_percent', 30):.1f}%
            - Monthly Payment: ${deal.get('monthly_rent', 0):,}
            - Equity: {deal.get('equity_percent', 5):.1f}%
            - Revenue Share: {deal.get('revenue_share_percent', 3):.1f}%
            """)
        
        with col3:
            st.markdown(f"""
            **Financial Info:**
            - Funding Raised: ${deal.get('funding_raised', 0):,}
            - Burn Rate: ${deal.get('burn_rate', 0):,}/month
            - Runway: {deal.get('runway_months', 0)} months
            - Has Revenue: {'Yes' if deal.get('has_revenue', False) else 'No'}
            """)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"✅ Approve", key=f"approve_{deal['id']}"):
                update_deal_status(deal['id'], 'approved')
                st.success("Deal approved!")
                st.rerun()
        
        with col2:
            if st.button(f"❌ Reject", key=f"reject_{deal['id']}"):
                update_deal_status(deal['id'], 'rejected')
                st.error("Deal rejected")
                st.rerun()
        
        with col3:
            if st.button(f"📋 Details", key=f"details_{deal['id']}"):
                st.session_state.selected_deal_id = deal['id']
                st.session_state.page = 'deal_details'
                st.rerun()
        
        with col4:
            contract = create_contract_template(deal)
            st.download_button(
                label="📄 Contract",
                data=contract,
                file_name=f"contract_{deal['business_name']}.txt",
                mime="text/plain",
                key=f"download_{deal['id']}"
            )

def show_portfolio_analytics(df):
    """Show portfolio analytics and charts"""
    if df.empty:
        st.info("No data available for analytics.")
        return
    
    if PLOTLY_AVAILABLE:
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk distribution
            risk_distribution = df['risk_score'].apply(
                lambda x: 'Low (0-40)' if x < 40 else 'Medium (41-70)' if x < 70 else 'High (71-100)'
            ).value_counts()
            
            fig_risk = px.pie(
                values=risk_distribution.values,
                names=risk_distribution.index,
                title="Risk Distribution",
                color_discrete_map={
                    'Low (0-40)': '#00cc96',
                    'Medium (41-70)': '#ffa500',
                    'High (71-100)': '#ff6b6b'
                }
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            # Business type distribution
            business_type_dist = df['business_type'].value_counts()
            
            fig_business = px.bar(
                x=business_type_dist.index,
                y=business_type_dist.values,
                title="Applications by Business Type",
                labels={'x': 'Business Type', 'y': 'Number of Applications'}
            )
            st.plotly_chart(fig_business, use_container_width=True)
        
        # Revenue projections
        if 'projected_revenue_12m' in df.columns:
            fig_revenue = px.scatter(
                df,
                x='risk_score',
                y='projected_revenue_12m',
                color='business_type',
                size='team_size',
                hover_data=['business_name'],
                title="Risk Score vs. Projected Revenue",
                labels={'risk_score': 'Risk Score', 'projected_revenue_12m': 'Projected Revenue (12m)'}
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
    else:
        # Simple analytics without plotly
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Risk Distribution:**")
            risk_counts = df['risk_score'].apply(
                lambda x: 'Low' if x < 40 else 'Medium' if x < 70 else 'High'
            ).value_counts()
            for risk_level, count in risk_counts.items():
                st.write(f"- {risk_level}: {count} deals")
        
        with col2:
            st.markdown("**Business Types:**")
            type_counts = df['business_type'].value_counts()
            for btype, count in type_counts.items():
                st.write(f"- {btype}: {count} deals")

def show_deal_details():
    """Show detailed view of a specific deal"""
    if 'selected_deal_id' not in st.session_state:
        st.error("No deal selected. Please go back to the dashboard.")
        return
    
    deal = get_deal_by_id(st.session_state.selected_deal_id)
    
    if not deal:
        st.error("Deal not found.")
        return
    
    st.title(f"📋 Deal Details: {deal['business_name']}")
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'landlord'
        st.rerun()
    
    # Deal overview
    show_deal_overview(deal)
    
    # Financial projections
    show_financial_projections(deal)
    
    # Risk assessment
    show_risk_assessment(deal)
    
    # Actions
    show_deal_actions(deal)

def show_deal_overview(deal):
    """Show deal overview section"""
    st.subheader("🏢 Business Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Basic Information:**
        - **Business Name:** {deal['business_name']}
        - **Type:** {deal['business_type']}
        - **Industry:** {deal.get('industry', 'N/A')}
        - **Location:** {deal['location']}
        - **Space Size:** {deal['space_size']:,} sq ft
        - **Lease Duration:** {deal.get('lease_duration', 'N/A')}
        """)
    
    with col2:
        st.markdown(f"""
        **Team & Experience:**
        - **Team Size:** {deal['team_size']} people
        - **Founder Experience:** {deal.get('founder_experience', 'N/A')}
        - **Has Funding:** {'Yes' if deal.get('has_funding', False) else 'No'}
        - **Has Revenue:** {'Yes' if deal.get('has_revenue', False) else 'No'}
        - **Has Customers:** {'Yes' if deal.get('has_customers', False) else 'No'}
        """)
    
    # Business description
    if deal.get('target_market'):
        st.markdown(f"**Target Market:** {deal['target_market']}")
    
    if deal.get('competitive_advantage'):
        st.markdown(f"**Competitive Advantage:** {deal['competitive_advantage']}")
    
    if deal.get('growth_strategy'):
        st.markdown(f"**Growth Strategy:** {deal['growth_strategy']}")

def show_financial_projections(deal):
    """Show financial projections section"""
    st.subheader("💰 Financial Projections")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Revenue", f"${deal['current_revenue']:,}/month")
    
    with col2:
        st.metric("12M Projection", f"${deal['projected_revenue_12m']:,}/month")
    
    with col3:
        st.metric("24M Projection", f"${deal['projected_revenue_24m']:,}/month")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Burn Rate", f"${deal.get('burn_rate', 0):,}/month")
    
    with col2:
        st.metric("Runway", f"{deal.get('runway_months', 0)} months")
    
    with col3:
        st.metric("Funding Raised", f"${deal.get('funding_raised', 0):,}")

def show_risk_assessment(deal):
    """Show AI risk assessment breakdown"""
    st.subheader("🤖 AI Risk Assessment")
    
    risk_score = deal.get('risk_score', 50)
    risk_color = "🟢" if risk_score < 40 else "🟡" if risk_score < 70 else "🔴"
    risk_label = "Low Risk" if risk_score < 40 else "Medium Risk" if risk_score < 70 else "High Risk"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Overall Risk Score", f"{risk_color} {risk_score}/100", risk_label)
        
        # Deal terms
        st.markdown("**Proposed Terms:**")
        st.write(f"• Upfront Rent: {deal.get('upfront_rent_percent', 30):.1f}%")
        st.write(f"• Monthly Payment: ${deal.get('monthly_rent', 0):,}")
        st.write(f"• Equity Stake: {deal.get('equity_percent', 5):.1f}%")
        st.write(f"• Revenue Share: {deal.get('revenue_share_percent', 3):.1f}% for {deal.get('revenue_share_years', 3)} years")
    
    with col2:
        # Risk factors breakdown
        st.markdown("**Risk Factors Analysis:**")
        
        factors = []
        if deal['business_type'] == 'Restaurant':
            factors.append("❌ High-risk industry (Restaurant)")
        elif deal['business_type'] in ['SaaS Startup', 'E-commerce']:
            factors.append("✅ Scalable business model")
        
        if deal.get('has_funding', False):
            factors.append("✅ Has institutional funding")
        else:
            factors.append("⚠️ No institutional funding")
        
        if deal.get('has_revenue', False):
            factors.append("✅ Generating revenue")
        else:
            factors.append("❌ Pre-revenue stage")
        
        if deal['team_size'] > 10:
            factors.append("✅ Established team size")
        elif deal['team_size'] < 3:
            factors.append("⚠️ Small team size")
        
        if deal.get('founder_experience') in ['Serial entrepreneur', 'Industry veteran (10+ years)', 'Previous successful exit']:
            factors.append("✅ Experienced founder")
        else:
            factors.append("⚠️ First-time founder")
        
        for factor in factors:
            st.write(factor)

def show_deal_actions(deal):
    """Show available actions for the deal"""
    st.subheader("⚡ Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Approve Deal", type="primary"):
            update_deal_status(deal['id'], 'approved')
            st.success("Deal approved successfully!")
            st.rerun()
    
    with col2:
        if st.button("❌ Reject Deal"):
            update_deal_status(deal['id'], 'rejected')
            st.error("Deal rejected")
            st.rerun()
    
    with col3:
        if st.button("📝 Request Modifications"):
            st.info("Modification request sent to tenant")
    
    with col4:
        contract = create_contract_template(deal)
        st.download_button(
            label="📄 Generate Contract",
            data=contract,
            file_name=f"contract_{deal['business_name']}.txt",
            mime="text/plain"
        )
    
    # Deal proposal
    if deal.get('proposal'):
        st.subheader("📋 Generated Proposal")
        with st.expander("View Full Proposal"):
            st.code(deal['proposal'], language="text")

# ========================================
# MAIN APPLICATION
# ========================================

def main():
    """Main application router"""
    # Initialize database
    initialize_database()
    
    # Load custom CSS
    load_css()
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🏢 EquiLease")
        
        # Navigation buttons
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'home'
        
        if st.button("🚀 Business Application", use_container_width=True):
            st.session_state.page = 'tenant'
        
        if st.button("🏢 Landlord Dashboard", use_container_width=True):
            st.session_state.page = 'landlord'
        
        if st.button("📋 Deal Details", use_container_width=True):
            st.session_state.page = 'deal_details'
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        deals = get_deals()
        st.metric("Total Deals", len(deals))
        if deals:
            pending = len([d for d in deals if d.get('status') == 'pending'])
            st.metric("Pending", pending)
        
        st.markdown("---")
        st.markdown("### 🛠️ System Info")
        st.write(f"Plotly: {'✅ Available' if PLOTLY_AVAILABLE else '❌ Not installed'}")
        st.write(f"Data: {len(deals)} deals stored")
    
    # Route to appropriate page
    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'tenant':
        show_tenant_form()
    elif st.session_state.page == 'landlord':
        show_landlord_dashboard()
    elif st.session_state.page == 'deal_details':
        show_deal_details()

if __name__ == "__main__":
    main()