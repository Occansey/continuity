"""Drive the Continuity agent through the ClickHouse MCP server.

Needs the CLICKHOUSE_* environment (see docs/CLICKHOUSE.md) and Vertex credentials.
"""
import asyncio, sys
sys.path.insert(0, "src")
from continuity.agent import build_agent

async def main(goal: str):
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    runner = InMemoryRunner(agent=build_agent(), app_name="continuity")
    session = await runner.session_service.create_session(app_name="continuity", user_id="sup")
    async for ev in runner.run_async(
        user_id="sup", session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=goal)]),
    ):
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text: print(p.text)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "find a cross-scene continuity error"))
