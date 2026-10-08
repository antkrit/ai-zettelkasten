import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from zettelkasten.adapters.qdrant import QdrantNoteIndex, note_to_document
from zettelkasten.models import AtomicNote

VECTOR_SIZE = 8
COLLECTION = "atomic_notes"


def _index(client: QdrantClient) -> QdrantNoteIndex:
    return QdrantNoteIndex(
        client, COLLECTION, DeterministicFakeEmbedding(size=VECTOR_SIZE)
    )


def test_note_to_document_maps_fields() -> None:
    note = AtomicNote(
        title="Spaced repetition",
        content="Reviewing at increasing intervals strengthens memory.",
        tags=["memory", "learning"],
    )
    document = note_to_document(note)

    assert document.page_content == (
        "Spaced repetition\n\nReviewing at increasing intervals strengthens memory."
    )
    assert document.metadata == note.model_dump()
    assert document.id == note_to_document(note).id


def test_add_note_creates_collection_sized_from_embeddings() -> None:
    client = QdrantClient(":memory:")
    _index(client).add_note(AtomicNote(title="A", content="First idea.", tags=["a"]))

    vectors = client.get_collection(COLLECTION).config.params.vectors
    assert isinstance(vectors, VectorParams)
    assert vectors.size == VECTOR_SIZE


def test_reindexing_same_note_does_not_duplicate() -> None:
    client = QdrantClient(":memory:")
    note = AtomicNote(title="Kept", content="Indexed twice.", tags=[])

    _index(client).add_note(note)
    second = _index(client)
    second.add_note(note)
    second.add_note(AtomicNote(title="Added", content="Another idea.", tags=[]))

    assert client.get_collection(COLLECTION).points_count == 2


def test_add_note_rejects_collection_with_other_dimension() -> None:
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE * 2, distance=Distance.COSINE),
    )

    with pytest.raises(ValueError, match="stores 16-dim vectors.*produces 8-dim"):
        _index(client).add_note(AtomicNote(title="A", content="Idea.", tags=[]))


def test_search_round_trips_notes_ranked_by_similarity() -> None:
    client = QdrantClient(":memory:")
    index = _index(client)
    memory = AtomicNote(
        title="Memory", content="Spaced repetition helps memory.", tags=["m"]
    )
    cooking = AtomicNote(title="Cooking", content="Simmer onions slowly.", tags=["c"])
    index.add_note(memory)
    index.add_note(cooking)

    hits = index.search(note_to_document(memory).page_content, k=2)

    assert [hit.note for hit in hits] == [memory, cooking]
    assert hits[0].score == pytest.approx(1.0)


def test_search_requires_existing_collection() -> None:
    with pytest.raises(ValueError, match="does not exist"):
        _index(QdrantClient(":memory:")).search("anything")
