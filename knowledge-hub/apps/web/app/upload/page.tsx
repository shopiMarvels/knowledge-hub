'use client'
import { useState } from 'react'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<string>('')
  const [docId, setDocId] = useState<number | null>(null)

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    setStatus('Uploading...')
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch(process.env.NEXT_PUBLIC_API_URL + '/documents', { method: 'POST', body: fd })
    const data = await res.json()
    setDocId(data.document_id)
    setStatus('Queued for parsing (doc #' + data.document_id + ')')
    // poll status
    const poll = async () => {
      const r = await fetch(process.env.NEXT_PUBLIC_API_URL + '/documents/' + data.document_id)
      const j = await r.json()
      setStatus(`Status: ${j.status} — chunks: ${j.chunks}`)
      if (j.status === 'parsed' || j.status === 'error' || j.status === 'parsed_empty') return
      setTimeout(poll, 1500)
    }
    setTimeout(poll, 1500)
  }

  return (
    <main className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold">Upload a Document</h1>
      <form onSubmit={onSubmit} className="mt-4 space-y-4">
        <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)} />
        <button className="px-4 py-2 rounded bg-black text-white" type="submit" disabled={!file}>Upload</button>
      </form>
      {status && (<p className="mt-4">{status}</p>)}
      {docId && (<p className="text-sm text-gray-500">Document ID: {docId}</p>)}
    </main>
  )
}
