import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://wmejplohqpdupugeluxx.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndtZWpwbG9ocXBkdXB1Z2VsdXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNTg0NzgsImV4cCI6MjEwMjczNDQ3OH0.Pqf79ne64__1CdsX1DxFxDr6YD50g_cpXOwejZNOe_4';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storageKey: 'cmlre_auth_supabase_session'
  }
});
