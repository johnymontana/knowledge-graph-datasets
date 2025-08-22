#!/usr/bin/env python3
"""
NYT News to Neo4j Knowledge Graph Importer

This script imports New York Times articles from JSON files into a Neo4j knowledge graph,
generating AI embeddings for semantic search capabilities.
"""

import os
import sys
import json
import uuid
import re
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j_config import load_neo4j_config
from ai_provider import get_ai_provider

# Load environment variables
load_dotenv()

class NewsImporterNeo4j:
    """Main class for importing news articles into Neo4j"""
    
    def __init__(self, config_file: str = "config.env"):
        """Initialize the importer with configuration"""
        self.config = load_neo4j_config(config_file)
        self.driver = self.config.get_driver()
        self.database = self.config.get_database()
        self.ai_provider = get_ai_provider()
        
        # Configuration from environment
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.data_dir = os.getenv('DATA_DIR', 'data/articles')
        self.embedding_batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE', '50'))
        
        print(f"🔧 Configuration loaded:")
        print(f"  Batch size: {self.batch_size}")
        print(f"  Data directory: {self.data_dir}")
        print(f"  Embedding batch size: {self.embedding_batch_size}")
        print(f"  AI Provider: {self.ai_provider.__class__.__name__}")
        
        # Initialize schema
        self._setup_schema()
    
    def _setup_schema(self):
        """Setup Neo4j schema (constraints and indexes)"""
        print("🏗️  Setting up Neo4j schema...")
        self.config.create_indexes()
        self.config.create_vector_index()
    
    def _parse_byline(self, byline: str) -> List[str]:
        """Extract author names from byline like 'By Author1, Author2 and Author3'"""
        if not byline or not isinstance(byline, str):
            return []
        
        # Remove "By " prefix
        if byline.startswith("By "):
            byline = byline[3:]
        
        # Split by commas and 'and'
        authors = re.split(r',\s*|\s+and\s+', byline)
        return [author.strip() for author in authors if author.strip()]
    
    def _geocode_location(self, location: str) -> Optional[Dict[str, float]]:
        """Geocode a location string to coordinates"""
        try:
            # Use AI provider to geocode (simplified approach)
            prompt = f"Convert this location to coordinates: {location}. Return only JSON with lat and lon as numbers."
            response = self.ai_provider.chat_completion([
                {"role": "user", "content": prompt}
            ])
            
            # Try to parse JSON response
            coordinates = json.loads(response.strip())
            if "lat" in coordinates and "lon" in coordinates:
                return {"latitude": float(coordinates["lat"]), "longitude": float(coordinates["lon"])}
        except:
            pass
        
        return None
    
    def _process_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single article and extract entities"""
        # Handle different JSON structures
        article = article_data
        if 'response' in article_data and 'docs' in article_data['response']:
            if article_data['response']['docs']:
                article = article_data['response']['docs'][0]
            else:
                return None
        elif 'results' in article_data:
            if article_data['results']:
                article = article_data['results'][0]
            else:
                return None
        
        # Extract basic article information
        title = article.get('headline', {}).get('main', '') or article.get('title', '')
        abstract = article.get('abstract', '') or article.get('lead_paragraph', '')
        
        if not title and not abstract:
            return None
        
        # Generate unique URI
        uri = article.get('uri', f"nyt://article/{uuid.uuid4()}")
        url = article.get('web_url', '') or article.get('url', '')
        
        # Parse publication date
        pub_date = article.get('pub_date', '') or article.get('published_date', '')
        published = None
        if pub_date:
            try:
                published = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Extract authors
        byline = article.get('byline', {}).get('original', '') if isinstance(article.get('byline'), dict) else str(article.get('byline', ''))
        authors = self._parse_byline(byline)
        
        # Extract topics/keywords
        topics = []
        if 'keywords' in article:
            topics.extend([kw.get('value', '') for kw in article['keywords'] if kw.get('value')])
        if 'des_facet' in article:
            topics.extend(article['des_facet'])
        if 'subject' in article:
            topics.append(article['subject'])
        
        # Extract organizations
        organizations = []
        if 'keywords' in article:
            organizations.extend([kw.get('value', '') for kw in article['keywords'] 
                                if kw.get('name') == 'organizations' and kw.get('value')])
        if 'org_facet' in article:
            organizations.extend(article['org_facet'])
        
        # Extract persons
        persons = []
        if 'keywords' in article:
            persons.extend([kw.get('value', '') for kw in article['keywords'] 
                          if kw.get('name') == 'persons' and kw.get('value')])
        if 'per_facet' in article:
            persons.extend(article['per_facet'])
        
        # Extract locations
        locations = []
        if 'keywords' in article:
            locations.extend([kw.get('value', '') for kw in article['keywords'] 
                            if kw.get('name') in ['glocations', 'locations'] and kw.get('value')])
        if 'geo_facet' in article:
            locations.extend(article['geo_facet'])
        
        # Extract images
        images = []
        if 'multimedia' in article:
            for media in article['multimedia']:
                if media.get('type') == 'image' or media.get('format'):
                    images.append({
                        'url': media.get('url', ''),
                        'caption': media.get('caption', '')
                    })
        
        return {
            'article': {
                'uri': uri,
                'title': title,
                'abstract': abstract,
                'published': published,
                'url': url
            },
            'authors': list(set(authors)),
            'topics': list(set(topics)),
            'organizations': list(set(organizations)),
            'persons': list(set(persons)),
            'locations': list(set(locations)),
            'images': images
        }
    
    def _import_batch_to_neo4j(self, batch: List[Dict[str, Any]]):
        """Import a batch of processed articles to Neo4j"""
        with self.driver.session(database=self.database) as session:
            # Create articles and their relationships
            for item in batch:
                try:
                    self._create_article_and_relationships(session, item)
                except Exception as e:
                    print(f"❌ Error importing article {item['article']['uri']}: {e}")
    
    def _create_article_and_relationships(self, session, item: Dict[str, Any]):
        """Create article node and all its relationships"""
        article = item['article']
        
        # Create article node
        article_query = """
        MERGE (a:Article {uri: $uri})
        SET a.title = $title,
            a.abstract = $abstract,
            a.published = $published,
            a.url = $url
        RETURN a
        """
        
        session.run(article_query, 
                   uri=article['uri'],
                   title=article['title'],
                   abstract=article['abstract'],
                   published=article['published'],
                   url=article['url'])
        
        # Create authors and relationships
        for author_name in item['authors']:
            if author_name:
                author_query = """
                MATCH (a:Article {uri: $uri})
                MERGE (author:Author {name: $name})
                MERGE (a)-[:WRITTEN_BY]->(author)
                """
                session.run(author_query, uri=article['uri'], name=author_name)
        
        # Create topics and relationships
        for topic_name in item['topics']:
            if topic_name:
                topic_query = """
                MATCH (a:Article {uri: $uri})
                MERGE (t:Topic {name: $name})
                MERGE (a)-[:HAS_TOPIC]->(t)
                """
                session.run(topic_query, uri=article['uri'], name=topic_name)
        
        # Create organizations and relationships
        for org_name in item['organizations']:
            if org_name:
                org_query = """
                MATCH (a:Article {uri: $uri})
                MERGE (o:Organization {name: $name})
                MERGE (a)-[:MENTIONS_ORGANIZATION]->(o)
                """
                session.run(org_query, uri=article['uri'], name=org_name)
        
        # Create persons and relationships
        for person_name in item['persons']:
            if person_name:
                person_query = """
                MATCH (a:Article {uri: $uri})
                MERGE (p:Person {name: $name})
                MERGE (a)-[:MENTIONS_PERSON]->(p)
                """
                session.run(person_query, uri=article['uri'], name=person_name)
        
        # Create locations and relationships
        for location_name in item['locations']:
            if location_name:
                # Try to geocode the location
                coordinates = self._geocode_location(location_name)
                
                if coordinates:
                    geo_query = """
                    MATCH (a:Article {uri: $uri})
                    MERGE (g:Geo {name: $name})
                    SET g.location = point({latitude: $lat, longitude: $lon})
                    MERGE (a)-[:LOCATED_IN]->(g)
                    """
                    session.run(geo_query, 
                               uri=article['uri'], 
                               name=location_name,
                               lat=coordinates['latitude'],
                               lon=coordinates['longitude'])
                else:
                    geo_query = """
                    MATCH (a:Article {uri: $uri})
                    MERGE (g:Geo {name: $name})
                    MERGE (a)-[:LOCATED_IN]->(g)
                    """
                    session.run(geo_query, uri=article['uri'], name=location_name)
        
        # Create images and relationships
        for image in item['images']:
            if image['url']:
                image_query = """
                MATCH (a:Article {uri: $uri})
                MERGE (i:Image {url: $url})
                SET i.caption = $caption
                MERGE (a)-[:HAS_IMAGE]->(i)
                """
                session.run(image_query, 
                           uri=article['uri'], 
                           url=image['url'],
                           caption=image['caption'])
    
    def import_articles(self, data_dir: str = None, limit: int = None):
        """Import articles from JSON files"""
        data_dir = data_dir or self.data_dir
        data_path = Path(data_dir)
        
        if not data_path.exists():
            print(f"❌ Data directory not found: {data_path}")
            return
        
        # Find all JSON files
        json_files = list(data_path.glob("**/*.json"))
        if not json_files:
            print(f"❌ No JSON files found in {data_path}")
            return
        
        print(f"📁 Found {len(json_files)} JSON files in {data_path}")
        
        total_articles = 0
        batch = []
        
        for json_file in tqdm(json_files, desc="Processing files"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different JSON structures
                articles_data = []
                if isinstance(data, list):
                    articles_data = data
                elif 'response' in data and 'docs' in data['response']:
                    articles_data = data['response']['docs']
                elif 'results' in data:
                    articles_data = data['results']
                else:
                    articles_data = [data]
                
                for article_data in articles_data:
                    processed = self._process_article(article_data)
                    if processed:
                        batch.append(processed)
                        total_articles += 1
                        
                        if len(batch) >= self.batch_size:
                            self._import_batch_to_neo4j(batch)
                            batch = []
                        
                        if limit and total_articles >= limit:
                            break
                
                if limit and total_articles >= limit:
                    break
                    
            except Exception as e:
                print(f"❌ Error processing file {json_file}: {e}")
        
        # Import remaining articles in batch
        if batch:
            self._import_batch_to_neo4j(batch)
        
        print(f"✅ Imported {total_articles} articles to Neo4j")
        
        # Print summary statistics
        self._print_import_summary()
    
    def _print_import_summary(self):
        """Print summary statistics of imported data"""
        with self.driver.session(database=self.database) as session:
            # Count nodes
            counts = {}
            labels = ["Article", "Author", "Topic", "Organization", "Person", "Geo", "Image"]
            
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                counts[label] = result.single()["count"]
            
            print(f"\n📊 Import Summary:")
            for label, count in counts.items():
                print(f"  {label}: {count}")
            
            # Count relationships
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()["count"]
            print(f"  Relationships: {rel_count}")
    
    def close(self):
        """Close the Neo4j connection"""
        self.config.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import NYT articles to Neo4j knowledge graph')
    parser.add_argument('--config', default='config.env', help='Configuration file path')
    parser.add_argument('--data-dir', help='Directory containing JSON files')
    parser.add_argument('--limit', type=int, help='Maximum number of articles to import')
    
    args = parser.parse_args()
    
    try:
        # Create importer
        importer = NewsImporterNeo4j(args.config)
        
        # Import articles
        importer.import_articles(args.data_dir, args.limit)
        
        # Close connection
        importer.close()
        
        print("🎉 Import completed successfully!")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()