"""LLM-based query parser for extracting symbols, intent, and entities from user queries"""

import json
import re
from typing import Dict, Any, List, Optional
from loguru import logger

from src.utils.llm_client import LLMClient


class QueryParser:
    """
    LLM-based query parser that extracts stock symbols, intent, and entities from user queries.
    Handles all user scenario variations including company names, multiple formats, and context.
    Falls back to enhanced regex if LLM is unavailable or fails.
    """
    
    # Enhanced regex patterns
    SYMBOL_PATTERN = re.compile(r'\b[A-Z]{1,5}\b', re.IGNORECASE)
    PARENTHETICAL_PATTERN = re.compile(r'\(([A-Z]{1,5})\)', re.IGNORECASE)  # Extract from "Company (SYMBOL)"
    
    # Common words to filter out
    COMMON_WORDS = {
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 
        'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 
        'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'WAY', 'USE', 'SHE', 'MAN', 'HAD',
        'ITS', 'HIM', 'HER', 'THEY', 'THEM', 'THIS', 'THAT', 'THESE', 'THOSE'
    }
    
    # Common company name to ticker mappings
    COMPANY_NAME_MAP = {
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'tesla': 'TSLA',
        'google': 'GOOGL',
        'amazon': 'AMZN',
        'nvidia': 'NVDA',
        'meta': 'META',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'amd': 'AMD',
        'intel': 'INTC',
        'rivian': 'RIVN',
        'lucid': 'LCID',
        'alphabet': 'GOOGL',
    }
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize query parser
        
        Args:
            llm_client: LLM client for intelligent extraction (optional)
        """
        self.llm_client = llm_client
        logger.info(f"Initialized QueryParser (LLM available: {llm_client is not None})")
    
    def parse(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse query to extract symbols, intent, and entities
        
        Args:
            query: User query string
            conversation_context: Previous conversation context for follow-up queries
            
        Returns:
            Dictionary with:
            - symbols: List of stock ticker symbols
            - intent_type: Query intent type
            - intent_flags: Intent flags dictionary
            - entities: Extracted entities (timeframes, metrics, filing types)
            - confidence: Extraction confidence
            - needs_clarification: Whether query needs clarification
            - clarification_question: Question to ask if clarification needed
            - extraction_method: "llm" or "regex"
            - reasoning: Brief explanation
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to parser")
            return self._empty_result("Empty query")
        
        query = query.strip()
        logger.debug(f"Parsing query: {query[:100]}...")
        
        # Try LLM-based extraction first
        if self.llm_client:
            try:
                result = self._llm_parse(query, conversation_context)
                if result and result.get("symbols"):
                    logger.info(f"LLM extraction succeeded: symbols={result.get('symbols')}, intent={result.get('intent_type')}")
                    return result
                else:
                    logger.warning("LLM extraction returned no symbols, falling back to regex")
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}, falling back to regex")
        
        # Fallback to regex extraction
        logger.info("Using regex fallback for symbol extraction")
        return self._regex_parse(query)
    
    def _llm_parse(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse query using LLM
        
        Args:
            query: User query string
            conversation_context: Previous conversation context
            
        Returns:
            Parsed result dictionary
        """
        system_prompt = """You are a financial query parser. Extract stock symbols, intent, and entities from user queries.

Rules:
1. Extract stock ticker symbols (e.g., "AAPL", "MSFT")
2. Map company names to tickers when possible:
   - "Apple" → "AAPL"
   - "Microsoft" → "MSFT"
   - "Tesla" → "TSLA"
   - "Google" → "GOOGL" or "GOOG"
   - "Amazon" → "AMZN"
   - "NVIDIA" → "NVDA"
   - "Meta" → "META"
   - "Netflix" → "NFLX"
   - "AMD" → "AMD"
   - "Intel" → "INTC"
   - "Rivian" → "RIVN"
   - "Lucid" → "LCID"
   - And other common companies
3. Handle various formats:
   - "Apple Inc. (AAPL)" → extract "AAPL"
   - "Microsoft (MSFT)" → extract "MSFT"
   - "AAPL" → extract "AAPL"
   - "Apple" → extract "AAPL" (if context indicates stock)
4. Identify query intent:
   - "analysis" | "comparison" | "trend" | "filing" | "comprehensive" | "metric"
5. Extract entities:
   - timeframes: "6-month", "last year", "2023", "since January 2024", etc.
   - metrics: "P/E ratio", "market cap", "revenue", etc.
   - filing_types: "10-K", "10-Q", "annual report", "quarterly report", etc.
   - filing_year: year number if specified
6. Handle multiple entities: extract all symbols from lists
7. Understand context: "Apple stock" vs "apple fruit"
8. For follow-up queries: use conversation context if provided to resolve references like "its", "that company", "those stocks"

Respond with valid JSON only. Do not include any markdown formatting or code blocks."""

        user_prompt = f"""Parse this financial query: "{query}"
{f"Previous context: {conversation_context}" if conversation_context else ""}

Extract:
- symbols: List of stock ticker symbols (e.g., ["AAPL"]) - uppercase only
- intent_type: "analysis" | "comparison" | "trend" | "filing" | "comprehensive" | "metric"
- is_comparison: boolean (true if comparing multiple entities)
- is_trend: boolean (true if asking about trends)
- is_edgar: boolean (true if asking about SEC filings)
- is_comprehensive: boolean (true if requesting comprehensive analysis)
- is_metric_query: boolean (true if asking for specific metric)
- entities: {{
    "timeframe": "..." | null,
    "metrics": ["..."] | [],
    "filing_type": "10-K" | "10-Q" | null,
    "filing_year": number | null
}}
- confidence: "high" | "medium" | "low"
- needs_clarification: boolean (true if query is ambiguous)
- clarification_question: string | null (if needs_clarification is true)
- reasoning: brief explanation

JSON Response:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm_client.completion(
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            content = self.llm_client.get_content(response)
            
            # Clean content - remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON response
            try:
                parsed = json.loads(content)
                
                # Normalize symbols to uppercase
                if "symbols" in parsed and isinstance(parsed["symbols"], list):
                    parsed["symbols"] = [s.upper() for s in parsed["symbols"] if s]
                
                # Ensure required fields
                result = {
                    "symbols": parsed.get("symbols", []),
                    "intent_type": parsed.get("intent_type", "analysis"),
                    "intent_flags": {
                        "is_comparison": parsed.get("is_comparison", False),
                        "is_trend": parsed.get("is_trend", False),
                        "is_edgar": parsed.get("is_edgar", False),
                        "is_comprehensive": parsed.get("is_comprehensive", False),
                        "is_metric_query": parsed.get("is_metric_query", False),
                        "is_single_entity": len(parsed.get("symbols", [])) == 1,
                        "is_multi_entity": len(parsed.get("symbols", [])) > 1
                    },
                    "entities": parsed.get("entities", {}),
                    "confidence": parsed.get("confidence", "medium"),
                    "needs_clarification": parsed.get("needs_clarification", False),
                    "clarification_question": parsed.get("clarification_question"),
                    "extraction_method": "llm",
                    "reasoning": parsed.get("reasoning", "LLM extraction")
                }
                
                logger.debug(f"LLM parsed result: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}, content: {content[:200]}")
                raise ValueError(f"Invalid JSON response from LLM: {e}")
                
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise
    
    def _regex_parse(self, query: str) -> Dict[str, Any]:
        """
        Parse query using enhanced regex fallback
        
        Args:
            query: User query string
            
        Returns:
            Parsed result dictionary
        """
        symbols = []
        
        # First, try to extract from parenthetical notation: "Company (SYMBOL)"
        parenthetical_matches = self.PARENTHETICAL_PATTERN.findall(query)
        if parenthetical_matches:
            symbols.extend([s.upper() for s in parenthetical_matches])
            logger.debug(f"Extracted symbols from parenthetical notation: {symbols}")
        
        # Then, extract standalone symbols (1-5 uppercase letters)
        standalone_matches = self.SYMBOL_PATTERN.findall(query)
        for match in standalone_matches:
            symbol = match.upper()
            # Filter out common words and already found symbols
            if symbol not in self.COMMON_WORDS and symbol not in symbols:
                # Basic validation: should be 1-5 letters, all uppercase after normalization
                if len(symbol) >= 1 and len(symbol) <= 5 and symbol.isalpha():
                    symbols.append(symbol)
        
        # Try to map company names to tickers
        query_lower = query.lower()
        for company_name, ticker in self.COMPANY_NAME_MAP.items():
            if company_name in query_lower and ticker not in symbols:
                # Check if context suggests stock (not fruit, etc.)
                if any(word in query_lower for word in ['stock', 'company', 'inc', 'corp', 'ticker', 'symbol', 'analyze', 'compare']):
                    symbols.append(ticker)
                    logger.debug(f"Mapped company name '{company_name}' to ticker '{ticker}'")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for s in symbols:
            if s not in seen:
                seen.add(s)
                unique_symbols.append(s)
        symbols = unique_symbols
        
        # Determine intent from query
        query_lower = query.lower()
        is_comparison = len(symbols) > 1 or any(word in query_lower for word in ['compare', 'comparison', 'versus', 'vs', 'vs.', 'against'])
        is_trend = any(word in query_lower for word in ['trend', 'trends', 'trending', 'pattern', 'historical', 'over time'])
        is_edgar = any(word in query_lower for word in ['10-k', '10-q', 'filing', 'filings', 'sec', 'edgar', 'annual report', 'quarterly report'])
        is_comprehensive = any(word in query_lower for word in ['comprehensive', 'complete', 'full', 'detailed', 'deep dive'])
        is_metric_query = any(word in query_lower for word in ['market cap', 'p/e', 'pe ratio', 'revenue', 'price', 'ratio'])
        
        # Determine intent type
        if is_edgar:
            intent_type = "filing_analysis"
        elif is_comparison:
            intent_type = "comprehensive_comparison" if is_comprehensive else "comparison"
        elif is_trend:
            intent_type = "comprehensive_trend" if is_comprehensive else "trend"
        elif is_comprehensive:
            intent_type = "comprehensive_analysis"
        elif is_metric_query:
            intent_type = "metric"
        else:
            intent_type = "analysis"
        
        # Extract basic entities
        entities = {}
        
        # Extract timeframe
        timeframe_patterns = [
            r'(\d+)\s*month',
            r'last\s+year',
            r'last\s+(\d+)\s+years?',
            r'since\s+\w+\s+\d{4}',
            r'\d{4}'
        ]
        for pattern in timeframe_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entities["timeframe"] = match.group(0)
                break
        
        # Extract metrics
        metrics = []
        metric_keywords = ['market cap', 'p/e', 'pe ratio', 'revenue', 'price', 'ratio', 'eps', 'dividend']
        for keyword in metric_keywords:
            if keyword in query_lower:
                metrics.append(keyword)
        if metrics:
            entities["metrics"] = metrics
        
        # Extract filing type
        if '10-k' in query_lower or 'annual report' in query_lower:
            entities["filing_type"] = "10-K"
        elif '10-q' in query_lower or 'quarterly report' in query_lower:
            entities["filing_type"] = "10-Q"
        
        # Extract filing year
        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            entities["filing_year"] = int(year_match.group(1))
        
        result = {
            "symbols": symbols,
            "intent_type": intent_type,
            "intent_flags": {
                "is_comparison": is_comparison,
                "is_trend": is_trend,
                "is_edgar": is_edgar,
                "is_comprehensive": is_comprehensive,
                "is_metric_query": is_metric_query,
                "is_single_entity": len(symbols) == 1,
                "is_multi_entity": len(symbols) > 1
            },
            "entities": entities,
            "confidence": "high" if symbols else "low",
            "needs_clarification": len(symbols) == 0 and not is_edgar,
            "clarification_question": "Which stock or company would you like me to analyze?" if len(symbols) == 0 else None,
            "extraction_method": "regex",
            "reasoning": f"Regex extraction found {len(symbols)} symbol(s)"
        }
        
        logger.debug(f"Regex parsed result: {result}")
        return result
    
    def _empty_result(self, reasoning: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "symbols": [],
            "intent_type": "analysis",
            "intent_flags": {
                "is_comparison": False,
                "is_trend": False,
                "is_edgar": False,
                "is_comprehensive": False,
                "is_metric_query": False,
                "is_single_entity": False,
                "is_multi_entity": False
            },
            "entities": {},
            "confidence": "low",
            "needs_clarification": True,
            "clarification_question": "Please provide a stock symbol or company name to analyze.",
            "extraction_method": "none",
            "reasoning": reasoning
        }
