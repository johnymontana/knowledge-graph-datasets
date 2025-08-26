'use client'

import { useState, useEffect, useRef } from 'react'
import { Box, VStack, HStack, Text, Badge, Button, Select, SimpleGrid, Card, CardBody, CardHeader, Tabs, TabList, TabPanels, Tab, TabPanel } from '@chakra-ui/react'
import { Article } from '@/lib/neo4j'

// Define types for graph data
interface GraphNode {
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

// Canvas-based graph renderer with zoom and pan
function CanvasGraphRenderer({ graphData, onNodeSelect }: { graphData: GraphData; onNodeSelect?: (node: GraphNode) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const [panX, setPanX] = useState(0)
  const [panY, setPanY] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  useEffect(() => {
    if (!canvasRef.current || !graphData.nodes.length) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    // Initialize node positions
    const nodes = graphData.nodes.map((node) => ({
      ...node,
      x: Math.random() * (canvas.width - 100) + 50,
      y: Math.random() * (canvas.height - 100) + 50,
      vx: 0,
      vy: 0
    }))

    // Simple force simulation
    let animationId: number

    const simulate = () => {
      // Apply forces
      for (let i = 0; i < nodes.length; i++) {
        const nodeA = nodes[i]
        
        // Repulsion between all nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const nodeB = nodes[j]
          const dx = nodeA.x - nodeB.x
          const dy = nodeA.y - nodeB.y
          const distance = Math.sqrt(dx * dx + dy * dy) || 1
          const force = 1000 / (distance * distance)
          
          const fx = (dx / distance) * force
          const fy = (dy / distance) * force
          
          nodeA.vx += fx
          nodeA.vy += fy
          nodeB.vx -= fx
          nodeB.vy -= fy
        }

        // Attraction for connected nodes
        graphData.edges.forEach(edge => {
          if (edge.source === nodeA.id) {
            const target = nodes.find(n => n.id === edge.target)
            if (target) {
              const dx = target.x - nodeA.x
              const dy = target.y - nodeA.y
              const distance = Math.sqrt(dx * dx + dy * dy) || 1
              const force = distance * 0.001
              
              nodeA.vx += (dx / distance) * force
              nodeA.vy += (dy / distance) * force
            }
          }
        })

        // Center gravity
        const centerX = canvas.width / 2
        const centerY = canvas.height / 2
        const dx = centerX - nodeA.x
        const dy = centerY - nodeA.y
        nodeA.vx += dx * 0.0001
        nodeA.vy += dy * 0.0001

        // Apply velocity and damping
        nodeA.vx *= 0.9
        nodeA.vy *= 0.9
        nodeA.x += nodeA.vx
        nodeA.y += nodeA.vy

        // Keep nodes in bounds
        nodeA.x = Math.max(20, Math.min(canvas.width - 20, nodeA.x))
        nodeA.y = Math.max(20, Math.min(canvas.height - 20, nodeA.y))
      }

      // Draw
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // Apply zoom and pan transformations
      ctx.save()
      ctx.translate(panX, panY)
      ctx.scale(zoom, zoom)

      // Draw edges
      ctx.strokeStyle = '#e2e8f0'
      ctx.lineWidth = 1 / zoom // Adjust line width for zoom
      graphData.edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.source)
        const target = nodes.find(n => n.id === edge.target)
        if (source && target) {
          ctx.beginPath()
          ctx.moveTo(source.x, source.y)
          ctx.lineTo(target.x, target.y)
          ctx.stroke()
        }
      })

      // Draw nodes
      nodes.forEach(node => {
        const size = NODE_SIZES[node.type] || 10
        const color = NODE_COLORS[node.type] || '#718096'
        
        ctx.beginPath()
        ctx.arc(node.x, node.y, size, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
        
        ctx.strokeStyle = selectedNode?.id === node.id ? '#000' : '#fff'
        ctx.lineWidth = selectedNode?.id === node.id ? 3 / zoom : 2 / zoom
        ctx.stroke()

        // Draw labels
        ctx.fillStyle = '#2d3748'
        ctx.font = `${12 / zoom}px Arial`
        ctx.textAlign = 'center'
        const label = node.label.length > 20 ? node.label.substring(0, 20) + '...' : node.label
        ctx.fillText(label, node.x, node.y + size + 15 / zoom)
      })

      ctx.restore()

      animationId = requestAnimationFrame(simulate)
    }

    // Handle click events
    const handleClick = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      const x = (event.clientX - rect.left - panX) / zoom
      const y = (event.clientY - rect.top - panY) / zoom

      const clickedNode = nodes.find(node => {
        const distance = Math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2)
        return distance <= (NODE_SIZES[node.type] || 10)
      })

      if (clickedNode) {
        setSelectedNode(clickedNode)
        if (onNodeSelect) {
          onNodeSelect(clickedNode)
        }
      } else {
        setSelectedNode(null)
      }
    }

    // Handle wheel zoom
    const handleWheel = (event: WheelEvent) => {
      event.preventDefault()
      const rect = canvas.getBoundingClientRect()
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top
      
      const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1
      const newZoom = Math.max(0.1, Math.min(5, zoom * zoomFactor))
      
      // Zoom towards mouse position
      const zoomRatio = newZoom / zoom
      setPanX(mouseX - (mouseX - panX) * zoomRatio)
      setPanY(mouseY - (mouseY - panY) * zoomRatio)
      setZoom(newZoom)
    }

    // Handle mouse down for panning
    const handleMouseDown = (event: MouseEvent) => {
      if (event.button === 0) { // Left click only
        setIsDragging(true)
        setDragStart({ x: event.clientX - panX, y: event.clientY - panY })
      }
    }

    // Handle mouse move for panning
    const handleMouseMove = (event: MouseEvent) => {
      if (isDragging) {
        setPanX(event.clientX - dragStart.x)
        setPanY(event.clientY - dragStart.y)
      }
    }

    // Handle mouse up for panning
    const handleMouseUp = () => {
      setIsDragging(false)
    }

    // Add event listeners
    canvas.addEventListener('click', handleClick)
    canvas.addEventListener('wheel', handleWheel, { passive: false })
    canvas.addEventListener('mousedown', handleMouseDown)
    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseup', handleMouseUp)
    canvas.addEventListener('mouseleave', handleMouseUp)

    // Start simulation
    simulate()

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId)
      canvas.removeEventListener('click', handleClick)
      canvas.removeEventListener('wheel', handleWheel)
      canvas.removeEventListener('mousedown', handleMouseDown)
      canvas.removeEventListener('mousemove', handleMouseMove)
      canvas.removeEventListener('mouseup', handleMouseUp)
      canvas.removeEventListener('mouseleave', handleMouseUp)
    }
  }, [graphData, onNodeSelect, zoom, panX, panY, isDragging, dragStart])

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        cursor: isDragging ? 'grabbing' : 'grab'
      }}
    />
  )
}

export default function NewsGraph({ graphData, onNodeSelect, height = '600px' }: NewsGraphProps) {
  const [layoutAlgorithm, setLayoutAlgorithm] = useState<string>('forceLayout')
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [activeTab, setActiveTab] = useState(0)

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
              <CanvasGraphRenderer graphData={graphData} onNodeSelect={onNodeSelect} />
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
            <HStack>
              <Badge colorScheme={selectedNode.type === 'article' ? 'blue' : selectedNode.type === 'topic' ? 'green' : selectedNode.type === 'person' ? 'yellow' : selectedNode.type === 'organization' ? 'purple' : selectedNode.type === 'geo' ? 'red' : 'cyan'}>
                {selectedNode.type}
              </Badge>
              <Text fontSize="lg" fontWeight="bold">{selectedNode.label}</Text>
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm"><strong>ID:</strong> {selectedNode.id}</Text>
              {selectedNode.data && Object.entries(selectedNode.data).map(([key, value]) => (
                <Text key={key} fontSize="sm">
                  <strong>{key}:</strong> {String(value)}
                </Text>
              ))}
            </VStack>
          </CardBody>
        </Card>
      )}
    </VStack>
  )
}