"""
3DEXPERIENCE PLM Product Intelligence & Change Impact Platform
Industrial Web Application for Automotive Electric Powertrain BOM
Module: app.py
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from plm_logic import get_engine, build_bom_tree, calculate_total_mass, get_where_used

# ------------------------------------------------------------------------------
# 1. PAGE CONFIG & 3DEXPERIENCE STYLING
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="PLM Intelligence",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for authentic 3DEXPERIENCE / Dassault Systèmes styling
st.markdown("""
<style>
    /* Hide default Streamlit header and footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar - 3DEXPERIENCE Compass styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        padding-top: 1rem;
    }

    /* Main background */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Dassault Blue Branding */
    h1, h2, h3, h4, .dassault-title {
        color: #005686 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-weight: 700;
    }

    /* Metric values in Dassault Blue */
    [data-testid="stMetricValue"] {
        color: #005686 !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    /* Clean widget card container */
    .widget-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 2px 6px rgba(0, 86, 134, 0.08);
        margin-bottom: 1rem;
    }

    /* Compass App Badge */
    .compass-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.5rem 0.25rem 1.25rem 0.25rem;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 1.25rem;
    }
    .compass-icon {
        width: 38px;
        height: 38px;
        background: #005686;
        color: #FFFFFF;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: bold;
    }
    .compass-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #005686;
        line-height: 1.2;
    }
    .compass-subtitle {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Search match badge */
    .match-badge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #FDE68A;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 2. DATA LOADING & CACHING
# ------------------------------------------------------------------------------
@st.cache_resource
def load_plm_data():
    """Load PLM relational entities and BOM tree with persistent caching."""
    engine = get_engine()
    products_df = engine.db.get_products_df()
    instances_df = engine.db.get_instances_df()
    bom_tree = build_bom_tree()
    return products_df, instances_df, bom_tree

products_df, instances_df, bom_tree = load_plm_data()

# Root system reference mass
ROOT_SYSTEM_MASS = 100.100  # Declared root mass in kg (ECAR-EI_410KW_EDRIVE_FRONT)


# ------------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION (THE COMPASS APP PANE)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="compass-header">
        <div class="compass-icon">🧭</div>
        <div>
            <div class="compass-title">3DEXPERIENCE</div>
            <div class="compass-subtitle">PLM Intelligence Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧭 PLM Apps")

    app_view = st.radio(
        label="Select App",
        options=[
            "📊 Dashboard & Analytics",
            "🌳 Product Structure (BOM)",
            "🔄 Change Impact Analysis",
            "🤖 AI Engineering Copilot"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    # System Status & Metadata Info
    st.markdown("#### ⚙️ Assembly Context")
    st.markdown(
        f"**Root Assembly:**<br>`ECAR-EI_410KW_EDRIVE_FRONT`<br>"
        f"**PLM ID:** `prd-12535825-00000047`<br>"
        f"**Total Mass:** `{ROOT_SYSTEM_MASS:.3f} kg`<br>"
        f"**Maturity:** `IN_WORK`",
        unsafe_allow_html=True
    )

    st.caption("3DEXPERIENCE R2024x | ESILV Hackathon Edition")


# ------------------------------------------------------------------------------
# 4. VIEW 1: DASHBOARD & ANALYTICS (POWER BI STYLE)
# ------------------------------------------------------------------------------
if app_view == "📊 Dashboard & Analytics":
    st.markdown("<h2 class='dassault-title'>📊 Executive Dashboard & Analytics</h2>", unsafe_allow_html=True)
    st.caption("Real-time telemetry, mass rollup distributions, and compliance risk detection.")

    # 4.1 Slicers Section (Power BI Filter Pane)
    st.markdown('<div class="widget-card">', unsafe_allow_html=True)
    st.markdown("##### 🎛️ Data Slicers")

    # Prepare material options with clear label for missing materials
    available_materials = sorted([m for m in products_df['material'].dropna().unique() if m != ""])
    material_display_options = ["⚠️ Missing / Unassigned"] + available_materials

    col_slicer1, col_slicer2 = st.columns(2)

    with col_slicer1:
        selected_materials_display = st.multiselect(
            "Filter by Material:",
            options=material_display_options,
            default=[],
            help="Select one or more materials to filter the dashboard. Empty selection shows all."
        )

    with col_slicer2:
        available_maturities = sorted(products_df['maturity'].dropna().unique().tolist())
        selected_maturities = st.multiselect(
            "Filter by Maturity State:",
            options=available_maturities,
            default=[],
            help="Select lifecycle release states. Empty selection shows all."
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # 4.2 Apply Slicer Filtering Logic
    filtered_df = products_df.copy()

    # Apply Material Slicer
    if selected_materials_display:
        include_missing = "⚠️ Missing / Unassigned" in selected_materials_display
        chosen_named = [m for m in selected_materials_display if m != "⚠️ Missing / Unassigned"]

        mask = pd.Series(False, index=filtered_df.index)
        if include_missing:
            mask = mask | (filtered_df['material'] == "") | (filtered_df['material'].isna())
        if chosen_named:
            mask = mask | (filtered_df['material'].isin(chosen_named))
        filtered_df = filtered_df[mask]

    # Apply Maturity Slicer
    if selected_maturities:
        filtered_df = filtered_df[filtered_df['maturity'].isin(selected_maturities)]

    # 4.3 KPI Row (4 Columns)
    kpi_mass = filtered_df['mass'].sum()
    kpi_parts = len(filtered_df)
    kpi_missing_mat = len(filtered_df[(filtered_df['material'] == "") | (filtered_df['material'].isna())])
    kpi_maturity = "100% IN_WORK" if (filtered_df['maturity'] == "IN_WORK").all() and len(filtered_df) > 0 else "MIXED"

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.metric(
            label="Total Filtered Mass",
            value=f"{kpi_mass:.3f} kg",
            delta=f"Root: {ROOT_SYSTEM_MASS:.3f} kg"
        )
    with col_kpi2:
        st.metric(
            label="Unique Components",
            value=f"{kpi_parts} Parts",
            delta=f"Total: {len(products_df)}"
        )
    with col_kpi3:
        st.metric(
            label="Missing Materials",
            value=f"{kpi_missing_mat} Parts",
            delta="Compliance Risk" if kpi_missing_mat > 0 else "Compliant",
            delta_color="inverse"
        )
    with col_kpi4:
        st.metric(
            label="Lifecycle Maturity",
            value=kpi_maturity,
            delta="Freeze Risk" if kpi_maturity == "100% IN_WORK" else "Released"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4.4 Plotly Visuals: Treemap & Material Bar Chart
    if filtered_df.empty:
        st.warning("⚠️ No components match the selected slicer criteria. Please broaden your selection.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        # Prepare display-ready DataFrame for visuals
        visual_df = filtered_df.copy()
        visual_df['material_clean'] = visual_df['material'].apply(
            lambda m: "⚠️ Missing / Unassigned" if not m or pd.isna(m) else m
        )
        visual_df['plot_mass'] = visual_df['mass'].apply(lambda x: max(float(x), 0.001))

        with chart_col1:
            st.markdown('<div class="widget-card">', unsafe_allow_html=True)
            st.markdown("##### 📦 Mass Distribution Treemap")
            fig_treemap = px.treemap(
                visual_df,
                path=['material_clean', 'name'],
                values='plot_mass',
                color='material_clean',
                color_discrete_map={"⚠️ Missing / Unassigned": "#EF4444"},
                title="Mass Allocation by Material & Component",
                hover_data={'plm_id': True, 'mass': ':.3f kg', 'plot_mass': False}
            )
            fig_treemap.update_layout(
                margin=dict(t=40, l=10, r=10, b=10),
                height=420,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_treemap, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_col2:
            st.markdown('<div class="widget-card">', unsafe_allow_html=True)
            st.markdown("##### 📊 Component Count by Material")
            mat_counts = visual_df['material_clean'].value_counts().reset_index()
            mat_counts.columns = ['Material', 'Count']

            fig_bar = px.bar(
                mat_counts,
                x='Material',
                y='Count',
                color='Material',
                color_discrete_map={"⚠️ Missing / Unassigned": "#EF4444"},
                text='Count',
                title="Frequency of Material Usage"
            )
            fig_bar.update_layout(
                margin=dict(t=40, l=10, r=10, b=10),
                height=420,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="",
                yaxis_title="Component Count",
                showlegend=False
            )
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # 4.5 Filtered Component Grid Table
    st.markdown('<div class="widget-card">', unsafe_allow_html=True)
    st.markdown("##### 📋 Filtered Component Master Table")
    display_table = filtered_df[[
        'name', 'plm_id', 'revision', 'maturity', 'mass', 'material', 'organization', 'project'
    ]].copy().rename(columns={
        'name': 'Component Name',
        'plm_id': 'PLM ID',
        'revision': 'Rev',
        'maturity': 'Maturity',
        'mass': 'Mass (kg)',
        'material': 'Material',
        'organization': 'Organization',
        'project': 'Project'
    })

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Mass (kg)": st.column_config.NumberColumn(format="%.3f kg")
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 5. VIEW 2: PRODUCT STRUCTURE (BOM)
# ------------------------------------------------------------------------------
elif app_view == "🌳 Product Structure (BOM)":
    st.markdown("<h2 class='dassault-title'>🌳 Product Structure (Multi-Level BOM)</h2>", unsafe_allow_html=True)
    st.caption("Hierarchical expansion of assemblies, subassemblies, and leaf parts with CAD property metadata.")

    # 5.1 Search Filter Box
    col_search, col_stats = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Search BOM by Component Name or PLM ID:",
            placeholder="e.g. STATOR, prd-12535825-00000085, Aluminium...",
            help="Filters and highlights matching nodes across the entire assembly tree."
        ).strip().lower()

    with col_stats:
        total_subassemblies = len(instances_df['owner_id'].unique())
        st.markdown(
            f"<div style='padding-top: 1.8rem; font-size: 0.9rem; color: #64748B;'>"
            f"<b>Tree Assemblies:</b> {total_subassemblies} | <b>Instances:</b> {len(instances_df)}"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 5.2 Recursive Tree Renderer
    def render_bom_node(node: Dict[str, Any], depth: int = 0):
        name = node.get("name", "Unknown")
        plm_id = node.get("plm_id", "")
        mass = node.get("mass", 0.0)
        revision = node.get("revision", "-")
        maturity = node.get("maturity", "-")
        material = node.get("material", "") or "Unassigned"
        children = node.get("children", [])
        is_leaf = node.get("is_leaf", False)
        instance_name = node.get("instance_name", "")

        # Check for search match
        is_match = False
        if search_query:
            if (search_query in name.lower()) or (search_query in plm_id.lower()) or (search_query in material.lower()):
                is_match = True

        match_badge = " 🎯 [MATCH]" if is_match else ""
        inst_label = f"[{instance_name}] " if instance_name else ""

        # Expander title
        if is_leaf or len(children) == 0:
            header_text = f"⚙️ {inst_label}{name} ({plm_id}) — Mass: {mass:.3f} kg{match_badge}"
        else:
            header_text = f"📁 {inst_label}{name} ({plm_id}) — Total Mass: {mass:.3f} kg ({len(children)} sub-items){match_badge}"

        # Expand if there is an active search match or at top levels
        auto_expand = is_match or (depth < 2 and not search_query)

        with st.expander(header_text, expanded=auto_expand):
            # Property badges
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.markdown(f"**PLM ID:**<br>`{plm_id}`", unsafe_allow_html=True)
            with p2:
                st.markdown(f"**Revision / Maturity:**<br>`Rev {revision}` | `{maturity}`", unsafe_allow_html=True)
            with p3:
                st.markdown(f"**Declared Mass:**<br>`{mass:.3f} kg`", unsafe_allow_html=True)
            with p4:
                mat_color = "#DC2626" if material == "Unassigned" else "#005686"
                st.markdown(f"**Material:**<br><span style='color:{mat_color}; font-weight:600;'>{material}</span>", unsafe_allow_html=True)

            # Recursive child traversal
            if children:
                st.markdown(f"<div style='margin-left: {15}px; border-left: 2px solid #E2E8F0; padding-left: 10px;'>", unsafe_allow_html=True)
                for child in children:
                    render_bom_node(child, depth=depth + 1)
                st.markdown("</div>", unsafe_allow_html=True)

    # Render from root
    st.markdown('<div class="widget-card">', unsafe_allow_html=True)
    st.markdown(f"#### 🌐 Root: `{bom_tree.get('name', 'Root')} ({bom_tree.get('plm_id', '')})`")
    render_bom_node(bom_tree, depth=0)
    st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 6. VIEW 3: CHANGE IMPACT ANALYSIS
# ------------------------------------------------------------------------------
elif app_view == "🔄 Change Impact Analysis":
    st.markdown("<h2 class='dassault-title'>🔄 Engineering Change Impact Analysis</h2>", unsafe_allow_html=True)
    st.caption("Simulate engineering change orders (ECO) with bottom-up Where-Used graph traversal and projected weight deltas.")

    st.markdown('<div class="widget-card">', unsafe_allow_html=True)
    st.markdown("##### 🎯 Target Component Selection & Simulation Parameters")

    # Dropdown to select a target component
    component_options = [
        f"{row['name']} ({row['plm_id']})" for _, row in products_df.iterrows()
    ]
    # Default to an interesting child part (e.g. BEA3 or front housing)
    default_idx = 0
    for idx, opt in enumerate(component_options):
        if "BEA3" in opt or "HOUSING FRONT" in opt:
            default_idx = idx
            break

    selected_option = st.selectbox(
        "Select Component to Modify / Replace:",
        options=component_options,
        index=default_idx,
        help="Select any component from the 3DEXPERIENCE catalog to evaluate its upstream assembly impact."
    )

    # Extract target record
    selected_plm_id = selected_option.split("(")[-1].replace(")", "").strip()
    target_row = products_df[products_df['plm_id'] == selected_plm_id].iloc[0]
    target_xml_id = target_row['xml_id']
    current_mass = float(target_row['mass'])

    col_mass1, col_mass2 = st.columns(2)
    with col_mass1:
        st.number_input(
            "Current Mass (kg):",
            value=current_mass,
            disabled=True,
            format="%.3f",
            help="Certified CAD declared mass from the current PLM extraction."
        )

    with col_mass2:
        proposed_mass = st.number_input(
            "Proposed New Mass (kg):",
            value=current_mass,
            step=0.05,
            format="%.3f",
            help="Input projected alternative mass (e.g. lightweighting or material substitution)."
        )

    run_sim = st.button("🚀 Run Impact Traversal", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Impact Traversal Execution
    if run_sim:
        where_used_results = get_where_used(target_xml_id)
        mass_delta = proposed_mass - current_mass
        new_projected_root_mass = ROOT_SYSTEM_MASS + mass_delta

        st.markdown('<div class="widget-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Simulation Results & Projected Vehicle Impact")

        res_col1, res_col2, res_col3 = st.columns(3)

        with res_col1:
            st.metric(
                label="Affected Parent Assemblies",
                value=f"{len(where_used_results)} Assemblies",
                delta="Direct & Indirect Impact"
            )

        with res_col2:
            st.metric(
                label="Single-Part Mass Delta",
                value=f"{mass_delta:+.3f} kg",
                delta="Weight Increase" if mass_delta > 0 else ("Lightweighting" if mass_delta < 0 else "Neutral"),
                delta_color="inverse"
            )

        with res_col3:
            st.metric(
                label="Projected Root Assembly Mass",
                value=f"{new_projected_root_mass:.3f} kg",
                delta=f"{mass_delta:+.3f} kg vs Base ({ROOT_SYSTEM_MASS:.3f} kg)",
                delta_color="inverse"
            )

        st.divider()

        # Traceability Breadcrumbs
        st.markdown("#### 🔗 Upstream Traceability Breadcrumbs (Where-Used Path)")
        if not where_used_results:
            st.info("ℹ️ **Top-Level Root Assembly:** This component has no upstream parent assemblies.")
        else:
            for item in where_used_results:
                level = item.get("level", 1)
                parent_name = item.get("parent_name", "")
                parent_plm_id = item.get("parent_plm_id", "")
                via_inst = item.get("via_instance_name", "")
                impact_path = item.get("impact_path", "")

                st.markdown(
                    f"**Level {level}:** `{parent_name} ({parent_plm_id})` via instance `{via_inst}`"
                )
                st.code(impact_path, language="text")

        st.markdown('</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# 7. VIEW 4: AI ENGINEERING COPILOT (GEMINI LLM)
# ------------------------------------------------------------------------------
elif app_view == "🤖 AI Engineering Copilot":
    st.markdown("<h2 class='dassault-title'>🤖 AI Engineering Copilot</h2>", unsafe_allow_html=True)
    st.caption("Live AI agent analyzing your complete 3DEXPERIENCE BOM data with mandatory PLM ID traceability.")

    # 7.1 API Key Input
    saved_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Enter your Gemini API Key:",
        value=saved_key,
        type="password",
        help="Get a free Gemini API key from https://aistudio.google.com"
    )
    st.caption("🔑 Obtain an API key from [aistudio.google.com](https://aistudio.google.com).")

    # 7.2 Prepare Context Data & System Instruction
    context_table = products_df[[
        'name', 'plm_id', 'revision', 'maturity', 'mass', 'material', 'organization', 'project'
    ]].to_markdown(index=False)

    SYSTEM_INSTRUCTION = f"""
You are an expert PLM Data Analyst and Senior Automotive Powertrain Engineer.
Here is the complete Bill of Materials (BOM) extracted from Dassault Systèmes 3DEXPERIENCE:

{context_table}

STRICT ENGINEERING RULES:
1. DATA BOUNDARY: Answer questions based strictly on the BOM data provided above. If an inquiry asks for specifications not in this dataset, respond: "That information is not available in the current PLM extraction."
2. CRITICAL TRACEABILITY REQUIREMENT: Every time you mention ANY component or assembly, you MUST explicitly cite its exact PLM ID in parentheses immediately following its name. Example: "ECAR-EI_HOUSING FRONT EDRIVE (prd-12535825-00000050)".
3. FORMATTING: Use bold text for component names, structured bullet points for lists, and concise technical language.
"""

    # 7.3 Chat History Initialization
    if "copilot_chat_history" not in st.session_state:
        st.session_state.copilot_chat_history = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hello! I am your **3DEXPERIENCE AI Engineering Copilot**.\n\n"
                    "I can answer natural language queries across the **ECAR-EI_410KW_EDRIVE_FRONT (prd-12535825-00000047)** "
                    "BOM with certified PLM ID traceability.\n\n"
                    "💡 *Try asking:*\n"
                    "- *'What parts use Aluminium?'*\n"
                    "- *'Show me the heaviest component.'*\n"
                    "- *'Are there any missing materials?'*\n"
                    "- *'What are the major subassemblies?'*"
                )
            }
        ]

    # Quick prompt pills
    st.markdown("**Suggested Engineering Prompts:**")
    qp1, qp2, qp3, qp4 = st.columns(4)
    quick_query = None
    with qp1:
        if st.button("🔩 Parts using Aluminium", use_container_width=True):
            quick_query = "What parts use Aluminium?"
    with qp2:
        if st.button("⚖️ Heaviest component", use_container_width=True):
            quick_query = "Show me the heaviest component."
    with qp3:
        if st.button("🚨 Audit missing materials", use_container_width=True):
            quick_query = "Are there any missing materials?"
    with qp4:
        if st.button("🏗️ Major subassemblies", use_container_width=True):
            quick_query = "What are the major subassemblies of the electric motor?"

    # Display chat history
    for msg in st.session_state.copilot_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    user_prompt = st.chat_input("Ask a technical question about the electric motor BOM...")
    active_input = quick_query or user_prompt

    if active_input:
        st.session_state.copilot_chat_history.append({"role": "user", "content": active_input})
        with st.chat_message("user"):
            st.markdown(active_input)

        if not api_key:
            reply = (
                "⚠️ **Gemini API Key Required**\n\n"
                "Please enter a valid Google Gemini API Key in the password field above to enable live LLM reasoning.\n\n"
                "You can get a free key from [aistudio.google.com](https://aistudio.google.com)."
            )
            st.session_state.copilot_chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.warning(reply)
        else:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing 3DEXPERIENCE BOM..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(
                            model_name="gemini-1.5-flash",
                            system_instruction=SYSTEM_INSTRUCTION
                        )
                        chat_session = model.start_chat()
                        response = chat_session.send_message(active_input)
                        bot_response = response.text if response and response.text else "No response generated."
                    except Exception as err:
                        bot_response = f"❌ **Error communicating with Gemini:** {str(err)}"

                st.markdown(bot_response)
                st.session_state.copilot_chat_history.append({"role": "assistant", "content": bot_response})
