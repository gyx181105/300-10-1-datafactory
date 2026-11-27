import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-1.5 rounded-xl text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-[#1a1a1a] text-white hover:bg-black',
        outline: 'border border-[#e5e5e5] bg-white text-[#1a1a1a] hover:bg-[#fafafa]',
        ghost: 'text-[#525252] hover:bg-black/5',
        soft: 'bg-[#f0f0f0] text-[#1a1a1a] hover:bg-[#e8e8e8]',
      },
      size: {
        default: 'h-9 px-3.5',
        sm: 'h-8 px-3 text-xs',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'button'
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />
}
