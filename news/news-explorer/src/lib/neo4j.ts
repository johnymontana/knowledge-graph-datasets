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
  parameters?: Record<string, any>,
  database?: string
): Promise<Record[]> {
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
      LIMIT $limit
    `
    
    const records = await runCypher(query, { limit })
    return records.map(record => record.get('a').properties as Article)
  }

  static async getArticlesByTopic(topicName: string, limit: number = 10): Promise<Article[]> {
    const query = `
      MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic {name: $topicName})
      RETURN a
      ORDER BY a.published DESC
      LIMIT $limit
    `
    
    const records = await runCypher(query, { topicName, limit })
    return records.map(record => record.get('a').properties as Article)
  }

  static async getArticlesWithLocation(limit: number = 50): Promise<{article: Article, geo: Geo}[]> {
    const query = `
      MATCH (a:Article)-[:LOCATED_IN]->(g:Geo)
      WHERE g.location IS NOT NULL
      RETURN a, g
      ORDER BY a.published DESC
      LIMIT $limit
    `
    
    const records = await runCypher(query, { limit })
    return records.map(record => ({
      article: record.get('a').properties as Article,
      geo: {
        name: record.get('g').properties.name,
        location: record.get('g').properties.location
      }
    }))
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
      article: record.get('node').properties as Article,
      score: record.get('score')
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
      topic: record.get('t').properties as Topic,
      count: record.get('articleCount').toNumber()
    }))
  }

  static async getArticleGraph(articleUri: string): Promise<any> {
    const query = `
      MATCH (a:Article {uri: $articleUri})
      OPTIONAL MATCH (a)-[r]->(n)
      RETURN a, collect({relationship: type(r), node: n}) as connections
    `
    
    const records = await runCypher(query, { articleUri })
    if (records.length === 0) return null
    
    return {
      article: records[0].get('a').properties,
      connections: records[0].get('connections')
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
    return records.map(record => record.get('node').properties as Article)
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
      date: record.get('date'),
      count: record.get('count').toNumber()
    }))
  }
}