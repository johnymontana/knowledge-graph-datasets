#!/usr/bin/env python3
"""
Diffbot Knowledge Graph API Client

This module provides a client for interacting with the Diffbot Knowledge Graph API
to search and retrieve entities and relationships.
"""

import asyncio
import aiohttp
import logging
import time
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from urllib.parse import urlencode
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DiffbotEntity:
    """Represents a Diffbot Knowledge Graph entity"""
    id: str
    type: str
    name: str
    properties: Dict[str, Any]
    relationships: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []

class DiffbotClient:
    """Client for Diffbot Knowledge Graph API"""
    
    def __init__(self, 
                 token: str,
                 base_url: str = "https://kg.diffbot.com/kg/v3",
                 request_delay: float = 1.0,
                 max_retries: int = 3,
                 timeout: int = 30,
                 max_concurrent: int = 5):
        """Initialize the Diffbot client"""
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        
        # Session will be created in async context
        self._session = None
        self._semaphore = None
        
        if not token:
            raise ValueError("Diffbot token is required")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def search_entities(self, 
                            query: str,
                            entity_types: Optional[List[str]] = None,
                            size: int = 100,
                            from_: int = 0) -> Dict[str, Any]:
        """Search for entities in the knowledge graph"""
        params = {
            'token': self.token,
            'query': query,
            'size': size,
            'from': from_
        }
        
        # Note: entity_types parameter is kept for compatibility but not sent to API
        # as it causes HTTP 400 errors. Filtering by type will be done post-query.
        
        endpoint = f"{self.base_url}/dql"
        
        async with self._semaphore:
            response = await self._make_request('GET', endpoint, params=params)
            return response
    
    async def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by its ID"""
        params = {
            'token': self.token,
            'id': entity_id
        }
        
        endpoint = f"{self.base_url}/kg"
        
        async with self._semaphore:
            response = await self._make_request('GET', endpoint, params=params)
            
            if response and 'data' in response and response['data']:
                return response['data'][0]
            return None
    
    async def enhance_entities(self, entities: List[Dict[str, str]]) -> Dict[str, Any]:
        """Enhance existing entities with Diffbot data"""
        data = {'entities': entities}
        params = {'token': self.token}
        
        endpoint = f"{self.base_url}/enhance"
        
        async with self._semaphore:
            response = await self._make_request('POST', endpoint, params=params, json_data=data)
            return response
    
    async def search_entities_paginated(self,
                                      query: str,
                                      entity_types: Optional[List[str]] = None,
                                      page_size: int = 100,
                                      max_results: int = 10000) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Search entities with pagination support"""
        from_offset = 0
        total_fetched = 0
        
        while total_fetched < max_results:
            # Adjust page size for last page
            current_size = min(page_size, max_results - total_fetched)
            
            try:
                response = await self.search_entities(
                    query=query,
                    entity_types=entity_types,
                    size=current_size,
                    from_=from_offset
                )
                
                if not response or 'data' not in response:
                    break
                
                entities = response['data']
                if not entities:
                    break
                
                # Transform the response to match expected format
                transformed_entities = []
                for item in entities:
                    if 'entity' in item:
                        # Extract entity data from the nested structure
                        entity_data = item['entity'].copy()
                        # Add the score if available
                        if 'score' in item:
                            entity_data['score'] = item['score']
                        transformed_entities.append(entity_data)
                    else:
                        transformed_entities.append(item)
                
                # Filter by entity types if specified
                if entity_types:
                    filtered_entities = []
                    for entity in transformed_entities:
                        entity_types_list = entity.get('types', [])
                        if any(entity_type in entity_types_list for entity_type in entity_types):
                            filtered_entities.append(entity)
                    transformed_entities = filtered_entities
                
                yield transformed_entities
                
                total_fetched += len(transformed_entities)
                from_offset += current_size
                
                # Check if we've reached the end
                total_available = response.get('hits', 0)
                if from_offset >= total_available:
                    break
                
                # Respect rate limits
                await asyncio.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error in paginated search: {e}")
                break
    
    async def _make_request(self,
                          method: str,
                          url: str,
                          params: Optional[Dict[str, Any]] = None,
                          json_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    async with self._session.get(url, params=params) as response:
                        return await self._handle_response(response)
                elif method == 'POST':
                    async with self._session.post(url, params=params, json=json_data) as response:
                        return await self._handle_response(response)
                        
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        
        return None
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Dict[str, Any]]:
        """Handle HTTP response"""
        if response.status == 200:
            return await response.json()
        elif response.status == 429:  # Rate limited
            retry_after_header = response.headers.get('Retry-After', str(self.request_delay))
            try:
                # Try to parse as seconds first
                retry_after = int(retry_after_header)
            except ValueError:
                # Parse human-readable time strings like "5 days, 16:37:22"
                retry_after = self._parse_retry_after_header(retry_after_header)
            
            logger.warning(f"Rate limited, waiting {retry_after} seconds")
            await asyncio.sleep(retry_after)
            raise Exception("Rate limited")
        elif response.status == 401:
            raise Exception("Invalid Diffbot token")
        elif response.status >= 400:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")
        
        return None
    
    def _parse_retry_after_header(self, retry_after_header: str) -> int:
        """Parse human-readable retry-after header into seconds"""
        import re
        
        # Default to 60 seconds if parsing fails
        default_seconds = 60
        
        try:
            # Handle formats like "5 days, 16:37:22" or "2 hours, 30 minutes"
            if 'days' in retry_after_header.lower():
                # For now, just wait 60 seconds instead of the full days
                # This is a reasonable compromise for development/testing
                logger.info(f"Rate limited for {retry_after_header}, waiting 60 seconds instead of full duration")
                return 60
            elif 'hours' in retry_after_header.lower():
                # Wait 30 seconds for hour-based delays
                logger.info(f"Rate limited for {retry_after_header}, waiting 30 seconds instead of full duration")
                return 30
            elif 'minutes' in retry_after_header.lower():
                # Extract minutes and convert to seconds
                match = re.search(r'(\d+)\s*minutes?', retry_after_header.lower())
                if match:
                    minutes = int(match.group(1))
                    return min(minutes * 60, 300)  # Cap at 5 minutes
                return 60
            else:
                # Try to extract any number of seconds
                match = re.search(r'(\d+)\s*seconds?', retry_after_header.lower())
                if match:
                    return int(match.group(1))
                return default_seconds
        except Exception as e:
            logger.warning(f"Error parsing retry-after header '{retry_after_header}': {e}, using default")
            return default_seconds

class DiffbotQueries:
    """Predefined search queries for common entity types"""
    
    @staticmethod
    def search_organizations(name_pattern: str = None, limit: int = 100) -> str:
        """Query to search for organizations"""
        if name_pattern:
            return f'type:Organization name:"{name_pattern}"'
        return 'type:Organization'
    
    @staticmethod
    def search_people(name_pattern: str = None, limit: int = 100) -> str:
        """Query to search for people"""
        if name_pattern:
            return f'type:Person name:"{name_pattern}"'
        return 'type:Person'
    
    @staticmethod
    def search_articles(title_pattern: str = None, domain: str = None) -> str:
        """Query to search for articles"""
        query_parts = ['type:Article']
        
        if title_pattern:
            query_parts.append(f'title:"{title_pattern}"')
        if domain:
            query_parts.append(f'site:"{domain}"')
        
        return ' '.join(query_parts)
    
    @staticmethod
    def search_by_location(location: str, entity_types: List[str] = None) -> str:
        """Query to search entities by location"""
        if entity_types:
            type_filter = f"type:{','.join(entity_types)}"
            return f'{type_filter} location:"{location}"'
        return f'location:"{location}"'