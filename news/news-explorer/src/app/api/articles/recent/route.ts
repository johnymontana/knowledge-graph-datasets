import { NextResponse } from 'next/server'
import { NewsQueries } from '@/lib/neo4j'

export async function GET() {
  try {
    const articles = await NewsQueries.getRecentArticles(50)
    return NextResponse.json(articles)
  } catch (error) {
    console.error('Failed to fetch recent articles:', error)
    return NextResponse.json([], { status: 500 })
  }
}