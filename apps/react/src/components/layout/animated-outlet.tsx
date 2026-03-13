import { useLocation, useMatches } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { useRef, type ReactNode } from "react";

interface AnimatedOutletProps {
  children: ReactNode;
}

export function AnimatedOutlet({ children }: AnimatedOutletProps) {
  const location = useLocation();
  const matches = useMatches();
  const prevPath = useRef(location.pathname);
  const direction = useRef(1);

  // Determine direction based on route depth
  const currentDepth = matches.length;
  if (location.pathname !== prevPath.current) {
    const prevDepth = prevPath.current.split("/").filter(Boolean).length;
    const nextDepth = location.pathname.split("/").filter(Boolean).length;
    direction.current = nextDepth >= prevDepth ? 1 : -1;
    prevPath.current = location.pathname;
  }

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: direction.current * 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: direction.current * -8 }}
        transition={{ duration: 0.15, ease: "easeInOut" }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
