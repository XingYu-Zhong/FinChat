import axios, { AxiosError } from 'axios';
import { StockAnalysisRequest, ChatRequest, Model } from '../types';

// API 响应类型定义
interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
}

// 后端响应类型定义
interface BackendResponse<T> {
  status: string;
  data?: T;
  report?: string;
  response?: string;
  models?: T;
  logs?: T;
}

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 3000000, // 30秒超时
});

// 错误处理函数
const handleApiError = (error: any): ApiResponse<any> => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    if (axiosError.response) {
      return {
        status: 'error',
        error: `请求失败: ${axiosError.response.status} - ${axiosError.response.statusText}`,
      };
    } else if (axiosError.request) {
      return {
        status: 'error',
        error: '无法连接到服务器，请检查网络连接',
      };
    }
  }
  return {
    status: 'error',
    error: error instanceof Error ? error.message : '未知错误',
  };
};

export const analyzeStock = async (params: StockAnalysisRequest): Promise<ApiResponse<string>> => {
  try {
    const response = await api.post<BackendResponse<string>>('/analyze', params);
    return {
      status: 'success',
      data: response.data.data || response.data.report || '',
    };
  } catch (error) {
    return handleApiError(error);
  }
};

export const sendChatMessage = async (params: ChatRequest): Promise<ApiResponse<string>> => {
  try {
    const response = await api.post<BackendResponse<string>>('/chat', params);
    return {
      status: 'success',
      data: response.data.data || response.data.response || '',
    };
  } catch (error) {
    return handleApiError(error);
  }
};

export const getAvailableModels = async (): Promise<ApiResponse<Model[]>> => {
  try {
    const response = await api.get<BackendResponse<Model[]>>('/models');
    return {
      status: 'success',
      data: response.data.data || response.data.models || [],
    };
  } catch (error) {
    return handleApiError(error);
  }
};

export async function fetchLogs(): Promise<ApiResponse<string>> {
  try {
    const response = await fetch('/local-logs');
    if (!response.ok) {
      throw new Error('获取日志失败');
    }
    const data = await response.json();
    return {
      status: 'success',
      data: data.content || ''
    };
  } catch (error) {
    console.error('获取日志失败:', error);
    return {
      status: 'error',
      error: '获取日志失败'
    };
  }
}

export async function clearLogs(): Promise<ApiResponse<null>> {
  try {
    const response = await fetch('/local-logs/clear', {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error('清除日志失败');
    }
    return {
      status: 'success'
    };
  } catch (error) {
    console.error('清除日志失败:', error);
    return {
      status: 'error',
      error: '清除日志失败'
    };
  }
} 