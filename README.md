# ⚡ PLM Product Intelligence Dashboard

An engineering intelligence platform designed for an automotive electric motor supplier. This solution transforms raw **3DEXPERIENCE PLM (XPDMXML)** export data into actionable business and engineering insights.

Built during the **PLM Intelligence Challenge / ESILV Hackathon**.

---

## 🚀 Key Capabilities

### 1. 🌳 Product Explorer & Multi-Level BOM
- **Automated Hierarchy Traversal**: Recursively maps parent-child assembly relationships from `<ProductInst>` and `<Product>` XML nodes.
- **Interactive Tree Navigation**: Expandable tree view with instance identifiers, declared masses, material properties, and revision indices.
- **Component Inspector**: Real-time search across names and PLM IDs (`prd-...`) with detailed property cards.

### 2. ⚠️ Risk Intelligence
- **Missing Material Audit**: Automatically flags components lacking assigned materials (critical for CAE simulations and REACH/RoHS compliance).
- **Lifecycle Maturity Tracking**: Highlights readiness risks across design release states (detects `IN_WORK` vs `RELEASED` states).
- **Mass Pareto Analysis**: Ranks the top 10 mass drivers across the 100.10 kg assembly.

### 3. 🔄 Change Impact Analysis (Where-Used)
- **Bottom-Up Impact Propagation**: Given any part, executes a reverse traversal (`Instancing` → `Owned`) to identify all affected parent assemblies up to the root.
- **Mass Delta Simulation**: Calculates projected system weight changes upon substituting components or materials.
- **Traceable Breadcrumbs**: Displays exact upward hierarchy paths (`Level 1 -> Level 2 -> Root`).

### 4. 🤖 PLM AI Assistant
- Natural language query interface powered by rule-based retrieval.
- Answers questions about materials (e.g. *"What parts use Aluminium?"*), heaviest components, and missing material audits.
- **Mandatory Traceable Citations**: Appends verified PLM IDs as sources for every answer.

---

## 🛠️ Architecture & Tech Stack

- **Data Engine**: Python `xml.etree.ElementTree`, SQLite (in-memory with B-tree indexing on foreign keys), and Pandas.
- **Hierarchical Engine**: Custom depth-first (`build_bom_tree`) and breadth-first (`get_where_used`) graph algorithms.
- **Frontend Dashboard**: Streamlit (`app.py`) with responsive UI and custom styling.

---

## 📦 Getting Started

### Prerequisites
- Python 3.10+
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shubhu1-ai/PLM_Hackathon.git
   cd PLM_Hackathon
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Dashboard:**
   ```bash
   streamlit run app.py
   ```

4. Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```text
├── XPDMXML_ECAR_PLM.xml      # 3DEXPERIENCE PLM XML extraction (BOM & metadata)
├── P7_PLM_ESILV_VF.pptx      # Challenge brief & problem statement
├── plm_parser.py             # XML parser & indexed SQLite schema setup
├── plm_logic.py              # BOM tree, Where-Used, & Mass calculation engine
├── app.py                    # Streamlit Dashboard (4 tabs)
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```
