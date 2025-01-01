const { createProxyMiddleware } = require('http-proxy-middleware');
const fs = require('fs');
const path = require('path');

const logFile = path.join(__dirname, '../../chat_logs.txt');

module.exports = function(app) {
  // API 代理
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://0.0.0.0:8000',
      changeOrigin: true,
    })
  );

  // 本地日志文件处理
  app.get('/local-logs', (req, res) => {
    try {
      const content = fs.readFileSync(logFile, 'utf-8');
      res.json({ content });
    } catch (error) {
      console.error('读取日志文件失败:', error);
      res.status(500).json({ error: '读取日志文件失败' });
    }
  });

  app.post('/local-logs/clear', (req, res) => {
    try {
      fs.writeFileSync(logFile, '', 'utf-8');
      res.json({ status: 'success' });
    } catch (error) {
      console.error('清除日志文件失败:', error);
      res.status(500).json({ error: '清除日志文件失败' });
    }
  });
}; 