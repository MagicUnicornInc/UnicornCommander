import logging
import os
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import time

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StructuredStorage")

# Try to import PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import Json, DictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("PostgreSQL support not available. Install with: pip install psycopg2-binary")

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis support not available. Install with: pip install redis")

class StructuredStorage:
    """Handles structured data storage using PostgreSQL and Redis"""
    
    def __init__(self, 
                postgres_dsn: Optional[str] = None,
                redis_url: Optional[str] = None,
                use_postgres: bool = True,
                use_redis: bool = True,
                fallback_to_json: bool = True):
        """Initialize structured storage
        
        Args:
            postgres_dsn: PostgreSQL connection string
            redis_url: Redis connection URL
            use_postgres: Whether to use PostgreSQL
            use_redis: Whether to use Redis
            fallback_to_json: Whether to fall back to JSON files if databases unavailable
        """
        self.use_postgres = use_postgres and POSTGRES_AVAILABLE
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.fallback_to_json = fallback_to_json
        
        # Initialize PostgreSQL
        self.pg_conn = None
        if self.use_postgres:
            try:
                if not postgres_dsn:
                    postgres_dsn = os.environ.get("POSTGRES_DSN", 
                        "postgresql://postgres:postgres@localhost:5432/kde_ai_memory")
                self.pg_conn = psycopg2.connect(postgres_dsn)
                self._init_postgres_tables()
                logger.info("Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                self.use_postgres = False
        
        # Initialize Redis
        self.redis_client = None
        if self.use_redis:
            try:
                if not redis_url:
                    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis server")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.use_redis = False
        
        # Initialize JSON storage path if fallback is enabled
        if self.fallback_to_json:
            import pathlib
            self.json_storage_path = pathlib.Path.home() / ".local" / "share" / "kde-ai-interface" / "structured_data"
            self.json_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"JSON storage path: {self.json_storage_path}")
    
    def _init_postgres_tables(self):
        """Initialize PostgreSQL tables if they don't exist"""
        if not self.pg_conn:
            return
            
        try:
            with self.pg_conn.cursor() as cur:
                # Create conversations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id VARCHAR(36) PRIMARY KEY,
                        title VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB
                    )
                """)
                
                # Create messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        conversation_id VARCHAR(36) REFERENCES conversations(id),
                        role VARCHAR(50),
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB
                    )
                """)
                
                # Create memory_items table for long-term memory
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memory_items (
                        id VARCHAR(36) PRIMARY KEY,
                        type VARCHAR(50),
                        content TEXT,
                        source VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP,
                        importance INTEGER,
                        metadata JSONB
                    )
                """)
                
                # Create metadata table for agents and models
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_models (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(255),
                        type VARCHAR(50),
                        system_prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        configuration JSONB,
                        is_enabled BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Create settings table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key VARCHAR(255) PRIMARY KEY,
                        value JSONB,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.pg_conn.commit()
                logger.info("PostgreSQL tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL tables: {e}")
            self.pg_conn.rollback()
    
    def close(self):
        """Close database connections"""
        if self.pg_conn:
            self.pg_conn.close()
            self.pg_conn = None
        
        if self.redis_client:
            self.redis_client = None
    
    # --- Conversation Management --- #
    
    def create_conversation(self, 
                           id: str, 
                           title: Optional[str] = None, 
                           metadata: Optional[Dict] = None) -> bool:
        """Create a new conversation
        
        Args:
            id: Unique ID for the conversation
            title: Optional title for the conversation
            metadata: Optional metadata for the conversation
            
        Returns:
            bool: True if successful
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO conversations (id, title, metadata, created_at, updated_at)
                        VALUES (%s, %s, %s, NOW(), NOW())
                    """, (id, title, Json(metadata or {})))
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to create conversation in PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                conv_data = {
                    "id": id,
                    "title": title,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                with open(self.json_storage_path / f"conversation_{id}.json", 'w') as f:
                    json.dump(conv_data, f)
                return True
            except Exception as e:
                logger.error(f"Failed to create conversation as JSON: {e}")
        
        return False
    
    def add_message(self, 
                   conversation_id: str, 
                   role: str, 
                   content: str, 
                   metadata: Optional[Dict] = None) -> bool:
        """Add a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
            metadata: Optional metadata for the message
            
        Returns:
            bool: True if successful
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    # Add message
                    cur.execute("""
                        INSERT INTO messages (conversation_id, role, content, metadata, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (conversation_id, role, content, Json(metadata or {})))
                    
                    # Update conversation's updated_at timestamp
                    cur.execute("""
                        UPDATE conversations
                        SET updated_at = NOW()
                        WHERE id = %s
                    """, (conversation_id,))
                    
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to add message in PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                # Load existing conversation if it exists
                conv_file = self.json_storage_path / f"conversation_{conversation_id}.json"
                if conv_file.exists():
                    with open(conv_file, 'r') as f:
                        conv_data = json.load(f)
                else:
                    # Create new conversation data
                    conv_data = {
                        "id": conversation_id,
                        "title": None,
                        "metadata": {},
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "messages": []
                    }
                
                # Add message
                if "messages" not in conv_data:
                    conv_data["messages"] = []
                
                conv_data["messages"].append({
                    "role": role,
                    "content": content,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat()
                })
                
                # Update timestamp
                conv_data["updated_at"] = datetime.now().isoformat()
                
                # Save conversation
                with open(conv_file, 'w') as f:
                    json.dump(conv_data, f)
                return True
            except Exception as e:
                logger.error(f"Failed to add message as JSON: {e}")
        
        return False
    
    def get_conversation(self, conversation_id: str) -> Dict:
        """Get a conversation with all its messages
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dict containing conversation data and messages
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    # Get conversation data
                    cur.execute("""
                        SELECT id, title, created_at, updated_at, metadata
                        FROM conversations
                        WHERE id = %s
                    """, (conversation_id,))
                    conv_data = cur.fetchone()
                    
                    if not conv_data:
                        return {}
                    
                    # Convert to dictionary
                    conversation = dict(conv_data)
                    
                    # Convert datetime objects to strings
                    conversation["created_at"] = conversation["created_at"].isoformat()
                    conversation["updated_at"] = conversation["updated_at"].isoformat()
                    
                    # Get messages
                    cur.execute("""
                        SELECT id, role, content, created_at, metadata
                        FROM messages
                        WHERE conversation_id = %s
                        ORDER BY created_at ASC
                    """, (conversation_id,))
                    messages = []
                    for row in cur.fetchall():
                        message = dict(row)
                        message["created_at"] = message["created_at"].isoformat()
                        messages.append(message)
                    
                    conversation["messages"] = messages
                    return conversation
            except Exception as e:
                logger.error(f"Failed to get conversation from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                conv_file = self.json_storage_path / f"conversation_{conversation_id}.json"
                if conv_file.exists():
                    with open(conv_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Failed to get conversation from JSON: {e}")
        
        return {}
    
    def list_conversations(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """List conversations
        
        Args:
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            
        Returns:
            List of conversation dictionaries
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT id, title, created_at, updated_at, metadata
                        FROM conversations
                        ORDER BY updated_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    conversations = []
                    for row in cur.fetchall():
                        conv = dict(row)
                        conv["created_at"] = conv["created_at"].isoformat()
                        conv["updated_at"] = conv["updated_at"].isoformat()
                        conversations.append(conv)
                    
                    return conversations
            except Exception as e:
                logger.error(f"Failed to list conversations from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                # Get all conversation files
                conv_files = list(self.json_storage_path.glob("conversation_*.json"))
                
                # Sort by modification time (most recent first)
                conv_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                
                # Apply pagination
                conv_files = conv_files[offset:offset+limit]
                
                # Load conversation data
                conversations = []
                for file in conv_files:
                    try:
                        with open(file, 'r') as f:
                            conv_data = json.load(f)
                            # Include only summary data, not messages
                            conv_summary = {
                                "id": conv_data.get("id"),
                                "title": conv_data.get("title"),
                                "created_at": conv_data.get("created_at"),
                                "updated_at": conv_data.get("updated_at"),
                                "metadata": conv_data.get("metadata", {})
                            }
                            conversations.append(conv_summary)
                    except Exception as e:
                        logger.error(f"Failed to load conversation from {file}: {e}")
                
                return conversations
            except Exception as e:
                logger.error(f"Failed to list conversations from JSON: {e}")
        
        return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            bool: True if successful
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    # First delete messages (due to foreign key)
                    cur.execute("""
                        DELETE FROM messages
                        WHERE conversation_id = %s
                    """, (conversation_id,))
                    
                    # Then delete the conversation
                    cur.execute("""
                        DELETE FROM conversations
                        WHERE id = %s
                    """, (conversation_id,))
                    
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to delete conversation in PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                conv_file = self.json_storage_path / f"conversation_{conversation_id}.json"
                if conv_file.exists():
                    os.remove(conv_file)
                return True
            except Exception as e:
                logger.error(f"Failed to delete conversation JSON file: {e}")
        
        return False
    
    # --- Memory Management --- #
    
    def add_memory_item(self, 
                       id: str, 
                       type: str, 
                       content: str, 
                       source: str = "user",
                       importance: int = 1,
                       metadata: Optional[Dict] = None) -> bool:
        """Add a memory item
        
        Args:
            id: Unique ID for the memory item
            type: Type of memory (fact, concept, rule, etc.)
            content: Content of the memory
            source: Source of the memory
            importance: Importance level (1-5)
            metadata: Optional metadata
            
        Returns:
            bool: True if successful
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO memory_items 
                        (id, type, content, source, created_at, last_accessed, importance, metadata)
                        VALUES (%s, %s, %s, %s, NOW(), NOW(), %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            updated_at = NOW(),
                            importance = EXCLUDED.importance,
                            metadata = EXCLUDED.metadata
                    """, (id, type, content, source, importance, Json(metadata or {})))
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to add memory item in PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Try Redis for important items (faster access)
        if self.use_redis and importance >= 4:
            try:
                self.redis_client.hset(
                    f"memory:{id}",
                    mapping={
                        "type": type,
                        "content": content,
                        "source": source,
                        "created_at": datetime.now().isoformat(),
                        "last_accessed": datetime.now().isoformat(),
                        "importance": importance,
                        "metadata": json.dumps(metadata or {})
                    }
                )
                
                # Expire after 7 days (for Redis memory management)
                self.redis_client.expire(f"memory:{id}", 60*60*24*7)
            except Exception as e:
                logger.error(f"Failed to add memory item to Redis: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                memory_file = self.json_storage_path / f"memory_{id}.json"
                memory_data = {
                    "id": id,
                    "type": type,
                    "content": content,
                    "source": source,
                    "created_at": datetime.now().isoformat(),
                    "last_accessed": datetime.now().isoformat(),
                    "importance": importance,
                    "metadata": metadata or {}
                }
                with open(memory_file, 'w') as f:
                    json.dump(memory_data, f)
                return True
            except Exception as e:
                logger.error(f"Failed to add memory item as JSON: {e}")
        
        return False
    
    def get_memory_item(self, id: str) -> Dict:
        """Get a memory item
        
        Args:
            id: ID of the memory item
            
        Returns:
            Dict containing memory item data
        """
        # Try Redis first (faster)
        if self.use_redis:
            try:
                memory_data = self.redis_client.hgetall(f"memory:{id}")
                if memory_data:
                    # Update last accessed time
                    self.redis_client.hset(
                        f"memory:{id}",
                        "last_accessed",
                        datetime.now().isoformat()
                    )
                    
                    # Convert metadata from JSON
                    if "metadata" in memory_data:
                        memory_data["metadata"] = json.loads(memory_data["metadata"])
                    
                    return memory_data
            except Exception as e:
                logger.error(f"Failed to get memory item from Redis: {e}")
        
        # Try PostgreSQL
        if self.use_postgres:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    # Get memory item
                    cur.execute("""
                        SELECT id, type, content, source, created_at, last_accessed, importance, metadata
                        FROM memory_items
                        WHERE id = %s
                    """, (id,))
                    item_data = cur.fetchone()
                    
                    if not item_data:
                        return {}
                    
                    # Update last accessed time
                    cur.execute("""
                        UPDATE memory_items
                        SET last_accessed = NOW()
                        WHERE id = %s
                    """, (id,))
                    
                    self.pg_conn.commit()
                    
                    # Convert to dictionary
                    item = dict(item_data)
                    item["created_at"] = item["created_at"].isoformat()
                    item["last_accessed"] = item["last_accessed"].isoformat()
                    
                    return item
            except Exception as e:
                logger.error(f"Failed to get memory item from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                memory_file = self.json_storage_path / f"memory_{id}.json"
                if memory_file.exists():
                    with open(memory_file, 'r') as f:
                        memory_data = json.load(f)
                        
                    # Update last accessed time
                    memory_data["last_accessed"] = datetime.now().isoformat()
                    with open(memory_file, 'w') as f:
                        json.dump(memory_data, f)
                        
                    return memory_data
            except Exception as e:
                logger.error(f"Failed to get memory item from JSON: {e}")
        
        return {}
    
    def delete_memory_item(self, id: str) -> bool:
        """Delete a memory item
        
        Args:
            id: ID of the memory item
            
        Returns:
            bool: True if successful
        """
        success = False
        
        # Try PostgreSQL
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM memory_items
                        WHERE id = %s
                    """, (id,))
                    self.pg_conn.commit()
                success = True
            except Exception as e:
                logger.error(f"Failed to delete memory item from PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Try Redis
        if self.use_redis:
            try:
                self.redis_client.delete(f"memory:{id}")
                success = True
            except Exception as e:
                logger.error(f"Failed to delete memory item from Redis: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                memory_file = self.json_storage_path / f"memory_{id}.json"
                if memory_file.exists():
                    os.remove(memory_file)
                success = True
            except Exception as e:
                logger.error(f"Failed to delete memory item JSON file: {e}")
        
        return success
    
    # --- Agent/Model Management --- #
    
    def save_agent_model(self,
                        id: str,
                        name: str,
                        type: str,
                        system_prompt: str,
                        configuration: Dict,
                        is_enabled: bool = True) -> bool:
        """Save an agent or model configuration
        
        Args:
            id: Unique ID for the agent/model
            name: Name of the agent/model
            type: Type (openai, ollama, agent, etc.)
            system_prompt: System prompt to use
            configuration: Configuration dictionary
            is_enabled: Whether the agent/model is enabled
            
        Returns:
            bool: True if successful
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO agent_models 
                        (id, name, type, system_prompt, created_at, updated_at, configuration, is_enabled)
                        VALUES (%s, %s, %s, %s, NOW(), NOW(), %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            type = EXCLUDED.type,
                            system_prompt = EXCLUDED.system_prompt,
                            updated_at = NOW(),
                            configuration = EXCLUDED.configuration,
                            is_enabled = EXCLUDED.is_enabled
                    """, (id, name, type, system_prompt, Json(configuration), is_enabled))
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to save agent/model in PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                agent_file = self.json_storage_path / f"agent_model_{id}.json"
                agent_data = {
                    "id": id,
                    "name": name,
                    "type": type,
                    "system_prompt": system_prompt,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "configuration": configuration,
                    "is_enabled": is_enabled
                }
                with open(agent_file, 'w') as f:
                    json.dump(agent_data, f)
                return True
            except Exception as e:
                logger.error(f"Failed to save agent/model as JSON: {e}")
        
        return False
    
    def get_agent_model(self, id: str) -> Dict:
        """Get an agent or model configuration
        
        Args:
            id: ID of the agent/model
            
        Returns:
            Dict containing agent/model data
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT id, name, type, system_prompt, created_at, updated_at, configuration, is_enabled
                        FROM agent_models
                        WHERE id = %s
                    """, (id,))
                    agent_data = cur.fetchone()
                    
                    if not agent_data:
                        return {}
                    
                    # Convert to dictionary
                    agent = dict(agent_data)
                    agent["created_at"] = agent["created_at"].isoformat()
                    agent["updated_at"] = agent["updated_at"].isoformat()
                    
                    return agent
            except Exception as e:
                logger.error(f"Failed to get agent/model from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                agent_file = self.json_storage_path / f"agent_model_{id}.json"
                if agent_file.exists():
                    with open(agent_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Failed to get agent/model from JSON: {e}")
        
        return {}
    
    def list_agent_models(self, type: Optional[str] = None) -> List[Dict]:
        """List agent/model configurations
        
        Args:
            type: Optional type filter
            
        Returns:
            List of agent/model dictionaries
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    if type:
                        cur.execute("""
                            SELECT id, name, type, system_prompt, created_at, updated_at, configuration, is_enabled
                            FROM agent_models
                            WHERE type = %s
                            ORDER BY name ASC
                        """, (type,))
                    else:
                        cur.execute("""
                            SELECT id, name, type, system_prompt, created_at, updated_at, configuration, is_enabled
                            FROM agent_models
                            ORDER BY name ASC
                        """)
                    
                    agents = []
                    for row in cur.fetchall():
                        agent = dict(row)
                        agent["created_at"] = agent["created_at"].isoformat()
                        agent["updated_at"] = agent["updated_at"].isoformat()
                        agents.append(agent)
                    
                    return agents
            except Exception as e:
                logger.error(f"Failed to list agents/models from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                # Get all agent files
                agent_files = list(self.json_storage_path.glob("agent_model_*.json"))
                
                # Load agent data
                agents = []
                for file in agent_files:
                    try:
                        with open(file, 'r') as f:
                            agent_data = json.load(f)
                            # Filter by type if specified
                            if not type or agent_data.get("type") == type:
                                agents.append(agent_data)
                    except Exception as e:
                        logger.error(f"Failed to load agent/model from {file}: {e}")
                
                # Sort by name
                agents.sort(key=lambda a: a.get("name", ""))
                
                return agents
            except Exception as e:
                logger.error(f"Failed to list agents/models from JSON: {e}")
        
        return []
    
    def delete_agent_model(self, id: str) -> bool:
        """Delete an agent or model configuration
        
        Args:
            id: ID of the agent/model
            
        Returns:
            bool: True if successful
        """
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM agent_models
                        WHERE id = %s
                    """, (id,))
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to delete agent/model from PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                agent_file = self.json_storage_path / f"agent_model_{id}.json"
                if agent_file.exists():
                    os.remove(agent_file)
                return True
            except Exception as e:
                logger.error(f"Failed to delete agent/model JSON file: {e}")
        
        return False
    
    # --- Settings Management --- #
    
    def save_setting(self, key: str, value: Any) -> bool:
        """Save a setting
        
        Args:
            key: Setting key
            value: Setting value (will be JSON serialized)
            
        Returns:
            bool: True if successful
        """
        # Try Redis first (faster access for settings)
        if self.use_redis:
            try:
                self.redis_client.set(f"setting:{key}", json.dumps(value))
                # Add to settings set for listing
                self.redis_client.sadd("settings", key)
                return True
            except Exception as e:
                logger.error(f"Failed to save setting to Redis: {e}")
        
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO settings (key, value, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (key) DO UPDATE SET
                            value = EXCLUDED.value,
                            updated_at = NOW()
                    """, (key, Json(value)))
                    self.pg_conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to save setting in PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                settings_file = self.json_storage_path / "settings.json"
                
                # Load existing settings
                settings = {}
                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                
                # Update setting
                settings[key] = {
                    "value": value,
                    "updated_at": datetime.now().isoformat()
                }
                
                # Save settings
                with open(settings_file, 'w') as f:
                    json.dump(settings, f)
                
                return True
            except Exception as e:
                logger.error(f"Failed to save setting as JSON: {e}")
        
        return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value
        """
        # Try Redis first (faster)
        if self.use_redis:
            try:
                value = self.redis_client.get(f"setting:{key}")
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Failed to get setting from Redis: {e}")
        
        if self.use_postgres:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT value
                        FROM settings
                        WHERE key = %s
                    """, (key,))
                    row = cur.fetchone()
                    
                    if row:
                        return row["value"]
            except Exception as e:
                logger.error(f"Failed to get setting from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                settings_file = self.json_storage_path / "settings.json"
                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                        
                    if key in settings:
                        return settings[key]["value"]
            except Exception as e:
                logger.error(f"Failed to get setting from JSON: {e}")
        
        return default
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings
        
        Returns:
            Dict of all settings
        """
        settings = {}
        
        # Try Redis first if available
        if self.use_redis:
            try:
                # Get all setting keys
                keys = self.redis_client.smembers("settings")
                for key in keys:
                    value = self.redis_client.get(f"setting:{key}")
                    if value:
                        settings[key] = json.loads(value)
            except Exception as e:
                logger.error(f"Failed to get all settings from Redis: {e}")
        
        # Try PostgreSQL if Redis failed or not available
        if self.use_postgres and not settings:
            try:
                with self.pg_conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT key, value
                        FROM settings
                    """)
                    
                    for row in cur.fetchall():
                        settings[row["key"]] = row["value"]
            except Exception as e:
                logger.error(f"Failed to get all settings from PostgreSQL: {e}")
        
        # Fallback to JSON
        if self.fallback_to_json and not settings:
            try:
                settings_file = self.json_storage_path / "settings.json"
                if settings_file.exists():
                    with open(settings_file, 'r') as f:
                        raw_settings = json.load(f)
                        
                    # Extract values
                    for key, data in raw_settings.items():
                        settings[key] = data["value"]
            except Exception as e:
                logger.error(f"Failed to get all settings from JSON: {e}")
        
        return settings
    
    def delete_setting(self, key: str) -> bool:
        """Delete a setting
        
        Args:
            key: Setting key
            
        Returns:
            bool: True if successful
        """
        success = False
        
        # Try Redis
        if self.use_redis:
            try:
                self.redis_client.delete(f"setting:{key}")
                self.redis_client.srem("settings", key)
                success = True
            except Exception as e:
                logger.error(f"Failed to delete setting from Redis: {e}")
        
        # Try PostgreSQL
        if self.use_postgres:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM settings
                        WHERE key = %s
                    """, (key,))
                    self.pg_conn.commit()
                success = True
            except Exception as e:
                logger.error(f"Failed to delete setting from PostgreSQL: {e}")
                self.pg_conn.rollback()
        
        # Fallback to JSON
        if self.fallback_to_json:
            try:
                settings_file = self.json_storage_path / "settings.json"
                if settings_file.exists():
                    # Load existing settings
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                    
                    # Remove setting
                    if key in settings:
                        del settings[key]
                        
                        # Save settings
                        with open(settings_file, 'w') as f:
                            json.dump(settings, f)
                
                success = True
            except Exception as e:
                logger.error(f"Failed to delete setting from JSON: {e}")
        
        return success
    
    # --- Cache Management (Redis only) --- #
    
    def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a cache value
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful
        """
        if not self.use_redis:
            return False
            
        try:
            self.redis_client.set(f"cache:{key}", json.dumps(value), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache in Redis: {e}")
            return False
    
    def get_cache(self, key: str, default: Any = None) -> Any:
        """Get a cached value
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        if not self.use_redis:
            return default
            
        try:
            value = self.redis_client.get(f"cache:{key}")
            if value:
                return json.loads(value)
            return default
        except Exception as e:
            logger.error(f"Failed to get cache from Redis: {e}")
            return default
    
    def delete_cache(self, key: str) -> bool:
        """Delete a cached value
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful
        """
        if not self.use_redis:
            return False
            
        try:
            self.redis_client.delete(f"cache:{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache from Redis: {e}")
            return False