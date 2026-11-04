"""
PLM Product Intelligence - Interactive Power BI-Style Dashboard
Front-End Application built with Streamlit & Plotly.
Module: app.py
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, Optional
import google.generativeai as genai
from plm_logic import get_engine, build_bom_tree, calculate_total_mass, get_where_used


# ==============================================================================
# 1. Page Configuration & Theme
# ==============================================================================
st.set_page_config(
    page_title="PLM Product Intelligence | Power BI Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to mimic enterprise Power BI dashboards
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .badge-in-work {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        border: 1px solid #FDE68A;
        display: inline-block;
    }
    .badge-released {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        border: 1px solid #A7F3D0;
        display: inline-block;
    }
    .badge-missing {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.78rem;
        border: 1px solid #FECACA;
        display: inline-block;
    }
    .detail-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .tree-leaf-box {
        background: #FFFFFF;
        border-left: 3px solid #3B82F6;
        padding: 6px 12px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 0.92rem;
        border-top: 1px solid #F1F5F9;
        border-right: 1px solid #F1F5F9;
        border-bottom: 1px solid #F1F5F9;
    }
    .impact-path-box {
        background-color: #F1F5F9;
        border-left: 4px solid #0284C7;
        padding: 8px 12px;
        font-family: monospace;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .powerbi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. Data Initialization & Caching
# ==============================================================================
@st.cache_resource
def load_engine():
    """Initialize and cache the PLM engine."""
    return get_engine()

engine = load_engine()
base_products_df = engine.db.get_products_df()
instances_df = engine.db.get_instances_df()
bom_tree = build_bom_tree()
top_mass_info = calculate_total_mass(bom_tree["xml_id"])


def count_tree_components(node: Dict[str, Any]) -> int:
    """Recursively count all components (nodes) in the BOM."""
    count = 1
    for child in node.get("children", []):
        count += count_tree_components(child)
    return count

total_components_in_tree = count_tree_components(bom_tree)


# ==============================================================================
# 3. Sidebar: Power BI Slicers & Dynamic Filters
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/dashboard-layout.png", width=54)
    st.title("PLM Power BI Hub")
    st.caption("Automotive 410kW E-Drive System")
    st.divider()

    st.subheader("🎛️ Data Slicers")

    # Search Bar
    search_query = st.text_input(
        "🔎 Search Part / PLM ID:",
        placeholder="e.g. BEA3 or prd-12535825-00000081",
        help="Filters live dashboard and data grids"
    ).strip()

    # Material Slicer (Cleaned labels with explicit Missing option)
    raw_materials = base_products_df["material"].unique().tolist()
    material_options = []
    for m in raw_materials:
        material_options.append("⚠️ Missing / Unassigned" if not m else m)
    material_options = sorted(list(set(material_options)))

    selected_materials = st.multiselect(
        "Material Slicer:",
        options=material_options,
        default=[],
        help="Select one or more materials to filter dashboard visuals"
    )

    # Maturity Slicer
    all_maturities = sorted(base_products_df["maturity"].unique().tolist())
    selected_maturities = st.multiselect(
        "Maturity Slicer:",
        options=all_maturities,
        default=[],
        help="Filter by lifecycle maturity status"
    )

    # Mass Range Slicer
    min_mass = float(base_products_df["mass"].min())
    max_mass = float(base_products_df["mass"].max())
    selected_mass_range = st.slider(
        "Component Mass Range (kg):",
        min_value=0.0,
        max_value=round(max_mass, 1),
        value=(0.0, round(max_mass, 1)),
        step=0.1
    )

    # Apply Slicers to create filtered_df
    filtered_df = base_products_df.copy()

    # Apply Text Search
    if search_query:
        filtered_df = filtered_df[
            filtered_df["plm_id"].str.contains(search_query, case=False, na=False) |
            filtered_df["name"].str.contains(search_query, case=False, na=False) |
            filtered_df["xml_id"].str.contains(search_query, case=False, na=False)
        ]

    # Apply Material Slicer
    if selected_materials:
        def match_material(mat):
            clean = "⚠️ Missing / Unassigned" if not mat else mat
            return clean in selected_materials
        filtered_df = filtered_df[filtered_df["material"].apply(match_material)]

    # Apply Maturity Slicer
    if selected_maturities:
        filtered_df = filtered_df[filtered_df["maturity"].isin(selected_maturities)]

    # Apply Mass Range
    filtered_df = filtered_df[
        (filtered_df["mass"] >= selected_mass_range[0]) &
        (filtered_df["mass"] <= selected_mass_range[1])
    ]

    st.divider()
    st.markdown("### 📊 Slicer Telemetry")
    st.markdown(f"- **Visible Parts**: `{len(filtered_df)}` of `{len(base_products_df)}`")
    st.markdown(f"- **Mass Filtered**: `{filtered_df['mass'].sum():.2f} kg`")
    missing_in_view = (filtered_df["material"] == "").sum()
    st.markdown(f"- **Missing Materials**: `{missing_in_view}` parts")


# ==============================================================================
# 4. Main Executive Header & KPI Cards
# ==============================================================================
st.markdown('<div class="main-header">⚡ PLM Intelligence Executive Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automotive Electric Motor Supplier Analysis · Power BI-Style Interactive Portal</div>', unsafe_allow_html=True)

# Top Metrics Row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric(
        label="Top Assembly Mass",
        value=f"{top_mass_info['calculated_total_mass']:.2f} kg",
        help="Declared CAD/PLM recursive total mass of the root e-drive assembly"
    )
with kpi2:
    st.metric(
        label="Active Slicer Scope",
        value=f"{len(filtered_df)} Parts",
        delta=f"{len(filtered_df) - len(base_products_df)} from Total" if len(filtered_df) != len(base_products_df) else "100% of Catalog",
        delta_color="off"
    )
with kpi3:
    missing_total = (base_products_df["material"] == "").sum()
    st.metric(
        label="Missing Material Risk",
        value=f"{missing_total} Items",
        delta=f"{(missing_total/len(base_products_df))*100:.1f}% Unassigned",
        delta_color="inverse"
    )
with kpi4:
    st.metric(
        label="Lifecycle Maturity",
        value="100% IN_WORK",
        delta="0% RELEASED",
        delta_color="inverse",
        help="All parts currently in work; none released"
    )

st.divider()


# ==============================================================================
# 5. Five Main Tabs
# ==============================================================================
tab_dash, tab_bom, tab_grid, tab_impact, tab_chat = st.tabs([
    "📊 Interactive Dashboard",
    "🌳 Product Explorer",
    "📋 Filtered Data Grid",
    "🔄 Change Impact Analysis",
    "🤖 PLM AI Assistant"
])


# ------------------------------------------------------------------------------
# TAB 1: INTERACTIVE DASHBOARD (POWER BI STYLE)
# ------------------------------------------------------------------------------
with tab_dash:
    st.markdown("### 📊 Visual Analytics & Multi-Level BOM Hierarchy")
    st.caption("Drill down into component weight contributors and inspect material risk allocations.")

    dash_col1, dash_col2 = st.columns([3, 2])

    with dash_col1:
        st.subheader("☀️ BOM Sunburst Chart (Mass Distribution)")
        st.markdown(
            "Click on any assembly slice to zoom in and navigate internal subassemblies. "
            "Slices are sized proportionally by **Mass (kg)**."
        )

        # Build Sunburst rows from BOM tree
        sunburst_rows = []
        def extract_sunburst_data(node, parent_id="", path_prefix="root"):
            current_id = path_prefix
            name = node["name"]
            inst = node.get("instance_name") or ""
            display_label = f"[{inst}] {name}" if inst else name
            mass_val = max(float(node.get("mass", 0.0)), 0.0001)
            mat_raw = node.get("material", "")
            mat_label = "⚠️ Missing Material" if not mat_raw else mat_raw

            sunburst_rows.append({
                "id": current_id,
                "label": display_label,
                "parent": parent_id,
                "mass": mass_val,
                "material": mat_label,
                "plm_id": node.get("plm_id", "")
            })

            for i, child in enumerate(node.get("children", [])):
                extract_sunburst_data(child, parent_id=current_id, path_prefix=f"{current_id}_{i}_{child['xml_id']}")

        extract_sunburst_data(bom_tree, parent_id="", path_prefix="root")
        df_sun = pd.DataFrame(sunburst_rows)

        fig_sun = px.sunburst(
            df_sun,
            ids="id",
            names="label",
            parents="parent",
            values="mass",
            color="material",
            title="Interactive Mass Rollup Sunburst (Click to Drill Down)",
            hover_data={"plm_id": True, "mass": ":.3f kg"},
            color_discrete_map={"⚠️ Missing Material": "#EF4444"}
        )
        fig_sun.update_layout(
            margin=dict(t=40, l=10, r=10, b=10),
            height=580
        )
        st.plotly_chart(fig_sun, use_container_width=True)

    with dash_col2:
        st.subheader("📊 Component Count by Material")
        st.markdown(
            "Overview of raw material consumption across the currently sliced data. "
            "**Red** indicates unassigned materials requiring engineering freeze."
        )

        mat_calc_df = filtered_df.copy()
        mat_calc_df["material_clean"] = mat_calc_df["material"].apply(
            lambda m: "⚠️ Missing Material" if not m else m
        )
        mat_summary = mat_calc_df["material_clean"].value_counts().reset_index()
        mat_summary.columns = ["Material", "Component Count"]

        fig_bar = px.bar(
            mat_summary,
            x="Component Count",
            y="Material",
            orientation="h",
            color="Material",
            title="Material Allocation (Active Slicer View)",
            text="Component Count",
            color_discrete_map={"⚠️ Missing Material": "#EF4444"}
        )
        fig_bar.update_layout(
            margin=dict(t=40, l=10, r=10, b=10),
            height=580,
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Second row of Power BI visuals: Mass Pareto & Treemap
    st.subheader("⚖️ Mass Pareto Analysis (Top Weight Drivers)")
    st.caption("Top 10 individual mass drivers in the currently filtered view:")

    top10_df = filtered_df.sort_values(by="mass", ascending=False).head(10)
    fig_top10 = px.bar(
        top10_df,
        x="name",
        y="mass",
        color="mass",
        text="mass",
        title="Top 10 Heaviest Components in Selection (kg)",
        labels={"name": "Component Name", "mass": "Mass (kg)"},
        color_continuous_scale="Blues"
    )
    fig_top10.update_layout(height=400, margin=dict(t=40, l=10, r=10, b=10))
    st.plotly_chart(fig_top10, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 2: PRODUCT EXPLORER & HIERARCHICAL BOM
# ------------------------------------------------------------------------------
with tab_bom:
    st.markdown("### 🌳 Multi-Level Bill of Materials (BOM)")
    st.caption("Explore assemblies, subassemblies, and leaf parts with CAD property metadata.")

    # Component Inspector Selector
    catalog_options = ["None (Browse Full BOM)"] + [
        f"{row['name']} ({row['plm_id']})" for _, row in base_products_df.iterrows()
    ]
    inspector_choice = st.selectbox(
        "🔎 Select Specific Component for Deep Inspection:",
        options=catalog_options,
        index=0
    )

    if inspector_choice != "None (Browse Full BOM)":
        ins_plm = inspector_choice.split("(")[-1].replace(")", "").strip()
        comp = engine._resolve_product_record(ins_plm)
        if comp:
            st.markdown(f"#### 🔎 Component Inspector: `{comp['name']}`")
            with st.container():
                st.markdown('<div class="detail-card">', unsafe_allow_html=True)
                dcol1, dcol2, dcol3, dcol4 = st.columns(4)

                with dcol1:
                    st.markdown(f"**Name:**<br>`{comp['name']}`", unsafe_allow_html=True)
                    st.markdown(f"**PLM ID:**<br>`{comp['plm_id']}`", unsafe_allow_html=True)
                    st.markdown(f"**Internal XML ID:**<br>`{comp['xml_id']}`", unsafe_allow_html=True)

                with dcol2:
                    st.markdown(f"**Revision:** `{comp['revision']}` (Index: `{comp['revision_index']}`)")
                    maturity_badge = (
                        f'<span class="badge-released">RELEASED</span>'
                        if comp['maturity'] == 'RELEASED'
                        else f'<span class="badge-in-work">⚠️ {comp["maturity"]}</span>'
                    )
                    st.markdown(f"**Maturity:**<br>{maturity_badge}", unsafe_allow_html=True)
                    st.markdown(f"**Lifecycle:** `{comp['lifecycle']}`")

                with dcol3:
                    mat_val = comp['material']
                    if mat_val:
                        st.markdown(f"**Material:**<br>`{mat_val}`", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '**Material:**<br><span class="badge-missing">⚠️ NO MATERIAL ASSIGNED</span>',
                            unsafe_allow_html=True
                        )
                    st.markdown(f"**Mass (kg):** `{comp['mass']:.3f} kg`")

                with dcol4:
                    st.markdown(f"**Author / CAD Owner:**<br>`{comp['owner']}`", unsafe_allow_html=True)
                    st.markdown(f"**Organization:**<br>`{comp['organization']}`", unsafe_allow_html=True)
                    st.markdown(f"**Project:**<br>`{comp['project']}`", unsafe_allow_html=True)

                # Recursive Subassembly Info
                comp_mass_info = calculate_total_mass(comp['xml_id'])
                if comp_mass_info['is_assembly']:
                    st.info(
                        f"**Subassembly Notice:** Contains **{comp_mass_info['subcomponent_count']} direct child components**. "
                        f"Total recursive mass: **{comp_mass_info['calculated_total_mass']:.3f} kg**."
                    )

                st.markdown('</div>', unsafe_allow_html=True)

    # Recursive Tree Renderer
    def render_bom_node(node: Dict[str, Any], depth: int = 0, is_root: bool = False):
        is_leaf = node.get("is_leaf", False)
        children = node.get("children", [])
        name = node.get("name", "Unknown")
        plm_id = node.get("plm_id", "")
        mass = node.get("mass", 0.0)
        material = node.get("material", "") or "No Material"
        revision = node.get("revision", "-")
        inst_name = node.get("instance_name")

        if is_leaf:
            st.markdown(
                f"""
                <div class="tree-leaf-box" style="margin-left: {depth * 18}px;">
                    <b>🔩 [{inst_name or 'Part'}]</b> {name} 
                    <span style="color: #64748B;">({plm_id})</span> &nbsp;|&nbsp; 
                    <b>Mass:</b> <code>{mass:.3f} kg</code> &nbsp;|&nbsp; 
                    <b>Material:</b> <code>{material}</code> &nbsp;|&nbsp; 
                    <b>Rev:</b> <code>{revision}</code>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            expander_label = (
                f"📦 [{inst_name or 'Assembly'}] {name} ({plm_id}) "
                f"· {mass:.3f} kg · {len(children)} sub-items"
            )
            default_expanded = is_root or (depth < 1)

            with st.expander(expander_label, expanded=default_expanded):
                hcol1, hcol2, hcol3 = st.columns([2, 1, 1])
                with hcol1:
                    st.caption(f"**Name:** {name} | **Rev:** {revision} | **Maturity:** {node.get('maturity')}")
                with hcol2:
                    st.caption(f"**Declared Mass:** {mass:.3f} kg")
                with hcol3:
                    st.caption(f"**Child Branches:** {len(children)}")

                for child in children:
                    render_bom_node(child, depth=depth + 1, is_root=False)

    render_bom_node(bom_tree, depth=0, is_root=True)


# ------------------------------------------------------------------------------
# TAB 3: FILTERED DATA GRID (CLEAN DATA DISPLAY)
# ------------------------------------------------------------------------------
with tab_grid:
    st.markdown("### 📋 Live Filtered PLM Dataset")
    st.caption("Clean, searchable table reflecting the active sidebar slicers. Use columns to sort or filter.")

    grid_cols = [
        "plm_id", "name", "revision", "maturity", "mass", "material", "owner", "project"
    ]
    display_df = filtered_df[grid_cols].rename(columns={
        "plm_id": "PLM ID",
        "name": "Component Name",
        "revision": "Rev",
        "maturity": "Maturity",
        "mass": "Mass (kg)",
        "material": "Material Assigned",
        "owner": "CAD Author",
        "project": "Project"
    })

    # Download CSV button
    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered View to CSV",
        data=csv_data,
        file_name="PLM_Filtered_BOM_Export.csv",
        mime="text/csv"
    )

    # Interactive table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=520
    )


# ------------------------------------------------------------------------------
# TAB 4: CHANGE IMPACT ANALYSIS
# ------------------------------------------------------------------------------
with tab_impact:
    st.markdown("### 🔄 Component Change Impact Analysis")
    st.caption("Simulate component redesigns, mass alterations, or material swaps with multi-level 'Where-Used' propagation.")

    select_items = [
        (row["xml_id"], f"{row['name']} ({row['plm_id']}) — {row['mass']:.3f} kg")
        for _, row in base_products_df.iterrows()
    ]
    
    col_sel, _ = st.columns([2, 1])
    with col_sel:
        impact_component_xml_id = st.selectbox(
            "Select Component to Modify / Replace:",
            options=[x[0] for x in select_items],
            format_func=lambda x: next(item[1] for item in select_items if item[0] == x),
            index=2
        )

    selected_comp = engine._resolve_product_record(impact_component_xml_id)
    current_mass = float(selected_comp["mass"])

    # Simulation Inputs
    st.markdown("#### 🧪 Simulation Parameters")
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        st.number_input(
            "Current Mass (kg):",
            value=current_mass,
            disabled=True,
            format="%.4f"
        )
    with sim_col2:
        proposed_mass = st.number_input(
            "Proposed New Mass (kg):",
            value=round(current_mass * 1.15, 4) if current_mass > 0 else 0.5000,
            step=0.0100,
            format="%.4f",
            help="Simulate replacing this part with a lighter or heavier alternative"
        )
    with sim_col3:
        proposed_material = st.text_input(
            "Proposed New Material (Optional):",
            value="Carbon Composite / Light Alloy" if not selected_comp["material"] else f"{selected_comp['material']} (Optimized)",
            help="Indicate replacement material"
        )

    simulate_btn = st.button("🚀 Simulate Impact", type="primary", use_container_width=True)

    if simulate_btn:
        with st.spinner("Executing bottom-up where-used traversal..."):
            where_used_list = get_where_used(impact_component_xml_id)
            root_mass_before = top_mass_info["calculated_total_mass"]
            delta = proposed_mass - current_mass
            root_mass_after = root_mass_before + delta

        st.divider()
        st.markdown(f"### 📈 Impact Simulation Results for `{selected_comp['name']}`")

        affected_count = len(where_used_list)
        if affected_count > 0:
            st.warning(
                f"⚠️ **High Impact Detected:** Modifying this component affects **{affected_count} parent assemblies** "
                f"up to the top-level e-drive root."
            )
        else:
            st.info("ℹ️ This component is the top-level assembly; no higher parents are affected.")

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("Current Part Mass", f"{current_mass:.4f} kg")
        with mcol2:
            st.metric("Proposed Part Mass", f"{proposed_mass:.4f} kg")
        with mcol3:
            st.metric(
                "Mass Delta (Δ)",
                f"{delta:+.4f} kg",
                delta=f"{delta:+.4f} kg",
                delta_color="inverse"
            )
        with mcol4:
            st.metric(
                "Projected Root E-Drive Mass",
                f"{root_mass_after:.4f} kg",
                delta=f"{delta:+.4f} kg",
                delta_color="inverse"
            )

        st.success(
            f"🎯 **System Weight Conclusion:** If this part is swapped, the total weight of the root assembly "
            f"will change by **{delta:+.4f} kg** (from **{root_mass_before:.4f} kg** to **{root_mass_after:.4f} kg**)."
        )

        if where_used_list:
            st.markdown("#### 🗺️ Upward Impact Paths (Breadcrumbs to Root):")
            for item in where_used_list:
                st.markdown(
                    f"""
                    <div class="impact-path-box">
                        <b>[Level {item['level']}]</b> <b>{item['parent_name']}</b> <code>({item['parent_plm_id']})</code><br>
                        <span style="color: #475569;">Path:</span> <code>{item['impact_path']}</code><br>
                        <span style="color: #64748B; font-size: 0.82rem;">Via Instance: <b>{item['via_instance_name']}</b> | Maturity: {item['parent_maturity']} | Parent Mass: {item['parent_mass']:.3f} kg</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("#### 📊 Affected Parent Assemblies Details")
            affected_df = pd.DataFrame(where_used_list)[[
                "level", "parent_name", "parent_plm_id", "via_instance_name", "parent_mass", "parent_maturity"
            ]].rename(columns={
                "level": "Level",
                "parent_name": "Parent Assembly",
                "parent_plm_id": "Parent PLM ID",
                "via_instance_name": "Instance Connection",
                "parent_mass": "Parent Mass (kg)",
                "parent_maturity": "Parent Maturity"
            })
            st.dataframe(affected_df, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# TAB 5: INTEGRATED LLM CHATBOT (GROUNDED ON FILTERED VIEW)
# ------------------------------------------------------------------------------
with tab_chat:
    st.markdown("### 🤖 PLM Engineering AI Assistant (Live LLM)")
    st.caption("Ask natural language questions. Powered by Gemini analyzing your active filtered BOM context.")

    # API Key Input
    saved_env_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Enter your Gemini API Key:",
        value=saved_env_key,
        type="password",
        help="Get a free key from aistudio.google.com"
    )
    st.caption("Get a free API key at [aistudio.google.com](https://aistudio.google.com).")

    if not api_key:
        st.warning("⚠️ Please enter a Gemini API key to enable live AI responses.")
    else:
        try:
            genai.configure(api_key=api_key)

            # Dynamically convert the current FILTERED dataframe into context for the LLM
            chat_context_df = filtered_df[['name', 'plm_id', 'revision', 'maturity', 'mass', 'material']]
            context_data = chat_context_df.to_markdown()

            st.info(
                f"🧠 **AI Context Status:** The LLM is currently grounded in the **{len(chat_context_df)} components** "
                f"matching your sidebar slicers."
            )

            system_instruction = f"""
            You are a Senior PLM (Product Lifecycle Management) Data Analyst and Engineering Assistant.
            Your goal is to help automotive engineers navigate the Bill of Materials (BOM), identify supply chain risks, 
            and analyze mass distribution for an electric motor assembly.

            Here is the current Bill of Materials (BOM) data matching the user's active dashboard filters:
            {context_data}

            Strict Rules of Operation:
            1. DATA BOUNDARY: Base your answers ONLY on the provided BOM context above. If a user asks about something not in the data, explicitly state: "That information is not available in the current PLM extraction."
            2. TRACEABILITY (CRITICAL): Every single time you mention a component, you MUST cite its exact PLM ID in parentheses immediately after the name. Example: "Stator Core (prd-12535825-00000086)".
            3. FORMATTING: Use bold text for component names. Use bullet points for lists. Be concise, highly technical, and professional.
            """

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )

            # Re-initialize chat session when context or key changes
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
                st.session_state.chat_session = model.start_chat(history=[])

            # Quick Prompt Pills
            st.markdown("**Quick Prompts:**")
            q1, q2, q3 = st.columns(3)
            quick_prompt = None
            with q1:
                if st.button("🔩 What parts use Aluminium?", use_container_width=True):
                    quick_prompt = "What parts use Aluminium in this filtered view?"
            with q2:
                if st.button("⚖️ Heaviest component in view", use_container_width=True):
                    quick_prompt = "Which component is the heaviest in this filtered view?"
            with q3:
                if st.button("🚨 Audit missing materials", use_container_width=True):
                    quick_prompt = "Are there any components with missing materials?"

            # Render message history
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            chat_input_val = st.chat_input("Ask a technical question about the electric motor BOM...")
            active_prompt = quick_prompt or chat_input_val

            if active_prompt:
                st.session_state.chat_history.append({"role": "user", "content": active_prompt})
                with st.chat_message("user"):
                    st.markdown(active_prompt)

                with st.spinner("AI is analyzing the PLM dataset..."):
                    try:
                        response = model.generate_content(active_prompt)
                        reply = response.text
                    except Exception as e:
                        reply = f"Error communicating with Gemini: {str(e)}"

                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(reply)

        except Exception as e:
            st.error(f"Error configuring Gemini SDK: {str(e)}")
