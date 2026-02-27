import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[var(--primary)] text-[var(--primary-foreground)]",
        secondary: "bg-[var(--secondary)] text-[var(--secondary-foreground)]",
        destructive: "bg-[var(--destructive)] text-white",
        outline: "border border-[var(--border)] text-[var(--foreground)]",
        low: "bg-[rgba(223,168,116,0.2)] text-[#d58d49]",
        medium: "bg-[rgba(86,136,224,0.15)] text-[#5688e0]",
        high: "bg-[rgba(216,114,125,0.1)] text-[#d8727d]",
        critical: "bg-[rgba(231,76,60,0.15)] text-[#e74c3c]",
        completed: "bg-[rgba(131,194,157,0.2)] text-[#68b266]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
