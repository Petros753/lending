import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

const EASE = [0.25, 0.1, 0.25, 1] as const

type FadeInProps = {
  children: ReactNode
  delay?: number
  duration?: number
  y?: number
  className?: string
  /** Play on mount instead of when scrolled into view. */
  immediate?: boolean
}

export default function FadeIn({
  children,
  delay = 0,
  duration = 0.7,
  y = 30,
  className,
  immediate = false,
}: FadeInProps) {
  const reduced = useReducedMotion()

  const hidden = { opacity: 0, y: reduced ? 0 : y }
  const shown = { opacity: 1, y: 0 }
  const transition = { duration: reduced ? 0 : duration, delay: reduced ? 0 : delay, ease: EASE }

  if (immediate) {
    return (
      <motion.div
        className={className}
        initial={hidden}
        animate={shown}
        transition={transition}
      >
        {children}
      </motion.div>
    )
  }

  return (
    <motion.div
      className={className}
      initial={hidden}
      whileInView={shown}
      viewport={{ once: true, margin: '50px' }}
      transition={transition}
    >
      {children}
    </motion.div>
  )
}
