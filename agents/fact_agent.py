from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from typing import Optional, Type, List
from pydantic import BaseModel, Field


class FactInput(BaseModel):
    player_name: str = Field(description="The name of the player to get facts for")
    exclude_facts: Optional[List[str]] = Field(
        default=None,
        description="List of facts to exclude (to avoid repetition)"
    )


class GoogleFactTool(BaseTool):
    name: str = "search_google_for_fact"
    description: str = "Search Google for recent news or interesting facts about a football player"
    args_schema: Type[BaseModel] = FactInput

    def _run(
        self,
        player_name: str,
        exclude_facts: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            tavily_tool = TavilySearchResults(k=5)
            query = f"latest interesting news or fact about {player_name} football"
            results = tavily_tool.run(query)

            if not results:
                return f"No relevant news found for {player_name}."

            for result in results:
                summary = result.get("content") or result.get("snippet")
                if summary and not any(fact.lower() in summary.lower() for fact in exclude_facts or []):
                    return f"{summary} (Source: {result.get('url')})"

            return f"No new or unique facts found for {player_name}."
        except Exception as e:
            return f"Error fetching Google facts for {player_name}: {str(e)}"


class FactAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool = GoogleFactTool()
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        tools = [self.tool]
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a football facts specialist. Your job is to retrieve interesting and engaging facts about football players.

Use the search_google_for_fact tool to fetch dynamic, real-time information about the player.
Avoid repeating previously used facts, and always pick something engaging or unexpected.

Facts should be suitable for sports commentary, fun trivia, or insightful narrative elements.
If nothing is found, return a graceful message."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def get_fact(self, player_name: str, exclude_facts: Optional[List[str]] = None) -> str:
        try:
            input_text = f"Get an interesting fact about player: {player_name}"
            if exclude_facts:
                input_text += f" (exclude these facts: {', '.join(exclude_facts)})"
            result = self.agent_executor.invoke({"input": input_text})
            return result["output"]
        except Exception as e:
            return f"Error in FactAgent: {str(e)}"

    def as_tool(self) -> BaseTool:
        class FactAgentTool(BaseTool):
            name: str = "fact_agent"
            description: str = "Get interesting facts about a football player using their name"
            args_schema: Type[BaseModel] = FactInput

            def _run(
                self,
                player_name: str,
                exclude_facts: Optional[List[str]] = None,
                run_manager: Optional[CallbackManagerForToolRun] = None
            ) -> str:
                agent = FactAgent(ChatOpenAI(temperature=0.3))
                return agent.get_fact(player_name, exclude_facts)

        return FactAgentTool()


# Backward compatibility
def fact_agent(player_name: str) -> str:
    from config import OPENAI_API_KEY
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.3, model="gpt-4o")
    agent = FactAgent(llm)
    return agent.get_fact(player_name)
