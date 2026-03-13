import { useNavigate } from "@tanstack/react-router";
import { useLogoutApiV1AuthLogoutPost } from "@packages/api-client";

export function LogoutButton() {
  const navigate = useNavigate();

  const logout = useLogoutApiV1AuthLogoutPost({
    mutation: {
      onSuccess: () => navigate({ to: "/login" }),
    },
  });

  return (
    <button
      onClick={() => logout.mutate()}
      className="text-sm text-gray-500 hover:text-gray-700"
    >
      Logout
    </button>
  );
}
