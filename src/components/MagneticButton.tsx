import { useRef, type ReactNode } from 'react'
import { motion, useMotionValue, useReducedMotion, useSpring } from 'framer-motion'

const RADIUS = 40

type MagneticButtonProps = {
  children: ReactNode
  href: string
  className?: string
}

/**
 * Pill button that drifts toward the cursor while hovered and springs back on
 * leave. Falls back to a plain button when reduced motion is requested.
 */
export default function MagneticButton({
  children,
  href,
  className = '',
}: MagneticButtonProps) {
  const ref = useRef<HTMLAnchorElement>(null)
  const reduced = useReducedMotion()

  const springConfig = { stiffness: 260, damping: 20, mass: 0.4 }
  const rawX = useMotionValue(0)
  const rawY = useMotionValue(0)
  const x = useSpring(rawX, springConfig)
  const y = useSpring(rawY, springConfig)

  const handleMove = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (reduced || !ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const dx = event.clientX - (rect.left + rect.width / 2)
    const dy = event.clientY - (rect.top + rect.height / 2)
    const distance = Math.hypot(dx, dy) || 1
    const pull = Math.min(distance, RADIUS) / distance
    rawX.set(dx * pull * 0.6)
    rawY.set(dy * pull * 0.6)
  }

  const reset = () => {
    rawX.set(0)
    rawY.set(0)
  }

  return (
    <motion.a
      ref={ref}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onMouseMove={handleMove}
      onMouseLeave={reset}
      onBlur={reset}
      style={reduced ? undefined : { x, y }}
      whileHover={reduced ? undefined : { scale: 1.03 }}
      whileTap={reduced ? undefined : { scale: 0.98 }}
      transition={{ type: 'spring', ...springConfig }}
      className={`inline-flex items-center justify-center gap-2 rounded-full bg-accent px-8 py-4 font-medium text-[#0a0a0a] transition-colors hover:bg-[#ff9d5c] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a0a] ${className}`}
    >
      {children}
    </motion.a>
  )
}
