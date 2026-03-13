import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  return (
    <div>
      <h1 className="mb-4 text-3xl font-bold">Home</h1>
      <p className="text-gray-600">Welcome to the React application.</p>
    </div>
  );
}
