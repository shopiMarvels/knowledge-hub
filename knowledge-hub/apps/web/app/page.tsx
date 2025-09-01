'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, Server } from 'lucide-react'

interface HealthResponse {
  status: string
  timestamp: string
  version: string
  environment: string
}

interface ApiStatus {
  isLoading: boolean
  isConnected: boolean
  data: HealthResponse | null
  error: string | null
}

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    isLoading: true,
    isConnected: false,
    data: null,
    error: null
  })

  const fetchApiHealth = async () => {
    setApiStatus(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const response = await fetch('http://localhost:8000/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: HealthResponse = await response.json()
      
      setApiStatus({
        isLoading: false,
        isConnected: true,
        data,
        error: null
      })
    } catch (error) {
      setApiStatus({
        isLoading: false,
        isConnected: false,
        data: null,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      })
    }
  }

  useEffect(() => {
    fetchApiHealth()
    
    // Poll every 30 seconds
    const interval = setInterval(fetchApiHealth, 30000)
    
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    if (apiStatus.isLoading) {
      return <Clock className="h-6 w-6 text-yellow-500 animate-spin" />
    }
    
    if (apiStatus.isConnected) {
      return <CheckCircle className="h-6 w-6 text-green-500" />
    }
    
    return <XCircle className="h-6 w-6 text-red-500" />
  }

  const getStatusText = () => {
    if (apiStatus.isLoading) return 'Checking API status...'
    if (apiStatus.isConnected) return 'API Connected'
    return 'API Disconnected'
  }

  const getStatusColor = () => {
    if (apiStatus.isLoading) return 'text-yellow-600'
    if (apiStatus.isConnected) return 'text-green-600'
    return 'text-red-600'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Knowledge Hub
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Your intelligent knowledge management system
            </p>
          </div>

          {/* API Status Card */}
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <Server className="h-8 w-8 text-indigo-600" />
                <h2 className="text-2xl font-semibold text-gray-900">
                  API Status
                </h2>
              </div>
              <button
                onClick={fetchApiHealth}
                disabled={apiStatus.isLoading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Refresh
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Connection Status */}
              <div className="flex items-center space-x-3">
                {getStatusIcon()}
                <div>
                  <p className="text-sm text-gray-500">Connection Status</p>
                  <p className={`font-medium ${getStatusColor()}`}>
                    {getStatusText()}
                  </p>
                </div>
              </div>

              {/* API Details */}
              {apiStatus.data && (
                <>
                  <div>
                    <p className="text-sm text-gray-500">Environment</p>
                    <p className="font-medium text-gray-900 capitalize">
                      {apiStatus.data.environment}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Version</p>
                    <p className="font-medium text-gray-900">
                      {apiStatus.data.version}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Last Updated</p>
                    <p className="font-medium text-gray-900">
                      {new Date(apiStatus.data.timestamp).toLocaleString()}
                    </p>
                  </div>
                </>
              )}

              {/* Error Display */}
              {apiStatus.error && (
                <div className="md:col-span-2">
                  <p className="text-sm text-gray-500">Error Details</p>
                  <p className="font-medium text-red-600 bg-red-50 p-3 rounded-lg">
                    {apiStatus.error}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                🤖 AI-Powered
              </h3>
              <p className="text-gray-600">
                Leverage advanced AI capabilities for intelligent knowledge processing and retrieval.
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                📚 Knowledge Base
              </h3>
              <p className="text-gray-600">
                Organize and manage your knowledge with powerful search and categorization features.
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                🔄 Real-time Sync
              </h3>
              <p className="text-gray-600">
                Keep your knowledge synchronized across all devices and team members.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
