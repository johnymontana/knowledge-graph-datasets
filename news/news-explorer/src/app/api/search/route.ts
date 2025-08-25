import { NextResponse } from 'next/server'
import { NewsQueries } from '@/lib/neo4j'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const query = searchParams.get('q')
    
    if (!query || query.trim().length === 0) {
      return NextResponse.json([])
    }

    const articles = await NewsQueries.searchArticles(query.trim(), 20)
    return NextResponse.json(articles)
  } catch (error) {
    console.error('Search failed:', error)
    return NextResponse.json([], { status: 500 })
  }
}