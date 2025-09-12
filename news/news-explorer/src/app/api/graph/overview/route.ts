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

export async function GET() {
  try {
    // Get overview data from Neo4j
    const overviewData = await NewsQueries.getOverviewGraph()
    
    if (!overviewData) {
      return NextResponse.json({ nodes: [], edges: [] })
    }

    // Transform the data into the format expected by the graph component
    const nodes: GraphNode[] = []
    const edges: GraphEdge[] = []

    // Add entity type nodes
    const entityTypes = [
      { type: 'article', label: 'Articles', color: '#3182ce', size: 20 },
      { type: 'topic', label: 'Topics', color: '#38a169', size: 15 },
      { type: 'person', label: 'People', color: '#d69e2e', size: 12 },
      { type: 'organization', label: 'Organizations', color: '#9f7aea', size: 12 },
      { type: 'geo', label: 'Locations', color: '#e53e3e', size: 10 },
      { type: 'author', label: 'Authors', color: '#00b5d8', size: 8 }
    ]

    entityTypes.forEach((entity, index) => {
      nodes.push({
        id: entity.type,
        label: entity.label,
        type: entity.type,
        size: entity.size,
        color: entity.color,
        data: { count: overviewData[entity.type] || 0 }
      })
    })

    // Add sample entities of each type
    if (overviewData.sampleArticles) {
      overviewData.sampleArticles.forEach((article: any, index: number) => {
        const nodeId = `article-${index}`
        nodes.push({
          id: nodeId,
          label: article.title?.substring(0, 30) + '...' || 'Article',
          type: 'article',
          size: 15,
          color: '#3182ce',
          data: article
        })
        
        edges.push({
          id: `edge-article-${index}`,
          source: 'article',
          target: nodeId,
          type: 'INSTANCE_OF',
          color: '#e2e8f0'
        })
      })
    }

    if (overviewData.sampleTopics) {
      overviewData.sampleTopics.forEach((topic: any, index: number) => {
        const nodeId = `topic-${index}`
        nodes.push({
          id: nodeId,
          label: topic.name || 'Topic',
          type: 'topic',
          size: 12,
          color: '#38a169',
          data: topic
        })
        
        edges.push({
          id: `edge-topic-${index}`,
          source: 'topic',
          target: nodeId,
          type: 'INSTANCE_OF',
          color: '#e2e8f0'
        })
      })
    }

    if (overviewData.samplePeople) {
      overviewData.samplePeople.forEach((person: any, index: number) => {
        const nodeId = `person-${index}`
        nodes.push({
          id: nodeId,
          label: person.name || 'Person',
          type: 'person',
          size: 10,
          color: '#d69e2e',
          data: person
        })
        
        edges.push({
          id: `edge-person-${index}`,
          source: 'person',
          target: nodeId,
          type: 'INSTANCE_OF',
          color: '#e2e8f0'
        })
      })
    }

    if (overviewData.sampleOrganizations) {
      overviewData.sampleOrganizations.forEach((org: any, index: number) => {
        const nodeId = `org-${index}`
        nodes.push({
          id: nodeId,
          label: org.name || 'Organization',
          type: 'organization',
          size: 10,
          color: '#9f7aea',
          data: org
        })
        
        edges.push({
          id: `edge-org-${index}`,
          source: 'organization',
          target: nodeId,
          type: 'INSTANCE_OF',
          color: '#e2e8f0'
        })
      })
    }

    if (overviewData.sampleLocations) {
      overviewData.sampleLocations.forEach((location: any, index: number) => {
        const nodeId = `location-${index}`
        nodes.push({
          id: nodeId,
          label: location.name || 'Location',
          type: 'geo',
          size: 8,
          color: '#e53e3e',
          data: location
        })
        
        edges.push({
          id: `edge-location-${index}`,
          source: 'geo',
          target: nodeId,
          type: 'INSTANCE_OF',
          color: '#e2e8f0'
        })
      })
    }

    if (overviewData.sampleAuthors) {
      overviewData.sampleAuthors.forEach((author: any, index: number) => {
        const nodeId = `author-${index}`
        nodes.push({
          id: nodeId,
          label: author.name || 'Author',
          type: 'author',
          size: 6,
          color: '#00b5d8',
          data: author
        })
        
        edges.push({
          id: `edge-author-${index}`,
          source: 'author',
          target: nodeId,
          type: 'INSTANCE_OF',
          color: '#e2e8f0'
        })
      })
    }

    return NextResponse.json({ nodes, edges })
  } catch (error) {
    console.error('Failed to fetch overview graph:', error)
    return NextResponse.json({ nodes: [], edges: [] }, { status: 500 })
  }
}

