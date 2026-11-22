import React from 'react'
import { cn } from '@/lib/utils'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'outline' | 'terracotta' | 'sage' | 'danger' | 'neutral'
}

export function Badge({ children, className, variant = 'default', ...props }: BadgeProps) {
  const normalizedVariant = variant === 'danger' ? 'error' : variant === 'neutral' ? 'default' : variant
  const variantStyles = {
    default: 'bg-[#F2EDE4] text-[#1E2229] border-[#E8E2D8] dark:bg-[#242831] dark:text-[#F2EFE9] dark:border-[#2C313E]',
    success: 'bg-[#EBF5EE] text-[#2D6A4F] border-[#C7E6D3] dark:bg-[#1B2F23] dark:text-[#7DA18F] dark:border-[#2C4A38]',
    warning: 'bg-[#FEF7EC] text-[#9A6218] border-[#FBE0B5] dark:bg-[#342410] dark:text-[#E9B872] dark:border-[#523B1E]',
    error: 'bg-[#FDF2F2] text-[#B83232] border-[#F8C8C8] dark:bg-[#321616] dark:text-[#EF5350] dark:border-[#5A2424]',
    outline: 'bg-transparent text-[#6A6E78] border-[#E8E2D8] dark:text-[#9EA3B0] dark:border-[#2C313E]',
    terracotta: 'bg-[#FDF3EE] text-[#C85A32] border-[#F6D8CB] dark:bg-[#301E17] dark:text-[#D96B43] dark:border-[#563124]',
    sage: 'bg-[#F1F6F3] text-[#52796F] border-[#D0E2D8] dark:bg-[#1C2822] dark:text-[#7DA18F] dark:border-[#2F443A]',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors',
        variantStyles[normalizedVariant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}

export default Badge

