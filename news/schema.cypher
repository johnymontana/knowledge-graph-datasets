// News Knowledge Graph Schema for Neo4j
// This file defines constraints, indexes, and initial setup for the news graph

// Create constraints and indexes for Articles
CREATE CONSTRAINT article_uri IF NOT EXISTS FOR (a:Article) REQUIRE a.uri IS UNIQUE;
CREATE INDEX article_title IF NOT EXISTS FOR (a:Article) ON (a.title);
CREATE INDEX article_published IF NOT EXISTS FOR (a:Article) ON (a.published);
CREATE FULLTEXT INDEX article_text IF NOT EXISTS FOR (a:Article) ON EACH [a.title, a.abstract];

// Create constraints and indexes for Topics
CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE;

// Create constraints and indexes for Organizations
CREATE CONSTRAINT organization_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE;

// Create constraints and indexes for Persons
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;

// Create constraints and indexes for Authors
CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE;

// Create constraints and indexes for Geo locations
CREATE CONSTRAINT geo_name IF NOT EXISTS FOR (g:Geo) REQUIRE g.name IS UNIQUE;
CREATE INDEX geo_location IF NOT EXISTS FOR (g:Geo) ON (g.location);

// Create constraints and indexes for Images
CREATE INDEX image_url IF NOT EXISTS FOR (i:Image) ON (i.url);

// Create vector index for article embeddings (requires Neo4j 5.11+)
// This creates a vector index for semantic similarity search
CREATE VECTOR INDEX article_embeddings IF NOT EXISTS
FOR (a:Article) ON (a.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }
};

// Example graph structure:
// (:Article)-[:HAS_TOPIC]->(:Topic)
// (:Article)-[:MENTIONS_ORGANIZATION]->(:Organization)
// (:Article)-[:MENTIONS_PERSON]->(:Person)
// (:Article)-[:WRITTEN_BY]->(:Author)
// (:Article)-[:LOCATED_IN]->(:Geo)
// (:Article)-[:HAS_IMAGE]->(:Image)

// Node labels and their properties:
// 
// Article:
//   - uri (unique identifier)
//   - title (article title)
//   - abstract (article summary)
//   - published (publication date)
//   - url (article URL)
//   - embedding (vector for similarity search)
//
// Topic:
//   - name (topic name)
//
// Organization:
//   - name (organization name)
//
// Person:
//   - name (person name)
//
// Author:
//   - name (author name)
//
// Geo:
//   - name (location name)
//   - location (point geometry for spatial queries)
//
// Image:
//   - url (image URL)
//   - caption (image description)

// Relationship types:
// - HAS_TOPIC: Article to Topic
// - MENTIONS_ORGANIZATION: Article to Organization
// - MENTIONS_PERSON: Article to Person
// - WRITTEN_BY: Article to Author
// - LOCATED_IN: Article to Geo
// - HAS_IMAGE: Article to Image