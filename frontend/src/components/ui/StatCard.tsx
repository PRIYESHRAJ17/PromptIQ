import React from 'react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  description?: string
  icon?: React.ReactNode
  className?: string
}

export function StatCard({
  title,
  value,
  change,
  trend = 'neutral',
  description,
  icon,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-[#1A1D23] border border-[#E8E2D8] dark:border-[#2C313E] rounded-xl p-5 shadow-xs transition-all hover:border-[#D5CCC0] dark:hover:border-[#3D4454]',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-[#6A6E78] dark:text-[#9EA3B0]">
          {title}
        </span>
        {icon && (
          <div className="p-2 rounded-lg bg-[#F8F6F0] dark:bg-[#242831] text-[#C85A32] dark:text-[#D96B43]">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <div className="text-3xl font-semibold tracking-tight text-[#1E2229] dark:text-[#F2EFE9]">
          {value}
        </div>
        {change && (
          <span
            className={cn(
              'text-xs font-medium px-1.5 py-0.5 rounded',
              trend === 'up' && 'text-[#2D6A4F] bg-[#EBF5EE] dark:text-[#7DA18F] dark:bg-[#1B2F23]',
              trend === 'down' && 'text-[#B83232] bg-[#FDF2F2] dark:text-[#EF5350] dark:bg-[#321616]',
              trend === 'neutral' && 'text-[#6A6E78] bg-[#F2EDE4] dark:text-[#9EA3B0] dark:bg-[#242831]'
            )}
          >
            {change}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-1.5 text-xs text-[#6A6E78] dark:text-[#9EA3B0]">
          {description}
        </p>
      )}
    </div>
  )
}

export default StatCard

