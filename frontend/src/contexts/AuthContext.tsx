import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabaseClient'

interface AuthContextType {
  session: Session | null
  loading: boolean
}

const AuthContext = createContext<AuthContextType>({ session: null, loading: true })

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session)
      if (event === 'SIGNED_IN') {
        console.log('[Auth] SIGNED_IN event, provider_refresh_token:', session?.provider_refresh_token ? 'present' : 'null')
        if (session?.provider_refresh_token) {
          const { error } = await supabase
            .from('users')
            .upsert({
              id: session.user.id,
              name: session.user.user_metadata?.full_name ?? session.user.email ?? '',
              google_refresh_token: session.provider_refresh_token,
            }, { onConflict: 'id' })
          console.log('[Auth] upsert result:', error ? error.message : 'success')
        }
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  return (
    <AuthContext.Provider value={{ session, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
