import { NextResponse } from 'next/server'
import { runCypher } from '@/lib/neo4j'

export async function GET() {
  try {
    // Get total articles
    const totalArticlesQuery = 'MATCH (a:Article) RETURN count(a) as count'
    const totalArticlesResult = await runCypher(totalArticlesQuery)
    const totalArticles = totalArticlesResult[0]?.get('count')?.toNumber() || 0

    // Get total topics
    const totalTopicsQuery = 'MATCH (t:Topic) RETURN count(t) as count'
    const totalTopicsResult = await runCypher(totalTopicsQuery)
    const totalTopics = totalTopicsResult[0]?.get('count')?.toNumber() || 0

    // Get articles with location
    const articlesWithLocationQuery = `
      MATCH (a:Article)-[:LOCATED_IN]->(g:Geo)
      WHERE g.location IS NOT NULL
      RETURN count(DISTINCT a) as count
    `
    const articlesWithLocationResult = await runCypher(articlesWithLocationQuery)
    const articlesWithLocation = articlesWithLocationResult[0]?.get('count')?.toNumber() || 0

    // Get recent articles (last 30 days)
    const recentArticlesQuery = `
      MATCH (a:Article)
      WHERE a.published IS NOT NULL 
        AND date(a.published) >= date() - duration('P30D')
      RETURN count(a) as count
    `
    const recentArticlesResult = await runCypher(recentArticlesQuery)
    const recentArticles = recentArticlesResult[0]?.get('count')?.toNumber() || 0

    return NextResponse.json({
      totalArticles,
      totalTopics,
      articlesWithLocation,
      recentArticles
    })
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    return NextResponse.json({
      totalArticles: 0,
      totalTopics: 0,
      articlesWithLocation: 0,
      recentArticles: 0
    }, { status: 500 })
  }
}