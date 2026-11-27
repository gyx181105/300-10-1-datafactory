import { cn } from '@/lib/utils'

export function Card({
  className,
  ...props
}: React.ComponentProps<'div'>) {
  return <div className={cn('card-surface p-5', className)} {...props} />
}

export function CardTitle({
  className,
  ...props
}: React.ComponentProps<'h3'>) {
  return <h3 className={cn('text-[15px] font-semibold tracking-tight', className)} {...props} />
}

export function CardDesc({
  className,
  ...props
}: React.ComponentProps<'p'>) {
  return <p className={cn('mt-1 text-[12px] text-[var(--color-muted)]', className)} {...props} />
}
