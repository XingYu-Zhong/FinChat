import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, IconButton, Alert, Tooltip } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AutoScrollOnIcon from '@mui/icons-material/VerticalAlignBottom';
import AutoScrollOffIcon from '@mui/icons-material/VerticalAlignTop';
import { fetchLogs, clearLogs } from '../services/api';

const LogViewer: React.FC = () => {
  const [logs, setLogs] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const retryCount = useRef(0);
  const lastContentLength = useRef(0);

  const fetchLatestLogs = async () => {
    try {
      const response = await fetchLogs();
      if (response.status === 'success' && response.data) {
        // 只有当内容发生变化时才更新
        if (response.data.length !== lastContentLength.current) {
          setLogs(response.data);
          lastContentLength.current = response.data.length;
          setError('');
          retryCount.current = 0;
        }
      }
    } catch (error) {
      console.error('获取日志失败:', error);
      if (retryCount.current < 3) {
        retryCount.current += 1;
      } else {
        setError('获取日志失败，请检查日志文件是否存在');
      }
    }
  };

  const handleClearLogs = async () => {
    try {
      await clearLogs();
      setLogs('');
      lastContentLength.current = 0;
      setError('');
    } catch (error) {
      console.error('清除日志失败:', error);
      setError('清除日志失败');
    }
  };

  useEffect(() => {
    fetchLatestLogs();
    const interval = setInterval(fetchLatestLogs, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const toggleAutoScroll = () => {
    setAutoScroll(!autoScroll);
  };

  return (
    <Box sx={{ 
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#1e1e1e',
    }}>
      {/* 标题栏 */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        p: 1,
        borderBottom: '1px solid #424242',
      }}>
        <Typography variant="subtitle2" sx={{ color: '#d4d4d4' }}>
          SWE Agent流程日志
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={autoScroll ? "关闭自动滚动" : "开启自动滚动"}>
            <IconButton 
              size="small" 
              onClick={toggleAutoScroll}
              sx={{ 
                color: autoScroll ? '#4caf50' : '#808080',
                '&:hover': {
                  color: autoScroll ? '#81c784' : '#d4d4d4',
                }
              }}
            >
              {autoScroll ? <AutoScrollOnIcon fontSize="small" /> : <AutoScrollOffIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
          <IconButton 
            size="small" 
            onClick={handleClearLogs}
            sx={{ 
              color: '#808080',
              '&:hover': {
                color: '#d4d4d4',
              }
            }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* 错误提示 */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            m: 1,
            backgroundColor: '#320000',
            color: '#ff6b6b',
            '& .MuiAlert-icon': {
              color: '#ff6b6b',
            },
          }}
          onClose={() => setError('')}
        >
          {error}
        </Alert>
      )}

      {/* 日志内容区域 */}
      <Box
        ref={logContainerRef}
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 1,
          fontFamily: 'Consolas, Monaco, monospace',
          fontSize: '12px',
          lineHeight: '1.4',
          color: '#d4d4d4',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
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
        }}
      >
        {logs || '等待日志...'}
      </Box>
    </Box>
  );
};

export default LogViewer; 