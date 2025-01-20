import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.title("Interactive Organogram Example")

# Define our nodes (people/roles/groups)
nodes = [
    Node(id="Board of Directors (BOD)", label="Board of Directors\n(BOD)", size=400, shape="box"),
    Node(id="Investors", label="Investors", size=200, shape="box"),
    Node(id="Other Stakeholders", label="Other\nStakeholders", size=200, shape="box"),
    Node(id="C-Level (RCS)", label="C-Level\n(RCS)", size=300, shape="box"),
    Node(id="CEO (Berman)", label="CEO\n(Berman)", size=200, shape="box"),
    Node(id="COO (Walthall)", label="COO\n(Walthall)", size=200, shape="box"),
    Node(id="CTO (Webb)", label="CTO\n(Webb)", size=200, shape="box"),
    Node(id="Senior Management", label="Senior\nManagement", size=300, shape="box"),
    Node(id="Head of Finance (James van Rensburg)", label="Head of Finance\n(James van Rensburg)", size=200, shape="box"),
    Node(id="Head of Partnerships (Leigh)", label="Head of Partnerships\n(Leigh)", size=200, shape="box"),
    Node(id="Head of Dev (Craig Berman)", label="Head of Dev\n(Craig Berman)", size=200, shape="box"),
    Node(id="Head of X (Liam Webb)", label="Head of X\n(Liam Webb)", size=200, shape="box"),
    Node(id="Team Members (Variable)", label="Team Members\n(Variable)", size=300, shape="box"),
    Node(id="Onboarding", label="Onboarding", size=200, shape="ellipse"),
    Node(id="Dev", label="Dev", size=200, shape="ellipse"),
    Node(id="Marketing / Sales (Outsourced)", label="Marketing / Sales\n(Outsourced)", size=200, shape="ellipse"),
    Node(id="Tech Support", label="Tech Support", size=200, shape="ellipse"),
]

# Define the edges (who reports to whom)
edges = [
    Edge(source="Board of Directors (BOD)", target="Investors"),
    Edge(source="Board of Directors (BOD)", target="Other Stakeholders"),
    Edge(source="Board of Directors (BOD)", target="C-Level (RCS)"),

    Edge(source="C-Level (RCS)", target="CEO (Berman)"),
    Edge(source="C-Level (RCS)", target="COO (Walthall)"),
    Edge(source="C-Level (RCS)", target="CTO (Webb)"),

    Edge(source="C-Level (RCS)", target="Senior Management"),

    Edge(source="Senior Management", target="Head of Finance (James van Rensburg)"),
    Edge(source="Senior Management", target="Head of Partnerships (Leigh)"),
    Edge(source="Senior Management", target="Head of Dev (Craig Berman)"),
    Edge(source="Senior Management", target="Head of X (Liam Webb)"),

    Edge(source="Senior Management", target="Team Members (Variable)"),

    Edge(source="Team Members (Variable)", target="Onboarding"),
    Edge(source="Onboarding", target="Dev"),
    Edge(source="Team Members (Variable)", target="Marketing / Sales (Outsourced)"),
    Edge(source="Team Members (Variable)", target="Tech Support"),
]

# Configure the interactive graph
config = Config(
    width=900,             # The width of the chart in px
    height=600,            # The height of the chart in px
    directed=True,         # Arrows on edges
    hierarchical=True,     # Use a hierarchical (top-down) layout
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A7",  # The color to highlight nodes on hover
    collapsible=True,      # Allows you to collapse/expand hierarchical nodes
    node={"labelProperty": "label"},
    link={"labelProperty": "label", "renderLabel": False},
)

agraph(nodes=nodes, edges=edges, config=config)
