import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

import { useAuthActions } from "@convex-dev/auth/react";
import { Authenticated, Unauthenticated } from "convex/react";
import { Button } from "./ui/button";
import { GoogleLogo, GitHubLogo } from "./logos";

import { ReactNode } from "react";
import { NuqsAdapter } from "nuqs/adapters/react"; // For plain React SPAs

import { Toaster } from "sonner";

export default function ProviderWrapper({ children }: { children: ReactNode }) {
  const { signIn } = useAuthActions();
  return (
    <main>
      <Authenticated>
        <NuqsAdapter>
          <QueryClientProvider client={queryClient}>
            <Toaster />
            {children}
          </QueryClientProvider>
        </NuqsAdapter>
      </Authenticated>
      <Unauthenticated>
        <div className="w-screen h-screen flex flex-col items-center justify-center gap-2">
          <Button
            variant="default"
            type="button"
            onClick={() => void signIn("google")}
          >
            <GoogleLogo className="mr-2 h-4 w-4" /> Sign in with Google
          </Button>
          <Button
            variant="default"
            type="button"
            onClick={() => void signIn("github")}
          >
            <GitHubLogo className="mr-2 h-4 w-4" /> Sign in with Github
          </Button>
        </div>
      </Unauthenticated>
    </main>
  );
}
