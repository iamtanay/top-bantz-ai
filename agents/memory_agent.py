from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain.memory import ConversationBufferMemory
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
import streamlit as st
from datetime import datetime, timedelta


class MemoryInput(BaseModel):
    """Input schema for memory operations"""
    player_name: str = Field(description="Name of the player")
    fact: Optional[str] = Field(default=None, description="Fact to store")
    action: str = Field(description="Action to perform: 'store', 'retrieve', 'check_duplicate'")


class MemoryStoreTool(BaseTool):
    """Tool for storing facts in memory"""
    name: str = "store_fact"
    description: str = "Store a fact about a player to avoid repetition"
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        player_name: str,
        fact: str,
        action: str = "store",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            if "shown_facts" not in st.session_state:
                st.session_state.shown_facts = {}

            if "fact_timestamps" not in st.session_state:
                st.session_state.fact_timestamps = {}

            st.session_state.shown_facts[player_name] = fact
            st.session_state.fact_timestamps[player_name] = datetime.now()

            return f"Successfully stored fact for {player_name}"
        except Exception as e:
            return f"Error storing fact: {str(e)}"


class MemoryRetrieveTool(BaseTool):
    """Tool for retrieving stored facts"""
    name: str = "retrieve_facts"
    description: str = "Retrieve previously shown facts for a player"
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        player_name: str,
        action: str = "retrieve",
        fact: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            if "shown_facts" not in st.session_state:
                return f"No facts stored for {player_name}"

            stored_fact = st.session_state.shown_facts.get(player_name)
            if stored_fact:
                if "fact_timestamps" in st.session_state:
                    timestamp = st.session_state.fact_timestamps.get(player_name)
                    if timestamp and datetime.now() - timestamp < timedelta(hours=1):
                        return f"Recent fact for {player_name}: {stored_fact}"

                return f"Stored fact for {player_name}: {stored_fact}"
            else:
                return f"No facts stored for {player_name}"
        except Exception as e:
            return f"Error retrieving facts: {str(e)}"


class MemoryCheckTool(BaseTool):
    """Tool for checking if a fact is a duplicate"""
    name: str = "check_duplicate"
    description: str = "Check if a fact has been shown recently to avoid repetition"
    args_schema: Type[BaseModel] = MemoryInput

    def _run(
        self,
        player_name: str,
        fact: str,
        action: str = "check_duplicate",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            if "shown_facts" not in st.session_state:
                return "No duplicates found - fact is new"

            stored_fact = st.session_state.shown_facts.get(player_name)
            if stored_fact and stored_fact.lower().strip() == fact.lower().strip():
                return f"Duplicate detected - this fact was already shown for {player_name}"

            return "No duplicates found - fact is new"
        except Exception as e:
            return f"Error checking duplicates: {str(e)}"


class MemoryAgent:
    """Agent responsible for managing memory and avoiding repetition"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(temperature=0)
        self.tools = [
            MemoryStoreTool(),
            MemoryRetrieveTool(),
            MemoryCheckTool()
        ]
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a memory management specialist for a football commentary system. 
Your job is to prevent repetition and manage the context of what information has been shared.

Your capabilities:
1. Store facts about players with timestamps
2. Retrieve previously shown facts
3. Check for duplicates to avoid repetition
4. Manage memory cleanup for optimal performance

When managing memory:
- Always check for duplicates before allowing new facts to be used
- Consider recency - facts shown very recently should be avoided
- Keep track of what's been shared to maintain engaging, fresh content
- Help maintain context across different commentary sessions"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=False)

    def store_fact(self, player_name: str, fact: str) -> str:
        try:
            result = self.agent_executor.invoke({
                "input": f"Store this fact for {player_name}: {fact}"
            })
            return result["output"]
        except Exception as e:
            return f"Error in MemoryAgent store: {str(e)}"

    def check_duplicate(self, player_name: str, fact: str) -> bool:
        try:
            result = self.agent_executor.invoke({
                "input": f"Check if this is a duplicate fact for {player_name}: {fact}"
            })
            return "duplicate detected" in result["output"].lower()
        except Exception as e:
            print(f"Error in MemoryAgent duplicate check: {e}")
            return False

    def get_stored_facts(self, player_name: str) -> List[str]:
        try:
            result = self.agent_executor.invoke({
                "input": f"Retrieve all stored facts for {player_name}"
            })
            if "No facts stored" in result["output"]:
                return []
            return [result["output"]]
        except Exception as e:
            print(f"Error in MemoryAgent retrieve: {e}")
            return []

    def as_tool(self) -> BaseTool:
        """Return this agent as a tool for use by other agents"""

        class MemoryAgentTool(BaseTool):
            name: str = "memory_agent"
            description: str = "Manage memory to avoid repetition and track shown facts"
            args_schema: Type[BaseModel] = MemoryInput

            def _run(
                self,
                player_name: str,
                action: str,
                fact: Optional[str] = None,
                run_manager: Optional[CallbackManagerForToolRun] = None
            ) -> str:
                agent = MemoryAgent()
                if action == "store" and fact:
                    return agent.store_fact(player_name, fact)
                elif action == "check_duplicate" and fact:
                    is_duplicate = agent.check_duplicate(player_name, fact)
                    return f"Duplicate: {is_duplicate}"
                elif action == "retrieve":
                    facts = agent.get_stored_facts(player_name)
                    return f"Stored facts: {facts}" if facts else "No facts stored"
                else:
                    return "Invalid action or missing parameters"

        return MemoryAgentTool()


# Backward compatibility function
def remember_fact(player_name: str, fact: str) -> None:
    try:
        agent = MemoryAgent()
        agent.store_fact(player_name, fact)
    except Exception as e:
        print(f"Error in remember_fact: {e}")