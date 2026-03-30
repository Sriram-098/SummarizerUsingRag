import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { getRagStats, listDocuments, getOcrStatus } from '../api'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import ChatPanel from '../components/ChatPanel'

export default function Dashboard() {
  const { user } = useAuth()
  const [documents, setDocuments] = useState([])
  const [stats, setStats] = useState({ vectors: 0, exists: false })
  const [ocrAvailable, setOcrAvailable] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [model, setModel] = useState('z-ai/glm-4.5-air:free')
  const [chunkSize, setChunkSize] = useState(1000)
  const [chunkOverlap, setChunkOverlap] = useState(100)
  const [topK, setTopK] = useState(3)

  const refresh = async () => {
    try {
      const [docsRes, statsRes, ocrRes] = await Promise.all([
        listDocuments(),
        getRagStats(),
        getOcrStatus(),
      ])
      setDocuments(docsRes.data)
      setStats(statsRes.data)
      setOcrAvailable(ocrRes.data.available)
    } catch (err) {
      console.error('Failed to refresh:', err)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Navbar
        user={user}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
          <Sidebar
            documents={documents}
            stats={stats}
            ocrAvailable={ocrAvailable}
            model={model}
            setModel={setModel}
            chunkSize={chunkSize}
            setChunkSize={setChunkSize}
            chunkOverlap={chunkOverlap}
            setChunkOverlap={setChunkOverlap}
            topK={topK}
            setTopK={setTopK}
            onRefresh={refresh}
          />
        )}

        {/* Chat */}
        <ChatPanel
          stats={stats}
          model={model}
          topK={topK}
          documents={documents}
        />
      </div>
    </div>
  )
}
