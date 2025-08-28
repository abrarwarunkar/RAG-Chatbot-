declare module 'axios-retry' {
  import { AxiosInstance, AxiosError } from 'axios';

  interface IAxiosRetryConfig {
    retries?: number;
    retryDelay?: (retryCount: number, error: AxiosError) => number;
    retryCondition?: (error: AxiosError) => boolean;
    shouldResetTimeout?: boolean;
  }

  interface IAxiosRetry {
    (axiosInstance: AxiosInstance, config?: IAxiosRetryConfig): void;
    isNetworkError(error: AxiosError): boolean;
  }

  const axiosRetry: IAxiosRetry;
  export = axiosRetry;
}