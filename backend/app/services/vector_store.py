from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service for managing vector storage with tenant isolation using ChromaDB."""

    def __init__(self, chroma_host: str = "chromadb", chroma_port: int = 8000):
        import chromadb

        self.chroma_host = chroma_host
        self.chroma_port = chroma_port

        # Use simple HTTP client without tenant specification
        # Tenant isolation is achieved through collection naming
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port
        )
        logger.info(f"Initialized ChromaDB client at {chroma_host}:{chroma_port}")

    def get_collection(self, tenant_id: str, project_id: str):
        """Get or create collection for project with tenant isolation.

        Args:
            tenant_id: Tenant UUID
            project_id: Project UUID

        Returns:
            ChromaDB collection
        """
        try:
            # Use shortened UUIDs for collection name (max 63 chars)
            # Format: t_{first8}_p_{first8} = 21 chars total
            tenant_short = str(tenant_id).replace('-', '')[:8]
            project_short = str(project_id).replace('-', '')[:8]
            collection_name = f"t_{tenant_short}_p_{project_short}"

            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(f"Retrieved collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to get collection: {e}")
            raise

    def add_documents(
        self,
        tenant_id: str,
        project_id: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> None:
        """Add document chunks to vector store.

        Args:
            tenant_id: Tenant UUID
            project_id: Project UUID
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
        """
        try:
            collection = self.get_collection(tenant_id, project_id)

            ids = [chunk["vector_id"] for chunk in chunks]
            documents = [chunk["text"] for chunk in chunks]
            metadatas = [
                {
                    "document_id": str(chunk["document_id"]),
                    "chunk_id": str(chunk["chunk_id"]),
                    "page_number": chunk.get("page_number", 0),
                    "chunk_index": chunk["chunk_index"]
                }
                for chunk in chunks
            ]

            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"Added {len(chunks)} chunks to collection for tenant {tenant_id}, project {project_id}")
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise

    def query(
        self,
        tenant_id: str,
        project_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        """Query vector store for similar chunks.

        Args:
            tenant_id: Tenant UUID
            project_id: Project UUID
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of similar chunks with metadata
        """
        try:
            collection = self.get_collection(tenant_id, project_id)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

            # Transform results into standardized format
            chunks = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    chunks.append({
                        "vector_id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score": 1.0 - results['distances'][0][i] if results['distances'] else 0.9,
                        "chunk_id": results['metadatas'][0][i].get('chunk_id')
                    })

            logger.info(f"Retrieved {len(chunks)} similar chunks for tenant {tenant_id}, project {project_id}")
            return chunks
        except Exception as e:
            logger.error(f"Failed to query vector store: {e}")
            raise

    def delete_collection(self, tenant_id: str, project_id: str) -> None:
        """Delete collection for a project.

        Args:
            tenant_id: Tenant UUID
            project_id: Project UUID
        """
        try:
            # Use same shortened naming as get_collection
            tenant_short = str(tenant_id).replace('-', '')[:8]
            project_short = str(project_id).replace('-', '')[:8]
            collection_name = f"t_{tenant_short}_p_{project_short}"

            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
