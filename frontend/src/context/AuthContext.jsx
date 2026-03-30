import { createContext, useContext, useState, useEffect } from 'react'
import { googleLogin, getMe } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('rag_token')
    const savedUser = localStorage.getItem('rag_user')
    if (token && savedUser) {
      setUser(JSON.parse(savedUser))
      // Validate token in background
      getMe()
        .then((res) => {
          setUser(res.data)
          localStorage.setItem('rag_user', JSON.stringify(res.data))
        })
        .catch(() => {
          localStorage.removeItem('rag_token')
          localStorage.removeItem('rag_user')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (credential) => {
    const res = await googleLogin(credential)
    const { token, user: userData } = res.data
    localStorage.setItem('rag_token', token)
    localStorage.setItem('rag_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const logout = () => {
    localStorage.removeItem('rag_token')
    localStorage.removeItem('rag_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
