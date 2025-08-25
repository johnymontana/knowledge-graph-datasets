import { openai } from '@ai-sdk/openai'
import { anthropic } from '@ai-sdk/anthropic'
import { streamText } from 'ai'
import { NewsQueries, runCypher } from '@/lib/neo4j'

export const runtime = 'edge'

export async function POST(req: Request) {
  const { messages } = await req.json()
  const lastMessage = messages[messages.length - 1].content

  try {
    // Determine if the query is about news data and extract relevant information
    const systemPrompt = `You are a helpful assistant that can answer questions about a news dataset stored in Neo4j. 

The dataset contains:
- Articles with properties: title, abstract, published date, section, byline, url
- Topics connected to articles
- People mentioned in articles
- Organizations mentioned in articles  
- Geographic locations where articles take place
- Authors who wrote articles
- Images associated with articles

When users ask about the news data, you should:
1. Understand their question and determine if it requires querying the database
2. If it does, generate appropriate Cypher queries to get the needed information
3. Present the results in a helpful, conversational way

If the user asks about specific articles, topics, people, or locations, you should query the database to provide accurate, current information.

Example queries you can make:
- Get recent articles: MATCH (a:Article) RETURN a ORDER BY a.published DESC LIMIT 10
- Find articles by topic: MATCH (a:Article)-[:HAS_TOPIC]->(t:Topic {name: 'Technology'}) RETURN a
- Get articles about a person: MATCH (a:Article)-[:MENTIONS_PERSON]->(p:Person {name: 'Joe Biden'}) RETURN a
- Find articles in a location: MATCH (a:Article)-[:LOCATED_IN]->(g:Geo {name: 'New York'}) RETURN a

Current user question: "${lastMessage}"`

    // Check if this looks like a news data query
    const isNewsQuery = /\b(article|news|topic|person|organization|location|recent|search|find|show|when|where|who|what)\b/i.test(lastMessage)

    let contextData = ''
    
    if (isNewsQuery) {
      try {
        // Try to get some relevant data based on the query
        if (/recent|latest|new/i.test(lastMessage)) {
          const recentArticles = await NewsQueries.getRecentArticles(5)
          contextData = `Recent articles: ${JSON.stringify(recentArticles.map(a => ({
            title: a.title,
            published: a.published,
            section: a.section
          })))}`
        } else if (/topic/i.test(lastMessage)) {
          const topics = await NewsQueries.getTopics(10)
          contextData = `Popular topics: ${JSON.stringify(topics.map(t => ({
            topic: t.topic.name,
            articleCount: t.count
          })))}`
        } else if (/location|geography|geo/i.test(lastMessage)) {
          const geoArticles = await NewsQueries.getArticlesWithLocation(5)
          contextData = `Articles with locations: ${JSON.stringify(geoArticles.map(a => ({
            title: a.article.title,
            location: a.geo.name
          })))}`
        } else if (/search|find/i.test(lastMessage)) {
          // Extract search terms from the message
          const searchMatch = lastMessage.match(/search|find.+?["']([^"']+)["']|search|find\s+(.+?)(?:\s|$)/i)
          if (searchMatch) {
            const searchTerm = searchMatch[1] || searchMatch[2]
            if (searchTerm) {
              const searchResults = await NewsQueries.searchArticles(searchTerm, 3)
              contextData = `Search results for "${searchTerm}": ${JSON.stringify(searchResults.map(a => ({
                title: a.title,
                abstract: a.abstract?.substring(0, 100) + '...'
              })))}`
            }
          }
        }
      } catch (error) {
        contextData = 'Note: Database query failed, providing general response without current data.'
      }
    }

    // Choose AI provider based on environment
    const aiProvider = process.env.OPENAI_API_KEY ? 
      openai('gpt-4o-mini') : 
      anthropic('claude-3-haiku-20240307')

    const result = await streamText({
      model: aiProvider,
      messages: [
        {
          role: 'system',
          content: systemPrompt + (contextData ? `\n\nRelevant data from the database: ${contextData}` : '')
        },
        ...messages,
      ],
    })

    return result.toDataStreamResponse()
  } catch (error) {
    console.error('Chat API error:', error)
    return new Response('An error occurred while processing your request.', {
      status: 500,
    })
  }
}