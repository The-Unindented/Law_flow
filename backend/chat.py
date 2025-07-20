from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from core_agent.agent import root_agent
from google.genai.types import Content, Part

async def chat_with_law_agent(user_message):
    app_name = "my_agent_app"
    user_id = "user123"

    # Initialize the session service with a database URL
    db_url = "sqlite:///./my_agent_data.db"
    session_service = DatabaseSessionService(db_url=db_url)
    session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id
        )
    
    runner = Runner(
            agent=root_agent,
            app_name=app_name,
            session_service=session_service
        )

    user_message = Content(role='user', parts=[Part(text=user_message)])

    async for event in runner.run_async(
                            user_id=user_id, 
                            session_id=session.id, 
                            new_message=user_message
                        ):
        if event.is_final_response():
            if (
                event.content
                and event.content.parts
                and hasattr(event.content.parts[0], "text")
                and event.content.parts[0].text
            ):
                final_response = event.content.parts[0].text.strip()

    return final_response