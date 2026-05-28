import os
import uuid
from typing import List
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer, CrossEncoder
from app.core.config import settings

# i used this model bcoz it was recommended in docs and its free
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIM = 384
TOP_K_RETRIEVE = 20

# load models once
_embedder = None
_reranker = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker

def get_qdrant():
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

def make_collection_if_not_exists():
    client = get_qdrant()
    existing = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )

# read pdf text
def read_pdf(path: str) -> str:
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def get_text(path: str) -> str:
    if path.endswith(".pdf"):
        return read_pdf(path)
    return read_txt(path)

# split text into chunks
def make_chunks(text: str) -> List[str]:
    chunks = []
    start = 0
    text = text.strip()
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def index_document(document_id: int, file_path: str, title: str) -> int:
    make_collection_if_not_exists()
    text = get_text(file_path)
    if not text.strip():
        raise ValueError("no text found in document")
    chunks = make_chunks(text)
    if not chunks:
        raise ValueError("could not split document into chunks")

    # make embeddings
    model = get_embedder()
    vectors = model.encode(chunks).tolist()

    # save to qdrant
    client = get_qdrant()
    points = []
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "document_id": document_id,
                "document_title": title,
                "chunk_text": chunk,
                "chunk_index": i
            }
        ))
    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    return len(chunks)

def semantic_search(query: str, top_k: int = 5) -> List[dict]:
    make_collection_if_not_exists()

    # embed query
    model = get_embedder()
    query_vec = model.encode(query).tolist()

    # search qdrant - get top 20 first
    client = get_qdrant()
    hits = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vec,
        limit=TOP_K_RETRIEVE,
        with_payload=True
    )
    if not hits:
        return []

    # rerank results to get best ones
    reranker = get_reranker()
    pairs = [(query, h.payload["chunk_text"]) for h in hits]
    scores = reranker.predict(pairs).tolist()

    # sort by score and return top_k
    combined = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {
            "document_id": h.payload["document_id"],
            "document_title": h.payload["document_title"],
            "chunk_text": h.payload["chunk_text"],
            "score": round(s, 4)
        }
        for h, s in combined
    ]

def get_document_context(document_id: int) -> List[str]:
    client = get_qdrant()
    results, _ = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        scroll_filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]),
        limit=200,
        with_payload=True
    )
    sorted_chunks = sorted(results, key=lambda p: p.payload.get("chunk_index", 0))
    return [p.payload["chunk_text"] for p in sorted_chunks]

def remove_document_embeddings(document_id: int):
    client = get_qdrant()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))])
    )
