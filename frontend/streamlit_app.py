import streamlit as st
import requests
import base64
from io import BytesIO

st.set_page_config(page_title="Research Assistant", layout="centered")
st.title("🧾 Team 6 Research Topic : Product Demand Analysis")

# --- Tool Description ---
st.markdown(
    """
    **Welcome to the Research Assistant!** 

    This tool is designed to help analysts and business users uncover **trending products and brands** across major retail platforms like **Amazon, Walmart, Target, and YouTube**.  
    By analyzing onsite search volume data from the web, the assistant reveals:  
    - What consumers are actively searching for.  
    - How demand is shifting over time.  
    - Which products are gaining or losing popularity.  

    Powered by a **multi-agent architecture**, this assistant combines **data retrieval**, **external research**, and **automated analysis** into one cohesive, interactive tool.  

    
    """
)

backend_base_url = "http://localhost:8000"

# --- Query Input ---
query = st.text_input("Ask your research question below...")

# Placeholder for displaying the response
response_placeholder = st.empty()

if query:
    with st.spinner("Thinking..."):
        try:
            res = requests.post(f"{backend_base_url}/use-all-agents/", params={"query": query})
            result = res.json()["result"]
            response_placeholder.markdown(result)
        
        except Exception as e:
            error_text = f"Error: {e}"
            response_placeholder.error(error_text)