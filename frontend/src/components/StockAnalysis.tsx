import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  SelectChangeEvent,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import { analyzeStock, getAvailableModels } from '../services/api';
import { Model } from '../types';

interface StockAnalysisProps {
  onAnalysisComplete: (result: string, stockName: string) => void;
}

const StockAnalysis: React.FC<StockAnalysisProps> = ({ onAnalysisComplete }) => {
  const [stockName, setStockName] = useState<string>('贵州茅台');
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs().subtract(30, 'day'));
  const [endDate, setEndDate] = useState<Dayjs | null>(dayjs().subtract(1, 'day'));
  const [chatModel, setChatModel] = useState<string>('deepseek-chat');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [models, setModels] = useState<Model[]>([]);

  useEffect(() => {
    const fetchModels = async () => {
      const response = await getAvailableModels();
      if (response.status === 'success' && response.data) {
        setModels(response.data);
      }
    };
    fetchModels();
  }, []);

  const handleAnalysis = async () => {
    if (!stockName || !startDate || !endDate) {
      setError('请填写完整的分析信息');
      return;
    }

    setLoading(true);
    setError('');

    const response = await analyzeStock({
      stock_name: stockName,
      start_date: startDate.format('YYYY-MM-DD'),
      end_date: endDate.format('YYYY-MM-DD'),
      chat_model: chatModel,
    });

    if (response.status === 'success' && response.data) {
      onAnalysisComplete(response.data, stockName);
    } else {
      setError(response.error || '分析失败，请重试');
    }

    setLoading(false);
  };

  const handleModelChange = (event: SelectChangeEvent) => {
    setChatModel(event.target.value);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <FormControl fullWidth>
          <InputLabel>选择LLM模型</InputLabel>
          <Select
            value={chatModel}
            label="选择LLM模型"
            onChange={handleModelChange}
          >
            {models.map((model) => (
              <MenuItem key={model.id} value={model.id}>
                {model.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="股票名称"
          value={stockName}
          onChange={(e) => setStockName(e.target.value)}
        />

        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <DatePicker
              label="开始日期"
              value={startDate}
              onChange={(newValue) => setStartDate(newValue)}
              sx={{ flex: 1 }}
            />
            <DatePicker
              label="结束日期"
              value={endDate}
              onChange={(newValue) => setEndDate(newValue)}
              sx={{ flex: 1 }}
            />
          </Box>
        </LocalizationProvider>

        <Button
          variant="contained"
          onClick={handleAnalysis}
          disabled={loading}
          sx={{ mt: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : '开始分析'}
        </Button>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Box>
    </Box>
  );
};

export default StockAnalysis; 