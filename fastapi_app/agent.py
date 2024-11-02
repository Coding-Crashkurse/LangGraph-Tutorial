from typing import Annotated, Any, Dict, List, TypedDict

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI  # Corrected import
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

load_dotenv()


# Define the tools using the @tool decorator
@tool
def get_weather(city: str) -> str:
    """Get the weather information for a given city."""
    return f"The weather in {city} is always 30°C."


@tool
def get_air_quality(city: str) -> str:
    """Get the air quality information for a given city."""
    return f"The air quality in {city} is 'Good' with an AQI of 42."


@tool
def default_answer() -> str:
    """Provide a default response when unable to answer."""
    return "I'm sorry, I can't answer that."


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    on_topic: str
    classification: str
    system_message: SystemMessage


get_weather_tools = [get_weather]
get_air_quality_tools = [get_air_quality]
default_answer_tools = [default_answer]

# Instantiate the language models with async support
supervisor_llm = ChatOpenAI(temperature=0)
weather_llm = ChatOpenAI(temperature=0).bind_tools(get_weather_tools)
air_quality_llm = ChatOpenAI(temperature=0).bind_tools(get_air_quality_tools)
off_topic_llm = ChatOpenAI(temperature=0).bind_tools(default_answer_tools)


# Asynchronous functions to invoke the models
async def call_weather_model(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    system_message = SystemMessage(
        content="You are WeatherBot. Answer the user's weather-related questions only in French."
    )
    conversation = [system_message] + messages
    response = await weather_llm.ainvoke(conversation)
    return {"messages": state["messages"] + [response]}


async def call_air_quality_model(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    system_message = SystemMessage(
        content="You are AirQualityBot. Provide air quality information in a very formal and polite manner."
    )
    conversation = [system_message] + messages
    response = await air_quality_llm.ainvoke(conversation)
    return {"messages": state["messages"] + [response]}


async def call_off_topic_model(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    system_message = SystemMessage(
        content="You are OffTopicBot. Apologize to the user and explain that you cannot help with their request, but do so in a friendly tone."
    )
    conversation = [system_message] + messages
    response = await off_topic_llm.ainvoke(conversation)
    return {"messages": state["messages"] + [response]}


def should_continue_weather(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "weather_tools"
    return END


def should_continue_air_quality(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "air_quality_tools"
    return END


def should_continue_off_topic(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "off_topic_tools"
    return END


class SupervisorDecision(BaseModel):
    """Decision made by the supervisor agent."""

    classification: str = Field(
        description="Classify the message as 'weather', 'air_quality', or 'other'"
    )


async def call_supervisor_model(state: AgentState) -> AgentState:
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    system_prompt = """You are a supervisor agent that decides whether the user's message is on topic and classifies it.

    Analyze the user's message and decide:

    Classify it as 'weather', 'air_quality', or 'other' if on topic.

    Provide your decision in the following structured format:
        "classification": "weather" or "air_quality" or "other"
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "User Message:\n\n{user_message}")]
    )

    structured_supervisor_llm = supervisor_llm.with_structured_output(
        SupervisorDecision
    )
    evaluator = prompt | structured_supervisor_llm

    result = await evaluator.ainvoke({"user_message": last_message})

    classification = result.classification
    state["classification"] = classification

    return state


weather_tool_node = ToolNode(tools=[get_weather])
air_quality_tool_node = ToolNode(tools=[get_air_quality])
off_topic_tool_node = ToolNode(tools=[default_answer])


def supervisor_router(state: AgentState) -> str:
    classification = state.get("classification", "")
    if classification == "weather":
        return "weather_model"
    elif classification == "air_quality":
        return "air_quality_model"
    else:
        return "off_topic_model"


workflow = StateGraph(AgentState)

workflow.add_node("supervisor_agent", call_supervisor_model)

workflow.add_node("weather_model", call_weather_model)
workflow.add_node("weather_tools", weather_tool_node)

workflow.add_node("air_quality_model", call_air_quality_model)
workflow.add_node("air_quality_tools", air_quality_tool_node)

workflow.add_node("off_topic_model", call_off_topic_model)
workflow.add_node("off_topic_tools", off_topic_tool_node)

workflow.add_edge(START, "supervisor_agent")
workflow.add_conditional_edges(
    "supervisor_agent",
    supervisor_router,
    ["weather_model", "air_quality_model", "off_topic_model"],
)

workflow.add_conditional_edges(
    "weather_model", should_continue_weather, ["weather_tools", END]
)
workflow.add_edge("weather_tools", "weather_model")

workflow.add_conditional_edges(
    "air_quality_model", should_continue_air_quality, ["air_quality_tools", END]
)
workflow.add_edge("air_quality_tools", "air_quality_model")

workflow.add_conditional_edges(
    "off_topic_model", should_continue_off_topic, ["off_topic_tools", END]
)
workflow.add_edge("off_topic_tools", "off_topic_model")

app = workflow.compile()

if __name__ == "__main__":
    from langchain.schema import HumanMessage
    import asyncio

    async def main():
        result = await app.ainvoke(
            {"messages": [HumanMessage(content="How is the weather in Munich?")]}
        )
        print(result)

    asyncio.run(main())
