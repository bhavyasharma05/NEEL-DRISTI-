import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { PaperAirplaneIcon, UserIcon, CpuChipIcon } from '@heroicons/react/24/outline';
import Sidebar from '../components/Sidebar';
import FloatingBubbles from '../components/FloatingBubbles';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
  chart?: {
    title: string;
    points: { x: number; y: number }[]; // x in [0,1], y in [0,1] normalized for SVG
    xLabels: string[]; // raw labels for tooltips (not implemented)
  };
}

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm Neel Drishti AI, your ocean data assistant. I can help you analyze ARGO float data, find patterns, and answer questions about ocean conditions. How can I assist you today?",
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Add session tracking
  const [sessionId] = useState(() => {
    // Generate or retrieve session ID
    let id = localStorage.getItem('chatbot_session_id');
    if (!id) {
      id = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('chatbot_session_id', id);
    }
    return id;
  });

  const sampleQuestions = [
    "Show salinity near the equator in last month",
    "What's the average temperature this year?",
    "Temperature trends in Pacific last 3 months",
    "Compare salinity last week vs this week",
    "Show data from past 30 days in Indian Ocean",
  ];

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: inputText,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuestion = inputText;
    setInputText('');
    setIsTyping(true);
    setIsStreaming(true);

    try {
      const botMessageId = messages.length + 2;
      const botMessage: Message = {
        id: botMessageId,
        text: '',
        isBot: true,
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, botMessage]);

      // Use streaming by default - POST with body + query params
      const streamUrl = `http://localhost:8000/ask?stream=true&session_id=${encodeURIComponent(sessionId)}`;

      console.log('🔄 Starting streaming request...');

      const response = await fetch(streamUrl, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: currentQuestion })
      });
      
      if (response.ok && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = '';
        let buffer = '';

        console.log('✅ Stream connected');

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            console.log('🏁 Stream complete');
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          
          // Process complete lines (SSE format: "data: ...\n\n")
          const lines = buffer.split('\n');
          // Keep the last incomplete line in buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;
                
                const data = JSON.parse(jsonStr);
                console.log('📨 Parsed data:', data);
                
                if (data.chunk && !data.done) {
                  accumulatedText += data.chunk;
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, text: accumulatedText }
                      : msg
                  ));
                }
                
                if (data.done) {
                  console.log('✅ Streaming done flag received');
                  setIsStreaming(false);
                  break;
                }
              } catch (e) {
                console.error('❌ Failed to parse SSE data:', e, 'Line:', line);
              }
            }
          }
        }
        
        // Ensure streaming flag is cleared
        setIsStreaming(false);
      } else {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

    } catch (error) {
      console.error('❌ Streaming error:', error);
      setIsStreaming(false);
      const errorMessage: Message = {
        id: messages.length + 2,
        text: "Sorry, I encountered an error while processing your request. Please try again.",
        isBot: true,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      setIsStreaming(false);
    }
  };

  const handleSampleQuestion = (question: string) => {
    setInputText(question);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-[#001f3f] text-white relative overflow-hidden">
      <FloatingBubbles />
      <Sidebar />
      
      <div className="ml-64 p-8 min-h-[calc(100vh-100px)] flex flex-col">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-4xl font-bold mb-2">Neel Drishti AI Assistant</h1>
          <p className="text-slate-400">Ask questions about ocean data and get AI-powered insights</p>
        </motion.div>

        {/* Sample Questions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <p className="text-sm text-slate-400 mb-3">Try these sample questions:</p>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSampleQuestion(question)}
                className="px-3 py-1 bg-white/10 text-sm rounded-full hover:bg-white/20 transition-colors border border-white/20"
              >
                {question}
              </button>
            ))}
            
            <div ref={messagesEndRef} />
          </div>
        </motion.div>

        {/* Chat Messages */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="flex-1 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20 p-6 overflow-hidden flex flex-col"
        >
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-2xl ${
                    message.isBot
                      ? 'bg-gradient-to-r from-[#00bcd4] to-[#00acc1] text-white'
                      : 'bg-white/20 text-white border border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {message.isBot ? (
                      <CpuChipIcon className="h-4 w-4" />
                    ) : (
                      <UserIcon className="h-4 w-4" />
                    )}
                    <span className="text-xs opacity-70">
                      {message.isBot ? 'Neel Drishti' : 'You'}
                    </span>
                    <span className="text-xs opacity-50">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.text}
                    {message.isBot && isStreaming && message.id === messages[messages.length - 1].id && (
                      <span className="inline-block w-2 h-4 ml-1 bg-white animate-pulse" />
                    )}
                  </p>
                  {message.isBot && message.chart && (
                    <div className="mt-3">
                      <p className="text-xs opacity-80 mb-1">{message.chart.title}</p>
                      <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-24">
                        <polyline
                          fill="none"
                          stroke="white"
                          strokeOpacity="0.9"
                          strokeWidth="1.5"
                          points={message.chart.points.map(p => `${p.x*100},${(1-p.y)*40}`).join(' ')}
                        />
                      </svg>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
            
            {isTyping && !isStreaming && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-gradient-to-r from-[#00bcd4] to-[#00acc1] text-white p-4 rounded-2xl max-w-[80%]">
                  <div className="flex items-center gap-2 mb-2">
                    <CpuChipIcon className="h-4 w-4" />
                    <span className="text-xs opacity-70">Neel Drishti</span>
                  </div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="flex gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask about ocean data patterns, temperature, salinity..."
              className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-400 focus:border-[#00bcd4] focus:outline-none"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isTyping}
              className="px-6 py-3 bg-gradient-to-r from-[#00bcd4] to-[#00acc1] text-white rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Chatbot;