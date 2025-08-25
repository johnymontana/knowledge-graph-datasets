'use client'

import { useState } from 'react'
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Avatar,
  Card,
  CardBody,
  IconButton,
  Tooltip,
  Alert,
  AlertIcon,
  Spinner,
  Badge
} from '@chakra-ui/react'
import { Send, Bot, User, Copy, ThumbsUp, ThumbsDown } from 'lucide-react'

interface NewsChatProps {
  height?: string
  placeholder?: string
}

export default function NewsChat({ 
  height = '600px', 
  placeholder = 'Ask me about the news dataset...' 
}: NewsChatProps) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Array<{id: string, role: 'user' | 'assistant', content: string, createdAt: Date}>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input,
      createdAt: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [...messages, userMessage] })
      })
      
      if (!response.ok) throw new Error('Failed to send message')
      
      // For now, just add a simple response
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'This is a placeholder response. The chat API is being configured.',
        createdAt: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }
  
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null)

  const copyToClipboard = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMessageId(messageId)
      setTimeout(() => setCopiedMessageId(null), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <VStack height={height} spacing={0} align="stretch">
      {/* Header */}
      <Box p={4} borderBottom="1px solid" borderColor="gray.200" bg="gray.50">
        <HStack>
          <Bot size={24} color="#3182ce" />
          <VStack align="start" spacing={0}>
            <Text fontWeight="bold" fontSize="lg">News Dataset Assistant</Text>
            <Text fontSize="sm" color="gray.600">
              Ask questions about articles, topics, people, and locations
            </Text>
          </VStack>
        </HStack>
      </Box>

      {/* Messages */}
      <Box flex="1" overflowY="auto" p={4}>
        <VStack spacing={4} align="stretch">
          {messages.length === 0 && (
            <Box textAlign="center" py={8}>
              <Bot size={48} color="#718096" style={{ margin: '0 auto 16px' }} />
              <Text color="gray.500" mb={4}>
                Welcome! I can help you explore the news dataset.
              </Text>
              <VStack spacing={2}>
                <Badge colorScheme="blue" size="sm">Try asking:</Badge>
                <Text fontSize="sm" color="gray.600">&ldquo;Show me recent articles&rdquo;</Text>
                <Text fontSize="sm" color="gray.600">&ldquo;What topics are most popular?&rdquo;</Text>
                <Text fontSize="sm" color="gray.600">&ldquo;Find articles about climate change&rdquo;</Text>
                <Text fontSize="sm" color="gray.600">&ldquo;Show me articles from New York&rdquo;</Text>
              </VStack>
            </Box>
          )}

          {messages.map((message) => (
            <HStack
              key={message.id}
              align="start"
              spacing={3}
              justify={message.role === 'user' ? 'flex-end' : 'flex-start'}
            >
              {message.role === 'assistant' && (
                <Avatar size="sm" bg="blue.500" icon={<Bot size={16} />} />
              )}

              <Card
                maxWidth="70%"
                bg={message.role === 'user' ? 'blue.500' : 'white'}
                color={message.role === 'user' ? 'white' : 'black'}
                border={message.role === 'assistant' ? '1px solid' : 'none'}
                borderColor="gray.200"
              >
                <CardBody p={3}>
                  <VStack align="start" spacing={2}>
                    <Text fontSize="sm" lineHeight="1.5" whiteSpace="pre-wrap">
                      {message.content}
                    </Text>
                    
                    <HStack justify="space-between" w="100%">
                      <Text fontSize="xs" opacity={0.7}>
                        {formatTimestamp(message.createdAt || new Date())}
                      </Text>
                      
                      {message.role === 'assistant' && (
                        <HStack spacing={1}>
                          <Tooltip label="Copy response">
                            <IconButton
                              size="xs"
                              variant="ghost"
                              aria-label="Copy response"
                              icon={<Copy size={12} />}
                              onClick={() => copyToClipboard(message.content, message.id)}
                              color={copiedMessageId === message.id ? 'green.500' : 'gray.500'}
                            />
                          </Tooltip>
                          <Tooltip label="Helpful">
                            <IconButton
                              size="xs"
                              variant="ghost"
                              aria-label="Thumbs up"
                              icon={<ThumbsUp size={12} />}
                              color="gray.500"
                              _hover={{ color: 'green.500' }}
                            />
                          </Tooltip>
                          <Tooltip label="Not helpful">
                            <IconButton
                              size="xs"
                              variant="ghost"
                              aria-label="Thumbs down"
                              icon={<ThumbsDown size={12} />}
                              color="gray.500"
                              _hover={{ color: 'red.500' }}
                            />
                          </Tooltip>
                        </HStack>
                      )}
                    </HStack>
                  </VStack>
                </CardBody>
              </Card>

              {message.role === 'user' && (
                <Avatar size="sm" bg="gray.500" icon={<User size={16} />} />
              )}
            </HStack>
          ))}

          {isLoading && (
            <HStack align="start" spacing={3}>
              <Avatar size="sm" bg="blue.500" icon={<Bot size={16} />} />
              <Card bg="white" border="1px solid" borderColor="gray.200">
                <CardBody p={3}>
                  <HStack spacing={2}>
                    <Spinner size="sm" />
                    <Text fontSize="sm" color="gray.600">
                      Thinking...
                    </Text>
                  </HStack>
                </CardBody>
              </Card>
            </HStack>
          )}
        </VStack>
      </Box>

      {error && (
        <Alert status="error" size="sm">
          <AlertIcon />
          <Text fontSize="sm">
            {error || 'An error occurred. Please try again.'}
          </Text>
        </Alert>
      )}

      {/* Input */}
      <Box p={4} borderTop="1px solid" borderColor="gray.200" bg="gray.50">
        <form onSubmit={handleSubmit}>
          <HStack>
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder={placeholder}
              disabled={isLoading}
              bg="white"
              _focus={{ borderColor: 'blue.400' }}
            />
            <Button
              type="submit"
              colorScheme="blue"
              disabled={!input.trim() || isLoading}
              leftIcon={<Send size={16} />}
              isLoading={isLoading}
            >
              Send
            </Button>
          </HStack>
        </form>
      </Box>
    </VStack>
  )
}