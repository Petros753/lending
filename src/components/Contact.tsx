import { Send } from 'lucide-react'
import Button from './Button'
import FadeIn from './FadeIn'
import { TELEGRAM_URL } from '../data/site'

export default function Contact() {
  return (
    <section id="contact" className="scroll-mt-28 px-6 py-24 md:px-10">
      <FadeIn className="mx-auto max-w-2xl">
        <div className="rounded-[32px] border border-white/10 bg-surface p-10 text-center md:p-16">
          <h2 className="text-2xl font-medium text-white md:text-3xl">
            Готов обсудить ваш проект
          </h2>
          <p className="mx-auto mt-4 max-w-md leading-relaxed text-white/60">
            Не знаете, с чего начать? Просто напишите — разберёмся вместе, без
            сложных терминов и заумных фраз
          </p>
          <Button href={TELEGRAM_URL} variant="accent" className="mt-8 px-8 py-4">
            <Send size={18} aria-hidden="true" />
            Написать в Telegram
          </Button>
        </div>
      </FadeIn>
    </section>
  )
}
