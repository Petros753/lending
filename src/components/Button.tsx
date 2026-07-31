import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

type Variant = 'solid' | 'accent' | 'outline'

type ButtonProps = {
  children: ReactNode
  href: string
  variant?: Variant
  className?: string
  /** Set false for in-page anchors. */
  external?: boolean
}

const variants: Record<Variant, string> = {
  solid: 'bg-white text-[#0a0a0a] hover:bg-neutral-200',
  accent: 'bg-accent text-[#0a0a0a] hover:bg-[#ff9d5c]',
  outline:
    'border border-white/15 text-white hover:border-white/35 hover:bg-white/5',
}

export default function Button({
  children,
  href,
  variant = 'solid',
  className = '',
  external = true,
}: ButtonProps) {
  const reduced = useReducedMotion()

  return (
    <motion.a
      href={href}
      target={external ? '_blank' : undefined}
      rel={external ? 'noopener noreferrer' : undefined}
      whileHover={reduced ? undefined : { scale: 1.03 }}
      whileTap={reduced ? undefined : { scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      className={`inline-flex items-center justify-center gap-2 rounded-full text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a0a] ${variants[variant]} ${className}`}
    >
      {children}
    </motion.a>
  )
}
