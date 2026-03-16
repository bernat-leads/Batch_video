import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@packages/ui/components/shadcn/alert-dialog";

interface ConfirmDeleteDialogProps {
  title?: string;
  description?: string;
  onConfirm: () => void;
  children: React.ReactNode;
}

/** Reusable destructive action confirmation dialog. Wraps the trigger element as a child. */
export function ConfirmDeleteDialog({
  title = "Delete?",
  description = "This action cannot be undone.",
  onConfirm,
  children,
}: ConfirmDeleteDialogProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-text-primary">
            {title}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-text-muted">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel className="border-border text-text-secondary">
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-status-error text-white"
          >
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
