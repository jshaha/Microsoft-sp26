from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.runnables import RunnableSequence
from langchain_anthropic import AnthropicChatMessage, ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

def make_agent_chain(profile):
    return (
        RunnableLambda(lambda inputs: build_prompt(profile, inputs))
        | llm
        | RunnableLambda(parse_pick)
    )

parallel_agents = RunnableParallel(
    executive=make_agent_chain(PROFILES["EXECUTIVE"]),
    financial_analyst=make_agent_chain(PROFILES["FINANCIAL_ANALYST"]),
    marketing_specialist=make_agent_chain(PROFILES["MARKETING_SPECIALIST"]),
    common_man=make_agent_chain(PROFILES["COMMON_MAN"]),
)

pipeline = (
    RunnableLambda(generate_pool)
    | parallel_agents 
    | RunnableLambda(run_algos)
    | RunnableLambda(update_history)
)

result = pipeline.invoke({"seed": "Jensen Huang's vision of AI agents everywhere aligns perfectly with ServiceNow's core business model. ServiceNow's stock has been dragged down by the SaaS sell-off, but its plummet is undeserved. Investors are afraid of AI disrupting SaaS companies, but ServiceNow's platform enables AI business disruption. 10 stocks we like better than Nvidia › Years ago, E.F. Hutton ran a commercial that proclaimed, "When E.F. Hutton speaks, people listen." We could perhaps replace E.F. Hutton with Jensen Huang in that statement today. When the Nvidia (NASDAQ: NVDA) CEO speaks, people listen. And Huang spoke at length at his company's 2026 GTC AI conference last week.", "history": {}})