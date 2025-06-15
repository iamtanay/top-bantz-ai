from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain.schema import HumanMessage, SystemMessage
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field


class NarrationInput(BaseModel):
    """Input schema for NarrationAgent"""
    player_name: str = Field(description="Name of the player")
    stat: str = Field(description="Statistical information about the player")
    fact: str = Field(description="Interesting fact about the player")
    style: Optional[str] = Field(
        default="energetic_commentator", 
        description="Commentary style (e.g., 'energetic_commentator', 'analytical', 'casual')"
    )


class CommentaryTool(BaseTool):
    """Tool for generating football commentary"""
    name: str = "generate_commentary"
    description: str = "Generate engaging football commentary from player stats and facts"
    args_schema: Type[BaseModel] = NarrationInput
    
    def _run(
        self, 
        player_name: str,
        stat: str,
        fact: str,
        style: str = "energetic_commentator",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Generate commentary"""
        try:
            # Style-specific prompts
            style_prompts = {
                "energetic_commentator": """
                Generate an energetic, exciting football commentary in the style of a passionate sports commentator.
                Use exclamation marks, dynamic language, and create excitement around the player's achievements.
                Make it sound like you're calling a live match!
                """,
                "analytical": """
                Generate analytical, data-driven commentary that focuses on the statistical significance
                and tactical implications of the player's performance. Be informative and insightful.
                """,
                "casual": """
                Generate casual, conversational commentary as if you're talking to a friend about
                the player. Keep it relaxed but engaging.
                """
            }
            
            style_prompt = style_prompts.get(style, style_prompts["energetic_commentator"])
            
            llm = ChatOpenAI(temperature=0.8)  # Higher temperature for creativity
            
            messages = [
                SystemMessage(content=f"""
                You are a professional football commentator. {style_prompt}
                
                Create compelling commentary that weaves together the statistical data and interesting facts
                about the player in a natural, engaging way.
                """),
                HumanMessage(content=f"""
                Create commentary for player: {player_name}
                Statistics: {stat}
                Interesting Fact: {fact}
                
                Blend these elements into engaging commentary that would captivate football fans.
                """)
            ]
            
            response = llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            return f"Error generating commentary: {str(e)}"


class NarrationAgent:
    """Agent responsible for creating engaging football commentary"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool = CommentaryTool()
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """Create the narration agent with its tools and prompt"""
        
        tools = [self.tool]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a master football commentator and storyteller. Your expertise lies in creating 
            captivating commentary that brings players to life for fans.

Your capabilities:
1. Transform dry statistics into exciting narratives
2. Weave interesting facts seamlessly into commentary
3. Adapt your style based on the context and audience
4. Create emotional connection between fans and players

When creating commentary:
- Make it vivid and engaging
- Use the player's stats and facts as building blocks
- Create a narrative that flows naturally
- Match the requested style and tone
- Keep the audience engaged throughout"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)
    
    def generate_commentary(
        self, 
        data: Dict[str, str], 
        style: str = "energetic_commentator"
    ) -> str:
        """Generate commentary from player data"""
        try:
            input_text = f"""
            Create engaging football commentary for {data['player']} using:
            - Statistics: {data['stat']}
            - Interesting fact: {data['fact']}
            - Style: {style}
            
            Make it compelling and broadcast-ready!
            """
            
            result = self.agent_executor.invoke({"input": input_text})
            return result["output"]
        except Exception as e:
            return f"Error in NarrationAgent: {str(e)}"
    
    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for use by other agents"""
        
        class NarrationAgentTool(BaseTool):
            name: str = "narration_agent"
            description: str = "Generate engaging football commentary from player statistics and facts"
            args_schema: Type[BaseModel] = NarrationInput
            
            def _run(
                self, 
                player_name: str,
                stat: str,
                fact: str,
                style: str = "energetic_commentator",
                run_manager: Optional[CallbackManagerForToolRun] = None
            ) -> str:
                agent = NarrationAgent(ChatOpenAI(temperature=0.8))
                data = {
                    "player": player_name,
                    "stat": stat,
                    "fact": fact
                }
                return agent.generate_commentary(data, style)
        
        return NarrationAgentTool()


# Backward compatibility function
def narration_agent(data: Dict[str, str]) -> str:
    """Legacy function for backward compatibility"""
    from config import OPENAI_API_KEY
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.8, model="gpt-4o")
    agent = NarrationAgent(llm)
    return agent.generate_commentary(data)