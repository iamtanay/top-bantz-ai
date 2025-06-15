from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field

from services.football_api import get_player_stat


class StatInput(BaseModel):
    """Input schema for StatAgent"""
    player_id: str = Field(description="The ID of the player to get stats for")


class StatTool(BaseTool):
    """Tool for getting player statistics"""
    name: str = "get_player_stat"
    description: str = "Get statistical data for a football player by their ID"
    args_schema: Type[BaseModel] = StatInput
    
    def _run(
        self, 
        player_id: str, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get player statistics"""
        try:
            stat = get_player_stat(player_id)
            if stat.startswith("No data"):
                return f"No statistical data found for player ID: {player_id}"
            return stat
        except Exception as e:
            return f"Error retrieving stats for player {player_id}: {str(e)}"


class StatAgent:
    """Agent responsible for retrieving player statistics"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool = StatTool()
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """Create the stat agent with its tools and prompt"""
        
        tools = [self.tool]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a football statistics specialist. Your job is to retrieve and interpret player statistics.

When given a player ID:
1. Use the get_player_stat tool to fetch the data
2. If no data is found, clearly indicate this
3. If data is found, return it in a clear, structured format
4. Handle any errors gracefully

Be concise but informative in your responses."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)
    
    def get_stat(self, player_id: str) -> str:
        """Get statistics for a player"""
        try:
            result = self.agent_executor.invoke({
                "input": f"Get statistics for player with ID: {player_id}"
            })
            return result["output"]
        except Exception as e:
            return f"Error in StatAgent: {str(e)}"
    
    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for use by other agents"""
        
        class StatAgentTool(BaseTool):
            name: str = "stat_agent"
            description: str = "Get statistical data for a football player using their ID"
            args_schema: Type[BaseModel] = StatInput
            
            def _run(
                self, 
                player_id: str, 
                run_manager: Optional[CallbackManagerForToolRun] = None
            ) -> str:
                agent = StatAgent(ChatOpenAI(temperature=0))
                return agent.get_stat(player_id)
        
        return StatAgentTool()


# Backward compatibility function
def stat_agent(player_id: str) -> str:
    """Legacy function for backward compatibility"""
    from config import OPENAI_API_KEY
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0, model="gpt-4o")
    agent = StatAgent(llm)
    return agent.get_stat(player_id)