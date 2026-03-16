import { Outlet, useLocation } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";

/** Route outlet with fade-in transition on navigation via Framer Motion. */
export function AnimatedOutlet() {
  const location = useLocation();

  return (
    <AnimatePresence mode="popLayout" initial={false}>
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <Outlet />
      </motion.div>
    </AnimatePresence>
  );
}
