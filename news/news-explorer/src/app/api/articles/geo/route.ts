import { NextResponse } from 'next/server'
import { NewsQueries } from '@/lib/neo4j'

export async function GET() {
  try {
    const articles = await NewsQueries.getArticlesWithLocation(100)
    return NextResponse.json(articles)
  } catch (error) {
    console.error('Failed to fetch geo articles:', error)
    return NextResponse.json([], { status: 500 })
  }
}