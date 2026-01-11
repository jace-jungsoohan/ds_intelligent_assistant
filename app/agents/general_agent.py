from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

# Helper class for a conversational agent
class GeneralAgent:
    def __init__(self):
        self.llm = ChatVertexAI(
            model_name="gemini-3.0-flash",
            project=settings.PROJECT_ID,
            location=settings.LOCATION,
            temperature=0.7 # Sligthly higher temp for better conversation
        )
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are 'Willog Intelligent Assistant', an AI assistant for logistics data analysis.
        
        **Your Capabilities:**
        1. **Data Analysis**: You can query the database for shipment volumes, damage rates, shock events, temperature excursions, etc.
        2. **Risk Management**: You can identify high-risk routes and provide heatmaps.
        3. **Documentation**: You can retrieve information from internal reports and guidelines (e.g., Whitepaper).
        
        **Your Goal:**
        - Answer general questions, greetings, and definitions clearly and professionally.
        - Explain what you can do.
        - If the user asks for specific data (numbers, stats) that you cannot provide directly, politely explain that you can query the database if they ask specifically (e.g., "Show me the damage rate for Vietnam").
        
        **Tone:**
        Professional, helpful, and concise. Korean language is preferred.
        
        Previous Conversation:
        {chat_history}
        
        User Question: {question}
        Answer:
        """)
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def process_query(self, question: str, chat_history: list = None):
        # Format history logic
        history_str = ""
        if chat_history:
            # Take last 5 turns to save tokens
            recent_history = chat_history[-10:] 
            for msg in recent_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"
        
        try:
            return self.chain.invoke({"question": question, "chat_history": history_str})
        except Exception as e:
            return f"죄송합니다. 일반 대화를 처리하는 중 오류가 발생했습니다: {str(e)}"

# Singleton Instance
general_agent = GeneralAgent()
