import { useEffect, useRef, useState } from 'react'
import './App.css'
import CompanyData from './components/CompanyData'

type AnswerType = 'text' | 'table' | 'graph'
type AppTab = 'chat' | 'company-data'

type TableData = {
  columns: string[]
  rows: string[][]
}

type GraphData = {
  labels: string[]
  values: number[]
  unit: string
}

type Message = {
  question: string
  answer: string
  answerType: AnswerType
  table?: TableData
  graph?: GraphData
  sources: string[]
}

type Conversation = {
  id: string
  title: string
  messages: Message[]
}

const loadHistory = (): Conversation[] => {
  try {
    const savedHistory = localStorage.getItem('companyBrainHistory')
    if (!savedHistory) return []

    const parsedHistory = JSON.parse(savedHistory)
    return Array.isArray(parsedHistory) ? parsedHistory : []
  } catch {
    return []
  }
}

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [history, setHistory] = useState<Conversation[]>(loadHistory)
  const [isLoading, setIsLoading] = useState(false)
  const [openSources, setOpenSources] = useState<number | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const [activeTab, setActiveTab] = useState<AppTab>('chat')

  const conversationRef = useRef<HTMLDivElement>(null)
  const currentConversationId = useRef<string | null>(null)

  const generateAnswer = (currentQuestion: string) => {
    const lowerQuestion = currentQuestion.toLowerCase()

    if (
      lowerQuestion.includes('overdue invoice') ||
      lowerQuestion.includes('overdue invoices')
    ) {
      return {
        answer:
          'There are 14 customers with overdue invoices totaling ₹428,500.',
        answerType: 'text' as AnswerType,
        sources: ['Invoice Records', 'Accounts Receivable'],
      }
    }

    if (
      lowerQuestion.includes('delayed shipment') ||
      lowerQuestion.includes('delayed shipments')
    ) {
      return {
        answer:
          'There are currently 8 delayed shipments. The longest delay is 6 days.',
        answerType: 'text' as AnswerType,
        sources: ['Shipment Records', 'Logistics Data'],
      }
    }

    if (lowerQuestion.includes('refund process')) {
      return {
        answer:
          'The refund process requires verifying the order, checking refund eligibility, and submitting the refund request.',
        answerType: 'text' as AnswerType,
        sources: ['Refund Policy', 'Customer Service SOP'],
      }
    }

    if (
      lowerQuestion.includes('recent order') ||
      lowerQuestion.includes('recent orders')
    ) {
      return {
        answer:
          'There are 27 recent orders. The latest order was placed today.',
        answerType: 'text' as AnswerType,
        sources: ['Order Records'],
      }
    }

    return {
      answer:
        'I found your question. Once connected to the company data, I can provide a relevant answer with supporting information.',
      answerType: 'text' as AnswerType,
      sources: [],
    }
  }

  const getTableForMessage = (message: Message): TableData | null => {
    const currentQuestion = message.question.toLowerCase()

    if (
      currentQuestion.includes('delayed shipment') ||
      currentQuestion.includes('delayed shipments')
    ) {
      return {
        columns: ['Shipment', 'Status', 'Delay'],
        rows: [
          ['SH-1024', 'Delayed', '6 days'],
          ['SH-1027', 'Delayed', '4 days'],
          ['SH-1031', 'Delayed', '3 days'],
          ['SH-1038', 'Delayed', '2 days'],
        ],
      }
    }

    if (
      currentQuestion.includes('overdue invoice') ||
      currentQuestion.includes('overdue invoices')
    ) {
      return {
        columns: ['Customer', 'Invoice', 'Amount', 'Status'],
        rows: [
          ['ABC Ltd', 'INV-1024', '₹45,000', 'Overdue'],
          ['XYZ Pvt Ltd', 'INV-1041', '₹32,500', 'Overdue'],
          ['Global Traders', 'INV-1052', '₹28,000', 'Overdue'],
          ['Prime Solutions', 'INV-1060', '₹21,500', 'Overdue'],
        ],
      }
    }

    if (
      currentQuestion.includes('recent order') ||
      currentQuestion.includes('recent orders') ||
      currentQuestion.includes('order graph') ||
      currentQuestion.includes('orders graph')
    ) {
      return {
        columns: ['Order', 'Customer', 'Status'],
        rows: [
          ['ORD-2041', 'ABC Ltd', 'Processing'],
          ['ORD-2042', 'XYZ Pvt Ltd', 'Shipped'],
          ['ORD-2043', 'Global Traders', 'Processing'],
          ['ORD-2044', 'Prime Solutions', 'Delivered'],
        ],
      }
    }

    return null
  }

  const getGraphForQuestion = (
    currentQuestion: string
  ): GraphData | null => {
    const text = currentQuestion.toLowerCase()

    if (
      text.includes('delayed shipment') ||
      text.includes('delayed shipments') ||
      text.includes('shipment graph') ||
      text.includes('shipments graph') ||
      text.includes('graph of shipments')
    ) {
      return {
        labels: ['SH-1024', 'SH-1027', 'SH-1031', 'SH-1038'],
        values: [6, 4, 3, 2],
        unit: 'days',
      }
    }

    if (
      text.includes('overdue invoice') ||
      text.includes('overdue invoices') ||
      text.includes('invoice graph') ||
      text.includes('invoices graph') ||
      text.includes('graph of invoices')
    ) {
      return {
        labels: ['ABC Ltd', 'XYZ Pvt Ltd', 'Global Traders', 'Prime Solutions'],
        values: [45000, 32500, 28000, 21500],
        unit: '₹',
      }
    }

    if (
      text.includes('recent order') ||
      text.includes('recent orders') ||
      text.includes('order graph') ||
      text.includes('orders graph') ||
      text.includes('graph of orders') ||
      text.includes('graph for orders') ||
      text.includes('orders as a graph') ||
      text.includes('order as a graph')
    ) {
      return {
        labels: ['Processing', 'Shipped', 'Delivered'],
        values: [2, 1, 1],
        unit: 'orders',
      }
    }

    return null
  }

  const isTableRequest = (currentQuestion: string) => {
    const text = currentQuestion.toLowerCase()
    return (
      text.includes('show me table') ||
      text.includes('show table') ||
      text.includes('in a table') ||
      text.includes('as a table') ||
      text.includes('display table')
    )
  }

  const isGraphRequest = (currentQuestion: string) => {
    const text = currentQuestion.toLowerCase()
    return (
      text.includes('graph') ||
      text.includes('chart') ||
      text.includes('plot') ||
      text.includes('visualize')
    )
  }

  useEffect(() => {
    try {
      localStorage.setItem('companyBrainHistory', JSON.stringify(history))
    } catch {
      // Keep the app usable if browser storage is unavailable.
    }
  }, [history])

  useEffect(() => {
    const conversation = conversationRef.current
    if (conversation) {
      conversation.scrollTop = conversation.scrollHeight
    }
  }, [messages, isLoading])

  const saveMessageToHistory = (message: Message) => {
    if (currentConversationId.current === null) {
      const newConversationId = crypto.randomUUID()
      currentConversationId.current = newConversationId

      const newConversation: Conversation = {
        id: newConversationId,
        title: message.question,
        messages: [message],
      }

      setHistory((previousHistory) => [
        newConversation,
        ...previousHistory,
      ])
      return
    }

    const conversationId = currentConversationId.current

    setHistory((previousHistory) =>
      previousHistory.map((conversation) =>
        conversation.id !== conversationId
          ? conversation
          : {
              ...conversation,
              messages: [...conversation.messages, message],
            }
      )
    )
  }

  const processQuestion = (currentQuestion: string) => {
    setQuestion('')
    setIsLoading(true)
    setOpenSources(null)
    setShowHistory(false)

    window.setTimeout(() => {
      let newMessage: Message

      if (isGraphRequest(currentQuestion)) {
        let graph = getGraphForQuestion(currentQuestion)
        let sourceMessage: Message | null = null

        if (!graph && messages.length > 0) {
          const lastMessage = messages[messages.length - 1]
          graph = getGraphForQuestion(lastMessage.question)
          sourceMessage = lastMessage
        }

        if (graph) {
          newMessage = {
            question: currentQuestion,
            answer: 'Here is the requested graph.',
            answerType: 'graph',
            graph,
            sources:
              sourceMessage?.sources ??
              generateAnswer(currentQuestion).sources,
          }
        } else {
          newMessage = {
            question: currentQuestion,
            answer: 'I could not find enough data to create that graph.',
            answerType: 'text',
            sources: [],
          }
        }
      } else if (isTableRequest(currentQuestion)) {
        let table = getTableForMessage({
          question: currentQuestion,
          answer: '',
          answerType: 'text',
          sources: [],
        })

        let sourceMessage: Message | null = null

        if (!table && messages.length > 0) {
          const lastMessage = messages[messages.length - 1]
          table = getTableForMessage(lastMessage)
          sourceMessage = lastMessage
        }

        if (table) {
          newMessage = {
            question: currentQuestion,
            answer: 'Here is the information in table format.',
            answerType: 'table',
            table,
            sources: sourceMessage?.sources ?? [],
          }
        } else {
          newMessage = {
            question: currentQuestion,
            answer: 'I could not find enough data to create that table.',
            answerType: 'text',
            sources: [],
          }
        }
      } else {
        const result = generateAnswer(currentQuestion)
        newMessage = {
          question: currentQuestion,
          answer: result.answer,
          answerType: result.answerType,
          sources: result.sources,
        }
      }

      setMessages((previousMessages) => [...previousMessages, newMessage])
      saveMessageToHistory(newMessage)
      setIsLoading(false)
    }, 1200)
  }

  const handleAsk = () => {
    if (!question.trim() || isLoading) return
    processQuestion(question.trim())
  }

  const handleSuggestion = (suggestion: string) => {
    if (isLoading) return
    processQuestion(suggestion)
  }

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === 'Enter') {
      handleAsk()
    }
  }

  const toggleSources = (index: number) => {
    setOpenSources((previousIndex) =>
      previousIndex === index ? null : index
    )
  }

  const handleNewConversation = () => {
    currentConversationId.current = null
    setMessages([])
    setQuestion('')
    setIsLoading(false)
    setOpenSources(null)
    setShowHistory(false)
  }

  const handleHistoryClick = (conversation: Conversation) => {
    currentConversationId.current = conversation.id
    setMessages(conversation.messages)
    setQuestion('')
    setOpenSources(null)
    setShowHistory(false)
    setActiveTab('chat')
  }

  const handleClearHistory = () => {
    const confirmed = window.confirm(
      'Are you sure you want to clear all conversation history?'
    )

    if (!confirmed) return

    currentConversationId.current = null
    setHistory([])
    localStorage.removeItem('companyBrainHistory')
  }

  const hasConversation = messages.length > 0 || isLoading

  const tabStyle = (tab: AppTab): React.CSSProperties => ({
    padding: '9px 15px',
    border: '1px solid',
    borderColor: activeTab === tab ? '#4f46e5' : '#e5e7eb',
    borderRadius: '9px',
    background: activeTab === tab ? '#eef2ff' : '#ffffff',
    color: activeTab === tab ? '#4338ca' : '#4b5563',
    fontSize: '14px',
    fontWeight: activeTab === tab ? 600 : 500,
    cursor: 'pointer',
  })

  return (
    <div
      className={`app ${
        activeTab === 'chat' && hasConversation
          ? 'chat-mode'
          : 'home-mode'
      }`}
    >
      <header className="header">
        <h1>Company Brain</h1>

        <nav
          aria-label="Main navigation"
          className="app-tabs"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginLeft: 'auto',
            marginRight: '16px',
          }}
        >
          <button
            type="button"
            style={tabStyle('chat')}
            aria-current={activeTab === 'chat' ? 'page' : undefined}
            onClick={() => {
              setActiveTab('chat')
              setShowHistory(false)
            }}
          >
            Chat
          </button>

          <button
            type="button"
            style={tabStyle('company-data')}
            aria-current={activeTab === 'company-data' ? 'page' : undefined}
            onClick={() => {
              setActiveTab('company-data')
              setShowHistory(false)
            }}
          >
            Company Data
          </button>
        </nav>

        {activeTab === 'chat' && (
          <div className="header-actions">
            <button
              className="history-button"
              onClick={() => setShowHistory(!showHistory)}
            >
              History
            </button>

            {hasConversation && (
              <button
                className="new-conversation"
                onClick={handleNewConversation}
              >
                New conversation
              </button>
            )}
          </div>
        )}
      </header>

      {activeTab === 'chat' && showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <div>
              <h3>Conversation History</h3>
              <p>
                {history.length} conversation
                {history.length === 1 ? '' : 's'}
              </p>
            </div>

            <div className="history-header-actions">
              {history.length > 0 && (
                <button
                  className="clear-history-button"
                  onClick={handleClearHistory}
                >
                  Clear
                </button>
              )}

              <button onClick={() => setShowHistory(false)}>
                Close
              </button>
            </div>
          </div>

          {history.length === 0 ? (
            <p className="empty-history">
              No previous conversations yet.
            </p>
          ) : (
            <div className="history-list">
              {history.map((conversation) => (
                <button
                  className="history-item"
                  key={conversation.id}
                  onClick={() => handleHistoryClick(conversation)}
                >
                  <span className="history-title">
                    {conversation.title}
                  </span>

                  <span className="history-count">
                    {conversation.messages.length}{' '}
                    {conversation.messages.length === 1
                      ? 'message'
                      : 'messages'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'company-data' ? (
        <CompanyData />
      ) : (
        <main className="main">
          {!hasConversation && (
            <>
              <h2>Your company's AI assistant</h2>
              <p>
                Ask questions about your company's data, processes,
                and documents.
              </p>
            </>
          )}

          <div className="conversation" ref={conversationRef}>
            {messages.map((message, index) => (
              <div className="message" key={index}>
                <div className="user-message">
                  <strong>You</strong>
                  <p>{message.question}</p>
                </div>

                <div className="ai-message">
                  <strong>Company Brain</strong>
                  <p>{message.answer}</p>

                  {message.answerType === 'table' && message.table && (
                    <div className="result-table-wrapper">
                      <table className="result-table">
                        <thead>
                          <tr>
                            {message.table.columns.map((column) => (
                              <th key={column}>{column}</th>
                            ))}
                          </tr>
                        </thead>

                        <tbody>
                          {message.table.rows.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                              {row.map((cell, cellIndex) => (
                                <td key={cellIndex}>{cell}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {message.answerType === 'graph' && message.graph && (
                    <div className="result-graph">
                      {message.graph.labels.map((label, graphIndex) => {
                        const value = message.graph!.values[graphIndex]
                        const maxValue = Math.max(...message.graph!.values)
                        const height =
                          maxValue === 0 ? 0 : (value / maxValue) * 100

                        return (
                          <div className="graph-column" key={label}>
                            <div className="graph-value">
                              {message.graph!.unit === '₹'
                                ? `₹${value.toLocaleString('en-IN')}`
                                : `${value} ${message.graph!.unit}`}
                            </div>

                            <div className="graph-bar-area">
                              <div
                                className="graph-bar"
                                style={{ height: `${height}%` }}
                              />
                            </div>

                            <div className="graph-label">{label}</div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {message.sources.length > 0 && (
                    <div className="sources">
                      <button
                        className="sources-toggle"
                        onClick={() => toggleSources(index)}
                      >
                        <span>Sources · {message.sources.length}</span>
                        <span>{openSources === index ? '▲' : '▼'}</span>
                      </button>

                      {openSources === index && (
                        <div className="source-list">
                          {message.sources.map((source) => (
                            <span className="source" key={source}>
                              {source}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message">
                <div className="ai-message thinking-message">
                  <strong>Company Brain</strong>

                  <div className="thinking">
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span>Thinking</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="question-box">
            <input
              type="text"
              placeholder={
                hasConversation
                  ? 'Ask another question about your company...'
                  : 'Ask anything about your company...'
              }
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />

            <button onClick={handleAsk} disabled={isLoading}>
              {isLoading ? '...' : 'Ask'}
            </button>
          </div>

          {!hasConversation && (
            <div className="suggestions">
              <h3>Try asking</h3>

              <button
                onClick={() =>
                  handleSuggestion(
                    'Which customers have overdue invoices?'
                  )
                }
              >
                Which customers have overdue invoices?
              </button>

              <button
                onClick={() => handleSuggestion('Show delayed shipments')}
              >
                Show delayed shipments
              </button>

              <button
                onClick={() =>
                  handleSuggestion('What is the refund process?')
                }
              >
                What is the refund process?
              </button>

              <button
                onClick={() => handleSuggestion('Show recent orders')}
              >
                Show recent orders
              </button>
            </div>
          )}
        </main>
      )}
    </div>
  )
}

export default App
