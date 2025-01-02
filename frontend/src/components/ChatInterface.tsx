import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress, Avatar, Divider } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ChatIcon from '@mui/icons-material/Chat';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import StockAnalysis from './StockAnalysis';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatInterfaceProps {
  stockName: string;
  onAnalysisComplete: (result: string, stockName: string) => void;
}

// 添加代码块组件的类型定义
interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ stockName, onAnalysisComplete }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `欢迎使用 FinChat 智能股票分析助手！👋

我是您的私人投资AI助理，我会基于SWE-Agent自主编写代码获取金融数据，并结合真实数据分析给你相对专业的分析。

您可以在下方直接输入您感兴趣的股票相关问题，我会尽力为您提供专业的分析和建议。

或者您可以点击右方按钮选择一个股票开始分析，我会通过SWE-Agent自主编写代码获取金融数据，并结合真实数据生成股票分析报告。

在右下方您可以看到SWE-Agent的思考过程，以及它生成的代码。
${stockName ? `目前已选择股票：${stockName}` : '请先选择一个股票开始分析。'}`
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAssistantMessage]);

  const handleSend = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);
    setCurrentAssistantMessage('');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          stock_name: stockName,
          chat_model: 'deepseek-chat'
        }),
      });

      if (!response.ok) {
        throw new Error('网络请求失败');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('无法读取响应流');
      }

      let fullMessage = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5));
              if (data.type === 'content') {
                fullMessage += data.content;
                setCurrentAssistantMessage(fullMessage);
              } else if (data.type === 'error') {
                throw new Error(data.error);
              } else if (data.type === 'done') {
                setMessages(prev => [...prev, { 
                  role: 'assistant', 
                  content: fullMessage 
                }]);
                setCurrentAssistantMessage('');
              }
            } catch (e) {
              console.error('解析消息出错:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('发送消息出错:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，处理消息时出现错误。' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  // Markdown样式
  const markdownStyles = {
    p: {
      margin: 0,
      lineHeight: 1.6,
    },
    'h1,h2,h3,h4,h5,h6': {
      color: '#569cd6',
      margin: '0.5em 0',
    },
    ul: {
      margin: '0.5em 0',
      paddingLeft: '1.5em',
    },
    ol: {
      margin: '0.5em 0',
      paddingLeft: '1.5em',
    },
    li: {
      margin: '0.2em 0',
    },
    table: {
      borderCollapse: 'collapse',
      margin: '0.5em 0',
      width: '100%',
    },
    th: {
      border: '1px solid #424242',
      padding: '0.5em',
      backgroundColor: '#2d2d2d',
    },
    td: {
      border: '1px solid #424242',
      padding: '0.5em',
    },
    pre: {
      backgroundColor: '#1e1e1e',
      padding: '0.5em',
      borderRadius: '4px',
      overflow: 'auto',
      margin: '0.5em 0',
    },
    code: {
      backgroundColor: '#1e1e1e',
      padding: '0.2em 0.4em',
      borderRadius: '3px',
      fontSize: '85%',
      fontFamily: 'Consolas, Monaco, monospace',
    },
    blockquote: {
      borderLeft: '4px solid #424242',
      margin: '0.5em 0',
      padding: '0.5em 1em',
      backgroundColor: '#2d2d2d',
    },
  };

  const MessageContent = ({ content }: { content: string }) => (
    <Box sx={{
      ...markdownStyles,
      '& *': { fontFamily: 'inherit' },
    }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          code: ({ node, inline, className, children, ...props }: CodeProps) => {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <pre className={className} style={{
                backgroundColor: '#1e1e1e',
                padding: '1em',
                borderRadius: '4px',
                overflow: 'auto',
              }}>
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      backgroundColor: '#1e1e1e',
      color: '#d4d4d4',
      p: 2,
      borderRadius: 1
    }}>
      {/* 标题头部 */}
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        pb: 2,
        borderBottom: '1px solid #424242',
        mb: 2
      }}>
        <ChatIcon sx={{ 
          fontSize: 32, 
          color: '#569cd6',
          backgroundColor: '#252526',
          p: 1,
          borderRadius: 1
        }} />
        <Typography variant="h5" sx={{
          fontWeight: 600,
          color: '#d4d4d4',
          letterSpacing: 1
        }}>
          FinChat-智能股票分析助手
        </Typography>
      </Box>
      
      {/* 消息显示区域 */}
      <Box sx={{ 
        flex: 1, 
        overflowY: 'auto', 
        mb: 2,
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: '#1e1e1e',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#424242',
          borderRadius: '4px',
        },
      }}>
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              mb: 2,
              display: 'flex',
              gap: 2,
              alignItems: 'flex-start',
            }}
          >
            <Avatar
              sx={{
                bgcolor: message.role === 'user' ? '#569cd6' : '#4ec9b0',
                width: 40,
                height: 40,
              }}
            >
              {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  color: message.role === 'user' ? '#569cd6' : '#4ec9b0',
                  mb: 0.5,
                  display: 'block'
                }}
              >
                {message.role === 'user' ? '用户' : 'AI助手'}
              </Typography>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  backgroundColor: message.role === 'user' ? '#252526' : '#2d2d2d',
                  color: '#d4d4d4',
                  borderLeft: '3px solid',
                  borderColor: message.role === 'user' ? '#569cd6' : '#4ec9b0',
                }}
              >
                <MessageContent content={message.content} />
              </Paper>
            </Box>
          </Box>
        ))}
        {currentAssistantMessage && (
          <Box sx={{ 
            mb: 2,
            display: 'flex',
            gap: 2,
            alignItems: 'flex-start',
          }}>
            <Avatar
              sx={{
                bgcolor: '#4ec9b0',
                width: 40,
                height: 40,
              }}
            >
              <SmartToyIcon />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography
                variant="caption"
                sx={{
                  color: '#4ec9b0',
                  mb: 0.5,
                  display: 'block'
                }}
              >
                AI助手
              </Typography>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  backgroundColor: '#2d2d2d',
                  color: '#d4d4d4',
                  borderLeft: '3px solid #4ec9b0',
                }}
              >
                <MessageContent content={currentAssistantMessage} />
              </Paper>
            </Box>
          </Box>
        )}
        {isLoading && !currentAssistantMessage && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={20} sx={{ color: '#569cd6' }} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* 底部输入区域 */}
      <Box sx={{ 
        backgroundColor: '#252526',
        p: 2,
        borderRadius: 1,
      }}>
        {/* 研报生成控制面板 */}
        <Box sx={{ mb: 2 }}>
          <StockAnalysis onAnalysisComplete={onAnalysisComplete} />
        </Box>
        
        <Divider sx={{ my: 2, borderColor: '#424242' }} />

        {/* 聊天输入框 */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入您的问题..."
            disabled={isLoading}
            sx={{
              backgroundColor: '#1e1e1e',
              '& .MuiOutlinedInput-root': {
                color: '#d4d4d4',
                '& fieldset': {
                  borderColor: '#424242',
                },
                '&:hover fieldset': {
                  borderColor: '#569cd6',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#569cd6',
                },
              },
              '& .MuiInputBase-input::placeholder': {
                color: '#808080',
              },
            }}
          />
          <Button
            variant="contained"
            onClick={handleSend}
            disabled={!inputMessage.trim() || isLoading}
            sx={{
              minWidth: 100,
              backgroundColor: '#0e639c',
              '&:hover': {
                backgroundColor: '#1177bb',
              },
              '&.Mui-disabled': {
                backgroundColor: '#2d2d2d',
                color: '#808080',
              },
            }}
          >
            {isLoading ? <CircularProgress size={24} sx={{ color: '#d4d4d4' }} /> : <SendIcon />}
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatInterface; 