import Axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from "axios";
import { env } from "./env";

/**
 * Shared Axios instance for API calls.
 * Base URL is read from PUBLIC_API_URL via the package env.
 */
export const AXIOS_INSTANCE = Axios.create({
  baseURL: env.PUBLIC_API_URL,
  withCredentials: true,
});

export const customInstance = <T>(
  config: AxiosRequestConfig,
  options?: AxiosRequestConfig,
): Promise<T> => {
  return AXIOS_INSTANCE({ ...config, ...options }).then((res: AxiosResponse<T>) => res.data);
};

export type ErrorType<Error> = AxiosError<Error>;
export type BodyType<BodyData> = BodyData;
