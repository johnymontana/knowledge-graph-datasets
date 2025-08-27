'use client'

import { useState, useEffect } from 'react'
import { Box, VStack, HStack, Text, Badge, Button, Select, SimpleGrid, Card, CardBody, CardHeader, Tabs, TabList, TabPanels, Tab, TabPanel } from '@chakra-ui/react'
import dynamic from 'next/dynamic'
import { Article } from '@/lib/neo4j'

// Define types for graph data
export interface GraphNode {
  id: string
  label: string
  type: 'article' | 'topic' | 'person' | 'organization' | 'geo' | 'author'
  size: number
  color: string
  data?: Record<string, unknown>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  color: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface NewsGraphProps {
  article?: Article
  graphData: GraphData
  onNodeSelect?: (node: GraphNode) => void
  height?: string
}

const NODE_COLORS = {
  article: '#3182ce',
  topic: '#38a169',
  person: '#d69e2e',
  organization: '#9f7aea',
  geo: '#e53e3e',
  author: '#00b5d8'
}

const NODE_SIZES = {
  article: 20,
  topic: 15,
  person: 12,
  organization: 12,
  geo: 10,
  author: 8
}

// Dynamically import React Sigma components to avoid SSR issues
const SigmaContainer = dynamic(
  () => import('@react-sigma/core').then(mod => ({ default: mod.SigmaContainer })),
  { 
    ssr: false, 
    loading: () => (
      <Box 
        height="100%" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        bg="gray.50"
      >
        <VStack spacing={2}>
          <Text>Loading React Sigma...</Text>
          <Text fontSize="sm" color="gray.500">Initializing graph visualization</Text>
        </VStack>
      </Box>
    )
  }
)

// Dynamically import the SigmaGraphRenderer component
const SigmaGraphRenderer = dynamic(
  () => import('./SigmaGraphRenderer'),
  { 
    ssr: false,
    loading: () => (
      <Box 
        height="100%" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        bg="gray.50"
      >
        <VStack spacing={2}>
          <Text>Loading Sigma Graph...</Text>
          <Text fontSize="sm" color="gray.500">Initializing graph visualization</Text>
        </VStack>
      </Box>
    )
  }
)

// Actual working React Sigma component that uses hooks correctly
function RealWorkingSigmaGraph({ graphData, onNodeSelect }: { graphData: GraphData; onNodeSelect?: (nodeId: string, nodeData: Record<string, unknown>) => void }) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return (
      <Box 
        height="100%" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        bg="gray.50"
      >
        <Text>Initializing...</Text>
      </Box>
    )
  }

  // Convert our graph data to Sigma.js format
  const sigmaNodes = graphData.nodes.map(node => ({
    id: node.id,
    label: node.label,
    size: NODE_SIZES[node.type] || 10,
    color: NODE_COLORS[node.type] || '#666',
    type: node.type,
    ...node.data
  }))

  const sigmaEdges = graphData.edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    color: edge.color || '#999',
    size: 1
  }))

  // Create the graph data for Sigma
  const sigmaGraph = {
    nodes: sigmaNodes,
    edges: sigmaEdges
  }

  return (
                    <SigmaGraphRenderer 
                  graphData={sigmaGraph} 
                  onNodeSelect={onNodeSelect}
                  originalNodes={graphData.nodes}
                />
  )
}

export default function NewsGraph({ graphData, onNodeSelect, height = '600px' }: NewsGraphProps) {
  const [layoutAlgorithm, setLayoutAlgorithm] = useState<string>('forceLayout')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [activeTab, setActiveTab] = useState(0)

  // Handle node selection from the graph
  const handleNodeSelect = (nodeId: string, nodeData: Record<string, unknown>) => {
    console.log('=== NODE SELECTION DEBUG ===')
    console.log('Node ID received:', nodeId)
    console.log('Node data received:', nodeData)
    console.log('Available graphData.nodes:', graphData.nodes)
    console.log('Looking for node with ID:', nodeId)
    
    // Find the original node data
    const originalNode = graphData.nodes.find(n => n.id === nodeId)
    console.log('Original node found:', originalNode)
    
    if (originalNode) {
      console.log('Setting selected node:', originalNode)
      setSelectedNode(originalNode)
      if (onNodeSelect) {
        onNodeSelect(originalNode)
      }
    } else {
      console.warn('No original node found for ID:', nodeId)
      console.warn('Available node IDs:', graphData.nodes.map(n => n.id))
    }
    console.log('=== END NODE SELECTION DEBUG ===')
  }

  if (!graphData.nodes.length) {
    return (
      <Box height={height} display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={4}>
          <Text>No graph data available</Text>
        </VStack>
      </Box>
    )
  }

  // Group nodes by type
  const nodesByType = graphData.nodes.reduce((acc, node) => {
    if (!acc[node.type]) {
      acc[node.type] = []
    }
    acc[node.type].push(node)
    return acc
  }, {} as Record<string, GraphNode[]>)

  // Group edges by type
  const edgesByType = graphData.edges.reduce((acc, edge) => {
    if (!acc[edge.type]) {
      acc[edge.type] = []
    }
    acc[edge.type].push(edge)
    return acc
  }, {} as Record<string, GraphEdge[]>)

  return (
    <VStack height={height} spacing={4} align="stretch" overflow="auto">
      <HStack justify="space-between" align="center">
        <VStack align="start" spacing={1}>
          <Text fontSize="lg" fontWeight="bold">Knowledge Graph</Text>
          <Text fontSize="sm" color="gray.600">
            {graphData.nodes.length} nodes, {graphData.edges.length} connections
          </Text>
        </VStack>

        <HStack spacing={4}>
          <Select
            size="sm"
            value={layoutAlgorithm}
            onChange={(e) => setLayoutAlgorithm(e.target.value)}
            width="150px"
          >
            <option value="forceLayout">Force Layout</option>
            <option value="circular">Circular</option>
            <option value="random">Random</option>
          </Select>
          
          <Button
            size="sm"
            onClick={() => {
              setSelectedNode(null)
            }}
          >
            Reset Selection
          </Button>
        </HStack>
      </HStack>

      {/* Tabbed Interface */}
      <Tabs index={activeTab} onChange={setActiveTab} variant="enclosed">
        <TabList>
          <Tab>Visual Graph</Tab>
          <Tab>Data View</Tab>
        </TabList>

        <TabPanels>
          {/* Visual Graph Tab */}
          <TabPanel p={0}>
            <Box
              height="500px"
              bg="white"
              border="1px solid"
              borderColor="gray.200"
              borderRadius="md"
              position="relative"
              overflow="hidden"
            >
              <SigmaContainer 
                style={{ height: '500px', width: '100%' }}
                settings={{
                  allowInvalidContainer: true,
                  renderEdgeLabels: true,
                  labelSize: 12,
                  labelWeight: 'bold',
                  zIndex: true,
                  minCameraRatio: 0.1,
                  maxCameraRatio: 10
                }}
              >
                <RealWorkingSigmaGraph graphData={graphData} onNodeSelect={handleNodeSelect} />
              </SigmaContainer>
            </Box>
          </TabPanel>

          {/* Data View Tab */}
          <TabPanel p={0}>
            <VStack spacing={4} align="stretch">
              {/* Graph Overview */}
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                {/* Nodes by Type */}
                <Card>
                  <CardHeader>
                    <Text fontSize="md" fontWeight="bold">Nodes by Type</Text>
                  </CardHeader>
                  <CardBody>
                    <VStack align="start" spacing={2}>
                      {Object.entries(nodesByType).map(([type, nodes]) => (
                        <HStack key={type} justify="space-between" width="100%">
                          <HStack>
                            <Badge colorScheme={type === 'article' ? 'blue' : type === 'topic' ? 'green' : type === 'person' ? 'yellow' : type === 'organization' ? 'purple' : type === 'geo' ? 'red' : 'cyan'}>
                              {type}
                            </Badge>
                            <Text fontSize="sm">{nodes.length} nodes</Text>
                          </HStack>
                        </HStack>
                      ))}
                    </VStack>
                  </CardBody>
                </Card>

                {/* Edges by Type */}
                <Card>
                  <CardHeader>
                    <Text fontSize="md" fontWeight="bold">Relationships by Type</Text>
                  </CardHeader>
                  <CardBody>
                    <VStack align="start" spacing={2}>
                      {Object.entries(edgesByType).map(([type, edges]) => (
                        <HStack key={type} justify="space-between" width="100%">
                          <Text fontSize="sm">{type}</Text>
                          <Badge colorScheme="blue">{edges.length} connections</Badge>
                        </HStack>
                      ))}
                    </VStack>
                  </CardBody>
                </Card>
              </SimpleGrid>

              {/* Node Details */}
              <Card>
                <CardHeader>
                  <Text fontSize="md" fontWeight="bold">Graph Nodes</Text>
                </CardHeader>
                <CardBody>
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={3}>
                    {graphData.nodes.map((node) => (
                      <Box
                        key={node.id}
                        p={3}
                        border="1px solid"
                        borderColor="gray.200"
                        borderRadius="md"
                        cursor="pointer"
                        onClick={() => {
                          setSelectedNode(node)
                          if (onNodeSelect) {
                            onNodeSelect(node)
                          }
                        }}
                        bg={selectedNode?.id === node.id ? 'blue.50' : 'white'}
                        _hover={{ bg: 'gray.50' }}
                      >
                        <VStack align="start" spacing={1}>
                          <HStack>
                            <Badge colorScheme={node.type === 'article' ? 'blue' : node.type === 'topic' ? 'green' : node.type === 'person' ? 'yellow' : node.type === 'organization' ? 'purple' : node.type === 'geo' ? 'red' : 'cyan'}>
                              {node.type}
                            </Badge>
                            <Text fontSize="sm" fontWeight="bold" noOfLines={2}>
                              {node.label}
                            </Text>
                          </HStack>
                          <Text fontSize="xs" color="gray.500">
                            ID: {node.id}
                          </Text>
                        </VStack>
                      </Box>
                    ))}
                  </SimpleGrid>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Selected Node Details */}
      {selectedNode && (
        <Card>
          <CardHeader>
            <HStack justify="space-between" align="center">
              <HStack>
                <Badge colorScheme={selectedNode.type === 'article' ? 'blue' : selectedNode.type === 'topic' ? 'green' : selectedNode.type === 'person' ? 'yellow' : selectedNode.type === 'organization' ? 'purple' : selectedNode.type === 'geo' ? 'red' : 'cyan'}>
                  {selectedNode.type}
                </Badge>
                <Text fontSize="lg" fontWeight="bold">{selectedNode.label}</Text>
              </HStack>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedNode(null)}
              >
                ✕
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            {/* Debug Info */}
            <Box mb={4} p={3} bg="yellow.50" borderRadius="md" border="1px solid" borderColor="yellow.200">
              <Text fontSize="sm" fontWeight="bold" color="yellow.800">Debug Info:</Text>
              <Text fontSize="xs" fontFamily="mono" color="yellow.700">
                selectedNode: {JSON.stringify(selectedNode, null, 2)}
              </Text>
            </Box>
            
            <VStack align="start" spacing={4}>
              {/* Basic Node Information */}
              <Box>
                <Text fontSize="md" fontWeight="bold" mb={2}>Node Information</Text>
                <SimpleGrid columns={2} spacing={3}>
                  <Box>
                    <Text fontSize="sm" color="gray.600">ID</Text>
                    <Text fontSize="sm" fontFamily="mono">{selectedNode.id}</Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.600">Type</Text>
                    <Text fontSize="sm">{selectedNode.type}</Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.600">Size</Text>
                    <Text fontSize="sm">{selectedNode.size}</Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.600">Color</Text>
                    <Box 
                      width="20px" 
                      height="20px" 
                      bg={selectedNode.color} 
                      borderRadius="sm"
                      border="1px solid"
                      borderColor="gray.300"
                    />
                  </Box>
                </SimpleGrid>
              </Box>

              {/* Node Data Properties */}
              {selectedNode.data && Object.keys(selectedNode.data).length > 0 && (
                <Box>
                  <Text fontSize="md" fontWeight="bold" mb={2}>Properties</Text>
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                    {Object.entries(selectedNode.data).map(([key, value]) => (
                      <Box key={key} p={3} bg="gray.50" borderRadius="md">
                        <Text fontSize="sm" fontWeight="bold" color="gray.700" mb={1}>
                          {key}
                        </Text>
                        <Text fontSize="sm" color="gray.600" wordBreak="break-word">
                          {String(value)}
                        </Text>
                      </Box>
                    ))}
                  </SimpleGrid>
                </Box>
              )}

              {/* Connected Edges */}
              <Box>
                <Text fontSize="md" fontWeight="bold" mb={2}>Connections</Text>
                <VStack align="start" spacing={2}>
                  {graphData.edges
                    .filter(edge => edge.source === selectedNode.id || edge.target === selectedNode.id)
                    .map(edge => {
                      const isSource = edge.source === selectedNode.id
                      const connectedNodeId = isSource ? edge.target : edge.source
                      const connectedNode = graphData.nodes.find(n => n.id === connectedNodeId)
                      
                      return (
                        <Box 
                          key={edge.id} 
                          p={3} 
                          bg="blue.50" 
                          borderRadius="md" 
                          border="1px solid"
                          borderColor="blue.200"
                          width="100%"
                        >
                          <HStack justify="space-between" align="center">
                            <VStack align="start" spacing={1}>
                              <Text fontSize="sm" fontWeight="bold">
                                {isSource ? '→' : '←'} {edge.type}
                              </Text>
                              <Text fontSize="sm" color="gray.600">
                                {connectedNode?.label || connectedNodeId}
                              </Text>
                            </VStack>
                            <Badge colorScheme={connectedNode?.type === 'article' ? 'blue' : connectedNode?.type === 'topic' ? 'green' : connectedNode?.type === 'person' ? 'yellow' : connectedNode?.type === 'organization' ? 'purple' : connectedNode?.type === 'geo' ? 'red' : 'cyan'}>
                              {connectedNode?.type || 'unknown'}
                            </Badge>
                          </HStack>
                        </Box>
                      )
                    })}
                  {graphData.edges.filter(edge => edge.source === selectedNode.id || edge.target === selectedNode.id).length === 0 && (
                    <Text fontSize="sm" color="gray.500">No connections found</Text>
                  )}
                </VStack>
              </Box>
            </VStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  )
}
