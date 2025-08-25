import { NextResponse } from 'next/server'
import { NewsQueries } from '@/lib/neo4j'

interface GraphNode {
  id: string
  label: string
  type: string
  size: number
  color: string
  data: Record<string, unknown>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  color: string
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ uri: string }> }
) {
  try {
    const { uri } = await params
    const articleUri = decodeURIComponent(uri)
    const graphData = await NewsQueries.getArticleGraph(articleUri)
    
    if (!graphData) {
      return NextResponse.json({ nodes: [], edges: [] })
    }

    // Transform the graph data into the format expected by the graph component
    const nodes: GraphNode[] = []
    const edges: GraphEdge[] = []

    // Add the central article node
    const article = graphData.article as unknown as Record<string, unknown>
    nodes.push({
      id: (article.uri as string) || articleUri,
      label: (article.title as string) || 'Article',
      type: 'article',
      size: 20,
      color: '#3182ce',
      data: article
    })

    // Add connected nodes and edges
    const connections = graphData.connections as Array<Record<string, unknown>>
    connections.forEach((connection, index) => {
      const nodeId = `${connection.relationship}-${index}`
      let nodeType = 'topic'
      let color = '#38a169'
      
      // Determine node type and color based on relationship
      switch (connection.relationship as string) {
        case 'HAS_TOPIC':
          nodeType = 'topic'
          color = '#38a169'
          break
        case 'MENTIONS_PERSON':
          nodeType = 'person'
          color = '#d69e2e'
          break
        case 'MENTIONS_ORGANIZATION':
          nodeType = 'organization'
          color = '#9f7aea'
          break
        case 'LOCATED_IN':
          nodeType = 'geo'
          color = '#e53e3e'
          break
        case 'WRITTEN_BY':
          nodeType = 'author'
          color = '#00b5d8'
          break
      }

      const node = connection.node as Record<string, unknown>
      const properties = node.properties as Record<string, unknown>
      
      nodes.push({
        id: nodeId,
        label: (properties?.name as string) || (properties?.title as string) || 'Unknown',
        type: nodeType,
        size: 15,
        color,
        data: properties
      })

      edges.push({
        id: `edge-${index}`,
        source: (article.uri as string) || articleUri,
        target: nodeId,
        type: connection.relationship as string,
        color: '#e2e8f0'
      })
    })

    return NextResponse.json({ nodes, edges })
  } catch (error) {
    console.error('Failed to fetch article graph:', error)
    return NextResponse.json({ nodes: [], edges: [] }, { status: 500 })
  }
}