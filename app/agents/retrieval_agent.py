from typing import Dict, Any, List
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.core.config import settings

class RetrievalAgent:
    def __init__(self):
        # 1. Initialize Embeddings & LLM
        self.embeddings = VertexAIEmbeddings(
            model_name="textembedding-gecko@003",
            project=settings.PROJECT_ID,
            location=settings.LOCATION
        )
        self.llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=settings.PROJECT_ID,
            location=settings.LOCATION,
            temperature=0.2
        )
        
        # 2. Key Term Definitions (Glossary) provided by user
        # In a real scenario, this could be loaded from files.
        self.glossary_texts = [
            """
            [용어 정의] 운송 건수
            - 의미: 조회기간 동안 운송 완료되거나 운송 중인 운송 물량의 총 합을 의미합니다.
            """,
            """
            [용어 정의] 출고 건수
            - 의미: 조회기간 동안 출고가 된 운송 물량의 총 합을 의미합니다.
            - 주의사항: 조회기간 이전에 출고된 건은 합계에서 제외됩니다.
            """,
            """
            [용어 정의] 일탈률 (Deviation Rate)
            - 의미: 전체 센싱 횟수(로그 수) 대비 충격 이슈 발생 비율을 의미합니다.
            - 공식: (충격 이벤트 발생 횟수 / 전체 로그 수) * 100
            """
        ]
        
        # 3. Create Vector Store (In-Memory FAISS)
        # This runs once on startup.
        print("🏗️ RetrievalAgent: Building Vector Store...")
        try:
            self.vector_store = FAISS.from_texts(
                texts=self.glossary_texts,
                embedding=self.embeddings
            )
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 1})
            print("✅ RetrievalAgent: Vector Store ready.")
        except Exception as e:
            print(f"❌ RetrievalAgent: Vector Store failed to build: {e}")
            self.retriever = None

        # 4. RAG Prompt
        self.prompt = ChatPromptTemplate.from_template("""
        You are a helpful assistant explaining logistics terms based on the provided context.
        Use the following pieces of retrieved context to answer the user's question.
        If the answer is not in the context, say that you don't know based on the provided documents.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer (in Korean):
        """)
        
        if self.retriever:
            self.chain = (
                {"context": self.retriever, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
        else:
            self.chain = None

    def process_query(self, question: str, chat_history: list = None) -> Dict[str, Any]:
        """
        Retrieves relevant documents and answers the question.
        """
        if not self.chain:
            return {
                "question": question,
                "answer": "죄송합니다. 문서 검색 시스템 초기화에 실패하여 답변을 드릴 수 없습니다.",
                "source_documents": []
            }
            
        try:
            # Execute RAG Chain
            answer = self.chain.invoke(question)
            
            # Retrieve source docs manually for metadata (optional)
            docs = self.retriever.get_relevant_documents(question)
            source_contents = [doc.page_content.strip() for doc in docs]
            
            return {
                "question": question,
                "answer": answer,
                "source_documents": source_contents
            }
        except Exception as e:
            return {
                "question": question,
                "answer": f"문서 검색 중 오류가 발생했습니다: {e}",
                "source_documents": []
            }

# Singleton Instance
retrieval_agent = RetrievalAgent()
