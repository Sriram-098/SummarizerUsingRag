import { GoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Shield,
  FileText,
  Search,
  Bot,
  Database,
  ScanLine,
} from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSuccess = async (credentialResponse) => {
    try {
      await login(credentialResponse.credential)
      toast.success('Welcome!')
      navigate('/app')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    }
  }

  const features = [
    { icon: FileText, title: 'Upload Documents', desc: 'PDF, TXT, and scanned documents' },
    { icon: ScanLine, title: 'OCR Support', desc: 'Extract text from scanned files' },
    { icon: Search, title: 'Smart Search', desc: 'Semantic similarity retrieval' },
    { icon: Bot, title: 'AI Answers', desc: 'Grounded in your data only' },
    { icon: Database, title: 'Private Storage', desc: 'Per-user isolated vector DB' },
    { icon: Shield, title: 'Secure Auth', desc: 'Google OAuth 2.0 sign-in' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-brand-50 flex">
      {/* Left — Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-600 to-brand-800 text-white p-12 flex-col justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight">🔍 RAG System</h1>
          <p className="mt-2 text-brand-200 text-lg">Enterprise Edition</p>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-12">
          {features.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10"
            >
              <Icon className="w-6 h-6 mb-2 text-brand-200" />
              <h3 className="font-semibold text-sm">{title}</h3>
              <p className="text-xs text-brand-200 mt-1">{desc}</p>
            </div>
          ))}
        </div>

        <p className="text-brand-300 text-xs">
          Powered by LangChain · ChromaDB · OpenRouter — 100% Free
        </p>
      </div>

      {/* Right — Login */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-10">
            <div className="text-5xl mb-4">🔍</div>
            <h2 className="text-3xl font-extrabold text-slate-900">Sign In</h2>
            <p className="text-slate-500 mt-2">
              Access your private enterprise RAG system
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleSuccess}
                onError={() => toast.error('Google login failed')}
                size="large"
                width="320"
                theme="outline"
                shape="pill"
                text="signin_with"
              />
            </div>

            <div className="mt-6 text-center">
              <p className="text-xs text-slate-400">
                By signing in you agree to our terms of service.
                <br />
                Your documents are stored privately and never shared.
              </p>
            </div>
          </div>

          {/* Mobile features */}
          <div className="lg:hidden mt-8 grid grid-cols-2 gap-3">
            {features.slice(0, 4).map(({ icon: Icon, title }) => (
              <div
                key={title}
                className="flex items-center gap-2 bg-white rounded-lg p-3 border border-slate-100 shadow-sm"
              >
                <Icon className="w-4 h-4 text-brand-500" />
                <span className="text-xs font-medium text-slate-700">{title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
