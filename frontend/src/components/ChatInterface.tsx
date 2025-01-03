import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  CircularProgress, 
  Avatar, 
  Divider,
  Tabs,
  Tab,
  IconButton
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ChatIcon from '@mui/icons-material/Chat';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import CloseIcon from '@mui/icons-material/Close';
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

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

interface AnalysisTab {
  id: string;
  label: string;
  content: string;
  type: 'report' | 'visualization';
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analysis-tabpanel-${index}`}
      aria-labelledby={`analysis-tab-${index}`}
      {...other}
      style={{ height: '100%', overflow: 'auto' }}
    >
      {value === index && (
        <Box sx={{ height: '100%', p: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const ChatInterface: React.FC<ChatInterfaceProps> = ({ stockName, onAnalysisComplete }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `欢迎使用 FinChat 智能股票分析助手！👋

我是您的私人投资AI助理，我会基于SWE-Agent自主编写代码获取金融数据，并结合真实数据分析给你相对专业的分析。

您可以在下方直接输入您感兴趣的股票相关问题，我会尽力为您提供专业的分析和建议。

或者您可以选择一个股票开始分析，我会通过SWE-Agent自主编写代码获取金融数据，并结合真实数据生成股票分析报告。

在右下方您可以看到SWE-Agent的思考过程，以及它生成的代码。
${stockName ? `目前已选择股票：${stockName}` : '请先选择一个股票开始分析。'}`
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState('');
  const [analysisTabs, setAnalysisTabs] = useState<AnalysisTab[]>([]);
  const [activeTab, setActiveTab] = useState(0);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAssistantMessage]);

  // 添加 ResizeObserver 警告处理
  useEffect(() => {
    // 防止 ResizeObserver 警告
    const resizeObserverError = (error: ErrorEvent) => {
      if (error.message === 'ResizeObserver loop completed with undelivered notifications.') {
        error.stopImmediatePropagation();
      }
    };

    window.addEventListener('error', resizeObserverError);
    
    return () => {
      window.removeEventListener('error', resizeObserverError);
    };
  }, []);

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

  // 处理新的分析报告
  const handleAnalysisComplete = (result: string, stockName: string) => {
    const newTab: AnalysisTab = {
      id: Date.now().toString(),
      label: `${stockName}分析报告`,
      content: result,
      type: 'report'
    };
    setAnalysisTabs(prev => [...prev, newTab]);
    setActiveTab(analysisTabs.length);
    onAnalysisComplete(result, stockName);
  };

  // 关闭标签页
  const handleCloseTab = (event: React.MouseEvent<HTMLElement>, tabId: string) => {
    event.stopPropagation();
    const tabIndex = analysisTabs.findIndex(tab => tab.id === tabId);
    const newTabs = analysisTabs.filter(tab => tab.id !== tabId);
    setAnalysisTabs(newTabs);
    
    if (activeTab === tabIndex) {
      setActiveTab(Math.max(0, tabIndex - 1));
    } else if (activeTab > tabIndex) {
      setActiveTab(activeTab - 1);
    }
  };

  return (
    <Box sx={{ 
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* 标题栏 */}
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        p: 2,
        borderBottom: 1,
        borderColor: 'divider',
        backgroundColor: 'background.paper'
      }}>
        <ChatIcon sx={{ 
          fontSize: 32,
          color: 'primary.main'
        }} />
        <Typography variant="h5" sx={{
          fontWeight: 600,
          color: 'text.primary',
          letterSpacing: 1
        }}>
          FinChat-智能股票分析助手
        </Typography>
      </Box>
      
      

      {/* 主要内容区域 */}
      <Box sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative'
      }}>
        

        {/* 聊天区域 */}
        <Box sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* 消息列表 */}
          <Box sx={{
            flex: 1,
            overflow: 'auto',
            padding: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2
          }}>
            {messages.map((message, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  gap: 2,
                  alignItems: 'flex-start'
                }}
              >
                <Avatar sx={{ bgcolor: message.role === 'assistant' ? 'primary.main' : 'secondary.main' }}>
                  {message.role === 'assistant' ? <SmartToyIcon /> : <PersonIcon />}
                </Avatar>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    flex: 1,
                    backgroundColor: message.role === 'assistant' ? 'background.paper' : 'action.hover',
                    maxWidth: 'calc(100% - 56px)',
                    overflow: 'hidden',
                    wordBreak: 'break-word'
                  }}
                >
                  <MessageContent content={message.content} />
                </Paper>
              </Box>
            ))}
            {currentAssistantMessage && (
              <Box
                sx={{
                  display: 'flex',
                  gap: 2,
                  alignItems: 'flex-start'
                }}
              >
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SmartToyIcon />
                </Avatar>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    flex: 1,
                    backgroundColor: 'background.paper',
                    maxWidth: 'calc(100% - 56px)',
                    overflow: 'hidden',
                    wordBreak: 'break-word'
                  }}
                >
                  <MessageContent content={currentAssistantMessage} />
                </Paper>
              </Box>
            )}
            {isLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                <CircularProgress size={24} />
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>

          {/* 输入区域 */}
          <Box sx={{
            borderTop: 1,
            borderColor: 'divider',
            backgroundColor: 'background.paper',
            p: 2
          }}>
            <StockAnalysis onAnalysisComplete={handleAnalysisComplete} />
            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入消息..."
                sx={{
                  '& .MuiInputBase-root': {
                    backgroundColor: 'background.paper'
                  }
                }}
              />
              <Button
                variant="contained"
                onClick={handleSend}
                disabled={isLoading || !inputMessage.trim()}
                sx={{ minWidth: 100 }}
              >
                {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
              </Button>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatInterface; 