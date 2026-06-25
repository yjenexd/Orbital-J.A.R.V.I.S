import { createClient } from '@supabase/supabase-js'

const rawSupabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

// Accept accidentally copied REST URLs (..../rest/v1) and normalize to project URL.
const supabaseUrl = rawSupabaseUrl?.replace(/\/rest\/v1\/?$/, '')

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env'
  )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
