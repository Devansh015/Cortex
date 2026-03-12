'use client'

import { useState, useRef, useEffect } from 'react'
import { useProfile } from '@/context/ProfileContext'
import { sendChatMessage } from '@/lib/api'
import type { ChatMessage } from '@/types/api'

interface ChatBotProps {
  onPanelToggle?: (open: boolean) => void
}

export default function ChatBot({ onPanelToggle }: ChatBotProps) {
  const { profile } = useProfile()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const hasMessages = messages.length > 0 || isTyping

  useEffect(() => {
    onPanelToggle?.(hasMessages)
  }, [hasMessages, onPanelToggle])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = async (text?: string) => {
    const message = text ?? input.trim()
    if (!message || !profile?.user_id || isTyping) return

    const userMsg: ChatMessage = { role: 'user', content: message }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)
    setSuggestions([])

    try {
      const history = [...messages, userMsg].slice(-10)
      const data = await sendChatMessage(profile.user_id, message, history)
      const assistantMsg: ChatMessage = { role: 'assistant', content: data.reply }
      setMessages(prev => [...prev, assistantMsg])
      if (data.suggestions?.length) setSuggestions(data.suggestions)
    } catch {
      const errorMsg: ChatMessage = { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* Right-side message panel - responsive: bottom sheet on mobile, side panel on desktop */}
      <div
        className={`fixed z-40 flex flex-col bg-black/90 sm:bg-black/70 backdrop-blur-xl border-white/10 transition-all duration-300 
          inset-x-0 bottom-0 h-[85vh] rounded-t-2xl border-t sm:border-l sm:border-t-0 sm:rounded-none
          sm:top-0 sm:right-0 sm:left-auto sm:h-full sm:w-[320px] md:w-[380px]
          ${hasMessages ? 'translate-y-0 sm:translate-y-0 sm:translate-x-0' : 'translate-y-full sm:translate-y-0 sm:translate-x-full'}
        `}
      >
        {/* Mobile drag handle */}
        <div className="sm:hidden w-12 h-1 bg-white/30 rounded-full mx-auto mt-2 mb-1" />
        
        {/* Header */}
        <div className="px-4 sm:px-5 py-3 sm:py-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold text-sm">CORTEX AI</h3>
            <p className="text-white/40 text-xs mt-0.5">Skills &amp; learning insights</p>
          </div>
          <button
            onClick={() => { setMessages([]); setSuggestions([]) }}
            className="text-white/30 hover:text-white/60 transition-colors"
            title="Clear chat"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-2 sm:py-3 space-y-2 sm:space-y-3">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] px-3 sm:px-3.5 py-2 sm:py-2.5 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-blue-600/80 text-white rounded-br-md'
                    : 'bg-white/10 text-white/90 rounded-bl-md'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white/10 px-4 py-3 rounded-2xl rounded-bl-md flex gap-1.5">
                <span className="w-2 h-2 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-white/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        {suggestions.length > 0 && (
          <div className="px-3 sm:px-4 pb-2 sm:pb-3 flex flex-wrap justify-center gap-1 sm:gap-1.5 border-t border-white/5 pt-2 sm:pt-3">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSend(s)}
                className="px-2.5 sm:px-3 py-1 sm:py-1.5 text-xs bg-white/10 hover:bg-white/20 border border-white/10 rounded-full text-white/70 hover:text-white transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bottom-center chat bar */}
      <div className="fixed bottom-4 sm:bottom-10 left-1/2 -translate-x-1/2 z-50 w-full max-w-[calc(100%-2rem)] sm:max-w-[600px]">
        <div className="flex items-center gap-2 bg-black/90 sm:bg-black/60 backdrop-blur-xl border border-white/20 rounded-full sm:rounded-2xl px-4 py-2.5 sm:py-3 shadow-lg shadow-black/50">
          <svg className="w-5 h-5 text-white/40 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={profile ? 'Ask about your skills...' : 'Upload a project first'}
            disabled={!profile || isTyping}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/40 outline-none disabled:opacity-40 min-w-0"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || !profile || isTyping}
            className="w-9 h-9 flex items-center justify-center rounded-full bg-white hover:bg-white/90 text-black transition-colors disabled:opacity-30 disabled:hover:bg-white shrink-0"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </>
  )
}
