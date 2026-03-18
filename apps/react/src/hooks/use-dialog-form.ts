import { useState, useCallback } from "react";

export function useDialogForm<T>(initialState: T) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<T>(initialState);

  const reset = useCallback(() => setState(initialState), [initialState]);

  const onOpenChange = useCallback(
    (v: boolean) => {
      setOpen(v);
      if (!v) reset();
    },
    [reset],
  );

  return { open, setOpen, state, setState, reset, onOpenChange };
}
