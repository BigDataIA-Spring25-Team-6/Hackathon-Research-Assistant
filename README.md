# Agentic RAG with LangGraph for Product Demand Analysis

## Team Members
- **Aditi Ashutosh Deodhar**  002279575  
- **Lenin Kumar Gorle**       002803806  
- **Poorvika Girish Babu**    002801388

## Project Overview
### Problem Statement

In a rapidly evolving digital commerce landscape, understanding real-time consumer demand and competitive positioning is crucial for brands, investors, and analysts. However, insights are fragmented across
multiple platforms like Amazon, Target, Walmart, and YouTube, making it challenging to track search trends. This project aims to develop a multi-agent research assistant powered by LangGraph, integrating Snowflake,
Web and Image Agent to help Stakeholders take comprehensive decision making Strategies based on the market trend. 

### Methodology
This project aims to develop a multi-agent research assistant powered by LangGraph, integrating:

-Snowflake for querying structured onsite search volume data from Similarweb
-Web Search Agent for retrieving real-time news and consumer sentiment across the web
-Image Agent to generate visual insights on emerging product trends

### Scope
```
The desired outcome is a streamlined application that empowers users to generate consolidated market research reports using natural language queries, track product and brand trends across major platforms, and receive actionable insights in real-time.

Key requirements and constraints include:
-Integrating Similarweb search volume data through secure Snowflake connectivity.
-Enabling real-time web search using Tavily for trend validation and news insights.
-Generating visual summaries of product trends via an integrated Image Agent.
-Orchestrating multi-agent collaboration using LangGraph.
```

## Technologies Used
```
FastAPI
Streamlit
LangGraph
Snowflake
Tavily API

```

## Architecture Diagram
![image](https://github.com/user-attachments/assets/da753b37-c955-4f03-9b1f-6ab3217c86a5)


## Prerequisites
```
-Python 3.10+
-OpenAI API key
-Streamlit installed
-FastAPI framework
-Tavilly API Key
```

## Set Up the Environment
```sh
# Clone the repository
git clone https://github.com/YourOrg/Hackathon-Research-Assistant.git
cd Hackathon-Research-Assistant

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate     # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
# Create a .env file with your Snowflake, Tavily, and Image Agent credentials

# Run FastAPI backend (inside /api folder)
cd api
uvicorn fastapi_backend:app --host 0.0.0.0 --port 8000 --reload

# Run Streamlit frontend (in a new terminal, inside /frontend folder)
cd ../frontend
streamlit run streamlit_app.py


```

## Project Structure

```

ASSIGNMENT05-PART-01/
├── agents/              # Custom agents like snowflake_agent, web_agent, image_agent
│
├── api/                 # FastAPI backend code
│   ├── fastapi_backend.py   # Main backend entry point
│   ├── ...                  # Other backend routes and logic
│
├── frontend/            # Streamlit-based frontend UI
│   ├── streamlit_app.py     # Main Streamlit app
│   ├── ...                  # Additional UI components or helpers
│
├── langgraph_code/      # LangGraph workflows, graph logic, and tool orchestration
│   ├── langgraph_flow.py    # Core LangGraph agent flow logic
│
├── utils/               # Utility modules (e.g., Snowflake connector, environment helpers)
│   ├── snowflake_connector.py
│
├── .gitignore           # Git ignore file
│
├── AiUseDisclosure.md   # AI usage disclosure and project description
│
├── requirements.txt     # Root dependencies file



```
