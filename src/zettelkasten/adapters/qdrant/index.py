from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID, uuid5

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from zettelkasten.models import AtomicNote

# Fixed namespace for note ids; never change it, or existing points get new ids.
NOTE_ID_NAMESPACE = UUID("a68ad001-4340-4960-97de-ecd91d8f1bfa")

logger = logging.getLogger(__name__)


def note_to_document(note: AtomicNote) -> Document:
    """Map an atomic note to a LangChain document for embedding storage.

    The id is derived from the note text, so re-indexing a note upserts it.
    """
    text = f"{note.title}\n\n{note.content}"
    return Document(
        id=str(uuid5(NOTE_ID_NAMESPACE, text)),
        page_content=text,
        metadata=note.model_dump(),
    )


@dataclass(frozen=True)
class SearchHit:
    note: AtomicNote
    score: float


class QdrantNoteIndex:
    """Embed AtomicNotes into a Qdrant collection and search them.

    The caller owns ``client``. The collection is created on the first
    ``add_note``, sized from the embedding model; it is never cleared.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection: str,
        embeddings: Embeddings,
    ) -> None:
        self._client = client
        self._collection = collection
        self._embeddings = embeddings
        self._store = QdrantVectorStore(
            client=client,
            collection_name=collection,
            embedding=embeddings,
            validate_collection_config=False,
        )
        self._collection_ready = False

    def add_note(self, note: AtomicNote) -> None:
        if not self._collection_ready:
            self._ensure_collection()
            self._collection_ready = True
        self._store.add_documents([note_to_document(note)])
        logger.debug("Indexed note: %s", note.title)

    def search(self, query: str, *, k: int = 5) -> list[SearchHit]:
        if not self._client.collection_exists(self._collection):
            raise ValueError(
                f"Qdrant collection {self._collection!r} does not exist. "
                "Index notes with --qdrant first."
            )
        results = self._store.similarity_search_with_score(query, k=k)
        return [
            SearchHit(note=AtomicNote.model_validate(document.metadata), score=score)
            for document, score in results
        ]

    def _ensure_collection(self) -> None:
        vector_size = len(self._embeddings.embed_query("dimension probe"))
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection %r", self._collection)
            return

        vectors = self._client.get_collection(self._collection).config.params.vectors
        existing_size = vectors.size if isinstance(vectors, VectorParams) else None
        if existing_size != vector_size:
            raise ValueError(
                f"Qdrant collection {self._collection!r} stores {existing_size}-dim "
                f"vectors, but the embedding model produces {vector_size}-dim vectors. "
                "Use another QDRANT_COLLECTION or delete the existing one."
            )
