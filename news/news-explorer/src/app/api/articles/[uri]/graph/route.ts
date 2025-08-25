import { NextResponse } from 'next/server'
import { NewsQueries } from '@/lib/neo4j'

export async function GET(
  request: Request,
  { params }: { params: { uri: string } }
) {
  try {
    const articleUri = decodeURIComponent(params.uri)
    const graphData = await NewsQueries.getArticleGraph(articleUri)
    
    if (!graphData) {
      return NextResponse.json({ nodes: [], edges: [] })
    }

    // Transform the graph data into the format expected by the graph component
    const nodes = []
    const edges = []

    // Add the central article node
    nodes.push({
      id: graphData.article.uri,
      label: graphData.article.title || 'Article',
      type: 'article',
      size: 20,
      color: '#3182ce',
      data: graphData.article
    })

    // Add connected nodes and edges
    graphData.connections.forEach((connection: any, index: number) => {
      const nodeId = `${connection.relationship}-${index}`
      let nodeType = 'topic'
      let color = '#38a169'
      
      // Determine node type and color based on relationship
      switch (connection.relationship) {
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

      nodes.push({
        id: nodeId,
        label: connection.node.properties?.name || connection.node.properties?.title || 'Unknown',
        type: nodeType,
        size: 15,
        color,
        data: connection.node.properties
      })

      edges.push({
        id: `edge-${index}`,
        source: graphData.article.uri,
        target: nodeId,
        type: connection.relationship,
        color: '#e2e8f0'
      })
    })

    return NextResponse.json({ nodes, edges })
  } catch (error) {
    console.error('Failed to fetch article graph:', error)
    return NextResponse.json({ nodes: [], edges: [] }, { status: 500 })
  }
}