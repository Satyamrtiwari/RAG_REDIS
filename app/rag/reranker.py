from typing import List
from langchain_core.documents import Document
from flashrank import Ranker, RerankRequest
from app.utils.logger import logger

# Initialize lightweight local FlashRank Cross-Encoder model
# Runs locally in ~15ms with zero GPU requirement
_ranker_instance = None


def get_ranker() -> Ranker:
    global _ranker_instance
    if _ranker_instance is None:
        logger.info("⚡ Initializing FlashRank Cross-Encoder Reranker...")
        _ranker_instance = Ranker(model_name="ms-marco-TinyBERT-L-2-v2")
    return _ranker_instance


def rerank_documents(query: str, documents: List[Document], top_n: int = 5) -> List[Document]:
    """
    Reranks candidate documents using Cross-Encoder attention scoring.
    Filters out noisy or misaligned chunks and returns top_n purest documents.
    """
    if not documents:
        return []

    if len(documents) <= top_n:
        return documents

    try:
        ranker = get_ranker()
        passages = [
            {
                "id": idx,
                "text": doc.page_content,
                "meta": doc.metadata
            }
            for idx, doc in enumerate(documents)
        ]

        rerank_req = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(rerank_req)

        reranked_docs = []
        for res in results[:top_n]:
            doc_idx = res["id"]
            reranked_docs.append(documents[doc_idx])

        logger.info(f"🎯 FlashRank Reranker: Selected top {len(reranked_docs)} chunks from {len(documents)} candidates.")
        return reranked_docs

    except Exception as e:
        logger.warning(f"⚠️ Reranker Fallback: {e}")
        return documents[:top_n]
