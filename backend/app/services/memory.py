from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit import MemoryRecord


class MemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self._collection = self._build_chroma_collection()

    def _build_chroma_collection(self) -> Any | None:
        if self.settings.vector_backend.lower() != "chroma" or not self.settings.openai_api_key:
            return None
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError:
            return None

        embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.settings.openai_api_key,
            model_name="text-embedding-3-small",
        )
        client = chromadb.PersistentClient(path=self.settings.chroma_path)
        return client.get_or_create_collection(
            name="agent_memory",
            embedding_function=embedding_fn,
        )

    def remember(
        self,
        *,
        agent_name: str,
        run_id: str | None,
        key: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        embedding_id = str(uuid4())
        record = MemoryRecord(
            agent_name=agent_name,
            run_id=run_id,
            key=key,
            text=text,
            metadata_json=metadata or {},
            embedding_id=embedding_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        if self._collection:
            self._collection.add(
                ids=[embedding_id],
                documents=[text],
                metadatas=[{"agent_name": agent_name, "run_id": run_id or "", "key": key}],
            )
        return record

    def recall(self, *, agent_name: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._collection:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where={"agent_name": agent_name},
            )
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            return [
                {"text": document, "metadata": metadata}
                for document, metadata in zip(documents, metadatas, strict=False)
            ]

        tokens = [token for token in query.lower().split() if len(token) > 3][:8]
        filters = [MemoryRecord.text.ilike(f"%{token}%") for token in tokens]
        q = self.db.query(MemoryRecord).filter(MemoryRecord.agent_name == agent_name)
        if filters:
            q = q.filter(or_(*filters))
        records = q.order_by(desc(MemoryRecord.created_at)).limit(limit).all()
        return [
            {"text": record.text, "metadata": record.metadata_json or {}, "key": record.key}
            for record in records
        ]

