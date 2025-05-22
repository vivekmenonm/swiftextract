const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';

interface ApiCallOptions {
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE'; // Add other methods as needed
  headers?: Record<string, string>;
  body?: any;
}

interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

async function apiCall<T = any>(
  endpoint: string,
  options: ApiCallOptions = {}
): Promise<ApiResponse<T>> {
  const { method = 'POST', headers = {}, body = null } = options;

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const status = response.status;

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        // Not a JSON response
        return { error: response.statusText || 'An unknown error occurred', status };
      }
      return { error: errorData.message || errorData.error || 'An error occurred', status };
    }

    // Handle cases where response might be empty (e.g., 204 No Content)
    if (response.status === 204) {
        return { data: undefined, status };
    }

    let responseData: T;
    try {
        responseData = await response.json();
    } catch (e) {
        return { error: 'Failed to parse JSON response', status };
    }

    return { data: responseData, status };

  } catch (error) {
    console.error('API call failed:', error);
    if (error instanceof Error) {
        return { error: error.message || 'A network error occurred', status: 0 }; // status 0 for network/client-side errors
    }
    return { error: 'A network error occurred', status: 0 };
  }
}

export default apiCall;
