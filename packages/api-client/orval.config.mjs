import { defineConfig } from "orval";

export default defineConfig({
  fastapi: {
    input: {
      target: `${process.env.APP_BACKEND_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000"}/openapi.json`,
    },
    output: {
      mode: "single",
      target: "src/generated.ts",
      schemas: "src/model",
      client: "react-query",
      httpClient: "axios",
      override: {
        mutator: {
          path: "src/custom-instance.ts",
          name: "customInstance",
        },
      },
    },
  },
});
