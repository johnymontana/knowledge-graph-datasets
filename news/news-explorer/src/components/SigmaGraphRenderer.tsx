'use client'

import React, { useEffect, useRef, useMemo } from "react"
import { useSigma, useLoadGraph, useRegisterEvents } from "@react-sigma/core"
import Graphology from "graphology"
import { random } from 'graphology-layout'
import { useLayoutNoverlap } from '@react-sigma/layout-noverlap'
import { GraphNode } from './NewsGraph'

interface SigmaGraphRendererProps {
  graphData: {
    nodes: Array<{
      id: string
      label: string
      size: number
      color: string
      type: string
      [key: string]: unknown
    }>
    edges: Array<{
      id: string
      source: string
      target: string
      label: string
      color: string
      size: number
    }>
  }
  onNodeSelect?: (node: GraphNode) => void
  originalNodes: GraphNode[]
}

// Simple component that loads the graph into Sigma
const LoadGraph: React.FC<{ 
  graph: Graphology; 
  onNodeClick?: (nodeId: string, nodeData: Record<string, unknown>) => void;
  onEdgeClick?: (edgeId: string, edgeData: Record<string, unknown>) => void;
}> = ({ graph, onNodeClick, onEdgeClick }) => {
  const loadGraph = useLoadGraph()
  const registerEvents = useRegisterEvents()
  const sigma = useSigma()
  const { assign } = useLayoutNoverlap()

  useEffect(() => {
    if (sigma && graph && graph.order > 0) {
      console.log('Loading graph with', graph.order, 'nodes and', graph.size, 'edges')
      
      // Apply circular layout
      random.assign(graph)
      
      // Load the graph
      loadGraph(graph)
      
      // Apply noverlap layout
      assign()
      
      console.log('Graph loaded successfully')
    }
  }, [assign, loadGraph, graph, sigma])

  useEffect(() => {
    if (sigma) {
      console.log('Sigma instance created:', sigma)
      console.log('Sigma container:', sigma.getContainer())
      console.log('Sigma container dimensions:', { 
        width: sigma.getContainer()?.clientWidth, 
        height: sigma.getContainer()?.clientHeight 
      })
      
      // Force Sigma to resize after a short delay to ensure container is ready
      setTimeout(() => {
        try {
          const container = sigma.getContainer()
          if (container && container.clientWidth > 0 && container.clientHeight > 0) {
            sigma.resize()
            console.log('Sigma resized, new dimensions:', { 
              width: container.clientWidth, 
              height: container.clientHeight 
            })
          } else {
            console.log('Container not ready for resize, dimensions:', { 
              width: container?.clientWidth, 
              height: container?.clientHeight 
            })
          }
        } catch (error) {
          console.warn('Error during Sigma resize:', error)
        }
      }, 200) // Increased delay to ensure container is ready
    }
  }, [sigma])

  useEffect(() => {
    if (sigma && registerEvents) {
      // Register click events on nodes
      registerEvents({
        clickNode: (event) => {
          try {
            const graph = sigma.getGraph()
            if (graph && graph.hasNode(event.node)) {
              const nodeAttributes = graph.getNodeAttributes(event.node)
              onNodeClick?.(event.node, nodeAttributes)
            }
          } catch (error) {
            console.error('Error handling node click:', error)
          }
        },
        clickEdge: (event) => {
          try {
            const graph = sigma.getGraph()
            if (graph && graph.hasEdge(event.edge)) {
              const edgeAttributes = graph.getEdgeAttributes(event.edge)
              onEdgeClick?.(event.edge, edgeAttributes)
            }
          } catch (error) {
            console.error('Error handling edge click:', error)
          }
        },
        clickStage: () => {
          // Optional: handle stage click to deselect
        }
      })
    }
  }, [registerEvents, onNodeClick, onEdgeClick, sigma])

  return null
}

// Main SigmaGraphRenderer component
const SigmaGraphRenderer: React.FC<SigmaGraphRendererProps> = ({ 
  graphData, 
  onNodeSelect, 
  originalNodes 
}) => {
  const containerRef = useRef<HTMLDivElement>(null)

  // Convert our graph data to Graphology format using useMemo to prevent recreation on every render
  const graph = useMemo(() => {
    const g = new Graphology()
    
    // Add nodes with standard circle type
    graphData.nodes.forEach(node => {
      g.addNode(node.id, {
        label: node.label,
        size: node.size,
        color: node.color,
        type: 'circle' // Use standard circle type that Sigma knows how to render
      })
    })

    // Add edges
    graphData.edges.forEach(edge => {
      g.addEdge(edge.source, edge.target, {
        label: edge.label,
        color: edge.color,
        size: edge.size
      })
    })
    
    return g
  }, [graphData.nodes, graphData.edges])

  // Ensure container has proper dimensions
  useEffect(() => {
    if (containerRef.current) {
      const container = containerRef.current
      const parent = container.parentElement
      if (parent) {
        const parentHeight = parent.clientHeight
        const parentWidth = parent.clientWidth
        console.log('Parent dimensions:', { width: parentWidth, height: parentHeight })
        console.log('Container dimensions before:', { width: container.clientWidth, height: container.clientHeight })
        
        // Force container to have proper dimensions
        if (parentHeight > 0) {
          container.style.height = `${parentHeight}px`
          container.style.minHeight = `${parentHeight}px`
        } else {
          // Fallback to default dimensions if parent height is not available
          container.style.height = '500px'
          container.style.minHeight = '500px'
        }
        if (parentWidth > 0) {
          container.style.width = `${parentWidth}px`
        }
        
        console.log('Container dimensions after:', { width: container.clientWidth, height: container.clientHeight })
        
        // Set up ResizeObserver to handle dynamic height changes
        const resizeObserver = new ResizeObserver((entries) => {
          for (const entry of entries) {
            const { width, height } = entry.contentRect
            if (height > 0) {
              container.style.height = `${height}px`
              container.style.minHeight = `${height}px`
            }
            if (width > 0) {
              container.style.width = `${width}px`
            }
          }
        })
        resizeObserver.observe(parent)
        
        return () => {
          resizeObserver.disconnect()
        }
      }
    }
  }, [graphData])

  // Monitor container dimensions and force Sigma to resize
  useEffect(() => {
    const interval = setInterval(() => {
      if (containerRef.current) {
        const container = containerRef.current
        const { width, height } = container.getBoundingClientRect()
        if (height > 0 && height !== 500) {
          console.log('Container dimensions changed, updating styles:', { width, height })
          container.style.height = `${height}px`
          container.style.minHeight = `${height}px`
        }
      }
    }, 1000) // Check every second
    
    return () => clearInterval(interval)
  }, [])

  // Force Sigma to resize when graph changes
  useEffect(() => {
    if (graph && graph.order > 0) {
      // Force a resize after the graph is loaded
      setTimeout(() => {
        if (containerRef.current) {
          const container = containerRef.current
          const { width, height } = container.getBoundingClientRect()
          console.log('Graph loaded, forcing container resize:', { width, height })
          if (height > 0) {
            container.style.height = `${height}px`
            container.style.minHeight = `${height}px`
          }
        }
      }, 200)
    }
  }, [graph])

  // Force Sigma to resize when component mounts
  useEffect(() => {
    const timer = setTimeout(() => {
      if (containerRef.current) {
        const container = containerRef.current
        const { width, height } = container.getBoundingClientRect()
        console.log('Component mounted, container dimensions:', { width, height })
        if (height > 0) {
          container.style.height = `${height}px`
          container.style.minHeight = `${height}px`
        }
      }
    }, 500)
    
    return () => clearTimeout(timer)
  }, [])

  if (!graph || graph.order === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        No graph data available
      </div>
    )
  }

  // Note: Settings are handled by the SigmaContainer in the parent component

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      <LoadGraph 
        graph={graph}
        onNodeClick={(nodeId) => {
          const originalNode = originalNodes.find(n => n.id === nodeId)
          if (originalNode && onNodeSelect) {
            onNodeSelect(originalNode)
          }
        }}
        onEdgeClick={(edgeId, edgeData) => {
          console.log('Edge clicked:', edgeId, edgeData)
        }}
      />
    </div>
  )
}

export default SigmaGraphRenderer
