import Axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from "axios";
import { env } from "./env";

/**
 * Shared Axios instance for API calls.
 * Base URL is read from PUBLIC_API_URL via the package env.
 */
export const AXIOS_INSTANCE = Axios.create({
  baseURL: env.PUBLIC_API_URL,
  withCredentials: true,
  timeout: 30_000,
  paramsSerializer: {
    // FastAPI expects repeated keys for arrays: ?video_id=a&video_id=b
    // Axios defaults to brackets: ?video_id[]=a&video_id[]=b
    indexes: null,
  },
});

AXIOS_INSTANCE.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && window.location.pathname !== "/login") {
      window.location.href = "/login";
      return new Promise(() => {});
    }
    return Promise.reject(error);
  },
);

export const customInstance = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig,
): Promise<T> => {
  return AXIOS_INSTANCE({ ...config, ...options }).then((res: AxiosResponse<T>) => res.data);
};

export type ErrorType<Error> = AxiosError<Error>;
export type BodyType<BodyData> = BodyData;
