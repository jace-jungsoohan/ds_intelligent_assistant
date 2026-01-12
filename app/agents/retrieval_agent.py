from typing import Dict, Any, List
# Removing FAISS and VertexEmbeddings dependencies to prevent initialization errors in restricted environments.
# Using simple Keyword/Semantic matching logic via LLM directly or Python strings for small glossary.

from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

class RetrievalAgent:
    def __init__(self):
        self.llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=settings.PROJECT_ID,
            location=settings.LOCATION,
            temperature=0.2
        )
        
        # In-memory Glossary (Simple Text)
        self.glossary_data = {
            "운송 건수": """
            [용어 정의] 운송 건수
            - 의미: 조회기간 동안 운송 완료되거나 운송 중인 운송 물량의 총 합을 의미합니다.
            """,
            "출고 건수": """
            [용어 정의] 출고 건수
            - 의미: 조회기간 동안 출고가 된 운송 물량의 총 합을 의미합니다.
            - 주의사항: 조회기간 이전에 출고된 건은 합계에서 제외됩니다.
            """,
            "일탈률": """
            [용어 정의] 일탈률 (Deviation Rate)
            - 의미: 전체 센싱 횟수(로그 수) 대비 충격 이슈 발생 비율을 의미합니다.
            - 공식: (충격 이벤트 발생 횟수 / 전체 로그 수) * 100
            """
        }
        
        # Simple RAG Prompt
        self.prompt = ChatPromptTemplate.from_template("""
        You are a helpful assistant explaining logistics terms.
        
        **Available Definitions:**
        {context}
        
        **User Question:** {question}
        
        **Instructions:**
        - Identify which term the user is asking about.
        - Explain the definition clearly in Korean using the provided context.
        - If the term is NOT in the context, politely say you don't have that definition.
        
        Answer (Korean):
        """)
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _retrieve_context(self, question: str) -> str:
        # Simple keyword matching
        relevant_texts = []
        for term, definition in self.glossary_data.items():
            if term in question or term.replace(" ", "") in question.replace(" ", ""):
                relevant_texts.append(definition)
        
        # If no exact keyword match, return all (since it's small) or let LLM decide
        if not relevant_texts:
            return "\n\n".join(self.glossary_data.values())
            
        return "\n\n".join(relevant_texts)

    def process_query(self, question: str, chat_history: list = None) -> Dict[str, Any]:
        """
        Retrieves relevant documents and answers the question.
        """
        try:
            # Simple Retrieval
            context = self._retrieve_context(question)
            
            # Generate Answer
            answer = self.chain.invoke({"context": context, "question": question})
            
            return {
                "question": question,
                "answer": answer,
                "source_documents": ["Global Glossary (Memory)"]
            }
        except Exception as e:
            return {
                "question": question,
                "answer": f"답변 생성 중 오류가 발생했습니다: {e}",
                "source_documents": []
            }

# Singleton Instance
retrieval_agent = RetrievalAgent()
