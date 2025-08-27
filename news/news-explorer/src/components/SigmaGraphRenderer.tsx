'use client'

import React, { useEffect, useMemo } from "react"
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
      
      // Add visual debugging - log the actual container dimensions
      const container = sigma.getContainer()
      if (container) {
        console.log('Container getBoundingClientRect:', container.getBoundingClientRect())
        console.log('Container offsetHeight:', container.offsetHeight)
        console.log('Container clientHeight:', container.clientHeight)
        console.log('Container scrollHeight:', container.scrollHeight)
        console.log('Container computed styles:', window.getComputedStyle(container))
      }
      
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

  if (!graph || graph.order === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        No graph data available
      </div>
    )
  }

  // Note: Settings are handled by the SigmaContainer in the parent component

  return (
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
  )
}

export default SigmaGraphRenderer
