'use client'

import { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Grid,
  GridItem,
  VStack,
  HStack,
  Text,
  Card,
  CardHeader,
  CardBody,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Button,
  Badge,
  Alert,

  Spinner,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
} from '@chakra-ui/react'
import { Search, Map, MessageSquare, BarChart3, Globe, Calendar, Users, FileText } from 'lucide-react'
import NewsMap from '@/components/NewsMap'
import NewsGraph from '@/components/NewsGraph'
import NewsChat from '@/components/NewsChat'
import { Article, Geo, NewsQueries } from '@/lib/neo4j'

interface DashboardStats {
  totalArticles: number
  totalTopics: number
  articlesWithLocation: number
  recentArticles: number
}

export default function HomePage() {
  const [mounted, setMounted] = useState(false)
  const [articles, setArticles] = useState<Array<{ article: Article; geo: Geo }>>([])
  const [recentArticles, setRecentArticles] = useState<Article[]>([])
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [graphData, setGraphData] = useState<any>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<DashboardStats>({
    totalArticles: 0,
    totalTopics: 0,
    articlesWithLocation: 0,
    recentArticles: 0,
  })
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedView, setSelectedView] = useState<'overview' | 'map' | 'graph' | 'chat'>('overview')

  // Set mounted state to prevent hydration issues
  useEffect(() => {
    setMounted(true)
  }, [])

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Load articles with geolocation for the map
        const geoArticles = await fetch('/api/articles/geo').then(res => res.json())
        setArticles(geoArticles || [])

        // Load recent articles
        const recent = await fetch('/api/articles/recent').then(res => res.json())
        setRecentArticles(recent || [])

        // Load dashboard stats
        const statsResponse = await fetch('/api/stats').then(res => res.json())
        setStats(statsResponse || stats)

        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Load graph data when article is selected
  useEffect(() => {
    if (selectedArticle) {
      const loadGraphData = async () => {
        try {
          const response = await fetch(`/api/articles/${encodeURIComponent(selectedArticle.uri)}/graph`)
          const data = await response.json()
          setGraphData(data || { nodes: [], edges: [] })
        } catch (err) {
          console.error('Failed to load graph data:', err)
          setGraphData({ nodes: [], edges: [] })
        }
      }
      loadGraphData()
    }
  }, [selectedArticle])

  const handleSearch = async (term: string) => {
    if (!term.trim()) {
      return
    }
    
    try {
      const results = await fetch(`/api/search?q=${encodeURIComponent(term)}`).then(res => res.json())
      setRecentArticles(results || [])
    } catch (err) {
      console.error('Search failed:', err)
    }
  }

  // Prevent hydration issues by not rendering until mounted
  if (!mounted) {
    return (
      <Box height="100vh" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={4}>
          <Spinner size="xl" color="blue.500" />
          <Text>Initializing...</Text>
        </VStack>
      </Box>
    )
  }

  if (loading) {
    return (
      <Box height="100vh" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={4}>
          <Spinner size="xl" color="blue.500" />
          <Text>Loading news data...</Text>
        </VStack>
      </Box>
    )
  }

  if (error) {
    return (
      <Container maxW="container.xl" py={8}>
        <Alert.Root status="error">
          <Alert.Indicator />
          <Alert.Content>
            <VStack align="start">
            <Text fontWeight="bold">Error loading data</Text>
            <Text fontSize="sm">{error}</Text>
            <Button size="sm" onClick={() => window.location.reload()}>
              Retry
            </Button>
            </VStack>
          </Alert.Content>
        </Alert.Root>
      </Container>
    )
  }

  return (
    <Box minHeight="100vh" bg="gray.50">
      {/* Header */}
      <Box bg="white" borderBottom="1px solid" borderColor="gray.200" px={6} py={4}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Text fontSize="2xl" fontWeight="bold" color="blue.600">
                News Explorer
              </Text>
              <Text fontSize="sm" color="gray.600">
                Interactive Knowledge Graph Dashboard
              </Text>
            </VStack>

            <HStack spacing={4}>
              <InputGroup size="md" maxW="300px">
                <InputLeftElement>
                  <Search size={16} color="#9ca3af" />
                </InputLeftElement>
                <Input
                  placeholder="Search articles..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch(searchTerm)
                    }
                  }}
                />
              </InputGroup>
              
              <Button
                size="sm"
                colorScheme="blue"
                onClick={() => handleSearch(searchTerm)}
                isDisabled={!searchTerm.trim()}
              >
                Search
              </Button>
            </HStack>
          </HStack>
        </Container>
      </Box>

      {/* Navigation */}
      <Box bg="white" borderBottom="1px solid" borderColor="gray.200" px={6}>
        <Container maxW="container.xl">
          <HStack spacing={8} py={2}>
            <Button
              variant={selectedView === 'overview' ? 'solid' : 'ghost'}
              leftIcon={<BarChart3 size={16} />}
              size="sm"
              colorScheme="blue"
              onClick={() => setSelectedView('overview')}
            >
              Overview
            </Button>
            <Button
              variant={selectedView === 'map' ? 'solid' : 'ghost'}
              leftIcon={<Map size={16} />}
              size="sm"
              colorScheme="blue"
              onClick={() => setSelectedView('map')}
            >
              Map View
            </Button>
            <Button
              variant={selectedView === 'graph' ? 'solid' : 'ghost'}
              leftIcon={<Globe size={16} />}
              size="sm"
              colorScheme="blue"
              onClick={() => setSelectedView('graph')}
            >
              Graph View
            </Button>
            <Button
              variant={selectedView === 'chat' ? 'solid' : 'ghost'}
              leftIcon={<MessageSquare size={16} />}
              size="sm"
              colorScheme="blue"
              onClick={() => setSelectedView('chat')}
            >
              AI Assistant
            </Button>
          </HStack>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="container.xl" py={6}>
        {selectedView === 'overview' && (
          <VStack spacing={6} align="stretch">
            {/* Stats Cards */}
            <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={6}>
              <Card>
                <CardBody>
                          <Stat>
            <StatLabel display="flex" alignItems="center" gap={2}>
              <FileText size={16} />
              Total Articles
            </StatLabel>
            <StatNumber>{stats.totalArticles.toLocaleString()}</StatNumber>
            <StatHelpText>In the knowledge graph</StatHelpText>
          </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel display="flex" alignItems="center" gap={2}>
                      <Users size={16} />
                      Topics
                    </StatLabel>
                    <StatNumber>{stats.totalTopics.toLocaleString()}</StatNumber>
                    <StatHelpText>Unique topics covered</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel display="flex" alignItems="center" gap={2}>
                      <Map size={16} />
                      Geolocated
                    </StatLabel>
                    <StatNumber>{stats.articlesWithLocation.toLocaleString()}</StatNumber>
                    <StatHelpText>Articles with locations</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card>
                <CardBody>
                  <Stat>
                    <StatLabel display="flex" alignItems="center" gap={2}>
                      <Calendar size={16} />
                      Recent
                    </StatLabel>
                    <StatNumber>{stats.recentArticles.toLocaleString()}</StatNumber>
                    <StatHelpText>Last 30 days</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </Grid>

            {/* Recent Articles */}
            <Grid templateColumns="2fr 1fr" gap={6}>
              <Card>
                <CardHeader>
                  <Text fontSize="lg" fontWeight="bold">Recent Articles</Text>
                </CardHeader>
                <CardBody>
                  <VStack spacing={3} align="stretch" maxH="400px" overflowY="auto">
                    {recentArticles.slice(0, 10).map((article) => (
                      <Box
                        key={article.uri}
                        p={3}
                        border="1px solid"
                        borderColor="gray.200"
                        borderRadius="md"
                        cursor="pointer"
                        _hover={{ bg: 'gray.50', borderColor: 'blue.300' }}
                        onClick={() => setSelectedArticle(article)}
                      >
                        <VStack align="start" spacing={2}>
                          <Text fontSize="sm" fontWeight="semibold" lineHeight="1.3">
                            {article.title}
                          </Text>
                          {article.abstract && (
                            <Text fontSize="xs" color="gray.600" lineHeight="1.3">
                              {article.abstract.length > 120
                                ? `${article.abstract.substring(0, 120)}...`
                                : article.abstract}
                            </Text>
                          )}
                          <HStack spacing={2}>
                            {article.section && (
                              <Badge colorScheme="blue" size="sm">
                                {article.section}
                              </Badge>
                            )}
                            {article.published && (
                              <Text fontSize="xs" color="gray.500">
                                {new Date(article.published).toLocaleDateString()}
                              </Text>
                            )}
                          </HStack>
                        </VStack>
                      </Box>
                    ))}
                  </VStack>
                </CardBody>
              </Card>

              <Card>
                <CardHeader>
                  <Text fontSize="lg" fontWeight="bold">Quick Actions</Text>
                </CardHeader>
                <CardBody>
                  <VStack spacing={3} align="stretch">
                    <Button
                      leftIcon={<Map size={16} />}
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedView('map')}
                    >
                      Explore Map View
                    </Button>
                    <Button
                      leftIcon={<Globe size={16} />}
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedView('graph')}
                    >
                      View Knowledge Graph
                    </Button>
                    <Button
                      leftIcon={<MessageSquare size={16} />}
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedView('chat')}
                    >
                      Ask AI Assistant
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </Grid>
          </VStack>
        )}

        {selectedView === 'map' && (
          <Card>
            <CardHeader>
              <Text fontSize="lg" fontWeight="bold">Geographic Distribution of Articles</Text>
            </CardHeader>
            <CardBody p={0}>
              <NewsMap
                articles={articles}
                onArticleSelect={setSelectedArticle}
                height="600px"
              />
            </CardBody>
          </Card>
        )}

        {selectedView === 'graph' && (
          <Card>
            <CardHeader>
              <HStack justify="space-between">
                <Text fontSize="lg" fontWeight="bold">Knowledge Graph Visualization</Text>
                {selectedArticle && (
                  <Badge colorScheme="green">
                    Showing: {selectedArticle.title.substring(0, 50)}...
                  </Badge>
                )}
              </HStack>
            </CardHeader>
            <CardBody p={0}>
              <NewsGraph
                article={selectedArticle}
                graphData={graphData}
                onNodeSelect={(node) => {
                  // Handle node selection if needed
                  console.log('Selected node:', node)
                }}
                height="600px"
              />
            </CardBody>
          </Card>
        )}

        {selectedView === 'chat' && (
          <Card>
            <CardBody p={0}>
              <NewsChat height="600px" />
            </CardBody>
          </Card>
        )}
      </Container>
    </Box>
  )
}