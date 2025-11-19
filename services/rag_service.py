# rag_manager.py
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from config.config import FAISS_SUFFIX, OFFSET_SUFFIX, OPENAI_API_KEY
from utils.utils import get_path_to_simple_history_file

GLOBAL_RAG_MANAGERS_DICT: dict[str, "RAGManager"] = {}

class RAGManager:
    """
    One instance == one source file.
    Handles incremental FAISS updates and RAG queries.
    """

    def __init__(
        self,
        docs_path: Path,
        *,
        index_dir: Optional[str | Path] = None,
        offset_file: Optional[str | Path] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        k: int = 2,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        embeddings: Optional[OpenAIEmbeddings] = None,
    ):
        self.docs_path = docs_path
        self.index_dir = Path(index_dir or f"{docs_path.parent}/{docs_path.stem}{FAISS_SUFFIX}")
        self.offset_file = Path(offset_file or f"{docs_path.parent}/{docs_path.stem}{OFFSET_SUFFIX}")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k = k
        self.model_name = model_name
        self.temperature = temperature

        self.embeddings = embeddings or OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        self.vectorstore = self._load_or_create_index()
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        self.rag_chain = self._get_context_docs()

    # ------------------------------------------------------------------ #
    #                     FAISS index handling
    # ------------------------------------------------------------------ #
    def _load_or_create_index(self) -> FAISS:
        if self.index_dir.exists():
            print(f"[{self.docs_path.name}] Loading index from {self.index_dir}")
            return FAISS.load_local(
                str(self.index_dir),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        print(f"[{self.docs_path.name}] Creating empty index")
        vs = FAISS.from_texts([""], self.embeddings)
        self._save_offset(0)
        return vs

    # ------------------------------------------------------------------ #
    #                     Offset handling
    # ------------------------------------------------------------------ #
    def _get_offset(self) -> int:
        if self.offset_file.exists():
            return int(self.offset_file.read_text().strip())
        return 0

    def _save_offset(self, offset: int) -> None:
        self.offset_file.write_text(str(offset))

    # ------------------------------------------------------------------ #
    #                     RAG chain
    # ------------------------------------------------------------------ #
    def _build_rag_chain(self):
        template = """{user_message}
        
        Полезный контекст: {context}
"""
        prompt = ChatPromptTemplate.from_template(template)
        llm = ChatOpenAI(model=self.model_name, temperature=self.temperature, api_key=OPENAI_API_KEY)
        answer_chain = prompt | llm | StrOutputParser()

        return RunnableParallel(
            {"context": self.retriever, "user_message": RunnablePassthrough()}
        ).assign(answer=answer_chain)

    def _get_context_docs(self):
        return RunnableParallel(
            {"context": self.retriever, "user_message": RunnablePassthrough()}
        )

    # ------------------------------------------------------------------ #
    #                     Public API
    # ------------------------------------------------------------------ #
    def update_index(self) -> None:
        """Read only the *new* part of the file and add it to FAISS."""
        if not self.docs_path.exists():
            print(f"[{self.docs_path.name}] File not found")
            return

        offset = self._get_offset()
        file_size = self.docs_path.stat().st_size

        if offset >= file_size:
            print(f"[{self.docs_path.name}] No new data")
            return

        print(f"[{self.docs_path.name}] Processing {offset} → {file_size}")
        with open(self.docs_path, "r", encoding="utf-8") as f:
            f.seek(offset)
            new_text = f.read()
            new_pos = f.tell()

        if not new_text.strip():
            print(f"[{self.docs_path.name}] New part is empty")
            self._save_offset(new_pos)
            return

        chunks = [c for c in self.splitter.split_text(new_text) if c.strip()]
        if chunks:
            print(f"[{self.docs_path.name}] Adding {len(chunks)} new chunks")
            self.vectorstore.add_texts(chunks)
            self.vectorstore.save_local(str(self.index_dir))
        else:
            print(f"[{self.docs_path.name}] No useful chunks")

        self._save_offset(new_pos)

    def query(self, question: str) -> dict:
        """Run RAG and return context + answer."""
        return self.rag_chain.invoke(question)

    def delete_files(self) -> None:
        """Delete crated files"""
        for path in [self.offset_file, self.index_dir, self.docs_path]:
            if path.exists():
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)

    @staticmethod
    def pretty_print(result: dict) -> None:
        print("\n=== КОНТЕКСТ ===")
        for i, doc in enumerate(result["context"], 1):
            print(f"\nЧанк {i}:")
            print(doc.page_content)
            print("-" * 50)
        print("\n=== ОТВЕТ ===")
        print(result["answer"])


# ---------------------------------------------------------------------- #
#   Factory – create a manager for *every* file you need
# ---------------------------------------------------------------------- #
def _build_manager(
    docs_path: str | Path,
) -> RAGManager:
    """
    Returns a RAGManager
    All managers share the same **common_kwargs** (chunk size, k, model …)
    """
    path = Path(docs_path)
    manager = RAGManager(docs_path=path)
    manager.update_index()
    return manager

def get_or_create_rag_manager(
    docs_path: str | Path,
) -> RAGManager:
    manager = GLOBAL_RAG_MANAGERS_DICT.get(docs_path, None)

    if manager is None:
        manager = _build_manager(docs_path)
        GLOBAL_RAG_MANAGERS_DICT[docs_path] = manager

    return manager

def get_context(
    chat_id: int,
    user_message: str,
) -> list[str]:
    docs_path: str|Path = get_path_to_simple_history_file(chat_id)
    manager = get_or_create_rag_manager(docs_path)
    response: dict = manager.query(user_message)
    context: list[str] = [c.page_content for c in response["context"]]
    return context

def delete_manager_and_clear_history(
    docs_path: str | Path,
) -> None:
    manager = GLOBAL_RAG_MANAGERS_DICT.pop(docs_path, None)
    if not manager:
        manager = get_or_create_rag_manager(docs_path)
    if manager:
        manager.delete_files()
        GLOBAL_RAG_MANAGERS_DICT.pop(docs_path, None)









