from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field

from services.data_loader import get_player_fact


class FactInput(BaseModel):
    """Input schema for FactAgent"""
    player_name: str = Field(description="The name of the player to get facts for")
    exclude_facts: Optional[List[str]] = Field(
        default=None, 
        description="List of facts to exclude (to avoid repetition)"
    )


class FactTool(BaseTool):
    """Tool for getting player facts"""
    name: str = "get_player_fact"
    description: str = "Get interesting facts about a football player by their name"
    args_schema: Type[BaseModel] = FactInput
    
    def _run(
        self, 
        player_name: str, 
        exclude_facts: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get player facts"""
        try:
            fact = get_player_fact(player_name)
            
            # Check if this fact should be excluded
            if exclude_facts and fact in exclude_facts:
                return f"Fact for {player_name} was already shown recently. Please request a different fact."
            
            return fact
        except Exception as e:
            return f"Error retrieving fact for player {player_name}: {str(e)}"


class FactAgent:
    """Agent responsible for retrieving interesting player facts"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool = FactTool()
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """Create the fact agent with its tools and prompt"""
        
        tools = [self.tool]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a football facts specialist. Your job is to retrieve interesting and engaging facts about football players.

When given a player name:
1. Use the get_player_fact tool to fetch interesting information
2. Consider any facts that should be excluded to avoid repetition
3. Return the most engaging and relevant fact available
4. If no facts are available, suggest what type of information would be helpful

Focus on facts that would be interesting for commentary and fan engagement."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)
    
    def get_fact(self, player_name: str, exclude_facts: Optional[List[str]] = None) -> str:
        """Get an interesting fact about a player"""
        try:
            input_text = f"Get an interesting fact about player: {player_name}"
            if exclude_facts:
                input_text += f" (exclude these facts: {', '.join(exclude_facts)})"
            
            result = self.agent_executor.invoke({"input": input_text})
            return result["output"]
        except Exception as e:
            return f"Error in FactAgent: {str(e)}"
    
    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for use by other agents"""
        
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


# Backward compatibility function
def fact_agent(player_name: str) -> str:
    """Legacy function for backward compatibility"""
    from config import OPENAI_API_KEY
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.3, model="gpt-4o",)
    agent = FactAgent(llm)
    return agent.get_fact(player_name)