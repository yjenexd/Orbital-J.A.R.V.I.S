export function validateGroqKeyFormat(key: string): string | null {
  if (!key.trim() || !key.startsWith('gsk_')) {
    return 'Key must start with "gsk_". Get yours at console.groq.com.'
  }
  return null
}
