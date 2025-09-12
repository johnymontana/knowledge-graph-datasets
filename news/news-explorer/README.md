# News Explorer - Knowledge Graph Dashboard

An interactive Next.js application for exploring and analyzing news data stored in Neo4j. Features geospatial visualizations, graph exploration, and AI-powered chat interface.

## 🚀 Features

- **Interactive Dashboard**: Overview with key statistics and recent articles
- **Geospatial Map View**: Visualize news articles by geographic location using MapLibre
- **Knowledge Graph Visualization**: Explore article connections and relationships using custom graph visualization
- **AI Chat Interface**: Ask questions about the news dataset using Vercel AI SDK
- **Full-text Search**: Search through articles by content
- **Responsive Design**: Built with Chakra UI for modern, accessible interface

## 🏗️ Architecture

Built on the news dataset Neo4j schema:
- **Articles**: News articles with title, abstract, published date, section
- **Topics**: Article topics and themes
- **People**: Individuals mentioned in articles
- **Organizations**: Organizations mentioned in articles
- **Locations**: Geographic locations (with coordinates for mapping)
- **Authors**: Article authors
- **Images**: Associated media

## 📋 Prerequisites

- Node.js 18+
- Neo4j database with news dataset loaded
- OpenAI or Anthropic API key (for AI chat)

## 🛠️ Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   Update `.env.local` with your configuration:
   ```bash
   # Neo4j Configuration
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   NEO4J_DATABASE=neo4j

   # AI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**: [http://localhost:3000](http://localhost:3000)

## 🎯 Usage

### Dashboard Overview
- View key statistics about the news dataset
- Browse recent articles
- Access different visualization modes

### Map View
- Explore geographic distribution of news articles
- Click on markers to see article details
- Interactive popups with article information

### Graph View  
- Select an article to visualize its connections
- See relationships to topics, people, organizations, locations
- Interactive node-link diagram with force-directed layout

### AI Assistant
- Ask natural language questions about the news data
- Get insights about articles, topics, and trends
- Context-aware responses based on the Neo4j dataset

### Search
- Full-text search across article titles and abstracts
- Real-time search results
- Filter and explore search results

## 🔧 Development

### Project Structure
```
src/
├── app/
│   ├── api/                    # API routes
│   │   ├── articles/          # Article endpoints
│   │   ├── chat/              # AI chat endpoint
│   │   ├── search/            # Search endpoint
│   │   └── stats/             # Statistics endpoint
│   ├── page.tsx               # Main dashboard
│   └── layout.tsx             # App layout
├── components/
│   ├── NewsMap.tsx            # MapLibre map component
│   ├── NewsGraph.tsx          # Graph visualization
│   └── NewsChat.tsx           # AI chat interface
└── lib/
    └── neo4j.ts               # Neo4j connection & queries
```

### Key Components

#### NewsMap
- Interactive map showing geolocated articles
- Uses MapLibre GL for rendering
- Custom markers and popups

#### NewsGraph  
- Custom graph visualization
- Force-directed layout algorithm
- Interactive node selection

#### NewsChat
- AI-powered chat interface
- Integrates with Vercel AI SDK
- Context-aware responses about the dataset

### API Endpoints

- `GET /api/articles/recent` - Recent articles
- `GET /api/articles/geo` - Articles with locations  
- `GET /api/articles/[uri]/graph` - Article graph data
- `GET /api/stats` - Dashboard statistics
- `GET /api/search?q=term` - Search articles
- `POST /api/chat` - AI chat interface

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm run build
vercel deploy
```

### Environment Variables for Production
- Set all Neo4j connection details
- Add production API keys
- Configure any additional environment-specific settings

## 🔍 Troubleshooting

### Neo4j Connection Issues
- Verify Neo4j is running and accessible
- Check connection credentials
- Ensure database contains the expected schema

### Map Not Loading
- Verify MapLibre dependencies are installed
- Check for JavaScript console errors
- Ensure geospatial data exists in database

### AI Chat Not Working  
- Verify API keys are set correctly
- Check API rate limits and quotas
- Review chat API logs for errors

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Chakra UI Documentation](https://chakra-ui.com/docs)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [MapLibre GL Documentation](https://maplibre.org/maplibre-gl-js-docs/)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)

---

**Explore news data like never before! 🚀📰**
