"""EDGAR Agent for Phase 5: EDGAR Integration"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from src.agents.base_agent import BaseAgent
from src.graph_db.neo4j_client import Neo4jClient
from src.graph_db.edgar_schema import EdgarNeo4jSchema
from src.vector_db.embeddings import EmbeddingPipeline


class EdgarAgent(BaseAgent):
    """
    EDGAR Agent: Retrieves and processes SEC EDGAR filings
    
    This agent:
    1. Fetches SEC filings using edgartools
    2. Parses filing content into sections
    3. Chunks sections for vector storage
    4. Stores structured data in Neo4j
    5. Generates embeddings for chunks
    """
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedding_pipeline: Optional[EmbeddingPipeline] = None
    ):
        """
        Initialize EDGAR Agent
        
        Args:
            neo4j_client: Neo4j client for graph storage
            embedding_pipeline: Embedding pipeline for vector generation
        """
        super().__init__("EdgarAgent")
        self.neo4j_client = neo4j_client
        self.edgar_schema = EdgarNeo4jSchema(neo4j_client)
        self.embedding_pipeline = embedding_pipeline or EmbeddingPipeline()
        
        # Initialize edgartools
        self._initialize_edgartools()
    
    def _initialize_edgartools(self):
        """Initialize edgartools library"""
        try:
            import edgar
            from edgar import Company, Filing, set_identity
            
            self.edgar_module = edgar
            self.Company = Company
            self.Filing = Filing
            self.set_identity = set_identity
            
            # Set identity (required by SEC)
            email = os.getenv("EDGAR_IDENTITY")
            if email:
                set_identity(email)
                logger.info(f"Set EDGAR identity: {email}")
            else:
                logger.warning("EDGAR_IDENTITY not set. SEC requires identity for EDGAR access.")
                logger.warning("Set EDGAR_IDENTITY environment variable.")
                logger.warning("Example: export EDGAR_IDENTITY='your.email@example.com'")
            
            logger.info("Successfully initialized edgartools")
        except ImportError as e:
            logger.error(f"Failed to import edgartools: {e}")
            logger.error("Install with: pip install edgartools>=5.8.0")
            raise
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute EDGAR agent
        
        Args:
            state: AgentState dictionary
            
        Returns:
            Updated AgentState dictionary with EDGAR data
        """
        if not self.validate_state(state):
            state.setdefault("errors", []).append("Invalid state for EdgarAgent")
            return state
        
        self.log_execution(state)
        
        symbols = state.get("symbols", [])
        query = state.get("query", "").lower()
        
        # Determine if EDGAR data is needed based on query
        edgar_keywords = ["filing", "10-k", "10-q", "8-k", "sec", "edgar", "annual report", "quarterly"]
        needs_edgar = any(keyword in query for keyword in edgar_keywords)
        
        if not needs_edgar and not symbols:
            logger.info("Query doesn't require EDGAR data, skipping")
            return state
        
        edgar_data = {}
        
        for symbol in symbols:
            try:
                logger.info(f"Fetching EDGAR data for {symbol}")
                
                # Get company filings
                filings_data = self._fetch_company_filings(symbol)
                
                if filings_data:
                    edgar_data[symbol] = filings_data
                    
                    # Add citation
                    state.setdefault("citations", []).append({
                        "source": "SEC EDGAR",
                        "symbol": symbol,
                        "type": "filing_data",
                        "filings_count": len(filings_data.get("filings", []))
                    })
                else:
                    logger.warning(f"No EDGAR filings found for {symbol}")
                    state.setdefault("errors", []).append(f"No EDGAR filings found for {symbol}")
            
            except Exception as e:
                logger.error(f"Error fetching EDGAR data for {symbol}: {e}")
                state.setdefault("errors", []).append(f"Failed to fetch EDGAR data for {symbol}: {str(e)}")
        
        # Store EDGAR data in state
        state["edgar_data"] = edgar_data
        
        return state
    
    def _fetch_company_filings(
        self,
        symbol: str,
        form_types: Optional[List[str]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Fetch company filings from SEC EDGAR
        
        Args:
            symbol: Stock ticker symbol
            form_types: List of form types to fetch (e.g., ["10-K", "10-Q"])
            limit: Maximum number of filings to fetch
            
        Returns:
            Dictionary with company info and filings
        """
        try:
            # Get company by ticker
            company = self.Company(symbol)
            
            # Get company info
            company_info = {
                "cik": company.cik,
                "name": company.name,
                "ticker": symbol
            }
            
            # Get filings
            if form_types:
                filings_obj = company.get_filings(form=form_types)
                # Convert EntityFilings to list
                filings = list(filings_obj) if hasattr(filings_obj, '__iter__') else []
            else:
                # Default: get recent 10-K and 10-Q filings
                filings_10k = company.get_filings(form="10-K")
                filings_10q = company.get_filings(form="10-Q")
                # Convert EntityFilings objects to lists and combine
                filings_list_10k = list(filings_10k) if hasattr(filings_10k, '__iter__') else []
                filings_list_10q = list(filings_10q) if hasattr(filings_10q, '__iter__') else []
                filings = filings_list_10k + filings_list_10q
            
            # Limit and process filings
            filings_list = []
            for filing in filings[:limit]:
                try:
                    filing_data = self._process_filing(filing, company_info)
                    if filing_data:
                        filings_list.append(filing_data)
                except Exception as e:
                    logger.error(f"Error processing filing {filing.accession_number}: {e}")
                    continue
            
            return {
                "company": company_info,
                "filings": filings_list,
                "fetched_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error fetching filings for {symbol}: {e}")
            raise
    
    def _process_filing(
        self,
        filing: Any,
        company_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single filing: extract sections, create chunks, store in Neo4j
        
        Args:
            filing: edgartools Filing object
            company_info: Company information dictionary
            
        Returns:
            Filing data dictionary
        """
        try:
            accession_number = filing.accession_number
            form_type = filing.form
            filing_date = filing.filing_date.isoformat() if hasattr(filing.filing_date, 'isoformat') else str(filing.filing_date)
            
            logger.info(f"Processing filing {accession_number} ({form_type})")
            
            # Get filing document
            try:
                # Try to get HTML content
                html_content = filing.html()
                
                # Extract sections from HTML
                sections = self._extract_sections(html_content, form_type)
                
            except Exception as e:
                logger.warning(f"Could not get HTML content for {accession_number}: {e}")
                # Fallback: use basic filing info
                sections = []
            
            # Store in Neo4j
            self.edgar_schema.create_filing_with_sections(
                accession_number=accession_number,
                cik=company_info["cik"],
                form_type=form_type,
                filing_date=filing_date,
                company_name=company_info["name"],
                sections=sections
            )
            
            # Create chunks with embeddings
            if sections:
                self._create_chunks_with_embeddings(
                    accession_number=accession_number,
                    cik=company_info["cik"],
                    form_type=form_type,
                    sections=sections
                )
            
            return {
                "accession_number": accession_number,
                "form_type": form_type,
                "filing_date": filing_date,
                "sections_count": len(sections),
                "sections": [s["section_id"] for s in sections]
            }
        
        except Exception as e:
            logger.error(f"Error processing filing: {e}")
            return None
    
    def _extract_sections(
        self,
        html_content: str,
        form_type: str
    ) -> List[Dict[str, Any]]:
        """
        Extract sections from filing HTML content
        
        Args:
            html_content: HTML content of filing
            form_type: Form type (10-K, 10-Q, etc.)
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Basic section extraction (can be enhanced)
        # For now, extract major sections based on form type
        if form_type in ["10-K", "10-Q"]:
            # Common sections in 10-K/10-Q
            section_items = [
                "Item 1", "Item 1A", "Item 2", "Item 3", "Item 4",
                "Item 5", "Item 6", "Item 7", "Item 7A", "Item 8",
                "Item 9", "Item 10", "Item 11", "Item 12", "Item 13",
                "Item 14", "Item 15"
            ]
            
            # Simple extraction: look for section headers
            # In production, use more sophisticated parsing
            for item in section_items:
                # Look for section in HTML (simplified)
                # Real implementation would parse HTML properly
                section_id = f"{form_type}_{item.replace(' ', '_')}"
                sections.append({
                    "section_id": section_id,
                    "section_item": item,
                    "content": f"Section {item} content extracted from {form_type}",
                    "section_type": "periodic_report_section",
                    "order": len(sections)
                })
        
        elif form_type == "8-K":
            # 8-K has different structure
            sections.append({
                "section_id": f"{form_type}_current_report",
                "section_item": "Current Report",
                "content": f"8-K current report content",
                "section_type": "form8k_item",
                "order": 0
            })
        
        return sections
    
    def _create_chunks_with_embeddings(
        self,
        accession_number: str,
        cik: str,
        form_type: str,
        sections: List[Dict[str, Any]]
    ):
        """
        Create chunks with embeddings for sections
        
        Args:
            accession_number: Filing accession number
            cik: Company CIK
            form_type: Form type
            sections: List of section dictionaries
        """
        for section in sections:
            section_id = section["section_id"]
            content = section.get("content", "")
            
            if not content or len(content.strip()) < 100:
                continue
            
            # Chunk the content (500-1000 tokens per chunk)
            chunks = self._chunk_text(content, max_tokens=800)
            
            # Generate embeddings and store chunks
            for idx, chunk_text in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.embedding_pipeline.generate_embedding(chunk_text)
                    
                    if not embedding:
                        logger.warning(f"Failed to generate embedding for chunk {idx} of {section_id}")
                        continue
                    
                    # Create chunk node with embedding
                    chunk_id = f"{section_id}_chunk_{idx}"
                    self.edgar_schema.create_chunk_with_embedding(
                        chunk_id=chunk_id,
                        section_id=section_id,
                        accession_number=accession_number,
                        cik=cik,
                        content=chunk_text,
                        embedding=embedding,
                        chunk_index=idx,
                        form_type=form_type,
                        semantic_type=section.get("section_type", "paragraph")
                    )
                    
                except Exception as e:
                    logger.error(f"Error creating chunk {idx} for {section_id}: {e}")
                    continue
    
    def _chunk_text(self, text: str, max_tokens: int = 800) -> List[str]:
        """
        Chunk text into smaller pieces
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk (approximate)
            
        Returns:
            List of text chunks
        """
        # Simple chunking: split by paragraphs, then by sentences
        # Approximate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        chunks = []
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
