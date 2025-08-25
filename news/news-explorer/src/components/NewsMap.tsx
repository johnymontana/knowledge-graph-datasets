'use client'

import { useEffect, useRef, useState } from 'react'
import { Map, MapRef, Marker, Popup } from '@vis.gl/react-maplibre'
import { Box, Text, VStack, Badge, Link, Spinner, Alert, AlertIcon } from '@chakra-ui/react'
import { Article, Geo } from '@/lib/neo4j'
import 'maplibre-gl/dist/maplibre-gl.css'

interface NewsMapProps {
  articles: Array<{ article: Article; geo: Geo }>
  onArticleSelect?: (article: Article) => void
  height?: string
}

interface PopupInfo {
  article: Article
  geo: Geo
  longitude: number
  latitude: number
}

export default function NewsMap({ articles, onArticleSelect, height = '600px' }: NewsMapProps) {
  const mapRef = useRef<MapRef>(null)
  const [popupInfo, setPopupInfo] = useState<PopupInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error] = useState<string | null>(null)

  useEffect(() => {
    setIsLoading(false)
  }, [articles])

  const handleMarkerClick = (article: Article, geo: Geo, longitude: number, latitude: number) => {
    setPopupInfo({ article, geo, longitude, latitude })
    if (onArticleSelect) {
      onArticleSelect(article)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return dateString
    }
  }

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

  return (
    <Box height={height} width="100%" position="relative">
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: -98.5795,
          latitude: 39.8283,
          zoom: 3
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      >
        {articles.map(({ article, geo }, index) => {
          if (!geo.location) return null
          
          const { longitude, latitude } = geo.location
          
          return (
            <Marker
              key={`${article.uri}-${index}`}
              longitude={longitude}
              latitude={latitude}
              anchor="bottom"
              onClick={() => handleMarkerClick(article, geo, longitude, latitude)}
            >
              <Box
                width="12px"
                height="12px"
                borderRadius="50%"
                bg="red.500"
                border="2px solid white"
                boxShadow="0 2px 4px rgba(0,0,0,0.3)"
                cursor="pointer"
                _hover={{
                  transform: 'scale(1.2)',
                  bg: 'red.600'
                }}
                transition="all 0.2s"
              />
            </Marker>
          )
        })}

        {popupInfo && (
          <Popup
            anchor="top"
            longitude={popupInfo.longitude}
            latitude={popupInfo.latitude}
            onClose={() => setPopupInfo(null)}
            closeButton={true}
            closeOnClick={false}
            maxWidth="320px"
          >
            <VStack align="start" spacing={2} p={2}>
              <Text fontSize="sm" fontWeight="bold" lineHeight="1.2">
                {popupInfo.article.title}
              </Text>
              
              {popupInfo.article.abstract && (
                <Text fontSize="xs" color="gray.600" lineHeight="1.3">
                  {popupInfo.article.abstract.length > 150
                    ? `${popupInfo.article.abstract.substring(0, 150)}...`
                    : popupInfo.article.abstract}
                </Text>
              )}

              <VStack align="start" spacing={1}>
                <Badge colorScheme="blue" size="sm">
                  {popupInfo.geo.name}
                </Badge>
                
                {popupInfo.article.published && (
                  <Text fontSize="xs" color="gray.500">
                    {formatDate(popupInfo.article.published)}
                  </Text>
                )}

                {popupInfo.article.section && (
                  <Badge colorScheme="green" size="sm">
                    {popupInfo.article.section}
                  </Badge>
                )}
              </VStack>

              {popupInfo.article.url && (
                <Link
                  href={popupInfo.article.url}
                  isExternal
                  fontSize="xs"
                  color="blue.500"
                  _hover={{ textDecoration: 'underline' }}
                >
                  Read full article →
                </Link>
              )}
            </VStack>
          </Popup>
        )}
      </Map>
    </Box>
  )
}