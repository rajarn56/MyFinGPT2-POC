"""Neo4j schema setup for Phase 4 Knowledge Layer"""

from typing import Dict, Any, List, Optional
from loguru import logger

from src.graph_db.neo4j_client import Neo4jClient


class Neo4jSchema:
    """Manages Neo4j schema creation and initialization"""
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize schema manager
        
        Args:
            neo4j_client: Neo4jClient instance
        """
        self.client = neo4j_client
    
    def initialize_schema(self):
        """Initialize basic Neo4j schema for Phase 4"""
        logger.info("Initializing Neo4j schema for Phase 4...")
        
        try:
            # Create indexes for Company nodes
            self._create_company_indexes()
            
            # Create indexes for Filing nodes
            self._create_filing_indexes()
            
            logger.info("Neo4j schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Neo4j schema: {e}")
            raise
    
    def _create_company_indexes(self):
        """Create indexes for Company nodes"""
        # Note: Neo4j syntax varies by version. Using try-except for compatibility
        constraints_and_indexes = [
            # Company CIK constraint (unique identifier) - Neo4j 4.x+ syntax
            ("CREATE CONSTRAINT company_cik IF NOT EXISTS FOR (c:Company) REQUIRE c.cik IS UNIQUE", True),
            # Company ticker index - Neo4j 4.x+ syntax
            ("CREATE INDEX company_ticker IF NOT EXISTS FOR (c:Company) ON (c.ticker)", False),
            # Company name index
            ("CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)", False),
        ]
        
        for index_query, is_constraint in constraints_and_indexes:
            try:
                self.client.execute_query(index_query)
                logger.debug(f"Created {'constraint' if is_constraint else 'index'}: {index_query[:50]}...")
            except Exception as e:
                # Index/constraint might already exist or syntax might differ, which is fine
                logger.debug(f"Index/constraint creation (may already exist or syntax issue): {e}")
                # Try alternative syntax for older Neo4j versions
                if is_constraint:
                    try:
                        # Alternative: CREATE CONSTRAINT ON (c:Company) ASSERT c.cik IS UNIQUE
                        alt_query = f"CREATE CONSTRAINT ON (c:Company) ASSERT c.cik IS UNIQUE"
                        self.client.execute_query(alt_query)
                    except:
                        pass
    
    def _create_filing_indexes(self):
        """Create indexes for Filing nodes"""
        constraints_and_indexes = [
            # Filing accession number constraint (unique identifier)
            ("CREATE CONSTRAINT filing_accession IF NOT EXISTS FOR (f:Filing) REQUIRE f.accession_number IS UNIQUE", True),
            # Filing form type index
            ("CREATE INDEX filing_form_type IF NOT EXISTS FOR (f:Filing) ON (f.form_type)", False),
            # Filing filing date index
            ("CREATE INDEX filing_date IF NOT EXISTS FOR (f:Filing) ON (f.filing_date)", False),
        ]
        
        for index_query, is_constraint in constraints_and_indexes:
            try:
                self.client.execute_query(index_query)
                logger.debug(f"Created {'constraint' if is_constraint else 'index'}: {index_query[:50]}...")
            except Exception as e:
                # Index/constraint might already exist or syntax might differ, which is fine
                logger.debug(f"Index/constraint creation (may already exist or syntax issue): {e}")
                # Try alternative syntax for older Neo4j versions
                if is_constraint:
                    try:
                        alt_query = f"CREATE CONSTRAINT ON (f:Filing) ASSERT f.accession_number IS UNIQUE"
                        self.client.execute_query(alt_query)
                    except:
                        pass
    
    def create_company(
        self,
        cik: str,
        ticker: str,
        name: str,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create or update a Company node
        
        Args:
            cik: Company CIK (Central Index Key)
            ticker: Stock ticker symbol
            name: Company name
            sector: Sector (optional)
            industry: Industry (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            True if successful
        """
        query = """
        MERGE (c:Company {cik: $cik})
        SET c.ticker = $ticker,
            c.name = $name,
            c.sector = $sector,
            c.industry = $industry,
            c.updated_at = datetime()
        """
        
        params = {
            "cik": cik,
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            **(metadata or {})
        }
        
        try:
            self.client.execute_query(query, params)
            logger.debug(f"Created/updated Company: {ticker} ({name})")
            return True
        except Exception as e:
            logger.error(f"Error creating Company: {e}")
            raise
    
    def create_filing(
        self,
        accession_number: str,
        cik: str,
        form_type: str,
        filing_date: str,
        company_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a Filing node and link it to Company
        
        Args:
            accession_number: SEC accession number (unique identifier)
            cik: Company CIK
            form_type: Form type (e.g., "10-K", "10-Q", "8-K")
            filing_date: Filing date (ISO format string)
            company_name: Company name (optional, for display)
            metadata: Additional metadata (optional)
            
        Returns:
            True if successful
        """
        query = """
        MATCH (c:Company {cik: $cik})
        MERGE (f:Filing {accession_number: $accession_number})
        SET f.form_type = $form_type,
            f.filing_date = date($filing_date),
            f.company_name = $company_name,
            f.created_at = datetime()
        MERGE (c)-[:FILED_BY]->(f)
        """
        
        params = {
            "accession_number": accession_number,
            "cik": cik,
            "form_type": form_type,
            "filing_date": filing_date,
            "company_name": company_name,
            **(metadata or {})
        }
        
        try:
            self.client.execute_query(query, params)
            logger.debug(f"Created Filing: {accession_number} ({form_type})")
            return True
        except Exception as e:
            logger.error(f"Error creating Filing: {e}")
            raise
    
    def get_company_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get company by ticker symbol
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Company node data or None
        """
        query = """
        MATCH (c:Company {ticker: $ticker})
        RETURN c
        """
        
        results = self.client.execute_query(query, {"ticker": ticker})
        if results:
            return results[0].get("c")
        return None
    
    def get_company_filings(
        self,
        ticker: str,
        form_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get filings for a company
        
        Args:
            ticker: Stock ticker symbol
            form_type: Filter by form type (optional)
            limit: Maximum number of filings to return
            
        Returns:
            List of filing data
        """
        if form_type:
            query = """
            MATCH (c:Company {ticker: $ticker})-[:FILED_BY]->(f:Filing {form_type: $form_type})
            RETURN f
            ORDER BY f.filing_date DESC
            LIMIT $limit
            """
            params = {"ticker": ticker, "form_type": form_type, "limit": limit}
        else:
            query = """
            MATCH (c:Company {ticker: $ticker})-[:FILED_BY]->(f:Filing)
            RETURN f
            ORDER BY f.filing_date DESC
            LIMIT $limit
            """
            params = {"ticker": ticker, "limit": limit}
        
        results = self.client.execute_query(query, params)
        return [r.get("f") for r in results]
