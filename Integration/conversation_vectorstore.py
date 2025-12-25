"""
Conversation Vector Store Module
Saves conversations to FAISS vector database for semantic search and retrieval
"""

import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
import os
import pickle

class ConversationVectorStore:
    """Store and retrieve conversations using FAISS vector database"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "conversation_index"):
        """
        Initialize vector store with embedding model
        
        Args:
            model_name: Sentence transformer model for embeddings
            index_path: Path to save FAISS index (without extension)
        """
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.metadata = []  # Store conversation metadata
        self.conversation_store = {}  # Store full conversation objects by vector_id
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.index_path) if os.path.dirname(self.index_path) else '.', exist_ok=True)
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        index_file = f"{self.index_path}.faiss"
        metadata_file = f"{self.index_path}_metadata.json"
        store_file = f"{self.index_path}_store.pkl"
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                self.index = faiss.read_index(index_file)
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                
                # Load conversation store if it exists
                if os.path.exists(store_file):
                    with open(store_file, 'rb') as f:
                        self.conversation_store = pickle.load(f)
            except Exception as e:
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.metadata = []
                self.conversation_store = {}
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
    
    def add_conversation(self, conversation: Dict, chatbot_type: str = "learning", user_id: str = "unknown"):
        """
        Add a complete conversation to vector store
        
        Args:
            conversation: Dict with 'messages' list, optionally 'timestamp'
            chatbot_type: 'learning' or 'emotional'
            user_id: User identifier
        """
        if not conversation.get('messages'):
            return
        
        timestamp = conversation.get('timestamp', datetime.now().isoformat())
        conversation_id = f"{user_id}_{timestamp}_{len(self.metadata)}"
        
        for i, message in enumerate(conversation['messages']):
            if message.get('content'):
                try:
                    # Create embedding for each message
                    embedding = self.model.encode(message['content'], convert_to_numpy=True)
                    
                    # Add to FAISS index
                    self.index.add(np.array([embedding]))
                    vector_id = self.index.ntotal - 1
                    
                    # Store metadata
                    metadata_entry = {
                        'user_id': user_id,
                        'chatbot_type': chatbot_type,
                        'conversation_id': conversation_id,
                        'message_index': i,
                        'role': message.get('role', 'user'),
                        'content_preview': message['content'][:200],
                        'timestamp': timestamp,
                        'vector_id': vector_id
                    }
                    self.metadata.append(metadata_entry)
                    
                    # Store full message
                    self.conversation_store[vector_id] = {
                        'content': message['content'],
                        'metadata': metadata_entry
                    }
                except Exception as e:
                    continue
    
    def search_similar(self, query: str, k: int = 5, chatbot_type: Optional[str] = None) -> List[Dict]:
        """
        Search for similar conversations
        
        Args:
            query: Search query text
            k: Number of results
            chatbot_type: Filter by 'learning' or 'emotional' (optional)
        
        Returns:
            List of dicts with similarity score, metadata, and content
        """
        if self.index.ntotal == 0:
            return []
        
        try:
            # Encode query
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # Search
            distances, indices = self.index.search(np.array([query_embedding]), min(k, self.index.ntotal))
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    
                    # Filter by chatbot type if specified
                    if chatbot_type and meta['chatbot_type'] != chatbot_type:
                        continue
                    
                    # Get full content
                    full_content = self.conversation_store.get(idx, {}).get('content', meta['content_preview'])
                    
                    results.append({
                        'similarity_score': float(distance),
                        'user_id': meta['user_id'],
                        'chatbot_type': meta['chatbot_type'],
                        'role': meta['role'],
                        'content': full_content,
                        'content_preview': meta['content_preview'],
                        'timestamp': meta['timestamp'],
                        'conversation_id': meta['conversation_id']
                    })
            
            return results
        except Exception as e:
            return []
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, f"{self.index_path}.faiss")
            with open(f"{self.index_path}_metadata.json", 'w') as f:
                json.dump(self.metadata, f)
            with open(f"{self.index_path}_store.pkl", 'wb') as f:
                pickle.dump(self.conversation_store, f)
        except Exception as e:
            pass
    
    def get_user_conversations(self, user_id: str) -> Dict:
        """Get conversation summary for a user"""
        user_messages = [m for m in self.metadata if m['user_id'] == user_id]
        
        return {
            'user_id': user_id,
            'total_messages': len(user_messages),
            'chatbot_interactions': {
                'learning': len([m for m in user_messages if m['chatbot_type'] == 'learning']),
                'emotional': len([m for m in user_messages if m['chatbot_type'] == 'emotional'])
            },
            'conversations': len(set(m['conversation_id'] for m in user_messages))
        }
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        if not self.metadata:
            return {
                'total_vectors': 0,
                'total_users': 0,
                'learning_messages': 0,
                'emotional_messages': 0
            }
        
        learning_msgs = len([m for m in self.metadata if m['chatbot_type'] == 'learning'])
        emotional_msgs = len([m for m in self.metadata if m['chatbot_type'] == 'emotional'])
        
        return {
            'total_vectors': self.index.ntotal,
            'total_users': len(set(m['user_id'] for m in self.metadata)),
            'learning_messages': learning_msgs,
            'emotional_messages': emotional_msgs,
            'total_messages': self.index.ntotal
        }


# Global instance for easy access
_vectorstore_instance = None

def get_vectorstore(index_path: str = "conversation_index") -> ConversationVectorStore:
    """Get or create global vectorstore instance"""
    global _vectorstore_instance
    if _vectorstore_instance is None:
        _vectorstore_instance = ConversationVectorStore(index_path=index_path)
    return _vectorstore_instance

def log_conversation_to_store(conversation: Dict, chatbot_type: str, user_id: str = "unknown"):
    """
    Helper function to log conversation to global vectorstore
    
    Args:
        conversation: Dict with 'messages' list
        chatbot_type: 'learning' or 'emotional'
        user_id: User identifier
    """
    try:
        vectorstore = get_vectorstore()
        vectorstore.add_conversation(conversation, chatbot_type=chatbot_type, user_id=user_id)
        vectorstore.save_index()
    except Exception as e:
        pass
