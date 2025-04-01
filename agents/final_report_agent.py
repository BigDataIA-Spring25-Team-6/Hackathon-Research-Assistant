from pydantic import BaseModel, Field
from langchain_core.tools.structured import StructuredTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

class FinalReportInput(BaseModel):
    executive_summary: str = Field(..., description="Concise summary of key findings")
    market_overview: str = Field(..., description="Market trends and context")
    internal_insights: str = Field(..., description="Insights from internal or platform-specific data")
    quantitative_analysis: str = Field(..., description="Charts, stats, numerical insights")
    recommendations: str = Field(..., description="Actionable next steps")
    sources: str = Field(..., description="Sources used")

def _final_report_logic(**kwargs) -> str:
    # Convert keyword arguments to a FinalReportInput instance
    data = FinalReportInput(**kwargs)
    prompt = f"""
You are a business analyst, technical writer, who can write long reports and include images, sources, links in detail, tasked with preparing a detailed,
professional Gartner-style report. You have to write a comprehensive 20–30 page stakeholder-facing research report (6000–12000 words) in markdown format.

Expand the following key insights into detailed sections using structured language, bullet points, numbered takeaways, and a clear professional tone. Add section headers and visual placeholders if needed.
Insert source images as actual images and also include video links properly.

Make sure report is not less than 30 pages. Use Following details for your idea expansion.

Make sure you expand the executive summary atleast 3 pages 3000 words, market overview to 3-4 pages with 4000 words, 
Quantitative analysis to 5-6 pages 6000 words, Recommendations with 6 pages 6000 words. Providing insights of each report field below.

---
Executive Summary:
{data.executive_summary}

Market Overview:
{data.market_overview}

Internal Insights:
{data.internal_insights}

Quantitative Analysis:
{data.quantitative_analysis}

Recommendations:
{data.recommendations}

Sources:
{data.sources}
"""
    return llm.invoke(prompt).content

final_report_tool = StructuredTool.from_function(
    name="final_report_tool",
    description="Compile a detailed, multi-page stakeholder report in markdown",
    func=_final_report_logic,
    args_schema=FinalReportInput
)