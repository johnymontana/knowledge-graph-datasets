/* eslint-disable @typescript-eslint/no-explicit-any */
import neo4j, { Driver, Record, Session } from 'neo4j-driver'

// Neo4j connection instance
let driver: Driver | null = null

export interface Neo4jConfig {
  uri: string
  username: string
  password: string
  database?: string
}

export function createNeo4jDriver(config: Neo4jConfig): Driver {
  if (!driver) {
    driver = neo4j.driver(
      config.uri,
      neo4j.auth.basic(config.username, config.password),
      {
        maxConnectionPoolSize: 16,
        connectionTimeout: 30000,
        maxTransactionRetryTime: 30000,
      }
    )
  }
  return driver
}

export function getNeo4jDriver(): Driver {
  if (!driver) {
    const config = {
      uri: process.env.NEO4J_URI || 'bolt://localhost:7687',
      username: process.env.NEO4J_USERNAME || 'neo4j',
      password: process.env.NEO4J_PASSWORD || 'password',
      database: process.env.NEO4J_DATABASE || 'neo4j',
    }
    driver = createNeo4jDriver(config)
  }
  return driver
}

export async function runCypher(
  query: string,
  parameters?: { [key: string]: unknown },
  database?: string
): Promise<unknown[]> {
  const session: Session = getNeo4jDriver().session({
    database: database || process.env.NEO4J_DATABASE || 'neo4j',
  })

  try {
    const result = await session.run(query, parameters)
    return result.records
  } finally {
    await session.close()
  }
}

export async function closeDatabaseConnection(): Promise<void> {
  if (driver) {
    await driver.close()
    driver = null
  }
}

// Types for the news data model
export interface Article {
  uri: string
  title: string
  abstract: string
  published: string
  url: string
  embedding?: number[]
  section?: string
  subsection?: string
  byline?: string
}

export interface Topic {
  name: string
}

export interface Organization {
  name: string
}

export interface Person {
  name: string
}

export interface Author {
  name: string
}

export interface Geo {
  name: string
  location?: {
    latitude: number
    longitude: number
  }
}

export interface Image {
  url: string
  caption?: string
}

// Common queries for the news dataset
export class NewsQueries {
  static async getRecentArticles(limit: number = 20): Promise<Article[]> {
    const query = `
      MATCH (a:Article)
      RETURN a
      ORDER BY a.published DESC
      LIMIT toInteger($limit)
    `
    
    const records = await runCypher(query, { limit })
    return records.map(record => (record as any).get('a').properties as Article)
  }

  static async getArticlesByTopic(topicName: string, limit: number = 10): Promise<Article[]> {
    const query = `
      MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic {name: $topicName})
      RETURN a
      ORDER BY a.published DESC
      LIMIT $limit
    `
    
    const records = await runCypher(query, { topicName, limit })
    return records.map(record => (record as any).get('a').properties as Article)
  }

  static async getArticlesWithLocation(limit: number = 50): Promise<{article: Article, geo: Geo}[]> {
    const query = `
      MATCH (a:Article)-[:LOCATED_IN]->(g:Geo)
      WHERE g.location IS NOT NULL
      RETURN a, g, 
             g.location.longitude as longitude, 
             g.location.latitude as latitude,
             toString(a.published) as published_str
      ORDER BY a.published DESC
      LIMIT toInteger($limit)
    `
    
    const records = await runCypher(query, { limit })
    console.log('Raw Neo4j records:', records)
    
    return records.map(record => {
      const longitude = (record as any).get('longitude')
      const latitude = (record as any).get('latitude')
      const publishedStr = (record as any).get('published_str')
      
      // Debug: Log the extracted coordinates and record structure
      console.log('Record structure:', record)
      console.log('Extracted coordinates:', { longitude, latitude, type: typeof longitude })
      console.log('Published string:', publishedStr)
      console.log('Article properties:', (record as any).get('a').properties)
      console.log('Geo properties:', (record as any).get('g').properties)
      
      // Ensure coordinates are valid numbers
      if (typeof longitude === 'number' && typeof latitude === 'number' && 
          !isNaN(longitude) && !isNaN(latitude) &&
          longitude >= -180 && longitude <= 180 && 
          latitude >= -90 && latitude <= 90) {
        
        // Create article with properly formatted published date
        const articleProps = (record as any).get('a').properties
        const article: Article = {
          ...articleProps,
          published: publishedStr || articleProps.published
        }
        
        return {
          article,
          geo: {
            name: (record as any).get('g').properties.name,
            location: { longitude, latitude }
          }
        }
      } else {
        console.warn(`Invalid coordinates extracted:`, { longitude, latitude })
        return null
      }
    }).filter(item => item !== null) as {article: Article, geo: Geo}[]
  }

  static async vectorSearch(queryVector: number[], limit: number = 10): Promise<{article: Article, score: number}[]> {
    const query = `
      CALL db.index.vector.queryNodes('article_embeddings', $limit, $queryVector)
      YIELD node, score
      RETURN node, score
      ORDER BY score DESC
    `
    
    const records = await runCypher(query, { queryVector, limit })
    return records.map(record => ({
      article: (record as any).get('node').properties as Article,
      score: (record as any).get('score')
    }))
  }

  static async getTopics(limit: number = 20): Promise<{topic: Topic, count: number}[]> {
    const query = `
      MATCH (t:Topic)<-[:HAS_TOPIC]-(a:Article)
      RETURN t, count(a) as articleCount
      ORDER BY articleCount DESC
      LIMIT $limit
    `
    
    const records = await runCypher(query, { limit })
    return records.map(record => ({
      topic: (record as any).get('t').properties as Topic,
      count: (record as any).get('articleCount').toNumber()
    }))
  }

  static async getArticleGraph(articleUri: string): Promise<{article: { [key: string]: unknown }, connections: unknown[]} | null> {
    const query = `
      MATCH (a:Article {uri: $articleUri})
      OPTIONAL MATCH (a)-[r]->(n)
      RETURN a, collect({relationship: type(r), node: n}) as connections
    `
    
    const records = await runCypher(query, { articleUri })
    if (records.length === 0) return null
    
    return {
      article: (records[0] as any).get('a').properties,
      connections: (records[0] as any).get('connections')
    }
  }

  static async searchArticles(searchTerm: string, limit: number = 20): Promise<Article[]> {
    const query = `
      CALL db.index.fulltext.queryNodes('article_text', $searchTerm)
      YIELD node, score
      RETURN node
      ORDER BY score DESC
      LIMIT $limit
    `
    
    const records = await runCypher(query, { searchTerm, limit })
    return records.map(record => (record as any).get('node').properties as Article)
  }

  static async getTimelineData(): Promise<{date: string, count: number}[]> {
    const query = `
      MATCH (a:Article)
      WHERE a.published IS NOT NULL
      WITH date(a.published) as publishedDate
      RETURN publishedDate.year + '-' + 
             lpad(publishedDate.month, 2, '0') + '-' +
             lpad(publishedDate.day, 2, '0') as date,
             count(*) as count
      ORDER BY date DESC
      LIMIT 365
    `
    
    const records = await runCypher(query)
    return records.map(record => ({
      date: (record as any).get('date'),
      count: (record as any).get('count').toNumber()
    }))
  }

  static async getOverviewGraph(): Promise<{
    article: number
    topic: number
    person: number
    organization: number
    geo: number
    author: number
    sampleArticles: Article[]
    sampleTopics: Topic[]
    samplePeople: Person[]
    sampleOrganizations: Organization[]
    sampleLocations: Geo[]
    sampleAuthors: Author[]
  } | null> {
    try {
      // Get counts for each entity type
      const countsQuery = `
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY label
      `
      
      const countsRecords = await runCypher(countsQuery)
      const counts: { [key: string]: number } = {}
      
      countsRecords.forEach(record => {
        const label = (record as any).get('label')
        const count = (record as any).get('count').toNumber()
        counts[label.toLowerCase()] = count
      })
      
      // Get sample entities of each type
      const sampleArticles = await this.getRecentArticles(5)
      
      const topicsQuery = `
        MATCH (t:Topic)
        RETURN t
        ORDER BY rand()
        LIMIT 5
      `
      const topicRecords = await runCypher(topicsQuery)
      const sampleTopics = topicRecords.map(record => (record as any).get('t').properties as Topic)
      
      const peopleQuery = `
        MATCH (p:Person)
        RETURN p
        ORDER BY rand()
        LIMIT 5
      `
      const peopleRecords = await runCypher(peopleQuery)
      const samplePeople = peopleRecords.map(record => (record as any).get('p').properties as Person)
      
      const orgsQuery = `
        MATCH (o:Organization)
        RETURN o
        ORDER BY rand()
        LIMIT 5
      `
      const orgRecords = await runCypher(orgsQuery)
      const sampleOrganizations = orgRecords.map(record => (record as any).get('o').properties as Organization)
      
      const locationsQuery = `
        MATCH (g:Geo)
        WHERE g.location IS NOT NULL
        RETURN g
        ORDER BY rand()
        LIMIT 5
      `
      const locationRecords = await runCypher(locationsQuery)
      const sampleLocations = locationRecords.map(record => (record as any).get('g').properties as Geo)
      
      const authorsQuery = `
        MATCH (a:Author)
        RETURN a
        ORDER BY rand()
        LIMIT 5
      `
      const authorRecords = await runCypher(authorsQuery)
      const sampleAuthors = authorRecords.map(record => (record as any).get('a').properties as Author)
      
      return {
        article: counts.article || 0,
        topic: counts.topic || 0,
        person: counts.person || 0,
        organization: counts.organization || 0,
        geo: counts.geo || 0,
        author: counts.author || 0,
        sampleArticles,
        sampleTopics,
        samplePeople,
        sampleOrganizations,
        sampleLocations,
        sampleAuthors
      }
    } catch (error) {
      console.error('Failed to get overview graph data:', error)
      return null
    }
  }
}