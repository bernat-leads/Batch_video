import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/about")({
  component: AboutPage,
});

function AboutPage() {
  return (
    <div>
      <h1 className="mb-4 text-3xl font-bold">About</h1>
      <p className="text-gray-600">This is a React application built with TanStack Router, Vite, and Tailwind CSS.</p>
    </div>
  );
}
