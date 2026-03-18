import {
  createFileRoute,
  isRedirect,
  redirect,
  useNavigate,
} from "@tanstack/react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff } from "lucide-react";
import {
  meApiV1AuthMeGet,
  useLoginApiV1AuthLoginPost,
} from "@packages/api-client";
import type { LoginRequest } from "@packages/api-client";
import { Button } from "@packages/ui/components/shadcn/button";
import { Input } from "@packages/ui/components/shadcn/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@packages/ui/components/shadcn/form";
import { loginSchema } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  beforeLoad: async () => {
    try {
      await meApiV1AuthMeGet();
      // eslint-disable-next-line @typescript-eslint/only-throw-error -- TanStack Router requires throwing redirect()
      throw redirect({ to: "/app" });
    } catch (e) {
      if (isRedirect(e)) throw e;
    }
  },
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<LoginRequest>({
    resolver: zodResolver(loginSchema),
    defaultValues: { password: "" },
  });

  const login = useLoginApiV1AuthLoginPost({
    mutation: {
      onSuccess: () => navigate({ to: "/app" }),
      onError: () =>
        form.setError("password", { message: "Invalid password" }),
    },
  });

  function onSubmit(values: LoginRequest) {
    login.mutate({ data: values });
  }

  return (
    <div className="flex h-full items-center justify-center bg-content-bg px-4">
      <motion.div
        className="w-full max-w-md"
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <div className="mb-6 flex flex-col items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-border">
            <img src="/logo.png" alt="Lead Alliances" className="h-8 w-8" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-text-primary">
            Lead Alliances
          </span>
        </div>

        <div className="rounded-2xl border border-border bg-card-bg p-10">
          <div className="mb-6 text-center">
            <h1 className="text-xl font-semibold text-text-primary">
              Welcome back
            </h1>
            <p className="mt-1 text-sm text-text-muted">
              Enter your team password to continue
            </p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-text-primary">
                      Password
                    </FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter team password"
                          autoFocus
                          className="h-11 border-border bg-white pr-10 text-text-primary"
                          {...field}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted transition-colors"
                          tabIndex={-1}
                        >
                          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button
                type="submit"
                className="h-11 w-full bg-brand text-white hover:opacity-90"
                disabled={login.isPending}
              >
                {login.isPending ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </Form>
        </div>

        <p className="mt-4 text-center text-xs text-text-muted">
          Lead Alliances Video Pipeline
        </p>
      </motion.div>
    </div>
  );
}
