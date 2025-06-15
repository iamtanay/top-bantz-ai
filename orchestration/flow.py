from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

from agents.stat_agent import StatAgent
from agents.fact_agent import FactAgent
from agents.narration_agent import NarrationAgent
from agents.memory_agent import MemoryAgent
from config import OPENAI_API_KEY


class MultiAgentOrchestrator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=OPENAI_API_KEY
        )

        self.stat_agent = StatAgent(self.llm)
        self.fact_agent = FactAgent(self.llm)
        self.narration_agent = NarrationAgent(self.llm)
        self.memory_agent = MemoryAgent()

        self.orchestrator = self._create_orchestrator()

    def _create_orchestrator(self):
        tools = [
            self.stat_agent.as_tool(),
            self.fact_agent.as_tool(),
            self.narration_agent.as_tool(),
            self.memory_agent.as_tool()
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a football commentary orchestrator. Your job is to coordinate different agents to create engaging player commentary.

Available agents:
1. StatAgent - Gets player statistics
2. FactAgent - Retrieves interesting facts about players
3. NarrationAgent - Creates commentary from stats and facts
4. MemoryAgent - Manages what facts have been shown to avoid repetition

Your workflow should be:
1. First, get player stats using StatAgent
2. If stats are available, get a fact using FactAgent
3. Check memory to avoid repeating facts
4. Generate commentary using NarrationAgent
5. Store the fact in memory

Return a full final commentary paragraph.
"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

    async def run_agent_flow(self, player_id: str, player_name: str) -> Optional[Dict[str, Any]]:
        try:
            input_data = {
                "input": f"Create football commentary for player {player_name} (ID: {player_id}). "
                         f"Follow the workflow: get stats, check if valid, get facts, check memory for duplicates, "
                         f"generate commentary, and store fact in memory. Return only the final combined commentary."
            }
            result = await self._run_orchestrator_async(input_data)
            return self._parse_result(result)
        except Exception as e:
            print(f"Error in agent flow: {e}")
            return None

    async def _run_orchestrator_async(self, input_data: Dict[str, Any]) -> str:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                self.orchestrator.invoke,
                input_data
            )
        return result["output"]

    def _parse_result(self, result: str) -> Optional[Dict[str, Any]]:
        try:
            # Just pass the full commentary as-is
            return {
                "commentary": result.strip()
            }
        except Exception as e:
            print(f"Error parsing result: {e}")
            return None


# Convenience function
async def run_agent_flow(player_id: str, player_name: str) -> Optional[Dict[str, Any]]:
    orchestrator = MultiAgentOrchestrator()
    return await orchestrator.run_agent_flow(player_id, player_name)


# Synchronous wrapper
def run_agent_flow_sync(player_id: str, player_name: str) -> Optional[Dict[str, Any]]:
    return asyncio.run(run_agent_flow(player_id, player_name))
