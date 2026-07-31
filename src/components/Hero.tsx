import { motion, useReducedMotion } from 'framer-motion'
import MagneticButton from './MagneticButton'
import StatBlock from './StatBlock'
import { TELEGRAM_URL } from '../data/site'

const EASE = [0.25, 0.1, 0.25, 1] as const
const WORD_SIZE = { fontSize: 'clamp(2.5rem, 9vw, 6rem)', letterSpacing: '-0.02em' }

function Word({
  children,
  delay,
  className,
  color,
}: {
  children: string
  delay: number
  className: string
  color: string
}) {
  const reduced = useReducedMotion()

  return (
    <motion.span
      initial={{ opacity: 0, y: reduced ? 0 : 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduced ? 0 : 0.8, delay: reduced ? 0 : delay, ease: EASE }}
      style={{ ...WORD_SIZE, color }}
      className={`block font-medium leading-[0.95] lowercase ${className}`}
    >
      {children}
    </motion.span>
  )
}

export default function Hero() {
  const reduced = useReducedMotion()

  return (
    <section id="top" className="relative min-h-screen overflow-hidden">
      {/* Ambient dot grid */}
      <div
        aria-hidden="true"
        className="dot-grid drift pointer-events-none absolute -inset-8 opacity-40"
      />

      <h1 className="sr-only">
        petr-ai — автоматизирую вашу рутину: Telegram-боты, AI-агенты и интеграции на n8n
      </h1>

      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center gap-7 px-6 pb-24 pt-32 text-center md:block md:px-0 md:pb-0 md:pt-0 md:text-left">
        <Word
          delay={0.1}
          color="#eeeeee"
          className="md:absolute md:left-[6%] md:top-[16%] lg:left-10"
        >
          автоматизирую
        </Word>

        <Word
          delay={0.25}
          color="#ff8a3d"
          className="md:absolute md:right-[6%] md:top-[34%] md:text-right lg:right-16"
        >
          вашу
        </Word>

        <Word
          delay={0.4}
          color="#eeeeee"
          className="md:absolute md:left-[14%] md:top-[52%] lg:left-24"
        >
          рутину
        </Word>

        <motion.p
          initial={{ opacity: 0, y: reduced ? 0 : 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduced ? 0 : 0.8, delay: reduced ? 0 : 0.5, ease: EASE }}
          className="max-w-[320px] text-sm leading-relaxed text-white/75 md:absolute md:right-[6%] md:top-[48%] md:max-w-[260px] md:text-left lg:right-16"
        >
          Снимаю 70–90% рутины с команды — Telegram-боты, AI-агенты и интеграции
          на n8n, которые ведут клиента до сделки
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: reduced ? 0 : 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduced ? 0 : 0.8, delay: reduced ? 0 : 0.65, ease: EASE }}
          className="md:absolute md:bottom-[16%] md:left-1/2 md:-translate-x-1/2"
        >
          <MagneticButton href={TELEGRAM_URL}>Обсудить проект</MagneticButton>
        </motion.div>

        {/* Corner stats — a row on mobile, scattered in the corners from md up */}
        <div className="mt-4 flex items-start justify-center gap-10 md:contents">
          <motion.div
            initial={{ opacity: 0, y: reduced ? 0 : 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduced ? 0 : 0.7, delay: reduced ? 0 : 0.6, ease: EASE }}
            className="md:absolute md:right-[6%] md:top-[16%] lg:right-16"
          >
            <StatBlock
              value="50+"
              label="проектов"
              tilt="right"
              dividerPosition="bottom"
              align="center"
              className="md:items-end md:text-right"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: reduced ? 0 : 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduced ? 0 : 0.7, delay: reduced ? 0 : 0.7, ease: EASE }}
            className="md:absolute md:bottom-[14%] md:left-[6%] lg:left-10"
          >
            <StatBlock
              value="40"
              label="клиентов"
              tilt="left"
              dividerPosition="top"
              align="center"
              className="md:items-start md:text-left"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: reduced ? 0 : 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduced ? 0 : 0.7, delay: reduced ? 0 : 0.8, ease: EASE }}
            className="md:absolute md:bottom-[14%] md:right-[6%] lg:right-16"
          >
            <StatBlock
              value="10"
              label="компаний"
              tilt="right"
              dividerPosition="top"
              align="center"
              className="md:items-end md:text-right"
            />
          </motion.div>
        </div>
      </div>

      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-0 left-0 h-48 w-full bg-gradient-to-b from-transparent to-[#0a0a0a]"
      />
    </section>
  )
}
