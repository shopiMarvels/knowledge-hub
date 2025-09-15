'use client'
import { useState } from 'react'
import Link from 'next/link'

export default function IngestPage() {
  const [url, setUrl] = useState('')
  const [source, setSource] = useState('github')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url) return

    setLoading(true)
    setStatus('Ingesting...')
    
    try {
      const res = await fetch(process.env.NEXT_PUBLIC_API_URL + '/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, url })
      })
      
      const data = await res.json()
      
      if (res.ok) {
        setStatus(`✅ Successfully queued ${data.job} for ${data.source}`)
        setUrl('')
      } else {
        setStatus(`❌ Error: ${data.message || 'Failed to ingest'}`)
      }
    } catch (err) {
      setStatus('❌ Error: Failed to connect to API')
    } finally {
      setLoading(false)
    }
  }

  const examples = {
    github: [
      'https://github.com/microsoft/TypeScript',
      'https://github.com/facebook/react',
      'https://github.com/vercel/next.js'
    ],
    rss: [
      'https://feeds.feedburner.com/oreilly/radar',
      'https://rss.cnn.com/rss/edition.rss',
      'https://feeds.a16z.com/a16z'
    ]
  }

  return (
    <main className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Multi-Source Ingestion</h1>
        <p className="text-gray-600">
          Ingest content from external sources into your knowledge hub.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Source Type</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setSource('github')}
              className={`p-4 rounded-lg border-2 text-left transition-colors ${
                source === 'github' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-semibold">GitHub Repository</div>
              <div className="text-sm text-gray-600">Import README and docs</div>
            </button>
            <button
              type="button"
              onClick={() => setSource('rss')}
              className={`p-4 rounded-lg border-2 text-left transition-colors ${
                source === 'rss' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-semibold">RSS Feed</div>
              <div className="text-sm text-gray-600">Import recent articles</div>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={source === 'github' ? 'https://github.com/user/repo' : 'https://example.com/feed.xml'}
            className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Examples</label>
          <div className="space-y-2">
            {examples[source as keyof typeof examples].map((example, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setUrl(example)}
                className="block w-full text-left px-3 py-2 text-sm bg-gray-50 rounded hover:bg-gray-100 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!url || loading}
            className="flex-1 px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Ingesting...' : `Ingest from ${source}`}
          </button>
          <Link
            href="/dashboard"
            className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
          >
            Dashboard
          </Link>
        </div>
      </form>

      {status && (
        <div className={`mt-6 p-4 rounded-lg ${
          status.startsWith('✅') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {status}
        </div>
      )}

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">How it works</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>GitHub:</strong> Fetches README.md and documentation files</li>
          <li>• <strong>RSS:</strong> Imports recent articles from news feeds and blogs</li>
          <li>• All content goes through the same pipeline: parsing → chunking → embedding → tagging → summarization</li>
        </ul>
      </div>
    </main>
  )
}
