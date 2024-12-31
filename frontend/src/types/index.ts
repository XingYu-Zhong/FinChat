export interface StockAnalysisRequest {
  stock_name: string;
  start_date: string;
  end_date: string;
  chat_model: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  stock_name: string;
  chat_history: ChatMessage[];
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  report?: string;
  response?: string;
  models?: Model[];
}

export interface Model {
  id: string;
  name: string;
} 