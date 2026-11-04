"""
PLM Product Intelligence Dashboard
Front-End Application built with Streamlit.
Module: app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any, Optional
from plm_logic import get_engine, build_bom_tree, calculate_total_mass, get_where_used


# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(
    page_title="PLM Product Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished Hackathon UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
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
        font-size: 0.8rem;
        border: 1px solid #FDE68A;
        display: inline-block;
    }
    .badge-released {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #A7F3D0;
        display: inline-block;
    }
    .badge-missing {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #FECACA;
        display: inline-block;
    }
    .detail-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
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
    .risk-card {
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #E2E8F0;
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
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. Data Initialization & Caching
# ==========================================
@st.cache_resource
def load_engine():
    """Initialize and cache the PLM engine."""
    return get_engine()

engine = load_engine()
products_df = engine.db.get_products_df()
instances_df = engine.db.get_instances_df()


def count_tree_components(node: Dict[str, Any]) -> int:
    """Recursively count all components (nodes) in the BOM."""
    count = 1
    for child in node.get("children", []):
        count += count_tree_components(child)
    return count


# ==========================================
# 3. Sidebar: Search & Filtering
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/engine.png", width=64)
    st.title("PLM Intelligence")
    st.caption("3DEXPERIENCE Data Extraction Navigator")
    st.divider()

    st.subheader("🔍 Component Search")
    search_query = st.text_input(
        "Search by Name or PLM ID:",
        placeholder="e.g. BEA3 or prd-12535825-00000081",
        help="Type part of a component name, PLM product ID, or XML ID"
    ).strip()

    product_options = ["None (Browse Full BOM)"] + [
        f"{row['name']} ({row['plm_id']})" for _, row in products_df.iterrows()
    ]
    selected_option = st.selectbox(
        "Or Select Component from Catalog:",
        options=product_options,
        index=0
    )

    # Determine active component target
    active_target_id = None
    if search_query:
        matched = products_df[
            products_df["plm_id"].str.contains(search_query, case=False, na=False) |
            products_df["name"].str.contains(search_query, case=False, na=False) |
            products_df["xml_id"].str.contains(search_query, case=False, na=False)
        ]
        if not matched.empty:
            active_target_id = matched.iloc[0]["xml_id"]
        else:
            st.warning(f"No component matching '{search_query}'")
    elif selected_option != "None (Browse Full BOM)":
        plm_id_extracted = selected_option.split("(")[-1].replace(")", "").strip()
        matched = products_df[products_df["plm_id"] == plm_id_extracted]
        if not matched.empty:
            active_target_id = matched.iloc[0]["xml_id"]

    st.divider()
    st.markdown("### 📊 Dataset Overview")
    st.markdown(f"- **Unique Products**: `{len(products_df)}`")
    st.markdown(f"- **BOM Instances**: `{len(instances_df)}`")
    missing_mat_count = (products_df["material"] == "").sum()
    st.markdown(f"- **Missing Materials**: `{missing_mat_count}` parts")
    st.markdown(f"- **Maturity**: `IN_WORK` (100%)")


# ==========================================
# 4. Main Dashboard Header & Metrics
# ==========================================
st.markdown('<div class="main-header">⚡ PLM Product Intelligence Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automotive Electric Motor Supplier Analysis · Powering E-Mobility</div>', unsafe_allow_html=True)

bom_tree = build_bom_tree()
top_mass_info = calculate_total_mass(bom_tree["xml_id"])
total_components_in_tree = count_tree_components(bom_tree)

# Top Metrics Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="Top Assembly Mass",
        value=f"{top_mass_info['calculated_total_mass']:.2f} kg",
        help="Recursively aggregated mass from calculate_total_mass()"
    )
with col2:
    st.metric(
        label="Total Tree Components",
        value=total_components_in_tree,
        help="Total nested component instances in BOM"
    )
with col3:
    st.metric(
        label="Unique Part Numbers",
        value=len(products_df),
        help="Unique product definitions in PLM extraction"
    )
with col4:
    st.metric(
        label="Root Assembly",
        value=bom_tree["revision"],
        delta=f"Rev {bom_tree['revision']} | {bom_tree['maturity']}",
        delta_color="off",
        help=f"PLM ID: {bom_tree['plm_id']}"
    )

st.divider()


# ==========================================
# 5. Component Details Section (If Searched)
# ==========================================
if active_target_id:
    comp = engine._resolve_product_record(active_target_id)
    if comp:
        st.markdown(f"### 🔎 Component Inspector: `{comp['name']}`")
        with st.container():
            st.markdown('<div class="detail-card">', unsafe_allow_html=True)
            dcol1, dcol2, dcol3, dcol4 = st.columns(4)

            with dcol1:
                st.markdown(f"**Component Name:**<br>`{comp['name']}`", unsafe_allow_html=True)
                st.markdown(f"**PLM ID:**<br>`{comp['plm_id']}`", unsafe_allow_html=True)
                st.markdown(f"**Internal XML ID:**<br>`{comp['xml_id']}`", unsafe_allow_html=True)

            with dcol2:
                st.markdown(f"**Revision:** `{comp['revision']}` (Index: `{comp['revision_index']}`)")
                maturity_badge = (
                    f'<span class="badge-released">RELEASED</span>'
                    if comp['maturity'] == 'RELEASED'
                    else f'<span class="badge-in-work">⚠️ {comp["maturity"]}</span>'
                )
                st.markdown(f"**Maturity State:**<br>{maturity_badge}", unsafe_allow_html=True)
                st.markdown(f"**Lifecycle:** `{comp['lifecycle']}`")

            with dcol3:
                material_str = comp['material']
                if material_str:
                    st.markdown(f"**Material:**<br>`{material_str}`", unsafe_allow_html=True)
                else:
                    st.markdown(
                        '**Material:**<br><span class="badge-missing">⚠️ NO MATERIAL ASSIGNED</span>',
                        unsafe_allow_html=True
                    )
                st.markdown(f"**Mass (kg):** `{comp['mass']:.3f} kg`")

            with dcol4:
                st.markdown(f"**Owner / CAD Author:**<br>`{comp['owner']}`", unsafe_allow_html=True)
                st.markdown(f"**Organization:**<br>`{comp['organization']}`", unsafe_allow_html=True)
                st.markdown(f"**Project:**<br>`{comp['project']}`", unsafe_allow_html=True)

            comp_mass_info = calculate_total_mass(comp['xml_id'])
            if comp_mass_info['is_assembly']:
                st.info(
                    f"**Assembly Notice:** This is a subassembly containing "
                    f"**{comp_mass_info['subcomponent_count']} direct child elements**. "
                    f"Total recursive mass: **{comp_mass_info['calculated_total_mass']:.3f} kg**."
                )

            st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 6. Five Main Views: Tabs
# ==========================================
tab_bom, tab_risk, tab_impact, tab_chat, tab_viz = st.tabs([
    "🌳 Product Explorer",
    "⚠️ Risk Intelligence",
    "🔄 Change Impact Analysis",
    "🤖 PLM AI Assistant",
    "📊 Advanced Visualizations"
])


# ------------------------------------------
# TAB 1: PRODUCT EXPLORER
# ------------------------------------------
with tab_bom:
    st.markdown("### 🌳 Multi-Level Bill of Materials (BOM)")
    st.caption("Expand assemblies to navigate the multi-level hierarchy, inspect mass, materials, and instances.")

    def render_bom_node(node: Dict[str, Any], depth: int = 0, is_root: bool = False):
        """
        Recursively renders BOM tree using nested st.expander elements.
        """
        is_leaf = node.get("is_leaf", False)
        children = node.get("children", [])
        name = node.get("name", "Unknown")
        plm_id = node.get("plm_id", "")
        mass = node.get("mass", 0.0)
        material = node.get("material", "") or "No Material"
        revision = node.get("revision", "-")
        inst_name = node.get("instance_name")

        is_highlighted = (active_target_id is not None and node.get("xml_id") == active_target_id)
        highlight_prefix = "⭐ " if is_highlighted else ""

        if is_leaf:
            st.markdown(
                f"""
                <div class="tree-leaf-box" style="margin-left: {depth * 18}px; {'border-left: 4px solid #F59E0B; background: #FFFBEB;' if is_highlighted else ''}">
                    {highlight_prefix}<b>🔩 [{inst_name or 'Part'}]</b> {name} 
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
                f"{highlight_prefix}📦 [{inst_name or 'Assembly'}] {name} ({plm_id}) "
                f"· {mass:.3f} kg · {len(children)} sub-items"
            )
            default_expanded = is_root or is_highlighted or (depth < 1)

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


# ------------------------------------------
# TAB 2: RISK INTELLIGENCE
# ------------------------------------------
with tab_risk:
    st.markdown("### ⚠️ Engineering & Supply Chain Risk Intelligence")
    st.caption("Automated audit of BOM compliance, lifecycle readiness, and material assignments.")

    missing_materials_df = products_df[products_df["material"] == ""].copy()
    unreleased_df = products_df[products_df["maturity"] != "RELEASED"].copy()

    rcol1, rcol2 = st.columns(2)
    with rcol1:
        st.markdown("""
        <div class="risk-card" style="background-color: #FEF2F2; border-color: #F87171;">
            <h4 style="color: #991B1B; margin-top: 0;">🚨 Missing Material Risk</h4>
            <p style="color: #7F1D1D; font-size: 0.92rem;">
                Components with undefined materials cannot undergo accurate CAE stress simulation, 
                environmental compliance audits (REACH / RoHS), or precise raw material cost rollups.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.metric(
            label="Missing Material Components",
            value=f"{len(missing_materials_df)} / {len(products_df)}",
            delta=f"{(len(missing_materials_df)/len(products_df))*100:.1f}% Unassigned",
            delta_color="inverse"
        )

    with rcol2:
        st.markdown("""
        <div class="risk-card" style="background-color: #FFFBEB; border-color: #FBBF24;">
            <h4 style="color: #92400E; margin-top: 0;">⚠️ Lifecycle Maturity Risk</h4>
            <p style="color: #78350F; font-size: 0.92rem;">
                Supplier risk warning: All components are currently in <b>IN_WORK</b> maturity. 
                Zero components have reached the verified <b>RELEASED</b> state, indicating ongoing design freeze volatility.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.metric(
            label="Unreleased BOM Components",
            value=f"{len(unreleased_df)} / {len(products_df)}",
            delta="100% Unreleased (IN_WORK)",
            delta_color="inverse"
        )

    st.subheader(f"📋 Missing Materials Audit ({len(missing_materials_df)} Items)")
    st.markdown("These components require immediate material definition by the engineering or supplier team:")

    display_missing = missing_materials_df[[
        "plm_id", "name", "revision", "maturity", "mass", "owner", "project"
    ]].rename(columns={
        "plm_id": "PLM ID",
        "name": "Component Name",
        "revision": "Rev",
        "maturity": "Maturity",
        "mass": "Mass (kg)",
        "owner": "Author",
        "project": "Project"
    })
    st.dataframe(display_missing, use_container_width=True, hide_index=True)

    st.divider()

    # Heaviest Components Analysis (Mass Pareto)
    st.subheader("⚖️ Heaviest Components (Top Mass Drivers)")
    st.caption("Top 10 individual components and subassemblies driving product weight:")
    top_heavy = products_df.sort_values(by="mass", ascending=False).head(10)[[
        "plm_id", "name", "revision", "mass", "material"
    ]].rename(columns={
        "plm_id": "PLM ID",
        "name": "Component Name",
        "revision": "Rev",
        "mass": "Mass (kg)",
        "material": "Material Assigned"
    })
    st.dataframe(top_heavy, use_container_width=True, hide_index=True)


# ------------------------------------------
# TAB 3: CHANGE IMPACT ANALYSIS
# ------------------------------------------
with tab_impact:
    st.markdown("### 🔄 Component Change Impact Analysis")
    st.caption("Simulate component redesigns, mass alterations, or material swaps with multi-level 'Where-Used' propagation.")

    select_items = [
        (row["xml_id"], f"{row['name']} ({row['plm_id']}) — {row['mass']:.3f} kg")
        for _, row in products_df.iterrows()
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


# ------------------------------------------
# TAB 4: REAL PLM AI ASSISTANT
# ------------------------------------------
with tab_chat:
    st.markdown("### 🤖 PLM Engineering AI Assistant (Live LLM)")
    st.caption("Ask natural language questions. Powered by real AI analyzing your live BOM data.")

    # API Key Input
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.caption("Get a free API key at [aistudio.google.com](https://aistudio.google.com). Ensure you log in with your personal email address associated with your AI Pro account, not your ESILV school email.")

    if not api_key:
        st.warning("⚠️ Please enter an API key to enable the AI.")
    else:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Convert the BOM dataframe into a readable string format for the LLM
        context_data = products_df[['name', 'plm_id', 'revision', 'maturity', 'mass', 'material']].to_markdown()

        # Instruct the AI on how to behave and enforce the challenge requirement (citing sources)
        system_instruction = f"""
        You are an expert PLM AI Assistant helping an automotive engineer.
        Here is the complete Bill of Materials (BOM) data for an electric motor:
        {context_data}

        Rules:
        1. Answer the user's questions based ONLY on the data provided above.
        2. You MUST explicitly cite the specific PLM ID (e.g., prd-12535825-...) for any component you mention to provide traceable evidence.
        3. Be concise and professional.
        """

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )

        if "real_chat_history" not in st.session_state:
            st.session_state.real_chat_history = []
            st.session_state.chat_session = model.start_chat(history=[])

        # Render chat history
        for msg in st.session_state.real_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_query = st.chat_input("Ask anything about the motor's materials, mass, or structure...")

        if user_query:
            # Display User Message
            st.session_state.real_chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Generate and Display AI Response
            with st.spinner("AI is analyzing the PLM data..."):
                try:
                    response = st.session_state.chat_session.send_message(user_query)
                    reply = response.text
                except Exception as e:
                    reply = f"Error connecting to AI: {e}"

            st.session_state.real_chat_history.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)


# ------------------------------------------
# TAB 5: ADVANCED VISUALIZATIONS
# ------------------------------------------
with tab_viz:
    st.markdown("### 📊 Advanced Engineering Visualizations")
    st.caption("Interactive multi-dimensional charts for mass distribution and material risk audits.")

    # -------------------------------------------------------------
    # Visual 1: BOM Sunburst Chart (Mass Distribution)
    # -------------------------------------------------------------
    st.subheader("☀️ BOM Sunburst Chart (Hierarchical Mass Breakdown)")
    st.markdown(
        "Click on any assembly slice to zoom in and inspect its internal subassemblies and parts. "
        "The arc size represents each component's mass contribution in kilograms."
    )

    # Flatten the tree into Sunburst rows (id, label, parent, mass, material)
    sunburst_rows = []
    def extract_sunburst_data(node, parent_id="", path_prefix="root"):
        current_id = path_prefix
        name = node["name"]
        inst = node.get("instance_name") or ""
        display_label = f"[{inst}] {name}" if inst else name
        mass_val = max(float(node.get("mass", 0.0)), 0.0001)
        material_val = node.get("material") or "⚠️ Unassigned Material"

        sunburst_rows.append({
            "id": current_id,
            "label": display_label,
            "parent": parent_id,
            "mass": mass_val,
            "material": material_val,
            "plm_id": node.get("plm_id", "")
        })

        for i, child in enumerate(node.get("children", [])):
            extract_sunburst_data(child, parent_id=current_id, path_prefix=f"{current_id}_{i}_{child['xml_id']}")

    extract_sunburst_data(bom_tree, parent_id="", path_prefix="root")
    df_sunburst = pd.DataFrame(sunburst_rows)

    fig_sunburst = px.sunburst(
        df_sunburst,
        ids="id",
        names="label",
        parents="parent",
        values="mass",
        color="material",
        title="Interactive E-Drive BOM Mass Distribution (Click to Zoom)",
        hover_data={"plm_id": True, "mass": ":.3f kg"},
        color_discrete_map={"⚠️ Unassigned Material": "#EF4444"}
    )
    fig_sunburst.update_layout(
        margin=dict(t=40, l=10, r=10, b=10),
        height=620
    )
    st.plotly_chart(fig_sunburst, use_container_width=True)

    st.divider()

    # -------------------------------------------------------------
    # Visual 2: Material Distribution Treemap & Bar Chart
    # -------------------------------------------------------------
    st.subheader("🗺️ Material Allocation & Compliance Risk")
    st.markdown(
        "Visualizes component counts across materials. "
        "Components marked **⚠️ Missing / Unassigned** indicate immediate compliance and CAE simulation risks."
    )

    mat_df = products_df.copy()
    mat_df["material_clean"] = mat_df["material"].apply(lambda m: "⚠️ Missing / Unassigned" if not m else m)
    mat_summary = mat_df["material_clean"].value_counts().reset_index()
    mat_summary.columns = ["Material", "Component Count"]

    vcol1, vcol2 = st.columns(2)

    with vcol1:
        fig_treemap = px.treemap(
            mat_summary,
            path=["Material"],
            values="Component Count",
            color="Material",
            title="Material Distribution Treemap",
            color_discrete_map={"⚠️ Missing / Unassigned": "#DC2626"}
        )
        fig_treemap.update_layout(margin=dict(t=40, l=10, r=10, b=10), height=450)
        st.plotly_chart(fig_treemap, use_container_width=True)

    with vcol2:
        fig_bar = px.bar(
            mat_summary,
            x="Component Count",
            y="Material",
            orientation="h",
            color="Material",
            title="Component Count by Material Assignment",
            text="Component Count",
            color_discrete_map={"⚠️ Missing / Unassigned": "#DC2626"}
        )
        fig_bar.update_layout(
            margin=dict(t=40, l=10, r=10, b=10),
            height=450,
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_bar, use_container_width=True)
