try:
    import chromadb
    CHROMADB_AVAILABLE = True
except Exception:
    chromadb = None
    CHROMADB_AVAILABLE = False

from typing import List, Dict, Optional
import uuid
from datetime import datetime


if CHROMADB_AVAILABLE:
    class ChromaManagerAlternative:
        def __init__(self, persist_directory: str = "./chroma_db"):
            self.persist_directory = persist_directory
            self.client = chromadb.PersistentClient(path=persist_directory)
            try:
                self.conversation_collection = self.client.get_or_create_collection(
                    name="conversations",
                    metadata={"hnsw:space": "cosine"}
                )
                self.context_collection = self.client.get_or_create_collection(
                    name="context_memory",
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"Warning: ChromaDB initialization error: {e}")
                self.conversation_collection = self.client.get_or_create_collection(name="conversations")
                self.context_collection = self.client.get_or_create_collection(name="context_memory")

        def add_conversation_turn(self, user_id: str, conversation_id: str,
                                user_message: str, bot_response: str,
                                metadata: Dict = None) -> bool:
            try:
                combined_text = f"User: {user_message}\nAssistant: {bot_response}"
                msg_metadata = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "timestamp": str(datetime.now()),
                    "type": "conversation_turn",
                    "user_message_length": len(user_message),
                    "bot_response_length": len(bot_response)
                }
                if metadata:
                    msg_metadata.update(metadata)
                self.conversation_collection.add(
                    documents=[combined_text],
                    metadatas=[msg_metadata],
                    ids=[f"{conversation_id}_turn_{uuid.uuid4().hex[:8]}"]
                )
                return True
            except Exception as e:
                print(f"Error adding conversation turn: {e}")
                return False

        def get_relevant_context(self, user_id: str, query: str,
                                conversation_id: str = None,
                                n_results: int = 5) -> List[Dict]:
            try:
                where_clause = {"user_id": user_id}
                if conversation_id:
                    where_clause["conversation_id"] = conversation_id
                results = self.conversation_collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause,
                    include=["documents", "metadatas", "distances"]
                )
                contexts = []
                if results.get("documents") and results["documents"]:
                    for i, (doc, metadata, distance) in enumerate(zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0]
                    )):
                        contexts.append({
                            "content": doc,
                            "metadata": metadata,
                            "relevance_score": 1 - distance,
                            "rank": i + 1
                        })
                return contexts
            except Exception as e:
                print(f"Error getting relevant context: {e}")
                return []

        def get_conversation_summary(self, user_id: str, conversation_id: str) -> Dict:
            try:
                where_clause = {"user_id": user_id, "conversation_id": conversation_id}
                results = self.conversation_collection.get(where=where_clause, include=["metadatas"])
                if not results.get("metadatas"):
                    return {"total_turns": 0, "start_time": None, "end_time": None, "topics": []}
                timestamps = [meta.get("timestamp") for meta in results["metadatas"]]
                timestamps.sort()
                return {
                    "total_turns": len(results["metadatas"]),
                    "start_time": timestamps[0] if timestamps else None,
                    "end_time": timestamps[-1] if timestamps else None,
                    "topics": self._extract_topics(results["metadatas"])
                }
            except Exception as e:
                print(f"Error getting conversation summary: {e}")
                return {"total_turns": 0, "start_time": None, "end_time": None, "topics": []}

        def _extract_topics(self, metadatas: List[Dict]) -> List[str]:
            topics = []
            for meta in metadatas:
                content = meta.get("content", "")
                if any(word in content.lower() for word in ["admission", "exam", "course", "fee"]):
                    topics.append("Academic Queries")
                if any(word in content.lower() for word in ["hostel", "campus", "facilities"]):
                    topics.append("Campus Life")
                if any(word in content.lower() for word in ["placement", "job", "career"]):
                    topics.append("Career & Placements")
            return list(set(topics))

        def add_context_memory(self, user_id: str, key: str, value: str, metadata: Dict = None) -> bool:
            try:
                context_id = f"{user_id}_context_{key}_{uuid.uuid4().hex[:8]}"
                context_metadata = {"user_id": user_id, "key": key, "timestamp": str(datetime.now()), "type": "context_memory"}
                if metadata:
                    context_metadata.update(metadata)
                self.context_collection.add(documents=[value], metadatas=[context_metadata], ids=[context_id])
                return True
            except Exception as e:
                print(f"Error adding context memory: {e}")
                return False

        def get_context_memory(self, user_id: str, key: str = None) -> List[Dict]:
            try:
                where_clause = {"user_id": user_id, "type": "context_memory"}
                if key:
                    where_clause["key"] = key
                results = self.context_collection.get(where=where_clause, include=["documents", "metadatas"])
                memories = []
                if results.get("documents"):
                    for doc, metadata in zip(results["documents"], results["metadatas"]):
                        memories.append({"content": doc, "key": metadata.get("key"), "timestamp": metadata.get("timestamp")})
                return memories
            except Exception as e:
                print(f"Error getting context memory: {e}")
                return []

        def delete_user_data(self, user_id: str) -> bool:
            try:
                where_clause = {"user_id": user_id}
                conv_results = self.conversation_collection.get(where=where_clause, include=[])
                context_results = self.context_collection.get(where=where_clause, include=[])
                if conv_results.get("ids"):
                    self.conversation_collection.delete(ids=conv_results["ids"])
                if context_results.get("ids"):
                    self.context_collection.delete(ids=context_results["ids"])
                return True
            except Exception as e:
                print(f"Error deleting user data: {e}")
                return False

    chroma_manager = ChromaManagerAlternative()
else:
    # Dummy fallback implementation when chromadb is not available.
    class ChromaManagerAlternative:
        def __init__(self, persist_directory: str = "./chroma_db"):
            self.enabled = False
            print("Warning: chromadb is not installed. Chroma features are disabled.")

        def add_conversation_turn(self, *args, **kwargs) -> bool:
            # No-op: return False to indicate data wasn't stored.
            return False

        def get_relevant_context(self, *args, **kwargs) -> List[Dict]:
            return []

        def get_conversation_summary(self, *args, **kwargs) -> Dict:
            return {"total_turns": 0, "start_time": None, "end_time": None, "topics": []}

        def add_context_memory(self, *args, **kwargs) -> bool:
            return False

        def get_context_memory(self, *args, **kwargs) -> List[Dict]:
            return []

        def delete_user_data(self, *args, **kwargs) -> bool:
            return False

    chroma_manager = ChromaManagerAlternative()
