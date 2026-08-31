'use client'

import { useState, useEffect } from 'react'

export function useCurrentUser() {
  const [user, setUser] = useState<string>('')

  useEffect(() => {
    let id = localStorage.getItem('currentUserName')
    if (!id) {
      id = `User-${Math.random().toString(36).slice(2, 6)}`
      localStorage.setItem('currentUserName', id)
    }
    setUser(id)
  }, [])

  return user
}