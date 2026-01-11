"""Extended Neo4j schema for EDGAR data (Phase 5)"""

from typing import Dict, Any, List, Optional
from loguru import logger

from src.graph_db.neo4j_client import Neo4jClient


class EdgarNeo4jSchema:
    """
    Extended Neo4j schema for EDGAR filing data
    
    Extends Phase 4 schema with:
    - Section nodes
    - Chunk nodes with vector embeddings
    - Vector indexes for hybrid search
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize EDGAR schema manager
        
        Args:
            neo4j_client: Neo4jClient instance
        """
        self.client = neo4j_client
    
    def initialize_schema(self, embedding_dimension: int = 1536):
        """
        Initialize EDGAR-specific Neo4j schema
        
        Args:
            embedding_dimension: Dimension of embedding vectors (default: 1536 for OpenAI)
        """
        logger.info("Initializing EDGAR Neo4j schema...")
        
        try:
            # Create Section node indexes
            self._create_section_indexes()
            
            # Create Chunk node indexes
            self._create_chunk_indexes()
            
            # Create vector indexes for hybrid search
            self._create_vector_indexes(embedding_dimension)
            
            logger.info("EDGAR Neo4j schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing EDGAR schema: {e}")
            raise
    
    def _create_section_indexes(self):
        """Create indexes for Section nodes"""
        indexes = [
            ("CREATE INDEX section_id IF NOT EXISTS FOR (s:Section) ON (s.section_id)", False),
            ("CREATE CONSTRAINT section_id_unique IF NOT EXISTS FOR (s:Section) REQUIRE s.section_id IS UNIQUE", True),
            ("CREATE INDEX section_type IF NOT EXISTS FOR (s:Section) ON (s.section_type)", False),
        ]
        
        for index_query, is_constraint in indexes:
            try:
                self.client.execute_query(index_query)
                logger.debug(f"Created {'constraint' if is_constraint else 'index'} for Section")
            except Exception as e:
                logger.debug(f"Index/constraint creation (may already exist): {e}")
    
    def _create_chunk_indexes(self):
        """Create indexes for Chunk nodes"""
        indexes = [
            ("CREATE INDEX chunk_id IF NOT EXISTS FOR (ch:Chunk) ON (ch.chunk_id)", False),
            ("CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (ch:Chunk) REQUIRE ch.chunk_id IS UNIQUE", True),
            ("CREATE INDEX chunk_semantic_type IF NOT EXISTS FOR (ch:Chunk) ON (ch.semantic_type)", False),
            ("CREATE INDEX chunk_company_cik IF NOT EXISTS FOR (ch:Chunk) ON (ch.company_cik)", False),
            ("CREATE INDEX chunk_form_type IF NOT EXISTS FOR (ch:Chunk) ON (ch.form_type)", False),
        ]
        
        for index_query, is_constraint in indexes:
            try:
                self.client.execute_query(index_query)
                logger.debug(f"Created {'constraint' if is_constraint else 'index'} for Chunk")
            except Exception as e:
                logger.debug(f"Index/constraint creation (may already exist): {e}")
    
    def _create_vector_indexes(self, dimension: int = 1536):
        """
        Create vector indexes for hybrid search
        
        Args:
            dimension: Embedding vector dimension
        """
        # Note: Neo4j vector index syntax varies by version
        # Using Neo4j 5.x+ syntax with fallback
        
        vector_indexes = [
            {
                "name": "textChunkEmbeddings",
                "where_clause": "ch.chunk_type IN ['paragraph', 'narrative']",
                "description": "General text content"
            },
            {
                "name": "riskChunkEmbeddings",
                "where_clause": "ch.semantic_type = 'risk_discussion'",
                "description": "Risk factor discussions"
            },
            {
                "name": "financialChunkEmbeddings",
                "where_clause": "ch.semantic_type IN ['financial_analysis', 'revenue_analysis', 'margin_analysis']",
                "description": "Financial analysis"
            },
            {
                "name": "strategyChunkEmbeddings",
                "where_clause": "ch.semantic_type IN ['strategy', 'forward_looking', 'guidance']",
                "description": "Strategic/forward-looking content"
            },
        ]
        
        for idx_config in vector_indexes:
            try:
                # Try Neo4j 5.x+ vector index syntax
                query = f"""
                CREATE VECTOR INDEX {idx_config['name']} IF NOT EXISTS
                FOR (ch:Chunk)
                ON ch.embedding
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {dimension},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
                self.client.execute_query(query)
                logger.info(f"Created vector index: {idx_config['name']} ({idx_config['description']})")
            except Exception as e:
                logger.warning(f"Could not create vector index {idx_config['name']}: {e}")
                logger.warning("Vector indexes require Neo4j 5.x+ with vector index plugin")
                # Continue without vector indexes (can still use graph traversal)
    
    def create_filing_with_sections(
        self,
        accession_number: str,
        cik: str,
        form_type: str,
        filing_date: str,
        company_name: Optional[str] = None,
        sections: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Create Filing node with Section nodes
        
        Args:
            accession_number: Filing accession number
            cik: Company CIK
            form_type: Form type
            filing_date: Filing date (ISO format)
            company_name: Company name
            sections: List of section dictionaries
            
        Returns:
            True if successful
        """
        try:
            # Ensure Company exists
            company_query = """
            MERGE (c:Company {cik: $cik})
            SET c.updated_at = datetime()
            """
            self.client.execute_query(company_query, {"cik": cik})
            
            # Create Filing node
            filing_query = """
            MATCH (c:Company {cik: $cik})
            MERGE (f:Filing {accession_number: $accession_number})
            SET f.form_type = $form_type,
                f.filing_date = date($filing_date),
                f.company_name = $company_name,
                f.updated_at = datetime()
            MERGE (c)-[:FILED_BY]->(f)
            """
            self.client.execute_query(filing_query, {
                "accession_number": accession_number,
                "cik": cik,
                "form_type": form_type,
                "filing_date": filing_date,
                "company_name": company_name
            })
            
            # Create Section nodes
            if sections:
                for section in sections:
                    self.create_section(
                        section_id=section["section_id"],
                        accession_number=accession_number,
                        section_item=section.get("section_item"),
                        section_type=section.get("section_type", "periodic_report_section"),
                        order=section.get("order", 0)
                    )
            
            logger.debug(f"Created filing {accession_number} with {len(sections or [])} sections")
            return True
        
        except Exception as e:
            logger.error(f"Error creating filing with sections: {e}")
            raise
    
    def create_section(
        self,
        section_id: str,
        accession_number: str,
        section_item: Optional[str] = None,
        section_type: str = "periodic_report_section",
        order: int = 0
    ) -> bool:
        """
        Create a Section node linked to Filing
        
        Args:
            section_id: Unique section identifier
            accession_number: Filing accession number
            section_item: Section item (e.g., "Item 1", "Item 7")
            section_type: Section type (periodic_report_section, form8k_item, etc.)
            order: Section order within filing
            
        Returns:
            True if successful
        """
        query = """
        MATCH (f:Filing {accession_number: $accession_number})
        MERGE (s:Section {section_id: $section_id})
        SET s.section_item = $section_item,
            s.section_type = $section_type,
            s.order = $order,
            s.created_at = datetime()
        MERGE (f)-[:CONTAINS {order: $order}]->(s)
        """
        
        try:
            self.client.execute_query(query, {
                "section_id": section_id,
                "accession_number": accession_number,
                "section_item": section_item,
                "section_type": section_type,
                "order": order
            })
            return True
        except Exception as e:
            logger.error(f"Error creating section: {e}")
            raise
    
    def create_chunk_with_embedding(
        self,
        chunk_id: str,
        section_id: str,
        accession_number: str,
        cik: str,
        content: str,
        embedding: List[float],
        chunk_index: int,
        form_type: str,
        semantic_type: str = "paragraph"
    ) -> bool:
        """
        Create a Chunk node with embedding stored as property
        
        Args:
            chunk_id: Unique chunk identifier
            section_id: Section identifier
            accession_number: Filing accession number
            cik: Company CIK
            content: Chunk text content
            embedding: Embedding vector (list of floats)
            chunk_index: Chunk index within section
            form_type: Form type
            semantic_type: Semantic type (paragraph, risk_discussion, financial_analysis, etc.)
            
        Returns:
            True if successful
        """
        query = """
        MATCH (s:Section {section_id: $section_id})
        MATCH (c:Company {cik: $cik})
        MERGE (ch:Chunk {chunk_id: $chunk_id})
        SET ch.content = $content,
            ch.embedding = $embedding,
            ch.chunk_index = $chunk_index,
            ch.form_type = $form_type,
            ch.semantic_type = $semantic_type,
            ch.company_cik = $cik,
            ch.content_length = $content_length,
            ch.created_at = datetime()
        MERGE (s)-[:CONTAINS]->(ch)
        MERGE (ch)-[:FROM_COMPANY]->(c)
        """
        
        try:
            self.client.execute_query(query, {
                "chunk_id": chunk_id,
                "section_id": section_id,
                "cik": cik,
                "content": content,
                "embedding": embedding,
                "chunk_index": chunk_index,
                "form_type": form_type,
                "semantic_type": semantic_type,
                "content_length": len(content)
            })
            logger.debug(f"Created chunk {chunk_id} with embedding (dimension: {len(embedding)})")
            return True
        except Exception as e:
            logger.error(f"Error creating chunk with embedding: {e}")
            raise
    
    def search_chunks_by_vector(
        self,
        query_embedding: List[float],
        limit: int = 10,
        semantic_type: Optional[str] = None,
        company_cik: Optional[str] = None,
        form_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search chunks using vector similarity (hybrid search)
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            semantic_type: Filter by semantic type
            company_cik: Filter by company CIK
            form_type: Filter by form type
            
        Returns:
            List of chunk results with similarity scores
        """
        # Build WHERE clause for filtering
        where_clauses = []
        params = {
            "query_embedding": query_embedding,
            "limit": limit
        }
        
        if semantic_type:
            where_clauses.append("ch.semantic_type = $semantic_type")
            params["semantic_type"] = semantic_type
        
        if company_cik:
            where_clauses.append("ch.company_cik = $company_cik")
            params["company_cik"] = company_cik
        
        if form_type:
            where_clauses.append("ch.form_type = $form_type")
            params["form_type"] = form_type
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Try vector similarity search (Neo4j 5.x+)
        # Fallback to graph traversal if vector indexes not available
        try:
            query = f"""
            CALL db.index.vector.queryNodes('textChunkEmbeddings', $limit, $query_embedding)
            YIELD node AS ch, score
            WHERE {where_clause}
            MATCH (ch)-[:FROM_COMPANY]->(c:Company)
            MATCH (ch)<-[:CONTAINS]-(s:Section)<-[:CONTAINS]-(f:Filing)
            RETURN ch.chunk_id AS chunk_id,
                   ch.content AS content,
                   ch.semantic_type AS semantic_type,
                   ch.form_type AS form_type,
                   c.ticker AS ticker,
                   c.name AS company_name,
                   f.accession_number AS accession_number,
                   s.section_item AS section_item,
                   score AS similarity_score
            ORDER BY score DESC
            LIMIT $limit
            """
            results = self.client.execute_query(query, params)
            return results
        except Exception as e:
            logger.warning(f"Vector similarity search not available: {e}")
            # Fallback: return empty results or use graph traversal
            logger.warning("Falling back to graph traversal search")
            return []
    
    def search_chunks_by_graph(
        self,
        company_ticker: Optional[str] = None,
        form_type: Optional[str] = None,
        section_item: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search chunks using graph traversal (fallback when vector search unavailable)
        
        Args:
            company_ticker: Filter by company ticker
            form_type: Filter by form type
            section_item: Filter by section item
            limit: Maximum number of results
            
        Returns:
            List of chunk results
        """
        where_clauses = []
        params = {"limit": limit}
        
        if company_ticker:
            where_clauses.append("c.ticker = $ticker")
            params["ticker"] = company_ticker
        
        if form_type:
            where_clauses.append("f.form_type = $form_type")
            params["form_type"] = form_type
        
        if section_item:
            where_clauses.append("s.section_item = $section_item")
            params["section_item"] = section_item
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        MATCH (c:Company)-[:FILED_BY]->(f:Filing)-[:CONTAINS]->(s:Section)-[:CONTAINS]->(ch:Chunk)
        WHERE {where_clause}
        RETURN ch.chunk_id AS chunk_id,
               ch.content AS content,
               ch.semantic_type AS semantic_type,
               ch.form_type AS form_type,
               c.ticker AS ticker,
               c.name AS company_name,
               f.accession_number AS accession_number,
               s.section_item AS section_item
        ORDER BY f.filing_date DESC
        LIMIT $limit
        """
        
        try:
            results = self.client.execute_query(query, params)
            return results
        except Exception as e:
            logger.error(f"Error in graph search: {e}")
            return []
