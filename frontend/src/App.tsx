import React, { useState } from 'react';
import { Box, CssBaseline, Typography, Button } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import DownloadIcon from '@mui/icons-material/Download';
import StockAnalysis from './components/StockAnalysis';
import ChatInterface from './components/ChatInterface';
import LogViewer from './components/LogViewer';
import { ThemeProvider, createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#1e1e1e',
      paper: '#252526',
    },
    text: {
      primary: '#d4d4d4',
      secondary: '#808080',
    },
    primary: {
      main: '#569cd6',
    },
    secondary: {
      main: '#4ec9b0',
    },
  },
});

// 添加代码块组件的类型定义
interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

// 修改 MarkdownStyles 对象，移除重复的样式
const MarkdownStyles = {
  h1: {
    color: '#569cd6',
    borderBottom: '1px solid #424242',
    paddingBottom: '0.3em',
    marginTop: '1.5em',
    marginBottom: '0.5em',
  },
  h2: {
    color: '#569cd6',
    borderBottom: '1px solid #424242',
    paddingBottom: '0.3em',
    marginTop: '1.5em',
    marginBottom: '0.5em',
  },
  h3: {
    color: '#569cd6',
    marginTop: '1.5em',
    marginBottom: '0.5em',
  },
  'h4,h5,h6': {
    color: '#569cd6',
    marginTop: '1.2em',
    marginBottom: '0.5em',
  },
  ul: {
    paddingLeft: '2em',
    marginTop: '0.5em',
    marginBottom: '0.5em',
  },
  ol: {
    paddingLeft: '2em',
    marginTop: '0.5em',
    marginBottom: '0.5em',
  },
  li: {
    margin: '0.3em 0',
  },
  table: {
    borderCollapse: 'collapse',
    margin: '1em 0',
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
    padding: '1em',
    borderRadius: '4px',
    overflow: 'auto',
  },
  code: {
    backgroundColor: '#1e1e1e',
    padding: '0.2em 0.4em',
    borderRadius: '3px',
    fontSize: '85%',
  },
  blockquote: {
    borderLeft: '4px solid #424242',
    margin: '1em 0',
    padding: '0.5em 1em',
    backgroundColor: '#2d2d2d',
  },
  hr: {
    border: 'none',
    borderBottom: '1px solid #424242',
    margin: '1.5em 0',
  },
  a: {
    color: '#569cd6',
    textDecoration: 'none',
    '&:hover': {
      textDecoration: 'underline',
    },
  },
  img: {
    maxWidth: '100%',
    height: 'auto',
  },
};

function App() {
  const [analysisResult, setAnalysisResult] = useState<string>('');
  const [currentStock, setCurrentStock] = useState<string>('');

  const handleDownload = () => {
    if (analysisResult) {
      const blob = new Blob([analysisResult], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentStock}-分析报告.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        height: '100vh',
        display: 'flex',
        backgroundColor: '#1e1e1e',
      }}>
        {/* 左侧区域：聊天界面（包含研报生成） */}
        <Box sx={{ 
          flex: 3,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid #424242',
        }}>
          <Box sx={{ 
            flex: 1,
            overflow: 'hidden',
          }}>
            <ChatInterface 
              stockName={currentStock} 
              onAnalysisComplete={(result: string, stockName: string) => {
                setAnalysisResult(result || '');
                setCurrentStock(stockName);
              }}
            />
          </Box>
        </Box>

        {/* 右侧区域：分析报告和日志 */}
        <Box sx={{ 
          flex: 7,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}>
          {/* 分析报告展示区域 */}
          <Box sx={{ 
            flex: 7,
            overflow: 'auto',
            p: 2,
            borderBottom: '1px solid #424242',
          }}>
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              mb: 2 
            }}>
              <Typography variant="subtitle1" sx={{ color: '#569cd6' }}>
                分析报告
              </Typography>
              {analysisResult && (
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownload}
                  size="small"
                >
                  下载报告
                </Button>
              )}
            </Box>
            <Box sx={{
              backgroundColor: '#252526',
              p: 2,
              borderRadius: 1,
              fontFamily: 'Consolas, Monaco, monospace',
              fontSize: '14px',
              color: '#d4d4d4',
              '& *': { fontFamily: 'inherit' },
              ...MarkdownStyles,
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
                {analysisResult || '暂无分析报告'}
              </ReactMarkdown>
            </Box>
          </Box>

          {/* 日志区域 */}
          <Box sx={{ 
            flex: 3,
            overflow: 'hidden',
            backgroundColor: '#1e1e1e',
          }}>
            <LogViewer />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App; 