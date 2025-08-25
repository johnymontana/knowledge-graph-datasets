'use client'

import { useEffect, useRef, useState } from 'react'
import { Box, VStack, HStack, Text, Badge, Button, Select, Alert, AlertIcon, Spinner } from '@chakra-ui/react'
import { Article } from '@/lib/neo4j'

// Define types for graph data
interface GraphNode {
  id: string
  label: string
  type: 'article' | 'topic' | 'person' | 'organization' | 'geo' | 'author'
  size: number
  color: string
  data?: any
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

export default function NewsGraph({ article, graphData, onNodeSelect, height = '600px' }: NewsGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [layoutAlgorithm, setLayoutAlgorithm] = useState<string>('forceLayout')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Simple force-directed layout implementation
  useEffect(() => {
    if (!containerRef.current || !graphData.nodes.length) return

    setIsLoading(true)
    
    try {
      // Create canvas
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('Could not get canvas context')

      const container = containerRef.current
      canvas.width = container.clientWidth
      canvas.height = container.clientHeight
      canvas.style.width = '100%'
      canvas.style.height = '100%'
      
      // Clear previous canvas
      while (container.firstChild) {
        container.removeChild(container.firstChild)
      }
      container.appendChild(canvas)

      // Initialize node positions
      const nodes = graphData.nodes.map((node, i) => ({
        ...node,
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
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

        // Draw edges
        ctx.strokeStyle = '#e2e8f0'
        ctx.lineWidth = 1
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
          
          ctx.beginPath()
          ctx.arc(node.x, node.y, size, 0, Math.PI * 2)
          ctx.fillStyle = NODE_COLORS[node.type] || '#718096'
          ctx.fill()
          
          ctx.strokeStyle = selectedNode?.id === node.id ? '#000' : '#fff'
          ctx.lineWidth = selectedNode?.id === node.id ? 3 : 2
          ctx.stroke()

          // Draw labels
          ctx.fillStyle = '#2d3748'
          ctx.font = '12px Arial'
          ctx.textAlign = 'center'
          const label = node.label.length > 20 ? node.label.substring(0, 20) + '...' : node.label
          ctx.fillText(label, node.x, node.y + size + 15)
        })

        animationId = requestAnimationFrame(simulate)
      }

      // Handle click events
      const handleClick = (event: MouseEvent) => {
        const rect = canvas.getBoundingClientRect()
        const x = event.clientX - rect.left
        const y = event.clientY - rect.top

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

      canvas.addEventListener('click', handleClick)

      // Start simulation
      simulate()
      setIsLoading(false)

      // Cleanup
      return () => {
        cancelAnimationFrame(animationId)
        canvas.removeEventListener('click', handleClick)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
      setIsLoading(false)
    }
  }, [graphData, selectedNode, onNodeSelect])

  if (isLoading) {
    return (
      <Box height={height} display="flex" alignItems="center" justifyContent="center">
        <Spinner size="xl" />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert status="error" height={height}>
        <AlertIcon />
        {error}
      </Alert>
    )
  }

  if (!graphData.nodes.length) {
    return (
      <Alert status="info" height={height}>
        <AlertIcon />
        No graph data available. Select an article to view its connections.
      </Alert>
    )
  }

  return (
    <VStack height={height} spacing={4} align="stretch">
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
              // Reset positions
              setIsLoading(true)
              setTimeout(() => setIsLoading(false), 100)
            }}
          >
            Reset Layout
          </Button>
        </HStack>
      </HStack>

      <Box
        ref={containerRef}
        flex="1"
        bg="white"
        border="1px solid"
        borderColor="gray.200"
        borderRadius="md"
        position="relative"
        overflow="hidden"
      />

      {selectedNode && (
        <Box p={4} bg="gray.50" borderRadius="md">
          <VStack align="start" spacing={2}>
            <HStack>
              <Badge colorScheme="blue">{selectedNode.type}</Badge>
              <Text fontSize="lg" fontWeight="bold">{selectedNode.label}</Text>
            </HStack>
            {selectedNode.data && (
              <Text fontSize="sm" color="gray.600">
                {JSON.stringify(selectedNode.data, null, 2)}
              </Text>
            )}
          </VStack>
        </Box>
      )}
    </VStack>
  )
}