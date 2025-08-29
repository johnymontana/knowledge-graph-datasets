#!/usr/bin/env python3
"""
Wikidata SPARQL Query Service Client

This module provides functionality to query Wikidata using SPARQL
and process the results for Neo4j import.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Generator, Tuple
from urllib.parse import urlencode
import requests
from SPARQLWrapper import SPARQLWrapper, JSON, CSV
import json
import pandas as pd

logger = logging.getLogger(__name__)

class WikidataSPARQLClient:
    """Client for querying Wikidata SPARQL endpoint"""
    
    def __init__(self, 
                 endpoint: str = "https://query.wikidata.org/sparql",
                 request_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30):
        """Initialize SPARQL client
        
        Args:
            endpoint: Wikidata SPARQL endpoint URL
            request_delay: Delay between requests in seconds
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize SPARQL wrapper
        self.sparql = SPARQLWrapper(endpoint)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(timeout)
        
        # Set User-Agent for responsible scraping
        self.sparql.agent = "WikidataKnowledgeGraph/1.0 (https://github.com/johnymontana/knowledge-graph-datasets)"
        
        logger.info(f"Initialized Wikidata SPARQL client: {endpoint}")
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute SPARQL query and return results
        
        Args:
            query: SPARQL query string
            limit: Optional limit for results
            
        Returns:
            List of result bindings
        """
        if limit:
            query = self._add_limit_to_query(query, limit)
            
        logger.info(f"Executing SPARQL query (length: {len(query)})")
        logger.debug(f"Query: {query}")
        
        for attempt in range(self.max_retries + 1):
            try:
                # Add delay between requests to be respectful
                if attempt > 0:
                    time.sleep(self.request_delay * attempt)
                
                self.sparql.setQuery(query)
                results = self.sparql.queryAndConvert()
                
                if "results" in results and "bindings" in results["results"]:
                    bindings = results["results"]["bindings"]
                    logger.info(f"Query returned {len(bindings)} results")
                    return bindings
                else:
                    logger.warning("No results found in SPARQL response")
                    return []
                    
            except Exception as e:
                logger.warning(f"SPARQL query attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    logger.error(f"SPARQL query failed after {self.max_retries + 1} attempts")
                    raise
                    
        return []
    
    def execute_query_paginated(self, 
                              query: str, 
                              page_size: int = 10000, 
                              max_results: Optional[int] = None) -> Generator[List[Dict[str, Any]], None, None]:
        """Execute query with pagination for large result sets
        
        Args:
            query: SPARQL query string
            page_size: Number of results per page
            max_results: Maximum total results to return
            
        Yields:
            Pages of results
        """
        offset = 0
        total_results = 0
        
        while True:
            # Add LIMIT and OFFSET to query, but only if LIMIT not already present
            if "LIMIT" not in query.upper():
                paginated_query = f"{query.rstrip()} LIMIT {page_size} OFFSET {offset}"
            else:
                # If LIMIT already exists, replace it with page_size and add OFFSET
                import re
                paginated_query = re.sub(r'\s+LIMIT\s+\d+', f' LIMIT {page_size}', query, flags=re.IGNORECASE)
                paginated_query = f"{paginated_query.rstrip()} OFFSET {offset}"
            
            results = self.execute_query(paginated_query)
            
            if not results:
                break
                
            yield results
            
            total_results += len(results)
            offset += page_size
            
            # Check if we've reached max_results or got fewer results than page_size
            if (max_results and total_results >= max_results) or len(results) < page_size:
                break
                
            logger.info(f"Processed {total_results} results, continuing...")
            
            # Add delay between pages
            time.sleep(self.request_delay)
    
    def query_to_dataframe(self, query: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Execute query and return results as pandas DataFrame
        
        Args:
            query: SPARQL query string
            limit: Optional limit for results
            
        Returns:
            DataFrame with query results
        """
        results = self.execute_query(query, limit)
        return self._bindings_to_dataframe(results)
    
    def _bindings_to_dataframe(self, bindings: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert SPARQL bindings to pandas DataFrame"""
        if not bindings:
            return pd.DataFrame()
            
        # Extract variable names from first binding
        columns = list(bindings[0].keys())
        
        # Convert bindings to rows
        rows = []
        for binding in bindings:
            row = {}
            for col in columns:
                if col in binding:
                    value = binding[col]
                    # Extract the actual value and datatype
                    if isinstance(value, dict):
                        row[col] = value.get('value', '')
                        row[f"{col}_type"] = value.get('type', '')
                        if 'datatype' in value:
                            row[f"{col}_datatype"] = value.get('datatype', '')
                    else:
                        row[col] = value
                else:
                    row[col] = None
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def _add_limit_to_query(self, query: str, limit: int) -> str:
        """Add LIMIT clause to query if not present"""
        query_upper = query.upper().strip()
        if "LIMIT" not in query_upper:
            return f"{query.rstrip()} LIMIT {limit}"
        
        # If LIMIT already exists, replace it with the new limit
        import re
        # Remove existing LIMIT clause and add new one
        query = re.sub(r'\s+LIMIT\s+\d+', '', query, flags=re.IGNORECASE)
        return f"{query.rstrip()} LIMIT {limit}"
    
    def get_entity_info(self, entity_id: str) -> Dict[str, Any]:
        """Get basic information about a Wikidata entity
        
        Args:
            entity_id: Wikidata entity ID (e.g., 'Q42')
            
        Returns:
            Dictionary with entity information
        """
        query = f"""
        SELECT ?item ?itemLabel ?itemDescription ?itemAltLabel WHERE {{
            VALUES ?item {{ wd:{entity_id} }}
            SERVICE wikibase:label {{ 
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
            }}
        }}
        """
        
        results = self.execute_query(query)
        if results:
            return self._bindings_to_dataframe(results).iloc[0].to_dict()
        return {}
    
    def search_entities(self, search_term: str, limit: int = 10) -> pd.DataFrame:
        """Search for entities by label
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results
            
        Returns:
            DataFrame with search results
        """
        query = f"""
        SELECT ?item ?itemLabel ?itemDescription WHERE {{
            ?item rdfs:label ?itemLabel .
            FILTER(CONTAINS(LCASE(?itemLabel), LCASE("{search_term}")))
            FILTER(LANG(?itemLabel) = "en")
            SERVICE wikibase:label {{ 
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
            }}
        }} LIMIT {limit}
        """
        
        return self.query_to_dataframe(query)

class WikidataQueries:
    """Collection of predefined Wikidata SPARQL queries"""
    
    @staticmethod
    def get_scientists(limit: int = 1000) -> str:
        """Query for scientists with basic information"""
        return f"""
        SELECT ?item ?itemLabel ?birthDate ?deathDate ?fieldLabel ?countryLabel ?coordinates WHERE {{
            ?item wdt:P31 wd:Q5 .                    # human
            ?item wdt:P106 wd:Q901 .                 # occupation: scientist
            
            OPTIONAL {{ ?item wdt:P569 ?birthDate }}  # birth date
            OPTIONAL {{ ?item wdt:P570 ?deathDate }}  # death date
            OPTIONAL {{ 
                ?item wdt:P101 ?field .              # field of work
            }}
            OPTIONAL {{ 
                ?item wdt:P27 ?country .             # country of citizenship
            }}
            OPTIONAL {{ 
                ?item wdt:P625 ?coordinates .        # coordinates
            }}
            
            SERVICE wikibase:label {{ 
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
            }}
        }} LIMIT {limit}
        """
    
    @staticmethod
    def get_cities(country: str = "Q30", limit: int = 1000) -> str:
        """Query for cities in a specific country
        
        Args:
            country: Wikidata ID for country (default: Q30 = United States)
            limit: Maximum results
        """
        return f"""
        SELECT ?item ?itemLabel ?population ?coordinates ?stateLabel ?mayorLabel WHERE {{
            ?item wdt:P31/wdt:P279* wd:Q515 .        # city
            ?item wdt:P17 wd:{country} .             # country
            
            OPTIONAL {{ ?item wdt:P1082 ?population }}  # population
            OPTIONAL {{ ?item wdt:P625 ?coordinates }}  # coordinates
            OPTIONAL {{ ?item wdt:P131 ?state }}        # state/province
            OPTIONAL {{ ?item wdt:P6 ?mayor }}          # mayor
            
            SERVICE wikibase:label {{ 
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
            }}
        }} LIMIT {limit}
        """
    
    @staticmethod
    def get_universities(limit: int = 1000) -> str:
        """Query for universities with basic information"""
        return f"""
        SELECT ?item ?itemLabel ?countryLabel ?coordinates ?founded ?studentsCount WHERE {{
            ?item wdt:P31/wdt:P279* wd:Q3918 .       # university
            
            OPTIONAL {{ ?item wdt:P17 ?country }}     # country
            OPTIONAL {{ ?item wdt:P625 ?coordinates }} # coordinates
            OPTIONAL {{ ?item wdt:P571 ?founded }}    # inception date
            OPTIONAL {{ ?item wdt:P2196 ?studentsCount }} # students count
            
            SERVICE wikibase:label {{ 
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
            }}
        }} LIMIT {limit}
        """
    
    @staticmethod
    def get_companies(limit: int = 1000) -> str:
        """Query for companies with basic information"""
        return f"""
        SELECT ?item ?itemLabel ?countryLabel ?coordinates ?founded ?ceo ?industry WHERE {{
            ?item wdt:P31/wdt:P279* wd:Q4830453 .    # business enterprise
            
            OPTIONAL {{ ?item wdt:P17 ?country }}     # country
            OPTIONAL {{ ?item wdt:P625 ?coordinates }} # coordinates
            OPTIONAL {{ ?item wdt:P571 ?founded }}    # inception date
            OPTIONAL {{ ?item wdt:P169 ?ceo }}        # CEO
            OPTIONAL {{ ?item wdt:P452 ?industry }}   # industry
            
            SERVICE wikibase:label {{ 
                bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" . 
            }}
        }} LIMIT {limit}
        """