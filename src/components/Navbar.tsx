import { motion, useReducedMotion } from 'framer-motion'
import { TELEGRAM_URL } from '../data/site'

const links = [
  { label: 'Услуги', href: '#services' },
  { label: 'Проекты', href: '#projects' },
  { label: 'Как работаем', href: '#services' },
  { label: 'Контакты', href: '#contact' },
]

export default function Navbar() {
  const reduced = useReducedMotion()

  return (
    <motion.header
      initial={{ opacity: 0, y: reduced ? 0 : -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduced ? 0 : 0.6, ease: [0.25, 0.1, 0.25, 1] }}
      className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-6 pt-6 md:px-10"
    >
      <a
        href="#top"
        className="flex items-center gap-2 rounded-full bg-pill px-4 py-3 transition-colors hover:bg-neutral-800"
      >
        <span
          aria-hidden="true"
          className="block h-4 w-4 rounded-[4px] bg-accent"
        />
        <span className="text-sm font-medium text-white">petr-ai</span>
      </a>

      <nav className="hidden rounded-full bg-pill px-3 py-2 md:flex">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href}
            className="rounded-full px-4 py-2 text-sm text-neutral-300 transition-colors hover:bg-white/5 hover:text-white"
          >
            {link.label}
          </a>
        ))}
      </nav>

      <a
        href={TELEGRAM_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-full bg-white px-6 py-3 text-sm font-medium text-[#0a0a0a] transition-colors hover:bg-neutral-200"
      >
        Написать в Telegram
      </a>
    </motion.header>
  )
}
